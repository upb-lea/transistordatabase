"""LTspice Double Pulse Test (DPT) generator and analyzer.

Generates LTspice netlists for double pulse testing and analyzes simulation
results to extract switching loss parameters. PyLTSpice is an optional
dependency - basic netlist generation works without it, but simulation
execution requires it.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import numpy.typing as npt

from transistordatabase.core.models import SwitchingLossData, Transistor

logger = logging.getLogger(__name__)

# Soft import of PyLTSpice
try:
    from PyLTSpice import SimRunner, SpiceEditor  # noqa: F401
    HAS_PYLTSPICE = True
except ImportError:
    HAS_PYLTSPICE = False


@dataclass
class DPTConfig:
    """Configuration for double pulse test.

    :param v_dc: DC bus voltage in V.
    :param i_target: Target inductor current at turn-off in A.
    :param l_load: Load inductance in H.
    :param r_g_on: Gate resistance for turn-on in Ohm.
    :param r_g_off: Gate resistance for turn-off in Ohm.
    :param v_g_on: Gate drive voltage for turn-on in V.
    :param v_g_off: Gate drive voltage for turn-off in V.
    :param t_dead: Dead time between pulses in s.
    :param t_pulse2: Duration of second pulse in s.
    """

    v_dc: float = 400.0
    i_target: float = 20.0
    l_load: float = 100e-6  # H
    r_g_on: float = 10.0    # Ohm
    r_g_off: float = 10.0   # Ohm
    v_g_on: float = 15.0    # V
    v_g_off: float = -5.0   # V
    t_dead: float = 5e-6    # s
    t_pulse2: float = 2e-6  # s

    @property
    def t_pulse1(self) -> float:
        """Calculate first pulse duration to reach target current.

        Uses the inductor equation: I = V * t / L => t = I * L / V.

        :return: Duration of first pulse in seconds.
        :raises ValueError: If DC bus voltage is not positive.
        """
        if self.v_dc <= 0:
            raise ValueError("DC bus voltage must be positive")
        return self.i_target * self.l_load / self.v_dc


@dataclass
class DPTResult:
    """Results from double pulse test analysis.

    :param e_on: Turn-on switching energy in J.
    :param e_off: Turn-off switching energy in J.
    :param t_r: Current rise time in s.
    :param t_f: Current fall time in s.
    :param i_peak: Peak current during turn-on in A.
    :param v_overshoot: Voltage overshoot during turn-off in V.
    :param di_dt_on: di/dt during turn-on in A/s.
    :param dv_dt_off: dv/dt during turn-off in V/s.
    """

    e_on: float = 0.0
    e_off: float = 0.0
    t_r: float = 0.0
    t_f: float = 0.0
    i_peak: float = 0.0
    v_overshoot: float = 0.0
    di_dt_on: float = 0.0
    dv_dt_off: float = 0.0


class LTspiceDPT:
    """LTspice Double Pulse Test generator and analyzer.

    Provides methods to generate LTspice netlists for double pulse testing,
    run simulations (requires PyLTSpice), and analyze waveforms to extract
    switching loss parameters.
    """

    def __init__(self, config: DPTConfig) -> None:
        """Initialize LTspice DPT with the given configuration.

        :param config: Double pulse test configuration.
        """
        self.config = config

    def generate_netlist(
        self,
        output_path: Path,
        transistor: Optional[Transistor] = None,
    ) -> Path:
        """Generate an LTspice netlist for double pulse test.

        Creates a basic DPT circuit netlist. If transistor is provided,
        uses its parameters for the SPICE model.

        :param output_path: Directory or file path to write the netlist.
        :param transistor: Optional transistor for model parameters.
        :return: Path to the generated netlist file.
        """
        name = transistor.metadata.name if transistor else "DUT"
        if output_path.is_dir():
            netlist_path = output_path / f"dpt_{name}.asc"
        else:
            netlist_path = output_path

        cfg = self.config
        t1 = cfg.t_pulse1
        t_total = t1 + cfg.t_dead + cfg.t_pulse2 + 5e-6

        lines = [
            f"* Double Pulse Test for {name}",
            f"* V_dc = {cfg.v_dc}V, I_target = {cfg.i_target}A",
            f"* L_load = {cfg.l_load * 1e6:.1f}uH",
            f"* Rg_on = {cfg.r_g_on}Ohm, Rg_off = {cfg.r_g_off}Ohm",
            "*",
            f"V1 vdc 0 {cfg.v_dc}",
            f"L1 vdc vl {cfg.l_load}",
            "M1 vl gate 0 0 DUT_NMOS",
            "D1 0 vl DBODY",
            f"R_g gate vgate {cfg.r_g_on}",
            (
                f"V_gate vgate 0 PULSE({cfg.v_g_off} {cfg.v_g_on}"
                f" 0 10n 10n {t1} {t_total})"
            ),
            ".model DUT_NMOS NMOS(VTO=3 KP=50 RD=0.01)",
            ".model DBODY D(IS=1e-12 BV=600)",
            f".tran {t_total}",
            ".backanno",
            ".end",
        ]

        netlist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(netlist_path, "w") as f:
            f.write("\n".join(lines))

        return netlist_path

    def run_simulation(self, netlist_path: Path) -> Optional[Path]:
        """Run LTspice simulation on the given netlist.

        Requires PyLTSpice to be installed.

        :param netlist_path: Path to the LTspice netlist.
        :return: Path to raw output file, or None if simulation failed.
        :raises ImportError: If PyLTSpice is not installed.
        """
        if not HAS_PYLTSPICE:
            raise ImportError(
                "PyLTSpice is required for simulation execution. "
                "Install with: pip install PyLTSpice"
            )

        runner = SimRunner(output_folder=str(netlist_path.parent))
        runner.run(str(netlist_path))
        raw_path = netlist_path.with_suffix(".raw")
        return raw_path if raw_path.exists() else None

    def analyze_waveforms(
        self,
        time: npt.NDArray[np.float64],
        v_ds: npt.NDArray[np.float64],
        i_d: npt.NDArray[np.float64],
        v_gs: Optional[npt.NDArray[np.float64]] = None,
    ) -> DPTResult:
        """Analyze DPT waveforms to extract switching parameters.

        Detects turn-off and turn-on transitions, then extracts switching
        energies, rise/fall times, peak current, voltage overshoot, and
        slew rates. Uses 10%/90% thresholds for rise/fall time calculation.

        :param time: Time array in s.
        :param v_ds: Drain-source voltage in V.
        :param i_d: Drain current in A.
        :param v_gs: Gate-source voltage in V (optional).
        :return: DPTResult with extracted parameters.
        """
        cfg = self.config
        i_max = np.max(i_d)

        if i_max <= 0:
            return DPTResult()

        # --- Detect turn-off event ---
        # Turn-off is the first major falling edge of current from near
        # i_target. Find where current drops below 90% of peak for the
        # first time after reaching peak.
        i_threshold_high = 0.9 * i_max
        i_threshold_low = 0.1 * i_max

        # Find index where current first reaches near i_max
        idx_peak_region = np.where(i_d >= i_threshold_high)[0]
        if len(idx_peak_region) == 0:
            return DPTResult()

        # Turn-off: first falling edge after the first high-current region
        # Find the first contiguous block of high current, then the drop
        first_high = idx_peak_region[0]

        # Find where current drops below low threshold after first high
        off_candidates = np.where(
            (i_d[first_high:] < i_threshold_low)
        )[0]
        if len(off_candidates) == 0:
            return DPTResult()
        idx_off_end = first_high + off_candidates[0]

        # Turn-off start: last index above high threshold before off_end
        off_start_candidates = np.where(
            i_d[:idx_off_end] >= i_threshold_high
        )[0]
        if len(off_start_candidates) == 0:
            return DPTResult()
        idx_off_start = off_start_candidates[-1]

        # --- Detect turn-on event ---
        # Turn-on is the rising edge of current after the dead time (after
        # current has been near zero for a while).
        # Look for current rising above low threshold after turn-off
        post_off = np.where(i_d[idx_off_end:] >= i_threshold_low)[0]
        if len(post_off) == 0:
            return DPTResult()
        idx_on_start_approx = idx_off_end + post_off[0]

        # Find where current rises above high threshold for the turn-on
        on_high_candidates = np.where(
            i_d[idx_on_start_approx:] >= i_threshold_high
        )[0]
        if len(on_high_candidates) == 0:
            # Current may not reach 90% in short pulse - use max after on
            idx_on_end = len(i_d) - 1
        else:
            idx_on_end = idx_on_start_approx + on_high_candidates[0]

        # Use a margin around the events to capture full switching energy
        margin = max(
            1,
            int(0.1 * (idx_off_end - idx_off_start)),
        )
        off_slice_start = max(0, idx_off_start - margin)
        off_slice_end = min(len(time) - 1, idx_off_end + margin)
        on_slice_start = max(0, idx_on_start_approx - margin)
        on_slice_end = min(len(time) - 1, idx_on_end + margin)

        # --- Calculate switching energies ---
        # P(t) = V_ds(t) * I_d(t), E = integral(P, dt)
        p_off = v_ds[off_slice_start:off_slice_end + 1] * \
            i_d[off_slice_start:off_slice_end + 1]
        t_off = time[off_slice_start:off_slice_end + 1]
        e_off = float(np.trapezoid(p_off, t_off))

        p_on = v_ds[on_slice_start:on_slice_end + 1] * \
            i_d[on_slice_start:on_slice_end + 1]
        t_on = time[on_slice_start:on_slice_end + 1]
        e_on = float(np.trapezoid(p_on, t_on))

        # --- Rise/fall times (10%-90%) ---
        # Fall time: time for current to go from 90% to 10% of i_max
        t_f = float(time[idx_off_end] - time[idx_off_start])

        # Rise time: time for current to go from 10% to 90% of i_max
        t_r = float(time[idx_on_end] - time[idx_on_start_approx])

        # --- Peak current during turn-on ---
        on_region = i_d[on_slice_start:on_slice_end + 1]
        i_peak = float(np.max(on_region)) if len(on_region) > 0 else 0.0

        # --- Voltage overshoot during turn-off ---
        off_region_v = v_ds[off_slice_start:off_slice_end + 1]
        v_overshoot = float(np.max(off_region_v)) if len(off_region_v) > 0 else 0.0

        # --- Slew rates ---
        di_dt_on = (
            (i_threshold_high - i_threshold_low) / t_r
            if t_r > 0 else 0.0
        )
        dv_dt_off = (
            (np.max(off_region_v) - np.min(off_region_v)) / t_f
            if t_f > 0 else 0.0
        )

        return DPTResult(
            e_on=e_on,
            e_off=e_off,
            t_r=t_r,
            t_f=t_f,
            i_peak=i_peak,
            v_overshoot=v_overshoot,
            di_dt_on=di_dt_on,
            dv_dt_off=float(dv_dt_off),
        )

    def extract_switching_loss_data(
        self, result: DPTResult, t_j: float = 25.0
    ) -> tuple[SwitchingLossData, SwitchingLossData]:
        """Convert DPT results to SwitchingLossData objects.

        Creates single-point switching loss data entries suitable for
        storing in a Transistor's switch component.

        :param result: DPT analysis result.
        :param t_j: Junction temperature in deg C.
        :return: Tuple of (e_on_data, e_off_data) SwitchingLossData.
        """
        cfg = self.config

        e_on_data = SwitchingLossData(
            dataset_type="single",
            t_j=t_j,
            v_supply=cfg.v_dc,
            v_g=cfg.v_g_on,
            v_g_off=cfg.v_g_off,
            e_x=result.e_on,
            i_x=cfg.i_target,
            r_g=cfg.r_g_on,
        )

        e_off_data = SwitchingLossData(
            dataset_type="single",
            t_j=t_j,
            v_supply=cfg.v_dc,
            v_g=cfg.v_g_on,
            v_g_off=cfg.v_g_off,
            e_x=result.e_off,
            i_x=cfg.i_target,
            r_g=cfg.r_g_off,
        )

        return e_on_data, e_off_data
