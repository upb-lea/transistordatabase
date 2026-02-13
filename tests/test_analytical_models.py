"""Tests for analytical switching loss models."""
from __future__ import annotations

import numpy as np
import pytest

from transistordatabase.analytical_models import (
    BielaModel,
    BielaModelParams,
    GateChargeModel,
    GateChargeModelParams,
    IgbtModel,
    IgbtModelParams,
)


class TestBielaModel:
    """Tests for the Biela inductive switching loss model."""

    @pytest.fixture
    def model(self) -> BielaModel:
        """Create a standard Biela model for testing."""
        params = BielaModelParams(
            c_oss=100e-12,   # 100pF
            q_g=50e-9,       # 50nC
            v_plateau=4.5,
            r_g_on=10.0,
            r_g_off=10.0,
            v_driver_on=15.0,
            v_driver_off=-5.0,
        )
        return BielaModel(params)

    def test_e_on_positive(self, model: BielaModel) -> None:
        """Verify turn-on energy is positive for valid inputs."""
        e_on = model.calc_e_on(400.0, 20.0)
        assert e_on > 0

    def test_e_off_positive(self, model: BielaModel) -> None:
        """Verify turn-off energy is positive for valid inputs."""
        e_off = model.calc_e_off(400.0, 20.0)
        assert e_off > 0

    def test_e_total_is_sum(self, model: BielaModel) -> None:
        """Verify total energy equals sum of on and off."""
        v_dc, i_load = 400.0, 20.0
        e_on = model.calc_e_on(v_dc, i_load)
        e_off = model.calc_e_off(v_dc, i_load)
        e_total = model.calc_e_total(v_dc, i_load)
        assert e_total == pytest.approx(e_on + e_off)

    def test_energy_increases_with_voltage(self, model: BielaModel) -> None:
        """Verify energy increases with bus voltage."""
        e_400 = model.calc_e_total(400.0, 20.0)
        e_800 = model.calc_e_total(800.0, 20.0)
        assert e_800 > e_400

    def test_energy_increases_with_current(self, model: BielaModel) -> None:
        """Verify energy increases with load current."""
        e_10 = model.calc_e_total(400.0, 10.0)
        e_40 = model.calc_e_total(400.0, 40.0)
        assert e_40 > e_10

    def test_temp_scaling(self, model: BielaModel) -> None:
        """Verify energy increases with temperature."""
        e_25 = model.calc_e_total(400.0, 20.0, t_j=25.0)
        e_150 = model.calc_e_total(400.0, 20.0, t_j=150.0)
        assert e_150 > e_25

    def test_zero_current_no_error(self, model: BielaModel) -> None:
        """Verify zero current doesn't cause division by zero."""
        e_on = model.calc_e_on(400.0, 0.0)
        assert e_on >= 0

    def test_switching_loss_curve(self, model: BielaModel) -> None:
        """Verify switching loss curve generation."""
        currents = np.linspace(1.0, 50.0, 10)
        e_on, e_off, e_total = model.calc_switching_loss_curve(400.0, currents)
        assert len(e_on) == 10
        assert len(e_off) == 10
        np.testing.assert_array_almost_equal(e_total, e_on + e_off)


class TestGateChargeModel:
    """Tests for the gate charge switching time model."""

    @pytest.fixture
    def model(self) -> GateChargeModel:
        """Create a standard gate charge model for testing."""
        params = GateChargeModelParams(
            q_gs=10e-9,      # 10nC
            q_gd=15e-9,      # 15nC
            q_g=50e-9,       # 50nC
            v_th=3.0,
            v_plateau=4.5,
            r_g=10.0,
            r_g_int=1.0,
        )
        return GateChargeModel(params)

    def test_turn_on_times_positive(self, model: GateChargeModel) -> None:
        """Verify all turn-on times are positive."""
        times = model.calc_turn_on_times(15.0)
        assert times['t_delay'] >= 0
        assert times['t_rise'] >= 0
        assert times['t_fall_v'] >= 0
        assert times['t_total'] > 0

    def test_turn_off_times_positive(self, model: GateChargeModel) -> None:
        """Verify all turn-off times are positive."""
        times = model.calc_turn_off_times(15.0, 0.0)
        assert times['t_delay'] >= 0
        assert times['t_rise_v'] >= 0
        assert times['t_fall_i'] >= 0
        assert times['t_total'] > 0

    def test_higher_rg_slower(self) -> None:
        """Verify higher gate resistance gives longer switching times."""
        params_low = GateChargeModelParams(
            q_gs=10e-9, q_gd=15e-9, q_g=50e-9,
            v_th=3.0, v_plateau=4.5, r_g=5.0,
        )
        params_high = GateChargeModelParams(
            q_gs=10e-9, q_gd=15e-9, q_g=50e-9,
            v_th=3.0, v_plateau=4.5, r_g=20.0,
        )
        t_low = GateChargeModel(params_low).calc_turn_on_times()['t_total']
        t_high = GateChargeModel(params_high).calc_turn_on_times()['t_total']
        assert t_high > t_low

    def test_total_is_sum_of_phases(self, model: GateChargeModel) -> None:
        """Verify total time is sum of individual phases."""
        times = model.calc_turn_on_times()
        assert times['t_total'] == pytest.approx(
            times['t_delay'] + times['t_rise'] + times['t_fall_v']
        )


class TestIgbtModel:
    """Tests for the IGBT tail current model."""

    @pytest.fixture
    def model(self) -> IgbtModel:
        """Create a standard IGBT model for testing."""
        return IgbtModel(IgbtModelParams(
            v_ce_sat=1.5,
            i_tail_factor=0.1,
            tau_tail=1e-6,
            t_fall=200e-9,
        ))

    def test_tail_energy_positive(self, model: IgbtModel) -> None:
        """Verify tail energy is positive."""
        e_tail = model.calc_tail_energy(600.0, 100.0)
        assert e_tail > 0

    def test_tail_increases_with_current(self, model: IgbtModel) -> None:
        """Verify tail energy increases with load current."""
        e_50 = model.calc_tail_energy(600.0, 50.0)
        e_200 = model.calc_tail_energy(600.0, 200.0)
        assert e_200 > e_50

    def test_e_off_total_exceeds_overlap(self, model: IgbtModel) -> None:
        """Verify total off energy exceeds overlap-only energy."""
        e_overlap = 0.5 * 600.0 * 100.0 * 200e-9
        e_total = model.calc_e_off_total(600.0, 100.0, e_overlap)
        assert e_total > e_overlap

    def test_conduction_loss(self, model: IgbtModel) -> None:
        """Verify conduction loss calculation."""
        p_cond = model.calc_conduction_loss(i_avg=50.0, i_rms=60.0)
        assert p_cond == pytest.approx(1.5 * 50.0)
