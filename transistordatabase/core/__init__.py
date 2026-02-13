"""
Core domain layer for the transistor database.

This package contains the core business models, services, and interfaces
that define the domain logic separated from presentation and infrastructure concerns.
"""

from .models import (
    Transistor,
    Switch,
    Diode,
    TransistorMetadata,
    ElectricalRatings,
    ThermalProperties,
    ChannelCharacteristics,
    SwitchingLossData,
    ITransistorComponent,
    FosterThermalModel,
    GateChargeCurve,
    SOA,
    VoltageDependentCapacitance,
    EffectiveOutputCapacitance,
    TemperatureDependResistance,
    RawMeasurementData,
    LinearizedModel,
)

from .services import (
    ITransistorLoader,
    ICalculationService,
    IExportService,
    IValidationService,
    IPlottingService,
    IComparisonService,
    TransistorRepository,
    TransistorService,
)

from .repository import (
    JsonTransistorRepository,
    JsonTransistorLoader,
    TransistorFactory,
)

__all__ = [
    # Models
    'Transistor',
    'Switch',
    'Diode',
    'TransistorMetadata',
    'ElectricalRatings',
    'ThermalProperties',
    'ChannelCharacteristics',
    'SwitchingLossData',
    'ITransistorComponent',
    'FosterThermalModel',
    'GateChargeCurve',
    'SOA',
    'VoltageDependentCapacitance',
    'EffectiveOutputCapacitance',
    'TemperatureDependResistance',
    'RawMeasurementData',
    'LinearizedModel',
    # Services
    'ITransistorLoader',
    'ICalculationService',
    'IExportService',
    'IValidationService',
    'IPlottingService',
    'IComparisonService',
    'TransistorRepository',
    'TransistorService',
    # Repository
    'JsonTransistorRepository',
    'JsonTransistorLoader',
    'TransistorFactory',
]

__version__ = '1.0.0'
