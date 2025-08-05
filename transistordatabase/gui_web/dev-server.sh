#!/bin/bash

# Transistor Database - Development Server Startup Script
# This script starts both backend and frontend servers for local development

set -e  # Exit on any error

echo "🔌 Transistor Database - Development Setup"
echo "=========================================="

# Get the script directory (gui_web folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 GUI web dir: $SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to find Python executable in UV venv
find_python_in_venv() {
    local venv_path="$1"
    if [ -f "$venv_path/bin/python" ]; then
        echo "$venv_path/bin/python"
    elif [ -f "$venv_path/Scripts/python.exe" ]; then
        echo "$venv_path/Scripts/python.exe"
    else
        echo ""
    fi
}

# Check required tools
echo ""
echo "🔍 Checking requirements..."

if ! command_exists uv; then
    echo -e "${RED}❌ UV not found. Please install UV: https://docs.astral.sh/uv/getting-started/installation/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ UV found: $(uv --version)${NC}"

if ! command_exists node; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

if ! command_exists npm; then
    echo -e "${RED}❌ npm not found. Please install npm${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm found: $(npm --version)${NC}"

# Setup Python virtual environment with UV
echo ""
echo "🐍 Setting up Python environment with UV..."

cd "$PROJECT_ROOT"

# Check if venv already exists
VENV_PATH="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    uv venv
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Find Python executable
PYTHON_EXEC=$(find_python_in_venv "$VENV_PATH")
if [ -z "$PYTHON_EXEC" ]; then
    echo -e "${RED}❌ Could not find Python in virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python executable: $PYTHON_EXEC${NC}"

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
cd "$SCRIPT_DIR/backend"

if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing Python packages with UV...${NC}"
    uv pip install -r requirements.txt
    echo -e "${GREEN}✅ Backend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, installing minimal dependencies...${NC}"
    uv pip install fastapi uvicorn python-multipart
fi

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd "$SCRIPT_DIR"

if [ -f "package.json" ]; then
    echo -e "${YELLOW}Installing npm packages...${NC}"
    npm install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${RED}❌ package.json not found in gui_web directory${NC}"
    exit 1
fi

# Function to start backend
start_backend() {
    echo -e "${BLUE}🚀 Starting FastAPI backend...${NC}"
    cd "$SCRIPT_DIR/backend"
    
    # Check which backend file to use
    if [ -f "main_simple.py" ]; then
        BACKEND_FILE="main_simple.py"
    elif [ -f "main.py" ]; then
        BACKEND_FILE="main.py"
    else
        echo -e "${RED}❌ No backend file found (main_simple.py or main.py)${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📍 Backend running at: http://localhost:8002${NC}"
    echo -e "${YELLOW}📖 API docs at: http://localhost:8002/docs${NC}"
    
    # Use UV to run Python with the virtual environment
    uv run python "$BACKEND_FILE"
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}🚀 Starting Vue.js frontend...${NC}"
    cd "$SCRIPT_DIR"
    
    echo -e "${YELLOW}📍 Frontend running at: http://localhost:5174${NC}"
    
    npm run dev
}

# Check if we should run both or just one
if [ "$#" -eq 0 ]; then
    # No arguments - run both in parallel
    echo ""
    echo "🚀 Starting both backend and frontend..."
    echo -e "${YELLOW}💡 Tip: Use Ctrl+C to stop both servers${NC}"
    echo ""
    
    # Start backend in background
    start_backend &
    BACKEND_PID=$!
    
    # Wait a moment for backend to start
    sleep 3
    
    # Start frontend in foreground
    start_frontend
    
    # When frontend stops, kill backend too
    kill $BACKEND_PID 2>/dev/null || true
    
elif [ "$1" = "backend" ] || [ "$1" = "api" ]; then
    # Run only backend
    echo ""
    echo "🚀 Starting backend only..."
    start_backend
    
elif [ "$1" = "frontend" ] || [ "$1" = "web" ] || [ "$1" = "ui" ]; then
    # Run only frontend
    echo ""
    echo "🚀 Starting frontend only..."
    start_frontend
    
elif [ "$1" = "install" ] || [ "$1" = "setup" ]; then
    # Just run installation
    echo ""
    echo -e "${GREEN}✅ Installation complete!${NC}"
    echo ""
    echo "🎯 Next steps:"
    echo "  • Run './dev-server.sh' to start both servers"
    echo "  • Run './dev-server.sh backend' to start only backend"
    echo "  • Run './dev-server.sh frontend' to start only frontend"
    
elif [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo ""
    echo "Usage: ./dev-server.sh [command]"
    echo ""
    echo "Commands:"
    echo "  (no args)         Start both backend and frontend"
    echo "  backend|api       Start only the FastAPI backend"
    echo "  frontend|web|ui   Start only the Vue.js frontend"
    echo "  install|setup     Install dependencies only"
    echo "  help              Show this help message"
    echo ""
    echo "URLs:"
    echo "  Frontend:  http://localhost:5174"
    echo "  Backend:   http://localhost:8002"
    echo "  API Docs:  http://localhost:8002/docs"
    
else
    echo -e "${RED}❌ Unknown command: $1${NC}"
    echo "Run './dev-server.sh help' for usage information"
    exit 1
fi
