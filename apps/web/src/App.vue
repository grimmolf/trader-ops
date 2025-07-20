<template>
  <div id="app" class="trader-terminal-app">
    <!-- Top Navigation Bar -->
    <nav class="top-nav">
      <div class="nav-brand">
        <h1>TraderTerminal</h1>
        <span class="deployment-badge" :class="deploymentMode">{{ deploymentModeText }}</span>
      </div>
      
      <div class="nav-status">
        <div class="connection-status" :class="{ connected: isConnected }">
          <span class="status-dot"></span>
          {{ isConnected ? 'Connected' : 'Disconnected' }}
        </div>
        
        <div class="market-status" :class="{ open: marketOpen }">
          {{ marketOpen ? 'Market Open' : 'Market Closed' }}
        </div>
      </div>
    </nav>

    <!-- Main Application Router View -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Global Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <div class="loading-text">{{ loadingMessage }}</div>
      </div>
    </div>

    <!-- Global Error Display -->
    <div v-if="globalError" class="error-overlay">
      <div class="error-content">
        <h3>Connection Error</h3>
        <p>{{ globalError }}</p>
        <button @click="retryConnection" class="retry-button">Retry</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

// Global app state
const isLoading = ref(false)
const loadingMessage = ref('Initializing...')
const globalError = ref<string | null>(null)
const isConnected = ref(false)
const marketOpen = ref(false)

// Deployment mode detection
const deploymentMode = computed(() => {
  const mode = import.meta.env.VITE_DEPLOYMENT_MODE
  if (mode) return mode
  
  // Auto-detect based on context
  if (window.location.protocol === 'file:') return 'electron'
  if (window.navigator.userAgent.includes('TraderTerminal')) return 'tauri'
  return 'web'
})

const deploymentModeText = computed(() => {
  switch (deploymentMode.value) {
    case 'electron': return 'Desktop'
    case 'tauri': return 'Desktop'
    case 'web': return 'Web'
    default: return 'Unknown'
  }
})

const router = useRouter()

// Connection management
async function initializeApp() {
  isLoading.value = true
  loadingMessage.value = 'Connecting to backend...'
  
  try {
    // Test backend connectivity
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080'
    const response = await fetch(`${apiUrl}/health`)
    
    if (response.ok) {
      isConnected.value = true
      
      // Check market status
      const marketResponse = await fetch(`${apiUrl}/api/market/status`)
      if (marketResponse.ok) {
        const marketData = await marketResponse.json()
        marketOpen.value = marketData.isOpen
      }
      
      globalError.value = null
    } else {
      throw new Error(`Backend health check failed: ${response.status}`)
    }
  } catch (error) {
    console.error('Failed to connect to backend:', error)
    globalError.value = `Failed to connect to backend: ${error.message}`
    isConnected.value = false
  } finally {
    isLoading.value = false
  }
}

async function retryConnection() {
  globalError.value = null
  await initializeApp()
}

// Lifecycle
onMounted(async () => {
  console.log('🚀 TraderTerminal Web App mounted')
  console.log('📊 Deployment mode:', deploymentMode.value)
  
  await initializeApp()
  
  // Set up periodic health checks
  const healthCheckInterval = setInterval(async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080'
      const response = await fetch(`${apiUrl}/health`)
      isConnected.value = response.ok
      
      if (!response.ok && !globalError.value) {
        globalError.value = 'Lost connection to backend'
      } else if (response.ok && globalError.value) {
        globalError.value = null
      }
    } catch (error) {
      isConnected.value = false
      if (!globalError.value) {
        globalError.value = 'Lost connection to backend'
      }
    }
  }, 5000) // Check every 5 seconds
  
  onUnmounted(() => {
    clearInterval(healthCheckInterval)
  })
})
</script>

<style scoped>
.trader-terminal-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--background-color);
  color: var(--text-primary);
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background-color: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-brand h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--primary-color);
}

.deployment-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.deployment-badge.web {
  background-color: #dbeafe;
  color: #1e40af;
}

.deployment-badge.electron,
.deployment-badge.tauri {
  background-color: #f3e8ff;
  color: #7c3aed;
}

.nav-status {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  background-color: #fef2f2;
  color: #dc2626;
  font-size: 0.875rem;
  font-weight: 500;
}

.connection-status.connected {
  background-color: #f0fdf4;
  color: #16a34a;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
}

.market-status {
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  background-color: #fef3c7;
  color: #d97706;
  font-size: 0.875rem;
  font-weight: 500;
}

.market-status.open {
  background-color: #dcfce7;
  color: #16a34a;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

.loading-overlay,
.error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content,
.error-content {
  background-color: var(--surface-color);
  padding: 2rem;
  border-radius: 0.5rem;
  box-shadow: var(--shadow-md);
  text-align: center;
  max-width: 400px;
  margin: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top: 4px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.error-content h3 {
  margin: 0 0 1rem 0;
  color: var(--danger-color);
}

.error-content p {
  margin: 0 0 1.5rem 0;
  color: var(--text-secondary);
}

.retry-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background-color: #1d4ed8;
}
</style>