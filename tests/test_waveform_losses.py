"""Tests for waveform-based loss calculations."""
from __future__ import annotations

import numpy as np
import pytest

from transistordatabase.core.models import (
    ChannelCharacteristics,
    LinearizedModel,
    SwitchingLossData,
)
from transistordatabase.waveform_losses import (
    LossResult,
    WaveformData,
    calc_conduction_loss,
    calc_conduction_loss_from_channel,
    calc_switching_loss,
    calc_total_loss,
    detect_switching_edges,
    detect_zvs,
)


@pytest.fixture
def linearized_model() -> LinearizedModel:
    """Create a linearized model for testing."""
    return LinearizedModel(
        t_j=25.0, i_channel=20.0,
        r_channel=0.05, v0_channel=0.7,
    )


@pytest.fixture
def channel_data() -> ChannelCharacteristics:
    """Create channel data for testing."""
    currents = np.array([0, 5, 10, 15, 20, 25, 30], dtype=np.float64)
    voltages = np.array([0.0, 0.3, 0.5, 0.8, 1.1, 1.45, 1.85], dtype=np.float64)
    return ChannelCharacteristics(
        t_j=25.0,
        graph_v_i=np.array([voltages, currents]),
    )


@pytest.fixture
def switching_data() -> tuple[list[SwitchingLossData], list[SwitchingLossData]]:
    """Create switching loss data for testing."""
    currents = np.array([0, 10, 20, 30, 40, 50], dtype=np.float64)
    e_on_vals = np.array([0, 0.1e-3, 0.3e-3, 0.6e-3, 1.0e-3, 1.5e-3])
    e_off_vals = np.array([0, 0.05e-3, 0.15e-3, 0.3e-3, 0.5e-3, 0.75e-3])

    e_on_data = [SwitchingLossData(
        dataset_type='graph_i_e', t_j=25.0, v_supply=400.0, v_g=15.0,
        graph_i_e=np.array([currents, e_on_vals]),
    )]
    e_off_data = [SwitchingLossData(
        dataset_type='graph_i_e', t_j=25.0, v_supply=400.0, v_g=15.0,
        graph_i_e=np.array([currents, e_off_vals]),
    )]
    return e_on_data, e_off_data


def _make_pwm_waveform(
    f_sw: float = 10000.0, duty: float = 0.5, i_load: float = 20.0,
    n_cycles: int = 5, samples_per_cycle: int = 200,
    ccm: bool = False,
) -> WaveformData:
    """Generate a simple PWM waveform for testing.

    :param ccm: If True, current is always i_load (continuous conduction mode).
    """
    t_period = 1.0 / f_sw
    n_samples = n_cycles * samples_per_cycle
    t_total = n_cycles * t_period

    time = np.linspace(0, t_total, n_samples)
    gate = np.zeros(n_samples)
    current = np.zeros(n_samples)

    for i in range(n_samples):
        t_in_period = time[i] % t_period
        if t_in_period < duty * t_period:
            gate[i] = 1.0
            current[i] = i_load
        elif ccm:
            current[i] = i_load  # CCM: current flows through diode when switch off

    return WaveformData(time=time, current=current, gate=gate)


class TestConductionLoss:
    """Tests for conduction loss calculation."""

    def test_positive_loss(self, linearized_model: LinearizedModel) -> None:
        """Verify conduction loss is positive for flowing current."""
        waveform = _make_pwm_waveform(duty=0.5, i_load=20.0)
        p_cond = calc_conduction_loss(waveform, linearized_model)
        assert p_cond > 0

    def test_zero_current_zero_loss(self, linearized_model: LinearizedModel) -> None:
        """Verify zero conduction loss with zero current."""
        time = np.linspace(0, 1e-3, 100)
        waveform = WaveformData(time=time, current=np.zeros(100))
        p_cond = calc_conduction_loss(waveform, linearized_model)
        assert p_cond == pytest.approx(0.0)

    def test_higher_duty_more_loss(self, linearized_model: LinearizedModel) -> None:
        """Verify higher duty cycle gives more conduction loss."""
        wf_25 = _make_pwm_waveform(duty=0.25, i_load=20.0)
        wf_75 = _make_pwm_waveform(duty=0.75, i_load=20.0)
        p_25 = calc_conduction_loss(wf_25, linearized_model)
        p_75 = calc_conduction_loss(wf_75, linearized_model)
        assert p_75 > p_25

    def test_from_channel_positive(self, channel_data: ChannelCharacteristics) -> None:
        """Verify channel-based conduction loss is positive."""
        waveform = _make_pwm_waveform(duty=0.5, i_load=15.0)
        p_cond = calc_conduction_loss_from_channel(waveform, channel_data)
        assert p_cond > 0


class TestSwitchingEdgeDetection:
    """Tests for switching edge detection."""

    def test_detect_edges(self) -> None:
        """Verify correct number of edges detected."""
        waveform = _make_pwm_waveform(n_cycles=5)
        on_times, off_times = detect_switching_edges(waveform)
        # First cycle starts at t=0 with gate=0, so first rising edge
        # is detected within cycle 1. Last cycle may not have a falling edge.
        assert len(on_times) >= 4
        assert len(off_times) >= 4

    def test_no_gate_raises(self) -> None:
        """Verify error when gate signal missing."""
        time = np.linspace(0, 1e-3, 100)
        waveform = WaveformData(time=time, current=np.zeros(100))
        with pytest.raises(ValueError, match="Gate signal required"):
            detect_switching_edges(waveform)


class TestZvsDetection:
    """Tests for ZVS detection."""

    def test_zvs_detection(self) -> None:
        """Verify ZVS detection with low voltage at turn-on."""
        waveform = _make_pwm_waveform(n_cycles=3, i_load=20.0)
        # Set voltage to zero slightly before gate goes high (ZVS condition)
        # Shift voltage to be low at rising edge instants
        voltage = np.full_like(waveform.current, 400.0)
        on_times, _ = detect_switching_edges(waveform)
        for t_on in on_times:
            idx = np.searchsorted(waveform.time, t_on)
            # Set voltage to near-zero around turn-on instant
            start = max(0, idx - 2)
            end = min(len(voltage), idx + 3)
            voltage[start:end] = 0.0
        waveform.voltage = voltage
        zvs_times, hard_sw_times = detect_zvs(waveform)
        assert len(zvs_times) > 0

    def test_hard_switching_detection(self) -> None:
        """Verify hard switching detection with high voltage at turn-on."""
        waveform = _make_pwm_waveform(n_cycles=3, i_load=20.0)
        # Voltage is high everywhere
        waveform.voltage = np.full_like(waveform.current, 400.0)
        zvs_times, hard_sw_times = detect_zvs(waveform)
        assert len(hard_sw_times) > 0


class TestSwitchingLoss:
    """Tests for switching loss calculation."""

    def test_positive_switching_loss(
        self,
        switching_data: tuple[list[SwitchingLossData], list[SwitchingLossData]],
    ) -> None:
        """Verify switching losses are positive in CCM mode."""
        e_on_data, e_off_data = switching_data
        waveform = _make_pwm_waveform(n_cycles=5, i_load=20.0, ccm=True)
        p_on, p_off = calc_switching_loss(waveform, e_on_data, e_off_data)
        assert p_on > 0
        assert p_off > 0

    def test_higher_frequency_more_loss(
        self,
        switching_data: tuple[list[SwitchingLossData], list[SwitchingLossData]],
    ) -> None:
        """Verify higher switching frequency gives more switching loss."""
        e_on_data, e_off_data = switching_data
        wf_10k = _make_pwm_waveform(f_sw=10000.0, n_cycles=5, i_load=20.0)
        wf_50k = _make_pwm_waveform(f_sw=50000.0, n_cycles=25, i_load=20.0)
        p_on_10k, p_off_10k = calc_switching_loss(wf_10k, e_on_data, e_off_data)
        p_on_50k, p_off_50k = calc_switching_loss(wf_50k, e_on_data, e_off_data)
        assert (p_on_50k + p_off_50k) > (p_on_10k + p_off_10k)


class TestTotalLoss:
    """Tests for total loss calculation."""

    def test_total_loss_result(
        self,
        linearized_model: LinearizedModel,
        switching_data: tuple[list[SwitchingLossData], list[SwitchingLossData]],
    ) -> None:
        """Verify total loss result structure and values."""
        e_on_data, e_off_data = switching_data
        waveform = _make_pwm_waveform(n_cycles=5, i_load=20.0, ccm=True)
        result = calc_total_loss(
            waveform, linearized_model, e_on_data, e_off_data
        )
        assert isinstance(result, LossResult)
        assert result.p_cond > 0
        assert result.p_sw_on > 0
        assert result.p_sw_off > 0
        assert result.p_total == pytest.approx(
            result.p_cond + result.p_sw_on + result.p_sw_off
        )
        assert result.n_cycles >= 4
