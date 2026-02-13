#!/usr/bin/env python3
"""
Test runner for the transistor database web application.

This script runs all tests and provides a summary of results.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests and return the result."""
    test_dir = Path(__file__).parent
    
    print("🧪 Running Transistor Database Web Application Tests")
    print("=" * 60)
    
    # Test commands to run
    test_commands = [
        {
            "name": "Main API Functions",
            "cmd": ["python", "-m", "pytest", "test_main.py::TestMainFunctions", "-v"]
        },
        {
            "name": "API Endpoints", 
            "cmd": ["python", "-m", "pytest", "test_main.py::TestAPIEndpoints", "-v"]
        },
        {
            "name": "File Upload Functionality",
            "cmd": ["python", "-m", "pytest", "test_file_upload.py::TestFileUpload", "-v"]
        },
        {
            "name": "Integration Tests",
            "cmd": ["python", "-m", "pytest", "test_main.py::TestIntegration", "-v"]
        },
        {
            "name": "File Upload Integration",
            "cmd": ["python", "-m", "pytest", "test_file_upload.py::TestFileUploadIntegration", "-v"]
        }
    ]
    
    results = []
    
    for test_group in test_commands:
        print(f"\n📋 Running {test_group['name']}...")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                test_group["cmd"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ {test_group['name']}: PASSED")
                results.append(True)
            else:
                print(f"❌ {test_group['name']}: FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                results.append(False)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_group['name']}: TIMEOUT")
            results.append(False)
        except Exception as e:
            print(f"💥 {test_group['name']}: ERROR - {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, test_group in enumerate(test_commands):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"{test_group['name']:<30} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} test groups passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

def run_specific_test():
    """Run a specific test for debugging."""
    print("🔍 Running specific test for debugging...")
    
    # Test the file upload functionality specifically
    cmd = [
        "python", "-m", "pytest", 
        "test_file_upload.py::TestFileUpload::test_upload_cree_format", 
        "-v", "-s"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ["pytest", "fastapi", "httpx"]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed")
    return True

if __name__ == "__main__":
    print("🚀 Transistor Database Test Suite")
    print("=" * 60)
    
    if not check_dependencies():
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        exit_code = run_specific_test()
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
