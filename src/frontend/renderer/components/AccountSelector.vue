<template>
  <div class="account-selector">
    <div class="selector-container">
      <label for="account-select" class="selector-label">
        Trading Account
      </label>
      
      <div class="select-wrapper">
        <select 
          id="account-select"
          v-model="selectedAccount" 
          @change="onAccountChange"
          class="account-dropdown"
          :disabled="loading || accounts.length === 0"
        >
          <option value="" disabled>
            {{ loading ? 'Loading accounts...' : 'Select Account' }}
          </option>
          
          <optgroup 
            v-for="platform in groupedAccounts" 
            :key="platform.name"
            :label="platform.name"
          >
            <option 
              v-for="account in platform.accounts" 
              :key="account.id"
              :value="account.id"
              :disabled="account.status !== 'active'"
            >
              {{ account.name }} (${{ account.size.toLocaleString() }})
              <span v-if="account.phase !== 'funded'"> - {{ formatPhase(account.phase) }}</span>
              <span v-if="account.status !== 'active'"> - {{ formatStatus(account.status) }}</span>
            </option>
          </optgroup>
        </select>
        
        <div class="select-icon">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <path d="M6 8L2 4h8l-4 4z"/>
          </svg>
        </div>
      </div>
    </div>
    
    <!-- Account Status Display -->
    <div v-if="activeAccount" class="account-status">
      <div class="status-row">
        <div class="status-indicator" :class="accountStatusClass">
          <span class="status-dot" :class="{ pulse: hasViolations }"></span>
        </div>
        
        <div class="status-info">
          <div class="status-text">{{ accountStatusText }}</div>
          <div class="account-details">
            {{ activeAccount.platform.toUpperCase() }} • 
            {{ formatPhase(activeAccount.phase) }} •
            {{ formatAccountType(activeAccount.accountType) }}
          </div>
        </div>
        
        <div class="connection-status" :class="{ connected: activeAccount.isConnected }">
          <span class="connection-dot"></span>
          {{ activeAccount.isConnected ? 'Connected' : 'Disconnected' }}
        </div>
      </div>
      
      <!-- Quick Metrics -->
      <div class="quick-metrics" v-if="activeAccount.metrics">
        <div class="metric-item" :class="{ negative: activeAccount.metrics.dailyPnL < 0 }">
          <span class="metric-label">Day P&L:</span>
          <span class="metric-value">
            {{ formatCurrency(activeAccount.metrics.dailyPnL) }}
          </span>
        </div>
        
        <div class="metric-item">
          <span class="metric-label">Balance:</span>
          <span class="metric-value">
            {{ formatCurrency(activeAccount.currentBalance) }}
          </span>
        </div>
        
        <div class="metric-item" v-if="activeAccount.metrics.openPositions > 0">
          <span class="metric-label">Positions:</span>
          <span class="metric-value">
            {{ activeAccount.metrics.openPositions }} 
            ({{ activeAccount.metrics.totalContracts }} contracts)
          </span>
        </div>
      </div>
      
      <!-- Violations Alert -->
      <div v-if="hasViolations" class="violations-alert">
        <div class="alert-icon">⚠️</div>
        <div class="alert-text">
          {{ violations.length }} active violation{{ violations.length > 1 ? 's' : '' }}
        </div>
        <button class="view-violations-btn" @click="$emit('showViolations')">
          View Details
        </button>
      </div>
    </div>
    
    <!-- Account Actions -->
    <div v-if="activeAccount" class="account-actions">
      <button 
        class="action-btn refresh-btn"
        @click="refreshAccount"
        :disabled="refreshing"
        title="Refresh account data"
      >
        <span class="btn-icon" :class="{ spinning: refreshing }">↻</span>
        {{ refreshing ? 'Refreshing...' : 'Refresh' }}
      </button>
      
      <button 
        v-if="activeAccount.metrics.openPositions > 0"
        class="action-btn flatten-btn"
        @click="confirmFlatten"
        :disabled="flattening"
        title="Close all positions"
      >
        <span class="btn-icon">🚫</span>
        {{ flattening ? 'Closing...' : 'Flatten All' }}
      </button>
      
      <button 
        class="action-btn details-btn"
        @click="$emit('showDetails')"
        title="View detailed account information"
      >
        <span class="btn-icon">📊</span>
        Details
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useFundedAccountsStore } from '@/stores/fundedAccounts'

interface Emits {
  (event: 'accountChanged', accountId: string): void
  (event: 'showViolations'): void
  (event: 'showDetails'): void
  (event: 'positionsFlattened'): void
}

const emit = defineEmits<Emits>()

const store = useFundedAccountsStore()
const refreshing = ref(false)
const flattening = ref(false)

// Computed properties
const { accounts, activeAccount, loading } = store

const selectedAccount = computed({
  get: () => store.activeAccountId,
  set: (value: string) => {
    store.setActiveAccount(value)
    emit('accountChanged', value)
  }
})

const groupedAccounts = computed(() => {
  return store.accountsByPlatform
})

const accountStatusClass = computed(() => {
  if (!activeAccount.value) return 'unknown'
  
  const status = activeAccount.value.status
  const hasViolation = hasViolations.value
  
  if (hasViolation) return 'violation'
  
  switch (status) {
    case 'active': return 'active'
    case 'suspended': return 'suspended'
    case 'passed': return 'passed'
    case 'failed': return 'failed'
    default: return 'unknown'
  }
})

const accountStatusText = computed(() => {
  if (!activeAccount.value) return 'No account selected'
  
  if (hasViolations.value) {
    return `Rule Violation${violations.value.length > 1 ? 's' : ''} Active`
  }
  
  const status = activeAccount.value.status
  switch (status) {
    case 'active': return 'Account Active'
    case 'suspended': return 'Account Suspended'
    case 'passed': return 'Evaluation Passed'
    case 'failed': return 'Evaluation Failed'
    default: return 'Status Unknown'
  }
})

const hasViolations = computed(() => {
  return activeAccount.value ? activeAccount.value.violations.some(v => !v.resolved) : false
})

const violations = computed(() => {
  return activeAccount.value ? activeAccount.value.violations.filter(v => !v.resolved) : []
})

// Helper functions
function formatPhase(phase: string): string {
  switch (phase) {
    case 'evaluation': return 'Evaluation'
    case 'funded': return 'Funded'
    case 'scaling': return 'Scaling'
    default: return phase
  }
}

function formatStatus(status: string): string {
  switch (status) {
    case 'active': return 'Active'
    case 'suspended': return 'Suspended'
    case 'passed': return 'Passed'
    case 'failed': return 'Failed'
    default: return status.charAt(0).toUpperCase() + status.slice(1)
  }
}

function formatAccountType(type: string): string {
  return type.replace(/([A-Z])/g, ' $1').trim()
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

// Event handlers
function onAccountChange() {
  // Account change is handled by the computed setter
}

async function refreshAccount() {
  if (!activeAccount.value || refreshing.value) return
  
  refreshing.value = true
  try {
    await store.updateMetrics(activeAccount.value.id)
  } catch (error) {
    console.error('Failed to refresh account:', error)
  } finally {
    refreshing.value = false
  }
}

async function confirmFlatten() {
  if (!activeAccount.value || flattening.value) return
  
  const confirmed = confirm(
    'Are you sure you want to close all positions? This action cannot be undone.'
  )
  
  if (!confirmed) return
  
  flattening.value = true
  try {
    await store.flattenPositions(activeAccount.value.id)
    emit('positionsFlattened')
  } catch (error) {
    console.error('Failed to flatten positions:', error)
    alert('Failed to close positions. Please try again.')
  } finally {
    flattening.value = false
  }
}
</script>

<style scoped>
.account-selector {
  background: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-color, #e1e5e9);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.selector-container {
  margin-bottom: 1rem;
}

.selector-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  margin-bottom: 0.5rem;
}

.select-wrapper {
  position: relative;
}

.account-dropdown {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 6px;
  background: var(--bg-primary, #ffffff);
  font-size: 0.875rem;
  color: var(--text-primary, #1f2937);
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
}

.account-dropdown:focus {
  outline: none;
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.account-dropdown:disabled {
  background: var(--bg-disabled, #f9fafb);
  color: var(--text-muted, #6b7280);
  cursor: not-allowed;
}

.select-icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted, #6b7280);
  pointer-events: none;
}

.account-status {
  border-top: 1px solid var(--border-color, #e1e5e9);
  padding-top: 1rem;
  margin-bottom: 1rem;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-info {
  flex: 1;
}

.status-text {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary, #1f2937);
}

.account-details {
  font-size: 0.75rem;
  color: var(--text-muted, #6b7280);
  margin-top: 0.25rem;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted, #6b7280);
}

.connection-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
}

.connection-status.connected .connection-dot {
  background: #10b981;
}

.quick-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: var(--bg-tertiary, #f9fafb);
  border-radius: 4px;
  border: 1px solid var(--border-light, #f3f4f6);
}

.metric-label {
  font-size: 0.75rem;
  color: var(--text-muted, #6b7280);
}

.metric-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
}

.metric-item.negative .metric-value {
  color: var(--danger-color, #ef4444);
}

.violations-alert {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  margin-bottom: 0.75rem;
}

.alert-icon {
  font-size: 1.25rem;
}

.alert-text {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  color: #991b1b;
}

.view-violations-btn {
  padding: 0.25rem 0.5rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.view-violations-btn:hover {
  background: #b91c1c;
}

.account-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 6px;
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1f2937);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-hover, #f9fafb);
  border-color: var(--border-hover, #9ca3af);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 0.875rem;
  transition: transform 0.3s ease;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

.flatten-btn {
  border-color: #fca5a5;
  color: #dc2626;
}

.flatten-btn:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #f87171;
}

.details-btn {
  border-color: #93c5fd;
  color: #2563eb;
}

.details-btn:hover:not(:disabled) {
  background: #eff6ff;
  border-color: #60a5fa;
}

/* Status indicator colors */
.status-indicator.active {
  background: #d1fae5;
  color: #065f46;
}

.status-indicator.active .status-dot {
  background: #10b981;
}

.status-indicator.violation {
  background: #fef2f2;
  color: #991b1b;
}

.status-indicator.violation .status-dot {
  background: #ef4444;
}

.status-indicator.suspended {
  background: #fef3c7;
  color: #92400e;
}

.status-indicator.suspended .status-dot {
  background: #f59e0b;
}

.status-indicator.passed {
  background: #dbeafe;
  color: #1e40af;
}

.status-indicator.passed .status-dot {
  background: #3b82f6;
}

.status-indicator.failed {
  background: #fecaca;
  color: #991b1b;
}

.status-indicator.failed .status-dot {
  background: #ef4444;
}

.pulse {
  animation: pulse 2s infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .account-selector {
    --bg-primary: #1f2937;
    --bg-secondary: #374151;
    --bg-tertiary: #4b5563;
    --bg-hover: #4b5563;
    --bg-disabled: #374151;
    --border-color: #4b5563;
    --border-light: #374151;
    --border-hover: #6b7280;
    --text-primary: #f9fafb;
    --text-muted: #9ca3af;
    --primary-color: #60a5fa;
    --danger-color: #f87171;
  }
}
</style>