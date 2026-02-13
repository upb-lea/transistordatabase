"""Dual Active Bridge (DAB) converter topology loss analysis.

Calculates semiconductor conduction and switching losses for a single-phase
DAB converter using single-phase-shift (SPS) modulation.

The model derives primary and secondary RMS currents from the applied
phase shift, transformer turns ratio, and series inductance, then uses
transistor data to compute conduction and switching losses.

References:
    [1] M. N. Kheraluwala, R. W. Gascoigne, D. M. Divan, E. D. Baumann,
        "Performance Characterization of a High-Power Dual Active Bridge
        DC-to-DC Converter," IEEE Trans. Ind. Appl., vol. 28, no. 6,
        pp. 1294-1301, Nov/Dec 1992.
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
class DABParams:
    """Operating parameters for DAB converter.

    :param v_in: Input DC voltage in V.
    :param v_out: Output DC voltage in V.
    :param p_out: Output power in W.
    :param f_sw: Switching frequency in Hz.
    :param l_s: Series inductance in H.
    :param n: Transformer turns ratio (N_primary / N_secondary).
    :param phi: Phase shift angle in radians.
    """

    v_in: float
    v_out: float
    p_out: float
    f_sw: float
    l_s: float
    n: float
    phi: float


@dataclass
class DABResult:
    """Loss analysis result for DAB converter.

    :param p_cond_primary: Primary-side conduction loss in W.
    :param p_sw_primary: Primary-side switching loss in W.
    :param p_cond_secondary: Secondary-side conduction loss in W.
    :param p_sw_secondary: Secondary-side switching loss in W.
    :param p_total: Total semiconductor loss in W.
    :param i_rms_primary: Primary RMS current in A.
    :param i_rms_secondary: Secondary RMS current in A.
    :param is_zvs: Whether ZVS is achieved on all switches.
    """

    p_cond_primary: float
    p_sw_primary: float
    p_cond_secondary: float
    p_sw_secondary: float
    p_total: float
    i_rms_primary: float
    i_rms_secondary: float
    is_zvs: bool


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


def _get_linearized_model(
    transistor: Transistor,
    component: str,
    i_channel: float,
    t_j: float = 25.0,
    v_g: float = 15.0,
) -> Optional[LinearizedModel]:
    """Attempt to linearize a component at an operating point.

    :param transistor: Transistor instance.
    :param component: Either ``'switch'`` or ``'diode'``.
    :param i_channel: Channel current in A.
    :param t_j: Junction temperature in deg C.
    :param v_g: Gate voltage in V.
    :return: Linearized model or None if data is insufficient.
    """
    try:
        comp = transistor.get_component(component)
        return comp.linearize_at_operating_point(t_j, v_g, i_channel)
    except (ValueError, IndexError):
        return None


class DABTopology:
    """Dual Active Bridge topology loss analyzer.

    Computes semiconductor losses for a single-phase DAB converter with
    single-phase-shift modulation. ZVS is achieved when the phase shift
    provides sufficient inductive energy to charge/discharge the output
    capacitances of the MOSFETs.

    :Example:

        >>> from transistordatabase.topologies import DABTopology
        >>> topo = DABTopology()
        >>> result = topo.calculate_losses(
        ...     primary_transistor, secondary_transistor, params
        ... )
        >>> print(f"ZVS achieved: {result.is_zvs}")
    """

    def calculate_losses(
        self,
        primary_transistor: Transistor,
        secondary_transistor: Transistor,
        params: DABParams,
    ) -> DABResult:
        """Calculate DAB converter losses.

        ZVS is achieved when the inductor current at the switching instant
        is sufficient to charge/discharge the MOSFET output capacitances.
        With SPS modulation this requires sufficient phase shift angle.

        :param primary_transistor: Transistor for the primary full-bridge.
        :param secondary_transistor: Transistor for the secondary full-bridge.
        :param params: DAB operating parameters.
        :return: Loss analysis result.
        :raises ValueError: If any parameter is non-positive.
        """
        _validate_positive(params.v_in, "v_in")
        _validate_positive(params.v_out, "v_out")
        _validate_positive(params.p_out, "p_out")
        _validate_positive(params.f_sw, "f_sw")
        _validate_positive(params.l_s, "l_s")
        _validate_positive(params.n, "n")

        # --- Derived quantities ---
        omega = 2.0 * math.pi * params.f_sw
        d = abs(params.phi) / math.pi  # Normalised phase shift

        # Primary-side RMS current (SPS modulation)
        # I_rms_pri = V_in / (omega * L_s) * sqrt(D*(1-D) + ...)
        # Simplified analytical formula for SPS:
        v_sec_ref = params.n * params.v_out
        i_rms_primary = (
            params.v_in
            / (2.0 * math.sqrt(3) * omega * params.l_s)
            * math.sqrt(
                params.v_in**2 * (1.0 - d)
                + v_sec_ref**2 * d
                + params.v_in * v_sec_ref * (6.0 * d * (1.0 - d) - 1.0)
                if (
                    params.v_in**2 * (1.0 - d)
                    + v_sec_ref**2 * d
                    + params.v_in * v_sec_ref * (6.0 * d * (1.0 - d) - 1.0)
                )
                > 0
                else 0.0
            )
        )

        # If the formula gives 0 or tiny, estimate from power
        if i_rms_primary < 1e-9:
            i_rms_primary = params.p_out / params.v_in

        i_rms_secondary = i_rms_primary / params.n

        # Peak current at switching instant for ZVS check
        i_peak_primary = (
            params.v_in * (1.0 - d) + v_sec_ref * d
        ) / (2.0 * omega * params.l_s)

        # --- ZVS condition ---
        # ZVS when inductor current at switching instant > 0
        # For SPS, this requires phi > 0 and sufficient deadtime energy
        is_zvs = i_peak_primary > 0 and d > 0

        # --- Primary conduction loss ---
        sw_model_pri = _get_linearized_model(
            primary_transistor, "switch", i_rms_primary,
        )
        r_ds_on_pri = sw_model_pri.r_channel if sw_model_pri else 0.05
        # 4 switches in a full-bridge, each conducts for half period
        p_cond_primary = 4.0 * r_ds_on_pri * (i_rms_primary / 2.0) ** 2

        # --- Primary switching loss ---
        if is_zvs:
            # ZVS: only turn-off losses matter (turn-on is lossless)
            e_off_pri = _interpolate_switching_energy(
                primary_transistor.switch.e_off_data, i_peak_primary,
            )
            p_sw_primary = 4.0 * e_off_pri * params.f_sw
        else:
            e_on_pri = _interpolate_switching_energy(
                primary_transistor.switch.e_on_data, i_peak_primary,
            )
            e_off_pri = _interpolate_switching_energy(
                primary_transistor.switch.e_off_data, i_peak_primary,
            )
            p_sw_primary = 4.0 * (e_on_pri + e_off_pri) * params.f_sw

        # --- Secondary conduction loss ---
        sw_model_sec = _get_linearized_model(
            secondary_transistor, "switch", i_rms_secondary,
        )
        r_ds_on_sec = sw_model_sec.r_channel if sw_model_sec else 0.05
        p_cond_secondary = 4.0 * r_ds_on_sec * (i_rms_secondary / 2.0) ** 2

        # --- Secondary switching loss ---
        i_peak_secondary = i_peak_primary / params.n
        if is_zvs:
            e_off_sec = _interpolate_switching_energy(
                secondary_transistor.switch.e_off_data, i_peak_secondary,
            )
            p_sw_secondary = 4.0 * e_off_sec * params.f_sw
        else:
            e_on_sec = _interpolate_switching_energy(
                secondary_transistor.switch.e_on_data, i_peak_secondary,
            )
            e_off_sec = _interpolate_switching_energy(
                secondary_transistor.switch.e_off_data, i_peak_secondary,
            )
            p_sw_secondary = 4.0 * (e_on_sec + e_off_sec) * params.f_sw

        p_total = (
            p_cond_primary
            + p_sw_primary
            + p_cond_secondary
            + p_sw_secondary
        )

        return DABResult(
            p_cond_primary=p_cond_primary,
            p_sw_primary=p_sw_primary,
            p_cond_secondary=p_cond_secondary,
            p_sw_secondary=p_sw_secondary,
            p_total=p_total,
            i_rms_primary=i_rms_primary,
            i_rms_secondary=i_rms_secondary,
            is_zvs=is_zvs,
        )
