#!/bin/bash

# Transistor Database - Production Server Script
# This script builds and serves the production version

set -e

echo "🏭 Transistor Database - Production Build & Serve"
echo "================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "📁 Working in: $SCRIPT_DIR"

# Build frontend
echo ""
echo -e "${BLUE}🔨 Building frontend for production...${NC}"
cd "$SCRIPT_DIR"

if [ ! -f "package.json" ]; then
    echo "❌ package.json not found"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Build
echo -e "${YELLOW}🔨 Building...${NC}"
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed - dist directory not created"
    exit 1
fi

echo -e "${GREEN}✅ Frontend built successfully${NC}"

# Serve options
if [ "$1" = "serve" ] || [ "$#" -eq 0 ]; then
    echo ""
    echo -e "${BLUE}🚀 Starting production preview server...${NC}"
    echo -e "${YELLOW}📍 Production preview at: http://localhost:4173${NC}"
    npm run preview
    
elif [ "$1" = "static" ]; then
    echo ""
    echo -e "${GREEN}✅ Static files ready in dist/ directory${NC}"
    echo "📁 Contents:"
    ls -la dist/
    echo ""
    echo "💡 You can now:"
    echo "  • Deploy dist/ folder to any web server"
    echo "  • Use 'npm run preview' to test locally"
    echo "  • Deploy to Vercel with 'vercel'"
    
else
    echo ""
    echo "Usage: ./production.sh [command]"
    echo ""
    echo "Commands:"
    echo "  serve     Build and start preview server (default)"
    echo "  static    Build only, show deployment info"
    echo ""
fi
