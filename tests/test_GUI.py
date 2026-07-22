"""
tests/test_gui.py
=================
Unit tests for GUI.py.

DESIGN APPROACH
---------------
GUI.py creates a Tkinter window on import, which requires a display
server.  In CI (Linux headless) and in any environment without a
screen, a plain ``import GUI`` fails immediately.

Solution: mock every display-dependent library BEFORE importing the
module (see ``gui_mod`` fixture below).  The mock block stays active
until exec_module returns; after that, the loaded module object keeps
its own references to the real (non-display) logic and can be tested.

WHAT IS TESTED
--------------
Three layers of increasing complexity:

1. Pure module-level functions — no Tk objects involved:
   • _get_axis_labels   chart-key → physical axis label pair
   • is_curve_field     field-name classification
   • TransistorGUI._cell_str   DataFrame cell → display string

2. Filesystem helper:
   • load_json_for_name   looks up a transistor JSON by name

3. Extracted logic / API contracts:
   • Filename sanitisation (from _create_save)
   • Search filter query builder
   • preprocess_query signature mismatch (GUI passes 2 args, szukaj
     only accepts 1) — documented as xfail until fixed

BUG MARKER
----------
Tests marked xfail(strict=True):
  XFAIL = bug still present   (expected, not a CI failure)
  XPASS = bug was just fixed  (remove the xfail marker then)

Run:
    pytest tests/test_gui.py -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_TESTS_DIR  = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(_TESTS_DIR)
GUI_PATH    = os.path.join(PROJECT_ROOT, "GUI.py")


# ---------------------------------------------------------------------------
# Headless import fixture
# ---------------------------------------------------------------------------

# All display-dependent modules replaced with MagicMock instances.
# Defined at module level so the same mock objects survive for the whole
# session (the module holds references to them after import).
_GUI_MOCKS = {
    "tkinter":                           MagicMock(),
    "tkinter.ttk":                       MagicMock(),
    "tkinter.messagebox":                MagicMock(),
    "tkinter.filedialog":                MagicMock(),
    "matplotlib":                        MagicMock(),
    "matplotlib.backends":               MagicMock(),
    "matplotlib.backends.backend_tkagg": MagicMock(),
    "matplotlib.figure":                 MagicMock(),
    "matplotlib.pyplot":                 MagicMock(),
    "converters":                        MagicMock(),
    "converters.gui_tab":                MagicMock(),
}


@pytest.fixture(scope="module")
def gui_mod():
    """
    Load GUI.py with all display-dependent modules mocked.

    subprocess.check_call is also patched so szukaj.py's auto-pip-install
    does not run when exec_module triggers its import.
    """
    with patch.dict(sys.modules, _GUI_MOCKS), patch("subprocess.check_call"):
        spec = importlib.util.spec_from_file_location("_GUI_headless", GUI_PATH)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# _get_axis_labels
# ===========================================================================
class TestGetAxisLabels:
    """
    _get_axis_labels(chart_key) returns (xlabel, ylabel) by scanning
    _CHART_AXIS_MAP for the first fragment contained in chart_key.lower().
    Unknown keys fall back to ('X', 'Y').
    """

    @pytest.mark.parametrize("key,expected_x,expected_y", [
        # V-I conduction curve
        ("graph_v_i",               "V [V]",    "I [A]"),
        # I-V inverse curve
        ("graph_i_v",               "I [A]",    "V [V]"),
        # switching energy vs current
        ("graph_i_e",               "I [A]",    "E [J]"),
        # switching energy named by type
        ("switch_e_on_graph_i_e",   "I [A]",    "E_on [J]"),
        ("switch_e_off_something",  "I [A]",    "E_off [J]"),
        # input capacitance
        ("c_iss",                   "V_DS [V]", "C_iss [F]"),
        ("c_oss_data",              "V_DS [V]", "C_oss [F]"),
        # unknown key
        ("some_unknown_field",      "X",        "Y"),
    ])
    def test_known_and_unknown_keys(self, gui_mod, key, expected_x, expected_y):
        xl, yl = gui_mod._get_axis_labels(key)
        assert xl == expected_x, f"xlabel wrong for key {key!r}"
        assert yl == expected_y, f"ylabel wrong for key {key!r}"

    def test_case_insensitive_matching(self, gui_mod):
        """Matching is done on chart_key.lower(), so mixed case must work."""
        xl, yl = gui_mod._get_axis_labels("GRAPH_V_I")
        assert xl == "V [V]" and yl == "I [A]"

    def test_empty_key_returns_fallback(self, gui_mod):
        assert gui_mod._get_axis_labels("") == ("X", "Y")


# ===========================================================================
# is_curve_field
# ===========================================================================
class TestIsCurveField:
    """
    is_curve_field(fn) classifies a field name as a curve (True) or scalar
    (False).  Curves start with 'graph_', 'diode_', 'switch_', or 'c_'
    and do NOT end in '_fix' or contain 'manufacturer', 'comment',
    'technology', or 't_j_max'.
    """

    @pytest.mark.parametrize("fn", [
        "graph_v_i",
        "graph_i_e",
        "switch_channel",
        "switch_e_on",
        "diode_channel",
        "c_iss",
        "c_oss",
        "c_rss",
    ])
    def test_curve_fields_return_true(self, gui_mod, fn):
        assert gui_mod.is_curve_field(fn) is True, f"{fn!r} should be a curve field"

    @pytest.mark.parametrize("fn", [
        "v_abs_max",        # scalar
        "i_abs_max",        # scalar
        "manufacturer",     # explicitly excluded
        "switch_manufacturer",  # contains 'manufacturer'
        "switch_t_j_max",   # contains 't_j_max'
        "t_j_max",          # contains 't_j_max'
        "graph_v_i_fix",    # ends with '_fix'
        "switch_channel_fix",  # ends with '_fix'
        "comment",          # explicitly excluded
        "technology",       # explicitly excluded
    ])
    def test_scalar_fields_return_false(self, gui_mod, fn):
        assert gui_mod.is_curve_field(fn) is False, f"{fn!r} should NOT be a curve field"


# ===========================================================================
# TransistorGUI._cell_str
# ===========================================================================
class TestCellStr:
    """
    _cell_str(v) converts a DataFrame cell to a display string.

    Contract
    --------
    • list or dict           → '[curve]'
    • None / NaN / '' / 'nan' / 'None' → '-'
    • Any other value        → str(v).strip()
    """

    def _s(self, gui_mod, v):
        return gui_mod.TransistorGUI._cell_str(v)

    def test_list_returns_curve(self, gui_mod):
        assert self._s(gui_mod, [1, 2, 3]) == "[curve]"

    def test_empty_list_returns_curve(self, gui_mod):
        assert self._s(gui_mod, []) == "[curve]"

    def test_dict_returns_curve(self, gui_mod):
        assert self._s(gui_mod, {"key": "val"}) == "[curve]"

    def test_none_returns_dash(self, gui_mod):
        assert self._s(gui_mod, None) == "-"

    def test_empty_string_returns_dash(self, gui_mod):
        assert self._s(gui_mod, "") == "-"

    def test_nan_string_returns_dash(self, gui_mod):
        assert self._s(gui_mod, "nan") == "-"

    def test_none_string_returns_dash(self, gui_mod):
        assert self._s(gui_mod, "None") == "-"

    def test_float_nan_returns_dash(self, gui_mod):
        assert self._s(gui_mod, float("nan")) == "-"

    def test_integer_returns_string(self, gui_mod):
        assert self._s(gui_mod, 1200) == "1200"

    def test_float_returns_string(self, gui_mod):
        assert self._s(gui_mod, 16.5) == "16.5"

    def test_normal_string_passes_through(self, gui_mod):
        assert self._s(gui_mod, "TO-247") == "TO-247"

    def test_whitespace_string_stripped(self, gui_mod):
        # str(v).strip() — leading/trailing whitespace removed
        assert self._s(gui_mod, "  SiC-MOSFET  ") == "SiC-MOSFET"


# ===========================================================================
# load_json_for_name
# ===========================================================================
class TestLoadJsonForName:
    """
    load_json_for_name(name, df) searches for a transistor JSON.

    Priority:
      1. Exact match on df["name"] → read from df["_original_file_path"]
      2. Case-insensitive match on df["name"] → same path
      3. Fallback: os.walk(_THIS_DIR) matching by name key or filename stem
      4. Returns (None, None) if nothing found
    """

    @pytest.fixture
    def device_file(self, tmp_path):
        """Write a single transistor JSON to a temp file; return (df, path)."""
        device = {
            "name":         "TEST_CREE",
            "type":         "SiC-MOSFET",
            "v_abs_max":    1200,
            "manufacturer": "TestCo",
        }
        fp = tmp_path / "TEST_CREE.json"
        fp.write_text(json.dumps(device), encoding="utf-8")
        df = pd.DataFrame([{
            "name": "TEST_CREE",
            "_original_file_path": str(fp),
        }])
        return df, str(fp)

    def test_exact_name_match_in_df(self, gui_mod, device_file):
        df, fp = device_file
        data, path = gui_mod.load_json_for_name("TEST_CREE", df)
        assert data is not None
        assert data["name"] == "TEST_CREE"
        assert path == fp

    def test_case_insensitive_name_match(self, gui_mod, device_file):
        df, _ = device_file
        data, path = gui_mod.load_json_for_name("test_cree", df)
        assert data is not None
        assert data["name"] == "TEST_CREE"

    def test_returns_none_when_not_found(self, gui_mod, device_file):
        df, _ = device_file
        data, path = gui_mod.load_json_for_name("DOES_NOT_EXIST", df)
        assert data is None
        assert path is None

    def test_fallback_walk_finds_file_by_name_key(self, gui_mod, tmp_path):
        """
        When the name is NOT in df, load_json_for_name falls back to
        os.walk(_THIS_DIR).  Patching _THIS_DIR controls which folder is walked.
        """
        device = {"name": "WALK_DEVICE", "type": "IGBT"}
        (tmp_path / "WALK_DEVICE.json").write_text(json.dumps(device))
        empty_df = pd.DataFrame(columns=["name", "_original_file_path"])

        # Redirect the fallback walk to our temp folder
        original_dir = gui_mod._THIS_DIR
        try:
            gui_mod._THIS_DIR = str(tmp_path)
            data, path = gui_mod.load_json_for_name("WALK_DEVICE", empty_df)
        finally:
            gui_mod._THIS_DIR = original_dir

        assert data is not None, "Fallback walk did not find the file"
        assert data["name"] == "WALK_DEVICE"

    def test_missing_file_path_in_df_does_not_crash(self, gui_mod, tmp_path):
        """If _original_file_path points to a non-existent file, no exception."""
        df = pd.DataFrame([{
            "name": "GHOST",
            "_original_file_path": str(tmp_path / "gone.json"),
        }])
        original_dir = gui_mod._THIS_DIR
        try:
            gui_mod._THIS_DIR = str(tmp_path)  # empty tmp_path → walk finds nothing
            data, path = gui_mod.load_json_for_name("GHOST", df)
        finally:
            gui_mod._THIS_DIR = original_dir
        # Should return (None, None) gracefully rather than raising
        assert data is None


# ===========================================================================
# preprocess_query API mismatch — Bug
# ===========================================================================
class TestPreprocessQueryApi:
    """
    BUG: GUI._run_search calls
        preprocess_query(raw, self.df.columns)   ← 2 arguments
    but szukaj.py's function is defined as
        def preprocess_query(q):                  ← 1 argument

    This raises TypeError whenever a user types a raw query in the Search tab.

    Fix options:
      A) Change GUI.py:     preprocess_query(raw)  (drop df.columns)
      B) Change szukaj.py:  def preprocess_query(q, df_columns=None):
    """

    @pytest.mark.xfail(
        strict=True,
        reason="Bug: GUI calls preprocess_query(q, cols) but szukaj only accepts preprocess_query(q)"
    )
    def test_preprocess_query_accepts_two_arguments(self, gui_mod):
        """
        GUI._run_search passes self.df.columns as a second argument.
        The function must accept it without raising TypeError.
        """
        result = gui_mod.preprocess_query(
            "name == 'CREE'",
            pd.Index(["name", "type", "v_abs_max"]),
        )
        assert isinstance(result, str)

    def test_preprocess_query_works_with_one_argument(self, gui_mod):
        """
        The one-argument form must always work (szukaj.py's own CLI uses this).
        """
        result = gui_mod.preprocess_query("name == 'CREE'")
        assert "str.contains" in result
        assert "CREE" in result


# ===========================================================================
# Filename sanitisation  (extracted from _create_save)
# ===========================================================================
class TestFilenameSanitisation:
    """
    _create_save builds the JSON filename as:
        clean_fn = "".join(c if c.isalnum() or c in('_','-') else '_'
                           for c in name) + ".json"

    Every character that is not alphanumeric, underscore, or hyphen is
    replaced with an underscore.
    """

    @staticmethod
    def _sanitise(name: str) -> str:
        """Replicate the exact expression from _create_save."""
        return (
            "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
            + ".json"
        )

    def test_clean_name_is_unchanged(self):
        assert self._sanitise("CREE_C3M0016120K") == "CREE_C3M0016120K.json"

    def test_spaces_replaced_with_underscores(self):
        assert self._sanitise("Infineon IKW40N120") == "Infineon_IKW40N120.json"

    def test_special_chars_replaced(self):
        # Parentheses, dots, spaces → underscores
        assert self._sanitise("device (rev.B)") == "device__rev_B_.json"

    def test_hyphens_preserved(self):
        # Hyphen is in the allow-list
        assert self._sanitise("GaN-device") == "GaN-device.json"

    def test_empty_name_gives_only_extension(self):
        assert self._sanitise("") == ".json"

    def test_all_special_chars(self):
        assert self._sanitise("@#$%!") == "_____.json"


# ===========================================================================
# Create-save validation logic  (extracted from _create_save)
# ===========================================================================
class TestCreateSaveValidation:
    """
    _create_save validates two required fields before writing:
        1. 'name' must be non-empty
        2. 'Category' must be non-empty AND one of TECH_CATEGORIES

    We test the validation rules directly, without instantiating TransistorGUI,
    by replicating the exact condition from the method.
    """

    @staticmethod
    def _validate(gui_mod, name: str, category: str) -> str | None:
        """
        Returns an error-message string if validation fails, else None.
        Mirrors the guard clauses at the top of _create_save.
        """
        if not name or not category:
            return "'name' and 'Category' are required."
        if category not in gui_mod.TECH_CATEGORIES:
            return f"Category must be one of: {gui_mod.TECH_CATEGORIES}"
        return None

    def test_valid_input_passes(self, gui_mod):
        assert self._validate(gui_mod, "CREE_C3M", "SiC-MOSFET") is None

    def test_missing_name_fails(self, gui_mod):
        err = self._validate(gui_mod, "", "SiC-MOSFET")
        assert err is not None
        assert "required" in err

    def test_missing_category_fails(self, gui_mod):
        err = self._validate(gui_mod, "MY_DEVICE", "")
        assert err is not None
        assert "required" in err

    def test_invalid_category_fails(self, gui_mod):
        err = self._validate(gui_mod, "MY_DEVICE", "GaAs")
        assert err is not None
        assert "GaAs" not in gui_mod.TECH_CATEGORIES

    @pytest.mark.parametrize("category", ["GaN", "IGBT", "SiC-MOSFET", "Si-MOSFET"])
    def test_all_valid_categories_pass(self, gui_mod, category):
        assert self._validate(gui_mod, "DEVICE", category) is None


# ===========================================================================
# Module-level constants sanity
# ===========================================================================
class TestModuleConstants:
    """Basic sanity checks on constants used throughout the GUI."""

    def test_tech_categories_are_correct(self, gui_mod):
        assert set(gui_mod.TECH_CATEGORIES) == {"GaN", "IGBT", "SiC-MOSFET", "Si-MOSFET"}

    def test_color_constants_are_hex_strings(self, gui_mod):
        for name in ("CLR_HDR", "CLR_BTN", "CLR_ODD", "CLR_EVEN",
                     "CLR_DIFF", "CLR_GREEN", "CLR_RED"):
            val = getattr(gui_mod, name)
            assert isinstance(val, str) and val.startswith("#"), \
                f"{name} = {val!r} is not a hex color string"

    def test_chart_axis_map_has_required_entries(self, gui_mod):
        fragments = {row[0] for row in gui_mod._CHART_AXIS_MAP}
        for required in ("graph_v_i", "graph_i_e", "c_iss", "c_oss"):
            assert required in fragments, f"_CHART_AXIS_MAP missing entry for {required!r}"