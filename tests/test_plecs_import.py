"""Tests for PLECS XML importer."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from transistordatabase.plecs_importer import import_plecs_xml

TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def sample_switch_xml() -> Path:
    """Return path to sample PLECS switch XML file."""
    return TEST_DATA_DIR / "sample_plecs_switch.xml"


class TestPlecsImport:
    """Tests for PLECS XML import functionality."""

    def test_import_returns_transistor_list(self, sample_switch_xml: Path) -> None:
        """Verify import returns a list of Transistor objects."""
        result = import_plecs_xml(sample_switch_xml)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_metadata_parsed(self, sample_switch_xml: Path) -> None:
        """Verify metadata is correctly extracted from XML."""
        transistors = import_plecs_xml(sample_switch_xml)
        t = transistors[0]
        assert t.metadata.name == "TEST_MOSFET_001"
        assert t.metadata.manufacturer == "TestVendor"
        assert t.metadata.type == "MOSFET"

    def test_channel_data_parsed(self, sample_switch_xml: Path) -> None:
        """Verify conduction loss is mapped to channel characteristics."""
        transistors = import_plecs_xml(sample_switch_xml)
        t = transistors[0]
        assert len(t.switch.channel_data) == 2
        ch_25 = t.switch.channel_data[0]
        assert ch_25.t_j == 25.0
        assert ch_25.graph_v_i.shape == (2, 7)
        # Current axis should be [0, 5, 10, 15, 20, 25, 30]
        np.testing.assert_array_almost_equal(
            ch_25.graph_v_i[1], [0, 5, 10, 15, 20, 25, 30]
        )

    def test_switching_loss_parsed(self, sample_switch_xml: Path) -> None:
        """Verify switching loss data is correctly parsed."""
        transistors = import_plecs_xml(sample_switch_xml)
        t = transistors[0]
        # 2 temperatures x 2 voltages = 4 e_on datasets
        assert len(t.switch.e_on_data) == 4
        assert len(t.switch.e_off_data) == 4

        # Check first dataset: 25C, 400V
        e_on_0 = t.switch.e_on_data[0]
        assert e_on_0.t_j == 25.0
        assert e_on_0.v_supply == 400.0
        assert e_on_0.dataset_type == "graph_i_e"
        assert e_on_0.graph_i_e is not None
        assert e_on_0.graph_i_e.shape == (2, 6)

    def test_thermal_model_parsed(self, sample_switch_xml: Path) -> None:
        """Verify Foster thermal model is correctly parsed."""
        transistors = import_plecs_xml(sample_switch_xml)
        t = transistors[0]
        foster = t.switch.thermal_foster
        assert foster is not None
        assert foster.r_th_vector == [0.05, 0.10, 0.15, 0.20]
        assert foster.tau_vector == [0.001, 0.01, 0.1, 1.0]
        assert foster.r_th_total == pytest.approx(0.50)

    def test_electrical_ratings_inferred(self, sample_switch_xml: Path) -> None:
        """Verify electrical ratings are inferred from data."""
        transistors = import_plecs_xml(sample_switch_xml)
        t = transistors[0]
        assert t.electrical_ratings.v_abs_max == 800.0
        assert t.electrical_ratings.i_abs_max > 0

    def test_file_not_found_raises(self) -> None:
        """Verify FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            import_plecs_xml("/nonexistent/path.xml")

    def test_thermal_impedance_calculation(self, sample_switch_xml: Path) -> None:
        """Verify thermal impedance can be calculated from imported data."""
        transistors = import_plecs_xml(sample_switch_xml)
        foster = transistors[0].switch.thermal_foster
        assert foster is not None

        z_at_0 = foster.get_thermal_impedance(0.0)
        assert z_at_0 == pytest.approx(0.0, abs=1e-6)

        z_at_inf = foster.get_thermal_impedance(1000.0)
        assert z_at_inf == pytest.approx(0.50, abs=0.01)

    def test_energy_scale_applied(self, sample_switch_xml: Path) -> None:
        """Verify energy scale factor (0.001) is applied correctly."""
        transistors = import_plecs_xml(sample_switch_xml)
        e_on = transistors[0].switch.e_on_data[0]
        # Original values in XML: 0.00 0.10 0.30 0.60 1.00 1.50
        # Scale is 0.001, so: 0.0 0.0001 0.0003 0.0006 0.001 0.0015
        np.testing.assert_array_almost_equal(
            e_on.graph_i_e[1],
            [0.0, 0.0001, 0.0003, 0.0006, 0.001, 0.0015],
        )
