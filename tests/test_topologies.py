"""Tests for power converter topology analysis modules.

Tests all four topology analyzers: BridgelessPFC, DAB, LLC, and SRC-ZVS.
Each topology is tested for correct loss calculation, parameter validation,
sensitivity to switching frequency, and ZVS detection (where applicable).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from transistordatabase.core.models import (
    ChannelCharacteristics,
    Diode,
    ElectricalRatings,
    Switch,
    SwitchingLossData,
    ThermalProperties,
    Transistor,
    TransistorMetadata,
)
from transistordatabase.topologies.bridgeless_pfc import (
    BridgelessPFCParams,
    BridgelessPFCTopology,
)
from transistordatabase.topologies.dab import (
    DABParams,
    DABTopology,
)
from transistordatabase.topologies.llc import (
    LLCParams,
    LLCTopology,
)
from transistordatabase.topologies.src_zvs import (
    SRCZVSParams,
    SRCZVSTopology,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_channel_data(
    t_j: float = 25.0,
    v_g: float = 15.0,
    *,
    is_diode: bool = False,
) -> ChannelCharacteristics:
    """Create a simple V-I channel characteristic.

    :param t_j: Junction temperature in deg C.
    :param v_g: Gate voltage in V.
    :param is_diode: If True, use diode-like V-I characteristic.
    :return: ChannelCharacteristics instance.
    """
    if is_diode:
        # Diode: V_f ~ 0.7V + 0.01 Ohm * I
        currents = np.linspace(0.1, 100.0, 50)
        voltages = 0.7 + 0.01 * currents
    else:
        # MOSFET: V = R_ds_on * I with R_ds_on ~ 0.05 Ohm
        currents = np.linspace(0.1, 100.0, 50)
        voltages = 0.05 * currents
    graph_v_i = np.array([voltages, currents])
    return ChannelCharacteristics(t_j=t_j, graph_v_i=graph_v_i, v_g=v_g)


def _make_switching_loss_data(
    dataset_type: str = "graph_i_e",
    t_j: float = 25.0,
    v_supply: float = 400.0,
    v_g: float = 15.0,
    energy_scale: float = 1e-3,
) -> SwitchingLossData:
    """Create switching loss data with an I-E curve.

    :param dataset_type: Dataset type string.
    :param t_j: Junction temperature in deg C.
    :param v_supply: Supply voltage in V.
    :param v_g: Gate voltage in V.
    :param energy_scale: Scale factor for energy values in J/A.
    :return: SwitchingLossData instance with graph_i_e.
    """
    currents = np.linspace(0.0, 100.0, 20)
    # Energy ~ energy_scale * I (linear approximation)
    energies = energy_scale * currents
    graph_i_e = np.array([currents, energies])
    return SwitchingLossData(
        dataset_type=dataset_type,
        t_j=t_j,
        v_supply=v_supply,
        v_g=v_g,
        graph_i_e=graph_i_e,
    )


def _make_transistor_with_offset_energy() -> Transistor:
    """Create a transistor with switching energy that has a constant offset.

    The energy curve is E = 0.01 + 1e-3 * I, so the constant term causes
    switching power to increase with frequency even when peak current
    decreases proportionally.

    :return: Transistor instance with offset switching energy data.
    """
    metadata = TransistorMetadata(
        name="OFFSET_ENERGY_MOSFET",
        type="SiC-MOSFET",
        author="Test",
        manufacturer="Test Inc",
        housing_type="TO-247",
    )
    electrical = ElectricalRatings(
        v_abs_max=650.0, i_abs_max=100.0,
        i_cont=60.0, t_j_max=175.0,
    )
    thermal = ThermalProperties(housing_area=0.001, cooling_area=0.0008)

    transistor = Transistor(metadata, electrical, thermal)
    transistor.switch.channel_data.append(_make_channel_data(25.0, 15.0))

    # Switching energy with constant offset: E = 0.01 + 1e-3 * I
    currents = np.linspace(0.0, 100.0, 20)
    e_on_vals = 0.01 + 1e-3 * currents
    e_off_vals = 0.01 + 0.8e-3 * currents

    transistor.switch.e_on_data.append(SwitchingLossData(
        dataset_type="graph_i_e", t_j=25.0, v_supply=400.0, v_g=15.0,
        graph_i_e=np.array([currents, e_on_vals]),
    ))
    transistor.switch.e_off_data.append(SwitchingLossData(
        dataset_type="graph_i_e", t_j=25.0, v_supply=400.0, v_g=15.0,
        graph_i_e=np.array([currents, e_off_vals]),
    ))

    return transistor


@pytest.fixture
def basic_transistor() -> Transistor:
    """Create a transistor with basic channel and switching loss data.

    The transistor has:
    - Switch channel data at 25 deg C, V_g=15V, R_ds_on ~ 0.05 Ohm
    - E_on and E_off data (linear in current, ~1 mJ/A)
    - Diode channel data at 25 deg C, V_f ~ 0.7V, R_f ~ 0.01 Ohm
    - E_rr data (linear in current, ~0.5 mJ/A)
    """
    metadata = TransistorMetadata(
        name="TEST_MOSFET",
        type="SiC-MOSFET",
        author="Test",
        manufacturer="Test Inc",
        housing_type="TO-247",
    )
    electrical = ElectricalRatings(
        v_abs_max=650.0,
        i_abs_max=100.0,
        i_cont=60.0,
        t_j_max=175.0,
    )
    thermal = ThermalProperties(housing_area=0.001, cooling_area=0.0008)

    transistor = Transistor(metadata, electrical, thermal)

    # Switch channel data
    transistor.switch.channel_data.append(_make_channel_data(25.0, 15.0))

    # Switch E_on / E_off
    transistor.switch.e_on_data.append(
        _make_switching_loss_data(energy_scale=1e-3),
    )
    transistor.switch.e_off_data.append(
        _make_switching_loss_data(energy_scale=0.8e-3),
    )

    # Diode channel data
    transistor.diode.channel_data.append(
        _make_channel_data(25.0, 0.0, is_diode=True),
    )

    # Diode E_rr
    transistor.diode.e_rr_data.append(
        _make_switching_loss_data(energy_scale=0.5e-3),
    )

    return transistor


@pytest.fixture
def bare_transistor() -> Transistor:
    """Create a transistor with no channel or switching data.

    Tests that topologies fall back to sensible defaults.
    """
    metadata = TransistorMetadata(
        name="BARE_MOSFET",
        type="MOSFET",
        author="Test",
        manufacturer="Test Inc",
        housing_type="TO-220",
    )
    electrical = ElectricalRatings(
        v_abs_max=600.0,
        i_abs_max=50.0,
        i_cont=30.0,
        t_j_max=150.0,
    )
    thermal = ThermalProperties(housing_area=0.0005, cooling_area=0.0004)
    return Transistor(metadata, electrical, thermal)


# ---------------------------------------------------------------------------
# BridgelessPFC tests
# ---------------------------------------------------------------------------


class TestBridgelessPFC:
    """Tests for BridgelessPFCTopology."""

    @pytest.fixture
    def pfc_params(self) -> BridgelessPFCParams:
        """Return standard PFC operating point."""
        return BridgelessPFCParams(
            v_in_rms=230.0,
            v_out=400.0,
            p_out=1000.0,
            f_sw=100e3,
            l_boost=500e-6,
        )

    def test_basic_result(
        self, basic_transistor: Transistor, pfc_params: BridgelessPFCParams,
    ) -> None:
        """Verify calculate_losses returns a valid result."""
        topo = BridgelessPFCTopology()
        result = topo.calculate_losses(basic_transistor, pfc_params)

        assert result.p_total > 0
        assert result.p_cond_switch >= 0
        assert result.p_sw_switch >= 0
        assert result.p_cond_diode >= 0
        assert result.p_sw_diode >= 0
        assert result.p_total == pytest.approx(
            result.p_cond_switch
            + result.p_sw_switch
            + result.p_cond_diode
            + result.p_sw_diode,
        )

    def test_duty_cycle_range(
        self, basic_transistor: Transistor, pfc_params: BridgelessPFCParams,
    ) -> None:
        """Verify average duty cycle is in [0, 1]."""
        topo = BridgelessPFCTopology()
        result = topo.calculate_losses(basic_transistor, pfc_params)
        assert 0.0 <= result.duty_avg <= 1.0

    def test_i_rms_positive(
        self, basic_transistor: Transistor, pfc_params: BridgelessPFCParams,
    ) -> None:
        """Verify RMS current is positive."""
        topo = BridgelessPFCTopology()
        result = topo.calculate_losses(basic_transistor, pfc_params)
        assert result.i_rms > 0

    def test_higher_frequency_more_switching_loss(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify switching loss increases with frequency."""
        topo = BridgelessPFCTopology()

        params_low = BridgelessPFCParams(
            v_in_rms=230.0, v_out=400.0, p_out=1000.0,
            f_sw=50e3, l_boost=500e-6,
        )
        params_high = BridgelessPFCParams(
            v_in_rms=230.0, v_out=400.0, p_out=1000.0,
            f_sw=200e3, l_boost=500e-6,
        )

        result_low = topo.calculate_losses(basic_transistor, params_low)
        result_high = topo.calculate_losses(basic_transistor, params_high)

        assert result_high.p_sw_switch > result_low.p_sw_switch

    def test_negative_power_raises(self, basic_transistor: Transistor) -> None:
        """Verify negative power raises ValueError."""
        topo = BridgelessPFCTopology()
        params = BridgelessPFCParams(
            v_in_rms=230.0, v_out=400.0, p_out=-100.0,
            f_sw=100e3, l_boost=500e-6,
        )
        with pytest.raises(ValueError, match="p_out"):
            topo.calculate_losses(basic_transistor, params)

    def test_negative_voltage_raises(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify negative input voltage raises ValueError."""
        topo = BridgelessPFCTopology()
        params = BridgelessPFCParams(
            v_in_rms=-230.0, v_out=400.0, p_out=1000.0,
            f_sw=100e3, l_boost=500e-6,
        )
        with pytest.raises(ValueError, match="v_in_rms"):
            topo.calculate_losses(basic_transistor, params)

    def test_bare_transistor_defaults(
        self, bare_transistor: Transistor, pfc_params: BridgelessPFCParams,
    ) -> None:
        """Verify topology works with transistor lacking channel data."""
        topo = BridgelessPFCTopology()
        result = topo.calculate_losses(bare_transistor, pfc_params)
        assert result.p_total > 0


# ---------------------------------------------------------------------------
# DAB tests
# ---------------------------------------------------------------------------


class TestDAB:
    """Tests for DABTopology."""

    @pytest.fixture
    def dab_params(self) -> DABParams:
        """Return standard DAB operating point."""
        return DABParams(
            v_in=400.0,
            v_out=48.0,
            p_out=1000.0,
            f_sw=100e3,
            l_s=50e-6,
            n=4.0,
            phi=math.pi / 6,
        )

    def test_basic_result(
        self,
        basic_transistor: Transistor,
        dab_params: DABParams,
    ) -> None:
        """Verify calculate_losses returns a valid result."""
        topo = DABTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, dab_params,
        )

        assert result.p_total >= 0
        assert result.p_total == pytest.approx(
            result.p_cond_primary
            + result.p_sw_primary
            + result.p_cond_secondary
            + result.p_sw_secondary,
        )

    def test_rms_currents_positive(
        self,
        basic_transistor: Transistor,
        dab_params: DABParams,
    ) -> None:
        """Verify RMS currents are positive."""
        topo = DABTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, dab_params,
        )
        assert result.i_rms_primary > 0
        assert result.i_rms_secondary > 0

    def test_zvs_with_phase_shift(
        self,
        basic_transistor: Transistor,
        dab_params: DABParams,
    ) -> None:
        """Verify ZVS is detected with nonzero phase shift."""
        topo = DABTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, dab_params,
        )
        assert result.is_zvs is True

    def test_no_zvs_zero_phase(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify no ZVS at zero phase shift."""
        topo = DABTopology()
        params = DABParams(
            v_in=400.0, v_out=48.0, p_out=1000.0,
            f_sw=100e3, l_s=50e-6, n=4.0, phi=0.0,
        )
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, params,
        )
        assert result.is_zvs is False

    def test_higher_frequency_more_switching_loss(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify switching loss increases with frequency.

        In a DAB, the peak switching current is inversely proportional
        to omega*L_s. With purely linear E(I) curves, p_sw = E(I)*f_sw
        is constant because the decrease in I exactly cancels the
        increase in f_sw. To test frequency sensitivity we use switching
        energy data that includes a constant offset (capacitive loss
        component), which breaks the cancellation.
        """
        topo = DABTopology()

        # Build a transistor whose switching energy has a constant offset
        # E = 0.01 + 1e-3 * I  (the 0.01 J offset grows with f_sw)
        transistor = _make_transistor_with_offset_energy()

        params_low = DABParams(
            v_in=400.0, v_out=48.0, p_out=1000.0,
            f_sw=50e3, l_s=50e-6, n=4.0, phi=math.pi / 6,
        )
        params_high = DABParams(
            v_in=400.0, v_out=48.0, p_out=1000.0,
            f_sw=200e3, l_s=50e-6, n=4.0, phi=math.pi / 6,
        )

        r_low = topo.calculate_losses(transistor, transistor, params_low)
        r_high = topo.calculate_losses(transistor, transistor, params_high)

        total_sw_low = r_low.p_sw_primary + r_low.p_sw_secondary
        total_sw_high = r_high.p_sw_primary + r_high.p_sw_secondary
        assert total_sw_high > total_sw_low

    def test_negative_power_raises(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify negative power raises ValueError."""
        topo = DABTopology()
        params = DABParams(
            v_in=400.0, v_out=48.0, p_out=-500.0,
            f_sw=100e3, l_s=50e-6, n=4.0, phi=math.pi / 6,
        )
        with pytest.raises(ValueError, match="p_out"):
            topo.calculate_losses(
                basic_transistor, basic_transistor, params,
            )

    def test_bare_transistor_defaults(
        self,
        bare_transistor: Transistor,
        dab_params: DABParams,
    ) -> None:
        """Verify topology works with transistor lacking data."""
        topo = DABTopology()
        result = topo.calculate_losses(
            bare_transistor, bare_transistor, dab_params,
        )
        assert result.p_total >= 0


# ---------------------------------------------------------------------------
# LLC tests
# ---------------------------------------------------------------------------


class TestLLC:
    """Tests for LLCTopology."""

    @pytest.fixture
    def llc_params_below_resonance(self) -> LLCParams:
        """LLC operating below resonance (ZVS region)."""
        return LLCParams(
            v_in=400.0,
            v_out=12.0,
            p_out=300.0,
            f_sw=90e3,
            f_r=100e3,
            l_r=50e-6,
            l_m=250e-6,
            c_r=50e-9,
            n=16.0,
        )

    @pytest.fixture
    def llc_params_above_resonance(self) -> LLCParams:
        """LLC operating above resonance (no ZVS)."""
        return LLCParams(
            v_in=400.0,
            v_out=12.0,
            p_out=300.0,
            f_sw=120e3,
            f_r=100e3,
            l_r=50e-6,
            l_m=250e-6,
            c_r=50e-9,
            n=16.0,
        )

    def test_basic_result(
        self,
        basic_transistor: Transistor,
        llc_params_below_resonance: LLCParams,
    ) -> None:
        """Verify calculate_losses returns a valid result."""
        topo = LLCTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, llc_params_below_resonance,
        )

        assert result.p_total >= 0
        assert result.p_total == pytest.approx(
            result.p_cond_primary
            + result.p_sw_primary
            + result.p_cond_secondary,
        )

    def test_zvs_below_resonance(
        self,
        basic_transistor: Transistor,
        llc_params_below_resonance: LLCParams,
    ) -> None:
        """Verify ZVS is achieved when f_sw < f_r."""
        topo = LLCTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, llc_params_below_resonance,
        )
        assert result.is_zvs is True

    def test_no_zvs_above_resonance(
        self,
        basic_transistor: Transistor,
        llc_params_above_resonance: LLCParams,
    ) -> None:
        """Verify no ZVS when f_sw > f_r."""
        topo = LLCTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, llc_params_above_resonance,
        )
        assert result.is_zvs is False

    def test_gain_calculation(
        self,
        basic_transistor: Transistor,
        llc_params_below_resonance: LLCParams,
    ) -> None:
        """Verify voltage gain is computed correctly."""
        topo = LLCTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, llc_params_below_resonance,
        )
        expected_gain = 12.0 / (400.0 / (2.0 * 16.0))
        assert result.gain == pytest.approx(expected_gain)

    def test_i_rms_positive(
        self,
        basic_transistor: Transistor,
        llc_params_below_resonance: LLCParams,
    ) -> None:
        """Verify resonant RMS current is positive."""
        topo = LLCTopology()
        result = topo.calculate_losses(
            basic_transistor, basic_transistor, llc_params_below_resonance,
        )
        assert result.i_rms_resonant > 0

    def test_higher_frequency_more_switching_loss(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify switching loss increases with frequency (non-ZVS region)."""
        topo = LLCTopology()

        params_low = LLCParams(
            v_in=400.0, v_out=12.0, p_out=300.0,
            f_sw=110e3, f_r=100e3,
            l_r=50e-6, l_m=250e-6, c_r=50e-9, n=16.0,
        )
        params_high = LLCParams(
            v_in=400.0, v_out=12.0, p_out=300.0,
            f_sw=200e3, f_r=100e3,
            l_r=50e-6, l_m=250e-6, c_r=50e-9, n=16.0,
        )

        r_low = topo.calculate_losses(
            basic_transistor, basic_transistor, params_low,
        )
        r_high = topo.calculate_losses(
            basic_transistor, basic_transistor, params_high,
        )
        assert r_high.p_sw_primary > r_low.p_sw_primary

    def test_negative_power_raises(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify negative power raises ValueError."""
        topo = LLCTopology()
        params = LLCParams(
            v_in=400.0, v_out=12.0, p_out=-300.0,
            f_sw=90e3, f_r=100e3,
            l_r=50e-6, l_m=250e-6, c_r=50e-9, n=16.0,
        )
        with pytest.raises(ValueError, match="p_out"):
            topo.calculate_losses(
                basic_transistor, basic_transistor, params,
            )

    def test_bare_transistor_defaults(
        self,
        bare_transistor: Transistor,
        llc_params_below_resonance: LLCParams,
    ) -> None:
        """Verify topology works with transistor lacking data."""
        topo = LLCTopology()
        result = topo.calculate_losses(
            bare_transistor, bare_transistor, llc_params_below_resonance,
        )
        assert result.p_total >= 0


# ---------------------------------------------------------------------------
# SRC-ZVS tests
# ---------------------------------------------------------------------------


class TestSRCZVS:
    """Tests for SRCZVSTopology."""

    @pytest.fixture
    def src_params_zvs(self) -> SRCZVSParams:
        """SRC operating above resonance (ZVS achieved)."""
        return SRCZVSParams(
            v_in=400.0,
            v_out=48.0,
            p_out=500.0,
            f_sw=120e3,
            l_r=30e-6,
            c_r=70e-9,
            n=4.0,
        )

    @pytest.fixture
    def src_params_no_zvs(self) -> SRCZVSParams:
        """SRC operating below resonance (no ZVS)."""
        return SRCZVSParams(
            v_in=400.0,
            v_out=48.0,
            p_out=500.0,
            f_sw=80e3,
            l_r=30e-6,
            c_r=70e-9,
            n=4.0,
        )

    def test_basic_result(
        self,
        basic_transistor: Transistor,
        src_params_zvs: SRCZVSParams,
    ) -> None:
        """Verify calculate_losses returns a valid result."""
        topo = SRCZVSTopology()
        result = topo.calculate_losses(basic_transistor, src_params_zvs)

        assert result.p_total >= 0
        assert result.p_total == pytest.approx(result.p_cond + result.p_sw)

    def test_zvs_above_resonance(
        self,
        basic_transistor: Transistor,
        src_params_zvs: SRCZVSParams,
    ) -> None:
        """Verify ZVS is achieved when f_sw > f_r."""
        topo = SRCZVSTopology()
        result = topo.calculate_losses(basic_transistor, src_params_zvs)
        assert result.is_zvs is True

    def test_no_zvs_below_resonance(
        self,
        basic_transistor: Transistor,
        src_params_no_zvs: SRCZVSParams,
    ) -> None:
        """Verify no ZVS when f_sw < f_r."""
        topo = SRCZVSTopology()
        result = topo.calculate_losses(basic_transistor, src_params_no_zvs)
        assert result.is_zvs is False

    def test_q_factor_positive(
        self,
        basic_transistor: Transistor,
        src_params_zvs: SRCZVSParams,
    ) -> None:
        """Verify Q factor is positive."""
        topo = SRCZVSTopology()
        result = topo.calculate_losses(basic_transistor, src_params_zvs)
        assert result.q_factor > 0

    def test_i_rms_positive(
        self,
        basic_transistor: Transistor,
        src_params_zvs: SRCZVSParams,
    ) -> None:
        """Verify resonant RMS current is positive."""
        topo = SRCZVSTopology()
        result = topo.calculate_losses(basic_transistor, src_params_zvs)
        assert result.i_rms_resonant > 0

    def test_higher_frequency_more_switching_loss(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify switching loss increases with frequency."""
        topo = SRCZVSTopology()

        params_low = SRCZVSParams(
            v_in=400.0, v_out=48.0, p_out=500.0,
            f_sw=120e3, l_r=30e-6, c_r=70e-9, n=4.0,
        )
        params_high = SRCZVSParams(
            v_in=400.0, v_out=48.0, p_out=500.0,
            f_sw=300e3, l_r=30e-6, c_r=70e-9, n=4.0,
        )

        r_low = topo.calculate_losses(basic_transistor, params_low)
        r_high = topo.calculate_losses(basic_transistor, params_high)
        assert r_high.p_sw > r_low.p_sw

    def test_negative_power_raises(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify negative power raises ValueError."""
        topo = SRCZVSTopology()
        params = SRCZVSParams(
            v_in=400.0, v_out=48.0, p_out=-500.0,
            f_sw=120e3, l_r=30e-6, c_r=70e-9, n=4.0,
        )
        with pytest.raises(ValueError, match="p_out"):
            topo.calculate_losses(basic_transistor, params)

    def test_negative_voltage_raises(
        self, basic_transistor: Transistor,
    ) -> None:
        """Verify negative input voltage raises ValueError."""
        topo = SRCZVSTopology()
        params = SRCZVSParams(
            v_in=-400.0, v_out=48.0, p_out=500.0,
            f_sw=120e3, l_r=30e-6, c_r=70e-9, n=4.0,
        )
        with pytest.raises(ValueError, match="v_in"):
            topo.calculate_losses(basic_transistor, params)

    def test_bare_transistor_defaults(
        self,
        bare_transistor: Transistor,
        src_params_zvs: SRCZVSParams,
    ) -> None:
        """Verify topology works with transistor lacking data."""
        topo = SRCZVSTopology()
        result = topo.calculate_losses(bare_transistor, src_params_zvs)
        assert result.p_total >= 0
