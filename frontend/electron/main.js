const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    title: 'AI数字人',
    show: false
  });

  // 开发模式加载 Vite 开发服务器
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  // 优先使用打包在 resources 目录下的 backend
  const isPackaged = app.isPackaged;
  const basePath = isPackaged
    ? path.join(app.getAppPath())
    : path.join(__dirname, '..');

  // 尝试多个可能的 backend 路径
  const possibleBackendPaths = [
    path.join(basePath, 'backend'),
    path.join(__dirname, '..', '..', 'backend'),
    path.join(__dirname, '..', 'backend')
  ];

  let backendPath = possibleBackendPaths.find(p => {
    try { require('fs').accessSync(path.join(p, 'main.py')); return true; } catch { return false; }
  }) || possibleBackendPaths[0];

  const mainPython = path.join(backendPath, 'main.py');

  console.log('[Electron] Starting backend from:', backendPath);

  // 查找 FFmpeg：优先 resources/ffmpeg/ffmpeg.exe，其次系统 PATH
  const possibleFfmpegPaths = [
    path.join(basePath, 'ffmpeg', 'ffmpeg.exe'),
    path.join(__dirname, '..', 'ffmpeg', 'ffmpeg.exe'),
    path.join(__dirname, '..', '..', 'ffmpeg', 'ffmpeg.exe')
  ];

  const ffmpegBundled = possibleFfmpegPaths.find(p => {
    try { require('fs').accessSync(p); return true; } catch { return false; }
  });

  if (ffmpegBundled) {
    console.log('[Electron] FFmpeg bundled at:', ffmpegBundled);
  }

  const env = { ...process.env };
  if (ffmpegBundled) {
    env.PATH = path.dirname(ffmpegBundled) + path.delimiter + (env.PATH || '');
  }

  backendProcess = spawn('python', [mainPython], {
    cwd: backendPath,
    stdio: 'pipe',
    env
  });

  backendProcess.stdout.on('data', (data) => {
    console.log('[Backend]', data.toString().trim());
  });

  backendProcess.stderr.on('data', (data) => {
    console.error('[Backend Error]', data.toString().trim());
  });

  backendProcess.on('close', (code) => {
    console.log('[Backend] Process exited with code:', code);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

// 启动后端服务
app.whenReady().then(() => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC 处理
ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result.filePaths[0] || null;
});

ipcMain.handle('select-file', async (event, filters) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: filters || []
  });
  return result.filePaths[0] || null;
});

ipcMain.handle('open-path', async (event, filePath) => {
  shell.showItemInFolder(filePath);
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});