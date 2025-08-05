print("Test starting...")

# Test 1: Import main package
try:
    import transistordatabase
    print("✅ transistordatabase package imported")
except Exception as e:
    print(f"❌ Failed to import transistordatabase: {e}")

# Test 2: Import Transistor class
try:
    from transistordatabase import Transistor
    print("✅ Transistor class imported")
except Exception as e:
    print(f"❌ Failed to import Transistor: {e}")

# Test 3: Test master data availability 
import os
master_data_path = "tests/master_data"
if os.path.exists(master_data_path):
    print(f"✅ Master data directory found: {master_data_path}")
    files = os.listdir(master_data_path)
    print(f"   Found {len(files)} files in master data")
else:
    print(f"❌ Master data directory not found: {master_data_path}")

print("✅ Environment setup test completed!")
