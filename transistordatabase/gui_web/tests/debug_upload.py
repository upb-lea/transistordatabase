#!/usr/bin/env python3
"""Simple test script to debug the file upload issue."""

import json
import requests
import tempfile
import os
from pathlib import Path

def test_upload_endpoint():
    """Test the upload endpoint directly."""
    # Create test data in CREE format
    cree_data = {
        "name": "CREE_C3M0016120K",
        "type": "SiC-MOSFET",
        "author": "Test Author",
        "technology": None,
        "template_version": None,
        "template_date": None,
        "creation_date": None,
        "last_modified": None,
        "comment": "Test upload",
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
    
    print("🧪 Testing file upload endpoint...")
    print("=" * 50)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        json.dump(cree_data, tmp_file, indent=2)
        tmp_file_path = tmp_file.name
    
    try:
        # Test 1: Check if backend is running
        print("1. Checking if backend is accessible...")
        try:
            response = requests.get("http://localhost:8002/", timeout=5)
            print(f"   ✅ Backend responding: {response.status_code}")
            print(f"   Response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Backend not accessible: {e}")
            return False
        
        # Test 2: Upload the file
        print("\n2. Testing file upload...")
        with open(tmp_file_path, 'rb') as f:
            files = {'file': ('CREE_C3M0016120K.json', f, 'application/json')}
            
            try:
                response = requests.post(
                    "http://localhost:8002/api/transistors/upload",
                    files=files,
                    timeout=10
                )
                
                print(f"   Status Code: {response.status_code}")
                print(f"   Response Headers: {dict(response.headers)}")
                print(f"   Response Text: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("   ✅ Upload successful!")
                    print(f"   Transistor ID: {data.get('id')}")
                    print(f"   Transistor Name: {data.get('name')}")
                    print(f"   Manufacturer: {data.get('manufacturer')}")
                    return True
                else:
                    print("   ❌ Upload failed!")
                    try:
                        error_data = response.json()
                        print(f"   Error detail: {error_data.get('detail')}")
                    except:
                        print(f"   Raw response: {response.text}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Request failed: {e}")
                return False
        
        # Test 3: Verify the transistor was added
        print("\n3. Verifying transistor was added...")
        try:
            response = requests.get("http://localhost:8002/api/transistors", timeout=5)
            if response.status_code == 200:
                transistors = response.json()
                print(f"   Total transistors in database: {len(transistors)}")
                if transistors:
                    for t in transistors:
                        print(f"   - {t['metadata']['name']} ({t['metadata']['manufacturer']})")
                return True
            else:
                print(f"   ❌ Failed to get transistors: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed to verify: {e}")
            return False
            
    finally:
        # Clean up
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

def test_minimal_upload():
    """Test with minimal data."""
    print("\n🔬 Testing minimal data upload...")
    print("=" * 50)
    
    minimal_data = {
        "name": "Minimal_Test",
        "type": "MOSFET", 
        "manufacturer": "TestCorp",
        "v_abs_max": 600,
        "i_abs_max": 30
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        json.dump(minimal_data, tmp_file, indent=2)
        tmp_file_path = tmp_file.name
    
    try:
        with open(tmp_file_path, 'rb') as f:
            files = {'file': ('minimal_test.json', f, 'application/json')}
            
            response = requests.post(
                "http://localhost:8002/api/transistors/upload",
                files=files,
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            return response.status_code == 200
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

if __name__ == "__main__":
    print("🚀 Transistor Database Upload Test")
    print("=" * 60)
    
    success1 = test_upload_endpoint()
    success2 = test_minimal_upload()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"CREE Format Upload: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Minimal Data Upload: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All upload tests passed!")
    else:
        print("\n⚠️  Some upload tests failed. Check the backend logs.")
