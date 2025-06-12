#!/bin/bash

# ProKeys Electron App Build Script

echo "Building ProKeys Electron App..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist node_modules/.cache

# Ensure ProKeys.png exists
if [ ! -f "ProKeys.png" ]; then
    echo "Error: ProKeys.png not found!"
    exit 1
fi

# Ensure prokeys.py exists
if [ ! -f "prokeys.py" ]; then
    echo "Error: prokeys.py not found!"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build for macOS
echo "Building for macOS..."
npm run dist

# Check if build was successful
if [ -d "dist/mac" ] || [ -d "dist/mac-arm64" ]; then
    echo "Build successful!"
    echo "App location: dist/"
    
    # List the built files
    ls -la dist/
else
    echo "Build failed!"
    exit 1
fi

echo "Done!"