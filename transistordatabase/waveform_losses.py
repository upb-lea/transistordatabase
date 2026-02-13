"""Waveform-based semiconductor loss calculation.

Calculate conduction and switching losses from arbitrary current/voltage
waveforms and gate signal edges. Supports ZVS/ZCS detection.

Based on time-domain integration methods for power semiconductor losses
in switched-mode power supplies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import numpy.typing as npt

from transistordatabase.core.models import (
    ChannelCharacteristics,
    LinearizedModel,
    SwitchingLossData,
)


@dataclass
class WaveformData:
    """Time-domain waveform data for loss calculation.

    :param time: Time array in seconds.
    :param current: Current waveform in A.
    :param voltage: Voltage waveform in V (optional, for ZVS detection).
    :param gate: Gate signal (0/1 or analog) for switching edge detection.
    """

    time: npt.NDArray[np.float64]
    current: npt.NDArray[np.float64]
    voltage: Optional[npt.NDArray[np.float64]] = None
    gate: Optional[npt.NDArray[np.float64]] = None


@dataclass
class LossResult:
    """Result of waveform loss calculation.

    :param p_cond: Average conduction loss in W.
    :param p_sw_on: Average turn-on switching loss in W.
    :param p_sw_off: Average turn-off switching loss in W.
    :param p_total: Total average loss in W.
    :param n_cycles: Number of switching cycles detected.
    :param switching_instants: Array of switching time instants.
    """

    p_cond: float
    p_sw_on: float
    p_sw_off: float
    p_total: float
    n_cycles: int
    switching_instants: npt.NDArray[np.float64]


def calc_conduction_loss(
    waveform: WaveformData,
    linearized: LinearizedModel,
) -> float:
    """Calculate average conduction loss from current waveform.

    Uses linearized model: V = V0 + R * I, P_cond = V0 * I_avg + R * I_rms^2.

    :param waveform: Time-domain waveform data.
    :param linearized: Linearized device model at operating point.
    :return: Average conduction power loss in W.
    """
    dt = np.diff(waveform.time)
    i_mid = (waveform.current[:-1] + waveform.current[1:]) / 2.0

    # Only count intervals where device is conducting (positive current)
    conducting = i_mid > 0
    if not np.any(conducting):
        return 0.0

    t_total = waveform.time[-1] - waveform.time[0]
    if t_total <= 0:
        return 0.0

    # P_cond = (1/T) * integral(V0*i + R*i^2) dt
    i_cond = np.where(conducting, i_mid, 0.0)
    e_cond = np.sum(
        (linearized.v0_channel * i_cond + linearized.r_channel * i_cond**2) * dt
    )

    return float(e_cond / t_total)


def calc_conduction_loss_from_channel(
    waveform: WaveformData,
    channel: ChannelCharacteristics,
) -> float:
    """Calculate conduction loss using full V-I characteristic curve.

    More accurate than linearized model; uses interpolation on the actual curve.

    :param waveform: Time-domain waveform data.
    :param channel: Channel V-I characteristic.
    :return: Average conduction power loss in W.
    """
    dt = np.diff(waveform.time)
    i_mid = (waveform.current[:-1] + waveform.current[1:]) / 2.0

    t_total = waveform.time[-1] - waveform.time[0]
    if t_total <= 0:
        return 0.0

    # Interpolate voltage drop for each current sample
    currents_curve = channel.graph_v_i[1]
    voltages_curve = channel.graph_v_i[0]

    i_cond = np.clip(i_mid, 0, float(np.max(currents_curve)))
    v_drop = np.interp(i_cond, currents_curve, voltages_curve)

    # P = (1/T) * integral(v(i) * i) dt
    e_cond = np.sum(v_drop * i_cond * dt)
    return float(e_cond / t_total)


def detect_switching_edges(
    waveform: WaveformData,
    threshold: float = 0.5,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Detect turn-on and turn-off edges from gate signal.

    :param waveform: Waveform data with gate signal.
    :param threshold: Gate signal threshold for edge detection.
    :return: Tuple of (turn_on_times, turn_off_times) arrays.
    :raises ValueError: If gate signal is not provided.
    """
    if waveform.gate is None:
        raise ValueError("Gate signal required for edge detection")

    gate = waveform.gate
    time = waveform.time

    # Detect edges by comparing consecutive samples
    gate_high = gate > threshold
    rising = ~gate_high[:-1] & gate_high[1:]
    falling = gate_high[:-1] & ~gate_high[1:]

    turn_on_times = time[:-1][rising]
    turn_off_times = time[:-1][falling]

    return turn_on_times, turn_off_times


def detect_zvs(
    waveform: WaveformData,
    v_threshold_fraction: float = 0.1,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Detect zero-voltage switching (ZVS) and hard-switching events.

    :param waveform: Waveform data with voltage and gate signals.
    :param v_threshold_fraction: Fraction of max voltage below which ZVS is declared.
    :return: Tuple of (zvs_times, hard_sw_times) arrays.
    :raises ValueError: If voltage or gate signal is missing.
    """
    if waveform.voltage is None or waveform.gate is None:
        raise ValueError("Voltage and gate signals required for ZVS detection")

    turn_on_times, _ = detect_switching_edges(waveform)
    v_max = np.max(np.abs(waveform.voltage))
    v_threshold = v_max * v_threshold_fraction

    zvs_times = []
    hard_sw_times = []

    for t_on in turn_on_times:
        idx = np.searchsorted(waveform.time, t_on)
        if idx < len(waveform.voltage):
            v_at_switch = abs(waveform.voltage[idx])
            if v_at_switch < v_threshold:
                zvs_times.append(t_on)
            else:
                hard_sw_times.append(t_on)

    return np.array(zvs_times), np.array(hard_sw_times)


def calc_switching_loss(
    waveform: WaveformData,
    e_on_data: list[SwitchingLossData],
    e_off_data: list[SwitchingLossData],
    t_j: float = 25.0,
    zvs_reduction: float = 0.0,
) -> tuple[float, float]:
    """Calculate average switching losses from waveform and loss data.

    :param waveform: Waveform data with gate signal.
    :param e_on_data: Turn-on switching loss data.
    :param e_off_data: Turn-off switching loss data.
    :param t_j: Junction temperature for loss lookup.
    :param zvs_reduction: Fraction of E_on reduction during ZVS (0-1).
    :return: Tuple of (p_sw_on, p_sw_off) average switching power in W.
    :raises ValueError: If gate signal is missing.
    """
    if waveform.gate is None:
        raise ValueError("Gate signal required for switching loss calculation")

    turn_on_times, turn_off_times = detect_switching_edges(waveform)
    t_total = waveform.time[-1] - waveform.time[0]
    if t_total <= 0:
        return 0.0, 0.0

    # Calculate turn-on losses
    e_on_total = 0.0
    for t_on in turn_on_times:
        idx = np.searchsorted(waveform.time, t_on)
        i_at_switch = abs(waveform.current[min(idx, len(waveform.current) - 1)])
        e_on = _interpolate_energy(e_on_data, i_at_switch, t_j)

        # Apply ZVS reduction if voltage data available
        if zvs_reduction > 0 and waveform.voltage is not None:
            v_max = np.max(np.abs(waveform.voltage))
            v_at_switch = abs(waveform.voltage[min(idx, len(waveform.voltage) - 1)])
            if v_at_switch < 0.1 * v_max:
                e_on *= (1.0 - zvs_reduction)

        e_on_total += e_on

    # Calculate turn-off losses
    e_off_total = 0.0
    for t_off in turn_off_times:
        idx = np.searchsorted(waveform.time, t_off)
        i_at_switch = abs(waveform.current[min(idx, len(waveform.current) - 1)])
        e_off_total += _interpolate_energy(e_off_data, i_at_switch, t_j)

    p_sw_on = e_on_total / t_total
    p_sw_off = e_off_total / t_total
    return float(p_sw_on), float(p_sw_off)


def calc_total_loss(
    waveform: WaveformData,
    linearized: LinearizedModel,
    e_on_data: list[SwitchingLossData],
    e_off_data: list[SwitchingLossData],
    t_j: float = 25.0,
) -> LossResult:
    """Calculate total semiconductor losses from waveform data.

    :param waveform: Time-domain waveform data with current and gate.
    :param linearized: Linearized device model.
    :param e_on_data: Turn-on loss data.
    :param e_off_data: Turn-off loss data.
    :param t_j: Junction temperature.
    :return: LossResult with all loss components.
    """
    p_cond = calc_conduction_loss(waveform, linearized)

    if waveform.gate is not None:
        p_sw_on, p_sw_off = calc_switching_loss(
            waveform, e_on_data, e_off_data, t_j
        )
        turn_on_times, turn_off_times = detect_switching_edges(waveform)
        switching_instants = np.sort(
            np.concatenate([turn_on_times, turn_off_times])
        )
        n_cycles = max(len(turn_on_times), len(turn_off_times))
    else:
        p_sw_on = 0.0
        p_sw_off = 0.0
        switching_instants = np.array([])
        n_cycles = 0

    return LossResult(
        p_cond=p_cond,
        p_sw_on=p_sw_on,
        p_sw_off=p_sw_off,
        p_total=p_cond + p_sw_on + p_sw_off,
        n_cycles=n_cycles,
        switching_instants=switching_instants,
    )


def _interpolate_energy(
    loss_data: list[SwitchingLossData],
    current: float,
    t_j: float,
) -> float:
    """Interpolate switching energy from loss data at given current.

    :param loss_data: List of switching loss datasets.
    :param current: Current at switching instant in A.
    :param t_j: Junction temperature in deg C.
    :return: Interpolated switching energy in J.
    """
    if not loss_data:
        return 0.0

    # Find datasets matching closest temperature
    temps = list({d.t_j for d in loss_data})
    if not temps:
        return 0.0

    closest_t = min(temps, key=lambda x: abs(x - t_j))
    matching = [d for d in loss_data if d.t_j == closest_t]

    for data in matching:
        if data.dataset_type == 'graph_i_e' and data.graph_i_e is not None:
            currents = data.graph_i_e[0]
            energies = data.graph_i_e[1]
            return float(np.interp(current, currents, energies))
        if data.dataset_type == 'single' and data.e_x is not None:
            if data.i_x is not None and data.i_x > 0:
                return data.e_x * (current / data.i_x)
            return data.e_x

    return 0.0
