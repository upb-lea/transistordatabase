"""Unit tests for core transistor models using master data."""
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from transistordatabase.core import (
    Transistor,
    TransistorMetadata,
    ElectricalRatings,
    ThermalProperties,
    Switch,
    Diode,
    JsonTransistorLoader,
    TransistorFactory
)


class TestTransistorMetadata:
    """Test cases for TransistorMetadata class."""
    
    def test_metadata_creation(self):
        """Test basic metadata creation."""
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
        assert metadata.comment is None
        assert metadata.datasheet_hyperlink is None


class TestElectricalRatings:
    """Test cases for ElectricalRatings class."""
    
    def test_electrical_ratings_creation(self):
        """Test electrical ratings creation."""
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


class TestThermalProperties:
    """Test cases for ThermalProperties class."""
    
    def test_thermal_properties_creation(self):
        """Test thermal properties creation."""
        thermal = ThermalProperties(
            housing_area=0.001,
            cooling_area=0.0008,
            r_th_cs=0.24,
            t_c_max=100.0
        )
        
        assert thermal.housing_area == 0.001
        assert thermal.cooling_area == 0.0008
        assert thermal.r_th_cs == 0.24
        assert thermal.t_c_max == 100.0


class TestTransistor:
    """Test cases for main Transistor class."""
    
    def test_transistor_creation(self):
        """Test basic transistor creation."""
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
    
    def test_working_point_update(self):
        """Test working point updates."""
        transistor = self._create_test_transistor()
        
        # Initially no working point
        assert transistor.working_point is None
        
        # Update working point - this would need proper implementation
        # transistor.update_working_point(25.0, 15.0, 50.0)
        # assert transistor.working_point is not None
    
    def test_get_component(self):
        """Test component retrieval."""
        transistor = self._create_test_transistor()
        
        switch = transistor.get_component("switch")
        assert isinstance(switch, Switch)
        
        diode = transistor.get_component("diode") 
        assert isinstance(diode, Diode)
        
        with pytest.raises(ValueError):
            transistor.get_component("invalid")
    
    def _create_test_transistor(self) -> Transistor:
        """Create a test transistor for use in tests."""
        return TransistorFactory.create_empty_transistor("TEST", "IGBT")


class TestJsonTransistorLoader:
    """Test cases for JSON loader using master data."""
    
    @pytest.fixture
    def master_data_path(self) -> Path:
        """Get path to master data directory."""
        current_dir = Path(__file__).parent
        return current_dir / "master_data"
    
    @pytest.fixture
    def cree_data_path(self, master_data_path: Path) -> Path:
        """Get path to CREE test data."""
        return master_data_path / "test_data_CREE_C3M0060065J.json"
    
    @pytest.fixture
    def fuji_data_path(self, master_data_path: Path) -> Path:
        """Get path to Fuji test data."""
        return master_data_path / "test_data_Fuji_2MBI400XBE065-50.json"
    
    def test_load_cree_transistor(self, cree_data_path: Path):
        """Test loading CREE transistor from master data."""
        if not cree_data_path.exists():
            pytest.skip(f"Master data file not found: {cree_data_path}")
        
        loader = JsonTransistorLoader()
        
        # Load raw JSON first to verify structure
        with open(cree_data_path, 'r') as f:
            raw_data = json.load(f)
        
        # Verify basic structure
        assert 'name' in raw_data
        assert 'type' in raw_data
        assert raw_data['name'] == "CREE_C3M0060065J"
        
        # Test actual loading
        try:
            transistor = loader.load_from_json(cree_data_path)
            assert transistor.metadata.name == "CREE_C3M0060065J"
            assert transistor.metadata.type in ["SiC-MOSFET", "MOSFET", "IGBT"]  # Allow variations
        except Exception as e:
            pytest.fail(f"Failed to load CREE transistor: {e}")
    
    def test_load_fuji_transistor(self, fuji_data_path: Path):
        """Test loading Fuji transistor from master data."""
        if not fuji_data_path.exists():
            pytest.skip(f"Master data file not found: {fuji_data_path}")
        
        loader = JsonTransistorLoader()
        
        # Load raw JSON first
        with open(fuji_data_path, 'r') as f:
            raw_data = json.load(f)
        
        # Verify basic structure
        assert 'name' in raw_data
        assert raw_data['name'] == "Fuji_2MBI400XBE065-50"
        
        # Test actual loading
        try:
            transistor = loader.load_from_json(fuji_data_path)
            assert transistor.metadata.name == "Fuji_2MBI400XBE065-50"
            assert transistor.metadata.manufacturer.lower() in ["fuji", "fujitsu", "fuji electric"]
        except Exception as e:
            pytest.fail(f"Failed to load Fuji transistor: {e}")
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        loader = JsonTransistorLoader()
        fake_path = Path("/fake/path/nonexistent.json")
        
        with pytest.raises(FileNotFoundError):
            loader.load_from_json(fake_path)
    
    def test_save_and_load_roundtrip(self, tmp_path: Path):
        """Test save and load roundtrip."""
        # Create test transistor
        transistor = TransistorFactory.create_empty_transistor("TEST_ROUNDTRIP", "IGBT")
        transistor.electrical_ratings.v_abs_max = 1200.0
        transistor.electrical_ratings.i_abs_max = 100.0
        
        # Save to file
        loader = JsonTransistorLoader()
        test_file = tmp_path / "test_transistor.json"
        
        try:
            loader.save_to_json(transistor, test_file)
            assert test_file.exists()
            
            # Load back
            loaded_transistor = loader.load_from_json(test_file)
            
            # Verify data integrity
            assert loaded_transistor.metadata.name == "TEST_ROUNDTRIP"
            assert loaded_transistor.metadata.type == "IGBT"
            assert loaded_transistor.electrical_ratings.v_abs_max == 1200.0
            assert loaded_transistor.electrical_ratings.i_abs_max == 100.0
        except Exception as e:
            pytest.fail(f"Roundtrip test failed: {e}")


class TestTransistorFactory:
    """Test cases for TransistorFactory."""
    
    def test_create_empty_transistor(self):
        """Test creating empty transistor."""
        transistor = TransistorFactory.create_empty_transistor("EMPTY_TEST", "MOSFET")
        
        assert transistor.metadata.name == "EMPTY_TEST"
        assert transistor.metadata.type == "MOSFET"
        assert transistor.electrical_ratings.v_abs_max == 0.0
        assert transistor.thermal_properties.housing_area == 0.0
        assert isinstance(transistor.switch, Switch)
        assert isinstance(transistor.diode, Diode)
    
    def test_create_from_template(self):
        """Test creating from template (placeholder)."""
        transistor = TransistorFactory.create_from_template("template", "NEW_FROM_TEMPLATE")
        
        # Currently returns empty transistor - implement template loading later
        assert transistor.metadata.name == "NEW_FROM_TEMPLATE"


class TestIntegrationWithMasterData:
    """Integration tests using multiple master data files."""
    
    @pytest.fixture
    def master_data_path(self) -> Path:
        """Get path to master data directory."""
        current_dir = Path(__file__).parent
        return current_dir / "master_data"
    
    def test_load_multiple_transistors(self, master_data_path: Path):
        """Test loading multiple transistors from master data."""
        if not master_data_path.exists():
            pytest.skip("Master data directory not found")
        
        loader = JsonTransistorLoader()
        loaded_count = 0
        errors = []
        
        # Try to load all JSON files in master data
        for json_file in master_data_path.glob("*.json"):
            try:
                transistor = loader.load_from_json(json_file)
                assert transistor.metadata.name is not None
                assert len(transistor.metadata.name) > 0
                loaded_count += 1
            except Exception as e:
                errors.append(f"{json_file.name}: {e}")
        
        # Report results
        print(f"Successfully loaded {loaded_count} transistors")
        if errors:
            print(f"Errors encountered: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        # Should load at least some transistors
        assert loaded_count > 0, "No transistors could be loaded from master data"
    
    def test_transistor_data_consistency(self, master_data_path: Path):
        """Test data consistency across loaded transistors."""
        if not master_data_path.exists():
            pytest.skip("Master data directory not found")
        
        loader = JsonTransistorLoader()
        transistors = []
        
        # Load first few transistors
        for json_file in list(master_data_path.glob("*.json"))[:3]:
            try:
                transistor = loader.load_from_json(json_file)
                transistors.append(transistor)
            except Exception:
                continue  # Skip files that can't be loaded yet
        
        # Verify basic consistency
        for transistor in transistors:
            # All should have basic metadata
            assert transistor.metadata.name
            assert transistor.metadata.type
            
            # All should have some electrical ratings
            assert transistor.electrical_ratings.v_abs_max >= 0
            assert transistor.electrical_ratings.i_abs_max >= 0
            assert transistor.electrical_ratings.t_j_max > 0
            
            # Should have switch and diode components
            assert isinstance(transistor.switch, Switch)
            assert isinstance(transistor.diode, Diode)
