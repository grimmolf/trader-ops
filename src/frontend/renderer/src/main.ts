import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import TradingDashboard from '../components/TradingDashboard.vue'

// Create router
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: TradingDashboard,
      meta: { title: 'Trading Dashboard' }
    }
  ]
})

// Create Pinia store
const pinia = createPinia()

// Create Vue app
const app = createApp(App)

// Use plugins
app.use(pinia)
app.use(router)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Vue error:', error, info)
  // You can add error reporting here
}

// Mount app
app.mount('#app')