const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  startProKeys: () => ipcRenderer.invoke('start-prokeys'),
  stopProKeys: () => ipcRenderer.invoke('stop-prokeys'),
  getProKeysStatus: () => ipcRenderer.invoke('get-prokeys-status'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  expandWindow: () => ipcRenderer.invoke('expand-window'),
  checkAccessibilityPermission: () => ipcRenderer.invoke('check-accessibility-permission'),
  requestAccessibilityPermission: () => ipcRenderer.invoke('request-accessibility-permission'),
  
  // Listen for events from main process
  onProKeysOutput: (callback) => {
    ipcRenderer.on('prokeys-output', (event, data) => callback(data));
  },
  onProKeysError: (callback) => {
    ipcRenderer.on('prokeys-error', (event, data) => callback(data));
  },
  onProKeysStopped: (callback) => {
    ipcRenderer.on('prokeys-stopped', () => callback());
  }
});