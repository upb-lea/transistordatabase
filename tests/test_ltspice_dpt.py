"""Tests for LTspice Double Pulse Test utility."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from transistordatabase.core.models import (
    ElectricalRatings,
    SwitchingLossData,
    ThermalProperties,
    Transistor,
    TransistorMetadata,
)
from transistordatabase.utils.ltspice_dpt import (
    DPTConfig,
    DPTResult,
    LTspiceDPT,
)


# ---------------------------------------------------------------------------
# Helpers for building synthetic DPT waveforms
# ---------------------------------------------------------------------------

def _make_dpt_waveforms(
    v_dc: float = 400.0,
    i_target: float = 20.0,
    t_rise: float = 50e-9,
    t_fall: float = 50e-9,
    dt: float = 1e-9,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray,
]:
    """Create synthetic DPT waveforms with finite switching transitions.

    The waveform represents one complete DPT cycle:
    1. First pulse: current ramps from 0 to i_target (inductor charging).
    2. Turn-off: current falls to 0 over t_fall while v_ds rises to v_dc.
    3. Dead time: current stays at 0, v_ds at v_dc.
    4. Turn-on: current rises to i_target over t_rise while v_ds drops.
    5. Short second pulse at i_target.

    :param v_dc: DC bus voltage in V.
    :param i_target: Target inductor current in A.
    :param t_rise: Current rise time for turn-on in s.
    :param t_fall: Current fall time for turn-off in s.
    :param dt: Time step in s.
    :return: Tuple of (time, v_ds, i_d, v_gs) arrays.
    """
    # Phase durations
    t_ramp = 5e-6       # First pulse ramp-up time
    t_dead = 2e-6       # Dead time
    t_pulse2 = 1e-6     # Second pulse duration
    t_tail = 0.5e-6     # Tail after second pulse

    # Build each phase
    # Phase 1: First pulse - current ramps from 0 to i_target, v_ds ~ 0
    n_ramp = int(t_ramp / dt)
    t_phase1 = np.arange(n_ramp) * dt
    i_phase1 = np.linspace(0, i_target, n_ramp)
    v_phase1 = np.full(n_ramp, 0.5)  # Small on-state voltage
    vg_phase1 = np.full(n_ramp, 15.0)

    # Phase 2: Turn-off - current falls, voltage rises (linear transitions)
    n_fall = int(t_fall / dt)
    if n_fall < 2:
        n_fall = 2
    t_phase2 = t_phase1[-1] + np.arange(1, n_fall + 1) * dt
    i_phase2 = np.linspace(i_target, 0, n_fall)
    v_phase2 = np.linspace(0.5, v_dc, n_fall)
    vg_phase2 = np.linspace(15.0, -5.0, n_fall)

    # Phase 3: Dead time - current at 0, v_ds at v_dc
    n_dead = int(t_dead / dt)
    t_phase3 = t_phase2[-1] + np.arange(1, n_dead + 1) * dt
    i_phase3 = np.zeros(n_dead)
    v_phase3 = np.full(n_dead, v_dc)
    vg_phase3 = np.full(n_dead, -5.0)

    # Phase 4: Turn-on - current rises, voltage drops
    n_rise = int(t_rise / dt)
    if n_rise < 2:
        n_rise = 2
    t_phase4 = t_phase3[-1] + np.arange(1, n_rise + 1) * dt
    i_phase4 = np.linspace(0, i_target, n_rise)
    v_phase4 = np.linspace(v_dc, 0.5, n_rise)
    vg_phase4 = np.linspace(-5.0, 15.0, n_rise)

    # Phase 5: Second pulse at i_target
    n_pulse2 = int(t_pulse2 / dt)
    t_phase5 = t_phase4[-1] + np.arange(1, n_pulse2 + 1) * dt
    i_phase5 = np.full(n_pulse2, i_target)
    v_phase5 = np.full(n_pulse2, 0.5)
    vg_phase5 = np.full(n_pulse2, 15.0)

    # Phase 6: Short tail
    n_tail = int(t_tail / dt)
    t_phase6 = t_phase5[-1] + np.arange(1, n_tail + 1) * dt
    i_phase6 = np.linspace(i_target, i_target * 0.95, n_tail)
    v_phase6 = np.full(n_tail, 0.5)
    vg_phase6 = np.full(n_tail, 15.0)

    # Concatenate all phases
    time = np.concatenate([
        t_phase1, t_phase2, t_phase3, t_phase4, t_phase5, t_phase6,
    ])
    v_ds = np.concatenate([
        v_phase1, v_phase2, v_phase3, v_phase4, v_phase5, v_phase6,
    ])
    i_d = np.concatenate([
        i_phase1, i_phase2, i_phase3, i_phase4, i_phase5, i_phase6,
    ])
    v_gs = np.concatenate([
        vg_phase1, vg_phase2, vg_phase3, vg_phase4, vg_phase5, vg_phase6,
    ])

    return time, v_ds, i_d, v_gs


def _make_transistor(name: str = "TEST_DUT") -> Transistor:
    """Create a minimal Transistor object for testing.

    :param name: Transistor name string.
    :return: A Transistor instance.
    """
    metadata = TransistorMetadata(
        name=name,
        type="SiC-MOSFET",
        author="Test",
        manufacturer="TestCorp",
        housing_type="TO-247",
    )
    electrical = ElectricalRatings(
        v_abs_max=650.0,
        i_abs_max=50.0,
        i_cont=30.0,
        t_j_max=175.0,
    )
    thermal = ThermalProperties(
        housing_area=0.001,
        cooling_area=0.001,
    )
    return Transistor(
        metadata=metadata,
        electrical=electrical,
        thermal=thermal,
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestDPTConfig:
    """Tests for DPTConfig dataclass."""

    def test_t_pulse1_calculation(self) -> None:
        """First pulse duration should satisfy I = V*t/L."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0, l_load=100e-6)
        expected = 20.0 * 100e-6 / 400.0  # 5e-6
        assert cfg.t_pulse1 == pytest.approx(expected, rel=1e-9)

    def test_t_pulse1_different_params(self) -> None:
        """Verify t_pulse1 scales correctly with different parameters."""
        cfg = DPTConfig(v_dc=800.0, i_target=50.0, l_load=200e-6)
        expected = 50.0 * 200e-6 / 800.0
        assert cfg.t_pulse1 == pytest.approx(expected, rel=1e-9)

    def test_t_pulse1_zero_voltage_raises(self) -> None:
        """Zero DC bus voltage should raise ValueError."""
        cfg = DPTConfig(v_dc=0.0)
        with pytest.raises(ValueError, match="positive"):
            _ = cfg.t_pulse1

    def test_t_pulse1_negative_voltage_raises(self) -> None:
        """Negative DC bus voltage should raise ValueError."""
        cfg = DPTConfig(v_dc=-100.0)
        with pytest.raises(ValueError, match="positive"):
            _ = cfg.t_pulse1

    def test_default_values(self) -> None:
        """Check that default values are sensible."""
        cfg = DPTConfig()
        assert cfg.v_dc == 400.0
        assert cfg.i_target == 20.0
        assert cfg.l_load == 100e-6
        assert cfg.r_g_on == 10.0
        assert cfg.r_g_off == 10.0


class TestNetlistGeneration:
    """Tests for netlist generation."""

    def test_generate_netlist_creates_file(self, tmp_path: Path) -> None:
        """Netlist file should be created at the output path."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        result = dpt.generate_netlist(tmp_path)
        assert result.exists()
        assert result.suffix == ".asc"

    def test_generate_netlist_content(self, tmp_path: Path) -> None:
        """Netlist should contain correct voltage and component values."""
        cfg = DPTConfig(v_dc=600.0, i_target=30.0, l_load=50e-6)
        dpt = LTspiceDPT(cfg)
        result = dpt.generate_netlist(tmp_path)
        content = result.read_text()

        assert "600.0" in content  # V_dc
        assert "50e-06" in content or "5e-05" in content  # L_load
        assert "DUT_NMOS" in content
        assert ".tran" in content
        assert ".end" in content

    def test_generate_netlist_with_transistor(self, tmp_path: Path) -> None:
        """Netlist filename should use transistor name when provided."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        transistor = _make_transistor("MY_MOSFET")
        result = dpt.generate_netlist(tmp_path, transistor=transistor)
        assert "MY_MOSFET" in result.name

    def test_generate_netlist_without_transistor(self, tmp_path: Path) -> None:
        """Netlist should use 'DUT' as default name."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        result = dpt.generate_netlist(tmp_path)
        assert "DUT" in result.name

    def test_generate_netlist_specific_file(self, tmp_path: Path) -> None:
        """When output_path is a file path, use it directly."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        file_path = tmp_path / "custom_netlist.asc"
        result = dpt.generate_netlist(file_path)
        assert result == file_path
        assert result.exists()

    def test_generate_netlist_creates_parent_dirs(
        self, tmp_path: Path,
    ) -> None:
        """Should create parent directories if they do not exist."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        file_path = tmp_path / "sub" / "dir" / "netlist.asc"
        result = dpt.generate_netlist(file_path)
        assert result.exists()


class TestWaveformAnalysis:
    """Tests for waveform analysis."""

    def test_basic_analysis(self) -> None:
        """Analyze synthetic waveforms and check all fields are populated."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, v_gs = _make_dpt_waveforms(
            v_dc=400.0, i_target=20.0,
        )
        result = dpt.analyze_waveforms(time, v_ds, i_d, v_gs)

        assert result.e_on > 0
        assert result.e_off > 0
        assert result.t_r > 0
        assert result.t_f > 0
        assert result.i_peak > 0
        assert result.v_overshoot > 0

    def test_switching_energy_order_of_magnitude(self) -> None:
        """Switching energies should be in a physically reasonable range.

        For 400V/20A with 50ns transitions, E ~ V*I*t/2 ~ 0.2 mJ.
        """
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, v_gs = _make_dpt_waveforms(
            v_dc=400.0, i_target=20.0, t_rise=50e-9, t_fall=50e-9,
        )
        result = dpt.analyze_waveforms(time, v_ds, i_d, v_gs)

        # Rough estimate: E ~ V_dc * I_target * t_sw / 2
        e_rough = 400.0 * 20.0 * 50e-9 / 2  # 0.2 mJ
        # Allow factor of 10 tolerance for integration window effects
        assert result.e_off < e_rough * 10
        assert result.e_on < e_rough * 10
        assert result.e_off > 0
        assert result.e_on > 0

    def test_rise_fall_time_extraction(self) -> None:
        """Rise and fall times should match the synthetic transitions."""
        t_rise = 100e-9
        t_fall = 80e-9
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, v_gs = _make_dpt_waveforms(
            v_dc=400.0, i_target=20.0,
            t_rise=t_rise, t_fall=t_fall,
        )
        result = dpt.analyze_waveforms(time, v_ds, i_d, v_gs)

        # The 10%-90% rise/fall times should be close to the synthetic
        # transition times (within ~30% due to discretization and
        # threshold detection)
        assert result.t_f == pytest.approx(t_fall, rel=0.35)
        assert result.t_r == pytest.approx(t_rise, rel=0.35)

    def test_near_instantaneous_switching(self) -> None:
        """Near-instantaneous switching should give very small energies."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, v_gs = _make_dpt_waveforms(
            v_dc=400.0, i_target=20.0,
            t_rise=2e-9, t_fall=2e-9, dt=1e-9,
        )
        result = dpt.analyze_waveforms(time, v_ds, i_d, v_gs)

        # With ~instantaneous switching, energy should be very small
        # compared to typical values
        e_reference = 400.0 * 20.0 * 50e-9 / 2
        assert result.e_off < e_reference * 0.5
        assert result.e_on < e_reference * 0.5

    def test_empty_waveform(self) -> None:
        """Zero-current waveform should return default DPTResult."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        n = 1000
        time = np.linspace(0, 1e-5, n)
        v_ds = np.full(n, 400.0)
        i_d = np.zeros(n)
        result = dpt.analyze_waveforms(time, v_ds, i_d)

        assert result.e_on == 0.0
        assert result.e_off == 0.0

    def test_di_dt_positive(self) -> None:
        """Turn-on di/dt should be positive."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, v_gs = _make_dpt_waveforms()
        result = dpt.analyze_waveforms(time, v_ds, i_d, v_gs)
        assert result.di_dt_on > 0

    def test_dv_dt_positive(self) -> None:
        """Turn-off dv/dt should be positive."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, v_gs = _make_dpt_waveforms()
        result = dpt.analyze_waveforms(time, v_ds, i_d, v_gs)
        assert result.dv_dt_off > 0

    def test_analysis_without_vgs(self) -> None:
        """Analysis should work without v_gs array."""
        cfg = DPTConfig(v_dc=400.0, i_target=20.0)
        dpt = LTspiceDPT(cfg)
        time, v_ds, i_d, _ = _make_dpt_waveforms()
        result = dpt.analyze_waveforms(time, v_ds, i_d)
        assert result.e_on > 0
        assert result.e_off > 0


class TestSwitchingDataExtraction:
    """Tests for extract_switching_loss_data."""

    def test_creates_valid_switching_loss_data(self) -> None:
        """Extracted data should have correct dataset_type and fields."""
        cfg = DPTConfig(
            v_dc=400.0, i_target=20.0,
            r_g_on=5.0, r_g_off=10.0,
            v_g_on=15.0, v_g_off=-5.0,
        )
        dpt = LTspiceDPT(cfg)
        result = DPTResult(e_on=0.5e-3, e_off=0.3e-3)
        e_on_data, e_off_data = dpt.extract_switching_loss_data(result)

        assert isinstance(e_on_data, SwitchingLossData)
        assert isinstance(e_off_data, SwitchingLossData)

    def test_dataset_type_is_single(self) -> None:
        """Both datasets should have dataset_type 'single'."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        result = DPTResult(e_on=0.5e-3, e_off=0.3e-3)
        e_on_data, e_off_data = dpt.extract_switching_loss_data(result)

        assert e_on_data.dataset_type == "single"
        assert e_off_data.dataset_type == "single"

    def test_energy_values_match(self) -> None:
        """Switching energies should match the input result."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        result = DPTResult(e_on=1.5e-3, e_off=0.8e-3)
        e_on_data, e_off_data = dpt.extract_switching_loss_data(result)

        assert e_on_data.e_x == pytest.approx(1.5e-3)
        assert e_off_data.e_x == pytest.approx(0.8e-3)

    def test_config_parameters_propagated(self) -> None:
        """Config parameters should be propagated to switching loss data."""
        cfg = DPTConfig(
            v_dc=600.0, i_target=30.0,
            r_g_on=5.0, r_g_off=12.0,
            v_g_on=18.0, v_g_off=-3.0,
        )
        dpt = LTspiceDPT(cfg)
        result = DPTResult(e_on=0.5e-3, e_off=0.3e-3)
        e_on_data, e_off_data = dpt.extract_switching_loss_data(result)

        assert e_on_data.v_supply == 600.0
        assert e_on_data.i_x == 30.0
        assert e_on_data.r_g == 5.0
        assert e_on_data.v_g == 18.0
        assert e_on_data.v_g_off == -3.0

        assert e_off_data.v_supply == 600.0
        assert e_off_data.i_x == 30.0
        assert e_off_data.r_g == 12.0

    def test_junction_temperature(self) -> None:
        """Junction temperature should be set correctly."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        result = DPTResult(e_on=0.5e-3, e_off=0.3e-3)
        e_on_data, e_off_data = dpt.extract_switching_loss_data(
            result, t_j=150.0,
        )

        assert e_on_data.t_j == 150.0
        assert e_off_data.t_j == 150.0

    def test_default_junction_temperature(self) -> None:
        """Default junction temperature should be 25 deg C."""
        cfg = DPTConfig()
        dpt = LTspiceDPT(cfg)
        result = DPTResult()
        e_on_data, e_off_data = dpt.extract_switching_loss_data(result)

        assert e_on_data.t_j == 25.0
        assert e_off_data.t_j == 25.0


class TestSimulationRunner:
    """Tests for simulation execution."""

    def test_run_simulation_raises_without_pyltspice(
        self, tmp_path: Path,
    ) -> None:
        """run_simulation should raise ImportError when PyLTSpice missing."""
        import transistordatabase.utils.ltspice_dpt as dpt_module

        original = dpt_module.HAS_PYLTSPICE
        try:
            dpt_module.HAS_PYLTSPICE = False
            cfg = DPTConfig()
            dpt = LTspiceDPT(cfg)
            netlist = tmp_path / "test.asc"
            netlist.write_text("* test netlist")

            with pytest.raises(ImportError, match="PyLTSpice"):
                dpt.run_simulation(netlist)
        finally:
            dpt_module.HAS_PYLTSPICE = original
