# ProKeys - Electron Version

A modern, native macOS application for smart clipboard typing built with Electron.

## Features

- Native macOS app with modern UI
- System tray integration
- Real-time status updates
- Configurable typing speed (9-999 WPM)
- No Python installation required for end users
- Runs completely offline

## Development

### Prerequisites

- Node.js 16+ and npm
- Python 3.7+ (for development only)
- macOS 10.14+

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Python dependencies (for development):
   ```bash
   source venv/bin/activate
   pip install pyperclip pynput
   ```

### Running in Development

```bash
npm start
```

### Building the App

```bash
./build-app.sh
```

Or manually:

```bash
npm run dist
```

The built app will be in the `dist` folder.

## Architecture

- **Electron Main Process**: Manages the app lifecycle, system tray, and Python process
- **Electron Renderer**: Web-based UI using HTML/CSS/JavaScript
- **Python Backend**: The original prokeys.py script for keyboard monitoring and typing
- **IPC Communication**: Secure communication between UI and Python process

## Security

The app requires accessibility permissions on macOS to monitor keyboard input and simulate keystrokes. Users will be prompted to grant these permissions on first run.

## Distribution

The built `.app` file can be distributed as-is or packaged in a DMG for easier installation.

## Troubleshooting

1. **App won't start**: Check Console.app for error messages
2. **Keyboard monitoring not working**: Ensure accessibility permissions are granted
3. **Python errors**: The app bundles its own Python runtime, but ensure prokeys.py is included