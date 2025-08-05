# 🚀 Development Scripts

This directory contains helper scripts to easily run the Transistor Database development environment.

## 📋 Available Scripts

### 🔧 `dev-server.sh` (Linux/macOS)
Main development script that handles everything automatically:

```bash
# Start both backend and frontend
./dev-server.sh

# Start only backend
./dev-server.sh backend

# Start only frontend  
./dev-server.sh frontend

# Install dependencies only
./dev-server.sh install

# Show help
./dev-server.sh help
```

**Features:**
- ✅ Automatically detects and uses UV virtual environment
- ✅ Installs Python dependencies with UV
- ✅ Installs npm dependencies
- ✅ Starts FastAPI backend on port 8002
- ✅ Starts Vue.js frontend on port 5174
- ✅ Runs both servers in parallel with proper cleanup

### 🪟 `dev-server.bat` (Windows)
Windows equivalent with same functionality:

```batch
# Start both servers
dev-server.bat

# Start only backend
dev-server.bat backend

# Start only frontend
dev-server.bat frontend
```

### 🧪 `test-env.sh` (Environment Testing)
Verifies your development environment:

```bash
./test-env.sh
```

**Checks:**
- UV installation and virtual environment
- Python package installation capability
- Node.js and npm versions
- Required project files
- Frontend build process

### 🏭 `production.sh` (Production Build)
Builds and serves production version:

```bash
# Build and serve
./production.sh

# Build only (for deployment)
./production.sh static
```

### ✅ `verify-deployment.sh` (Vercel Preparation)
Verifies Vercel deployment readiness:

```bash
./verify-deployment.sh
```

## 🎯 Quick Start

1. **First-time setup:**
   ```bash
   ./test-env.sh          # Verify environment
   ./dev-server.sh setup  # Install dependencies
   ```

2. **Daily development:**
   ```bash
   ./dev-server.sh        # Start both servers
   ```

3. **Production testing:**
   ```bash
   ./production.sh        # Build and preview
   ```

4. **Deploy to Vercel:**
   ```bash
   ./verify-deployment.sh # Check readiness
   vercel                 # Deploy
   ```

## 📡 Server URLs

When running locally:
- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8002  
- **API Documentation**: http://localhost:8002/docs

## 🔧 Requirements

**For Development:**
- Python 3.8+
- [UV](https://docs.astral.sh/uv/getting-started/installation/) (for Python environment management)
- Node.js 16+
- npm

**Installation Commands:**
```bash
# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js (via package manager)
# Ubuntu/Debian:
sudo apt install nodejs npm

# macOS (via Homebrew):
brew install node

# Or download from: https://nodejs.org/
```

## 🐛 Troubleshooting

### UV Not Found
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Port Already in Use
- Frontend (5174): Stop existing Vite dev server
- Backend (8002): Stop existing FastAPI/uvicorn process

### Virtual Environment Issues
```bash
# Clean and recreate
rm -rf .venv
./dev-server.sh setup
```

### Permission Denied
```bash
# Make scripts executable
chmod +x *.sh
```

## 🌟 Script Features

### Smart Environment Detection
- Automatically finds and creates UV virtual environment
- Detects existing installations to avoid conflicts
- Cross-platform path handling

### Dependency Management
- Installs Python packages with UV for faster, reliable installs
- Handles npm packages with proper error checking
- Verifies all dependencies before starting servers

### Process Management
- Runs backend and frontend in parallel
- Proper cleanup when stopping
- Background process handling with PID tracking

### Error Handling
- Comprehensive error checking at each step
- Helpful error messages with solutions
- Graceful failure with cleanup

### Development Workflow
- One-command setup and start
- Separate commands for backend/frontend only
- Production build testing
- Deployment preparation

## 📁 Directory Structure

```
gui_web/
├── dev-server.sh         # Main development script (Linux/macOS)
├── dev-server.bat        # Main development script (Windows)  
├── test-env.sh          # Environment verification
├── production.sh        # Production build & serve
├── verify-deployment.sh # Vercel deployment check
├── src/                 # Vue.js source code
├── backend/             # FastAPI backend
├── package.json         # Frontend dependencies
├── requirements.txt     # Python dependencies (for Vercel)
└── vercel.json         # Vercel deployment config
```

The scripts automatically handle directory navigation and virtual environment activation, so you can run them from anywhere within the project!
