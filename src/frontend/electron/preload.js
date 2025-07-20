"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
const electronAPI = {
    apiRequest: (endpoint, options) => electron_1.ipcRenderer.invoke('api:request', endpoint, options),
    websocketConnect: (url) => electron_1.ipcRenderer.invoke('websocket:connect', url),
    getAppVersion: () => electron_1.ipcRenderer.invoke('app:version'),
    getPlatform: () => electron_1.ipcRenderer.invoke('app:platform'),
    minimizeWindow: () => electron_1.ipcRenderer.invoke('window:minimize'),
    maximizeWindow: () => electron_1.ipcRenderer.invoke('window:maximize'),
    closeWindow: () => electron_1.ipcRenderer.invoke('window:close')
};
electron_1.contextBridge.exposeInMainWorld('electronAPI', electronAPI);
