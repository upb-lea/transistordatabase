#!/bin/bash

# Quick test script to verify the development environment

set -e

echo "🧪 Transistor Database - Environment Test"
echo "========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📁 Testing from: $SCRIPT_DIR"

# Test 1: Check if UV is installed and working
echo ""
echo "🧪 Test 1: UV Installation"
if command -v uv >/dev/null 2>&1; then
    echo -e "${GREEN}✅ UV is installed: $(uv --version)${NC}"
else
    echo -e "${RED}❌ UV not found${NC}"
    exit 1
fi

# Test 2: Check if virtual environment can be created
echo ""
echo "🧪 Test 2: Virtual Environment"
cd "$PROJECT_ROOT"
if [ -d ".venv" ]; then
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
else
    echo -e "${YELLOW}📦 Creating test virtual environment...${NC}"
    uv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Test 3: Check if Python packages can be installed
echo ""
echo "🧪 Test 3: Python Package Installation"
cd "$SCRIPT_DIR/backend"
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}🔍 Testing pip install...${NC}"
    uv pip install --dry-run -r requirements.txt >/dev/null 2>&1
    echo -e "${GREEN}✅ Python dependencies can be installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, testing with fastapi...${NC}"
    uv pip install --dry-run fastapi >/dev/null 2>&1
    echo -e "${GREEN}✅ Python packages can be installed${NC}"
fi

# Test 4: Check Node.js and npm
echo ""
echo "🧪 Test 4: Node.js Environment"
cd "$SCRIPT_DIR"
if command -v node >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
else
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi

if command -v npm >/dev/null 2>&1; then
    echo -e "${GREEN}✅ npm: $(npm --version)${NC}"
else
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi

# Test 5: Check if npm packages can be installed
echo ""
echo "🧪 Test 5: npm Package Installation"
if [ -f "package.json" ]; then
    echo -e "${YELLOW}🔍 Testing npm install (dry run)...${NC}"
    npm install --dry-run >/dev/null 2>&1
    echo -e "${GREEN}✅ npm dependencies can be installed${NC}"
else
    echo -e "${RED}❌ package.json not found${NC}"
    exit 1
fi

# Test 6: Check required files
echo ""
echo "🧪 Test 6: Required Files"
files_to_check=(
    "package.json"
    "vite.config.js"
    "src/main.js"
    "src/App.vue"
    "backend/main_simple.py"
    "vercel.json"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
    fi
done

# Test 7: Try building the frontend
echo ""
echo "🧪 Test 7: Frontend Build Test"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing npm dependencies for build test...${NC}"
    npm install >/dev/null 2>&1
fi

echo -e "${YELLOW}🔨 Testing build process...${NC}"
if npm run build >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend builds successfully${NC}"
    if [ -d "dist" ]; then
        echo -e "${GREEN}✅ dist/ directory created${NC}"
    fi
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All tests passed!${NC}"
echo ""
echo "🚀 Your environment is ready!"
echo "Run './dev-server.sh' to start the development servers"
