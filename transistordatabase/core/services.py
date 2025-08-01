"""
Business logic interfaces and services for transistor operations.
These services handle calculations, data processing, and business rules.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import numpy.typing as npt
from pathlib import Path

from .models import Transistor, ChannelCharacteristics, SwitchingLossData


class ITransistorLoader(ABC):
    """Interface for loading transistor data from various sources."""
    
    @abstractmethod
    def load_from_json(self, file_path: Path) -> Transistor:
        """Load transistor from JSON file."""
        pass
    
    @abstractmethod
    def save_to_json(self, transistor: Transistor, file_path: Path) -> None:
        """Save transistor to JSON file."""
        pass


class ICalculationService(ABC):
    """Interface for transistor calculations and analysis."""
    
    @abstractmethod
    def calculate_channel_resistance(self, channel_data: ChannelCharacteristics, 
                                   current: float) -> float:
        """Calculate channel resistance at specific current."""
        pass
    
    @abstractmethod
    def interpolate_switching_losses(self, loss_data: List[SwitchingLossData],
                                   conditions: Dict[str, float]) -> float:
        """Interpolate switching losses for given conditions."""
        pass
    
    @abstractmethod
    def calculate_thermal_impedance(self, thermal_model: Dict[str, Any],
                                  time_points: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Calculate thermal impedance for given time points."""
        pass


class IExportService(ABC):
    """Interface for exporting transistor data to various formats."""
    
    @abstractmethod
    def export_to_plecs(self, transistor: Transistor, output_path: Path,
                       template_config: Optional[Dict[str, Any]] = None) -> None:
        """Export transistor to PLECS format."""
        pass
    
    @abstractmethod
    def export_to_matlab(self, transistor: Transistor, output_path: Path) -> None:
        """Export transistor to MATLAB format."""
        pass
    
    @abstractmethod
    def export_to_ltspice(self, transistor: Transistor, output_path: Path) -> None:
        """Export transistor to LTSpice format."""
        pass


class IValidationService(ABC):
    """Interface for validating transistor data."""
    
    @abstractmethod
    def validate_transistor(self, transistor: Transistor) -> List[str]:
        """Validate transistor data and return list of errors."""
        pass
    
    @abstractmethod
    def validate_channel_data(self, channel_data: List[ChannelCharacteristics]) -> List[str]:
        """Validate channel characteristics data."""
        pass
    
    @abstractmethod
    def validate_switching_data(self, switching_data: List[SwitchingLossData]) -> List[str]:
        """Validate switching loss data."""
        pass


class IPlottingService(ABC):
    """Interface for plotting transistor characteristics."""
    
    @abstractmethod
    def plot_channel_characteristics(self, transistor: Transistor, 
                                   component: str = "switch",
                                   temperatures: Optional[List[float]] = None) -> Any:
        """Plot channel characteristics."""
        pass
    
    @abstractmethod
    def plot_switching_losses(self, transistor: Transistor,
                            loss_type: str = "e_on") -> Any:
        """Plot switching losses."""
        pass
    
    @abstractmethod
    def plot_safe_operating_area(self, transistor: Transistor) -> Any:
        """Plot safe operating area."""
        pass
    
    @abstractmethod
    def plot_thermal_impedance(self, transistor: Transistor) -> Any:
        """Plot thermal impedance."""
        pass


class TransistorRepository(ABC):
    """Repository interface for transistor data persistence."""
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Transistor]:
        """Get transistor by name."""
        pass
    
    @abstractmethod
    def save(self, transistor: Transistor) -> None:
        """Save transistor to repository."""
        pass
    
    @abstractmethod
    def list_all(self) -> List[str]:
        """List all available transistor names."""
        pass
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete transistor from repository."""
        pass


class TransistorService:
    """High-level service for transistor operations."""
    
    def __init__(self, 
                 loader: ITransistorLoader,
                 calculator: ICalculationService,
                 exporter: IExportService,
                 validator: IValidationService,
                 plotter: IPlottingService,
                 repository: TransistorRepository):
        self._loader = loader
        self._calculator = calculator
        self._exporter = exporter
        self._validator = validator
        self._plotter = plotter
        self._repository = repository
    
    def load_transistor(self, source: Path | str) -> Transistor:
        """Load transistor from file or repository."""
        if isinstance(source, str):
            # Load from repository by name
            transistor = self._repository.get_by_name(source)
            if transistor is None:
                raise ValueError(f"Transistor '{source}' not found in repository")
            return transistor
        else:
            # Load from file path
            return self._loader.load_from_json(source)
    
    def validate_and_save(self, transistor: Transistor) -> List[str]:
        """Validate transistor and save if valid."""
        errors = self._validator.validate_transistor(transistor)
        if not errors:
            self._repository.save(transistor)
        return errors
    
    def analyze_transistor(self, transistor: Transistor, 
                         analysis_type: str = "full") -> Dict[str, Any]:
        """Perform comprehensive analysis of transistor."""
        results = {}
        
        if analysis_type in ["full", "channel"]:
            # Analyze channel characteristics
            results["channel_analysis"] = self._analyze_channel_data(transistor)
        
        if analysis_type in ["full", "switching"]:
            # Analyze switching losses
            results["switching_analysis"] = self._analyze_switching_data(transistor)
        
        if analysis_type in ["full", "thermal"]:
            # Analyze thermal properties
            results["thermal_analysis"] = self._analyze_thermal_data(transistor)
        
        return results
    
    def _analyze_channel_data(self, transistor: Transistor) -> Dict[str, Any]:
        """Analyze channel characteristics."""
        # Implementation placeholder
        return {"status": "analyzed"}
    
    def _analyze_switching_data(self, transistor: Transistor) -> Dict[str, Any]:
        """Analyze switching loss data."""
        # Implementation placeholder
        return {"status": "analyzed"}
    
    def _analyze_thermal_data(self, transistor: Transistor) -> Dict[str, Any]:
        """Analyze thermal properties."""
        # Implementation placeholder
        return {"status": "analyzed"}
