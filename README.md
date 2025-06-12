<h1 align="center" style="color:#ff6b35; font-weight: 800;">ProKeys</h1>

<p align="center">
  <img src="ProKeys.gif" alt="ProKeys demo animation" height="200" />
  <br/>
  <a href="ProKeys-2.0.0-arm64.dmg">Download the latest macOS build (.dmg)</a>
</p>

**Install in one step:** Download the DMG above, open it, and drag the **ProKeys** icon into your **Applications** folder. Launch the app and you're ready to roll—no terminal commands or extra setup.

**What is ProKeys?** It's a tiny utility that re-types whatever is on your clipboard at blazing speed. Pick a words-per-minute rate, press <kbd>⌘⇧V</kbd>, and watch your text appear keystroke by keystroke—perfect for coding, note-taking, or anywhere a regular paste isn't enough.

Inspired by **AutoHotKey** on Windows, ProKeys is a focused subset of that power—purpose-built for ultra-fast paste on macOS.

### Tech Stack

• **Electron** – native macOS window, auto-update, and system tray integration
• **Node.js** – orchestrates the main process and IPC messaging
• **Python** (`pynput`) – generates low-level keyboard events for ultra-reliable type emulation
• **HTML / CSS / Vanilla JS** – minimal interface styled with the signature orange accent

### High-level overview of the codebase

• **`main.js`** – boots the Electron app, registers the global shortcut, and streams IPC between the UI and Python backend.
• **`prokeys.py`** – synthesises keyboard events with `pynput`, doing the heavy lifting outside Electron.
• **`renderer.js`** – handles UI logic for the in-app controls and wires user actions back to the main process.
• **`index.html` & `styles.css`** – lightweight front-end styled with the signature orange accent.

Everything else—build scripts, auto-updater config, and packaging artefacts—keeps shipping smooth.

---

#### by [Lakshman Turlapati](https://www.audienclature.com)