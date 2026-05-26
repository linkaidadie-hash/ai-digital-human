const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const http = require('http');

let mainWindow;
let backendProcess = null;

// Find python.exe using where
function findPython() {
  try {
    const result = execSync('where py', { encoding: 'utf8', windowsHide: true });
    const firstLine = result.split('\n')[0].trim();
    if (firstLine && firstLine.toLowerCase().endsWith('py.exe')) return 'py';
    if (firstLine) return firstLine;
  } catch (_) {}
  // Fallback
  try {
    const result2 = execSync('where python', { encoding: 'utf8', windowsHide: true });
    return result2.split('\n')[0].trim();
  } catch (_) {}
  return 'python';
}

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
    // 打包模式下，等待后端就绪后再加载
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const isPackaged = app.isPackaged;
  const basePath = isPackaged
    ? path.join(app.getAppPath(), 'resources')
    : path.join(__dirname, '..');

  const possibleBackendPaths = [
    path.join(basePath, 'backend'),
    path.join(__dirname, '..', 'resources', 'backend'),
    path.join(__dirname, '..', '..', 'backend'),
    path.join(__dirname, '..', 'backend')
  ];

  let backendPath = possibleBackendPaths.find(p => {
    try { require('fs').accessSync(path.join(p, 'main.py')); return true; } catch { return false; }
  }) || possibleBackendPaths[0];

  const mainPython = path.join(backendPath, 'main.py');
  console.log('[Electron] Starting backend from:', backendPath);

  // 查找 FFmpeg
  const possibleFfmpegPaths = [
    path.join(basePath, '..', 'ffmpeg', 'ffmpeg.exe'),
    path.join(__dirname, '..', 'ffmpeg', 'ffmpeg.exe'),
    path.join(__dirname, '..', '..', 'ffmpeg', 'ffmpeg.exe')
  ];

  const ffmpegBundled = possibleFfmpegPaths.find(p => {
    try { require('fs').accessSync(p); return true; } catch { return false; }
  });

  if (ffmpegBundled) {
    console.log('[Electron] FFmpeg bundled at:', ffmpegBundled);
  }

  // Find python
  const pythonCmd = findPython();
  console.log('[Electron] Python command:', pythonCmd);

  const env = { ...process.env };
  env.PYTHONUNBUFFERED = '1';
  if (ffmpegBundled) {
    env.PATH = path.dirname(ffmpegBundled) + path.delimiter + (env.PATH || '');
  }

  backendProcess = spawn(pythonCmd, ['-u', mainPython], {
    cwd: backendPath,
    stdio: 'pipe',
    env
  });

  backendProcess.stdout.on('data', (data) => {
    const msg = data.toString();
    const lines = msg.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed) console.log('[Backend]', trimmed);
    }
    if (msg.includes('[API]')) checkBackendReady();
  });

  backendProcess.stderr.on('data', (data) => {
    console.error('[Backend Error]', data.toString().trim());
  });

  backendProcess.on('close', (code) => {
    console.log('[Backend] Process exited with code:', code);
  });
}

// Poll /ping until we get {ok: true, service: "fastapi-backend"}, then load frontend
let pingInterval = null;
function checkBackendReady() {
  if (pingInterval) return;
  pingInterval = setInterval(() => {
    const req = http.get('http://127.0.0.1:8000/ping', (res) => {
      let body = '';
      res.on('data', chunk => { body += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          if (json.ok === true && json.service === 'fastapi-backend') {
            clearInterval(pingInterval);
            pingInterval = null;
            console.log('\n=== BACKEND_STARTED ===\n');
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
              mainWindow.once('ready-to-show', () => { mainWindow.show(); });
            }
          }
        } catch (_) {}
      });
    });
    req.on('error', () => {});
    req.setTimeout(2000, () => { req.destroy(); });
  }, 1000);
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