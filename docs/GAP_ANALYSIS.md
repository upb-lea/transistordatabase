# Gap Analysis: `archive_ntbees2/sc/` vs `transistordatabase/`

## Overview

The archive `sc/` package (`semiconductors`, v0.0.0, by tinix84) is a complementary codebase focused on **analytical switching models**, **PLECS XML parsing**, **LTspice DPT automation**, and **Digikey catalog integration**. This document maps what it has against the current `transistordatabase` and defines a phased merge roadmap.

---

## Feature Matrix

| Feature Area | Archive (`sc/`) | Current (`transistordatabase`) | Gap Severity |
|---|---|---|---|
| **PLECS XML import** | Full parser (`scplecs.py`), 371 device files across Wolfspeed, Infineon, GaN Systems | Export only (Jinja2 template-based) | **Critical** |
| **Analytical switching models** | ETH Biela capacitive model + gate-charge 4-interval model | LUT interpolation only | **Major** |
| **Rg formula scaling** | `E/(a*Rg+b)` per-device formulas from PLECS | Single Rg per measurement | **Major** |
| **Waveform-based loss calc** | `calc_Psw_Semi_v2()` from time-domain signals with gate-edge detection | Average operating-point only | **Major** |
| **4D temperature LUTs** | I x V x T x Rg interpolation | 2D I x V at fixed T | **Major** |
| **IGBT transient models** | di/dt, dv/dt analytical (`igbt.py`) | None | **Moderate** |
| **LTspice DPT automation** | RAW file parser + Eon/Eoff extraction | Manual measurement entry | **Moderate** |
| **Digikey catalog data** | 500 Si MOSFETs + 100 GaN FETs from CSV | ~25 example devices | **Moderate** |
| **Topology calculators** | 7 converters (PFC, DAB, LLC, SRC, 6-switch PFC) | 3 converters (buck, boost, buck-boost) | **Moderate** |
| **Interactive visualization** | Bokeh/Plotly 3D surfaces, waveform viewer | Matplotlib (static), Chart.js (web) | **Low** |
| **Capacitance integration** | `calc_mosfet_capacitances()` with trapz over C(V) | `calc_v_eoss()` exists but simpler | **Low** |
| **MATLAB interop** | Native .m functions, SemiconductorEditor.m | `.mat` export only | **Low** |
| **Data container model** | `ScData` versioned generic model | JSON dict -> nested dataclasses | **Low** (TDB is richer) |

---

## Archive Source File Map

```
sc/
├── semiconductors/                    # Core Python package
│   ├── scplecs.py                     # PLECS XML parser (ScDataPlecs class)
│   ├── scdata.py                      # Generic data container (versioned)
│   ├── helpers.py                     # calc_Pcond_Semi, calc_Psw_Semi_v2
│   ├── biela_swlosses.py              # ETH Biela analytical switching model
│   ├── mosfet.py                      # Gate-charge 4-interval turn-on model
│   ├── igbt.py                        # IGBT di/dt, dv/dt transient model
│   ├── transistor.py                  # Base transistor class
│   ├── diode.py                       # Diode parameter fitting
│   └── helpers_plot.py                # Bokeh/Plotly visualization
│
├── db/                                # Device database
│   ├── plecs/                         # 371 PLECS XML files
│   │   ├── Wolfspeed_MOSFET_PLECS_10_2019/   # 63 SiC MOSFETs
│   │   ├── WS_Diodes/                         # 62 SiC Diodes
│   │   ├── GaN-Systems/                       # 8 GaN HEMTs
│   │   ├── Infineon_IGBT/                     # 229 Si IGBTs
│   │   └── WS_Modue_PLECS_07_27_18/          # 10 SiC modules
│   ├── 201210_mos_digikey.csv         # 500 Si MOSFETs parametric
│   └── 201210_gan_digikey.csv         # 100 GaN FETs parametric
│
├── matlab_func/                       # Topology calculators
│   ├── Bridgeless_PFC/
│   ├── DCDC_DAB/
│   ├── DCDC_SRC_ZVS/
│   ├── LLC/
│   └── PFC-SixSwitch/
│
├── utils/dpt/                         # Double-pulse tester
│   ├── ltspice_dpt.py                 # LTspice RAW/log parser
│   └── helpers_plot.py                # Waveform viewer
│
└── tests/
    ├── test_basic.py
    ├── test_igbt.py
    └── test_xmlplecs.py
```

---

## What transistordatabase already covers (no gap)

- MongoDB + JSON dual storage with DatabaseManager
- PyQt5 desktop GUI (9,600 LOC)
- Vue 3 + FastAPI web GUI (search, compare, plot, export, dark mode)
- Export to GeckoCIRCUITS, PLECS, Simulink, MATLAB, virtual datasheet
- Validation framework with completeness scoring
- Comparison service (multi-transistor)
- Foster thermal model support
- SOA curves, gate charge curves, temperature-dependent Rds_on
- Core architecture refactor with repository/service patterns
- Vercel deployment + CI/CD

---

## Features NOT recommended for merge

| Archive feature | Reason to skip |
|---|---|
| `scdata.py` generic container | TDB nested dataclass model is more mature and typed |
| MATLAB `.m` files | Maintenance burden; Python equivalents preferred |
| Bokeh visualization | Web GUI uses Chart.js; Bokeh adds redundant dependency |
| `SemiconductorEditor.m` | PyQt5 + Vue GUIs already cover this use case |

---

## Merge Roadmap

### Phase 1 — PLECS XML Import (Critical, foundational)

**Goal**: Import 371 PLECS XML device files into TDB JSON format.

| Step | Task | Source | Target |
|---|---|---|---|
| 1.1 | Port `scplecs.py` XML parser | `sc/semiconductors/scplecs.py` | `transistordatabase/plecs_importer.py` |
| 1.2 | Map PLECS fields to Transistor/Switch/Diode dataclasses | `scplecs.py` property mappings | `database_manager.py` converter |
| 1.3 | Handle vendor quirks (Wolfspeed uJ scale, Infineon J scale, temperature sentinels 900/1000C) | Embedded in `scplecs.py` | Importer logic |
| 1.4 | Add `xmltodict` dependency | — | `setup.py` |
| 1.5 | Batch-convert 371 PLECS XMLs to JSON | `sc/db/plecs/` | fileexchange or examples |
| 1.6 | Add `DatabaseManager.import_from_plecs(path)` method | — | `database_manager.py` |
| 1.7 | Tests: round-trip import/export | `sc/tests/test_xmlplecs.py` | `tests/test_plecs_import.py` |

**New dependency**: `xmltodict`
**Risk**: PLECS 4D LUTs (I x V x T with Rg formula) don't map cleanly to current `SwitchEnergyData` which stores single graph types. May need schema extension.

### Phase 2 — Analytical Switching Models (Major, design enabler)

**Goal**: Predict switching losses from datasheet parameters without measurements.

| Step | Task | Source | Target |
|---|---|---|---|
| 2.1 | Port Biela capacitive model | `sc/semiconductors/biela_swlosses.py` | `transistordatabase/analytical_models.py` |
| 2.2 | Port gate-charge MOSFET model (4-interval) | `sc/semiconductors/mosfet.py` | Same file |
| 2.3 | Port IGBT di/dt, dv/dt model | `sc/semiconductors/igbt.py` | Same file |
| 2.4 | Add `Transistor.calc_switching_energy_analytical(Vds, Id, Rg, T)` | — | `transistor.py` |
| 2.5 | Add transconductance fitting | `biela_swlosses.py` | `helper_functions.py` |
| 2.6 | Validation tests against known LUT data | — | `tests/test_analytical_models.py` |

**New dependencies**: None (numpy/scipy already present)

### Phase 3 — Rg Formula Support (Major, schema change)

**Goal**: Store and evaluate gate-resistance-dependent energy scaling.

| Step | Task | Source | Target |
|---|---|---|---|
| 3.1 | Add `r_g_formula` optional field to `SwitchEnergyData` | PLECS formula pattern | `data_classes.py` |
| 3.2 | Implement formula evaluation: `E_scaled = E / (a*Rg + b)` | `scplecs.py` | `data_classes.py` |
| 3.3 | Update `export_plecs()` to emit Rg formulas | — | `transistor.py` |
| 3.4 | Update validation for new field | — | `checker_functions.py` |
| 3.5 | Backward-compatible JSON schema update | — | `database_manager.py` |

**Risk**: Schema migration. Existing JSON files must remain loadable. New field must be optional.

### Phase 4 — Waveform-Based Loss Calculator (Major, unlocks resonant topologies)

**Goal**: Calculate losses from time-domain current/voltage/gate waveforms.

| Step | Task | Source | Target |
|---|---|---|---|
| 4.1 | Port `calc_Pcond_Semi()` | `sc/semiconductors/helpers.py` | `transistordatabase/waveform_losses.py` |
| 4.2 | Port `calc_Psw_Semi_v2()` with gate-edge detection | Same | Same |
| 4.3 | Add ZVS/ZCS detection (zero-crossing before gate edge) | Same | Same |
| 4.4 | Add `Transistor.calc_losses_from_waveforms(time, vds, id, gate)` | — | `transistor.py` |
| 4.5 | Tests with known converter waveforms | — | `tests/test_waveform_losses.py` |

**New dependencies**: None

### Phase 5 — Extended Topology Library (Moderate)

**Goal**: Add advanced converter topologies.

| Step | Task | Source | Target |
|---|---|---|---|
| 5.1 | Port Bridgeless PFC calculator | `sc/matlab_func/Bridgeless_PFC/` | `transistordatabase/topologies/bridgeless_pfc.py` |
| 5.2 | Port DAB (Dual Active Bridge) | `sc/matlab_func/DCDC_DAB/` | `transistordatabase/topologies/dab.py` |
| 5.3 | Port LLC resonant | `sc/matlab_func/LLC/` | `transistordatabase/topologies/llc.py` |
| 5.4 | Port SRC ZVS | `sc/matlab_func/DCDC_SRC_ZVS/` | `transistordatabase/topologies/src_zvs.py` |
| 5.5 | Add topology API endpoints | — | `gui_web/backend/main.py` |
| 5.6 | Add topology Vue components | — | Vue frontend |

**Depends on**: Phase 4

### Phase 6 — LTspice DPT Automation (Moderate, independent)

**Goal**: Auto-extract Eon/Eoff LUTs from LTspice double-pulse simulations.

| Step | Task | Source | Target |
|---|---|---|---|
| 6.1 | Port RAW file parser | `sc/utils/dpt/ltspice_dpt.py` | `transistordatabase/utils/ltspice_dpt.py` |
| 6.2 | Port log file parser | Same | Same |
| 6.3 | Add `Transistor.import_dpt_ltspice(raw_file)` | — | `transistor.py` |
| 6.4 | Port DPT waveform viewer to web GUI | `sc/utils/dpt/helpers_plot.py` | Vue component |

**New dependency**: `PyLTSpice` (optional, soft import)

### Phase 7 — Digikey Catalog Integration (Moderate, independent)

**Goal**: Bulk-import device catalog data for screening.

| Step | Task | Source | Target |
|---|---|---|---|
| 7.1 | Add CSV catalog parser | `sc/db/*.csv` | `transistordatabase/catalog_importer.py` |
| 7.2 | Map catalog fields to Transistor metadata | — | Importer logic |
| 7.3 | Add FOM calculations (Rds x Qg, Rds x Coss) | — | `helper_functions.py` |
| 7.4 | Add catalog search/filter to web GUI | — | Vue component |

---

## Dependency Summary

| Phase | New pip dependency | Required? |
|---|---|---|
| 1 | `xmltodict` | Yes |
| 2-5 | None | — |
| 6 | `PyLTSpice` | Optional (soft import) |
| 7 | None | — |

## Branch Strategy

```
main
 ├── feature/plecs-import          (Phase 1)
 ├── feature/analytical-models     (Phase 2, parallel with Phase 1)
 ├── feature/rg-formula            (Phase 3, after Phase 1)
 ├── feature/waveform-losses       (Phase 4, after Phase 2)
 ├── feature/topologies            (Phase 5, after Phase 4)
 ├── feature/ltspice-dpt           (Phase 6, independent)
 └── feature/catalog-import        (Phase 7, independent)
```

Phases 1+2 can proceed in parallel. Phases 6+7 are independent. Phases 3->4->5 are sequential.
