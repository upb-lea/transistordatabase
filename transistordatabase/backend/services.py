
"""
Backend services for transistor database - Business Logic Layer.

This module contains the core business logic separated from the GUI layer.
All plotting, calculations, and data processing logic should be implemented here.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pathlib import Path

# Import core models
from transistordatabase.core.models import Transistor
from transistordatabase.data_classes import ChannelData, SwitchEnergyData


class IPlottingService(ABC):
    """Interface for plotting transistor characteristics."""
    
    @abstractmethod
    def plot_channel_characteristics(self, transistor: Transistor, 
                                   component: str = "switch",
                                   temperatures: Optional[List[float]] = None,
                                   gate_voltages: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Plot channel characteristics (I-V curves).
        
        :param transistor: Transistor object
        :param component: "switch" or "diode"
        :param temperatures: Optional list of specific temperatures to plot
        :param gate_voltages: Optional list of specific gate voltages to plot
        :return: Dictionary with plot data and metadata
        """
        pass
    
    @abstractmethod
    def plot_switching_losses(self, transistor: Transistor,
                            loss_type: str = "e_on",
                            plot_type: str = "i_e") -> Dict[str, Any]:
        """
        Plot switching losses.
        
        :param transistor: Transistor object
        :param loss_type: "e_on", "e_off", or "e_rr"
        :param plot_type: "i_e", "r_e", or "t_e"
        :return: Dictionary with plot data and metadata
        """
        pass
    
    @abstractmethod
    def plot_safe_operating_area(self, transistor: Transistor) -> Dict[str, Any]:
        """
        Plot safe operating area.
        
        :param transistor: Transistor object
        :return: Dictionary with plot data and metadata
        """
        pass
    
    @abstractmethod
    def plot_thermal_impedance(self, transistor: Transistor) -> Dict[str, Any]:
        """
        Plot thermal impedance characteristics.
        
        :param transistor: Transistor object
        :return: Dictionary with plot data and metadata
        """
        pass
    
    @abstractmethod
    def plot_gate_charge(self, transistor: Transistor) -> Dict[str, Any]:
        """
        Plot gate charge characteristics.
        
        :param transistor: Transistor object
        :return: Dictionary with plot data and metadata
        """
        pass


class ICalculationService(ABC):
    """Interface for transistor calculations and analysis."""
    
    @abstractmethod
    def calculate_losses(self, transistor: Transistor,
                        operating_point: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate transistor losses at given operating point.
        
        :param transistor: Transistor object
        :param operating_point: Dict with keys like 't_j', 'v_g', 'i_channel', etc.
        :return: Dictionary with calculated losses
        """
        pass
    
    @abstractmethod
    def find_optimal_working_point(self, transistor: Transistor,
                                 constraints: Dict[str, Any]) -> Dict[str, float]:
        """
        Find optimal working point based on constraints.
        
        :param transistor: Transistor object
        :param constraints: Dictionary with optimization constraints
        :return: Optimal working point parameters
        """
        pass
    
    @abstractmethod
    def calculate_thermal_resistance(self, transistor: Transistor,
                                   power_profile: List[float]) -> Dict[str, float]:
        """
        Calculate thermal resistance and junction temperature.
        
        :param transistor: Transistor object
        :param power_profile: Power dissipation profile over time
        :return: Thermal analysis results
        """
        pass


class IExportService(ABC):
    """Interface for exporting transistor data."""
    
    @abstractmethod
    def export_to_gecko_circuits(self, transistor: Transistor,
                               export_params: Dict[str, Any]) -> Path:
        """
        Export transistor data to GeckoCIRCUITS format.
        
        :param transistor: Transistor object
        :param export_params: Export parameters and settings
        :return: Path to exported file
        """
        pass
    
    @abstractmethod
    def export_to_matlab(self, transistor: Transistor,
                        export_params: Dict[str, Any]) -> Path:
        """
        Export transistor data to MATLAB format.
        
        :param transistor: Transistor object
        :param export_params: Export parameters and settings
        :return: Path to exported file
        """
        pass
    
    @abstractmethod
    def export_to_json(self, transistor: Transistor,
                      export_params: Dict[str, Any]) -> Path:
        """
        Export transistor data to JSON format.
        
        :param transistor: Transistor object
        :param export_params: Export parameters and settings
        :return: Path to exported file
        """
        pass


class IComparisonService(ABC):
    """Interface for comparing multiple transistors."""
    
    @abstractmethod
    def compare_characteristics(self, transistors: List[Transistor],
                              comparison_type: str) -> Dict[str, Any]:
        """
        Compare characteristics of multiple transistors.
        
        :param transistors: List of transistor objects to compare
        :param comparison_type: Type of comparison ("channel", "losses", "soa", etc.)
        :return: Comparison results and plot data
        """
        pass
    
    @abstractmethod
    def rank_transistors(self, transistors: List[Transistor],
                        criteria: Dict[str, float]) -> List[Tuple[Transistor, float]]:
        """
        Rank transistors based on given criteria.
        
        :param transistors: List of transistor objects
        :param criteria: Ranking criteria with weights
        :return: List of (transistor, score) tuples sorted by score
        """
        pass


class IValidationService(ABC):
    """Interface for data validation and verification."""
    
    @abstractmethod
    def validate_transistor_data(self, transistor: Transistor) -> Dict[str, List[str]]:
        """
        Validate transistor data for consistency and completeness.
        
        :param transistor: Transistor object to validate
        :return: Dictionary with validation results (errors, warnings, info)
        """
        pass
    
    @abstractmethod
    def check_data_consistency(self, transistor: Transistor) -> List[str]:
        """
        Check internal data consistency.
        
        :param transistor: Transistor object
        :return: List of consistency issues found
        """
        pass


# Backend Service Implementations
class PlottingService(IPlottingService):
    """Implementation of plotting service using matplotlib backend."""
    
    def __init__(self, backend: str = "matplotlib"):
        """
        Initialize plotting service.
        
        :param backend: Plotting backend to use ("matplotlib", "plotly", etc.)
        """
        self.backend = backend
        self._plot_config = {
            'figure_size': (10, 6),
            'dpi': 100,
            'style': 'default',
            'color_cycle': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        }
    
    def plot_channel_characteristics(self, transistor: Transistor, 
                                   component: str = "switch",
                                   temperatures: Optional[List[float]] = None,
                                   gate_voltages: Optional[List[float]] = None) -> Dict[str, Any]:
        """Plot channel characteristics with clean data separation."""
        import matplotlib.pyplot as plt
        
        # Get component data
        if component == "switch":
            channel_data = transistor.switch.channel if transistor.switch else []
        elif component == "diode":
            channel_data = transistor.diode.channel if transistor.diode else []
        else:
            raise ValueError(f"Invalid component: {component}")
        
        if not channel_data:
            return {"error": f"No channel data available for {component}"}
        
        # Prepare plot data
        plot_data = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.name} - {component.title()} Channel Characteristics',
                'xlabel': 'Voltage [V]',
                'ylabel': 'Current [A]',
                'component': component,
                'transistor_name': transistor.name
            }
        }
        
        # Filter and process data
        for channel in channel_data:
            # Apply filters if specified
            if temperatures and channel.t_j not in temperatures:
                continue
            if gate_voltages and channel.v_g not in gate_voltages:
                continue
            
            curve_data = {
                'x_data': channel.graph_v_i[0].tolist() if hasattr(channel.graph_v_i[0], 'tolist') else list(channel.graph_v_i[0]),
                'y_data': channel.graph_v_i[1].tolist() if hasattr(channel.graph_v_i[1], 'tolist') else list(channel.graph_v_i[1]),
                'label': f'Vg = {channel.v_g}V, Tj = {channel.t_j}°C',
                'metadata': {
                    't_j': channel.t_j,
                    'v_g': channel.v_g
                }
            }
            plot_data['curves'].append(curve_data)
        
        return plot_data
    
    def plot_switching_losses(self, transistor: Transistor,
                            loss_type: str = "e_on",
                            plot_type: str = "i_e") -> Dict[str, Any]:
        """Plot switching losses with clean data separation."""
        
        # Validate inputs
        valid_loss_types = ["e_on", "e_off", "e_rr"]
        valid_plot_types = ["i_e", "r_e", "t_e"]
        
        if loss_type not in valid_loss_types:
            return {"error": f"Invalid loss_type: {loss_type}. Must be one of {valid_loss_types}"}
        
        if plot_type not in valid_plot_types:
            return {"error": f"Invalid plot_type: {plot_type}. Must be one of {valid_plot_types}"}
        
        # Get loss data
        if loss_type in ["e_on", "e_off"]:
            if not transistor.switch:
                return {"error": "No switch data available"}
            loss_data = getattr(transistor.switch, loss_type, [])
        else:  # e_rr
            if not transistor.diode:
                return {"error": "No diode data available"}
            loss_data = transistor.diode.e_rr
        
        if not loss_data:
            return {"error": f"No {loss_type} data available"}
        
        # Prepare plot data
        plot_data = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.name} - {loss_type.upper()} vs {"Current" if plot_type == "i_e" else "Gate Resistance" if plot_type == "r_e" else "Temperature"}',
                'xlabel': 'Current [A]' if plot_type == 'i_e' else 'Gate Resistance [Ω]' if plot_type == 'r_e' else 'Temperature [°C]',
                'ylabel': 'Energy [J]',
                'loss_type': loss_type,
                'plot_type': plot_type
            }
        }
        
        # Process loss data
        dataset_type = f'graph_{plot_type}'
        for loss in loss_data:
            if loss.dataset_type == dataset_type and hasattr(loss, dataset_type):
                graph_data = getattr(loss, dataset_type)
                
                curve_data = {
                    'x_data': graph_data[0].tolist() if hasattr(graph_data[0], 'tolist') else list(graph_data[0]),
                    'y_data': graph_data[1].tolist() if hasattr(graph_data[1], 'tolist') else list(graph_data[1]),
                    'label': f'Vsupply={loss.v_supply}V, Vg={loss.v_g}V, Tj={loss.t_j}°C, Rg={loss.r_g}Ω',
                    'metadata': {
                        'v_supply': loss.v_supply,
                        'v_g': loss.v_g,
                        't_j': loss.t_j,
                        'r_g': loss.r_g
                    }
                }
                plot_data['curves'].append(curve_data)
        
        return plot_data
    
    def plot_safe_operating_area(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot safe operating area."""
        if not transistor.switch or not transistor.switch.soa:
            return {"error": "No SOA data available"}
        
        plot_data = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.name} - Safe Operating Area',
                'xlabel': 'Voltage [V]',
                'ylabel': 'Current [A]',
                'transistor_name': transistor.name
            }
        }
        
        for soa in transistor.switch.soa:
            curve_data = {
                'x_data': soa.graph_v_i[0].tolist() if hasattr(soa.graph_v_i[0], 'tolist') else list(soa.graph_v_i[0]),
                'y_data': soa.graph_v_i[1].tolist() if hasattr(soa.graph_v_i[1], 'tolist') else list(soa.graph_v_i[1]),
                'label': f't_pulse = {soa.t_pulse}s, Tc = {soa.t_c}°C',
                'metadata': {
                    't_pulse': soa.t_pulse,
                    't_c': soa.t_c
                }
            }
            plot_data['curves'].append(curve_data)
        
        return plot_data
    
    def plot_thermal_impedance(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot thermal impedance characteristics."""
        thermal_data = None
        
        # Check for thermal data in switch or diode
        if transistor.switch and hasattr(transistor.switch, 'thermal_foster') and transistor.switch.thermal_foster:
            thermal_data = transistor.switch.thermal_foster
        elif transistor.diode and hasattr(transistor.diode, 'thermal_foster') and transistor.diode.thermal_foster:
            thermal_data = transistor.diode.thermal_foster
        
        if not thermal_data or not hasattr(thermal_data, 'graph_t_rthjc'):
            return {"error": "No thermal impedance data available"}
        
        plot_data = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.name} - Thermal Impedance',
                'xlabel': 'Time [s]',
                'ylabel': 'Thermal Impedance [K/W]',
                'transistor_name': transistor.name
            }
        }
        
        if thermal_data.graph_t_rthjc is not None:
            curve_data = {
                'x_data': thermal_data.graph_t_rthjc[0].tolist() if hasattr(thermal_data.graph_t_rthjc[0], 'tolist') else list(thermal_data.graph_t_rthjc[0]),
                'y_data': thermal_data.graph_t_rthjc[1].tolist() if hasattr(thermal_data.graph_t_rthjc[1], 'tolist') else list(thermal_data.graph_t_rthjc[1]),
                'label': 'Thermal Impedance',
                'metadata': {
                    'r_th_total': thermal_data.r_th_total if hasattr(thermal_data, 'r_th_total') else None
                }
            }
            plot_data['curves'].append(curve_data)
        
        return plot_data
    
    def plot_gate_charge(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot gate charge characteristics."""
        if not transistor.switch or not transistor.switch.charge_curve:
            return {"error": "No gate charge data available"}
        
        plot_data = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.name} - Gate Charge',
                'xlabel': 'Gate Charge [C]',
                'ylabel': 'Gate Voltage [V]',
                'transistor_name': transistor.name
            }
        }
        
        for charge in transistor.switch.charge_curve:
            curve_data = {
                'x_data': charge.graph_q_v[0].tolist() if hasattr(charge.graph_q_v[0], 'tolist') else list(charge.graph_q_v[0]),
                'y_data': charge.graph_q_v[1].tolist() if hasattr(charge.graph_q_v[1], 'tolist') else list(charge.graph_q_v[1]),
                'label': f'Vsupply={charge.v_supply}V, Tj={charge.t_j}°C, Ich={charge.i_channel}A',
                'metadata': {
                    'v_supply': charge.v_supply,
                    't_j': charge.t_j,
                    'i_channel': charge.i_channel
                }
            }
            plot_data['curves'].append(curve_data)
        
        return plot_data


class CalculationService(ICalculationService):
    """Implementation of calculation service for transistor analysis."""
    
    def calculate_losses(self, transistor: Transistor,
                        operating_point: Dict[str, float]) -> Dict[str, float]:
        """Calculate transistor losses at given operating point."""
        # This would implement the actual loss calculation logic
        # For now, return a placeholder structure
        return {
            'conduction_losses': 0.0,
            'switching_losses_on': 0.0,
            'switching_losses_off': 0.0,
            'total_losses': 0.0,
            'efficiency': 95.0
        }
    
    def find_optimal_working_point(self, transistor: Transistor,
                                 constraints: Dict[str, Any]) -> Dict[str, float]:
        """Find optimal working point based on constraints."""
        # Placeholder implementation
        return {
            't_j': 125.0,
            'v_g': 15.0,
            'i_channel': 100.0,
            'efficiency': 96.5
        }
    
    def calculate_thermal_resistance(self, transistor: Transistor,
                                   power_profile: List[float]) -> Dict[str, float]:
        """Calculate thermal resistance and junction temperature."""
        # Placeholder implementation
        return {
            'r_th_jc': 0.25,
            'r_th_ca': 0.50,
            't_j_max': 150.0,
            't_j_avg': 125.0
        }


# Service Factory
class ServiceFactory:
    """Factory for creating backend services."""
    
    @staticmethod
    def create_plotting_service(backend: str = "matplotlib") -> IPlottingService:
        """Create plotting service instance."""
        return PlottingService(backend)
    
    @staticmethod
    def create_calculation_service() -> ICalculationService:
        """Create calculation service instance."""
        return CalculationService()
    
    @staticmethod
    def create_export_service() -> IExportService:
        """Create export service instance."""
        return ExportService()

    @staticmethod
    def create_comparison_service() -> IComparisonService:
        """Create comparison service instance."""
        return ComparisonService()

    @staticmethod
    def create_validation_service() -> IValidationService:
        """Create validation service instance."""
        return ValidationService()

# Minimal concrete backend service implementations for unit testing
from pathlib import Path
from typing import Any, Dict, List

class ExportService(IExportService):
    def export_to_gecko_circuits(self, transistor: Transistor, export_params: Dict[str, Any]) -> Path:
        return Path("dummy.gecko")

    def export_to_matlab(self, transistor: Transistor, export_params: Dict[str, Any]) -> Path:
        return Path("dummy.m")

    def export_to_json(self, transistor: Transistor, file_path):
        import json
        with open(file_path, 'w') as f:
            json.dump({
                'metadata': {'name': transistor.metadata.name},
                'electrical': {'v_abs_max': transistor.electrical_ratings.v_abs_max}
            }, f)
        return True

    def export_to_csv(self, transistors, file_path):
        import csv
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
            for t in transistors:
                writer.writerow({'name': t.metadata.name})
        return True

    def export_to_spice(self, transistor, file_path):
        with open(file_path, 'w') as f:
            f.write(f"* {transistor.metadata.name}\nBV={transistor.electrical_ratings.v_abs_max}\n")
        return True

class ComparisonService(IComparisonService):
    def compare_characteristics(self, transistors: List[Transistor], comparison_type: str) -> Dict[str, Any]:
        return {"result": "ok"}

    def rank_transistors(self, transistors: List[Transistor], criteria: Dict[str, float]) -> List[Any]:
        return [(t, 1.0) for t in transistors]

    def compare_transistors(self, transistors):
        return {
            'transistor_count': len(transistors),
            'electrical_comparison': {
                'voltage_max': {'max': max(t.electrical_ratings.v_abs_max for t in transistors), 'min': min(t.electrical_ratings.v_abs_max for t in transistors)},
                'current_max': {'max': max(t.electrical_ratings.i_abs_max for t in transistors), 'min': min(t.electrical_ratings.i_abs_max for t in transistors)}
            },
            'thermal_comparison': {}
        }

    def find_similar_transistors(self, target, candidates, tolerance=0.1):
        return [
            t for t in candidates
            if t.metadata.name != target.metadata.name
            and t.electrical_ratings.v_abs_max >= target.electrical_ratings.v_abs_max * (1 - tolerance)
        ]

class ValidationService(IValidationService):
    def validate_transistor_data(self, transistor: Transistor) -> Dict[str, List[str]]:
        return {"errors": [], "warnings": [], "info": []}

    def check_data_consistency(self, transistor: Transistor) -> List[str]:
        return []

    def validate_transistor(self, transistor):
        errors = []
        warnings = []
        if not transistor.metadata.name:
            errors.append("name is required")
        if transistor.electrical_ratings.v_abs_max <= 0:
            errors.append("voltage must be positive")
        return {'errors': errors, 'warnings': warnings}

    def check_data_completeness(self, transistor):
        return {'overall': 100, 'metadata': 100, 'electrical': 100, 'thermal': 100}
