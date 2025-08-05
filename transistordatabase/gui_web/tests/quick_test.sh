#!/bin/bash

# Quick Test Runner - Simplified version
# This script provides a minimal setup to run the upload tests

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Quick Transistor Database Test${NC}"
echo "=================================="

# Step 1: Activate environment
echo -e "${BLUE}📦 Activating environment...${NC}"
if [ -f "../../../transistordatabase-env/bin/activate" ]; then
    source ../../../transistordatabase-env/bin/activate
    echo -e "${GREEN}✅ Environment activated${NC}"
else
    echo -e "${RED}⚠️  Virtual environment not found, using system Python${NC}"
fi

# Step 2: Install required dependencies
echo -e "${BLUE}📋 Installing dependencies...${NC}"
pip install requests fastapi uvicorn python-multipart httpx
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 3: Start backend in background
echo -e "${BLUE}🔧 Starting backend server...${NC}"
cd ../backend

# Kill any existing processes on port 8002
if lsof -ti:8002 >/dev/null 2>&1; then
    echo "Killing existing process on port 8002..."
    kill -9 $(lsof -ti:8002) 2>/dev/null || true
    sleep 2
fi

# Start backend
nohup uvicorn main:app --host 0.0.0.0 --port 8002 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Step 4: Wait for backend to start
echo -e "${BLUE}⏳ Waiting for backend to start...${NC}"
for i in {1..15}; do
    if curl -s http://localhost:8002/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Step 5: Run tests
echo -e "${BLUE}🧪 Running tests...${NC}"
cd ../tests
python debug_upload.py

TEST_RESULT=$?

# Step 6: Cleanup
echo -e "${BLUE}🧹 Cleaning up...${NC}"
if kill -0 $BACKEND_PID 2>/dev/null; then
    kill $BACKEND_PID
    echo "Backend stopped"
fi

# Final result
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 Tests completed successfully!${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
fi

exit $TEST_RESULT
