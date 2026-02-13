# Architecture

## Overview

The Transistor Database follows a layered clean architecture with `core/` as the domain layer, `backend/` as the application layer, and `frontend/` / `gui_web/` as presentation layers.

## Layer Diagram

```
┌───────────────────────────────────────────────────────────┐
│  Presentation Layer                                       │
│  ┌─────────────────┐  ┌───────────────────────────────┐  │
│  │ gui/ (PyQt5)    │  │ gui_web/ (Vue 3 + FastAPI)    │  │
│  │ - MainWindow    │  │ - Vue components              │  │
│  │ - PlotWidgets   │  │ - FastAPI endpoints           │  │
│  └────────┬────────┘  └──────────────┬────────────────┘  │
│           │                          │                    │
│  ┌────────┴──────────────────────────┴────────────────┐  │
│  │ frontend/ (controllers + widget interfaces)        │  │
│  │ - PlotController, TransistorController             │  │
│  │ - IPlotWidget, ITransistorView, IMainWindow        │  │
│  └────────────────────────┬───────────────────────────┘  │
└───────────────────────────┼───────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────┐
│  Application Layer        │                               │
│  ┌────────────────────────┴───────────────────────────┐  │
│  │ backend/concrete_services.py                       │  │
│  │ - PlottingService (matplotlib)                     │  │
│  │ - CalculationService (numpy/scipy)                 │  │
│  │ - ExportService (JSON, CSV, SPICE)                 │  │
│  │ - ComparisonService                                │  │
│  │ - ValidationService                                │  │
│  │ - ConcreteServiceFactory                           │  │
│  └────────────────────────┬───────────────────────────┘  │
└───────────────────────────┼───────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────┐
│  Domain Layer (core/)     │                               │
│  ┌────────────────────────┴───────────────────────────┐  │
│  │ core/services.py — ABC interfaces                  │  │
│  │ ICalculationService, IExportService,               │  │
│  │ IValidationService, IPlottingService,              │  │
│  │ IComparisonService, TransistorRepository           │  │
│  └────────────────────────┬───────────────────────────┘  │
│  ┌────────────────────────┴───────────────────────────┐  │
│  │ core/models.py — Domain entities                   │  │
│  │ Transistor, Switch, Diode, TransistorMetadata,     │  │
│  │ ChannelCharacteristics, SwitchingLossData,         │  │
│  │ FosterThermalModel, GateChargeCurve, SOA,          │  │
│  │ LinearizedModel, VoltageDependentCapacitance, ...  │  │
│  └────────────────────────┬───────────────────────────┘  │
│  ┌────────────────────────┴───────────────────────────┐  │
│  │ core/repository.py — Persistence                   │  │
│  │ JsonTransistorRepository, JsonTransistorLoader     │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## Domain Model

### Transistor Aggregate

The `Transistor` class is the root aggregate. It owns:

- **TransistorMetadata** — identity and descriptive data
- **ElectricalRatings** — absolute maximum ratings
- **ThermalProperties** — thermal characteristics of the package
- **Switch** — MOSFET/IGBT switching element with:
  - Channel V-I curves (`ChannelCharacteristics`)
  - Switching energy data (`SwitchingLossData`)
  - Thermal model (`FosterThermalModel`)
  - Gate charge curves (`GateChargeCurve`)
  - Safe operating area (`SOA`)
  - Temperature-dependent resistance (`TemperatureDependResistance`)
  - Linearized model at operating point (`LinearizedModel`)
- **Diode** — body/freewheeling diode with similar structure
- **Voltage-dependent capacitances** — C_oss, C_iss, C_rss

### Key Operations

1. **Linearization**: `Switch.linearize_at_operating_point(t_j, v_g, i_channel)` returns a `LinearizedModel` with `v0_channel` and `r_channel` for conduction loss calculation.

2. **Resistance calculation**: `ChannelCharacteristics.get_resistance_at_current(i)` interpolates the V-I curve.

3. **Loss calculation**: `CalculationService.calculate_losses()` combines conduction and switching losses.

4. **Thermal impedance**: `FosterThermalModel.get_thermal_impedance(t)` evaluates the Foster RC network.

## Service Interfaces

All ABCs are defined in `core/services.py`. Backend provides concrete implementations.

| Interface | Purpose | Backend Implementation |
|---|---|---|
| `ICalculationService` | Loss/thermal calculations | `CalculationService` |
| `IExportService` | File format export | `ExportService` |
| `IValidationService` | Data validation | `ValidationService` |
| `IPlottingService` | Plot data generation | `PlottingService` |
| `IComparisonService` | Multi-transistor comparison | `ComparisonService` |
| `TransistorRepository` | Data persistence | `JsonTransistorRepository` |
| `ITransistorLoader` | File I/O | `JsonTransistorLoader` |

## Data Flow

```
JSON file / MongoDB
       │
       ▼
JsonTransistorLoader.load_from_json()
       │
       ▼
Transistor (core/models.py)  ◄─── Source of truth
       │
       ├──► CalculationService.calculate_losses()
       ├──► PlottingService.plot_channel_characteristics()
       ├──► ExportService.export_to_json() / export_to_plecs()
       └──► ValidationService.validate_transistor()
```

## Legacy Migration Path

The legacy modules (`transistor.py`, `data_classes.py`, `switch.py`, `diode.py`) are being incrementally migrated to `core/`. During transition:

- New features go into `core/` + `backend/`
- Legacy code remains functional via `__init__.py` wildcard imports
- `gui/` will be refactored to use `frontend/` controllers backed by core services

## File Organization

| Directory | Purpose |
|---|---|
| `core/` | Domain models, service ABCs, repository |
| `backend/` | Concrete service implementations |
| `frontend/` | UI abstractions and controllers |
| `gui/` | PyQt5 desktop application (legacy) |
| `gui_web/` | Vue 3 + FastAPI web interface |
| `templates/` | Jinja2 templates for PLECS and datasheets |
| `data/` | Static reference data (housing types, manufacturers) |
| `examples/` | Example transistor JSON files |
| `tests/` | pytest test suite |
