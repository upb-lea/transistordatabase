"""
Loss estimation engine wrapping the TransistorDatabase library.

All public functions are defensive: they return None for missing data
instead of propagating exceptions from TDB interpolation methods.

Physics references
------------------
- Conduction:  P = V0·I_mean + R·I_rms²   (IGBT / diode model)
               P = R_ds·I_rms²             (MOSFET, V0 = 0)
- Switching:   P = (E_on + E_off) · f_sw
               E(I, V) ≈ E_meas(I, V_meas) · (V / V_meas)   [linear V-scaling]
- Diode RR:    P_rr = E_rr(I, V) · f_sw
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

import transistordatabase as tdb
from transistordatabase.data_classes import ChannelData, SwitchEnergyData
from transistordatabase.exceptions import MissingDataError

from .models import CircuitRequirements, CurrentWaveform, LossBreakdown, Topology

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Topology → current waveform
# ---------------------------------------------------------------------------

def compute_waveform(req: CircuitRequirements) -> CurrentWaveform:
    """
    Derive per-switch current waveform parameters from topology and specs.

    Assumptions
    -----------
    * CCM (continuous conduction mode).
    * Low inductor current ripple (≤ 20 %, ripple ignored for RMS calc).
    * For half-bridge inverter: sinusoidal modulation, D ≈ 0.5 per switch.

    Parameters
    ----------
    req : CircuitRequirements
        User-supplied circuit requirements.

    Returns
    -------
    CurrentWaveform
        Waveform quantities for the high-side (or only) switch.
    """
    if req.topology == Topology.BUCK:
        # High-side switch carries current during D, diode during (1-D)
        d = req.v_out / req.v_bus  # type: ignore[operator]
        i_peak = req.i_load
        return CurrentWaveform(
            duty_cycle=d,
            i_sw_rms=req.i_load * math.sqrt(d),
            i_sw_mean=req.i_load * d,
            i_diode_rms=req.i_load * math.sqrt(1.0 - d),
            i_diode_mean=req.i_load * (1.0 - d),
            i_peak=i_peak,
        )

    elif req.topology == Topology.BOOST:
        # v_out here is the INPUT (low) voltage; v_bus is the output (high) voltage
        d = 1.0 - req.v_out / req.v_bus  # type: ignore[operator]
        # I_in (switch sees input current):  power balance  η≈1
        i_in = req.i_load / (1.0 - d)  # ≈ I_load · V_bus / V_out
        i_peak = i_in
        return CurrentWaveform(
            duty_cycle=d,
            i_sw_rms=i_in * math.sqrt(d),
            i_sw_mean=i_in * d,
            i_diode_rms=req.i_load * math.sqrt(1.0 - d),
            i_diode_mean=req.i_load * (1.0 - d),
            i_peak=i_peak,
        )

    else:  # HALF_BRIDGE / inverter
        # Each switch is on ≈50 % of the time; sinusoidal load
        # i_load is the peak sinusoidal current
        d = 0.5
        i_peak = req.i_load
        i_rms_half = req.i_load / 2.0          # half-wave RMS of full sine
        return CurrentWaveform(
            duty_cycle=d,
            i_sw_rms=i_rms_half,
            i_sw_mean=req.i_load / math.pi,    # half-wave average
            i_diode_rms=i_rms_half,
            i_diode_mean=req.i_load / math.pi,
            i_peak=i_peak,
        )


# ---------------------------------------------------------------------------
# Safe energy interpolation helpers
# ---------------------------------------------------------------------------

def _energy_from_graph_i_e(
    eed: SwitchEnergyData,
    i: float,
    v_bus: float,
) -> Optional[float]:
    """
    Interpolate a graph_i_e SwitchEnergyData at current *i* and scale to v_bus.

    Parameters
    ----------
    eed     : SwitchEnergyData with dataset_type == 'graph_i_e'
    i       : operating current [A]
    v_bus   : operating bus voltage [V] (for linear V-scaling)

    Returns
    -------
    float | None
        Energy in joules at (i, v_bus), or None if data is invalid.
    """
    if eed.graph_i_e is None:
        return None
    i_vec = np.asarray(eed.graph_i_e[0], dtype=float)
    e_vec = np.asarray(eed.graph_i_e[1], dtype=float)
    if i_vec.size < 2:
        return None
    e_at_i = float(np.interp(i, i_vec, e_vec, left=e_vec[0], right=e_vec[-1]))
    if eed.v_supply and eed.v_supply > 0:
        return e_at_i * v_bus / eed.v_supply
    return e_at_i


def _energy_from_single(eed: SwitchEnergyData, v_bus: float) -> Optional[float]:
    """
    Return the scalar energy from a 'single' dataset, scaled to v_bus.
    """
    if eed.e_x is None:
        return None
    if eed.v_supply and eed.v_supply > 0:
        return float(eed.e_x) * v_bus / eed.v_supply
    return float(eed.e_x)


def _best_energy(
    datasets: list[SwitchEnergyData],
    t_j: float,
    v_g: float,
    i: float,
    v_bus: float,
) -> tuple[Optional[float], Optional[SwitchEnergyData]]:
    """
    Pick the nearest operating-point dataset and interpolate switching energy.

    Strategy (in priority order)
    ----------------------------
    1. graph_i_e  – most accurate (full I-E curve at known r_g, v_g, v_supply)
    2. single     – scalar measurement at (i_x, r_g)
    3. graph_r_e  – E vs R_g at fixed i_x; not usable without r_g → skipped

    Returns
    -------
    (energy_J, used_dataset) or (None, None)
    """
    if not datasets:
        return None, None

    def _score(d: SwitchEnergyData) -> float:
        """Normalised distance in (t_j/10, v_g) space."""
        return math.hypot((d.t_j - t_j) / 10.0, (d.v_g or 0.0) - v_g)

    # --- try graph_i_e first ---
    g_ie = [d for d in datasets if d.dataset_type == "graph_i_e"]
    if g_ie:
        best = min(g_ie, key=_score)
        val = _energy_from_graph_i_e(best, i, v_bus)
        if val is not None:
            return val, best

    # --- fallback to single ---
    singles = [d for d in datasets if d.dataset_type == "single"]
    if singles:
        best = min(singles, key=_score)
        val = _energy_from_single(best, v_bus)
        if val is not None:
            return val, best

    return None, None


# ---------------------------------------------------------------------------
# Channel linearisation helpers
# ---------------------------------------------------------------------------

@dataclass
class ChannelLinear:
    """Linear model  V = V0 + R·I  at an operating point."""
    v0: float          # forward voltage [V]  (0 for MOSFET)
    r: float           # on-resistance / slope [Ω]
    t_j_used: float
    v_g_used: float


def _linearise_channel(
    transistor: tdb.Transistor,
    channel_list: list[ChannelData],
    switch_or_diode: str,
    t_j: float,
    v_g: float,
    i: float,
) -> Optional[ChannelLinear]:
    """
    Find the nearest (t_j, v_g) operating point in *channel_list* and
    call ``transistor.calc_lin_channel``.

    Unlike ``update_wp``, this function does NOT require non-empty e_on/e_off.

    Parameters
    ----------
    transistor      : loaded Transistor object
    channel_list    : transistor.switch.channel or transistor.diode.channel
    switch_or_diode : 'switch' or 'diode'
    t_j             : target junction temperature [°C]
    v_g             : target gate voltage [V] (ignored for standard diodes)
    i               : channel current for linearisation [A]
    """
    if not channel_list:
        return None

    # Clip i to avoid ValueError from calc_lin_channel
    i_safe = min(i, transistor.i_abs_max * 0.99)
    if i_safe <= 0:
        i_safe = transistor.i_abs_max * 0.1

    def _dist(ch: ChannelData) -> float:
        return math.hypot((ch.t_j - t_j) / 10.0, ((ch.v_g or 0.0) - v_g))

    # For standard diodes (IGBT body diode), v_g is irrelevant
    best = min(channel_list, key=_dist)

    try:
        v_ch, r_ch = transistor.calc_lin_channel(
            best.t_j, best.v_g, i_safe, switch_or_diode
        )
        return ChannelLinear(
            v0=float(v_ch) if v_ch is not None else 0.0,
            r=float(r_ch) if r_ch is not None else 0.0,
            t_j_used=best.t_j,
            v_g_used=best.v_g or 0.0,
        )
    except (ValueError, TypeError, IndexError) as exc:
        logger.debug(
            "calc_lin_channel failed for %s (%s, t_j=%.0f, v_g=%.1f, i=%.1f): %s",
            transistor.name, switch_or_diode, best.t_j, best.v_g or 0, i_safe, exc,
        )
        return None


# ---------------------------------------------------------------------------
# Main loss estimator
# ---------------------------------------------------------------------------

def estimate_losses(
    transistor: tdb.Transistor,
    waveform: CurrentWaveform,
    req: CircuitRequirements,
) -> LossBreakdown:
    """
    Estimate all power-loss components for *transistor* at the given operating
    point, handling missing data gracefully.

    Parameters
    ----------
    transistor : loaded tdb.Transistor
    waveform   : CurrentWaveform from compute_waveform()
    req        : CircuitRequirements (for V_bus, f_sw, t_j_op, v_g)

    Returns
    -------
    LossBreakdown
        Partial or full loss estimate; components not computable are None.
    """
    t_j = req.t_j_op
    v_g = req.v_g
    v_bus = req.v_bus
    f_sw = req.f_sw

    p_sw_cond: Optional[float] = None
    p_sw_on: Optional[float] = None
    p_sw_off: Optional[float] = None
    p_diode_cond: Optional[float] = None
    p_diode_rr: Optional[float] = None

    sw_channel_source: Optional[str] = None
    e_on_source: Optional[str] = None
    e_off_source: Optional[str] = None
    e_rr_source: Optional[str] = None
    e_on_v_scale: Optional[float] = None
    e_off_v_scale: Optional[float] = None

    # ------------------------------------------------------------------
    # 1. Switch conduction loss
    # ------------------------------------------------------------------
    sw_lin = _linearise_channel(
        transistor,
        transistor.switch.channel,
        "switch",
        t_j,
        v_g,
        waveform.i_peak,
    )
    if sw_lin is not None:
        # P = V0·I_mean + R·I_rms²
        p_sw_cond = (
            sw_lin.v0 * waveform.i_sw_mean
            + sw_lin.r * waveform.i_sw_rms ** 2
        )
        sw_channel_source = f"t_j={sw_lin.t_j_used:.0f}°C, v_g={sw_lin.v_g_used:.1f}V"

    # ------------------------------------------------------------------
    # 2. Turn-on switching loss
    # ------------------------------------------------------------------
    e_on_j, e_on_ds = _best_energy(
        transistor.switch.e_on, t_j, v_g, waveform.i_peak, v_bus
    )
    if e_on_j is not None and e_on_ds is not None:
        p_sw_on = e_on_j * f_sw
        e_on_source = (
            f"t_j={e_on_ds.t_j:.0f}°C, v_g={e_on_ds.v_g:.1f}V, "
            f"v_supply={e_on_ds.v_supply:.0f}V [{e_on_ds.dataset_type}]"
        )
        if e_on_ds.v_supply and e_on_ds.v_supply > 0:
            e_on_v_scale = v_bus / e_on_ds.v_supply

    # ------------------------------------------------------------------
    # 3. Turn-off switching loss
    # ------------------------------------------------------------------
    e_off_j, e_off_ds = _best_energy(
        transistor.switch.e_off, t_j, v_g, waveform.i_peak, v_bus
    )
    if e_off_j is not None and e_off_ds is not None:
        p_sw_off = e_off_j * f_sw
        e_off_source = (
            f"t_j={e_off_ds.t_j:.0f}°C, v_g={e_off_ds.v_g:.1f}V, "
            f"v_supply={e_off_ds.v_supply:.0f}V [{e_off_ds.dataset_type}]"
        )
        if e_off_ds.v_supply and e_off_ds.v_supply > 0:
            e_off_v_scale = v_bus / e_off_ds.v_supply

    # ------------------------------------------------------------------
    # 4. Diode conduction loss  (body diode or anti-parallel diode)
    # ------------------------------------------------------------------
    # For SiC-MOSFET/GaN: body diode v_g is negative (e.g. -2 V or 0 V)
    # We search all diode channel entries
    diode_v_g = -2.0 if transistor.type in ("SiC-MOSFET", "GaN-Transistor") else v_g
    d_lin = _linearise_channel(
        transistor,
        transistor.diode.channel,
        "diode",
        t_j,
        diode_v_g,
        waveform.i_peak,
    )
    if d_lin is not None:
        p_diode_cond = (
            d_lin.v0 * waveform.i_diode_mean
            + d_lin.r * waveform.i_diode_rms ** 2
        )

    # ------------------------------------------------------------------
    # 5. Reverse-recovery loss
    # ------------------------------------------------------------------
    e_rr_j, e_rr_ds = _best_energy(
        transistor.diode.e_rr, t_j, v_g, waveform.i_peak, v_bus
    )
    if e_rr_j is not None and e_rr_ds is not None:
        p_diode_rr = e_rr_j * f_sw
        e_rr_source = (
            f"t_j={e_rr_ds.t_j:.0f}°C, v_supply={e_rr_ds.v_supply:.0f}V"
        )

    # ------------------------------------------------------------------
    # 6. Total
    # ------------------------------------------------------------------
    components = [p_sw_cond, p_sw_on, p_sw_off, p_diode_cond, p_diode_rr]
    p_total = sum(c for c in components if c is not None)

    return LossBreakdown(
        p_sw_cond_w=round(p_sw_cond, 4) if p_sw_cond is not None else None,
        p_sw_on_w=round(p_sw_on, 4) if p_sw_on is not None else None,
        p_sw_off_w=round(p_sw_off, 4) if p_sw_off is not None else None,
        p_diode_cond_w=round(p_diode_cond, 4) if p_diode_cond is not None else None,
        p_diode_rr_w=round(p_diode_rr, 4) if p_diode_rr is not None else None,
        p_total_w=round(p_total, 4),
        sw_channel_source=sw_channel_source,
        e_on_source=e_on_source,
        e_off_source=e_off_source,
        e_rr_source=e_rr_source,
        e_on_v_scale=round(e_on_v_scale, 3) if e_on_v_scale is not None else None,
        e_off_v_scale=round(e_off_v_scale, 3) if e_off_v_scale is not None else None,
    )


# ---------------------------------------------------------------------------
# Data-confidence scoring
# ---------------------------------------------------------------------------

def data_confidence(transistor: tdb.Transistor, losses: LossBreakdown) -> float:
    """
    Return 0–100 % indicating what fraction of relevant loss components
    were successfully estimated.

    Weights
    -------
    Switch channel (conduction):  30 %
    E_on data:                    25 %
    E_off data:                   25 %
    Diode channel (conduction):   10 %
    E_rr data:                    10 %
    """
    score = 0.0
    if losses.p_sw_cond_w is not None:
        score += 30.0
    if losses.p_sw_on_w is not None:
        score += 25.0
    if losses.p_sw_off_w is not None:
        score += 25.0
    if losses.p_diode_cond_w is not None:
        score += 10.0
    if losses.p_diode_rr_w is not None:
        score += 10.0
    return round(score, 1)


def missing_data_notes(
    transistor: tdb.Transistor,
    losses: LossBreakdown,
) -> list[str]:
    """Human-readable list of what data is absent."""
    notes: list[str] = []
    if losses.p_sw_cond_w is None:
        notes.append("No switch channel (V-I) data — conduction loss not estimated.")
    if losses.p_sw_on_w is None:
        if not transistor.switch.e_on:
            notes.append("No E_on datasets in database.")
        else:
            notes.append("E_on data present but graph_i_e / single formats not usable.")
    if losses.p_sw_off_w is None:
        if not transistor.switch.e_off:
            notes.append("No E_off datasets in database.")
        else:
            notes.append("E_off data present but graph_i_e / single formats not usable.")
    if losses.p_diode_cond_w is None:
        if not transistor.diode.channel:
            notes.append("No diode channel data — diode conduction loss not estimated.")
    if losses.p_diode_rr_w is None:
        if not transistor.diode.e_rr:
            notes.append(
                "No E_rr data (body diode only, or SiC — RR loss typically negligible)."
            )
    # Warn if significant voltage extrapolation
    if losses.e_on_v_scale is not None and losses.e_on_v_scale > 2.0:
        notes.append(
            f"E_on V-scaling factor {losses.e_on_v_scale:.1f}× — "
            "measurement V_supply was much lower than V_bus."
        )
    if losses.e_off_v_scale is not None and losses.e_off_v_scale > 2.0:
        notes.append(
            f"E_off V-scaling factor {losses.e_off_v_scale:.1f}× — "
            "measurement V_supply was much lower than V_bus."
        )
    return notes
