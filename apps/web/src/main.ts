import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import { routes } from './router'

// Global CSS (if any) would be imported here
// import './assets/main.css'

// Create Vue app instance
const app = createApp(App)

// Configure router
const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// Configure Pinia store
const pinia = createPinia()

// Install plugins
app.use(pinia)
app.use(router)

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', vm)
  console.error('Info:', info)
  
  // In production, you would send this to an error reporting service
  if (import.meta.env.PROD) {
    // reportError(err, vm, info)
  }
}

// Global warning handler  
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('Vue Warning:', msg)
  console.warn('Component:', vm)
  console.warn('Trace:', trace)
}

// Mount the app
app.mount('#app')

// Development helpers
if (import.meta.env.DEV) {
  console.log('🚀 TraderTerminal Web App initialized in development mode')
  console.log('📊 Backend API URL:', import.meta.env.VITE_API_URL || 'http://localhost:8080')
  console.log('🔌 WebSocket URL:', import.meta.env.VITE_WS_URL || 'ws://localhost:8080')
}