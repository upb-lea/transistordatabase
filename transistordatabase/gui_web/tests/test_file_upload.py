"""
Test cases specifically for file upload functionality.

This module focuses on testing the upload endpoint with real TDB files.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient  # noqa: E402
from main import app, transistors_db  # noqa: E402

client = TestClient(app)


class TestFileUpload:
    """Test file upload functionality with various scenarios."""
    
    def setup_method(self):
        """Set up for each test method."""
        transistors_db.clear()
    
    def test_upload_cree_format(self):
        """Test uploading a file in CREE TDB format."""
        # Real CREE data structure based on the actual file
        cree_data = {
            "name": "CREE_C3M0016120K",
            "type": "SiC-MOSFET",
            "author": "Nikolas Förster",
            "technology": None,
            "template_version": None,
            "template_date": None,
            "creation_date": None,
            "last_modified": None,
            "comment": "",
            "datasheet_hyperlink": "https://www.wolfspeed.com/downloads/dl/file/id/1483/product/0/c3m0016120k.pdf",
            "datasheet_date": "2019-04",
            "datasheet_version": "unknown",
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
            "r_th_cs": 0,
            "r_th_switch_cs": 0,
            "r_th_diode_cs": 0,
            "v_abs_max": 1200,
            "i_abs_max": 250,
            "i_cont": 115,
            # Add some sample curve data
            "c_oss": [
                {
                    "t_j": 25,
                    "graph_v_c": [
                        [0.0, 1.6077, 4.4678, 7.074, 10.289],
                        [2.3e-10, 2.2e-10, 2.1e-10, 2.0e-10, 1.9e-10]
                    ]
                }
            ]
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(cree_data, tmp_file, indent=2)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("CREE_C3M0016120K.json", f, "application/json")}
                )
            
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Transistor uploaded successfully"
            assert data["name"] == "CREE_C3M0016120K"
            assert data["manufacturer"] == "Wolfspeed"
            assert data["type"] == "SiC-MOSFET"
            
            # Verify it was added to the database
            assert len(transistors_db) == 1
            transistor_id = data["id"]
            assert transistor_id in transistors_db
            
            # Verify the data was parsed correctly
            transistor = transistors_db[transistor_id]
            assert transistor.metadata.name == "CREE_C3M0016120K"
            assert transistor.metadata.manufacturer == "Wolfspeed"
            assert transistor.electrical_ratings.v_abs_max == 1200
            assert transistor.electrical_ratings.i_abs_max == 250
            assert transistor.electrical_ratings.i_cont == 115
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_minimal_format(self):
        """Test uploading with minimal required fields."""
        minimal_data = {
            "name": "Minimal_Device",
            "type": "MOSFET",
            "manufacturer": "MinimalCorp",
            "v_abs_max": 600,
            "i_abs_max": 30
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(minimal_data, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("minimal.json", f, "application/json")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Minimal_Device"
            
            # Verify defaults were applied
            transistor = transistors_db[data["id"]]
            assert transistor.electrical_ratings.t_j_max == 150  # Default value
            assert transistor.thermal_properties.r_th_cs == 0  # Default value
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_with_t_c_max_fallback(self):
        """Test that t_c_max is used when t_j_max is missing."""
        data_with_tc = {
            "name": "TC_Fallback_Device",
            "type": "IGBT",
            "manufacturer": "TestCorp",
            "v_abs_max": 1200,
            "i_abs_max": 150,
            "t_c_max": 125  # Should be used as t_j_max
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(data_with_tc, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("tc_fallback.json", f, "application/json")}
                )
            
            assert response.status_code == 200
            transistor = transistors_db[response.json()["id"]]
            assert transistor.electrical_ratings.t_j_max == 125
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_large_file(self):
        """Test uploading a larger file with extensive data."""
        large_data = {
            "name": "Large_Dataset_Device",
            "type": "SiC-MOSFET",
            "manufacturer": "LargeCorp",
            "housing_type": "TO247",
            "v_abs_max": 1700,
            "i_abs_max": 300,
            "i_cont": 250,
            "t_j_max": 200,
            "r_th_cs": 0.2,
            "housing_area": 0.0008,
            "cooling_area": 0.0004,
            # Add extensive curve data
            "channel": [
                {
                    "t_j": 25,
                    "v_g": 15,
                    "graph_v_i": [
                        list(range(0, 100, 1)),  # 100 voltage points
                        list(range(0, 1000, 10))  # 100 current points
                    ]
                },
                {
                    "t_j": 175,
                    "v_g": 15,
                    "graph_v_i": [
                        list(range(0, 100, 1)),
                        list(range(0, 800, 8))
                    ]
                }
            ],
            "switch": {
                "t_j": 25,
                "graph_r_v": [
                    list(range(0, 50, 1)),
                    [0.001 + i*0.0001 for i in range(50)]
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(large_data, tmp_file, indent=2)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("large_device.json", f, "application/json")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Large_Dataset_Device"
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_error_handling(self):
        """Test various error conditions."""
        # Test 1: Invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_file.write("{ invalid json content")
            invalid_json_path = tmp_file.name
        
        try:
            with open(invalid_json_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("invalid.json", f, "application/json")}
                )
            
            assert response.status_code == 400
            assert "Invalid JSON format" in response.json()["detail"]
            
        finally:
            os.unlink(invalid_json_path)
        
        # Test 2: Non-JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("This is a text file")
            txt_file_path = tmp_file.name
        
        try:
            with open(txt_file_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("text.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            assert "Only JSON files are supported" in response.json()["detail"]
            
        finally:
            os.unlink(txt_file_path)
        
        # Test 3: Empty JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump({}, tmp_file)
            empty_json_path = tmp_file.name
        
        try:
            with open(empty_json_path, 'rb') as f:
                response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("empty.json", f, "application/json")}
                )
            
            # Should still work with defaults
            assert response.status_code == 200
            
        finally:
            os.unlink(empty_json_path)
    
    def test_upload_duplicate_handling(self):
        """Test uploading the same device twice."""
        device_data = {
            "name": "Duplicate_Test",
            "type": "MOSFET",
            "manufacturer": "DupCorp",
            "v_abs_max": 600,
            "i_abs_max": 30
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(device_data, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload first time
            with open(tmp_file_path, 'rb') as f:
                response1 = client.post(
                    "/api/transistors/upload",
                    files={"file": ("duplicate1.json", f, "application/json")}
                )
            
            assert response1.status_code == 200
            assert len(transistors_db) == 1
            
            # Upload second time (should overwrite)
            with open(tmp_file_path, 'rb') as f:
                response2 = client.post(
                    "/api/transistors/upload",
                    files={"file": ("duplicate2.json", f, "application/json")}
                )
            
            assert response2.status_code == 200
            assert len(transistors_db) == 1  # Still only one entry
            
        finally:
            os.unlink(tmp_file_path)


class TestFileUploadIntegration:
    """Integration tests for file upload with other operations."""
    
    def setup_method(self):
        """Set up for each test method."""
        transistors_db.clear()
    
    def test_upload_then_operations(self):
        """Test uploading a file and then performing various operations."""
        # Upload a device
        device_data = {
            "name": "Integration_Test_Device",
            "type": "SiC-MOSFET",
            "manufacturer": "IntegrationCorp",
            "housing_type": "TO247",
            "v_abs_max": 1200,
            "i_abs_max": 200,
            "i_cont": 180,
            "t_j_max": 175,
            "r_th_cs": 0.3,
            "housing_area": 0.001,
            "cooling_area": 0.0005
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(device_data, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            # 1. Upload
            with open(tmp_file_path, 'rb') as f:
                upload_response = client.post(
                    "/api/transistors/upload",
                    files={"file": ("integration_test.json", f, "application/json")}
                )
            
            assert upload_response.status_code == 200
            device_id = upload_response.json()["id"]
            
            # 2. Retrieve the uploaded device
            get_response = client.get(f"/api/transistors/{device_id}")
            assert get_response.status_code == 200
            retrieved_data = get_response.json()
            assert retrieved_data["metadata"]["name"] == "Integration_Test_Device"
            
            # 3. Update the device
            update_data = retrieved_data
            update_data["electrical"]["v_abs_max"] = 1500
            update_response = client.put(f"/api/transistors/{device_id}", json=update_data)
            assert update_response.status_code == 200
            
            # 4. Validate the device
            validate_response = client.post(f"/api/transistors/{device_id}/validate")
            assert validate_response.status_code == 200
            
            # 5. Export the device
            export_response = client.post(f"/api/transistors/{device_id}/export/json")
            assert export_response.status_code == 200
            
        finally:
            os.unlink(tmp_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
