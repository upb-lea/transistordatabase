#!/bin/bash

# Transistor Database Test Runner
# This script starts the backend server and runs the upload tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8002
FRONTEND_PORT=5173
PROJECT_ROOT="/home/tinix84/ntbees/transistordatabase"
BACKEND_DIR="$PROJECT_ROOT/transistordatabase/gui_web/backend"
FRONTEND_DIR="$PROJECT_ROOT/transistordatabase/gui_web"
TESTS_DIR="$PROJECT_ROOT/transistordatabase/gui_web/tests"
ENV_DIR="$PROJECT_ROOT/transistordatabase-env"

# PID files to track running processes
BACKEND_PID_FILE="/tmp/transistor_backend.pid"
FRONTEND_PID_FILE="/tmp/transistor_frontend.pid"

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔷 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Function to activate virtual environment
activate_env() {
    if [ -f "$ENV_DIR/bin/activate" ]; then
        print_step "Activating virtual environment..."
        source "$ENV_DIR/bin/activate"
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found at $ENV_DIR"
        print_info "Continuing with system Python..."
    fi
}

# Function to install dependencies
install_dependencies() {
    print_step "Installing/checking dependencies..."
    
    # Check if we're in virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        pip install requests fastapi uvicorn python-multipart httpx pytest
    else
        pip3 install --user requests fastapi uvicorn python-multipart httpx pytest
    fi
    
    print_success "Dependencies checked/installed"
}

# Function to start backend server
start_backend() {
    print_step "Starting backend server..."
    
    if check_port $BACKEND_PORT; then
        print_warning "Backend port $BACKEND_PORT is already in use"
        
        # Check if it's our backend
        if curl -s "http://localhost:$BACKEND_PORT/" | grep -q "Transistor Database API"; then
            print_success "Backend is already running"
            return 0
        else
            print_error "Another service is using port $BACKEND_PORT"
            return 1
        fi
    fi
    
    cd "$BACKEND_DIR"
    
    # Start backend in background
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        nohup uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > backend.log 2>&1 &
    else
        nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > backend.log 2>&1 &
    fi
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"
    
    print_info "Backend started with PID: $BACKEND_PID"
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:$BACKEND_PORT/" "Backend"; then
        print_success "Backend server is running on http://localhost:$BACKEND_PORT"
        return 0
    else
        return 1
    fi
}

# Function to start frontend server (optional)
start_frontend() {
    print_step "Starting frontend server..."
    
    if check_port $FRONTEND_PORT; then
        print_warning "Frontend port $FRONTEND_PORT is already in use"
        print_success "Frontend is likely already running"
        return 0
    fi
    
    cd "$FRONTEND_DIR"
    
    # Start frontend in background
    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
    
    print_info "Frontend started with PID: $FRONTEND_PID"
    
    # Wait for frontend to be ready
    if wait_for_service "http://localhost:$FRONTEND_PORT/" "Frontend"; then
        print_success "Frontend server is running on http://localhost:$FRONTEND_PORT"
        return 0
    else
        print_warning "Frontend failed to start, but continuing with tests..."
        return 0  # Don't fail if frontend doesn't start
    fi
}

# Function to run tests
run_tests() {
    print_step "Running upload tests..."
    
    cd "$TESTS_DIR"
    
    # Run the debug upload test
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        python debug_upload.py
    else
        python3 debug_upload.py
    fi
    
    local test_result=$?
    
    if [ $test_result -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed!"
    fi
    
    return $test_result
}

# Function to run pytest tests (if available)
run_pytest() {
    print_step "Running pytest tests..."
    
    cd "$TESTS_DIR"
    
    # Check if pytest is available and test files exist
    if command -v pytest >/dev/null 2>&1 && [ -f "test_main.py" ]; then
        print_info "Running pytest suite..."
        
        if [[ "$VIRTUAL_ENV" != "" ]]; then
            pytest test_main.py test_file_upload.py -v
        else
            python3 -m pytest test_main.py test_file_upload.py -v
        fi
        
        local pytest_result=$?
        
        if [ $pytest_result -eq 0 ]; then
            print_success "Pytest tests passed!"
        else
            print_error "Some pytest tests failed!"
        fi
        
        return $pytest_result
    else
        print_info "Pytest not available or test files not found, skipping..."
        return 0
    fi
}

# Function to cleanup processes
cleanup() {
    print_step "Cleaning up..."
    
    # Kill backend if we started it
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_info "Stopping backend server (PID: $BACKEND_PID)..."
            kill "$BACKEND_PID"
            sleep 2
            # Force kill if still running
            if kill -0 "$BACKEND_PID" 2>/dev/null; then
                kill -9 "$BACKEND_PID"
            fi
        fi
        rm -f "$BACKEND_PID_FILE"
    fi
    
    # Kill frontend if we started it
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_info "Stopping frontend server (PID: $FRONTEND_PID)..."
            kill "$FRONTEND_PID"
            sleep 2
            # Force kill if still running
            if kill -0 "$FRONTEND_PID" 2>/dev/null; then
                kill -9 "$FRONTEND_PID"
            fi
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    print_success "Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-frontend    Skip starting the frontend server"
    echo "  --no-cleanup     Don't cleanup servers after tests"
    echo "  --pytest-only    Run only pytest tests"
    echo "  --debug-only     Run only debug upload tests"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests with frontend"
    echo "  $0 --no-frontend     # Run tests without frontend"
    echo "  $0 --pytest-only     # Run only pytest suite"
}

# Main execution
main() {
    local skip_frontend=false
    local skip_cleanup=false
    local pytest_only=false
    local debug_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-frontend)
                skip_frontend=true
                shift
                ;;
            --no-cleanup)
                skip_cleanup=true
                shift
                ;;
            --pytest-only)
                pytest_only=true
                shift
                ;;
            --debug-only)
                debug_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Set up trap to cleanup on exit
    if [ "$skip_cleanup" = false ]; then
        trap cleanup EXIT INT TERM
    fi
    
    echo -e "${PURPLE}🚀 Transistor Database Test Runner${NC}"
    echo -e "${PURPLE}=====================================${NC}"
    
    # Step 1: Activate environment
    activate_env
    
    # Step 2: Install dependencies
    install_dependencies
    
    # Step 3: Start backend
    if ! start_backend; then
        print_error "Failed to start backend server"
        exit 1
    fi
    
    # Step 4: Start frontend (optional)
    if [ "$skip_frontend" = false ]; then
        start_frontend
    fi
    
    # Step 5: Run tests
    local test_results=0
    
    if [ "$pytest_only" = true ]; then
        run_pytest
        test_results=$?
    elif [ "$debug_only" = true ]; then
        run_tests
        test_results=$?
    else
        # Run both test suites
        run_tests
        local debug_result=$?
        
        run_pytest
        local pytest_result=$?
        
        # Overall result is success only if both pass
        if [ $debug_result -eq 0 ] && [ $pytest_result -eq 0 ]; then
            test_results=0
        else
            test_results=1
        fi
    fi
    
    # Final summary
    echo ""
    echo -e "${PURPLE}=====================================${NC}"
    echo -e "${PURPLE}📊 FINAL SUMMARY${NC}"
    echo -e "${PURPLE}=====================================${NC}"
    
    if [ $test_results -eq 0 ]; then
        print_success "🎉 All tests completed successfully!"
        echo -e "${GREEN}Backend: http://localhost:$BACKEND_PORT${NC}"
        if [ "$skip_frontend" = false ]; then
            echo -e "${GREEN}Frontend: http://localhost:$FRONTEND_PORT${NC}"
        fi
    else
        print_error "❌ Some tests failed. Check the output above."
    fi
    
    if [ "$skip_cleanup" = true ]; then
        print_info "Servers left running (--no-cleanup specified)"
        print_info "To stop manually, kill PIDs in $BACKEND_PID_FILE and $FRONTEND_PID_FILE"
    fi
    
    exit $test_results
}

# Run main function with all arguments
main "$@"
