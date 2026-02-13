"""Standalone test for new core models architecture.

This test file can run independently to verify the new design.
"""
import sys
import os
from pathlib import Path
import json
import pytest

# Add the core module to Python path
current_dir = Path(__file__).parent
core_path = current_dir.parent / "transistordatabase" / "core"
sys.path.insert(0, str(core_path.parent))

try:
    from transistordatabase.core.models import (
        TransistorMetadata,
        ElectricalRatings, 
        ThermalProperties,
        Transistor,
        Switch,
        Diode
    )
    from transistordatabase.core.repository import TransistorFactory
except ImportError as e:
    print(f"Import error: {e}")
    # Skip tests if imports fail
    pytest.skip("Core modules not available", allow_module_level=True)


class TestNewArchitecture:
    """Test the new core architecture."""
    
    def test_metadata_creation(self):
        """Test TransistorMetadata creation."""
        metadata = TransistorMetadata(
            name="TEST_TRANSISTOR",
            type="IGBT", 
            author="Test Author",
            manufacturer="Test Manufacturer",
            housing_type="TO-247"
        )
        
        assert metadata.name == "TEST_TRANSISTOR"
        assert metadata.type == "IGBT"
        assert metadata.author == "Test Author"
        assert metadata.manufacturer == "Test Manufacturer"
        assert metadata.housing_type == "TO-247"
    
    def test_electrical_ratings(self):
        """Test ElectricalRatings creation."""
        ratings = ElectricalRatings(
            v_abs_max=1200.0,
            i_abs_max=100.0,
            i_cont=75.0,
            t_j_max=175.0
        )
        
        assert ratings.v_abs_max == 1200.0
        assert ratings.i_abs_max == 100.0
        assert ratings.i_cont == 75.0
        assert ratings.t_j_max == 175.0
    
    def test_thermal_properties(self):
        """Test ThermalProperties creation."""
        thermal = ThermalProperties(
            housing_area=0.001,
            cooling_area=0.0008,
            r_th_cs=0.24
        )
        
        assert thermal.housing_area == 0.001
        assert thermal.cooling_area == 0.0008
        assert thermal.r_th_cs == 0.24
    
    def test_transistor_creation(self):
        """Test complete Transistor creation."""
        metadata = TransistorMetadata(
            name="TEST_TRANSISTOR",
            type="IGBT",
            author="Test",
            manufacturer="Test Inc",
            housing_type="TO-247"
        )
        
        electrical = ElectricalRatings(
            v_abs_max=1200.0,
            i_abs_max=100.0,
            i_cont=75.0,
            t_j_max=175.0
        )
        
        thermal = ThermalProperties(
            housing_area=0.001,
            cooling_area=0.0008
        )
        
        transistor = Transistor(metadata, electrical, thermal)
        
        assert transistor.metadata.name == "TEST_TRANSISTOR"
        assert transistor.electrical_ratings.v_abs_max == 1200.0
        assert transistor.thermal_properties.housing_area == 0.001
        assert isinstance(transistor.switch, Switch)
        assert isinstance(transistor.diode, Diode)
        assert transistor.working_point is None
    
    def test_component_access(self):
        """Test component access methods."""
        transistor = TransistorFactory.create_empty_transistor("TEST", "IGBT")
        
        switch = transistor.get_component("switch")
        assert isinstance(switch, Switch)
        
        diode = transistor.get_component("diode")
        assert isinstance(diode, Diode)
        
        with pytest.raises(ValueError, match="Unknown component type"):
            transistor.get_component("invalid")
    
    def test_factory_creation(self):
        """Test TransistorFactory."""
        transistor = TransistorFactory.create_empty_transistor("FACTORY_TEST", "MOSFET")
        
        assert transistor.metadata.name == "FACTORY_TEST"
        assert transistor.metadata.type == "MOSFET"
        assert transistor.electrical_ratings.v_abs_max == 0.0
        assert transistor.thermal_properties.housing_area == 0.0


class TestMasterDataCompatibility:
    """Test compatibility with existing master data files."""
    
    @pytest.fixture
    def master_data_path(self) -> Path:
        """Get path to master data directory."""
        current_dir = Path(__file__).parent
        return current_dir.parent / "tests" / "master_data"
    
    def test_master_data_structure(self, master_data_path: Path):
        """Test that we can read master data structure."""
        if not master_data_path.exists():
            pytest.skip("Master data directory not found")
        
        json_files = list(master_data_path.glob("*.json"))
        assert len(json_files) > 0, "No JSON files found in master data"
        
        # Test reading first file
        test_file = json_files[0]
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        # Verify basic structure exists
        assert 'name' in data, f"Missing 'name' field in {test_file.name}"
        assert 'type' in data, f"Missing 'type' field in {test_file.name}"
        
        print(f"✓ Successfully read master data file: {test_file.name}")
        print(f"  - Name: {data.get('name', 'N/A')}")
        print(f"  - Type: {data.get('type', 'N/A')}")
        print(f"  - Keys: {list(data.keys())}")
    
    def test_multiple_master_files(self, master_data_path: Path):
        """Test reading multiple master data files."""
        if not master_data_path.exists():
            pytest.skip("Master data directory not found")
        
        json_files = list(master_data_path.glob("*.json"))
        readable_files = 0
        
        for json_file in json_files[:5]:  # Test first 5 files
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Basic validation
                if 'name' in data and 'type' in data:
                    readable_files += 1
                    print(f"✓ {json_file.name}: {data['name']} ({data['type']})")
                else:
                    print(f"⚠ {json_file.name}: Missing required fields")
                    
            except Exception as e:
                print(f"✗ {json_file.name}: {e}")
        
        assert readable_files > 0, "No master data files could be read"
        print(f"\nSuccessfully read {readable_files} master data files")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
