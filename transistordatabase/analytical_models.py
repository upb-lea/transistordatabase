"""Analytical switching loss and device models.

Provides physics-based models for estimating switching losses when
empirical data is incomplete or unavailable. Based on:

- Biela switching loss model (inductive switching)
- Gate charge model (switching time estimation)
- IGBT tail current model (turn-off with minority carrier tail)

References:
    [1] J. Biela, "Optimierung des elektromagnetisch integrierten
        Serien-Parallel-Resonanzkonverters", ETH Zurich, 2005.
    [2] B. J. Baliga, "Fundamentals of Power Semiconductor Devices",
        Springer, 2008.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import numpy.typing as npt


@dataclass
class BielaModelParams:
    """Parameters for the Biela inductive switching loss model.

    :param c_oss: Output capacitance at nominal voltage in F.
    :param q_g: Total gate charge in C.
    :param v_plateau: Gate plateau voltage in V.
    :param r_g_on: Gate resistance for turn-on in Ohm.
    :param r_g_off: Gate resistance for turn-off in Ohm.
    :param v_driver_on: Gate driver voltage for turn-on in V.
    :param v_driver_off: Gate driver voltage for turn-off in V.
    """

    c_oss: float
    q_g: float
    v_plateau: float
    r_g_on: float
    r_g_off: float
    v_driver_on: float = 15.0
    v_driver_off: float = -5.0


class BielaModel:
    """Biela analytical switching loss model for inductive switching.

    Estimates turn-on and turn-off energy based on device capacitances,
    gate charge, and circuit conditions. Suitable for hard-switched
    converters with inductive load.
    """

    def __init__(self, params: BielaModelParams) -> None:
        self.params = params

    def calc_e_on(
        self, v_dc: float, i_load: float, t_j: float = 25.0
    ) -> float:
        """Calculate turn-on switching energy.

        :param v_dc: DC bus voltage in V.
        :param i_load: Load current at switching instant in A.
        :param t_j: Junction temperature in deg C (for temp scaling).
        :return: Turn-on energy in J.
        """
        p = self.params

        # Current rise time (gate charging through Miller plateau)
        t_ri = (p.q_g * p.r_g_on) / (p.v_driver_on - p.v_plateau)

        # Voltage fall time (discharge of C_oss)
        t_fv = (p.c_oss * v_dc) / i_load if i_load > 0 else 0.0

        # Turn-on energy: overlap loss + capacitive loss
        e_overlap = 0.5 * v_dc * i_load * (t_ri + t_fv)
        e_coss = 0.5 * p.c_oss * v_dc**2

        # Temperature scaling (approximate +0.3%/K above 25C)
        temp_factor = 1.0 + 0.003 * max(t_j - 25.0, 0.0)

        return (e_overlap + e_coss) * temp_factor

    def calc_e_off(
        self, v_dc: float, i_load: float, t_j: float = 25.0
    ) -> float:
        """Calculate turn-off switching energy.

        :param v_dc: DC bus voltage in V.
        :param i_load: Load current at switching instant in A.
        :param t_j: Junction temperature in deg C.
        :return: Turn-off energy in J.
        """
        p = self.params

        # Voltage rise time (C_oss charging)
        t_rv = (p.c_oss * v_dc) / i_load if i_load > 0 else 0.0

        # Current fall time (gate discharging through Miller plateau)
        v_drive_off = abs(p.v_driver_off) if p.v_driver_off < 0 else 0.0
        t_fi = (p.q_g * p.r_g_off) / (p.v_plateau + v_drive_off)

        # Turn-off energy: overlap loss
        e_overlap = 0.5 * v_dc * i_load * (t_rv + t_fi)

        # Temperature scaling
        temp_factor = 1.0 + 0.003 * max(t_j - 25.0, 0.0)

        return e_overlap * temp_factor

    def calc_e_total(
        self, v_dc: float, i_load: float, t_j: float = 25.0
    ) -> float:
        """Calculate total switching energy (E_on + E_off).

        :param v_dc: DC bus voltage in V.
        :param i_load: Load current in A.
        :param t_j: Junction temperature in deg C.
        :return: Total switching energy in J.
        """
        return self.calc_e_on(v_dc, i_load, t_j) + self.calc_e_off(
            v_dc, i_load, t_j
        )

    def calc_switching_loss_curve(
        self, v_dc: float, currents: npt.NDArray[np.float64],
        t_j: float = 25.0,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64],
               npt.NDArray[np.float64]]:
        """Calculate switching loss curves over a range of currents.

        :param v_dc: DC bus voltage in V.
        :param currents: Array of current values in A.
        :param t_j: Junction temperature in deg C.
        :return: Tuple of (e_on_array, e_off_array, e_total_array) in J.
        """
        e_on = np.array([self.calc_e_on(v_dc, i, t_j) for i in currents])
        e_off = np.array([self.calc_e_off(v_dc, i, t_j) for i in currents])
        return e_on, e_off, e_on + e_off


@dataclass
class GateChargeModelParams:
    """Parameters for gate charge switching time model.

    :param q_gs: Gate-source charge in C.
    :param q_gd: Gate-drain (Miller) charge in C.
    :param q_g: Total gate charge in C.
    :param v_th: Threshold voltage in V.
    :param v_plateau: Plateau voltage in V.
    :param r_g: External gate resistance in Ohm.
    :param r_g_int: Internal gate resistance in Ohm.
    """

    q_gs: float
    q_gd: float
    q_g: float
    v_th: float
    v_plateau: float
    r_g: float
    r_g_int: float = 0.0


class GateChargeModel:
    """Gate charge based switching time estimation model.

    Estimates switching transition times from gate charge characteristics.
    Useful for predicting di/dt and dv/dt during switching.
    """

    def __init__(self, params: GateChargeModelParams) -> None:
        self.params = params

    def calc_turn_on_times(
        self, v_driver: float = 15.0
    ) -> dict[str, float]:
        """Calculate turn-on transition times.

        :param v_driver: Gate driver supply voltage in V.
        :return: Dict with 't_delay', 't_rise', 't_fall_v', 't_total' in s.
        """
        p = self.params
        r_total = p.r_g + p.r_g_int

        # Delay time: charge gate to threshold
        t_delay = r_total * p.q_gs * np.log(
            v_driver / (v_driver - p.v_th)
        ) if v_driver > p.v_th else 0.0

        # Current rise time: charge from threshold to plateau
        q_rise = p.q_gs - (p.q_gs * p.v_th / p.v_plateau)
        t_rise = r_total * q_rise / (v_driver - p.v_plateau) if v_driver > p.v_plateau else 0.0

        # Voltage fall time: Miller plateau (constant Vgs = V_plateau)
        t_fall_v = r_total * p.q_gd / (v_driver - p.v_plateau) if v_driver > p.v_plateau else 0.0

        return {
            't_delay': t_delay,
            't_rise': t_rise,
            't_fall_v': t_fall_v,
            't_total': t_delay + t_rise + t_fall_v,
        }

    def calc_turn_off_times(
        self, v_driver: float = 15.0, v_off: float = 0.0
    ) -> dict[str, float]:
        """Calculate turn-off transition times.

        :param v_driver: Gate driver on-state voltage in V.
        :param v_off: Gate driver off-state voltage in V (0 or negative).
        :return: Dict with 't_delay', 't_rise_v', 't_fall_i', 't_total' in s.
        """
        p = self.params
        r_total = p.r_g + p.r_g_int
        v_swing = v_driver - v_off

        # Delay: discharge from v_driver to plateau
        t_delay = r_total * (p.q_g - p.q_gd - p.q_gs) / v_swing if v_swing > 0 else 0.0

        # Voltage rise time: Miller plateau discharge
        t_rise_v = r_total * p.q_gd / (p.v_plateau - v_off) if p.v_plateau > v_off else 0.0

        # Current fall time: discharge below plateau to threshold
        t_fall_i = r_total * p.q_gs / (p.v_plateau - v_off) if p.v_plateau > v_off else 0.0

        return {
            't_delay': t_delay,
            't_rise_v': t_rise_v,
            't_fall_i': t_fall_i,
            't_total': t_delay + t_rise_v + t_fall_i,
        }


@dataclass
class IgbtModelParams:
    """Parameters for IGBT turn-off tail current model.

    :param v_ce_sat: Collector-emitter saturation voltage in V.
    :param i_tail_factor: Tail current as fraction of load current.
    :param tau_tail: Tail current time constant in s.
    :param t_fall: Current fall time in s.
    """

    v_ce_sat: float = 1.5
    i_tail_factor: float = 0.1
    tau_tail: float = 1e-6
    t_fall: float = 200e-9


class IgbtModel:
    """IGBT-specific model accounting for minority carrier tail current.

    IGBTs have a tail current during turn-off due to stored minority
    carriers in the drift region. This model estimates the additional
    energy loss from the tail current.
    """

    def __init__(self, params: IgbtModelParams) -> None:
        self.params = params

    def calc_tail_energy(self, v_dc: float, i_load: float) -> float:
        """Calculate energy loss from IGBT tail current.

        :param v_dc: DC bus voltage in V.
        :param i_load: Load current in A.
        :return: Tail current energy loss in J.
        """
        p = self.params
        i_tail = i_load * p.i_tail_factor
        # E_tail = V_dc * I_tail * tau_tail (exponential decay integral)
        return v_dc * i_tail * p.tau_tail

    def calc_e_off_total(
        self, v_dc: float, i_load: float,
        e_off_mosfet: Optional[float] = None,
    ) -> float:
        """Calculate total IGBT turn-off energy including tail current.

        :param v_dc: DC bus voltage in V.
        :param i_load: Load current in A.
        :param e_off_mosfet: Base turn-off energy (overlap) in J.
        :return: Total turn-off energy in J.
        """
        p = self.params

        if e_off_mosfet is None:
            # Simple estimate: overlap during current fall
            e_off_mosfet = 0.5 * v_dc * i_load * p.t_fall

        e_tail = self.calc_tail_energy(v_dc, i_load)
        return e_off_mosfet + e_tail

    def calc_conduction_loss(
        self, i_avg: float, i_rms: float
    ) -> float:
        """Calculate IGBT conduction loss using V_CE(sat) model.

        :param i_avg: Average current in A.
        :param i_rms: RMS current in A.
        :return: Conduction power loss in W.
        """
        p = self.params
        # P_cond = V_CE0 * I_avg + r_CE * I_rms^2
        # Simplified: use V_CE_sat as constant
        return p.v_ce_sat * i_avg
