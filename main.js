const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, shell, systemPreferences } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');
const log = require('electron-log');

// Configure electron-log
log.transports.file.level = 'debug';
log.transports.console.level = 'debug';
log.info('=== ProKeys Starting ===');
log.info(`App version: ${app.getVersion()}`);
log.info(`Electron version: ${process.versions.electron}`);
log.info(`Node version: ${process.versions.node}`);
log.info(`Platform: ${process.platform}`);
log.info(`App packaged: ${app.isPackaged}`);

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
  
  // Open DevTools for debugging (disabled for production)
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
  
  updateTrayMenu();
  
  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

function updateTrayMenu() {
  if (!tray) return;
  
  const config = store.get('config', defaultConfig);
  const isRunning = pythonProcess !== null;
  
  const speedPresets = [
    { label: '100 WPM', speed: 100 },
    { label: '250 WPM', speed: 250 },
    { label: '500 WPM', speed: 500 },
    { label: '1000 WPM', speed: 1000 },
    { label: '2000 WPM', speed: 2000 }
  ];
  
  const speedMenuItems = speedPresets.map(preset => ({
    label: preset.label,
    type: 'radio',
    checked: config.typing_speed_wpm === preset.speed,
    click: () => {
      updateSpeedFromTray(preset.speed);
    }
  }));
  
  speedMenuItems.push(
    { type: 'separator' },
    {
      label: 'Custom Speed...',
      click: () => {
        mainWindow.show();
      }
    }
  );
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: `Status: ${isRunning ? 'Running' : 'Stopped'}`,
      enabled: false
    },
    {
      label: isRunning ? 'Stop ProKeys' : 'Start ProKeys',
      click: () => {
        toggleProKeysFromTray();
      }
    },
    { type: 'separator' },
    {
      label: `Speed: ${config.typing_speed_wpm} WPM`,
      submenu: speedMenuItems
    },
    { type: 'separator' },
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
  
  tray.setToolTip(`ProKeys - ${isRunning ? 'Running' : 'Stopped'} - ${config.typing_speed_wpm} WPM`);
  tray.setContextMenu(contextMenu);
}

// Tray helper functions
async function toggleProKeysFromTray() {
  try {
    if (pythonProcess) {
      const result = await stopProKeys();
      if (result.success) {
        updateTrayMenu();
        // Notify main window if it's open
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('prokeys-stopped');
        }
      }
    } else {
      const result = await startProKeys();
      if (result.success) {
        updateTrayMenu();
        // Notify main window if it's open
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('prokeys-started');
        }
      }
    }
  } catch (error) {
    log.error('Tray toggle error:', error);
  }
}

function updateSpeedFromTray(newSpeed) {
  try {
    const config = store.get('config', defaultConfig);
    config.typing_speed_wpm = newSpeed;
    config.delay = wpmToDelay(newSpeed);
    
    store.set('config', config);
    updateTrayMenu();
    
    // Notify main window if it's open
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('config-updated', config);
    }
    
    log.info(`Speed updated from tray: ${newSpeed} WPM`);
  } catch (error) {
    log.error('Tray speed update error:', error);
  }
}

function wpmToDelay(wpm) {
  // Convert WPM to delay between keystrokes (same logic as in Python)
  const baseDelay = 60.0 / (wpm * 5);
  
  if (wpm < 60) {
    return baseDelay * 1.2;
  } else if (wpm < 120) {
    return baseDelay * 1.3;
  } else if (wpm < 200) {
    return baseDelay * 1.4;
  } else {
    return baseDelay * 1.5;
  }
}

// Extract start/stop logic into separate functions for reuse
async function startProKeys() {
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
    
    // Python executable detection with proper development vs production handling
    let pythonExecutable = 'python3';
    let scriptPath = null;
    
    // Detect if we're in development or production
    const isDev = !app.isPackaged;
    
    log.info(`=== Python Environment Detection ===`);
    log.info(`Running in ${isDev ? 'development' : 'production'} mode`);
    log.info(`__dirname: ${__dirname}`);
    log.info(`process.resourcesPath: ${process.resourcesPath}`);
    log.info(`app.getAppPath(): ${app.getAppPath()}`);
    
    // Define base paths based on environment
    let basePaths = [];
    
    if (isDev) {
      // Development: use current directory
      basePaths = [__dirname];
    } else {
      // Production: Python venv is in extraResources
      basePaths = [
        process.resourcesPath, // extraResources are here
        path.join(process.resourcesPath, '..'), // fallback
      ];
    }
    
    log.info(`Base paths to search: ${basePaths.join(', ')}`);
    
    // Find the correct paths
    for (const basePath of basePaths) {
      const venvPython = path.join(basePath, 'venv_portable', 'bin', 'python');
      const testScriptPath = isDev 
        ? path.join(basePath, 'prokeys.py')  // Dev: script in same dir
        : path.join(basePath, 'prokeys.py'); // Prod: script in extraResources
      
      log.info(`Checking Python: ${venvPython}`);
      log.info(`Checking script: ${testScriptPath}`);
      log.info(`Python exists: ${fs.existsSync(venvPython)}`);
      log.info(`Script exists: ${fs.existsSync(testScriptPath)}`);
      
      if (fs.existsSync(venvPython) && fs.existsSync(testScriptPath)) {
        pythonExecutable = venvPython;
        scriptPath = testScriptPath;
        log.info(`✅ Found Python environment at: ${venvPython}`);
        log.info(`✅ Found ProKeys script at: ${scriptPath}`);
        break;
      } else {
        log.warn(`❌ Missing files in ${basePath}`);
      }
    }
    
    // Fallback: if venv not found, look for script only with system Python
    if (!scriptPath) {
      log.warn('No portable Python found, trying system Python fallback');
      const fallbackScriptPath = isDev 
        ? path.join(__dirname, 'prokeys.py')
        : path.join(process.resourcesPath, 'prokeys.py');
        
      log.info(`Checking fallback script: ${fallbackScriptPath}`);
      log.info(`Fallback script exists: ${fs.existsSync(fallbackScriptPath)}`);
        
      if (fs.existsSync(fallbackScriptPath)) {
        scriptPath = fallbackScriptPath;
        pythonExecutable = 'python3'; // Use system Python
        log.warn(`⚠️  Found ProKeys script at: ${scriptPath} (using system Python)`);
      }
    }
    
    if (!scriptPath) {
      const error = 'ProKeys script not found in any expected location';
      log.error(error);
      return { success: false, error };
    }
    
    log.info('=== Python Environment Validation ===');
    
    // Test if the Python executable can actually run and import required modules
    try {
      const { execSync } = require('child_process');
      
      log.info(`Testing Python executable: ${pythonExecutable}`);
      
      // First test if Python works
      const versionResult = execSync(`"${pythonExecutable}" --version`, { timeout: 5000, encoding: 'utf8' });
      log.info(`Python version: ${versionResult.trim()}`);
      
      // Test if required modules can be imported
      log.info('Testing Python dependencies...');
      const testCommand = `"${pythonExecutable}" -c "import pyperclip, pynput; print('Dependencies OK')"`;
      const result = execSync(testCommand, { timeout: 10000, encoding: 'utf8' });
      log.info(`Dependency test result: ${result.trim()}`);
      
      if (!result.includes('Dependencies OK')) {
        throw new Error('Required Python modules not available');
      }
      
      log.info('✅ Python environment validation successful');
      
    } catch (error) {
      log.error(`❌ Python validation failed: ${error.message}`);
      log.error(`Error details: ${error.toString()}`);
      
      if (pythonExecutable !== 'python3') {
        log.warn('Bundled Python failed, attempting system Python fallback...');
        pythonExecutable = 'python3';
        try {
          const versionResult = execSync(`${pythonExecutable} --version`, { timeout: 5000, encoding: 'utf8' });
          log.info(`System Python version: ${versionResult.trim()}`);
          
          // Test system Python dependencies
          const testCommand = `${pythonExecutable} -c "import pyperclip, pynput; print('Dependencies OK')"`;
          const result = execSync(testCommand, { timeout: 10000, encoding: 'utf8' });
          log.info(`System Python dependency test: ${result.trim()}`);
          
          if (!result.includes('Dependencies OK')) {
            const error = 'Required Python modules (pyperclip, pynput) not available in system Python. Please install them with: pip3 install pyperclip pynput';
            log.error(error);
            return { success: false, error };
          }
          
          log.info('✅ System Python fallback successful');
          
        } catch (fallbackError) {
          const error = 'Neither bundled nor system Python is available or has required dependencies';
          log.error(`❌ ${error}`);
          log.error(`Fallback error: ${fallbackError.message}`);
          return { success: false, error };
        }
      } else {
        const error = 'Python is not available or missing required dependencies (pyperclip, pynput)';
        log.error(error);
        return { success: false, error };
      }
    }
    
    const config = store.get('config', defaultConfig);
    
    log.info('=== Starting Python Process ===');
    log.info(`Python executable: ${pythonExecutable}`);
    log.info(`Script path: ${scriptPath}`);
    log.info(`Config: ${JSON.stringify(config)}`);
    
    const spawnArgs = [
      scriptPath,
      '--trigger-key', config.trigger_key,
      '--delay', config.delay.toString()
    ];
    
    // Windows mode is always disabled for macOS
    // Backend still supports --windows-mode flag for advanced CLI users
    
    // Add debug flag for troubleshooting (can be enabled via config later)
    if (config.debug) {
      spawnArgs.push('--debug');
    }
    log.info(`Spawn arguments: ${JSON.stringify(spawnArgs)}`);
    
    try {
      pythonProcess = spawn(pythonExecutable, spawnArgs, {
        stdio: ['ignore', 'pipe', 'pipe'], // Explicitly configure stdio
        env: process.env // Pass environment variables
      });
      
      log.info(`Python process spawned with PID: ${pythonProcess.pid}`);

      pythonProcess.stdout.on('data', (data) => {
        const output = data.toString();
        log.info(`ProKeys stdout: ${output.trim()}`);
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('prokeys-output', output);
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        const error = data.toString();
        log.error(`ProKeys stderr: ${error.trim()}`);
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('prokeys-error', error);
        }
      });

      pythonProcess.on('close', (code) => {
        log.info(`ProKeys process exited with code ${code}`);
        pythonProcess = null;
        updateTrayMenu(); // Update tray when process stops
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('prokeys-stopped');
        }
      });
      
      pythonProcess.on('error', (error) => {
        log.error(`Failed to start Python process: ${error.message}`);
        pythonProcess = null;
        updateTrayMenu(); // Update tray on error
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('prokeys-error', `Process spawn error: ${error.message}`);
        }
        return { success: false, error: `Failed to start Python process: ${error.message}` };
      });
      
      // Give the process a moment to start
      setTimeout(() => {
        if (pythonProcess && pythonProcess.pid) {
          log.info('✅ Python process appears to have started successfully');
          updateTrayMenu(); // Update tray when process starts
        } else {
          log.error('❌ Python process failed to start properly');
        }
      }, 1000);
      
    } catch (spawnError) {
      log.error(`Spawn error: ${spawnError.message}`);
      return { success: false, error: `Failed to spawn Python process: ${spawnError.message}` };
    }

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function stopProKeys() {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
    updateTrayMenu(); // Update tray when stopped
    return { success: true };
  }
  return { success: false, error: 'ProKeys is not running' };
}

// IPC handlers
ipcMain.handle('get-config', () => {
  return store.get('config', defaultConfig);
});

ipcMain.handle('save-config', (event, config) => {
  store.set('config', config);
  updateTrayMenu(); // Update tray menu when config changes
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
  const result = await startProKeys();
  if (result.success) {
    updateTrayMenu(); // Update tray menu after successful start
  }
  return result;
});

ipcMain.handle('stop-prokeys', async () => {
  const result = await stopProKeys();
  if (result.success) {
    updateTrayMenu(); // Update tray menu after successful stop
  }
  return result;
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