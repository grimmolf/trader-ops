import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AppState {
  isInitialized: boolean
  isConnected: boolean
  version: string
  platform: string
  lastUpdate: Date | null
}

export const useAppStore = defineStore('app', () => {
  // State
  const isInitialized = ref(false)
  const isConnected = ref(false)
  const version = ref('')
  const platform = ref('')
  const lastUpdate = ref<Date | null>(null)
  const error = ref<string | null>(null)

  // Getters
  const appInfo = computed(() => ({
    version: version.value,
    platform: platform.value,
    isInitialized: isInitialized.value,
    isConnected: isConnected.value
  }))

  const isReady = computed(() => 
    isInitialized.value && isConnected.value
  )

  // Actions
  async function initialize() {
    try {
      console.log('Initializing app...')
      
      // Get app info from Electron
      if (window.electronAPI) {
        version.value = await window.electronAPI.getAppVersion()
        platform.value = await window.electronAPI.getPlatform()
      }

      // Test backend connection
      await testBackendConnection()
      
      isInitialized.value = true
      lastUpdate.value = new Date()
      error.value = null
      
      console.log('App initialized successfully')
    } catch (err) {
      console.error('Failed to initialize app:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    }
  }

  async function testBackendConnection() {
    try {
      console.log('Testing backend connection...')
      
      const response = await window.electronAPI?.apiRequest('/health')
      
      if (response?.status === 'ok') {
        isConnected.value = true
        console.log('Backend connection successful')
      } else {
        throw new Error('Backend health check failed')
      }
    } catch (err) {
      console.warn('Backend connection failed (this is expected in development):', err)
      isConnected.value = false
      // Don't throw error in development when backend isn't running
      if (process.env.NODE_ENV === 'development') {
        console.log('Continuing in development mode without backend')
      } else {
        throw err
      }
    }
  }

  function setError(errorMessage: string) {
    error.value = errorMessage
  }

  function clearError() {
    error.value = null
  }

  function updateConnectionStatus(connected: boolean) {
    isConnected.value = connected
    lastUpdate.value = new Date()
  }

  return {
    // State
    isInitialized,
    isConnected,
    version,
    platform,
    lastUpdate,
    error,
    
    // Getters
    appInfo,
    isReady,
    
    // Actions
    initialize,
    testBackendConnection,
    setError,
    clearError,
    updateConnectionStatus
  }
})