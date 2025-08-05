@echo off
REM Transistor Database - Development Server for Windows
REM This script starts both backend and frontend servers

setlocal enabledelayedexpansion

echo 🔌 Transistor Database - Development Setup (Windows)
echo =====================================================

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

echo 📁 Project root: %PROJECT_ROOT%
echo 📁 GUI web dir: %SCRIPT_DIR%

REM Check required tools
echo.
echo 🔍 Checking requirements...

where uv >nul 2>&1
if errorlevel 1 (
    echo ❌ UV not found. Please install UV: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)
echo ✅ UV found

where node >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)
echo ✅ Node.js found

where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ npm not found. Please install npm
    pause
    exit /b 1
)
echo ✅ npm found

REM Setup Python environment
echo.
echo 🐍 Setting up Python environment with UV...

cd /d "%PROJECT_ROOT%"

if not exist ".venv" (
    echo 📦 Creating virtual environment...
    uv venv
) else (
    echo ✅ Virtual environment already exists
)

REM Install backend dependencies
echo.
echo 📦 Installing backend dependencies...
cd /d "%SCRIPT_DIR%backend"

if exist "requirements.txt" (
    echo Installing Python packages with UV...
    uv pip install -r requirements.txt
    echo ✅ Backend dependencies installed
) else (
    echo ⚠️ requirements.txt not found, installing minimal dependencies...
    uv pip install fastapi uvicorn python-multipart
)

REM Install frontend dependencies
echo.
echo 📦 Installing frontend dependencies...
cd /d "%SCRIPT_DIR%"

if exist "package.json" (
    echo Installing npm packages...
    npm install
    echo ✅ Frontend dependencies installed
) else (
    echo ❌ package.json not found
    pause
    exit /b 1
)

REM Check arguments
if "%1"=="backend" goto start_backend
if "%1"=="api" goto start_backend
if "%1"=="frontend" goto start_frontend
if "%1"=="web" goto start_frontend
if "%1"=="ui" goto start_frontend
if "%1"=="install" goto install_only
if "%1"=="setup" goto install_only
if "%1"=="help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help
if not "%1"=="" goto unknown_command

REM Default: start both
echo.
echo 🚀 Starting both backend and frontend...
echo 💡 Tip: Use Ctrl+C to stop servers
echo.

REM Start backend in new window
start "Backend Server" /d "%SCRIPT_DIR%backend" cmd /k "echo 🚀 Starting FastAPI backend... && echo 📍 Backend: http://localhost:8002 && echo 📖 API docs: http://localhost:8002/docs && uv run python main_simple.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo 🚀 Starting Vue.js frontend...
echo 📍 Frontend: http://localhost:5174
npm run dev
goto end

:start_backend
echo.
echo 🚀 Starting backend only...
cd /d "%SCRIPT_DIR%backend"
echo 📍 Backend running at: http://localhost:8002
echo 📖 API docs at: http://localhost:8002/docs
uv run python main_simple.py
goto end

:start_frontend
echo.
echo 🚀 Starting frontend only...
cd /d "%SCRIPT_DIR%"
echo 📍 Frontend running at: http://localhost:5174
npm run dev
goto end

:install_only
echo.
echo ✅ Installation complete!
echo.
echo 🎯 Next steps:
echo   • Run 'dev-server.bat' to start both servers
echo   • Run 'dev-server.bat backend' to start only backend
echo   • Run 'dev-server.bat frontend' to start only frontend
goto end

:show_help
echo.
echo Usage: dev-server.bat [command]
echo.
echo Commands:
echo   (no args)         Start both backend and frontend
echo   backend/api       Start only the FastAPI backend
echo   frontend/web/ui   Start only the Vue.js frontend
echo   install/setup     Install dependencies only
echo   help              Show this help message
echo.
echo URLs:
echo   Frontend:  http://localhost:5174
echo   Backend:   http://localhost:8002
echo   API Docs:  http://localhost:8002/docs
goto end

:unknown_command
echo ❌ Unknown command: %1
echo Run 'dev-server.bat help' for usage information
goto end

:end
pause
