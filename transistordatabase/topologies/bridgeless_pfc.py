"""Bridgeless PFC converter topology loss analysis.

Calculates semiconductor conduction and switching losses for a bridgeless
(totem-pole) PFC converter operating in continuous conduction mode.

The model computes average duty cycle, RMS input current, and uses the
transistor's channel data and switching energy data to estimate losses.

References:
    [1] L. Huber, Y. Jang, M. M. Jovanovic, "Performance Evaluation of
        Bridgeless PFC Boost Rectifiers," IEEE Trans. Power Electron.,
        vol. 23, no. 3, pp. 1381-1390, May 2008.
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
class BridgelessPFCParams:
    """Operating parameters for bridgeless PFC.

    :param v_in_rms: Input RMS voltage in V (e.g., 230).
    :param v_out: Output DC voltage in V (e.g., 400).
    :param p_out: Output power in W.
    :param f_sw: Switching frequency in Hz.
    :param l_boost: Boost inductance in H.
    :param eta_est: Estimated efficiency for input current calculation.
    """

    v_in_rms: float
    v_out: float
    p_out: float
    f_sw: float
    l_boost: float
    eta_est: float = 0.95


@dataclass
class BridgelessPFCResult:
    """Loss analysis result for bridgeless PFC.

    :param p_cond_switch: Switch conduction loss in W.
    :param p_sw_switch: Switch switching loss in W.
    :param p_cond_diode: Diode conduction loss in W.
    :param p_sw_diode: Diode switching loss (reverse recovery) in W.
    :param p_total: Total semiconductor loss in W.
    :param duty_avg: Average duty cycle (dimensionless).
    :param i_rms: Input RMS current in A.
    """

    p_cond_switch: float
    p_sw_switch: float
    p_cond_diode: float
    p_sw_diode: float
    p_total: float
    duty_avg: float
    i_rms: float


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

    Searches for ``graph_i_e`` datasets and interpolates energy at the
    requested current. Returns 0.0 when no usable data is available.

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
            # Linear scaling from a single data point
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


def _get_linearized_diode(
    transistor: Transistor,
    i_channel: float,
    t_j: float = 25.0,
    v_g: float = 0.0,
) -> Optional[LinearizedModel]:
    """Attempt to linearize the diode at an operating point.

    :param transistor: Transistor instance.
    :param i_channel: Channel current in A.
    :param t_j: Junction temperature in deg C.
    :param v_g: Gate voltage in V.
    :return: Linearized model or None if data is insufficient.
    """
    try:
        return transistor.diode.linearize_at_operating_point(
            t_j, v_g, i_channel,
        )
    except (ValueError, IndexError):
        return None


class BridgelessPFCTopology:
    """Bridgeless PFC topology loss analyzer.

    Computes semiconductor losses for a bridgeless (totem-pole) PFC boost
    converter operating in continuous conduction mode with sinusoidal
    input current.

    :Example:

        >>> from transistordatabase.topologies import BridgelessPFCTopology
        >>> topo = BridgelessPFCTopology()
        >>> result = topo.calculate_losses(transistor, params)
        >>> print(f"Total loss: {result.p_total:.1f} W")
    """

    def calculate_losses(
        self,
        transistor: Transistor,
        params: BridgelessPFCParams,
    ) -> BridgelessPFCResult:
        """Calculate semiconductor losses for bridgeless PFC.

        The method computes:
        - Input RMS current from output power and estimated efficiency
        - Average duty cycle from the voltage conversion ratio
        - Switch conduction loss using linearized R_ds_on model
        - Switch switching loss from E_on + E_off curves
        - Diode conduction loss using linearized V_f / R_f model
        - Diode reverse recovery loss from E_rr data

        :param transistor: Transistor with switch and diode data.
        :param params: Bridgeless PFC operating parameters.
        :return: Loss analysis result.
        :raises ValueError: If any parameter is non-positive.
        """
        _validate_positive(params.v_in_rms, "v_in_rms")
        _validate_positive(params.v_out, "v_out")
        _validate_positive(params.p_out, "p_out")
        _validate_positive(params.f_sw, "f_sw")
        _validate_positive(params.l_boost, "l_boost")

        # --- Derived quantities ---
        v_in_peak = params.v_in_rms * math.sqrt(2)
        i_in_rms = params.p_out / (params.v_in_rms * params.eta_est)

        # Average duty cycle: D_avg ~ 1 - V_in_peak / V_out
        duty_avg = max(1.0 - v_in_peak / params.v_out, 0.0)

        # Average input current (rectified sine mean)
        i_avg = i_in_rms * 2 * math.sqrt(2) / math.pi

        # --- Switch conduction loss ---
        # P_cond_sw = R_ds_on * I_rms^2 * D
        sw_model = _get_linearized_switch(transistor, i_avg)
        if sw_model is not None:
            r_ds_on = sw_model.r_channel
        else:
            # Default fallback
            r_ds_on = 0.05
        p_cond_switch = r_ds_on * i_in_rms**2 * duty_avg

        # --- Switch switching loss ---
        # P_sw = (E_on + E_off) * f_sw
        e_on = _interpolate_switching_energy(
            transistor.switch.e_on_data, i_avg,
        )
        e_off = _interpolate_switching_energy(
            transistor.switch.e_off_data, i_avg,
        )
        p_sw_switch = (e_on + e_off) * params.f_sw

        # --- Diode conduction loss ---
        # P_cond_diode = V_f * I_avg + R_f * I_rms^2 * (1 - D)
        diode_model = _get_linearized_diode(transistor, i_avg)
        if diode_model is not None:
            v_f = diode_model.v0_channel
            r_f = diode_model.r_channel
        else:
            v_f = 0.7
            r_f = 0.01
        p_cond_diode = (
            v_f * i_avg + r_f * i_in_rms**2 * (1.0 - duty_avg)
        )

        # --- Diode reverse recovery loss ---
        e_rr = _interpolate_switching_energy(
            transistor.diode.e_rr_data, i_avg,
        )
        p_sw_diode = e_rr * params.f_sw

        p_total = p_cond_switch + p_sw_switch + p_cond_diode + p_sw_diode

        return BridgelessPFCResult(
            p_cond_switch=p_cond_switch,
            p_sw_switch=p_sw_switch,
            p_cond_diode=p_cond_diode,
            p_sw_diode=p_sw_diode,
            p_total=p_total,
            duty_avg=duty_avg,
            i_rms=i_in_rms,
        )
