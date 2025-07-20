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
          @click="$emit('toggleRealtime')"
          title="Toggle real-time updates"
        >
          <span class="btn-icon" :class="{ pulse: realtimeEnabled }">●</span>
          {{ realtimeEnabled ? 'Live' : 'Paused' }}
        </button>
        
        <button 
          class="refresh-all-btn"
          @click="$emit('refreshAll')"
          :disabled="loading"
          title="Refresh all accounts"
        >
          <span class="btn-icon" :class="{ spinning: loading }">↻</span>
        </button>
      </div>
    </div>

    <!-- Account Selector -->
    <AccountSelector 
      :accounts="accounts"
      :active-account="activeAccount"
      :loading="loading"
      :grouped-accounts="groupedAccounts"
      :selected-account-id="selectedAccountId"
      @account-changed="$emit('accountChanged', $event)"
      @show-violations="showViolationsModal = true"
      @show-details="showDetailsModal = true"
      @positions-flattened="$emit('positionsFlattened')"
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
            @click="$emit('refreshAccount')"
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
      <button v-if="accounts.length === 0" @click="$emit('fetchAccounts')" class="load-accounts-btn">
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
import { computed, ref } from 'vue'
import AccountSelector from './AccountSelector.vue'
import RiskMeter from './RiskMeter.vue'

interface Props {
  accounts?: any[]
  activeAccount?: any
  loading?: boolean
  refreshing?: boolean
  realtimeEnabled?: boolean
  groupedAccounts?: any[]
  selectedAccountId?: string
  activeViolations?: any[]
}

interface Emits {
  (event: 'accountChanged', accountId: string): void
  (event: 'positionsFlattened'): void
  (event: 'toggleRealtime'): void
  (event: 'refreshAll'): void
  (event: 'refreshAccount'): void
  (event: 'fetchAccounts'): void
  (event: 'emergencyFlatten'): void
}

const props = withDefaults(defineProps<Props>(), {
  accounts: () => [],
  loading: false,
  refreshing: false,
  realtimeEnabled: false,
  groupedAccounts: () => [],
  selectedAccountId: '',
  activeViolations: () => []
})

const emit = defineEmits<Emits>()

// Local state
const showViolationsModal = ref(false)
const showDetailsModal = ref(false)
const flattening = ref(false)

// Computed properties
const totalAccountValue = computed(() => {
  return props.accounts.reduce((total, account) => total + (account.balance || 0), 0)
})

const totalDailyPnL = computed(() => {
  return props.accounts.reduce((total, account) => total + (account.dailyLoss || 0), 0)
})

const profitProgress = computed(() => {
  if (!props.activeAccount || props.activeAccount.phase !== 'evaluation') return 0
  const target = props.activeAccount.rules.profitTarget
  const current = props.activeAccount.metrics.totalPnL
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
  if (!props.activeAccount?.evaluationEndDate) return null
  
  const endDate = new Date(props.activeAccount.evaluationEndDate)
  const now = new Date()
  const diffMs = endDate.getTime() - now.getTime()
  
  if (diffMs <= 0) return 'Expired'
  
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  
  if (days > 0) return `${days}d ${hours}h`
  return `${hours}h`
})

const hasRestrictions = computed(() => {
  if (!props.activeAccount) return false
  const rules = props.activeAccount.rules
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
  if (!props.activeAccount) return 0
  return Math.max(0, props.activeAccount.rules.maxDailyLoss + props.activeAccount.metrics.dailyPnL)
}

function getDailyLossStatus(): string {
  const remaining = getRemainingDailyLoss()
  const limit = props.activeAccount?.rules.maxDailyLoss || 1
  const percentage = (remaining / limit) * 100
  
  if (percentage <= 10) return 'critical'
  if (percentage <= 25) return 'danger'
  if (percentage <= 50) return 'warning'
  return 'safe'
}

function getWinRateClass(): string {
  const rate = props.activeAccount?.metrics.winRate || 0
  if (rate >= 70) return 'excellent'
  if (rate >= 60) return 'good'
  if (rate >= 50) return 'average'
  return 'poor'
}

function getProfitFactorClass(): string {
  const factor = props.activeAccount?.metrics.profitFactor || 0
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

function confirmEmergencyFlatten() {
  if (!props.activeAccount || flattening.value) return
  
  const confirmed = confirm(
    '⚠️ EMERGENCY POSITION CLOSE ⚠️\n\n' +
    'This will immediately close ALL open positions in this account.\n' +
    'This action cannot be undone.\n\n' +
    'Are you sure you want to proceed?'
  )
  
  if (!confirmed) return
  
  flattening.value = true
  emit('emergencyFlatten')
  
  // Reset flattening state after a delay
  setTimeout(() => {
    flattening.value = false
  }, 3000)
}
</script>

<style scoped>
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

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.toggle-realtime-btn,
.refresh-all-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-realtime-btn.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.btn-icon.pulse {
  animation: pulse 2s infinite;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
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

.profit-target-card {
  padding: 1.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.target-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.target-progress-bar {
  height: 12px;
  background: var(--bg-tertiary, #e9ecef);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
  margin-bottom: 1rem;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.5s ease;
}

.progress-fill.complete { background: #28a745; }
.progress-fill.near-complete { background: #20c997; }
.progress-fill.good { background: #17a2b8; }
.progress-fill.progress { background: #ffc107; }
.progress-fill.early { background: #fd7e14; }

.target-values {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.evaluation-details {
  display: flex;
  gap: 2rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.detail-value {
  font-weight: 600;
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

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.rule-label {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.rule-value {
  font-weight: 600;
  color: var(--text-primary);
}

.rule-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.rule-status.safe { background: #d4edda; color: #155724; }
.rule-status.warning { background: #fff3cd; color: #856404; }
.rule-status.danger { background: #f8d7da; color: #721c24; }
.rule-status.critical { background: #f8d7da; color: #721c24; font-weight: 600; }

.restrictions-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.restrictions-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
}

.restrictions-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.restriction-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.perf-card {
  text-align: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.perf-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.perf-value {
  font-size: 1.25rem;
  font-weight: 600;
}

.perf-value.excellent { color: #28a745; }
.perf-value.good { color: #20c997; }
.perf-value.average { color: #17a2b8; }
.perf-value.poor { color: #dc3545; }
.perf-value.warning { color: #ffc107; }

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

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.emergency-btn {
  border-color: #f87171;
  color: #dc2626;
}

.emergency-btn:hover:not(:disabled) {
  background: #fef2f2;
}

.action-icon {
  font-size: 1.5rem;
}

.action-text {
  font-size: 0.875rem;
  font-weight: 500;
}

.no-account-state,
.loading-state {
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

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
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

.modal-body {
  padding: 1.5rem;
}

.violations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.violation-item {
  padding: 1rem;
  border-left: 4px solid #dc3545;
  background: #fef2f2;
  border-radius: 4px;
}

.violation-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.violation-type {
  font-weight: 600;
  color: #dc3545;
}

.violation-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.violation-message {
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.violation-details {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.details-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
}

.json-display {
  background: var(--bg-secondary);
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 300px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* CSS Variables for theming */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-tertiary: #e9ecef;
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
    --bg-tertiary: #404040;
    --bg-hover: #404040;
    --text-primary: #ffffff;
    --text-muted: #adb5bd;
    --border-color: #404040;
    --primary-color: #0d6efd;
    --danger-color: #dc3545;
  }
}
</style>