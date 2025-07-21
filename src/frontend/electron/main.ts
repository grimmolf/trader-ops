import { app, BrowserWindow, ipcMain, Menu } from 'electron';
import * as path from 'path';
import { URL } from 'url';

const isDevelopment = process.env.NODE_ENV !== 'production';

// Configuration for webserver-first architecture
interface AppConfig {
  uiUrl: string;
  apiUrl: string;
  wsUrl: string;
  headless: boolean;
}

function loadConfig(): AppConfig {
  // Check for headless mode
  const headless = process.argv.includes('--headless');
  
  // Determine UI URL based on environment and configuration
  let uiUrl: string;
  
  if (process.env.UI_URL) {
    // Explicit override from environment
    uiUrl = process.env.UI_URL;
  } else if (isDevelopment) {
    // Development: Use Vite dev server
    uiUrl = 'http://localhost:5173';
  } else {
    // Production: Use FastAPI web server
    uiUrl = process.env.WEB_SERVER_URL || 'http://localhost:8000';
  }
  
  return {
    uiUrl,
    apiUrl: process.env.API_URL || 'http://localhost:8000',
    wsUrl: process.env.WS_URL || 'ws://localhost:8000',
    headless
  };
}

const config = loadConfig();

let mainWindow: BrowserWindow | null;

function createWindow(): void {
    // Skip window creation in headless mode
    if (config.headless) {
        console.log('Running in headless mode - no window will be created');
        console.log(`UI available at: ${config.uiUrl}`);
        console.log(`API available at: ${config.apiUrl}`);
        return;
    }

    mainWindow = new BrowserWindow({
        width: 1920,
        height: 1080,
        minWidth: 1200,
        minHeight: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            webSecurity: true
        },
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
        frame: process.platform !== 'darwin',
        show: false,
        icon: process.platform === 'linux' ? path.join(__dirname, '../renderer/assets/icon.png') : undefined
    });

    // Load the UI from configured URL
    console.log(`Loading UI from: ${config.uiUrl}`);
    mainWindow.loadURL(config.uiUrl);

    // Handle navigation to ensure we stay within our app
    mainWindow.webContents.on('will-navigate', (event, url) => {
        const urlObj = new URL(url);
        const configUrlObj = new URL(config.uiUrl);
        
        // Allow navigation within the same origin
        if (urlObj.origin !== configUrlObj.origin) {
            event.preventDefault();
            require('electron').shell.openExternal(url);
        }
    });

    mainWindow.once('ready-to-show', () => {
        if (mainWindow) {
            mainWindow.show();
            if (isDevelopment) {
                mainWindow.webContents.openDevTools();
            }
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        require('electron').shell.openExternal(url);
        return { action: 'deny' };
    });
}

// IPC handlers for backend communication
ipcMain.handle('api:request', async (event, endpoint: string, options?: RequestInit) => {
    try {
        const response = await fetch(`${config.apiUrl}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
});

// Add configuration access for renderer process
ipcMain.handle('app:config', () => {
    return {
        uiUrl: config.uiUrl,
        apiUrl: config.apiUrl,
        wsUrl: config.wsUrl,
        headless: config.headless,
        isDevelopment
    };
});

ipcMain.handle('websocket:connect', async (event, url: string) => {
    // WebSocket connections will be handled in the renderer process
    // This is just for validation and connection state management
    try {
        const wsUrl = new URL(url);
        return { success: true, url: wsUrl.toString() };
    } catch (error) {
        console.error('Invalid WebSocket URL:', error);
        throw error;
    }
});

ipcMain.handle('app:version', () => {
    return app.getVersion();
});

ipcMain.handle('app:platform', () => {
    return process.platform;
});

ipcMain.handle('window:minimize', () => {
    if (mainWindow) {
        mainWindow.minimize();
    }
});

ipcMain.handle('window:maximize', () => {
    if (mainWindow) {
        if (mainWindow.isMaximized()) {
            mainWindow.unmaximize();
        } else {
            mainWindow.maximize();
        }
    }
});

ipcMain.handle('window:close', () => {
    if (mainWindow) {
        mainWindow.close();
    }
});

// App event handlers
app.whenReady().then(() => {
    createWindow();

    // Create application menu
    if (process.platform === 'darwin') {
        const template: Electron.MenuItemConstructorOptions[] = [
            {
                label: app.getName(),
                submenu: [
                    { role: 'about' },
                    { type: 'separator' },
                    { role: 'services' },
                    { type: 'separator' },
                    { role: 'hide' },
                    { role: 'hideOthers' },
                    { role: 'unhide' },
                    { type: 'separator' },
                    { role: 'quit' }
                ]
            },
            {
                label: 'File',
                submenu: [
                    { role: 'close' }
                ]
            },
            {
                label: 'Edit',
                submenu: [
                    { role: 'undo' },
                    { role: 'redo' },
                    { type: 'separator' },
                    { role: 'cut' },
                    { role: 'copy' },
                    { role: 'paste' }
                ]
            },
            {
                label: 'View',
                submenu: [
                    { role: 'reload' },
                    { role: 'forceReload' },
                    { role: 'toggleDevTools' },
                    { type: 'separator' },
                    { role: 'resetZoom' },
                    { role: 'zoomIn' },
                    { role: 'zoomOut' },
                    { type: 'separator' },
                    { role: 'togglefullscreen' }
                ]
            },
            {
                label: 'Window',
                submenu: [
                    { role: 'minimize' },
                    { role: 'zoom' },
                    { type: 'separator' },
                    { role: 'front' }
                ]
            }
        ];

        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    // Cleanup code here if needed
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
    contents.setWindowOpenHandler(({ url }) => {
        require('electron').shell.openExternal(url);
        return { action: 'deny' };
    });
});