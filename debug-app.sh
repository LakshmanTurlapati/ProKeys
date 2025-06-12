#!/bin/bash

# Debug script for ProKeys production app
echo "=== ProKeys Debug Launcher ==="

# Set environment variables for debugging
export ELECTRON_ENABLE_LOGGING=1
export ELECTRON_LOG_ASAR_READS=1

# Find the app
APP_PATH="./dist/mac-arm64/ProKeys.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found at: $APP_PATH"
    echo "Please run 'npm run build' first"
    exit 1
fi

echo "📱 App found at: $APP_PATH"
echo "🔍 Starting with remote debugging on port 8315"
echo "💡 Open Chrome and go to: chrome://inspect/#devices"
echo "🗂️  Log file location: ~/Library/Logs/ProKeys/"
echo ""

# Run the app with debugging enabled
"$APP_PATH/Contents/MacOS/ProKeys" --remote-debugging-port=8315 --enable-logging