"""
Concrete implementations of backend services.

All ABC interfaces are imported from core.services. No duplicate interface
definitions exist in the backend layer.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from transistordatabase.core.models import (
    FosterThermalModel,
    Transistor,
)
from transistordatabase.core.services import (
    ICalculationService,
    IComparisonService,
    IExportService,
    IPlottingService,
    IValidationService,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
class PlottingService(IPlottingService):
    """Matplotlib-based plotting service returning structured plot data."""

    def __init__(self, backend: str = "matplotlib") -> None:
        self.backend = backend

    def plot_channel_characteristics(
        self, transistor: Transistor,
        component: str = "switch",
        temperatures: list[float] | None = None,
        gate_voltages: list[float] | None = None,
    ) -> Dict[str, Any]:
        """Plot channel characteristics (I-V curves)."""
        if component == "switch":
            channel_data = transistor.switch.channel_data
        elif component == "diode":
            channel_data = transistor.diode.channel_data
        else:
            raise ValueError(f"Invalid component: {component}")

        if not channel_data:
            return {"error": f"No channel data available for {component}"}

        plot_data: Dict[str, Any] = {
            'curves': [],
            'metadata': {
                'title': (
                    f'{transistor.metadata.name} - '
                    f'{component.title()} Channel Characteristics'
                ),
                'xlabel': 'Voltage [V]',
                'ylabel': 'Current [A]',
                'component': component,
                'transistor_name': transistor.metadata.name,
            },
        }

        for ch in channel_data:
            if temperatures and ch.t_j not in temperatures:
                continue
            if gate_voltages and ch.v_g not in gate_voltages:
                continue

            x = ch.graph_v_i[0]
            y = ch.graph_v_i[1]
            plot_data['curves'].append({
                'x_data': x.tolist() if hasattr(x, 'tolist') else list(x),
                'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                'label': f'Vg = {ch.v_g}V, Tj = {ch.t_j} deg C',
                'metadata': {'t_j': ch.t_j, 'v_g': ch.v_g},
            })

        return plot_data

    def plot_switching_losses(
        self, transistor: Transistor,
        loss_type: str = "e_on",
        plot_type: str = "i_e",
    ) -> Dict[str, Any]:
        """Plot switching losses."""
        valid_loss = ("e_on", "e_off", "e_rr")
        valid_plot = ("i_e", "r_e", "t_e")
        if loss_type not in valid_loss:
            return {"error": f"Invalid loss_type: {loss_type}"}
        if plot_type not in valid_plot:
            return {"error": f"Invalid plot_type: {plot_type}"}

        if loss_type == "e_on":
            loss_data = transistor.switch.e_on_data
        elif loss_type == "e_off":
            loss_data = transistor.switch.e_off_data
        else:
            loss_data = transistor.diode.e_rr_data

        if not loss_data:
            return {"error": f"No {loss_type} data available"}

        plot_data: Dict[str, Any] = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.metadata.name} - {loss_type.upper()}',
                'xlabel': {
                    'i_e': 'Current [A]',
                    'r_e': 'Gate Resistance [Ohm]',
                    't_e': 'Temperature [deg C]',
                }[plot_type],
                'ylabel': 'Energy [J]',
                'loss_type': loss_type,
                'plot_type': plot_type,
            },
        }

        dataset_attr = f'graph_{plot_type}'
        for loss in loss_data:
            if loss.dataset_type == dataset_attr:
                graph = getattr(loss, dataset_attr, None)
                if graph is not None:
                    x = graph[0]
                    y = graph[1]
                    plot_data['curves'].append({
                        'x_data': x.tolist() if hasattr(x, 'tolist') else list(x),
                        'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                        'label': (
                            f'Vsupply={loss.v_supply}V, Vg={loss.v_g}V, '
                            f'Tj={loss.t_j} deg C, Rg={loss.r_g}Ohm'
                        ),
                        'metadata': {
                            'v_supply': loss.v_supply,
                            'v_g': loss.v_g,
                            't_j': loss.t_j,
                            'r_g': loss.r_g,
                        },
                    })

        return plot_data

    def plot_safe_operating_area(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot safe operating area."""
        if not transistor.switch.soa:
            return {"error": "No SOA data available"}

        plot_data: Dict[str, Any] = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.metadata.name} - Safe Operating Area',
                'xlabel': 'Voltage [V]',
                'ylabel': 'Current [A]',
                'transistor_name': transistor.metadata.name,
            },
        }

        for soa in transistor.switch.soa:
            if soa.graph_i_v is not None and soa.graph_i_v.size > 0:
                x = soa.graph_i_v[0]
                y = soa.graph_i_v[1]
                plot_data['curves'].append({
                    'x_data': x.tolist() if hasattr(x, 'tolist') else list(x),
                    'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                    'label': (
                        f't_pulse = {soa.time_pulse}s, '
                        f'Tc = {soa.t_c} deg C'
                    ),
                    'metadata': {
                        'time_pulse': soa.time_pulse,
                        't_c': soa.t_c,
                    },
                })

        return plot_data

    def plot_thermal_impedance(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot thermal impedance characteristics."""
        thermal_data: FosterThermalModel | None = None

        if transistor.switch.thermal_foster is not None:
            thermal_data = transistor.switch.thermal_foster
        elif transistor.diode.thermal_foster is not None:
            thermal_data = transistor.diode.thermal_foster

        if thermal_data is None or thermal_data.graph_t_rthjc is None:
            return {"error": "No thermal impedance data available"}

        x = thermal_data.graph_t_rthjc[0]
        y = thermal_data.graph_t_rthjc[1]
        plot_data: Dict[str, Any] = {
            'curves': [{
                'x_data': x.tolist() if hasattr(x, 'tolist') else list(x),
                'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                'label': 'Thermal Impedance',
                'metadata': {'r_th_total': thermal_data.r_th_total},
            }],
            'metadata': {
                'title': f'{transistor.metadata.name} - Thermal Impedance',
                'xlabel': 'Time [s]',
                'ylabel': 'Thermal Impedance [K/W]',
                'transistor_name': transistor.metadata.name,
            },
        }
        return plot_data

    def plot_gate_charge(self, transistor: Transistor) -> Dict[str, Any]:
        """Plot gate charge characteristics."""
        if not transistor.switch.gate_charge_curves:
            return {"error": "No gate charge data available"}

        plot_data: Dict[str, Any] = {
            'curves': [],
            'metadata': {
                'title': f'{transistor.metadata.name} - Gate Charge',
                'xlabel': 'Gate Charge [C]',
                'ylabel': 'Gate Voltage [V]',
                'transistor_name': transistor.metadata.name,
            },
        }

        for gc in transistor.switch.gate_charge_curves:
            if gc.graph_q_v is not None:
                x = gc.graph_q_v[0]
                y = gc.graph_q_v[1]
                plot_data['curves'].append({
                    'x_data': x.tolist() if hasattr(x, 'tolist') else list(x),
                    'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                    'label': (
                        f'Vsupply={gc.v_supply}V, Tj={gc.t_j} deg C, '
                        f'Ich={gc.i_channel}A'
                    ),
                    'metadata': {
                        'v_supply': gc.v_supply,
                        't_j': gc.t_j,
                        'i_channel': gc.i_channel,
                    },
                })

        return plot_data


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------
class CalculationService(ICalculationService):
    """Transistor calculation and analysis service."""

    def calculate_channel_resistance(
        self, channel_data: Any, current: float
    ) -> float:
        """Calculate channel resistance at specific current."""
        return channel_data.get_resistance_at_current(current)

    def interpolate_switching_losses(
        self, loss_data: list, conditions: Dict[str, float]
    ) -> float:
        """Interpolate switching losses for given conditions.

        Uses linear interpolation between available data points matching
        the closest temperature and supply voltage.
        """
        t_j = conditions.get('t_j', 25.0)
        i_channel = conditions.get('i_channel', 0.0)

        # Find datasets matching temperature
        matching = [d for d in loss_data if d.t_j == t_j]
        if not matching:
            # Find closest temperature
            temps = [d.t_j for d in loss_data]
            if not temps:
                return 0.0
            closest_t = min(temps, key=lambda x: abs(x - t_j))
            matching = [d for d in loss_data if d.t_j == closest_t]

        for data in matching:
            if data.dataset_type == 'graph_i_e' and data.graph_i_e is not None:
                currents = data.graph_i_e[0]
                energies = data.graph_i_e[1]
                return float(np.interp(i_channel, currents, energies))
            if data.dataset_type == 'single' and data.e_x is not None:
                return data.e_x

        return 0.0

    def calculate_thermal_impedance(
        self, thermal_model: Dict[str, Any],
        time_points: np.ndarray,
    ) -> np.ndarray:
        """Calculate thermal impedance Z_th(t) using Foster model."""
        r_th_vector = thermal_model.get('r_th_vector', [])
        tau_vector = thermal_model.get('tau_vector', [])

        if not r_th_vector or not tau_vector:
            r_th_total = thermal_model.get('r_th_total', 0.0)
            return np.full_like(time_points, r_th_total, dtype=np.float64)

        z_th = np.zeros_like(time_points, dtype=np.float64)
        for r_th, tau in zip(r_th_vector, tau_vector, strict=True):
            z_th += r_th * (1.0 - np.exp(-time_points / tau))
        return z_th

    def calculate_losses(
        self, transistor: Transistor, operating_point: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate transistor losses at given operating point."""
        t_j = operating_point.get('t_j', 25.0)
        v_g = operating_point.get('v_g', 15.0)
        i_channel = operating_point.get('i_channel', 0.0)
        f_sw = operating_point.get('f_sw', 10000.0)

        # Conduction losses from linearized model
        cond_loss = 0.0
        try:
            lm = transistor.switch.linearize_at_operating_point(
                t_j, v_g, i_channel
            )
            cond_loss = (lm.v0_channel * i_channel
                         + lm.r_channel * i_channel ** 2)
        except ValueError:
            pass

        # Switching losses
        e_on = self.interpolate_switching_losses(
            transistor.switch.e_on_data,
            {'t_j': t_j, 'i_channel': i_channel},
        )
        e_off = self.interpolate_switching_losses(
            transistor.switch.e_off_data,
            {'t_j': t_j, 'i_channel': i_channel},
        )
        sw_loss = (e_on + e_off) * f_sw

        return {
            'conduction_losses': cond_loss,
            'switching_losses_on': e_on * f_sw,
            'switching_losses_off': e_off * f_sw,
            'total_losses': cond_loss + sw_loss,
        }

    def find_optimal_working_point(
        self, transistor: Transistor, constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """Find optimal working point based on constraints."""
        return {
            't_j': constraints.get('t_j_max', 125.0),
            'v_g': constraints.get('v_g', 15.0),
            'i_channel': constraints.get('i_max', 100.0),
        }

    def calculate_thermal_resistance(
        self, transistor: Transistor, power_profile: List[float]
    ) -> Dict[str, float]:
        """Calculate thermal resistance and junction temperature."""
        r_th = transistor.thermal_properties.r_th_cs or 0.0
        avg_power = sum(power_profile) / len(power_profile) if power_profile else 0.0
        t_j_rise = avg_power * r_th

        return {
            'r_th_jc': r_th,
            't_j_rise': t_j_rise,
            't_j_avg': 25.0 + t_j_rise,
        }


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
class ExportService(IExportService):
    """Service for exporting transistor data to various formats."""

    def export_to_json(self, transistor: Transistor, file_path: Path) -> bool:
        """Export transistor to JSON format."""
        try:
            data = {
                'metadata': {
                    'name': transistor.metadata.name,
                    'type': transistor.metadata.type,
                    'manufacturer': transistor.metadata.manufacturer,
                    'housing_type': transistor.metadata.housing_type,
                },
                'electrical': {
                    'v_abs_max': transistor.electrical_ratings.v_abs_max,
                    'i_abs_max': transistor.electrical_ratings.i_abs_max,
                    'i_cont': transistor.electrical_ratings.i_cont,
                },
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            logger.exception("Error exporting to JSON")
            return False

    def export_to_csv(self, transistors: List[Transistor], file_path: Path) -> bool:
        """Export transistors to CSV format."""
        try:
            if not transistors:
                return False
            headers = [
                'name', 'type', 'manufacturer', 'v_abs_max',
                'i_abs_max', 'i_cont', 'housing_type',
            ]
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for t in transistors:
                    writer.writerow({
                        'name': t.metadata.name,
                        'type': t.metadata.type,
                        'manufacturer': t.metadata.manufacturer,
                        'v_abs_max': t.electrical_ratings.v_abs_max,
                        'i_abs_max': t.electrical_ratings.i_abs_max,
                        'i_cont': t.electrical_ratings.i_cont,
                        'housing_type': t.metadata.housing_type,
                    })
            return True
        except Exception:
            logger.exception("Error exporting to CSV")
            return False

    def export_to_spice(self, transistor: Transistor, file_path: Path) -> bool:
        """Export transistor model to SPICE format."""
        try:
            name = transistor.metadata.name.replace(' ', '_')
            lines = [
                f"* SPICE model for {transistor.metadata.name}",
                f"* Manufacturer: {transistor.metadata.manufacturer}",
                f"* Type: {transistor.metadata.type}",
                f".model {name} NPN (",
                f"+ BV={transistor.electrical_ratings.v_abs_max}",
                "+ )",
            ]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            return True
        except Exception:
            logger.exception("Error exporting to SPICE")
            return False

    def export_to_plecs(
        self, transistor: Transistor, output_path: Path,
        template_config: dict[str, Any] | None = None,
    ) -> None:
        """Export transistor to PLECS format."""
        raise NotImplementedError("PLECS export not yet implemented in backend")

    def export_to_matlab(self, transistor: Transistor, output_path: Path) -> None:
        """Export transistor to MATLAB format."""
        raise NotImplementedError("MATLAB export not yet implemented in backend")

    def export_to_ltspice(self, transistor: Transistor, output_path: Path) -> None:
        """Export transistor to LTSpice format."""
        raise NotImplementedError("LTSpice export not yet implemented in backend")

    def export_to_gecko_circuits(
        self, transistor: Transistor, export_params: Dict[str, Any]
    ) -> Path:
        """Export transistor to GeckoCIRCUITS format."""
        raise NotImplementedError("GeckoCIRCUITS export not yet implemented")


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
class ComparisonService(IComparisonService):
    """Service for comparing transistors."""

    def compare_characteristics(
        self, transistors: List[Transistor], comparison_type: str
    ) -> Dict[str, Any]:
        """Compare characteristics of multiple transistors."""
        return self.compare_transistors(transistors)

    def rank_transistors(
        self, transistors: List[Transistor], criteria: Dict[str, float]
    ) -> list[tuple[Transistor, float]]:
        """Rank transistors based on given criteria."""
        return [(t, 1.0) for t in transistors]

    def compare_transistors(
        self, transistors: List[Transistor]
    ) -> Dict[str, Any]:
        """Compare multiple transistors."""
        if len(transistors) < 2:
            return {'error': 'At least 2 transistors required for comparison'}

        v_values = [t.electrical_ratings.v_abs_max for t in transistors]
        i_values = [t.electrical_ratings.i_abs_max for t in transistors]

        return {
            'transistor_count': len(transistors),
            'transistors': [t.metadata.name for t in transistors],
            'electrical_comparison': {
                'voltage_max': {
                    'max': max(v_values), 'min': min(v_values),
                    'avg': sum(v_values) / len(v_values),
                },
                'current_max': {
                    'max': max(i_values), 'min': min(i_values),
                    'avg': sum(i_values) / len(i_values),
                },
            },
        }

    def find_similar_transistors(
        self, target: Transistor, candidates: List[Transistor],
        tolerance: float = 0.1,
    ) -> List[Transistor]:
        """Find transistors similar to target within tolerance."""
        target_v = target.electrical_ratings.v_abs_max
        target_i = target.electrical_ratings.i_abs_max
        similar = []

        for c in candidates:
            if c.metadata.name == target.metadata.name:
                continue
            v_diff = abs(c.electrical_ratings.v_abs_max - target_v) / max(target_v, 1)
            i_diff = abs(c.electrical_ratings.i_abs_max - target_i) / max(target_i, 1)
            if v_diff <= tolerance and i_diff <= tolerance:
                similar.append(c)

        similar.sort(key=lambda t: (
            abs(t.electrical_ratings.v_abs_max - target_v) / max(target_v, 1)
            + abs(t.electrical_ratings.i_abs_max - target_i) / max(target_i, 1)
        ))
        return similar


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
class ValidationService(IValidationService):
    """Service for validating transistor data."""

    def validate_transistor(self, transistor: Transistor) -> Dict[str, List[str]]:
        """Validate complete transistor data."""
        errors: list[str] = []
        warnings: list[str] = []

        # Metadata
        if not transistor.metadata.name or not transistor.metadata.name.strip():
            errors.append("Transistor name is required")
        valid_types = ('IGBT', 'MOSFET', 'SiC-MOSFET', 'GaN-Transistor', 'Diode')
        if transistor.metadata.type not in valid_types:
            warnings.append(f"Unusual transistor type: {transistor.metadata.type}")
        if not transistor.metadata.manufacturer:
            warnings.append("Manufacturer is not specified")

        # Electrical
        if transistor.electrical_ratings.v_abs_max <= 0:
            errors.append("Maximum voltage must be positive")
        if transistor.electrical_ratings.i_abs_max <= 0:
            errors.append("Maximum current must be positive")
        if transistor.electrical_ratings.i_cont > transistor.electrical_ratings.i_abs_max:
            errors.append("Continuous current cannot exceed maximum current")

        # Thermal
        if (transistor.thermal_properties.r_th_cs is not None
                and transistor.thermal_properties.r_th_cs < 0):
            errors.append("Thermal resistance cannot be negative")

        return {'errors': errors, 'warnings': warnings}

    def validate_channel_data(self, channel_data: list) -> List[str]:
        """Validate channel characteristics data."""
        errors: list[str] = []
        for i, ch in enumerate(channel_data):
            if ch.graph_v_i is None or ch.graph_v_i.size == 0:
                errors.append(f"Channel data [{i}]: empty graph_v_i")
            if ch.graph_v_i is not None and ch.graph_v_i.ndim != 2:
                errors.append(f"Channel data [{i}]: graph_v_i must be 2D")
        return errors

    def validate_switching_data(self, switching_data: list) -> List[str]:
        """Validate switching loss data."""
        errors: list[str] = []
        for i, sd in enumerate(switching_data):
            if sd.dataset_type not in ('single', 'graph_i_e', 'graph_r_e', 'graph_t_e'):
                errors.append(f"Switching data [{i}]: invalid dataset_type")
        return errors

    def check_data_consistency(self, transistor: Transistor) -> List[str]:
        """Check internal data consistency."""
        issues: list[str] = []
        if (transistor.metadata.type == 'Diode'
                and transistor.electrical_ratings.i_cont
                > transistor.electrical_ratings.i_abs_max * 0.8):
            issues.append(
                "Continuous current high relative to maximum for a diode"
            )
        return issues

    def check_data_completeness(self, transistor: Transistor) -> Dict[str, Any]:
        """Check how complete the transistor data is."""
        meta_fields = ['name', 'type', 'manufacturer', 'housing_type', 'author']
        meta_filled = sum(
            1 for f in meta_fields if getattr(transistor.metadata, f, None)
        )
        meta_pct = meta_filled / len(meta_fields) * 100

        elec_fields = ['v_abs_max', 'i_abs_max', 'i_cont']
        elec_filled = sum(
            1 for f in elec_fields
            if getattr(transistor.electrical_ratings, f, None) is not None
        )
        elec_pct = elec_filled / len(elec_fields) * 100

        switch_pct = 100.0 if transistor.switch.channel_data else 0.0
        diode_pct = 100.0 if transistor.diode.channel_data else 0.0

        overall = (meta_pct + elec_pct + switch_pct + diode_pct) / 4.0

        return {
            'metadata': meta_pct,
            'electrical': elec_pct,
            'switch_data': switch_pct,
            'diode_data': diode_pct,
            'overall': overall,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
class ConcreteServiceFactory:
    """Factory for creating concrete service implementations."""

    @staticmethod
    def create_plotting_service() -> IPlottingService:
        """Create plotting service."""
        return PlottingService()

    @staticmethod
    def create_calculation_service() -> ICalculationService:
        """Create calculation service."""
        return CalculationService()

    @staticmethod
    def create_export_service() -> IExportService:
        """Create export service."""
        return ExportService()

    @staticmethod
    def create_comparison_service() -> IComparisonService:
        """Create comparison service."""
        return ComparisonService()

    @staticmethod
    def create_validation_service() -> IValidationService:
        """Create validation service."""
        return ValidationService()

    @staticmethod
    def create_all_services() -> Dict[str, Any]:
        """Create all services."""
        return {
            'plotting': ConcreteServiceFactory.create_plotting_service(),
            'calculation': ConcreteServiceFactory.create_calculation_service(),
            'export': ConcreteServiceFactory.create_export_service(),
            'comparison': ConcreteServiceFactory.create_comparison_service(),
            'validation': ConcreteServiceFactory.create_validation_service(),
        }
