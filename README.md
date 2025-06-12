# ProKeys

<div align="center">
  <img src="ProKeys.gif" alt="ProKeys Animation" width="120">
  
  **Smart Clipboard Typing for macOS**
  
  A modern, native macOS application that intelligently types your clipboard content with customizable speed and formatting.
  
  [![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)](https://github.com/LakshmanTurlapati/ProKeys)
  [![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://github.com/LakshmanTurlapati/ProKeys)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>

## ✨ Features

- **🚀 Smart Typing**: Automatically types clipboard content with natural timing
- **⚡ Customizable Speed**: Adjustable typing speed from 9 to 999 WPM
- **🎨 Native Design**: Beautiful macOS-native interface with system theme support
- **🌓 Dynamic Theming**: Automatically switches between light and dark modes
- **🔧 Quick Presets**: One-click speed presets for different use cases
- **🔒 Privacy Focused**: Runs completely offline, no data collection
- **📱 System Tray**: Convenient access from the menu bar
- **⌨️ Keyboard Shortcuts**: Easy trigger with ⌘+⇧+V

## 🎯 Use Cases

- **Code Sharing**: Type code snippets with proper formatting
- **Documentation**: Insert text blocks naturally in meetings
- **Presentations**: Demonstrate typing without copy-paste artifacts
- **Content Creation**: Add realistic typing effects to recordings
- **Accessibility**: Helps with repetitive typing tasks

## 📥 Download & Installation

### Download Options

1. **DMG Installer (Recommended)**
   - Download `ProKeys-2.0.0-arm64.dmg` from the [Releases](https://github.com/LakshmanTurlapati/ProKeys/releases) page
   - Double-click the DMG file to mount it
   - Drag ProKeys.app to your Applications folder
   - Launch ProKeys from Applications

2. **ZIP Archive**
   - Download `ProKeys-2.0.0-arm64-mac.zip` from the [Releases](https://github.com/LakshmanTurlapati/ProKeys/releases) page
   - Extract the ZIP file
   - Move ProKeys.app to your Applications folder
   - Launch ProKeys from Applications

### System Requirements

- **macOS**: 10.14 (Mojave) or later
- **Architecture**: Apple Silicon (M1/M2) or Intel processors
- **Accessibility**: Permission required for keyboard monitoring

### First Launch Setup

1. **Open ProKeys** from your Applications folder
2. **Grant Accessibility Permission** when prompted:
   - Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
   - Click the lock icon and enter your password
   - Check the box next to **ProKeys**
3. **Start using** with the default trigger: ⌘+⇧+V

## 🚀 How to Use

1. **Start ProKeys**: Click the "Start ProKeys" button in the app
2. **Copy content**: Use ⌘+C to copy any text or code
3. **Trigger typing**: Press ⌘+⇧+V anywhere to start smart typing
4. **Stop anytime**: Press Escape to cancel typing or stop ProKeys

### Speed Configuration

- **Slider**: Drag to set custom speed (9-999 WPM)
- **Presets**: Quick buttons for common speeds:
  - **30 WPM**: Slow, deliberate typing
  - **60 WPM**: Natural human typing
  - **120 WPM**: Fast typing (default)
  - **200 WPM**: Very fast
  - **400 WPM**: Ultra-fast for large content

### Keyboard Shortcuts

- **⌘+⇧+V**: Trigger clipboard typing
- **⎋ (Escape)**: Stop current typing or exit ProKeys

## 🛠️ Development

### Prerequisites

- Node.js 16+ and npm
- Python 3.7+ (for development only)
- macOS 10.14+

### Building from Source

```bash
# Clone the repository
git clone https://github.com/LakshmanTurlapati/ProKeys.git
cd ProKeys

# Install dependencies
npm install

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pyperclip pynput

# Run in development mode
npm start

# Build for distribution
npm run dist
```

### Architecture

- **Electron Main Process**: Window management and Python process control
- **Electron Renderer**: Web-based UI with HTML/CSS/JavaScript
- **Python Backend**: Keyboard monitoring and typing simulation (`prokeys.py`)
- **IPC Communication**: Secure bridge between UI and Python process

## 🔒 Security & Privacy

- **Local Processing**: All operations happen on your device
- **No Network Access**: No data is sent to external servers
- **Accessibility Only**: Only requires permissions for keyboard monitoring
- **Open Source**: Full source code available for review

## 🐛 Troubleshooting

### Common Issues

**App won't start**
- Check Console.app for error messages
- Ensure macOS version compatibility
- Try restarting your Mac

**Keyboard monitoring not working**
- Verify accessibility permissions in System Preferences
- Remove and re-add ProKeys in accessibility settings
- Restart the app after granting permissions

**Python errors**
- The app includes its own Python runtime
- If issues persist, try rebuilding from source

**Performance issues**
- Lower the typing speed for large content
- Ensure sufficient system resources
- Close other resource-intensive applications

### Getting Help

- **Issues**: Report bugs on [GitHub Issues](https://github.com/LakshmanTurlapati/ProKeys/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/LakshmanTurlapati/ProKeys/discussions)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Lakshman Turlapati**
- GitHub: [@LakshmanTurlapati](https://github.com/LakshmanTurlapati)
- Project: [ProKeys](https://github.com/LakshmanTurlapati/ProKeys)

---

<div align="center">
  Made with ❤️ for the macOS community
</div>