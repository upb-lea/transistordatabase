# Product Requirements Document (PRD)

## Product: Transistor Database v1.0

### Vision

A unified Python toolkit for power semiconductor device characterization, simulation model export, and topology-level loss analysis. Combines the data management capabilities of the original transistordatabase with analytical models and topology-specific calculations.

### Target Users

- Power electronics engineers designing converters
- Researchers characterizing semiconductor devices
- Students learning power electronics
- Simulation tool users (PLECS, GeckoCIRCUITS, MATLAB/Simulink, LTSpice)

### Core Capabilities

#### 1. Device Data Management
- Store transistor parameters in structured JSON or MongoDB
- Import from PLECS XML, Digikey catalogs, CSV, and datasheets
- Validate data consistency and completeness
- Virtual datasheet generation (HTML/PDF)

#### 2. Simulation Model Export
- **GeckoCIRCUITS** (.scl) — conduction + switching loss curves
- **PLECS** (.xml) — thermal and electrical models
- **MATLAB/Simulink** (.m) — loss lookup tables
- **LTSpice** (.lib) — SPICE device models

#### 3. Analytical Models
- **Biela switching loss model** — analytical E_on/E_off estimation
- **Gate charge model** — switching time and loss prediction
- **IGBT tail current model** — turn-off energy with tail current
- **Rg formula** — gate resistance dependent switching energy

#### 4. Waveform-Based Loss Calculation
- Conduction losses from arbitrary i(t) waveforms
- Switching losses from gate edge detection
- ZVS/ZCS detection and soft-switching loss reduction
- Integration with topology models

#### 5. Topology Analysis
- **Bridgeless PFC** — boost PFC loss analysis
- **Dual Active Bridge (DAB)** — phase-shift modulation losses
- **LLC Resonant Converter** — resonant transition losses
- **Series Resonant Converter (SRC)** — ZVS range analysis

#### 6. User Interfaces
- **PyQt5 Desktop GUI** — full-featured transistor viewer/editor
- **Web Interface** — Vue 3 + FastAPI for browser-based access
- **Python API** — programmatic access for scripts and notebooks

### Non-Functional Requirements

| Requirement | Target |
|---|---|
| Python version | >= 3.10 |
| Test coverage | > 85% |
| Lint violations | 0 (ruff check) |
| Dead code | < 10 false positives (vulture) |
| Import time | < 2s for core module |
| JSON load time | < 100ms per transistor |

### Data Model

See `docs/ARCHITECTURE.md` for the full domain model. Key entities:

- **Transistor** — root aggregate with metadata, ratings, components
- **Switch / Diode** — components with channel data, switching losses, thermal model
- **ChannelCharacteristics** — V-I curves at specific temperature and gate voltage
- **SwitchingLossData** — E_on/E_off/E_rr energy curves
- **FosterThermalModel** — transient thermal RC network

### Milestones

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Core refactoring (models, services, interfaces) | In Progress |
| Phase 1 | PLECS import, analytical models, Rg formula | Planned |
| Phase 2 | Waveform losses, topology analysis | Planned |
| Phase 3 | Legacy migration, GUI refactor | Planned |
| Phase 4 | LTSpice DPT, Digikey catalog, docs | Planned |
| Phase 5 | Testing gate, v1.0 release | Planned |

### Success Criteria

1. All existing tests pass after refactoring
2. Core module importable without PyQt5
3. Backend services fully implement core ABCs
4. Export functions produce identical output to legacy
5. Web API functional for CRUD + basic analysis
