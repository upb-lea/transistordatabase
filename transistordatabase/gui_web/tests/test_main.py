"""
Test cases for the FastAPI backend main.py module.

This module tests all functions and API endpoints in the main.py file.
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch
import sys
import os

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient  # noqa: E402
from main import app, dict_to_transistor, transistor_to_dict, transistors_db  # noqa: E402

# Create test client
client = TestClient(app)

class TestMainFunctions:
    """Test the utility functions in main.py."""
    
    def setup_method(self):
        """Set up for each test method."""
        # Clear the database before each test
        transistors_db.clear()
    
    def test_dict_to_transistor_nested_format(self):
        """Test dict_to_transistor with nested format (web interface format)."""
        data = {
            "metadata": {
                "name": "Test_MOSFET",
                "type": "MOSFET",
                "manufacturer": "TestCorp",
                "housing_type": "TO220",
                "author": "Test Author",
                "comment": "Test comment"
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
        
        transistor = dict_to_transistor(data)
        
        assert transistor.metadata.name == "Test_MOSFET"
        assert transistor.metadata.type == "MOSFET"
        assert transistor.metadata.manufacturer == "TestCorp"
        assert transistor.metadata.housing_type == "TO220"
        assert transistor.metadata.author == "Test Author"
        assert transistor.metadata.comment == "Test comment"
        assert transistor.electrical_ratings.v_abs_max == 600
        assert transistor.electrical_ratings.i_abs_max == 30
        assert transistor.electrical_ratings.i_cont == 25
        assert transistor.electrical_ratings.t_j_max == 175
        assert transistor.thermal_properties.r_th_cs == 0.5
        assert transistor.thermal_properties.housing_area == 0.001
        assert transistor.thermal_properties.cooling_area == 0.0005
    
    def test_dict_to_transistor_flat_format(self):
        """Test dict_to_transistor with flat format (TDB file format)."""
        data = {
            "name": "CREE_C3M0016120K",
            "type": "SiC-MOSFET",
            "manufacturer": "Wolfspeed",
            "housing_type": "TO247",
            "author": "Test Author",
            "comment": "Test CREE device",
            "v_abs_max": 1200,
            "i_abs_max": 250,
            "i_cont": 115,
            "t_j_max": 175,
            "r_th_cs": 0.27,
            "housing_area": 0.000367,
            "cooling_area": 0.00016
        }
        
        transistor = dict_to_transistor(data)
        
        assert transistor.metadata.name == "CREE_C3M0016120K"
        assert transistor.metadata.type == "SiC-MOSFET"
        assert transistor.metadata.manufacturer == "Wolfspeed"
        assert transistor.metadata.housing_type == "TO247"
        assert transistor.electrical_ratings.v_abs_max == 1200
        assert transistor.electrical_ratings.i_abs_max == 250
        assert transistor.electrical_ratings.i_cont == 115
        assert transistor.electrical_ratings.t_j_max == 175
        assert transistor.thermal_properties.r_th_cs == 0.27
    
    def test_dict_to_transistor_flat_format_with_missing_fields(self):
        """Test dict_to_transistor with missing fields (should use defaults)."""
        data = {
            "name": "Minimal_Device",
            "type": "IGBT",
            "manufacturer": "Unknown",
            "v_abs_max": 1000,
            "i_abs_max": 100
            # Missing many fields
        }
        
        transistor = dict_to_transistor(data)
        
        assert transistor.metadata.name == "Minimal_Device"
        assert transistor.metadata.type == "IGBT"
        assert transistor.metadata.manufacturer == "Unknown"
        assert transistor.metadata.housing_type == "Unknown"  # Default
        assert transistor.metadata.author == ""  # Default
        assert transistor.metadata.comment == ""  # Default
        assert transistor.electrical_ratings.v_abs_max == 1000
        assert transistor.electrical_ratings.i_abs_max == 100
        assert transistor.electrical_ratings.i_cont == 0  # Default
        assert transistor.electrical_ratings.t_j_max == 150  # Default
        assert transistor.thermal_properties.r_th_cs == 0  # Default
    
    def test_dict_to_transistor_with_t_c_max_fallback(self):
        """Test dict_to_transistor uses t_c_max when t_j_max is missing."""
        data = {
            "name": "Test_Device",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "v_abs_max": 600,
            "i_abs_max": 30,
            "i_cont": 25,
            "t_c_max": 125,  # Should be used as fallback for t_j_max
            "r_th_cs": 0.5
        }
        
        transistor = dict_to_transistor(data)
        assert transistor.electrical_ratings.t_j_max == 125
    
    def test_transistor_to_dict(self):
        """Test transistor_to_dict conversion."""
        # First create a transistor from flat format
        data = {
            "name": "Test_Transistor",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "housing_type": "TO220",
            "author": "Test Author",
            "comment": "Test device",
            "v_abs_max": 600,
            "i_abs_max": 30,
            "i_cont": 25,
            "t_j_max": 175,
            "r_th_cs": 0.5,
            "housing_area": 0.001,
            "cooling_area": 0.0005
        }
        
        transistor = dict_to_transistor(data)
        result_dict = transistor_to_dict(transistor)
        
        # Check the nested structure
        assert "metadata" in result_dict
        assert "electrical" in result_dict
        assert "thermal" in result_dict
        
        assert result_dict["metadata"]["name"] == "Test_Transistor"
        assert result_dict["metadata"]["type"] == "MOSFET"
        assert result_dict["metadata"]["manufacturer"] == "TestCorp"
        assert result_dict["electrical"]["v_abs_max"] == 600
        assert result_dict["electrical"]["i_abs_max"] == 30
        assert result_dict["thermal"]["r_th_cs"] == 0.5


class TestAPIEndpoints:
    """Test all API endpoints."""
    
    def setup_method(self):
        """Set up for each test method."""
        # Clear the database before each test
        transistors_db.clear()
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Transistor Database API"
        assert data["version"] == "1.0.0"
    
    def test_get_transistors_empty(self):
        """Test getting transistors when database is empty."""
        response = client.get("/api/transistors")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_transistors_with_data(self):
        """Test getting transistors when database has data."""
        # Add a test transistor to the database
        test_data = {
            "metadata": {
                "name": "Test_Device",
                "type": "MOSFET",
                "manufacturer": "TestCorp",
                "housing_type": "TO220",
                "author": "Test",
                "comment": "Test device"
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
        
        transistor = dict_to_transistor(test_data)
        transistors_db["Test_Device"] = transistor
        
        response = client.get("/api/transistors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["metadata"]["name"] == "Test_Device"
    
    def test_get_transistor_by_id_existing(self):
        """Test getting a specific transistor by ID."""
        test_data = {
            "name": "Test_Device",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "housing_type": "TO220",
            "v_abs_max": 600,
            "i_abs_max": 30,
            "i_cont": 25,
            "t_j_max": 175,
            "r_th_cs": 0.5,
            "housing_area": 0.001,
            "cooling_area": 0.0005
        }
        
        transistor = dict_to_transistor(test_data)
        transistors_db["Test_Device"] = transistor
        
        response = client.get("/api/transistors/Test_Device")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "Test_Device"
    
    def test_get_transistor_by_id_not_found(self):
        """Test getting a non-existent transistor."""
        response = client.get("/api/transistors/NonExistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_transistor_success(self):
        """Test creating a new transistor."""
        test_data = {
            "metadata": {
                "name": "New_Device",
                "type": "IGBT",
                "manufacturer": "NewCorp",
                "housing_type": "TO247",
                "author": "Test Author",
                "comment": "New test device"
            },
            "electrical": {
                "v_abs_max": 1200,
                "i_abs_max": 150,
                "i_cont": 120,
                "t_j_max": 175
            },
            "thermal": {
                "r_th_cs": 0.3,
                "housing_area": 0.002,
                "cooling_area": 0.001
            }
        }
        
        response = client.post("/api/transistors", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Transistor created successfully"
        assert "id" in data
        
        # Verify it was added to the database
        assert len(transistors_db) == 1
    
    def test_create_transistor_invalid_data(self):
        """Test creating transistor with minimal/invalid data (should use defaults)."""
        minimal_data = {
            "invalid": "data"  # No valid transistor fields
        }
        
        response = client.post("/api/transistors", json=minimal_data)
        # Current implementation is lenient and accepts this, creating defaults
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Transistor created successfully"
        
        # Verify the transistor was created with default values
        transistor = transistors_db[data["id"]]
        assert transistor.metadata.name == "Unknown"  # Default value
        assert transistor.metadata.type == "Unknown"  # Default value
    
    def test_update_transistor_success(self):
        """Test updating an existing transistor."""
        # First create a transistor
        original_data = {
            "name": "Update_Test",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "v_abs_max": 600,
            "i_abs_max": 30,
            "i_cont": 25,
            "t_j_max": 175,
            "r_th_cs": 0.5
        }
        
        transistor = dict_to_transistor(original_data)
        transistors_db["Update_Test"] = transistor
        
        # Update data
        updated_data = {
            "metadata": {
                "name": "Update_Test",
                "type": "MOSFET",
                "manufacturer": "UpdatedCorp",
                "housing_type": "TO220",
                "author": "Updated Author",
                "comment": "Updated device"
            },
            "electrical": {
                "v_abs_max": 800,
                "i_abs_max": 40,
                "i_cont": 35,
                "t_j_max": 180
            },
            "thermal": {
                "r_th_cs": 0.4,
                "housing_area": 0.001,
                "cooling_area": 0.0005
            }
        }
        
        response = client.put("/api/transistors/Update_Test", json=updated_data)
        assert response.status_code == 200
        assert response.json()["message"] == "Transistor updated successfully"
        
        # Verify the update
        updated_transistor = transistors_db["Update_Test"]
        assert updated_transistor.metadata.manufacturer == "UpdatedCorp"
        assert updated_transistor.electrical_ratings.v_abs_max == 800
    
    def test_update_transistor_not_found(self):
        """Test updating a non-existent transistor."""
        update_data = {
            "metadata": {"name": "NonExistent"},
            "electrical": {"v_abs_max": 600},
            "thermal": {"r_th_cs": 0.5}
        }
        
        response = client.put("/api/transistors/NonExistent", json=update_data)
        assert response.status_code == 404
    
    def test_delete_transistor_success(self):
        """Test deleting an existing transistor."""
        # First create a transistor
        test_data = {
            "name": "Delete_Test",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "v_abs_max": 600,
            "i_abs_max": 30
        }
        
        transistor = dict_to_transistor(test_data)
        transistors_db["Delete_Test"] = transistor
        
        response = client.delete("/api/transistors/Delete_Test")
        assert response.status_code == 200
        assert response.json()["message"] == "Transistor deleted successfully"
        
        # Verify deletion
        assert "Delete_Test" not in transistors_db
    
    def test_delete_transistor_not_found(self):
        """Test deleting a non-existent transistor."""
        response = client.delete("/api/transistors/NonExistent")
        assert response.status_code == 404
    
    def test_upload_transistor_success(self):
        """Test uploading a transistor from JSON file."""
        # Create test JSON data (TDB format)
        test_data = {
            "name": "CREE_C3M0016120K",
            "type": "SiC-MOSFET",
            "manufacturer": "Wolfspeed",
            "housing_type": "TO247",
            "author": "Test Author",
            "comment": "Test CREE device",
            "v_abs_max": 1200,
            "i_abs_max": 250,
            "i_cont": 115,
            "t_j_max": 175,
            "r_th_cs": 0.27,
            "housing_area": 0.000367,
            "cooling_area": 0.00016
        }
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(test_data, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload the file
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("test.json", f, "application/json")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Transistor uploaded successfully"
            assert data["name"] == "CREE_C3M0016120K"
            assert data["manufacturer"] == "Wolfspeed"
            assert data["type"] == "SiC-MOSFET"
            
            # Verify it was added to the database
            assert len(transistors_db) == 1
            
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    def test_upload_transistor_invalid_file_type(self):
        """Test uploading a non-JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("This is not JSON")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            assert "Only JSON files are supported" in response.json()["detail"]
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_transistor_invalid_json(self):
        """Test uploading invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_file.write("{ invalid json")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("invalid.json", f, "application/json")}
                )
            
            assert response.status_code == 400
            assert "Invalid JSON format" in response.json()["detail"]
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_compare_transistors_success(self):
        """Test comparing transistors."""
        # Add two transistors to compare
        data1 = {
            "name": "Device1",
            "type": "MOSFET",
            "manufacturer": "Corp1",
            "v_abs_max": 600,
            "i_abs_max": 30
        }
        
        data2 = {
            "name": "Device2",
            "type": "IGBT",
            "manufacturer": "Corp2",
            "v_abs_max": 1200,
            "i_abs_max": 150
        }
        
        transistors_db["Device1"] = dict_to_transistor(data1)
        transistors_db["Device2"] = dict_to_transistor(data2)
        
        response = client.post("/api/transistors/compare", json=["Device1", "Device2"])
        assert response.status_code == 200
        # The exact response depends on the comparison service implementation
    
    def test_compare_transistors_insufficient_devices(self):
        """Test comparing with less than 2 transistors."""
        data1 = {"name": "Device1", "type": "MOSFET", "manufacturer": "Corp1"}
        transistors_db["Device1"] = dict_to_transistor(data1)
        
        response = client.post("/api/transistors/compare", json=["Device1"])
        assert response.status_code == 400
        assert "At least 2 transistors required" in response.json()["detail"]
    
    def test_compare_transistors_not_found(self):
        """Test comparing with non-existent transistor."""
        response = client.post("/api/transistors/compare", json=["NonExistent1", "NonExistent2"])
        assert response.status_code == 404
    
    def test_validate_transistor(self):
        """Test transistor validation."""
        data = {
            "name": "Validate_Test",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "v_abs_max": 600,
            "i_abs_max": 30
        }
        
        transistors_db["Validate_Test"] = dict_to_transistor(data)
        
        response = client.post("/api/transistors/Validate_Test/validate")
        assert response.status_code == 200
        # The exact response depends on the validation service implementation
    
    def test_export_transistor_json(self):
        """Test exporting transistor as JSON."""
        data = {
            "name": "Export_Test",
            "type": "MOSFET",
            "manufacturer": "TestCorp",
            "v_abs_max": 600,
            "i_abs_max": 30
        }
        
        transistors_db["Export_Test"] = dict_to_transistor(data)
        
        response = client.post("/api/transistors/Export_Test/export/json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_export_transistor_invalid_format(self):
        """Test exporting with invalid format."""
        data = {"name": "Export_Test", "type": "MOSFET"}
        transistors_db["Export_Test"] = dict_to_transistor(data)
        
        response = client.post("/api/transistors/Export_Test/export/invalid")
        assert response.status_code == 400
        assert "Unsupported export format" in response.json()["detail"]


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def setup_method(self):
        """Set up for each test method."""
        transistors_db.clear()
    
    def test_full_transistor_lifecycle(self):
        """Test complete transistor lifecycle: create, read, update, delete."""
        # 1. Create
        create_data = {
            "metadata": {
                "name": "Lifecycle_Test",
                "type": "MOSFET",
                "manufacturer": "TestCorp",
                "housing_type": "TO220",
                "author": "Test Author",
                "comment": "Lifecycle test device"
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
        
        create_response = client.post("/api/transistors", json=create_data)
        assert create_response.status_code == 200
        transistor_id = create_response.json()["id"]
        
        # 2. Read
        read_response = client.get(f"/api/transistors/{transistor_id}")
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data["metadata"]["name"] == "Lifecycle_Test"
        
        # 3. Update
        update_data = create_data.copy()
        update_data["electrical"]["v_abs_max"] = 800
        update_response = client.put(f"/api/transistors/{transistor_id}", json=update_data)
        assert update_response.status_code == 200
        
        # Verify update
        updated_response = client.get(f"/api/transistors/{transistor_id}")
        assert updated_response.json()["electrical"]["v_abs_max"] == 800
        
        # 4. Delete
        delete_response = client.delete(f"/api/transistors/{transistor_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        final_response = client.get(f"/api/transistors/{transistor_id}")
        assert final_response.status_code == 404
    
    def test_upload_and_use_workflow(self):
        """Test uploading a transistor and then using it in other operations."""
        # Upload
        test_data = {
            "name": "Upload_Workflow_Test",
            "type": "SiC-MOSFET",
            "manufacturer": "WorkflowCorp",
            "housing_type": "TO247",
            "v_abs_max": 1200,
            "i_abs_max": 200,
            "i_cont": 150,
            "t_j_max": 175,
            "r_th_cs": 0.25,
            "housing_area": 0.0005,
            "cooling_area": 0.0003
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(test_data, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                upload_response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("workflow_test.json", f, "application/json")}
                )
            
            assert upload_response.status_code == 200
            transistor_id = upload_response.json()["id"]
            
            # Validate
            validate_response = client.post(f"/api/transistors/{transistor_id}/validate")
            assert validate_response.status_code == 200
            
            # Export
            export_response = client.post(f"/api/transistors/{transistor_id}/export/json")
            assert export_response.status_code == 200
            
        finally:
            os.unlink(tmp_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
