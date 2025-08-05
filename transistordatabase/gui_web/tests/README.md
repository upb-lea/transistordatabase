# Transistor Database Test Suite

This directory contains test scripts and test cases for the Transistor Database Web Application.

## 🚀 Quick Start

### Option 1: Quick Test (Recommended)
```bash
./quick_test.sh
```

### Option 2: Full Test Suite
```bash
./run_tests.sh
```

## 📋 Test Scripts

### `quick_test.sh` - Simple Test Runner
- **Purpose**: Quick validation of upload functionality
- **Features**:
  - Automatically starts/stops backend server
  - Runs the debug upload tests
  - Minimal setup and cleanup
  - Perfect for quick validation

**Usage:**
```bash
./quick_test.sh
```

### `run_tests.sh` - Comprehensive Test Runner
- **Purpose**: Full test suite with all features
- **Features**:
  - Starts backend and frontend servers
  - Runs both debug tests and pytest suite
  - Comprehensive error handling
  - Detailed logging and cleanup

**Usage:**
```bash
# Run all tests
./run_tests.sh

# Run without frontend
./run_tests.sh --no-frontend

# Run only pytest tests
./run_tests.sh --pytest-only

# Run only debug tests
./run_tests.sh --debug-only

# Keep servers running after tests
./run_tests.sh --no-cleanup

# Show help
./run_tests.sh --help
```

## 🧪 Test Files

### `debug_upload.py` - Upload Test Script
- Tests file upload functionality with real data
- Validates CREE transistor format
- Tests minimal data format
- Provides detailed error reporting

### `test_main.py` - Unit Tests
- Tests all API endpoints
- Tests utility functions (`dict_to_transistor`, `transistor_to_dict`)
- Tests error handling
- Integration tests

### `test_file_upload.py` - File Upload Tests
- Specialized tests for file upload scenarios
- Tests various file formats and edge cases
- Tests error conditions
- Integration with other API operations

### `conftest.py` - Test Configuration
- Pytest fixtures for test data
- Sample transistor data in various formats
- Test utilities and helpers

## 🔧 Manual Testing

If you prefer to test manually:

1. **Start Backend:**
   ```bash
   cd ../backend
   python main.py
   ```

2. **Run Tests:**
   ```bash
   python debug_upload.py
   ```

3. **Run Pytest:**
   ```bash
   pytest test_main.py -v
   ```

## 📊 Test Coverage

The test suite covers:

- ✅ **API Endpoints**: All REST API endpoints
- ✅ **File Upload**: JSON file upload with TDB format
- ✅ **Data Conversion**: Flat to nested format conversion
- ✅ **Error Handling**: Invalid data, missing fields, network errors
- ✅ **Integration**: End-to-end workflows
- ✅ **Edge Cases**: Minimal data, large files, duplicates

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port is in use
lsof -i :8002

# Kill existing processes
kill -9 $(lsof -ti:8002)
```

### Tests Fail with Connection Error
- Ensure backend is running on port 8002
- Check firewall settings
- Verify virtual environment is activated

### Import Errors
```bash
# Install missing dependencies
pip install requests fastapi uvicorn python-multipart httpx pytest
```

### Permission Denied
```bash
# Make scripts executable
chmod +x *.sh
```

## 📝 Test Results

Successful test output should show:
- ✅ Backend responding
- ✅ File upload successful
- ✅ Transistor data parsed correctly
- ✅ Data stored in database
- ✅ All verification checks passed

## 🔗 Related Files

- `../backend/main.py` - FastAPI backend server
- `../src/` - Vue.js frontend components
- `../../examples/` - Sample transistor data files
- `../../database/` - Transistor database files
