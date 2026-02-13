"""Test configuration for the transistor database web application."""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_transistor_flat():
    """Return sample transistor data in flat format (TDB format)."""
    return {
        "name": "Test_CREE_C3M0016120K",
        "type": "SiC-MOSFET",
        "author": "Test Author",
        "technology": None,
        "template_version": None,
        "template_date": None,
        "creation_date": None,
        "last_modified": None,
        "comment": "Test device",
        "datasheet_hyperlink": "https://test.com/datasheet.pdf",
        "datasheet_date": "2023-01",
        "datasheet_version": "1.0",
        "housing_area": 0.000367,
        "cooling_area": 0.00016,
        "t_c_max": None,
        "r_g_int": 2.6,
        "r_g_on_recommended": None,
        "r_g_off_recommended": None,
        "c_oss_fix": 2.3e-10,
        "c_iss_fix": 6.085e-09,
        "c_rss_fix": 1.3e-11,
        "housing_type": "TO247",
        "manufacturer": "Wolfspeed",
        "r_th_cs": 0.27,
        "r_th_switch_cs": 0.27,
        "r_th_diode_cs": 0.27,
        "v_abs_max": 1200,
        "i_abs_max": 250,
        "i_cont": 115,
        "t_j_max": 175
    }

@pytest.fixture
def sample_transistor_nested():
    """Return sample transistor data in nested format (web interface format)."""
    return {
        "metadata": {
            "name": "Test_Nested_Device",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "housing_type": "TO220",
            "author": "Test Author",
            "comment": "Test nested format device"
        },
        "electrical": {
            "v_abs_max": 600,
            "i_abs_max": 30,
            "i_cont": 25,
            "t_j_max": 175
        },
        "thermal": {
            "r_th_cs": 0.5,
            "housing_area": 0.001,
            "cooling_area": 0.0005
        }
    }

@pytest.fixture
def multiple_transistors_data():
    """Return multiple transistor samples for testing collections."""
    return [
        {
            "name": "Device_A",
            "type": "MOSFET",
            "manufacturer": "Corp_A",
            "housing_type": "TO220",
            "v_abs_max": 600,
            "i_abs_max": 30,
            "i_cont": 25,
            "t_j_max": 175,
            "r_th_cs": 0.5,
            "housing_area": 0.001,
            "cooling_area": 0.0005
        },
        {
            "name": "Device_B",
            "type": "IGBT",
            "manufacturer": "Corp_B",
            "housing_type": "TO247",
            "v_abs_max": 1200,
            "i_abs_max": 150,
            "i_cont": 120,
            "t_j_max": 175,
            "r_th_cs": 0.3,
            "housing_area": 0.002,
            "cooling_area": 0.001
        },
        {
            "name": "Device_C",
            "type": "SiC-MOSFET",
            "manufacturer": "Corp_C",
            "housing_type": "TO247",
            "v_abs_max": 1700,
            "i_abs_max": 200,
            "i_cont": 180,
            "t_j_max": 200,
            "r_th_cs": 0.25,
            "housing_area": 0.0015,
            "cooling_area": 0.0008
        }
    ]
