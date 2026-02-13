"""LLC resonant converter topology loss analysis.

Calculates semiconductor losses for a half-bridge LLC resonant converter.
The model uses first-harmonic approximation (FHA) to derive resonant
tank currents and determines ZVS conditions based on the relationship
between switching frequency and resonant frequency.

References:
    [1] B. Yang, F. C. Lee, A. J. Zhang, G. Huang, "LLC Resonant
        Converter for Front End DC/DC Conversion," in Proc. IEEE APEC,
        2002, pp. 1108-1112.
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
class LLCParams:
    """Operating parameters for LLC resonant converter.

    :param v_in: Input DC voltage in V.
    :param v_out: Output DC voltage in V.
    :param p_out: Output power in W.
    :param f_sw: Switching frequency in Hz.
    :param f_r: Resonant frequency in Hz.
    :param l_r: Resonant inductance in H.
    :param l_m: Magnetizing inductance in H.
    :param c_r: Resonant capacitance in F.
    :param n: Transformer turns ratio (N_primary / N_secondary).
    """

    v_in: float
    v_out: float
    p_out: float
    f_sw: float
    f_r: float
    l_r: float
    l_m: float
    c_r: float
    n: float


@dataclass
class LLCResult:
    """Loss analysis result for LLC resonant converter.

    :param p_cond_primary: Primary-side conduction loss in W.
    :param p_sw_primary: Primary-side switching loss in W.
    :param p_cond_secondary: Secondary-side conduction (rectifier) loss in W.
    :param p_total: Total semiconductor loss in W.
    :param i_rms_resonant: RMS current through resonant tank in A.
    :param gain: Voltage gain M = V_out / (V_in / 2 / n).
    :param is_zvs: Whether primary-side ZVS is achieved.
    """

    p_cond_primary: float
    p_sw_primary: float
    p_cond_secondary: float
    p_total: float
    i_rms_resonant: float
    gain: float
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


class LLCTopology:
    """LLC resonant converter topology loss analyzer.

    Computes semiconductor losses for a half-bridge LLC resonant converter
    with center-tapped secondary rectification. Primary switches achieve
    ZVS when the switching frequency is below the resonant frequency.

    :Example:

        >>> from transistordatabase.topologies import LLCTopology
        >>> topo = LLCTopology()
        >>> result = topo.calculate_losses(
        ...     primary_transistor, secondary_transistor, params
        ... )
        >>> print(f"Gain: {result.gain:.3f}, ZVS: {result.is_zvs}")
    """

    def calculate_losses(
        self,
        primary_transistor: Transistor,
        secondary_transistor: Transistor,
        params: LLCParams,
    ) -> LLCResult:
        """Calculate LLC converter losses.

        Primary switches achieve ZVS when ``f_sw <= f_r`` because the
        magnetizing current provides reactive energy to charge/discharge
        the output capacitances during the dead time.

        :param primary_transistor: Transistor for the primary half-bridge.
        :param secondary_transistor: Transistor for the secondary rectifier.
        :param params: LLC operating parameters.
        :return: Loss analysis result.
        :raises ValueError: If any parameter is non-positive.
        """
        _validate_positive(params.v_in, "v_in")
        _validate_positive(params.v_out, "v_out")
        _validate_positive(params.p_out, "p_out")
        _validate_positive(params.f_sw, "f_sw")
        _validate_positive(params.f_r, "f_r")
        _validate_positive(params.l_r, "l_r")
        _validate_positive(params.l_m, "l_m")
        _validate_positive(params.c_r, "c_r")
        _validate_positive(params.n, "n")

        # --- Derived quantities ---
        omega_sw = 2.0 * math.pi * params.f_sw
        f_n = params.f_sw / params.f_r  # Normalised frequency

        # Voltage gain M = V_out / (V_in / 2 / n)
        gain = params.v_out / (params.v_in / (2.0 * params.n))

        # --- ZVS condition ---
        # Primary-side ZVS when f_sw <= f_r (inductive region)
        is_zvs = params.f_sw <= params.f_r

        # --- Resonant tank RMS current (FHA approximation) ---
        # Characteristic impedance and quality factor
        z_r = math.sqrt(params.l_r / params.c_r)
        r_ac = (8.0 * params.n**2 / math.pi**2) * (
            params.v_out**2 / params.p_out
        )
        q = z_r / r_ac if r_ac > 0 else 0.0

        # RMS current estimate from power and voltage
        v_in_fund = 2.0 * params.v_in / math.pi  # Fundamental of square wave
        if v_in_fund > 0:
            # Impedance of resonant tank at f_sw
            x_lr = omega_sw * params.l_r
            x_cr = 1.0 / (omega_sw * params.c_r) if omega_sw > 0 else 0.0
            x_lm = omega_sw * params.l_m
            # Parallel combination of L_m and R_ac
            z_parallel_mag = (
                x_lm * r_ac / math.sqrt(x_lm**2 + r_ac**2)
                if (x_lm**2 + r_ac**2) > 0
                else 0.0
            )
            z_total = math.sqrt(
                (x_lr - x_cr)**2 + z_parallel_mag**2,
            )
            i_rms_resonant = (
                v_in_fund / (math.sqrt(2) * z_total)
                if z_total > 0
                else params.p_out / (params.v_in / 2.0)
            )
        else:
            i_rms_resonant = params.p_out / (params.v_in / 2.0)

        # Magnetizing peak current (for ZVS turn-off current)
        i_mag_peak = params.v_in / (4.0 * params.f_sw * params.l_m)

        # Secondary-side RMS current
        i_rms_secondary = i_rms_resonant / params.n

        # --- Primary conduction loss ---
        # Half-bridge: 2 switches, each sees full RMS current
        sw_model_pri = _get_linearized_model(
            primary_transistor, "switch", i_rms_resonant,
        )
        r_ds_on_pri = sw_model_pri.r_channel if sw_model_pri else 0.05
        p_cond_primary = 2.0 * r_ds_on_pri * i_rms_resonant**2 * 0.5

        # --- Primary switching loss ---
        if is_zvs:
            # ZVS: switching at magnetizing current (near zero-current)
            # Only turn-off loss at magnetizing current level
            e_off_pri = _interpolate_switching_energy(
                primary_transistor.switch.e_off_data, i_mag_peak,
            )
            p_sw_primary = 2.0 * e_off_pri * params.f_sw
        else:
            e_on_pri = _interpolate_switching_energy(
                primary_transistor.switch.e_on_data, i_rms_resonant,
            )
            e_off_pri = _interpolate_switching_energy(
                primary_transistor.switch.e_off_data, i_rms_resonant,
            )
            p_sw_primary = 2.0 * (e_on_pri + e_off_pri) * params.f_sw

        # --- Secondary conduction loss (diode rectifier) ---
        diode_model = _get_linearized_model(
            secondary_transistor, "diode", i_rms_secondary,
        )
        if diode_model is not None:
            v_f = diode_model.v0_channel
            r_f = diode_model.r_channel
        else:
            v_f = 0.7
            r_f = 0.01
        # Average rectifier current
        i_avg_secondary = params.p_out / params.v_out
        p_cond_secondary = (
            2.0 * (v_f * i_avg_secondary / 2.0
                   + r_f * (i_rms_secondary / math.sqrt(2))**2)
        )

        p_total = p_cond_primary + p_sw_primary + p_cond_secondary

        return LLCResult(
            p_cond_primary=p_cond_primary,
            p_sw_primary=p_sw_primary,
            p_cond_secondary=p_cond_secondary,
            p_total=p_total,
            i_rms_resonant=i_rms_resonant,
            gain=gain,
            is_zvs=is_zvs,
        )
