import { contextBridge, ipcRenderer } from 'electron';

// Define the API interface
export interface ElectronAPI {
  // Backend API communication
  apiRequest: (endpoint: string, options?: RequestInit) => Promise<any>;
  
  // WebSocket management
  websocketConnect: (url: string) => Promise<{ success: boolean; url: string }>;
  
  // App information
  getAppVersion: () => Promise<string>;
  getPlatform: () => Promise<string>;
  
  // Window controls
  minimizeWindow: () => Promise<void>;
  maximizeWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
const electronAPI: ElectronAPI = {
  apiRequest: (endpoint: string, options?: RequestInit) => 
    ipcRenderer.invoke('api:request', endpoint, options),
    
  websocketConnect: (url: string) => 
    ipcRenderer.invoke('websocket:connect', url),
    
  getAppVersion: () => 
    ipcRenderer.invoke('app:version'),
    
  getPlatform: () => 
    ipcRenderer.invoke('app:platform'),
    
  minimizeWindow: () => 
    ipcRenderer.invoke('window:minimize'),
    
  maximizeWindow: () => 
    ipcRenderer.invoke('window:maximize'),
    
  closeWindow: () => 
    ipcRenderer.invoke('window:close')
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);

// Type declaration for TypeScript
declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}