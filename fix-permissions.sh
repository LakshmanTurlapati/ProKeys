#!/bin/bash

# Fix Python executable permissions after Electron build
echo "Fixing Python executable permissions..."

# Find the app bundle
APP_PATH="dist/mac-arm64/ProKeys.app"

if [ -d "$APP_PATH" ]; then
    # Fix permissions for the bundled Python executable
    PYTHON_EXEC="$APP_PATH/Contents/Resources/app/venv/bin/python"
    
    if [ -f "$PYTHON_EXEC" ]; then
        echo "Found Python executable at: $PYTHON_EXEC"
        chmod +x "$PYTHON_EXEC"
        echo "Fixed Python executable permissions"
    else
        echo "Python executable not found at expected location"
    fi
    
    # Also fix permissions for any other executables in venv/bin
    VENV_BIN="$APP_PATH/Contents/Resources/app/venv/bin"
    if [ -d "$VENV_BIN" ]; then
        echo "Fixing permissions for all venv executables..."
        chmod +x "$VENV_BIN"/*
        echo "Fixed venv executable permissions"
    fi
else
    echo "App bundle not found at: $APP_PATH"
fi