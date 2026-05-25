const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  selectFile: (filters) => ipcRenderer.invoke('select-file', filters),
  openPath: (filePath) => ipcRenderer.invoke('open-path', filePath),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  platform: process.platform
});