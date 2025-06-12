<div align="center">
  
# ProKeys

[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://github.com/yourusername/prokeys)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/yourusername/prokeys/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

<div align="center">
  <img src="ProKeys.gif" alt="ProKeys demo animation" height="200"width="200" />
</div>

## Installation

Download the DMG above, open it, and drag the **ProKeys** icon into your **Applications** folder. Launch the app and you're ready to roll—no terminal commands or extra setup.

## What is ProKeys?

A minimal utility that re-types clipboard content at adjustable speeds. Set your preferred words-per-minute rate, press `⌘⇧V`, and watch your text appear keystroke by keystroke—perfect for coding, note-taking, or anywhere a regular paste isn't enough.

Inspired by **AutoHotKey** on Windows, ProKeys delivers focused functionality purpose-built for ultra-fast paste on macOS.

## Tech Stack

- **Electron** – Native macOS window, auto-update, and system tray integration
- **Node.js** – Main process orchestration and IPC messaging
- **Python** (`pynput`) – Low-level keyboard event generation for reliable typing emulation
- **HTML/CSS/Vanilla JS** – Minimal interface with clean styling

## Codebase Overview

- **`main.js`** – Electron app initialization, global shortcut registration, and IPC coordination
- **`prokeys.py`** – Keyboard event synthesis using `pynput` for typing automation
- **`renderer.js`** – UI logic and user interaction handling
- **`index.html` & `styles.css`** – Lightweight frontend with minimal styling

Additional files include build scripts, auto-updater configuration, and packaging artifacts.

---

**Created by [Lakshman Turlapati](https://www.audienclature.com)**