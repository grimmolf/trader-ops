import { app, BrowserWindow, ipcMain, Menu } from 'electron';
import * as path from 'path';
import { URL } from 'url';

const isDevelopment = process.env.NODE_ENV !== 'production';

let mainWindow: BrowserWindow | null;

function createWindow(): void {
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

    // Load the frontend
    if (isDevelopment) {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../renderer/dist/index.html'));
    }

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
        const baseUrl = process.env.BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}${endpoint}`, {
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