"""
Core domain models for the transistor database.

These models represent the core business entities using Python 3.10+ dataclass syntax.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import numpy.typing as npt


@dataclass
class TransistorMetadata:
    """Core metadata for a transistor."""

    name: str
    type: str  # IGBT, MOSFET, SiC-MOSFET, GaN-Transistor, etc.
    author: str
    manufacturer: str
    housing_type: str
    comment: Optional[str] = None
    datasheet_hyperlink: Optional[str] = None
    datasheet_date: Optional[datetime] = None
    datasheet_version: Optional[str] = None


@dataclass
class ElectricalRatings:
    """Electrical ratings and limits."""

    v_abs_max: float  # V
    i_abs_max: float  # A
    i_cont: float     # A
    t_j_max: float    # deg C


@dataclass
class ThermalProperties:
    """Thermal properties of the transistor."""

    housing_area: float    # m^2
    cooling_area: float    # m^2
    r_th_cs: Optional[float] = None      # K/W
    r_th_switch_cs: Optional[float] = None  # K/W
    r_th_diode_cs: Optional[float] = None   # K/W
    t_c_max: Optional[float] = None      # deg C


@dataclass
class FosterThermalModel:
    """Foster thermal RC network model for transient thermal behavior.

    Describes the transient temperature behavior as a thermal RC-network.
    Parameters can be estimated by curve-fitting transient temperature data
    or by manually specifying R, C, and tau vectors.
    """

    r_th_vector: Optional[list[float]] = None  # K/W per element
    r_th_total: Optional[float] = None         # K/W total
    c_th_vector: Optional[list[float]] = None  # J/K per element
    c_th_total: Optional[float] = None         # J/K total
    tau_vector: Optional[list[float]] = None   # s per element
    tau_total: Optional[float] = None          # s total
    graph_t_rthjc: Optional[npt.NDArray[np.float64]] = None  # 2D: [time, Z_th]

    def get_thermal_impedance(self, time: float) -> float:
        """Calculate thermal impedance at a given time using Foster model.

        :param time: Time point in seconds.
        :return: Thermal impedance Z_th(t) in K/W.
        """
        if self.r_th_vector is None or self.tau_vector is None:
            if self.r_th_total is not None:
                return self.r_th_total
            raise ValueError("No Foster model parameters available")

        z_th = 0.0
        for r_th, tau in zip(self.r_th_vector, self.tau_vector, strict=True):
            z_th += r_th * (1.0 - np.exp(-time / tau))
        return z_th


@dataclass
class GateChargeCurve:
    """Gate charge characteristics of a switch."""

    v_supply: float  # Drain-source / collector-emitter voltage
    t_j: float       # Junction temperature in deg C
    i_channel: float  # Channel current during measurement
    i_g: Optional[float] = None  # Gate current
    graph_q_v: Optional[npt.NDArray[np.float64]] = None  # 2D: [charge, voltage]


@dataclass
class SOA:
    """Safe Operating Area characteristics."""

    t_c: Optional[float] = None        # Case temperature in deg C
    time_pulse: Optional[float] = None  # Pulse duration in s
    graph_i_v: Optional[npt.NDArray[np.float64]] = field(
        default_factory=lambda: np.array([])
    )  # 2D: [voltage, current]


@dataclass
class VoltageDependentCapacitance:
    """Voltage-dependent capacitance data (C_oss, C_iss, C_rss)."""

    t_j: float  # Junction temperature in deg C
    graph_v_c: Optional[npt.NDArray[np.float64]] = None  # 2D: [voltage, capacitance]


@dataclass
class EffectiveOutputCapacitance:
    """Energy-related or time-related effective output capacitance."""

    c_o: float    # Fixed output capacitance in F
    v_gs: float   # Gate-source voltage in V
    v_ds: float   # Drain-source voltage in V


@dataclass
class TemperatureDependResistance:
    """Temperature-dependent on-resistance curve."""

    i_channel: float   # Channel current for measurement
    v_g: float         # Gate voltage
    dataset_type: str  # 't_r' or 't_factor' (normalized)
    graph_t_r: Optional[npt.NDArray[np.float64]] = None  # 2D: [temp, resistance]
    r_channel_nominal: Optional[float] = None  # Required for 't_factor' type


@dataclass
class RawMeasurementData:
    """RAW measurement data, e.g. from double pulse test."""

    dataset_type: str  # e.g. 'dpt_u_i', 'dpt_u_i_r'
    comment: Optional[str] = None
    measurement_date: Optional[datetime] = None
    measurement_testbench: Optional[str] = None
    commutation_device: Optional[str] = None
    t_j: Optional[float] = None         # deg C
    v_supply: Optional[float] = None     # V
    v_g: Optional[float] = None          # V
    v_g_off: Optional[float] = None      # V
    r_g: Optional[list[float]] = None    # Ohm
    r_g_off: Optional[list[float]] = None  # Ohm
    load_inductance: Optional[float] = None        # H
    commutation_inductance: Optional[float] = None  # H
    dpt_on_vds: Optional[list[npt.NDArray[np.float64]]] = None
    dpt_on_id: Optional[list[npt.NDArray[np.float64]]] = None
    dpt_off_vds: Optional[list[npt.NDArray[np.float64]]] = None
    dpt_off_id: Optional[list[npt.NDArray[np.float64]]] = None


@dataclass
class LinearizedModel:
    """Linearized Switch/Diode model at a specific operating point."""

    t_j: float          # Junction temperature in deg C
    i_channel: float    # Channel current in A
    r_channel: float    # Channel resistance in Ohm
    v0_channel: float   # Channel threshold voltage in V
    v_g: Optional[float] = None  # Gate voltage in V (mandatory for Switch)


@dataclass
class ChannelCharacteristics:
    """V-I characteristics for a channel at specific conditions."""

    t_j: float  # Junction temperature in deg C
    graph_v_i: npt.NDArray[np.float64]  # 2D array: [voltage, current]
    v_g: Optional[float] = None  # Gate voltage (mandatory for switch)

    def get_resistance_at_current(self, current: float) -> float:
        """Calculate channel resistance at a specific current via interpolation.

        :param current: Current at which to calculate resistance in A.
        :return: Channel resistance in Ohm.
        :raises ValueError: If current is outside the data range.
        """
        voltages = self.graph_v_i[0]
        currents = self.graph_v_i[1]

        if current <= 0:
            raise ValueError("Current must be positive")

        if current < np.min(currents) or current > np.max(currents):
            raise ValueError(
                f"Current {current} A is outside data range "
                f"[{np.min(currents):.2f}, {np.max(currents):.2f}] A"
            )

        voltage = float(np.interp(current, currents, voltages))
        return voltage / current if current != 0 else float('inf')


@dataclass
class SwitchingLossData:
    """Switching loss characteristics."""

    dataset_type: str  # 'single', 'graph_i_e', 'graph_r_e', 'graph_t_e'
    t_j: float        # deg C
    v_supply: float   # V
    v_g: float        # V

    # Optional scalar parameters
    e_x: Optional[float] = None  # Single-point switching energy in J
    r_g: Optional[float] = None  # Gate resistance in Ohm
    i_x: Optional[float] = None  # Current point in A
    v_g_off: Optional[float] = None  # Gate voltage for turn-off in V

    # Graph datasets (mutually exclusive based on dataset_type)
    graph_i_e: Optional[npt.NDArray[np.float64]] = None  # [current, energy]
    graph_r_e: Optional[npt.NDArray[np.float64]] = None  # [resistance, energy]
    graph_t_e: Optional[npt.NDArray[np.float64]] = None  # [temperature, energy]

    # Measurement metadata
    comment: Optional[str] = None
    measurement_date: Optional[datetime] = None
    measurement_testbench: Optional[str] = None
    commutation_device: Optional[str] = None
    load_inductance: Optional[float] = None
    commutation_inductance: Optional[float] = None


class ITransistorComponent(ABC):
    """Interface for transistor components (Switch/Diode)."""

    @abstractmethod
    def get_channel_data(
        self, t_j: float, v_g: Optional[float] = None
    ) -> List[ChannelCharacteristics]:
        """Get channel characteristics for given conditions."""

    @abstractmethod
    def linearize_at_operating_point(
        self, t_j: float, v_g: float, i_channel: float
    ) -> LinearizedModel:
        """Linearize component at a specific operating point."""


class Switch(ITransistorComponent):
    """Switch component with all switching characteristics."""

    def __init__(self) -> None:
        self.channel_data: List[ChannelCharacteristics] = []
        self.e_on_data: List[SwitchingLossData] = []
        self.e_off_data: List[SwitchingLossData] = []
        self.thermal_foster: Optional[FosterThermalModel] = None
        self.gate_charge_curves: List[GateChargeCurve] = []
        self.soa: List[SOA] = []
        self.r_channel_temp: List[TemperatureDependResistance] = []
        self.raw_measurement_data: List[RawMeasurementData] = []
        self.linearized_model: List[LinearizedModel] = []
        self.metadata: Dict[str, Any] = {}

    def get_channel_data(
        self, t_j: float, v_g: Optional[float] = None
    ) -> List[ChannelCharacteristics]:
        """Get channel data for specific temperature and gate voltage."""
        return [
            ch for ch in self.channel_data
            if ch.t_j == t_j and (v_g is None or ch.v_g == v_g)
        ]

    def linearize_at_operating_point(
        self, t_j: float, v_g: float, i_channel: float
    ) -> LinearizedModel:
        """Linearize switch at operating point.

        Uses V-I curve to find voltage at given current, then calculates
        r_channel (slope) and v0_channel (intercept) of the linear model:
        v = v0_channel + r_channel * i

        :param t_j: Junction temperature in deg C.
        :param v_g: Gate voltage in V.
        :param i_channel: Channel current in A.
        :return: LinearizedModel with r_channel and v0_channel.
        :raises ValueError: If no matching channel data is found.
        """
        channel_data = self.get_channel_data(t_j, v_g)
        if not channel_data:
            raise ValueError(
                f"No channel data found for t_j={t_j}, v_g={v_g}"
            )

        ch = channel_data[0]
        voltages = ch.graph_v_i[0]
        currents = ch.graph_v_i[1]

        # Interpolate voltage at operating current
        v_at_i = float(np.interp(i_channel, currents, voltages))

        # Calculate linearized parameters using two-point method
        # Use a small delta around operating point
        delta = max(i_channel * 0.01, 0.1)
        i_low = max(i_channel - delta, float(np.min(currents)))
        i_high = min(i_channel + delta, float(np.max(currents)))

        v_low = float(np.interp(i_low, currents, voltages))
        v_high = float(np.interp(i_high, currents, voltages))

        r_channel = (v_high - v_low) / (i_high - i_low) if i_high != i_low else 0.0
        v0_channel = v_at_i - r_channel * i_channel

        return LinearizedModel(
            t_j=t_j,
            v_g=v_g,
            i_channel=i_channel,
            r_channel=r_channel,
            v0_channel=v0_channel,
        )


class Diode(ITransistorComponent):
    """Diode component with reverse characteristics."""

    def __init__(self) -> None:
        self.channel_data: List[ChannelCharacteristics] = []
        self.e_rr_data: List[SwitchingLossData] = []
        self.thermal_foster: Optional[FosterThermalModel] = None
        self.soa: List[SOA] = []
        self.raw_measurement_data: List[RawMeasurementData] = []
        self.linearized_model: List[LinearizedModel] = []
        self.metadata: Dict[str, Any] = {}

    def get_channel_data(
        self, t_j: float, v_g: Optional[float] = None
    ) -> List[ChannelCharacteristics]:
        """Get channel data for specific temperature."""
        return [ch for ch in self.channel_data if ch.t_j == t_j]

    def linearize_at_operating_point(
        self, t_j: float, v_g: float, i_channel: float
    ) -> LinearizedModel:
        """Linearize diode at operating point.

        :param t_j: Junction temperature in deg C.
        :param v_g: Gate voltage in V (may be unused for standard diodes).
        :param i_channel: Channel current in A.
        :return: LinearizedModel with r_channel and v0_channel.
        :raises ValueError: If no matching channel data is found.
        """
        channel_data = self.get_channel_data(t_j)
        if not channel_data:
            raise ValueError(f"No channel data found for t_j={t_j}")

        ch = channel_data[0]
        voltages = ch.graph_v_i[0]
        currents = ch.graph_v_i[1]

        v_at_i = float(np.interp(i_channel, currents, voltages))

        delta = max(i_channel * 0.01, 0.1)
        i_low = max(i_channel - delta, float(np.min(currents)))
        i_high = min(i_channel + delta, float(np.max(currents)))

        v_low = float(np.interp(i_low, currents, voltages))
        v_high = float(np.interp(i_high, currents, voltages))

        r_channel = (v_high - v_low) / (i_high - i_low) if i_high != i_low else 0.0
        v0_channel = v_at_i - r_channel * i_channel

        return LinearizedModel(
            t_j=t_j,
            v_g=v_g,
            i_channel=i_channel,
            r_channel=r_channel,
            v0_channel=v0_channel,
        )


class Transistor:
    """Main transistor aggregate containing all components and metadata."""

    def __init__(
        self,
        metadata: TransistorMetadata,
        electrical: ElectricalRatings,
        thermal: ThermalProperties,
    ) -> None:
        self.metadata = metadata
        self.electrical_ratings = electrical
        self.thermal_properties = thermal
        self.switch = Switch()
        self.diode = Diode()
        self.c_oss: List[VoltageDependentCapacitance] = []
        self.c_iss: List[VoltageDependentCapacitance] = []
        self.c_rss: List[VoltageDependentCapacitance] = []
        self.c_oss_er: Optional[EffectiveOutputCapacitance] = None
        self.c_oss_tr: Optional[EffectiveOutputCapacitance] = None
        self._working_point: Optional[Dict[str, Any]] = None

    @property
    def working_point(self) -> Optional[Dict[str, Any]]:
        """Current working point data."""
        return self._working_point

    def update_working_point(
        self, t_j: float, v_g: float, i_channel: float,
        component: str = "both",
    ) -> None:
        """Update working point for calculations."""
        wp_data: Dict[str, Any] = {}

        if component in ("switch", "both"):
            switch_wp = self.switch.linearize_at_operating_point(
                t_j, v_g, i_channel
            )
            wp_data["switch"] = switch_wp

        if component in ("diode", "both"):
            diode_wp = self.diode.linearize_at_operating_point(
                t_j, v_g, i_channel
            )
            wp_data["diode"] = diode_wp

        self._working_point = wp_data

    def get_component(self, component_type: str) -> ITransistorComponent:
        """Get specific component by type string.

        :param component_type: Either 'switch' or 'diode'.
        :return: The requested component.
        :raises ValueError: If component_type is invalid.
        """
        if component_type.lower() == "switch":
            return self.switch
        elif component_type.lower() == "diode":
            return self.diode
        else:
            raise ValueError(f"Unknown component type: {component_type}")
