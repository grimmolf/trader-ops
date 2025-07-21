<template>
  <div class="tradenote-panel">
    <!-- Panel Header -->
    <div class="panel-header">
      <div class="header-title">
        <h3>Trade Journal</h3>
        <div class="connection-status">
          <span 
            class="status-dot" 
            :class="connectionStatus"
            :title="connectionStatusText"
          ></span>
          <span class="status-text">{{ connectionStatusText }}</span>
        </div>
      </div>
      
      <div class="header-actions">
        <div class="view-toggle">
          <button 
            v-for="view in availableViews"
            :key="view.id"
            @click="selectedView = view.id"
            :class="{ active: selectedView === view.id }"
            class="view-btn"
            :title="view.description"
          >
            <span class="view-icon">{{ view.icon }}</span>
            <span class="view-label">{{ view.label }}</span>
          </button>
        </div>
        
        <button 
          class="settings-btn"
          @click="showSettings = true"
          title="TradeNote Settings"
        >
          <span class="settings-icon">⚙️</span>
        </button>
      </div>
    </div>

    <!-- Connection Error -->
    <div v-if="connectionError" class="connection-error">
      <div class="error-content">
        <div class="error-icon">🔌</div>
        <div class="error-message">
          <h4>TradeNote Connection Error</h4>
          <p>{{ connectionError }}</p>
        </div>
        <div class="error-actions">
          <button @click="retryConnection" class="retry-btn">Retry Connection</button>
          <button @click="showSettings = true" class="settings-btn-alt">Check Settings</button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="panel-content">
      <!-- Calendar View -->
      <div v-if="selectedView === 'calendar'" class="view-container">
        <TradeNoteCalendar />
      </div>

      <!-- Analytics View -->
      <div v-else-if="selectedView === 'analytics'" class="view-container">
        <TradeNoteAnalytics />
      </div>

      <!-- Combined View -->
      <div v-else-if="selectedView === 'combined'" class="view-container combined-view">
        <div class="combined-header">
          <h4>Calendar & Analytics Overview</h4>
        </div>
        
        <div class="combined-layout">
          <div class="calendar-section">
            <TradeNoteCalendar />
          </div>
          
          <div class="analytics-section">
            <TradeNoteAnalytics />
          </div>
        </div>
      </div>
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettings" class="settings-modal-overlay" @click="closeSettings">
      <div class="settings-modal" @click.stop>
        <div class="modal-header">
          <h4>TradeNote Settings</h4>
          <button @click="closeSettings" class="close-btn">×</button>
        </div>
        
        <div class="modal-content">
          <div class="settings-form">
            <div class="form-group">
              <label for="tradenote-url">TradeNote URL</label>
              <input 
                id="tradenote-url"
                v-model="settings.baseUrl"
                type="url"
                placeholder="http://localhost:8082"
                class="form-input"
              />
              <small class="form-help">URL of your TradeNote instance</small>
            </div>
            
            <div class="form-group">
              <label for="app-id">Application ID</label>
              <input 
                id="app-id"
                v-model="settings.appId"
                type="text"
                placeholder="Enter App ID"
                class="form-input"
              />
              <small class="form-help">TradeNote Parse Server App ID</small>
            </div>
            
            <div class="form-group">
              <label for="master-key">Master Key</label>
              <input 
                id="master-key"
                v-model="settings.masterKey"
                type="password"
                placeholder="Enter Master Key"
                class="form-input"
              />
              <small class="form-help">TradeNote Parse Server Master Key</small>
            </div>
            
            <div class="form-group">
              <label class="checkbox-label">
                <input 
                  v-model="settings.enabled"
                  type="checkbox"
                  class="form-checkbox"
                />
                <span class="checkbox-text">Enable TradeNote Integration</span>
              </label>
              <small class="form-help">Automatically log trades to TradeNote</small>
            </div>
            
            <div class="form-group">
              <label class="checkbox-label">
                <input 
                  v-model="settings.autoSync"
                  type="checkbox"
                  class="form-checkbox"
                />
                <span class="checkbox-text">Auto-sync every 5 minutes</span>
              </label>
              <small class="form-help">Automatically sync new trades from TradeNote</small>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="testConnection" :disabled="isTesting" class="test-btn">
            {{ isTesting ? 'Testing...' : 'Test Connection' }}
          </button>
          <button @click="saveSettings" :disabled="isSaving" class="save-btn">
            {{ isSaving ? 'Saving...' : 'Save Settings' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Status Toast -->
    <div v-if="statusMessage" class="status-toast" :class="statusType">
      <span class="toast-icon">
        {{ statusType === 'success' ? '✅' : statusType === 'error' ? '❌' : 'ℹ️' }}
      </span>
      <span class="toast-message">{{ statusMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTradeNoteStore } from '../stores/tradenote'
import TradeNoteCalendar from './TradeNoteCalendar.vue'
import TradeNoteAnalytics from './TradeNoteAnalytics.vue'

// Store
const tradeNoteStore = useTradeNoteStore()

// Reactive data
const selectedView = ref('calendar')
const showSettings = ref(false)
const isTesting = ref(false)
const isSaving = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const connectionError = ref('')

// Available views
const availableViews = [
  {
    id: 'calendar',
    label: 'Calendar',
    icon: '📅',
    description: 'Trading calendar heat-map'
  },
  {
    id: 'analytics',
    label: 'Analytics', 
    icon: '📊',
    description: 'Performance statistics and charts'
  },
  {
    id: 'combined',
    label: 'Overview',
    icon: '🎯',
    description: 'Combined calendar and analytics view'
  }
]

// Settings form
const settings = ref({
  baseUrl: '',
  appId: '',
  masterKey: '',
  enabled: true,
  autoSync: true
})

// Computed properties
const connectionStatus = computed(() => {
  const status = tradeNoteStore.connectionStatus
  if (status === 'connected') return 'connected'
  if (status === 'connecting') return 'connecting'
  if (status === 'error') return 'error'
  return 'disconnected'
})

const connectionStatusText = computed(() => {
  const status = tradeNoteStore.connectionStatus
  switch (status) {
    case 'connected': return 'Connected'
    case 'connecting': return 'Connecting...'
    case 'error': return 'Connection Error'
    default: return 'Disconnected'
  }
})

// Methods
async function initializeTradeNote() {
  try {
    await tradeNoteStore.initialize()
    
    // Load settings
    const config = tradeNoteStore.config
    if (config) {
      settings.value = {
        baseUrl: config.base_url || '',
        appId: config.app_id || '',
        masterKey: config.master_key || '',
        enabled: config.enabled || false,
        autoSync: config.auto_sync || false
      }
    }
    
    // Check connection
    if (settings.value.enabled) {
      await tradeNoteStore.checkConnection()
    }
    
  } catch (error) {
    console.error('Failed to initialize TradeNote:', error)
    connectionError.value = error.message || 'Failed to initialize TradeNote'
  }
}

async function retryConnection() {
  connectionError.value = ''
  await tradeNoteStore.checkConnection()
  
  if (tradeNoteStore.connectionStatus === 'error') {
    connectionError.value = 'Failed to connect to TradeNote. Check your settings.'
  }
}

async function testConnection() {
  isTesting.value = true
  
  try {
    const result = await tradeNoteStore.testConnection({
      base_url: settings.value.baseUrl,
      app_id: settings.value.appId,
      master_key: settings.value.masterKey,
      enabled: settings.value.enabled
    })
    
    if (result.success) {
      showStatusMessage('Connection successful!', 'success')
    } else {
      showStatusMessage(result.message || 'Connection failed', 'error')
    }
  } catch (error) {
    showStatusMessage('Connection test failed', 'error')
  } finally {
    isTesting.value = false
  }
}

async function saveSettings() {
  isSaving.value = true
  
  try {
    const config = {
      base_url: settings.value.baseUrl,
      app_id: settings.value.appId,
      master_key: settings.value.masterKey,
      enabled: settings.value.enabled,
      auto_sync: settings.value.autoSync
    }
    
    const result = await tradeNoteStore.updateConfig(config)
    
    if (result.success) {
      showStatusMessage('Settings saved successfully!', 'success')
      showSettings.value = false
      connectionError.value = ''
      
      // Reinitialize if enabled
      if (settings.value.enabled) {
        await tradeNoteStore.checkConnection()
      }
    } else {
      showStatusMessage(result.message || 'Failed to save settings', 'error')
    }
  } catch (error) {
    showStatusMessage('Failed to save settings', 'error')
  } finally {
    isSaving.value = false
  }
}

function closeSettings() {
  showSettings.value = false
}

function showStatusMessage(message, type = 'info') {
  statusMessage.value = message
  statusType.value = type
  
  setTimeout(() => {
    statusMessage.value = ''
  }, 3000)
}

// Auto-sync interval
let autoSyncInterval = null

function startAutoSync() {
  if (autoSyncInterval) {
    clearInterval(autoSyncInterval)
  }
  
  if (settings.value.autoSync && settings.value.enabled) {
    autoSyncInterval = setInterval(async () => {
      try {
        await tradeNoteStore.syncData()
      } catch (error) {
        console.error('Auto-sync failed:', error)
      }
    }, 5 * 60 * 1000) // 5 minutes
  }
}

function stopAutoSync() {
  if (autoSyncInterval) {
    clearInterval(autoSyncInterval)
    autoSyncInterval = null
  }
}

// Lifecycle
onMounted(() => {
  initializeTradeNote()
  startAutoSync()
})

onUnmounted(() => {
  stopAutoSync()
})
</script>

<style scoped>
.tradenote-panel {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Panel Header */
.panel-header {
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-title h3 {
  margin: 0 0 4px 0;
  color: #fff;
  font-size: 18px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.connected {
  background: #22c55e;
}

.status-dot.connecting {
  background: #f59e0b;
  animation: pulse 1.5s infinite;
}

.status-dot.error {
  background: #ef4444;
}

.status-dot.disconnected {
  background: #6b7280;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  display: flex;
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 6px;
  overflow: hidden;
}

.view-btn {
  background: none;
  border: none;
  color: #888;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  transition: all 0.2s;
}

.view-btn:hover {
  background: #333;
  color: #e5e5e5;
}

.view-btn.active {
  background: #0ea5e9;
  color: #fff;
}

.view-icon {
  font-size: 14px;
}

.settings-btn {
  background: #333;
  border: 1px solid #555;
  color: #e5e5e5;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.settings-btn:hover {
  background: #444;
}

/* Connection Error */
.connection-error {
  padding: 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #ef4444;
  margin: 16px;
  border-radius: 6px;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.error-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.error-message h4 {
  margin: 0 0 4px 0;
  color: #ef4444;
}

.error-message p {
  margin: 0;
  color: #e5e5e5;
  font-size: 14px;
}

.error-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.retry-btn,
.settings-btn-alt {
  background: #ef4444;
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.settings-btn-alt {
  background: #333;
}

.retry-btn:hover {
  background: #dc2626;
}

.settings-btn-alt:hover {
  background: #444;
}

/* Panel Content */
.panel-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.view-container {
  height: 100%;
}

.combined-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.combined-header {
  text-align: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
}

.combined-header h4 {
  margin: 0;
  color: #fff;
  font-size: 16px;
}

.combined-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  flex: 1;
}

/* Settings Modal */
.settings-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.settings-modal {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  background: #333;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #444;
}

.modal-header h4 {
  margin: 0;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #fff;
}

.modal-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  color: #e5e5e5;
  font-size: 14px;
  font-weight: 500;
}

.form-input {
  background: #1a1a1a;
  border: 1px solid #444;
  color: #e5e5e5;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:focus {
  outline: none;
  border-color: #0ea5e9;
}

.form-help {
  color: #888;
  font-size: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-checkbox {
  width: 16px;
  height: 16px;
}

.checkbox-text {
  color: #e5e5e5;
  font-size: 14px;
}

.modal-footer {
  background: #333;
  padding: 16px 20px;
  border-top: 1px solid #444;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.test-btn,
.save-btn {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: none;
}

.test-btn {
  background: #6b7280;
  color: white;
}

.test-btn:hover {
  background: #4b5563;
}

.save-btn {
  background: #0ea5e9;
  color: white;
}

.save-btn:hover {
  background: #0284c7;
}

.test-btn:disabled,
.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Status Toast */
.status-toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #333;
  border: 1px solid #555;
  border-radius: 6px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1001;
  color: #e5e5e5;
  font-size: 14px;
  animation: slideIn 0.3s ease-out;
}

.status-toast.success {
  background: rgba(34, 197, 94, 0.2);
  border-color: #22c55e;
}

.status-toast.error {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
}

.status-toast.info {
  background: rgba(14, 165, 233, 0.2);
  border-color: #0ea5e9;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 1200px) {
  .combined-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .header-actions {
    justify-content: space-between;
  }
  
  .view-toggle {
    flex: 1;
  }
  
  .view-btn {
    flex: 1;
    justify-content: center;
  }
}
</style>