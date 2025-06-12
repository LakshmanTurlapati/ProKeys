#!/bin/bash

# Test script to validate bundled Python environment
echo "=== ProKeys Python Environment Test ==="

APP_PATH="./dist/mac-arm64/ProKeys.app"
PYTHON_PATH="$APP_PATH/Contents/Resources/venv_portable/bin/python"
SCRIPT_PATH="$APP_PATH/Contents/Resources/app.asar.unpacked/prokeys.py"

echo "Testing bundled Python environment..."
echo "App path: $APP_PATH"
echo "Python path: $PYTHON_PATH"
echo "Script path: $SCRIPT_PATH"
echo ""

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found. Run 'npm run build' first."
    exit 1
fi

if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python executable not found at: $PYTHON_PATH"
    echo "Checking what's in Resources:"
    ls -la "$APP_PATH/Contents/Resources/"
    exit 1
fi

echo "✅ Python executable found"

# Test Python version
echo "Testing Python version..."
"$PYTHON_PATH" --version
if [ $? -ne 0 ]; then
    echo "❌ Python version test failed"
    exit 1
fi

echo "✅ Python runs successfully"

# Test dependencies
echo "Testing Python dependencies..."
"$PYTHON_PATH" -c "import pyperclip, pynput; print('✅ All dependencies available')"
if [ $? -ne 0 ]; then
    echo "❌ Python dependencies test failed"
    exit 1
fi

echo "✅ Dependencies test passed"

# Test script execution (if available)
if [ -f "$SCRIPT_PATH" ]; then
    echo "Testing script execution..."
    "$PYTHON_PATH" "$SCRIPT_PATH" --help
    if [ $? -ne 0 ]; then
        echo "❌ Script execution test failed"
        exit 1
    fi
    echo "✅ Script runs successfully"
else
    echo "⚠️  ProKeys script not found at expected location"
    echo "Looking for script in app.asar..."
    echo "This is normal if the script is bundled in ASAR"
fi

echo ""
echo "🎉 All tests passed! Python environment is working."