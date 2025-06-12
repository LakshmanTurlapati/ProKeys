const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, shell, systemPreferences } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');

// Initialize store for settings
const store = new Store();

let mainWindow;
let tray;
let pythonProcess = null;

// Default configuration
const defaultConfig = {
  typing_speed_wpm: 120,
  delay: 0.01,
  trigger_key: "cmd+shift+v"
};

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 400,
    height: 400, // Start square
    resizable: false,
    titleBarStyle: 'hiddenInset',
    icon: path.join(__dirname, 'ProKeys.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');
  
  // Open DevTools for debugging (remove in production)
  // mainWindow.webContents.openDevTools();

  // Allow window to close normally
  mainWindow.on('close', (event) => {
    // Only prevent close if we want to minimize to tray
    // For now, let it close normally
    app.quit();
  });
}

function createTray() {
  const icon = nativeImage.createFromPath(path.join(__dirname, 'ProKeys.png'));
  tray = new Tray(icon.resize({ width: 16, height: 16 }));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show ProKeys',
      click: () => {
        mainWindow.show();
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip('ProKeys');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

// IPC handlers
ipcMain.handle('get-config', () => {
  return store.get('config', defaultConfig);
});

ipcMain.handle('save-config', (event, config) => {
  store.set('config', config);
  return true;
});

ipcMain.handle('check-accessibility-permission', () => {
  const hasPermission = systemPreferences.isTrustedAccessibilityClient(false);
  return { hasPermission };
});

ipcMain.handle('request-accessibility-permission', async () => {
  // This will prompt the user to grant accessibility permission
  const hasPermission = systemPreferences.isTrustedAccessibilityClient(true);
  
  if (!hasPermission) {
    // Wait a moment and check again - sometimes there's a delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    const recheckPermission = systemPreferences.isTrustedAccessibilityClient(false);
    return { hasPermission: recheckPermission };
  }
  
  return { hasPermission };
});

ipcMain.handle('start-prokeys', async () => {
  if (pythonProcess) {
    return { success: false, error: 'ProKeys is already running' };
  }

  // Check accessibility permission first
  const hasPermission = systemPreferences.isTrustedAccessibilityClient(false);
  if (!hasPermission) {
    return { 
      success: false, 
      error: 'Accessibility permission required',
      needsPermission: true 
    };
  }

  try {
    const fs = require('fs');
    
    // Simplified Python executable detection
    let pythonExecutable = 'python3';
    
    // Check if venv python exists
    const venvPython = path.join(__dirname, 'venv', 'bin', 'python');
    if (fs.existsSync(venvPython)) {
      pythonExecutable = venvPython;
    }
    
    // Check if prokeys.py exists
    const scriptPath = path.join(__dirname, 'prokeys.py');
    if (!fs.existsSync(scriptPath)) {
      return { success: false, error: 'ProKeys script not found' };
    }
    
    const config = store.get('config', defaultConfig);
    pythonProcess = spawn(pythonExecutable, [
      scriptPath,
      '--trigger-key', config.trigger_key,
      '--delay', config.delay.toString()
    ]);

    pythonProcess.stdout.on('data', (data) => {
      console.log(`ProKeys: ${data}`);
      mainWindow.webContents.send('prokeys-output', data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`ProKeys Error: ${data}`);
      mainWindow.webContents.send('prokeys-error', data.toString());
    });

    pythonProcess.on('close', (code) => {
      console.log(`ProKeys exited with code ${code}`);
      pythonProcess = null;
      mainWindow.webContents.send('prokeys-stopped');
    });

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stop-prokeys', () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
    return { success: true };
  }
  return { success: false, error: 'ProKeys is not running' };
});

ipcMain.handle('get-prokeys-status', () => {
  return { running: pythonProcess !== null };
});

ipcMain.handle('open-external', async (event, url) => {
  await shell.openExternal(url);
});

ipcMain.handle('expand-window', () => {
  if (mainWindow) {
    mainWindow.setSize(400, 580, true); // Animate to smaller expanded size
  }
});

// App event handlers
app.whenReady().then(() => {
  createWindow();
  createTray();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  // Clean up Python process
  if (pythonProcess) {
    pythonProcess.kill();
  }
});