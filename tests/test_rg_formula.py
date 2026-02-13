"""Tests for gate resistance dependent switching energy."""
from __future__ import annotations

import numpy as np
import pytest

from transistordatabase.core.models import SwitchingLossData
from transistordatabase.rg_formula import (
    find_rg_for_target_energy,
    get_available_rg_values,
    interpolate_energy_at_rg,
    scale_energy_by_rg,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def loss_data_with_graph_r_e() -> list[SwitchingLossData]:
    """SwitchingLossData entries that carry graph_r_e curves."""
    return [
        SwitchingLossData(
            dataset_type="graph_r_e",
            t_j=25.0,
            v_supply=800.0,
            v_g=15.0,
            r_g=5.0,
            graph_r_e=np.array([
                [1.0, 2.5, 5.0, 10.0, 20.0],   # resistance (Ohm)
                [0.5e-3, 0.8e-3, 1.2e-3, 2.0e-3, 3.5e-3],  # energy (J)
            ]),
        ),
    ]


@pytest.fixture()
def loss_data_with_graph_i_e() -> list[SwitchingLossData]:
    """SwitchingLossData entries with graph_i_e at different r_g values."""
    currents = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0])
    return [
        SwitchingLossData(
            dataset_type="graph_i_e",
            t_j=25.0,
            v_supply=800.0,
            v_g=15.0,
            r_g=2.5,
            graph_i_e=np.array([
                currents,
                np.array([0.0, 0.1e-3, 0.3e-3, 0.6e-3, 1.0e-3, 1.5e-3]),
            ]),
        ),
        SwitchingLossData(
            dataset_type="graph_i_e",
            t_j=25.0,
            v_supply=800.0,
            v_g=15.0,
            r_g=5.0,
            graph_i_e=np.array([
                currents,
                np.array([0.0, 0.15e-3, 0.45e-3, 0.9e-3, 1.5e-3, 2.25e-3]),
            ]),
        ),
        SwitchingLossData(
            dataset_type="graph_i_e",
            t_j=25.0,
            v_supply=800.0,
            v_g=15.0,
            r_g=10.0,
            graph_i_e=np.array([
                currents,
                np.array([0.0, 0.2e-3, 0.6e-3, 1.2e-3, 2.0e-3, 3.0e-3]),
            ]),
        ),
        # A dataset at a different temperature (150 deg C)
        SwitchingLossData(
            dataset_type="graph_i_e",
            t_j=150.0,
            v_supply=800.0,
            v_g=15.0,
            r_g=5.0,
            graph_i_e=np.array([
                currents,
                np.array([0.0, 0.18e-3, 0.54e-3, 1.08e-3, 1.8e-3, 2.7e-3]),
            ]),
        ),
    ]


# ---------------------------------------------------------------------------
# TestInterpolateEnergyAtRg
# ---------------------------------------------------------------------------


class TestInterpolateEnergyAtRg:
    """Tests for interpolate_energy_at_rg."""

    def test_direct_interpolation_from_graph_r_e(
        self, loss_data_with_graph_r_e: list[SwitchingLossData]
    ) -> None:
        """Interpolate directly on the Rg-Energy curve."""
        energy = interpolate_energy_at_rg(
            loss_data_with_graph_r_e, r_g=5.0, i_channel=20.0, t_j=25.0,
        )
        assert energy == pytest.approx(1.2e-3, rel=1e-6)

    def test_direct_interpolation_midpoint(
        self, loss_data_with_graph_r_e: list[SwitchingLossData]
    ) -> None:
        """Interpolate at an Rg between data points on graph_r_e."""
        energy = interpolate_energy_at_rg(
            loss_data_with_graph_r_e, r_g=7.5, i_channel=20.0, t_j=25.0,
        )
        # Linear interp between (5.0, 1.2e-3) and (10.0, 2.0e-3)
        expected = 1.2e-3 + (2.0e-3 - 1.2e-3) * (7.5 - 5.0) / (10.0 - 5.0)
        assert energy == pytest.approx(expected, rel=1e-6)

    def test_fallback_to_closest_rg(
        self, loss_data_with_graph_i_e: list[SwitchingLossData]
    ) -> None:
        """Fall back to closest r_g dataset when no graph_r_e is present."""
        # r_g=4.0 is closest to the dataset at r_g=5.0
        energy = interpolate_energy_at_rg(
            loss_data_with_graph_i_e, r_g=4.0, i_channel=30.0, t_j=25.0,
        )
        # At r_g=5.0, i=30 -> 0.9e-3
        assert energy == pytest.approx(0.9e-3, rel=1e-6)

    def test_exact_rg_match(
        self, loss_data_with_graph_i_e: list[SwitchingLossData]
    ) -> None:
        """Exact Rg match on graph_i_e datasets."""
        energy = interpolate_energy_at_rg(
            loss_data_with_graph_i_e, r_g=10.0, i_channel=40.0, t_j=25.0,
        )
        assert energy == pytest.approx(2.0e-3, rel=1e-6)

    def test_no_data_returns_zero(self) -> None:
        """Return 0.0 when no loss data is provided."""
        assert interpolate_energy_at_rg([], r_g=5.0, i_channel=20.0, t_j=25.0) == 0.0

    def test_no_matching_temperature_returns_zero(
        self, loss_data_with_graph_i_e: list[SwitchingLossData]
    ) -> None:
        """Return 0.0 when no dataset matches the requested temperature."""
        energy = interpolate_energy_at_rg(
            loss_data_with_graph_i_e, r_g=5.0, i_channel=20.0, t_j=75.0,
        )
        assert energy == 0.0


# ---------------------------------------------------------------------------
# TestScaleEnergyByRg
# ---------------------------------------------------------------------------


class TestScaleEnergyByRg:
    """Tests for scale_energy_by_rg."""

    def test_linear_scaling(self) -> None:
        """Linear scaling: E_target = E_ref * r_g_target / r_g_ref."""
        result = scale_energy_by_rg(
            e_ref=1.0e-3, r_g_ref=5.0, r_g_target=10.0, scaling="linear",
        )
        assert result == pytest.approx(2.0e-3, rel=1e-9)

    def test_sqrt_scaling(self) -> None:
        """Square-root scaling: E_target = E_ref * sqrt(r_g_target / r_g_ref)."""
        result = scale_energy_by_rg(
            e_ref=1.0e-3, r_g_ref=4.0, r_g_target=16.0, scaling="sqrt",
        )
        # sqrt(16/4) = 2.0
        assert result == pytest.approx(2.0e-3, rel=1e-9)

    def test_identity_scaling(self) -> None:
        """Scaling with same Rg returns the reference energy."""
        result = scale_energy_by_rg(
            e_ref=1.5e-3, r_g_ref=5.0, r_g_target=5.0, scaling="linear",
        )
        assert result == pytest.approx(1.5e-3, rel=1e-9)

    def test_rg_ref_zero_raises(self) -> None:
        """Zero reference resistance raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            scale_energy_by_rg(
                e_ref=1.0e-3, r_g_ref=0.0, r_g_target=5.0, scaling="linear",
            )

    def test_unknown_scaling_raises(self) -> None:
        """Unknown scaling method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown scaling method"):
            scale_energy_by_rg(
                e_ref=1.0e-3, r_g_ref=5.0, r_g_target=10.0, scaling="quadratic",
            )


# ---------------------------------------------------------------------------
# TestFindRgForTargetEnergy
# ---------------------------------------------------------------------------


class TestFindRgForTargetEnergy:
    """Tests for find_rg_for_target_energy."""

    def test_find_rg_from_graph_r_e(
        self, loss_data_with_graph_r_e: list[SwitchingLossData]
    ) -> None:
        """Find Rg from a graph_r_e curve."""
        rg = find_rg_for_target_energy(
            loss_data_with_graph_r_e,
            e_target=1.2e-3,
            i_channel=20.0,
            t_j=25.0,
        )
        assert rg is not None
        assert rg == pytest.approx(5.0, rel=1e-6)

    def test_find_rg_interpolated(
        self, loss_data_with_graph_r_e: list[SwitchingLossData]
    ) -> None:
        """Find an Rg value between data points on graph_r_e."""
        # Energy 1.6e-3 lies between (5.0, 1.2e-3) and (10.0, 2.0e-3)
        rg = find_rg_for_target_energy(
            loss_data_with_graph_r_e,
            e_target=1.6e-3,
            i_channel=20.0,
            t_j=25.0,
        )
        assert rg is not None
        # Linear interp: rg = 5.0 + (10.0-5.0)*(1.6e-3-1.2e-3)/(2.0e-3-1.2e-3) = 7.5
        assert rg == pytest.approx(7.5, rel=1e-3)

    def test_target_outside_range_returns_none(
        self, loss_data_with_graph_r_e: list[SwitchingLossData]
    ) -> None:
        """Return None when target energy is outside the data range."""
        rg = find_rg_for_target_energy(
            loss_data_with_graph_r_e,
            e_target=10.0,
            i_channel=20.0,
            t_j=25.0,
        )
        assert rg is None

    def test_find_rg_from_graph_i_e_fallback(
        self, loss_data_with_graph_i_e: list[SwitchingLossData]
    ) -> None:
        """Fall back to building Rg-energy map from graph_i_e datasets."""
        # At i_channel=30, the three datasets give:
        #   r_g=2.5 -> 0.6e-3,  r_g=5.0 -> 0.9e-3,  r_g=10.0 -> 1.2e-3
        rg = find_rg_for_target_energy(
            loss_data_with_graph_i_e,
            e_target=0.9e-3,
            i_channel=30.0,
            t_j=25.0,
        )
        assert rg is not None
        assert rg == pytest.approx(5.0, rel=1e-3)

    def test_empty_data_returns_none(self) -> None:
        """Return None for empty loss data list."""
        assert find_rg_for_target_energy([], e_target=1.0e-3, i_channel=20.0, t_j=25.0) is None


# ---------------------------------------------------------------------------
# TestGetAvailableRgValues
# ---------------------------------------------------------------------------


class TestGetAvailableRgValues:
    """Tests for get_available_rg_values."""

    def test_extraction(
        self, loss_data_with_graph_i_e: list[SwitchingLossData]
    ) -> None:
        """Extract unique Rg values sorted in ascending order."""
        rg_values = get_available_rg_values(loss_data_with_graph_i_e)
        assert rg_values == [2.5, 5.0, 10.0]

    def test_empty_list(self) -> None:
        """Return empty list for empty input."""
        assert get_available_rg_values([]) == []

    def test_none_rg_excluded(self) -> None:
        """Datasets without r_g are excluded."""
        data = [
            SwitchingLossData(
                dataset_type="graph_i_e",
                t_j=25.0,
                v_supply=800.0,
                v_g=15.0,
                r_g=None,
            ),
        ]
        assert get_available_rg_values(data) == []

    def test_duplicates_collapsed(self) -> None:
        """Duplicate Rg values are collapsed to unique entries."""
        data = [
            SwitchingLossData(
                dataset_type="graph_i_e",
                t_j=25.0,
                v_supply=800.0,
                v_g=15.0,
                r_g=5.0,
            ),
            SwitchingLossData(
                dataset_type="graph_i_e",
                t_j=150.0,
                v_supply=800.0,
                v_g=15.0,
                r_g=5.0,
            ),
        ]
        assert get_available_rg_values(data) == [5.0]
