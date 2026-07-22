"""
tests/test_szukaj.py
====================
Unit tests for szukaj.py.

HOW TO USE
----------
Never `import szukaj` directly in test code — szukaj.py has side effects
at module level (pip install calls, readline setup).  The `szukaj_mod`
session fixture from conftest.py loads it safely once per session.

`format_val` is a nested function inside build_structured_json and cannot
be imported directly — it is tested indirectly through build_structured_json.

load_full_database isolation
-----------------------------
The function resolves 'SiC-MOSFET', 'IGBT', etc. relative to the PROCESS
working directory at call time.  On Windows, monkeypatch.chdir is NOT
sufficient to isolate it from the real project database because the session-
scoped module was loaded with the project root as CWD context.

Solution: patch szukaj_mod.os.path.exists, szukaj_mod.os.walk, and
szukaj_mod.os.makedirs directly.  The helpers below capture os.walk and
os.path.exists BEFORE patching so fake_walk can still call the real
implementation on our temp paths without infinite recursion.

BUG MARKERS
-----------
• Bug 1 (e_on stored as scalar): tests marked  xfail(strict=True)
    XFAIL = bug present   → normal, not reported as failure
    XPASS = bug just fixed → remove the xfail marker

Run:
    pytest tests/test_szukaj.py -v
"""
from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from textwrap import dedent
from unittest.mock import patch

import pandas as pd
import pytest

# ── PLECS XML constants ──────────────────────────────────────────────────────

PLECS_NS = "http://www.plexim.com/xml/semiconductors/"

# Minimal switch-only PLECS XML.
# TurnOnLoss raw values: [0, 100, 400, 900] with scale="0.001"
# Correct import: [0.0, 0.1, 0.4, 0.9] J
# Bug 2 import:   [0.0, 0.0001, 0.0004, 0.0009] J  (÷1000 applied twice)
PLECS_XML = dedent(f"""\
    <?xml version="1.0" encoding="UTF-8"?>
    <SemiconductorLibrary xmlns="{PLECS_NS}">
      <Package class="MOSFET" vendor="TestCo" partnumber="TestSiC">
        <Variables/>
        <SemiconductorData>
          <ConductionLoss>
            <ComputationMethod>Table only</ComputationMethod>
            <CurrentAxis>-30 -20 -10 0 10 20 30</CurrentAxis>
            <TemperatureAxis>25</TemperatureAxis>
            <VoltageDrop scale="1">
              <Temperature>-0.48 -0.32 -0.16 0.0 0.16 0.32 0.48</Temperature>
            </VoltageDrop>
          </ConductionLoss>
          <TurnOnLoss>
            <ComputationMethod>Table only</ComputationMethod>
            <CurrentAxis>0 10 20 30</CurrentAxis>
            <VoltageAxis>600</VoltageAxis>
            <TemperatureAxis>25</TemperatureAxis>
            <Energy scale="0.001">
              <Temperature>
                <Voltage>0 100 400 900</Voltage>
              </Temperature>
            </Energy>
          </TurnOnLoss>
          <TurnOffLoss>
            <ComputationMethod>Table only</ComputationMethod>
            <CurrentAxis>0 10 20 30</CurrentAxis>
            <VoltageAxis>600</VoltageAxis>
            <TemperatureAxis>25</TemperatureAxis>
            <Energy scale="0.001">
              <Temperature>
                <Voltage>0 50 200 450</Voltage>
              </Temperature>
            </Energy>
          </TurnOffLoss>
        </SemiconductorData>
      </Package>
    </SemiconductorLibrary>
""")

EXPECTED_E_ON_J  = [0.0, 0.1, 0.4, 0.9]
EXPECTED_E_OFF_J = [0.0, 0.05, 0.2, 0.45]

# Minimal transistor JSON that export_plecs_xml accepts
TRANSISTOR_JSON = {
    "name": "TEST_EXPORT",
    "manufacturer": "TestCo",
    "type": "SiC-MOSFET",
    "switch": {
        "t_j_max": 175,
        "channel": [{"t_j": 25, "v_g": 15,
                     "graph_v_i": [[0.0, 0.16, 0.32, 0.48], [0, 10, 20, 30]]}],
        "e_on":  [{"dataset_type": "graph_i_e", "t_j": 25, "v_supply": 600,
                   "v_g": 15, "r_g": 5,
                   "graph_i_e": [[0, 10, 20, 30], [0.0, 0.1, 0.4, 0.9]]}],
        "e_off": [{"dataset_type": "graph_i_e", "t_j": 25, "v_supply": 600,
                   "v_g": 0, "r_g": 5,
                   "graph_i_e": [[0, 10, 20, 30], [0.0, 0.05, 0.2, 0.45]]}],
        "thermal_foster": {},
    },
    "diode": {
        "t_j_max": 175,
        "channel": [{"t_j": 25, "v_g": 0,
                     "graph_v_i": [[0.0, 1.0, 1.5, 2.0], [0, 10, 20, 30]]}],
        "e_rr": [],
        "thermal_foster": {},
    },
}

# ===========================================================================
# load_full_database isolation helpers
# ===========================================================================

# Capture original os functions NOW, before any test patches them.
# fake_walk must call _ORIG_WALK (not os.walk) to avoid infinite recursion
# once patch.object replaces os.walk on the szukaj_mod module.
_ORIG_WALK   = os.walk
_ORIG_EXISTS = os.path.exists

_TECH_FOLDERS = {'GaN', 'IGBT', 'SiC-MOSFET', 'Si-MOSFET'}


def _make_fs_patches(tmp_path, only=None):
    """
    Return (fake_exists, fake_walk, noop_makedirs).

    All calls to os.path.exists / os.walk on a tech-folder name are
    redirected to ``tmp_path / folder_name``.

    Parameters
    ----------
    tmp_path : Path   temp directory that holds the fake tech folders
    only     : set   tech folder names that "exist"; None = whatever is
                     physically present in tmp_path
    """
    def fake_exists(p: str) -> bool:
        name = os.path.basename(str(p).rstrip('/\\'))
        if name in _TECH_FOLDERS:
            if only is not None:
                return name in only
            return _ORIG_EXISTS(str(tmp_path / name))
        return _ORIG_EXISTS(p)

    def fake_walk(p):
        name = os.path.basename(str(p).rstrip('/\\'))
        key  = name if name in _TECH_FOLDERS else (p if p in _TECH_FOLDERS else None)
        if key:
            target = tmp_path / key
            if target.exists():
                yield from _ORIG_WALK(str(target))
        else:
            yield from _ORIG_WALK(p)

    return fake_exists, fake_walk, (lambda *a, **k: None)


# ===========================================================================
# format_val — tested indirectly via build_structured_json
# ===========================================================================
class TestFormatVal:
    """format_val is nested inside build_structured_json; tested via v_abs_max."""

    def test_absent_key_becomes_empty_string(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({})["v_abs_max"] == ""

    def test_empty_string_stays_empty(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({"v_abs_max": ""})["v_abs_max"] == ""

    def test_float_string_becomes_float(self, szukaj_mod):
        v = szukaj_mod.build_structured_json({"v_abs_max": "1200.5"})["v_abs_max"]
        assert v == pytest.approx(1200.5) and isinstance(v, float)

    def test_integer_string_becomes_int(self, szukaj_mod):
        v = szukaj_mod.build_structured_json({"v_abs_max": "1200"})["v_abs_max"]
        assert v == 1200 and isinstance(v, int)

    def test_native_int_passes_through(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({"v_abs_max": 1200})["v_abs_max"] == 1200

    def test_native_float_passes_through(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({"v_abs_max": 1200.5})["v_abs_max"] == pytest.approx(1200.5)

    def test_non_numeric_string_passes_through(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({"housing_type": "TO-247"})["housing_type"] == "TO-247"


# ===========================================================================
# Bug 1 regression — e_on / e_off must be lists
# ===========================================================================
class TestBugEonScalar:
    """
    BUG 1 (NOT YET FIXED): build_structured_json stores switch.e_on as a
    scalar instead of an empty list [].  TDB requires a list of
    SwitchEnergyData dicts.

    xfail(strict=True): XFAIL while bug is present; XPASS after it is fixed
    (then remove the marker).
    """

    @pytest.mark.xfail(strict=True, reason="Bug 1: switch.e_on is scalar, not list")
    def test_e_on_is_list(self, szukaj_mod):
        assert isinstance(szukaj_mod.build_structured_json({})["switch"]["e_on"], list)

    @pytest.mark.xfail(strict=True, reason="Bug 1: switch.e_off is scalar, not list")
    def test_e_off_is_list(self, szukaj_mod):
        assert isinstance(szukaj_mod.build_structured_json({})["switch"]["e_off"], list)

    @pytest.mark.xfail(strict=True, reason="Bug 1: switch.e_on_meas is scalar, not list")
    def test_e_on_meas_is_list(self, szukaj_mod):
        assert isinstance(szukaj_mod.build_structured_json({})["switch"]["e_on_meas"], list)

    def test_diode_e_rr_already_correct(self, szukaj_mod):
        assert isinstance(szukaj_mod.build_structured_json({})["diode"]["e_rr"], list)

    def test_diode_channel_already_correct(self, szukaj_mod):
        assert isinstance(szukaj_mod.build_structured_json({})["diode"]["channel"], list)


# ===========================================================================
# build_structured_json — schema structure
# ===========================================================================
class TestBuildStructuredJson:

    def test_top_level_keys_present(self, szukaj_mod):
        out = szukaj_mod.build_structured_json({})
        for key in ("name", "type", "manufacturer", "v_abs_max", "i_abs_max", "switch", "diode"):
            assert key in out

    def test_switch_subkeys_present(self, szukaj_mod):
        sw = szukaj_mod.build_structured_json({})["switch"]
        for key in ("t_j_max", "channel", "e_on", "e_off"):
            assert key in sw

    def test_diode_subkeys_present(self, szukaj_mod):
        di = szukaj_mod.build_structured_json({})["diode"]
        for key in ("t_j_max", "channel", "e_rr"):
            assert key in di

    def test_name_field_populated(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({"name": "MY_DEV"})["name"] == "MY_DEV"

    def test_v_abs_max_numeric_conversion(self, szukaj_mod):
        assert szukaj_mod.build_structured_json({"v_abs_max": "1200"})["v_abs_max"] == 1200


# ===========================================================================
# preprocess_query
# ===========================================================================
class TestPreprocessQuery:
    def test_equality_becomes_str_contains(self, szukaj_mod):
        out = szukaj_mod.preprocess_query("name == 'CREE'")
        assert "str.contains" in out and "CREE" in out and "==" not in out

    def test_inequality_becomes_negated_str_contains(self, szukaj_mod):
        out = szukaj_mod.preprocess_query("manufacturer != 'Infineon'")
        assert "str.contains" in out and "~" in out and "!=" not in out

    def test_numeric_comparison_is_unchanged(self, szukaj_mod):
        q = "v_abs_max >= 1200"
        assert szukaj_mod.preprocess_query(q) == q

    def test_combined_numeric_and_string_query(self, szukaj_mod):
        out = szukaj_mod.preprocess_query("v_abs_max >= 900 & manufacturer == 'ROHM'")
        assert "v_abs_max >= 900" in out and "str.contains" in out

    def test_double_quoted_string_handled(self, szukaj_mod):
        out = szukaj_mod.preprocess_query('name == "C3M"')
        assert "str.contains" in out and "C3M" in out

    def test_output_is_valid_pandas_query(self, szukaj_mod):
        df  = pd.DataFrame({"name": ["CREE_C3M", "infineon_42"], "v_abs_max": [1200, 650]})
        out = szukaj_mod.preprocess_query("name == 'CREE'")
        assert len(df.query(out)) == 1

    def test_case_insensitive_str_contains(self, szukaj_mod):
        df  = pd.DataFrame({"manufacturer": ["Infineon", "ROHM", "Wolfspeed"]})
        out = szukaj_mod.preprocess_query("manufacturer == 'infineon'")
        assert len(df.query(out)) == 1


# ===========================================================================
# load_full_database — filesystem-isolated via os-patching
# ===========================================================================
class TestLoadFullDatabase:
    """
    Why not monkeypatch.chdir?
    ---------------------------
    load_full_database resolves 'SiC-MOSFET' etc. relative to the process
    CWD.  On Windows pytest starts from the project root, which already has
    real transistor folders.  The session-scoped szukaj_mod was loaded in
    that context, so monkeypatch.chdir does not prevent the real database
    from being found.

    Instead we patch szukaj_mod.os.path.exists, szukaj_mod.os.walk, and
    szukaj_mod.os.makedirs to serve a controlled fake filesystem in tmp_path.
    The originals are captured in _ORIG_WALK / _ORIG_EXISTS at module import
    time (above), so fake_walk can call them without recursion.
    """

    DEVICE_JSON = {
        "name": "TEST_SIC_1200", "type": "SiC-MOSFET",
        "manufacturer": "TestCo", "housing_type": "TO-247",
        "v_abs_max": 1200, "i_abs_max": 60, "r_th_cs": 0.0,
        "switch": {"t_j_max": 175, "channel": [], "e_on": [], "e_off": []},
        "diode":  {"t_j_max": 175, "channel": [], "e_rr": []},
    }

    @pytest.fixture
    def sic_db(self, tmp_path):
        """tmp_path with one valid SiC-MOSFET device."""
        d = tmp_path / "SiC-MOSFET" / "1200V"
        d.mkdir(parents=True)
        (d / "TEST_SIC_1200.json").write_text(
            json.dumps(self.DEVICE_JSON), encoding="utf-8"
        )
        return tmp_path

    def test_returns_dataframe(self, szukaj_mod, tmp_path):
        fe, fw, fm = _make_fs_patches(tmp_path)
        with patch.object(szukaj_mod.os.path, "exists", fe), \
             patch.object(szukaj_mod.os, "walk", fw), \
             patch.object(szukaj_mod.os, "makedirs", fm):
            df = szukaj_mod.load_full_database()
        assert isinstance(df, pd.DataFrame)

    def test_device_appears_in_dataframe(self, szukaj_mod, sic_db):
        fe, fw, fm = _make_fs_patches(sic_db)
        with patch.object(szukaj_mod.os.path, "exists", fe), \
             patch.object(szukaj_mod.os, "walk", fw), \
             patch.object(szukaj_mod.os, "makedirs", fm):
            df = szukaj_mod.load_full_database()
        assert "TEST_SIC_1200" in df["name"].values

    def test_category_column_is_correct(self, szukaj_mod, sic_db):
        fe, fw, fm = _make_fs_patches(sic_db)
        with patch.object(szukaj_mod.os.path, "exists", fe), \
             patch.object(szukaj_mod.os, "walk", fw), \
             patch.object(szukaj_mod.os, "makedirs", fm):
            df = szukaj_mod.load_full_database()
        row = df[df["name"] == "TEST_SIC_1200"].iloc[0]
        assert row["Category"] == "SiC-MOSFET"

    def test_original_file_path_is_set(self, szukaj_mod, sic_db):
        fe, fw, fm = _make_fs_patches(sic_db)
        with patch.object(szukaj_mod.os.path, "exists", fe), \
             patch.object(szukaj_mod.os, "walk", fw), \
             patch.object(szukaj_mod.os, "makedirs", fm):
            df = szukaj_mod.load_full_database()
        assert "_original_file_path" in df.columns
        fpath = df[df["name"] == "TEST_SIC_1200"].iloc[0]["_original_file_path"]
        assert str(fpath).endswith(".json")

    def test_empty_db_returns_empty_dataframe(self, szukaj_mod, tmp_path):
        """When no tech folders exist, return an empty DataFrame, not an error."""
        fe, fw, fm = _make_fs_patches(tmp_path)   # tmp_path is empty
        with patch.object(szukaj_mod.os.path, "exists", fe), \
             patch.object(szukaj_mod.os, "walk", fw), \
             patch.object(szukaj_mod.os, "makedirs", fm):
            df = szukaj_mod.load_full_database()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_malformed_json_is_skipped(self, szukaj_mod, tmp_path):
        """Invalid JSON files must be silently skipped without crashing."""
        bad = tmp_path / "IGBT" / "bad"
        bad.mkdir(parents=True)
        (bad / "broken.json").write_text("{not valid json", encoding="utf-8")

        fe, fw, fm = _make_fs_patches(tmp_path, only={"IGBT"})
        with patch.object(szukaj_mod.os.path, "exists", fe), \
             patch.object(szukaj_mod.os, "walk", fw), \
             patch.object(szukaj_mod.os, "makedirs", fm):
            df = szukaj_mod.load_full_database()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


# ===========================================================================
# export_plecs_xml
# ===========================================================================
class TestExportPlecsXml:

    @pytest.fixture
    def transistor_json_path(self, tmp_path):
        p = tmp_path / "TEST_EXPORT.json"
        p.write_text(json.dumps(TRANSISTOR_JSON), encoding="utf-8")
        return p

    def test_returns_true_on_success(self, szukaj_mod, transistor_json_path, tmp_path):
        assert szukaj_mod.export_plecs_xml(str(transistor_json_path), output_dir=str(tmp_path)) is True

    def test_switch_xml_file_is_created(self, szukaj_mod, transistor_json_path, tmp_path):
        szukaj_mod.export_plecs_xml(str(transistor_json_path), output_dir=str(tmp_path))
        assert (tmp_path / "TEST_EXPORT_switch.xml").exists()

    def test_diode_xml_file_is_created(self, szukaj_mod, transistor_json_path, tmp_path):
        szukaj_mod.export_plecs_xml(str(transistor_json_path), output_dir=str(tmp_path))
        assert (tmp_path / "TEST_EXPORT_diode.xml").exists()

    def test_energy_values_multiplied_by_1000_in_xml(
            self, szukaj_mod, transistor_json_path, tmp_path):
        """
        e_on = [0.0, 0.1, 0.4, 0.9] J in JSON.
        The XML Energy element must store [0, 100, 400, 900] (×1000)
        with scale="0.001" so PLECS recovers the original joule values.

        We parse the XML with ElementTree — no fragile string search —
        to be robust against namespace prefixes and float formatting.
        """
        szukaj_mod.export_plecs_xml(str(transistor_json_path), output_dir=str(tmp_path))

        tree = ET.parse(str(tmp_path / "TEST_EXPORT_switch.xml"))
        root = tree.getroot()

        # Collect all Voltage elements that live inside an Energy element,
        # regardless of namespace prefix.
        energy_volt_texts = [
            el.text
            for energy in root.iter()
            if _local_name(energy) == "Energy"
            for el in energy.iter()
            if _local_name(el) == "Voltage" and el.text
        ]
        assert energy_volt_texts, "No Voltage elements found inside Energy elements in switch XML"

        raw = [float(x) for x in energy_volt_texts[0].split()]
        expected_raw = [v * 1000 for v in [0.0, 0.1, 0.4, 0.9]]
        assert raw == pytest.approx(expected_raw, rel=1e-6)

    def test_returns_false_for_missing_json(self, szukaj_mod, tmp_path):
        result = szukaj_mod.export_plecs_xml(
            str(tmp_path / "nonexistent.json"), output_dir=str(tmp_path)
        )
        assert result is False


def _local_name(el) -> str:
    """Return the local tag name, stripping any '{namespace}' prefix."""
    tag = el.tag
    return tag.split("}")[-1] if "}" in tag else tag


# ===========================================================================
# Bug 2 regression — PLECS energy must not be divided by 1000 twice
# ===========================================================================
class TestBugPlecsEnergyImport:
    """
    BUG 2: import_plecs_xml() applies the XML scale attribute correctly
    (raw × 0.001 → joules), then ALSO divides by 1000 again:

        e_vals   = raw * scale          # e.g. 100 * 0.001 = 0.1 J  ✓
        e_joules = e_vals / 1000.0      # 0.1 / 1000 = 0.0001 J    ✗  BUG

    import_plecs_xml() takes NO arguments; it reads file paths via input().
    We mock builtins.input so tests can run non-interactively.
    The function saves to {type}/PLECS_Import/{name}.json relative to CWD,
    so we monkeypatch.chdir to tmp_path to control the output location.
    """

    @pytest.fixture
    def imported_json(self, szukaj_mod, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        xml_file = tmp_path / "TestSiC.xml"
        xml_file.write_text(PLECS_XML, encoding="utf-8")

        answers = iter([str(xml_file), ""])   # switch path, then "" → skip diode
        monkeypatch.setattr("builtins.input", lambda _: next(answers))
        szukaj_mod.import_plecs_xml()

        saved = list(tmp_path.rglob("*.json"))
        assert saved, "import_plecs_xml() did not write any JSON file"
        with open(saved[0], encoding="utf-8") as f:
            return json.load(f)

    def test_e_on_energy_values_are_in_joules(self, imported_json):
        """
        TurnOnLoss raw=[0,100,400,900] × scale=0.001 → [0.0, 0.1, 0.4, 0.9] J.
        If Bug 2 is present the values are [0, 0.0001, 0.0004, 0.0009] J.
        """
        e_on_list = imported_json["switch"]["e_on"]
        assert e_on_list, "No e_on entries in imported JSON"
        values = e_on_list[0]["graph_i_e"][1]
        for i, (actual, expected) in enumerate(zip(values, EXPECTED_E_ON_J)):
            assert actual == pytest.approx(expected, abs=1e-9), (
                f"E_on[{i}] = {actual:.7f} J, expected {expected:.4f} J. "
                f"If actual ≈ {expected/1000:.7f} J, Bug 2 is still present."
            )

    def test_e_off_energy_values_are_in_joules(self, imported_json):
        e_off_list = imported_json["switch"]["e_off"]
        assert e_off_list
        values = e_off_list[0]["graph_i_e"][1]
        for i, (actual, expected) in enumerate(zip(values, EXPECTED_E_OFF_J)):
            assert actual == pytest.approx(expected, abs=1e-9), (
                f"E_off[{i}] = {actual:.7f} J, expected {expected:.4f} J."
            )

    def test_energy_magnitude_is_physically_plausible(self, imported_json):
        """
        900 mJ at 30 A is physically plausible for a 600 V device.
        0.9 mJ is not.  Bug 2 produces the latter.
        """
        values = imported_json["switch"]["e_on"][0]["graph_i_e"][1]
        assert values[-1] > 0.05, (
            f"E_on at 30 A = {values[-1]:.6f} J — too small. Bug 2 still active."
        )

    def test_channel_data_imported_correctly(self, imported_json):
        channels = imported_json["switch"]["channel"]
        assert channels
        i_axis = channels[0]["graph_v_i"][1]
        assert i_axis == pytest.approx([0.0, 10.0, 20.0, 30.0])

    def test_imported_json_type_is_sic_mosfet(self, imported_json):
        assert imported_json["type"] == "SiC-MOSFET"

    def test_e_on_e_off_are_lists(self, imported_json):
        assert isinstance(imported_json["switch"]["e_on"], list)
        assert isinstance(imported_json["switch"]["e_off"], list)