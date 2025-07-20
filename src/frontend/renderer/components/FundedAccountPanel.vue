<template>
  <div class="funded-account-panel">
    <!-- Panel Header -->
    <div class="panel-header">
      <div class="header-title">
        <h3>Funded Accounts</h3>
        <div class="account-summary" v-if="totalAccountValue > 0">
          <span class="total-value">
            Total: {{ formatCurrency(totalAccountValue) }}
          </span>
          <span class="daily-pnl" :class="{ negative: totalDailyPnL < 0 }">
            Day: {{ formatCurrency(totalDailyPnL) }}
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <button 
          class="toggle-realtime-btn"
          :class="{ active: realtimeEnabled }"
          @click="toggleRealtime"
          title="Toggle real-time updates"
        >
          <span class="btn-icon" :class="{ pulse: realtimeEnabled }">●</span>
          {{ realtimeEnabled ? 'Live' : 'Paused' }}
        </button>
        
        <button 
          class="refresh-all-btn"
          @click="refreshAllAccounts"
          :disabled="loading"
          title="Refresh all accounts"
        >
          <span class="btn-icon" :class="{ spinning: loading }">↻</span>
        </button>
      </div>
    </div>

    <!-- Account Selector -->
    <AccountSelector 
      @account-changed="onAccountChanged"
      @show-violations="showViolationsModal = true"
      @show-details="showDetailsModal = true"
      @positions-flattened="onPositionsFlattened"
    />

    <!-- Main Content -->
    <div v-if="activeAccount" class="panel-content">
      <!-- Risk Metrics Grid -->
      <div class="metrics-section">
        <h4 class="section-title">Risk Metrics</h4>
        
        <div class="metrics-grid">
          <RiskMeter
            label="Daily P&L"
            :current="Math.abs(activeAccount.metrics.dailyPnL)"
            :limit="activeAccount.rules.maxDailyLoss"
            :inverse="activeAccount.metrics.dailyPnL < 0"
            :show-threshold="true"
            :threshold-value="80"
            threshold-label="Warning"
            :show-details="true"
            format="currency"
          />
          
          <RiskMeter
            label="Trailing Drawdown"
            :current="activeAccount.metrics.currentDrawdown"
            :limit="activeAccount.rules.trailingDrawdown"
            :inverse="true"
            :show-threshold="true"
            :threshold-value="75"
            threshold-label="Danger"
            :show-details="true"
            format="currency"
          />
          
          <RiskMeter
            label="Position Size"
            :current="activeAccount.metrics.totalContracts"
            :limit="activeAccount.rules.maxContracts"
            :show-remaining="true"
            format="number"
          />
        </div>
      </div>

      <!-- Profit Target Progress (for evaluation accounts) -->
      <div v-if="activeAccount.phase === 'evaluation'" class="profit-target-section">
        <h4 class="section-title">Evaluation Progress</h4>
        
        <div class="profit-target-card">
          <div class="target-header">
            <span class="target-label">Profit Target</span>
            <span class="target-progress-text">
              {{ profitProgress.toFixed(1) }}% Complete
            </span>
          </div>
          
          <div class="target-progress-bar">
            <div 
              class="progress-fill" 
              :class="progressClass"
              :style="{ width: Math.min(profitProgress, 100) + '%' }"
            />
            <div class="progress-target-line" :style="{ left: '100%' }"></div>
          </div>
          
          <div class="target-values">
            <span class="current-profit">
              Current: {{ formatCurrency(activeAccount.metrics.totalPnL) }}
            </span>
            <span class="target-profit">
              Target: {{ formatCurrency(activeAccount.rules.profitTarget) }}
            </span>
          </div>
          
          <div class="evaluation-details">
            <div class="detail-item">
              <span class="detail-label">Trading Days:</span>
              <span class="detail-value">
                {{ activeAccount.metrics.tradingDays }} / {{ activeAccount.rules.minTradingDays }}
              </span>
            </div>
            
            <div class="detail-item" v-if="evaluationTimeRemaining">
              <span class="detail-label">Time Remaining:</span>
              <span class="detail-value">{{ evaluationTimeRemaining }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Trading Rules -->
      <div class="rules-section">
        <h4 class="section-title">Account Rules</h4>
        
        <div class="rules-grid">
          <div class="rule-card">
            <div class="rule-header">
              <span class="rule-label">Daily Loss Limit</span>
              <span class="rule-value">{{ formatCurrency(activeAccount.rules.maxDailyLoss) }}</span>
            </div>
            <div class="rule-status" :class="getDailyLossStatus()">
              Remaining: {{ formatCurrency(getRemainingDailyLoss()) }}
            </div>
          </div>
          
          <div class="rule-card">
            <div class="rule-header">
              <span class="rule-label">Max Contracts</span>
              <span class="rule-value">{{ activeAccount.rules.maxContracts }}</span>
            </div>
            <div class="rule-status">
              Current: {{ activeAccount.metrics.totalContracts }}
            </div>
          </div>
          
          <div class="rule-card">
            <div class="rule-header">
              <span class="rule-label">Account Size</span>
              <span class="rule-value">{{ formatCurrency(activeAccount.size) }}</span>
            </div>
            <div class="rule-status">
              Balance: {{ formatCurrency(activeAccount.currentBalance) }}
            </div>
          </div>
          
          <div class="rule-card">
            <div class="rule-header">
              <span class="rule-label">Platform</span>
              <span class="rule-value">{{ activeAccount.platform.toUpperCase() }}</span>
            </div>
            <div class="rule-status">
              {{ formatAccountType(activeAccount.accountType) }}
            </div>
          </div>
        </div>
        
        <!-- Trading Restrictions -->
        <div v-if="hasRestrictions" class="restrictions-section">
          <h5 class="restrictions-title">Trading Restrictions</h5>
          <div class="restrictions-list">
            <div v-if="!activeAccount.rules.allowOvernightPositions" class="restriction-item">
              <span class="restriction-icon">🌙</span>
              No overnight positions
            </div>
            <div v-if="!activeAccount.rules.allowNewsTrading" class="restriction-item">
              <span class="restriction-icon">📰</span>
              No news trading
            </div>
            <div v-if="activeAccount.rules.restrictedSymbols.length > 0" class="restriction-item">
              <span class="restriction-icon">🚫</span>
              Restricted symbols: {{ activeAccount.rules.restrictedSymbols.join(', ') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Statistics -->
      <div class="performance-section">
        <h4 class="section-title">Performance</h4>
        
        <div class="performance-grid">
          <div class="perf-card">
            <div class="perf-label">Win Rate</div>
            <div class="perf-value" :class="getWinRateClass()">
              {{ activeAccount.metrics.winRate.toFixed(1) }}%
            </div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Profit Factor</div>
            <div class="perf-value" :class="getProfitFactorClass()">
              {{ activeAccount.metrics.profitFactor.toFixed(2) }}
            </div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Total Trades</div>
            <div class="perf-value">{{ activeAccount.metrics.totalTrades }}</div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Open Positions</div>
            <div class="perf-value" :class="{ warning: activeAccount.metrics.openPositions > 0 }">
              {{ activeAccount.metrics.openPositions }}
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="actions-section">
        <h4 class="section-title">Quick Actions</h4>
        
        <div class="actions-grid">
          <button 
            class="action-button emergency-btn"
            @click="confirmEmergencyFlatten"
            :disabled="activeAccount.metrics.openPositions === 0 || flattening"
            title="Emergency close all positions"
          >
            <span class="action-icon">🚨</span>
            <span class="action-text">
              {{ flattening ? 'Closing...' : 'Emergency Close' }}
            </span>
          </button>
          
          <button 
            class="action-button refresh-btn"
            @click="refreshActiveAccount"
            :disabled="refreshing"
            title="Refresh account data"
          >
            <span class="action-icon" :class="{ spinning: refreshing }">🔄</span>
            <span class="action-text">
              {{ refreshing ? 'Refreshing...' : 'Refresh Data' }}
            </span>
          </button>
          
          <button 
            class="action-button violations-btn"
            @click="showViolationsModal = true"
            :disabled="activeViolations.length === 0"
            title="View rule violations"
          >
            <span class="action-icon">⚠️</span>
            <span class="action-text">
              Violations ({{ activeViolations.length }})
            </span>
          </button>
          
          <button 
            class="action-button details-btn"
            @click="showDetailsModal = true"
            title="View detailed account information"
          >
            <span class="action-icon">📊</span>
            <span class="action-text">View Details</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- No Account Selected State -->
    <div v-else-if="!loading" class="no-account-state">
      <div class="no-account-icon">👤</div>
      <div class="no-account-text">
        <h4>No Account Selected</h4>
        <p>Select a funded trading account to view metrics and manage risk</p>
      </div>
      <button v-if="accounts.length === 0" @click="fetchAccounts" class="load-accounts-btn">
        Load Accounts
      </button>
    </div>

    <!-- Loading State -->
    <div v-else class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading funded accounts...</div>
    </div>

    <!-- Violations Modal -->
    <div v-if="showViolationsModal" class="modal-overlay" @click="showViolationsModal = false">
      <div class="modal-content violations-modal" @click.stop>
        <div class="modal-header">
          <h3>Rule Violations</h3>
          <button class="modal-close" @click="showViolationsModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="activeViolations.length === 0" class="no-violations">
            <div class="no-violations-icon">✅</div>
            <p>No active rule violations</p>
          </div>
          <div v-else class="violations-list">
            <div 
              v-for="violation in activeViolations" 
              :key="violation.id"
              class="violation-item"
              :class="violation.type"
            >
              <div class="violation-header">
                <span class="violation-type">{{ formatViolationType(violation.type) }}</span>
                <span class="violation-time">{{ formatTime(violation.triggeredAt) }}</span>
              </div>
              <div class="violation-message">{{ violation.message }}</div>
              <div class="violation-details">
                <span>Limit: {{ formatCurrency(violation.ruleLimit) }}</span>
                <span>Actual: {{ formatCurrency(violation.actualValue) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="showDetailsModal" class="modal-overlay" @click="showDetailsModal = false">
      <div class="modal-content details-modal" @click.stop>
        <div class="modal-header">
          <h3>Account Details</h3>
          <button class="modal-close" @click="showDetailsModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="activeAccount" class="account-details">
            <!-- Account Information -->
            <div class="details-section">
              <h4>Account Information</h4>
              <div class="details-grid">
                <div class="detail-row">
                  <span class="detail-label">Account ID:</span>
                  <span class="detail-value">{{ activeAccount.id }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Created:</span>
                  <span class="detail-value">{{ formatDate(activeAccount.createdAt) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Last Trade:</span>
                  <span class="detail-value">
                    {{ activeAccount.lastTradeDate ? formatDate(activeAccount.lastTradeDate) : 'Never' }}
                  </span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Last Update:</span>
                  <span class="detail-value">{{ formatDate(activeAccount.lastUpdated) }}</span>
                </div>
              </div>
            </div>
            
            <!-- Raw JSON for debugging -->
            <div class="details-section">
              <h4>Raw Data (Debug)</h4>
              <pre class="json-display">{{ JSON.stringify(activeAccount, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useFundedAccountsStore } from '@/stores/fundedAccounts'
import AccountSelector from './AccountSelector.vue'
import RiskMeter from './RiskMeter.vue'

const store = useFundedAccountsStore()

// Local state
const showViolationsModal = ref(false)
const showDetailsModal = ref(false)
const refreshing = ref(false)
const flattening = ref(false)

// Store state
const { 
  accounts, 
  activeAccount, 
  loading, 
  totalAccountValue, 
  totalDailyPnL,
  activeViolations,
  realtimeEnabled
} = store

// Computed properties
const profitProgress = computed(() => {
  if (!activeAccount.value || activeAccount.value.phase !== 'evaluation') return 0
  const target = activeAccount.value.rules.profitTarget
  const current = activeAccount.value.metrics.totalPnL
  return target > 0 ? (current / target) * 100 : 0
})

const progressClass = computed(() => {
  const progress = profitProgress.value
  if (progress >= 100) return 'complete'
  if (progress >= 75) return 'near-complete'
  if (progress >= 50) return 'good'
  if (progress >= 25) return 'progress'
  return 'early'
})

const evaluationTimeRemaining = computed(() => {
  if (!activeAccount.value?.evaluationEndDate) return null
  
  const endDate = new Date(activeAccount.value.evaluationEndDate)
  const now = new Date()
  const diffMs = endDate.getTime() - now.getTime()
  
  if (diffMs <= 0) return 'Expired'
  
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  
  if (days > 0) return `${days}d ${hours}h`
  return `${hours}h`
})

const hasRestrictions = computed(() => {
  if (!activeAccount.value) return false
  const rules = activeAccount.value.rules
  return !rules.allowOvernightPositions || 
         !rules.allowNewsTrading || 
         rules.restrictedSymbols.length > 0
})

// Methods
function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

function formatAccountType(type: string): string {
  return type.replace(/([A-Z])/g, ' $1').trim()
}

function getRemainingDailyLoss(): number {
  if (!activeAccount.value) return 0
  return Math.max(0, activeAccount.value.rules.maxDailyLoss + activeAccount.value.metrics.dailyPnL)
}

function getDailyLossStatus(): string {
  const remaining = getRemainingDailyLoss()
  const limit = activeAccount.value?.rules.maxDailyLoss || 1
  const percentage = (remaining / limit) * 100
  
  if (percentage <= 10) return 'critical'
  if (percentage <= 25) return 'danger'
  if (percentage <= 50) return 'warning'
  return 'safe'
}

function getWinRateClass(): string {
  const rate = activeAccount.value?.metrics.winRate || 0
  if (rate >= 70) return 'excellent'
  if (rate >= 60) return 'good'
  if (rate >= 50) return 'average'
  return 'poor'
}

function getProfitFactorClass(): string {
  const factor = activeAccount.value?.metrics.profitFactor || 0
  if (factor >= 2.0) return 'excellent'
  if (factor >= 1.5) return 'good'
  if (factor >= 1.0) return 'average'
  return 'poor'
}

function formatViolationType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString()
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleString()
}

// Event handlers
function onAccountChanged(accountId: string) {
  console.log('Account changed to:', accountId)
}

function onPositionsFlattened() {
  console.log('Positions flattened')
}

async function refreshActiveAccount() {
  if (!activeAccount.value || refreshing.value) return
  
  refreshing.value = true
  try {
    await store.updateMetrics(activeAccount.value.id)
  } finally {
    refreshing.value = false
  }
}

async function refreshAllAccounts() {
  await store.fetchAccounts()
}

function toggleRealtime() {
  if (realtimeEnabled.value) {
    store.stopRealtimeUpdates()
  } else {
    store.startRealtimeUpdates()
  }
}

async function confirmEmergencyFlatten() {
  if (!activeAccount.value || flattening.value) return
  
  const confirmed = confirm(
    '⚠️ EMERGENCY POSITION CLOSE ⚠️\n\n' +
    'This will immediately close ALL open positions in this account.\n' +
    'This action cannot be undone.\n\n' +
    'Are you sure you want to proceed?'
  )
  
  if (!confirmed) return
  
  flattening.value = true
  try {
    await store.flattenPositions(activeAccount.value.id)
  } finally {
    flattening.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await store.fetchAccounts()
  store.startRealtimeUpdates()
})

onUnmounted(() => {
  store.stopRealtimeUpdates()
})
</script>

<style scoped>
/* Component styles would go here - this is a comprehensive component */
/* For brevity, I'll include key styles only */

.funded-account-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--bg-primary);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-title h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.account-summary {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
}

.daily-pnl.negative {
  color: var(--danger-color);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.section-title {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.rule-card {
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.action-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-button:hover:not(:disabled) {
  background: var(--bg-hover);
  transform: translateY(-1px);
}

.emergency-btn {
  border-color: #f87171;
  color: #dc2626;
}

.emergency-btn:hover:not(:disabled) {
  background: #fef2f2;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-muted);
}

.no-account-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.no-account-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* CSS Variables for theming */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-hover: #e9ecef;
  --text-primary: #212529;
  --text-muted: #6c757d;
  --border-color: #dee2e6;
  --primary-color: #0d6efd;
  --danger-color: #dc3545;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --bg-hover: #404040;
    --text-primary: #ffffff;
    --text-muted: #adb5bd;
    --border-color: #404040;
    --primary-color: #0d6efd;
    --danger-color: #dc3545;
  }
}
</style>