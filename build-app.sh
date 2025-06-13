#!/bin/bash

# ProKeys Electron App Complete Build Script
# This script sets up everything needed to build ProKeys from scratch

set -e  # Exit on any error

echo "🚀 ProKeys Electron App - Complete Build Script"
echo "================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Node.js installation
echo "📋 Checking system requirements..."
if ! command_exists node; then
    echo "❌ Error: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ Error: npm is not installed!"
    echo "Please install npm (usually comes with Node.js)"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Check Python installation (for the Python backend)
if ! command_exists python3; then
    echo "⚠️  Warning: python3 not found. ProKeys needs Python for backend functionality."
else
    echo "✅ Python version: $(python3 --version)"
fi

# Verify required files exist
echo ""
echo "📁 Checking required files..."
required_files=("ProKeys.png" "prokeys.py" "package.json" "main.js" "index.html")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Required file '$file' not found!"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf dist node_modules/.cache

# Install Node.js dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "Installing fresh dependencies..."
    npm install
else
    echo "Dependencies already installed, checking for updates..."
    npm ci
fi

# Set up Python environment if needed
echo ""
echo "🐍 Setting up Python environment..."
if [ -d "venv_portable" ]; then
    echo "✅ Portable Python environment already exists"
    echo "Skipping dependency update to preserve working environment..."
    echo "(If you need to update dependencies, delete venv_portable and re-run)"
else
    echo "📦 Creating portable Python environment..."
    if ! command_exists python3; then
        echo "❌ Error: python3 is required to create portable environment!"
        echo "Please install Python 3 from https://python.org/"
        exit 1
    fi
    
    echo "Creating virtual environment..."
    # Use Python 3.12 if available for better pynput compatibility
    if command_exists python3.12; then
        echo "Using Python 3.12 for better pynput compatibility..."
        python3.12 -m venv venv_portable
    else
        echo "Python 3.12 not found, using system python3..."
        python3 -m venv venv_portable
    fi
    
    echo "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        ./venv_portable/bin/pip install --upgrade pip
        ./venv_portable/bin/pip install -r requirements.txt
        echo "✅ Python environment created and dependencies installed"
    else
        echo "⚠️  requirements.txt not found, installing basic dependencies..."
        ./venv_portable/bin/pip install --upgrade pip pyperclip pynput
        echo "✅ Python environment created with basic dependencies"
    fi
fi

# Build for macOS
echo ""
echo "🔨 Building ProKeys for macOS..."
npm run dist

# Check if build was successful
echo ""
if [ -d "dist/mac" ] || [ -d "dist/mac-arm64" ]; then
    echo "🎉 Build successful!"
    echo ""
    echo "📁 Built files:"
    ls -la dist/
    
    # Find the DMG file
    dmg_file=$(find dist -name "*.dmg" | head -1)
    if [ -n "$dmg_file" ]; then
        echo ""
        echo "💿 DMG file created: $dmg_file"
        echo "   Size: $(du -h "$dmg_file" | cut -f1)"
    fi
    
    echo ""
    echo "⚠️  IMPORTANT: Security Notice for Users"
    echo "========================================"
    echo "This app is NOT signed with an Apple Developer certificate."
    echo "When users download and try to run it, macOS will show a warning."
    echo ""
    echo "📋 Instructions for users:"
    echo "1. Download the DMG file"
    echo "2. Open the DMG and drag ProKeys to Applications"
    echo "3. When opening ProKeys for the first time:"
    echo "   • macOS will show: 'ProKeys cannot be opened because it is from an unidentified developer'"
    echo "   • Right-click on ProKeys in Applications"
    echo "   • Select 'Open' from the context menu"
    echo "   • Click 'Open' in the dialog that appears"
    echo "4. Grant accessibility permissions when prompted"
    echo ""
    echo "💡 This only needs to be done once. After that, ProKeys will open normally."
    echo ""
    echo "🔒 To avoid this in the future, consider getting an Apple Developer certificate (\$99/year)"
    
else
    echo "❌ Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi

echo ""
echo "✅ Done! Your ProKeys app is ready for distribution."