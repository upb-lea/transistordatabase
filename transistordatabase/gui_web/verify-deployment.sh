#!/bin/bash

# Vercel Deployment Verification Script
# Run this script to verify your deployment setup

echo "🔍 Vercel Deployment Verification"
echo "================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run from gui_web directory."
    exit 1
fi

if [ ! -f "vercel.json" ]; then
    echo "❌ Error: vercel.json not found. Deployment configuration missing."
    exit 1
fi

if [ ! -d "api" ]; then
    echo "❌ Error: api/ directory not found. Serverless functions missing."
    exit 1
fi

echo "✅ Project structure looks good"

# Check dependencies
echo ""
echo "📦 Checking Dependencies..."

if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi

if command -v npm &> /dev/null; then
    echo "✅ npm: $(npm --version)"
else
    echo "❌ npm not found. Please install npm"
    exit 1
fi

if command -v python3 &> /dev/null; then
    echo "✅ Python: $(python3 --version)"
else
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if Vercel CLI is installed
if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLI: $(vercel --version)"
else
    echo "⚠️  Vercel CLI not found. Install with: npm i -g vercel"
fi

echo ""
echo "🔧 Testing Build Process..."

# Test npm install
if npm install; then
    echo "✅ npm install successful"
else
    echo "❌ npm install failed"
    exit 1
fi

# Test build
if npm run build; then
    echo "✅ Build successful"
    echo "✅ Output directory: dist/"
else
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "🎉 Deployment verification complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Run 'vercel' to deploy to Vercel"
echo "2. Or push to GitHub and connect via Vercel dashboard"
echo "3. Set root directory to 'transistordatabase/gui_web' in Vercel"
echo ""
echo "📖 For detailed instructions, see VERCEL_DEPLOYMENT.md"
