"""Series Resonant Converter with ZVS (SRC-ZVS) topology loss analysis.

Calculates semiconductor losses for a full-bridge series resonant converter
operating above resonance to achieve zero-voltage switching.

References:
    [1] R. L. Steigerwald, "A Comparison of Half-Bridge Resonant Converter
        Topologies," IEEE Trans. Power Electron., vol. 3, no. 2,
        pp. 174-182, Apr 1988.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from transistordatabase.core.models import (
    LinearizedModel,
    SwitchingLossData,
    Transistor,
)


@dataclass
class SRCZVSParams:
    """Operating parameters for SRC-ZVS converter.

    :param v_in: Input DC voltage in V.
    :param v_out: Output DC voltage in V.
    :param p_out: Output power in W.
    :param f_sw: Switching frequency in Hz.
    :param l_r: Resonant inductance in H.
    :param c_r: Resonant capacitance in F.
    :param n: Transformer turns ratio (N_primary / N_secondary).
    """

    v_in: float
    v_out: float
    p_out: float
    f_sw: float
    l_r: float
    c_r: float
    n: float


@dataclass
class SRCZVSResult:
    """Loss analysis result for SRC-ZVS converter.

    :param p_cond: Total conduction loss in W.
    :param p_sw: Total switching loss in W.
    :param p_total: Total semiconductor loss in W.
    :param i_rms_resonant: RMS current through resonant tank in A.
    :param is_zvs: Whether ZVS is achieved.
    :param q_factor: Quality factor of the resonant tank.
    """

    p_cond: float
    p_sw: float
    p_total: float
    i_rms_resonant: float
    is_zvs: bool
    q_factor: float


def _validate_positive(value: float, name: str) -> None:
    """Validate that a value is strictly positive.

    :param value: Value to validate.
    :param name: Parameter name for the error message.
    :raises ValueError: If value is not positive.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def _interpolate_switching_energy(
    loss_data_list: list[SwitchingLossData],
    current: float,
) -> float:
    """Interpolate switching energy from loss data at a given current.

    :param loss_data_list: List of switching loss data entries.
    :param current: Current at which to interpolate in A.
    :return: Interpolated switching energy in J.
    """
    for loss_data in loss_data_list:
        if loss_data.graph_i_e is not None:
            graph = np.asarray(loss_data.graph_i_e, dtype=np.float64)
            if graph.ndim == 2 and graph.shape[0] >= 2:
                currents = graph[0]
                energies = graph[1]
                return float(np.interp(current, currents, energies))
        if loss_data.e_x is not None and loss_data.i_x is not None:
            if loss_data.i_x > 0:
                return loss_data.e_x * (current / loss_data.i_x)
    return 0.0


def _get_linearized_switch(
    transistor: Transistor,
    i_channel: float,
    t_j: float = 25.0,
    v_g: float = 15.0,
) -> Optional[LinearizedModel]:
    """Attempt to linearize the switch at an operating point.

    :param transistor: Transistor instance.
    :param i_channel: Channel current in A.
    :param t_j: Junction temperature in deg C.
    :param v_g: Gate voltage in V.
    :return: Linearized model or None if data is insufficient.
    """
    try:
        return transistor.switch.linearize_at_operating_point(
            t_j, v_g, i_channel,
        )
    except (ValueError, IndexError):
        return None


class SRCZVSTopology:
    """Series Resonant Converter with ZVS topology loss analyzer.

    Computes semiconductor losses for a full-bridge series resonant converter.
    ZVS is achieved when operating above the resonant frequency, where the
    tank presents an inductive impedance ensuring the current lags the
    voltage at the switching instants.

    :Example:

        >>> from transistordatabase.topologies import SRCZVSTopology
        >>> topo = SRCZVSTopology()
        >>> result = topo.calculate_losses(transistor, params)
        >>> print(f"Q = {result.q_factor:.2f}, ZVS: {result.is_zvs}")
    """

    def calculate_losses(
        self,
        transistor: Transistor,
        params: SRCZVSParams,
    ) -> SRCZVSResult:
        """Calculate SRC-ZVS converter losses.

        ZVS is achieved when ``f_sw > f_r`` (above-resonance operation)
        because the series tank then presents inductive impedance, causing
        current to lag voltage and enabling zero-voltage turn-on.

        :param transistor: Transistor with switch data.
        :param params: SRC-ZVS operating parameters.
        :return: Loss analysis result.
        :raises ValueError: If any parameter is non-positive.
        """
        _validate_positive(params.v_in, "v_in")
        _validate_positive(params.v_out, "v_out")
        _validate_positive(params.p_out, "p_out")
        _validate_positive(params.f_sw, "f_sw")
        _validate_positive(params.l_r, "l_r")
        _validate_positive(params.c_r, "c_r")
        _validate_positive(params.n, "n")

        # --- Derived quantities ---
        omega_sw = 2.0 * math.pi * params.f_sw
        f_r = 1.0 / (2.0 * math.pi * math.sqrt(params.l_r * params.c_r))

        # Characteristic impedance
        z_r = math.sqrt(params.l_r / params.c_r)

        # Equivalent AC load resistance (FHA)
        r_ac = (8.0 * params.n**2 / math.pi**2) * (
            params.v_out**2 / params.p_out
        )

        # Quality factor
        q_factor = z_r / r_ac if r_ac > 0 else 0.0

        # --- ZVS condition ---
        # ZVS when f_sw > f_r (inductive region, current lags voltage)
        is_zvs = params.f_sw > f_r

        # --- Resonant tank RMS current ---
        # Impedance at switching frequency
        x_l = omega_sw * params.l_r
        x_c = 1.0 / (omega_sw * params.c_r) if omega_sw > 0 else 0.0
        z_tank = math.sqrt((x_l - x_c) ** 2 + r_ac**2)

        # Fundamental of full-bridge square wave
        v_in_fund = 4.0 * params.v_in / (math.pi * math.sqrt(2))
        i_rms_resonant = v_in_fund / z_tank if z_tank > 0 else 0.0

        # Fallback: estimate from power
        if i_rms_resonant < 1e-9:
            i_rms_resonant = params.p_out / params.v_in

        # --- Conduction loss ---
        # Full-bridge: 4 switches, each conducts for approximately half period
        sw_model = _get_linearized_switch(transistor, i_rms_resonant)
        r_ds_on = sw_model.r_channel if sw_model else 0.05
        p_cond = 4.0 * r_ds_on * (i_rms_resonant / 2.0) ** 2

        # --- Switching loss ---
        if is_zvs:
            # ZVS: only turn-off losses
            e_off = _interpolate_switching_energy(
                transistor.switch.e_off_data, i_rms_resonant,
            )
            p_sw = 4.0 * e_off * params.f_sw
        else:
            e_on = _interpolate_switching_energy(
                transistor.switch.e_on_data, i_rms_resonant,
            )
            e_off = _interpolate_switching_energy(
                transistor.switch.e_off_data, i_rms_resonant,
            )
            p_sw = 4.0 * (e_on + e_off) * params.f_sw

        p_total = p_cond + p_sw

        return SRCZVSResult(
            p_cond=p_cond,
            p_sw=p_sw,
            p_total=p_total,
            i_rms_resonant=i_rms_resonant,
            is_zvs=is_zvs,
            q_factor=q_factor,
        )
