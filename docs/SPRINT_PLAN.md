# Sprint Plan for Haiku Agents

This plan breaks the merge roadmap (see `GAP_ANALYSIS.md`) into atomic tasks sized for Claude Haiku agents. Each task has explicit inputs, outputs, and acceptance criteria so Haiku can execute autonomously.

---

## Conventions

- **Agent model**: `haiku` unless marked `sonnet` (for tasks requiring multi-file reasoning)
- **Task ID format**: `S{sprint}.{seq}` (e.g., S1.3 = Sprint 1, task 3)
- **Acceptance**: Every task must produce a file diff or new file that passes `ruff check` and existing tests
- **Context rule**: Each Haiku prompt must include the exact source file path and target file path. Never assume Haiku knows the repo layout.

---

## Sprint 1 — PLECS XML Import Foundation (Phase 1)

**Branch**: `feature/plecs-import`
**Goal**: Working PLECS XML -> TDB JSON converter for a single device type (SiC MOSFET)

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S1.1 | Add `xmltodict` to `setup.py` dependencies | haiku | Read `setup.py`, add `xmltodict>=0.13.0` to `install_requires` list, preserve existing order | `setup.py` | `setup.py` (edited) | `pip install -e .` succeeds; `import xmltodict` works |
| S1.2 | Scaffold `plecs_importer.py` with type stubs | haiku | Create `transistordatabase/plecs_importer.py` with: class `PlecsImporter` with methods `parse_xml(filepath) -> dict`, `convert_to_transistor_dict(plecs_dict) -> dict`, `import_file(filepath) -> Transistor`. Add docstrings, type hints, raise `NotImplementedError`. | — | `transistordatabase/plecs_importer.py` | `ruff check` passes; file importable |
| S1.3 | Implement XML parsing core | sonnet | Read `sc/semiconductors/scplecs.py` (full file). Port the XML loading and property extraction logic into `PlecsImporter.parse_xml()`. Use `xmltodict.parse()`. Extract: partnumber, vendor, package_class, semiconductor_type, conduction loss LUTs (temperature_axis, current_axis, voltage_drop_lut), switching energy LUTs (Eon/Eoff axes, scale, formula), thermal resistance. Return a flat dict with these keys. | `sc/semiconductors/scplecs.py`, `transistordatabase/plecs_importer.py` | `transistordatabase/plecs_importer.py` (edited) | Can parse `sc/db/plecs/Wolfspeed_MOSFET_PLECS_10_2019/C3M0016120K.xml` and return dict with all fields populated |
| S1.4 | Handle vendor-specific scale factors | haiku | In `plecs_importer.py`, in `parse_xml()`, add logic: if `scale_Eon` == `"1e-06"` multiply all energy values by 1e-6 to normalize to Joules. Same for `scale_Eoff`, `scale_Err`. Add comment explaining Wolfspeed uses uJ, Infineon uses J. | `transistordatabase/plecs_importer.py` | Same (edited) | Wolfspeed device energies in J (not uJ); Infineon device energies unchanged |
| S1.5 | Handle temperature sentinel clipping | haiku | In `plecs_importer.py`, after extracting temperature axes, filter out sentinel values >= 900. These are extrapolation guards in PLECS (900C, 1000C are not real). Clip corresponding LUT rows/columns. | `transistordatabase/plecs_importer.py` | Same (edited) | Temperature axes contain only physically real values (< 300C typically) |
| S1.6 | Map PLECS conduction data to TDB ChannelData | sonnet | Read `transistordatabase/data_classes.py` ChannelData class and `transistordatabase/switch.py` Switch class. In `PlecsImporter.convert_to_transistor_dict()`, map PLECS `voltage_drop_lut` (2D: temp x current -> voltage) to TDB ChannelData format: one ChannelData per temperature row, with `graph_v_i` = numpy array of [voltage, current] pairs, `t_j` = temperature, `v_g_on` from metadata. | `transistordatabase/plecs_importer.py`, `transistordatabase/data_classes.py`, `transistordatabase/switch.py` | `transistordatabase/plecs_importer.py` (edited) | Produces valid ChannelData dicts that pass `isvalid_dict()` |
| S1.7 | Map PLECS switching energy to TDB SwitchEnergyData | sonnet | Read `transistordatabase/data_classes.py` SwitchEnergyData class. Map PLECS Eon/Eoff 2D LUTs (current x voltage at each temp) to TDB `SwitchEnergyData` with `dataset_type="graph_i_e"`, `graph_i_e` = [current, energy] at reference voltage, `v_supply` from voltage axis, `t_j` from temp axis, `r_g` = None (formula-based). Create one SwitchEnergyData per temperature. | `transistordatabase/plecs_importer.py`, `transistordatabase/data_classes.py` | `transistordatabase/plecs_importer.py` (edited) | Produces valid SwitchEnergyData dicts |
| S1.8 | Map PLECS thermal model to TDB FosterThermalModel | haiku | Read `transistordatabase/data_classes.py` FosterThermalModel class. In converter, map PLECS `forwardThermalResistance` (Cauer RC ladder sum) to `r_th_total`. If individual R/C pairs available, map to `r_th_vector` and `c_th_vector`. | `transistordatabase/plecs_importer.py`, `transistordatabase/data_classes.py` | `transistordatabase/plecs_importer.py` (edited) | FosterThermalModel dict is valid |
| S1.9 | Assemble full Transistor dict | sonnet | In `convert_to_transistor_dict()`, assemble complete Transistor dict from mapped sub-dicts: set `name` = partnumber, `type` from semiconductor_type mapping (MOSFET/IGBT/SiC-MOSFET/GaN), `manufacturer` = vendor, `switch` with channel + e_on + e_off + thermal, `diode` with channel + e_rr + thermal if present. Read `transistordatabase/transistor.py` constructor to see required fields. | `transistordatabase/plecs_importer.py`, `transistordatabase/transistor.py` | `transistordatabase/plecs_importer.py` (edited) | `DatabaseManager().convert_dict_to_transistor_object(result)` succeeds |
| S1.10 | Add `import_file()` end-to-end method | haiku | Implement `PlecsImporter.import_file(filepath)`: call `parse_xml()`, then `convert_to_transistor_dict()`, then `DatabaseManager.convert_dict_to_transistor_object()`. Return Transistor object. Add error handling for missing/malformed XML. | `transistordatabase/plecs_importer.py` | Same (edited) | `PlecsImporter().import_file("path/to/C3M0016120K.xml")` returns valid Transistor |
| S1.11 | Add `DatabaseManager.import_from_plecs()` | haiku | Read `transistordatabase/database_manager.py`. Add method `import_from_plecs(self, filepath: str) -> None` that uses `PlecsImporter.import_file()` then calls `self.save_transistor()`. Add Sphinx docstring. | `transistordatabase/database_manager.py`, `transistordatabase/plecs_importer.py` | `transistordatabase/database_manager.py` (edited) | Method exists, docstring present, `ruff check` passes |
| S1.12 | Write unit tests for PLECS import | sonnet | Create `tests/test_plecs_import.py`. Test: (1) parse single Wolfspeed SiC MOSFET XML, assert partnumber/vendor/type correct. (2) parse Infineon IGBT XML, assert energy scale is J not uJ. (3) round-trip: import XML -> export PLECS -> compare structure. (4) temperature sentinels filtered. (5) malformed XML raises appropriate error. Use pytest fixtures. Copy one small XML file to `tests/test_data/` for CI. | `transistordatabase/plecs_importer.py`, `sc/db/plecs/` | `tests/test_plecs_import.py`, `tests/test_data/sample_plecs.xml` | `pytest tests/test_plecs_import.py` passes |
| S1.13 | Update `__init__.py` exports | haiku | Add `from transistordatabase.plecs_importer import *` to `transistordatabase/__init__.py` | `transistordatabase/__init__.py` | Same (edited) | `from transistordatabase import PlecsImporter` works |

---

## Sprint 2 — Analytical Switching Models (Phase 2)

**Branch**: `feature/analytical-models` (can start parallel to Sprint 1)
**Goal**: Working Biela model + gate-charge MOSFET model callable from Transistor

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S2.1 | Scaffold `analytical_models.py` | haiku | Create `transistordatabase/analytical_models.py` with classes: `BielaModel` (methods: `calc_mosfet_capacitances`, `calc_transconductance`, `calc_turn_on_energy`, `calc_turn_off_energy`), `GateChargeModel` (methods: `calc_turnon_transition`, `calc_turnoff_transition`), `IgbtModel` (methods: `calc_didt`, `calc_dvdt`). All raise `NotImplementedError`. Add docstrings and type hints. | — | `transistordatabase/analytical_models.py` | `ruff check` passes; importable |
| S2.2 | Port Biela capacitance integration | haiku | Read `sc/semiconductors/biela_swlosses.py` method `calc_mosfet_capacitances`. Port to `BielaModel.calc_mosfet_capacitances(Vds: np.ndarray, Ciss: np.ndarray, Crss: np.ndarray, Coss: np.ndarray, V0: float)`. Use `np.trapz` for equivalent capacitance integration. Return `(ciss_eq, crss_eq, coss_eq)`. | `sc/semiconductors/biela_swlosses.py`, `transistordatabase/analytical_models.py` | `transistordatabase/analytical_models.py` (edited) | Returns correct equivalent capacitances for known test input |
| S2.3 | Port Biela transconductance fitting | haiku | Read `sc/semiconductors/biela_swlosses.py` method `calc_transconductance_parameters`. Port to `BielaModel.calc_transconductance(vgs: np.ndarray, ich: np.ndarray, vth: float)`. Use `scipy.optimize.curve_fit` with the `func_ich_vgs` model. Return `(gm, x, k1, k2)`. | `sc/semiconductors/biela_swlosses.py`, `transistordatabase/analytical_models.py` | Same (edited) | Curve fit converges for known channel data |
| S2.4 | Port Biela turn-on/turn-off energy | sonnet | Read `sc/semiconductors/biela_swlosses.py` classes `Turnon` and `Turnoff`. Port `calc_ETon` and `calc_EToff` to `BielaModel`. Include: overshoot current `calc_Ioss`, rise/fall time calculations `calc_tri`, `calc_tfv`, reverse recovery `Erf`, `Ers`. All intermediate calculations as private methods. | `sc/semiconductors/biela_swlosses.py`, `transistordatabase/analytical_models.py` | Same (edited) | `calc_turn_on_energy(Vds, Id, Rg, Ciss_eq, Crss_eq, gm, Vth, Vg)` returns energy in Joules |
| S2.5 | Port gate-charge MOSFET model | sonnet | Read `sc/semiconductors/mosfet.py`. Port 4-interval turn-on model to `GateChargeModel.calc_turnon_transition(Vgon, Vth, gm, Rdrv, Cgd, Cgs, Cds, Vds, Io)`. Return `(time_wfm, Id_wfm, Vgs_wfm, Vds_wfm)` as numpy arrays. Include t1 (sub-threshold), t2 (current rise), t3 (Miller plateau), t4 (post-plateau). | `sc/semiconductors/mosfet.py`, `transistordatabase/analytical_models.py` | Same (edited) | Returns 4 waveform arrays with correct physical behavior |
| S2.6 | Port IGBT transient model | haiku | Read `sc/semiconductors/igbt.py`. Port di/dt and dv/dt calculations to `IgbtModel.calc_didt(...)` and `IgbtModel.calc_dvdt(...)`. Keep the physics equations, adapt to TDB naming conventions. | `sc/semiconductors/igbt.py`, `transistordatabase/analytical_models.py` | Same (edited) | Returns di/dt in A/s, dv/dt in V/s |
| S2.7 | Add `Transistor.calc_switching_energy_analytical()` | sonnet | Read `transistordatabase/transistor.py`. Add method `calc_switching_energy_analytical(self, v_supply, i_load, r_g, t_j)` that: (1) extracts Ciss/Crss/Coss from `self.c_iss`/`c_rss`/`c_oss`, (2) extracts gm from channel data via `BielaModel.calc_transconductance`, (3) calls `BielaModel.calc_turn_on_energy` / `calc_turn_off_energy`. Return dict `{"e_on": float, "e_off": float, "e_total": float}`. Import `BielaModel` at top. Add Sphinx docstring with example. | `transistordatabase/transistor.py`, `transistordatabase/analytical_models.py` | `transistordatabase/transistor.py` (edited) | Method callable on existing Transistor objects with capacitance data |
| S2.8 | Write unit tests | sonnet | Create `tests/test_analytical_models.py`. Test: (1) Biela capacitance integration with known C(V) curves. (2) Transconductance fit with synthetic channel data. (3) Turn-on energy for C3M0016120K at 800V/20A — compare against datasheet Eon. (4) Gate-charge model waveform shapes (monotonic Vgs rise, Vds fall during Miller). (5) IGBT di/dt within expected range. Use `pytest.approx` with 20% tolerance for analytical vs datasheet. | `transistordatabase/analytical_models.py` | `tests/test_analytical_models.py` | `pytest tests/test_analytical_models.py` passes |
| S2.9 | Update `__init__.py` exports | haiku | Add `from transistordatabase.analytical_models import *` to `__init__.py` | `transistordatabase/__init__.py` | Same (edited) | `from transistordatabase import BielaModel` works |

---

## Sprint 3 — Rg Formula + Schema Extension (Phase 3)

**Branch**: `feature/rg-formula`
**Depends on**: Sprint 1 merged
**Goal**: SwitchEnergyData supports Rg formula scaling

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S3.1 | Add `r_g_formula` field to SwitchEnergyData | haiku | Read `transistordatabase/data_classes.py` class `SwitchEnergyData`. Add optional field `r_g_formula: Optional[str] = None` (e.g. `"E/(5.3e-5*Rg+1.167e-3)"`). Update `__init__` and `convert_to_dict()` / `from_dict()` to handle it. Must be backward-compatible: if missing in JSON, default to None. | `transistordatabase/data_classes.py` | Same (edited) | Existing tests still pass; new field serializes/deserializes |
| S3.2 | Implement formula evaluator | haiku | In `transistordatabase/helper_functions.py`, add `evaluate_rg_formula(formula: str, e_ref: float, r_g: float) -> float`. Parse formula string (format: `"E/(a*Rg+b)"`), extract coefficients, compute scaled energy. Use `re` for parsing, not `eval()`. Raise `ValueError` for unparseable formulas. | `transistordatabase/helper_functions.py` | Same (edited) | `evaluate_rg_formula("E/(5.3e-5*Rg+1.167e-3)", 1e-3, 2.5)` returns correct float |
| S3.3 | Add `SwitchEnergyData.get_energy_at_rg()` | haiku | In `data_classes.py`, add method `get_energy_at_rg(self, r_g: float) -> np.ndarray` to `SwitchEnergyData`. If `r_g_formula` is set, scale the stored energy data by the formula. If not set, return stored data unchanged. Import `evaluate_rg_formula`. | `transistordatabase/data_classes.py`, `transistordatabase/helper_functions.py` | `transistordatabase/data_classes.py` (edited) | Returns scaled energy array when formula present; original when absent |
| S3.4 | Update PLECS exporter for Rg formulas | haiku | Read `transistordatabase/transistor.py` method `export_plecs()`. If `SwitchEnergyData.r_g_formula` is set, write it into the PLECS XML template `formula_Eon` / `formula_Eoff` field. Read the template at `transistordatabase/templates/PLECS_Exporter_template_Switch.txt` to find where to insert. | `transistordatabase/transistor.py`, `transistordatabase/templates/PLECS_Exporter_template_Switch.txt` | Both (edited) | Exported PLECS contains formula field when source data has it |
| S3.5 | Update validation for r_g_formula | haiku | In `transistordatabase/checker_functions.py`, add `check_rg_formula(formula: str) -> bool` that validates the formula string format. In the SwitchEnergyData validation path, call it if field is present. | `transistordatabase/checker_functions.py` | Same (edited) | Valid formulas pass; garbage strings fail |
| S3.6 | Wire PLECS importer to populate r_g_formula | haiku | In `transistordatabase/plecs_importer.py`, when mapping PLECS Eon/Eoff data, if the XML contains `formula_Eon`/`formula_Eoff`, store it in `SwitchEnergyData.r_g_formula`. | `transistordatabase/plecs_importer.py` | Same (edited) | Imported PLECS devices retain their Rg formulas |
| S3.7 | Write tests | haiku | Create `tests/test_rg_formula.py`. Test: (1) formula parsing with valid/invalid strings. (2) energy scaling at different Rg values. (3) backward compatibility: load old JSON without formula, field is None. (4) round-trip: save with formula, load, formula preserved. | — | `tests/test_rg_formula.py` | `pytest tests/test_rg_formula.py` passes |

---

## Sprint 4 — Waveform-Based Loss Calculator (Phase 4)

**Branch**: `feature/waveform-losses`
**Depends on**: Sprint 2 merged
**Goal**: Calculate losses from time-domain waveforms

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S4.1 | Scaffold `waveform_losses.py` | haiku | Create `transistordatabase/waveform_losses.py` with functions: `calc_conduction_loss(time, current, channel_data) -> (p_avg, i_rms)`, `calc_switching_loss(time, vdc, gate, current, switch_energy_data) -> (p_sw, p_on, p_off, e_on_events, e_off_events)`, `detect_zvs_zcs(time, voltage, current, gate) -> dict`. Add docstrings, type hints, raise `NotImplementedError`. | — | `transistordatabase/waveform_losses.py` | `ruff check` passes; importable |
| S4.2 | Port conduction loss calculator | haiku | Read `sc/semiconductors/helpers.py` function `calc_Pcond_Semi`. Port to `calc_conduction_loss()`. Use `scipy.interpolate.interp1d` with channel V-I data. Calculate instantaneous power p(t) = v(i(t)) * i(t), then average. Also return I_rms. Input `channel_data` should accept a TDB ChannelData dict with `graph_v_i`. | `sc/semiconductors/helpers.py`, `transistordatabase/waveform_losses.py` | `transistordatabase/waveform_losses.py` (edited) | Correct Pcond for sinusoidal current waveform through known V-I curve |
| S4.3 | Port switching loss calculator | sonnet | Read `sc/semiconductors/helpers.py` function `calc_Psw_Semi_v2`. Port to `calc_switching_loss()`. Detect gate rising/falling edges by comparing shifted gate signal. At each edge, interpolate switching energy from TDB `SwitchEnergyData.graph_i_e` at instantaneous current, scale by `vdc / v_supply_ref`. Sum over period. Return per-event energies too. | `sc/semiconductors/helpers.py`, `transistordatabase/waveform_losses.py` | Same (edited) | Correct Psw for hard-switched buck converter waveform |
| S4.4 | Implement ZVS/ZCS detection | haiku | In `detect_zvs_zcs()`, check if drain-source voltage crosses zero before turn-on gate edge (ZVS) or if current crosses zero before turn-off gate edge (ZCS). Return dict with `{"zvs_events": list[float], "zcs_events": list[float], "hard_switch_events": list[float]}` where values are timestamps. | `transistordatabase/waveform_losses.py` | Same (edited) | Correctly classifies events for LLC-type waveform (turn-on = ZVS, turn-off = ZCS) |
| S4.5 | Add `Transistor.calc_losses_from_waveforms()` | haiku | In `transistordatabase/transistor.py`, add method `calc_losses_from_waveforms(self, time, v_dc, i_load, gate_signal, t_j)`. Select appropriate channel and switching energy data for `t_j`, then call `calc_conduction_loss()` and `calc_switching_loss()`. Return dict with `p_cond`, `p_sw_on`, `p_sw_off`, `p_total`, `i_rms`, `switching_events`. | `transistordatabase/transistor.py`, `transistordatabase/waveform_losses.py` | `transistordatabase/transistor.py` (edited) | Method callable, docstring present |
| S4.6 | Write tests | sonnet | Create `tests/test_waveform_losses.py`. Test: (1) conduction loss with DC current = simple P = V*I check. (2) switching loss with square gate at known frequency = P_sw = f * (Eon + Eoff). (3) ZVS detection with synthetic LLC waveform. (4) ZCS detection. (5) edge case: no switching events in window. Generate synthetic waveforms with numpy. | — | `tests/test_waveform_losses.py` | `pytest tests/test_waveform_losses.py` passes |
| S4.7 | Update `__init__.py` exports | haiku | Add `from transistordatabase.waveform_losses import *` to `__init__.py` | `transistordatabase/__init__.py` | Same (edited) | Importable from top-level |

---

## Sprint 5 — Extended Topologies (Phase 5)

**Branch**: `feature/topologies`
**Depends on**: Sprint 4 merged
**Goal**: Add DAB, LLC, PFC topology calculators

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S5.1 | Create `topologies/` package | haiku | Create `transistordatabase/topologies/__init__.py` with docstring. Create empty files: `bridgeless_pfc.py`, `dab.py`, `llc.py`, `src_zvs.py`. Each with module docstring and placeholder class. | — | 5 new files | `ruff check` passes; `from transistordatabase.topologies import dab` works |
| S5.2 | Port Bridgeless PFC | sonnet | Read `sc/matlab_func/Bridgeless_PFC/calc_bridgeless_semiconductor_loss.py`. Port to `transistordatabase/topologies/bridgeless_pfc.py`. Class `BridgelessPFC` with `__init__(self, v_in, v_out, p_out, f_sw, f_line)` and `calc_losses(self, transistor: Transistor) -> dict`. Use `calc_losses_from_waveforms()` internally. Generate PFC current/gate waveforms analytically. | `sc/matlab_func/Bridgeless_PFC/`, `transistordatabase/topologies/bridgeless_pfc.py` | Same (edited) | Returns dict with per-switch and total losses |
| S5.3 | Port DAB | sonnet | Read `sc/matlab_func/DCDC_DAB/`. Port to `transistordatabase/topologies/dab.py`. Class `DualActiveBridge` with `__init__(self, v_in, v_out, p_out, f_sw, n_turns, l_leak)` and `calc_losses(self, transistor_primary, transistor_secondary) -> dict`. | `sc/matlab_func/DCDC_DAB/`, `transistordatabase/topologies/dab.py` | Same (edited) | Returns losses for both bridges |
| S5.4 | Port LLC | sonnet | Read `sc/matlab_func/LLC/`. Port to `transistordatabase/topologies/llc.py`. Class `LLCConverter` with appropriate init params and `calc_losses()`. Must use ZVS detection from waveform_losses for primary side. | `sc/matlab_func/LLC/`, `transistordatabase/topologies/llc.py` | Same (edited) | ZVS events correctly detected; primary turn-on loss near zero |
| S5.5 | Port SRC ZVS | sonnet | Read `sc/matlab_func/DCDC_SRC_ZVS/`. Port to `transistordatabase/topologies/src_zvs.py`. Class `SeriesResonantZVS`. | `sc/matlab_func/DCDC_SRC_ZVS/`, `transistordatabase/topologies/src_zvs.py` | Same (edited) | Returns losses with soft-switching accounted for |
| S5.6 | Write tests for all topologies | sonnet | Create `tests/test_topologies.py`. Test each topology with a known operating point and verify: (1) loss values are positive and physically reasonable, (2) efficiency is between 90-99.9%, (3) ZVS topologies show near-zero turn-on loss, (4) total loss = sum of component losses. Use example transistors from `tests/test_data/`. | — | `tests/test_topologies.py` | `pytest tests/test_topologies.py` passes |
| S5.7 | Add topology API endpoints | haiku | In `transistordatabase/gui_web/backend/main.py`, add POST endpoints: `/api/topology/bridgeless-pfc`, `/api/topology/dab`, `/api/topology/llc`, `/api/topology/src-zvs`. Each accepts JSON body with operating parameters + transistor name(s), loads transistor(s), runs calculator, returns loss breakdown. Follow pattern of existing topology endpoint. | `transistordatabase/gui_web/backend/main.py` | Same (edited) | Endpoints return 200 with loss dict |

---

## Sprint 6 — LTspice DPT Automation (Phase 6, independent)

**Branch**: `feature/ltspice-dpt`
**Goal**: Import switching energy data from LTspice double-pulse simulations

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S6.1 | Scaffold `utils/` package and `ltspice_dpt.py` | haiku | Create `transistordatabase/utils/__init__.py` and `transistordatabase/utils/ltspice_dpt.py` with class `LtspiceDptParser` with methods: `parse_log(filepath) -> DataFrame`, `parse_raw(filepath) -> dict`, `extract_switching_energy(time, vds, id) -> (Eon, Eoff)`. Stubs with docstrings. | — | 2 new files | Importable, `ruff check` passes |
| S6.2 | Port log file parser | haiku | Read `sc/utils/dpt/ltspice_dpt.py` function `import_ltspice_log`. Port to `LtspiceDptParser.parse_log()`. Use regex to extract `.step` parameters (idc, vdc) and Eon/Eoff measurements. Return pandas DataFrame with columns: step, current, voltage, eon, eoff. | `sc/utils/dpt/ltspice_dpt.py`, `transistordatabase/utils/ltspice_dpt.py` | Same (edited) | Parses sample log file correctly |
| S6.3 | Port switching energy extraction | haiku | Read `sc/utils/dpt/ltspice_dpt.py` function `calc_sw_losses_ltspice`. Port to `extract_switching_energy()`. Calculate instantaneous loss = vds*id - rdson*id^2, clip negative, integrate with `np.trapz` around turn-on/turn-off windows. Return (Eon, Eoff) in Joules. | `sc/utils/dpt/ltspice_dpt.py`, `transistordatabase/utils/ltspice_dpt.py` | Same (edited) | Returns Eon/Eoff within 10% of LTspice .meas values |
| S6.4 | Add `Transistor.import_dpt_ltspice()` | haiku | In `transistordatabase/transistor.py`, add method `import_dpt_ltspice(self, log_filepath: str)`. Parse log, create `SwitchEnergyData` objects for each (voltage, temperature) combination, append to `self.switch.e_on` / `self.switch.e_off`. Soft-import PyLTSpice: wrap in try/except ImportError with helpful message. | `transistordatabase/transistor.py`, `transistordatabase/utils/ltspice_dpt.py` | `transistordatabase/transistor.py` (edited) | Method works with PyLTSpice installed; raises clear error without it |
| S6.5 | Write tests | haiku | Create `tests/test_ltspice_dpt.py`. Create a minimal synthetic log file in `tests/test_data/sample_dpt.log` with 3 steps. Test: (1) parse_log returns correct DataFrame shape. (2) extract_switching_energy with synthetic vds*id waveform. (3) import_dpt_ltspice adds correct number of SwitchEnergyData entries. | — | `tests/test_ltspice_dpt.py`, `tests/test_data/sample_dpt.log` | `pytest tests/test_ltspice_dpt.py` passes |

---

## Sprint 7 — Digikey Catalog Integration (Phase 7, independent)

**Branch**: `feature/catalog-import`
**Goal**: Import bulk device parameters from distributor CSV exports

| ID | Task | Agent | Prompt summary | Input files | Output files | Acceptance criteria |
|---|---|---|---|---|---|---|
| S7.1 | Scaffold `catalog_importer.py` | haiku | Create `transistordatabase/catalog_importer.py` with class `CatalogImporter` with methods: `parse_digikey_csv(filepath) -> list[dict]`, `convert_to_transistor_dicts(entries) -> list[dict]`, `calc_fom(entries, fom_type) -> list[dict]`. Stubs. | — | `transistordatabase/catalog_importer.py` | Importable, `ruff check` passes |
| S7.2 | Implement CSV parser | haiku | Read headers from `sc/db/201210_mos_digikey.csv` (first 5 rows). Implement `parse_digikey_csv()` using `csv.DictReader`. Map columns: Mfr, Part Number, Vdss, Id_25C, Rds_on, Vgs_th, Qg, Ciss, Coss, Package, Datasheet_URL. Clean numeric fields (strip units like "mOhm", "nC", "pF"). Return list of dicts. | `sc/db/201210_mos_digikey.csv`, `transistordatabase/catalog_importer.py` | Same (edited) | Parses 500+ rows, numeric fields are floats |
| S7.3 | Map to Transistor metadata | haiku | Implement `convert_to_transistor_dicts()`. For each catalog entry, create minimal Transistor dict with: `name`, `type`, `manufacturer`, `v_abs_max`, `i_abs_max`, `r_th_cs` = None, `c_oss` / `c_iss` as single-point `VoltageDependentCapacitance` if available. These are parametric-only records (no curves). | `transistordatabase/catalog_importer.py`, `transistordatabase/data_classes.py` | Same (edited) | Produces valid minimal Transistor dicts |
| S7.4 | Implement FOM calculator | haiku | Implement `calc_fom()`. Support FOM types: `"rdson_qg"` = Rds_on * Qg, `"rdson_coss"` = Rds_on * Coss, `"rdson_area"` = Rds_on * Qg * Coss (Baliga FOM variant). Sort ascending (lower = better). Return list of dicts with `part_number`, `fom_value`, `manufacturer`. | `transistordatabase/catalog_importer.py` | Same (edited) | Correct FOM ranking for known devices |
| S7.5 | Add `DatabaseManager.import_from_catalog_csv()` | haiku | In `database_manager.py`, add method that calls `CatalogImporter.parse_digikey_csv()` then `convert_to_transistor_dicts()` then batch-saves. Add `skip_existing=True` parameter. | `transistordatabase/database_manager.py`, `transistordatabase/catalog_importer.py` | `transistordatabase/database_manager.py` (edited) | Batch imports 500 devices without error |
| S7.6 | Write tests | haiku | Create `tests/test_catalog_import.py`. Create `tests/test_data/sample_catalog.csv` with 5 rows of Digikey-format data. Test: (1) CSV parsing. (2) FOM calculation and ranking. (3) Transistor dict creation. (4) batch import with skip_existing. | — | `tests/test_catalog_import.py`, `tests/test_data/sample_catalog.csv` | `pytest tests/test_catalog_import.py` passes |

---

## Execution Order & Parallelism

```
Week 1-2:  S1 (PLECS Import)  |||  S2 (Analytical Models)  |||  S6 (LTspice, independent)
Week 3:    S3 (Rg Formula, needs S1)  |||  S7 (Catalog, independent)
Week 4:    S4 (Waveform Losses, needs S2)
Week 5:    S5 (Topologies, needs S4)
```

`|||` = run in parallel

---

## Haiku Agent Invocation Template

When launching a Haiku agent for any task above, use this prompt structure:

```
You are working on the transistordatabase Python project at /home/tinix/claude_wsl/transistordatabase/.

TASK: {task description from table}

SOURCE FILE TO READ FIRST: {input file path}
TARGET FILE TO EDIT/CREATE: {output file path}

CONSTRAINTS:
- Must pass `ruff check` (line-length 88, PEP257 docstrings, Python 3.9 target)
- Must pass `pycodestyle` (line-length 160)
- Type hints required on all function parameters and return values
- Use `from __future__ import annotations` at top of new files
- Sphinx docstrings with :param:, :type:, :return:, :rtype: sections
- Use numpy/scipy (already installed), do NOT add new dependencies unless specified
- Preserve all existing code in target file; only add new code
- Do NOT modify test fixtures in existing test files

ACCEPTANCE: {acceptance criteria from table}
```

Tasks marked `sonnet` require the sonnet agent due to multi-file reasoning across complex class hierarchies.
