"""
Business logic interfaces and services for transistor operations.

These services handle calculations, data processing, and business rules.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import numpy.typing as npt

from .models import (
    ChannelCharacteristics,
    SwitchingLossData,
    Transistor,
)


class ITransistorLoader(ABC):
    """Interface for loading transistor data from various sources."""

    @abstractmethod
    def load_from_json(self, file_path: Path) -> Transistor:
        """Load transistor from JSON file."""

    @abstractmethod
    def save_to_json(self, transistor: Transistor, file_path: Path) -> None:
        """Save transistor to JSON file."""


class ICalculationService(ABC):
    """Interface for transistor calculations and analysis."""

    @abstractmethod
    def calculate_channel_resistance(
        self, channel_data: ChannelCharacteristics, current: float
    ) -> float:
        """Calculate channel resistance at specific current."""

    @abstractmethod
    def interpolate_switching_losses(
        self, loss_data: List[SwitchingLossData], conditions: Dict[str, float]
    ) -> float:
        """Interpolate switching losses for given conditions."""

    @abstractmethod
    def calculate_thermal_impedance(
        self, thermal_model: Dict[str, Any],
        time_points: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        """Calculate thermal impedance for given time points."""

    @abstractmethod
    def calculate_losses(
        self, transistor: Transistor, operating_point: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate transistor losses at given operating point."""

    @abstractmethod
    def find_optimal_working_point(
        self, transistor: Transistor, constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """Find optimal working point based on constraints."""

    @abstractmethod
    def calculate_thermal_resistance(
        self, transistor: Transistor, power_profile: List[float]
    ) -> Dict[str, float]:
        """Calculate thermal resistance and junction temperature."""


class IExportService(ABC):
    """Interface for exporting transistor data to various formats."""

    @abstractmethod
    def export_to_plecs(
        self, transistor: Transistor, output_path: Path,
        template_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Export transistor to PLECS format."""

    @abstractmethod
    def export_to_matlab(
        self, transistor: Transistor, output_path: Path
    ) -> None:
        """Export transistor to MATLAB format."""

    @abstractmethod
    def export_to_ltspice(
        self, transistor: Transistor, output_path: Path
    ) -> None:
        """Export transistor to LTSpice format."""

    @abstractmethod
    def export_to_gecko_circuits(
        self, transistor: Transistor, export_params: Dict[str, Any]
    ) -> Path:
        """Export transistor to GeckoCIRCUITS format."""

    @abstractmethod
    def export_to_json(
        self, transistor: Transistor, file_path: Path
    ) -> bool:
        """Export transistor data to JSON format."""

    @abstractmethod
    def export_to_csv(
        self, transistors: List[Transistor], file_path: Path
    ) -> bool:
        """Export transistors to CSV format."""

    @abstractmethod
    def export_to_spice(
        self, transistor: Transistor, file_path: Path
    ) -> bool:
        """Export transistor model to SPICE format."""


class IValidationService(ABC):
    """Interface for validating transistor data."""

    @abstractmethod
    def validate_transistor(self, transistor: Transistor) -> Dict[str, List[str]]:
        """Validate transistor data and return dict with errors/warnings."""

    @abstractmethod
    def validate_channel_data(
        self, channel_data: List[ChannelCharacteristics]
    ) -> List[str]:
        """Validate channel characteristics data."""

    @abstractmethod
    def validate_switching_data(
        self, switching_data: List[SwitchingLossData]
    ) -> List[str]:
        """Validate switching loss data."""

    @abstractmethod
    def check_data_consistency(self, transistor: Transistor) -> List[str]:
        """Check internal data consistency."""

    @abstractmethod
    def check_data_completeness(self, transistor: Transistor) -> Dict[str, Any]:
        """Check how complete the transistor data is."""


class IPlottingService(ABC):
    """Interface for plotting transistor characteristics."""

    @abstractmethod
    def plot_channel_characteristics(
        self, transistor: Transistor,
        component: str = "switch",
        temperatures: Optional[List[float]] = None,
        gate_voltages: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Plot channel characteristics."""

    @abstractmethod
    def plot_switching_losses(
        self, transistor: Transistor,
        loss_type: str = "e_on",
        plot_type: str = "i_e",
    ) -> Dict[str, Any]:
        """Plot switching losses."""

    @abstractmethod
    def plot_safe_operating_area(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot safe operating area."""

    @abstractmethod
    def plot_thermal_impedance(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot thermal impedance."""

    @abstractmethod
    def plot_gate_charge(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot gate charge characteristics."""


class IComparisonService(ABC):
    """Interface for comparing multiple transistors."""

    @abstractmethod
    def compare_characteristics(
        self, transistors: List[Transistor], comparison_type: str
    ) -> Dict[str, Any]:
        """Compare characteristics of multiple transistors."""

    @abstractmethod
    def rank_transistors(
        self, transistors: List[Transistor], criteria: Dict[str, float]
    ) -> List[Tuple[Transistor, float]]:
        """Rank transistors based on given criteria."""

    @abstractmethod
    def compare_transistors(
        self, transistors: List[Transistor]
    ) -> Dict[str, Any]:
        """Compare multiple transistors comprehensively."""

    @abstractmethod
    def find_similar_transistors(
        self, target: Transistor, candidates: List[Transistor],
        tolerance: float = 0.1,
    ) -> List[Transistor]:
        """Find transistors similar to target within tolerance."""


class TransistorRepository(ABC):
    """Repository interface for transistor data persistence."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Transistor]:
        """Get transistor by name."""

    @abstractmethod
    def save(self, transistor: Transistor) -> None:
        """Save transistor to repository."""

    @abstractmethod
    def list_all(self) -> List[str]:
        """List all available transistor names."""

    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete transistor from repository."""


class TransistorService:
    """High-level service for transistor operations."""

    def __init__(
        self,
        loader: ITransistorLoader,
        calculator: ICalculationService,
        exporter: IExportService,
        validator: IValidationService,
        plotter: IPlottingService,
        repository: TransistorRepository,
    ) -> None:
        self._loader = loader
        self._calculator = calculator
        self._exporter = exporter
        self._validator = validator
        self._plotter = plotter
        self._repository = repository

    def load_transistor(self, source: Path | str) -> Transistor:
        """Load transistor from file or repository."""
        if isinstance(source, str):
            transistor = self._repository.get_by_name(source)
            if transistor is None:
                raise ValueError(
                    f"Transistor '{source}' not found in repository"
                )
            return transistor
        return self._loader.load_from_json(source)

    def validate_and_save(self, transistor: Transistor) -> List[str]:
        """Validate transistor and save if valid."""
        result = self._validator.validate_transistor(transistor)
        errors = result.get("errors", [])
        if not errors:
            self._repository.save(transistor)
        return errors

    def analyze_transistor(
        self, transistor: Transistor, analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of transistor."""
        results: Dict[str, Any] = {}

        if analysis_type in ("full", "channel"):
            results["channel_analysis"] = self._analyze_channel_data(transistor)

        if analysis_type in ("full", "switching"):
            results["switching_analysis"] = self._analyze_switching_data(transistor)

        if analysis_type in ("full", "thermal"):
            results["thermal_analysis"] = self._analyze_thermal_data(transistor)

        return results

    def _analyze_channel_data(self, transistor: Transistor) -> Dict[str, Any]:
        """Analyze channel characteristics."""
        return {"status": "analyzed"}

    def _analyze_switching_data(self, transistor: Transistor) -> Dict[str, Any]:
        """Analyze switching loss data."""
        return {"status": "analyzed"}

    def _analyze_thermal_data(self, transistor: Transistor) -> Dict[str, Any]:
        """Analyze thermal properties."""
        return {"status": "analyzed"}
