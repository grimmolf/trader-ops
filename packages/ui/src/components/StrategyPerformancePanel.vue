<template>
  <div class="strategy-performance-panel">
    <!-- Panel Header -->
    <div class="panel-header">
      <div class="header-title">
        <h3>Strategy Performance</h3>
        <div class="system-summary" v-if="systemStatus">
          <span class="total-strategies">
            Total: {{ systemStatus.total_strategies }}
          </span>
          <span class="live-strategies">
            Live: {{ systemStatus.live_strategies }}
          </span>
          <span class="at-risk-strategies" v-if="systemStatus.at_risk_strategies > 0">
            At Risk: {{ systemStatus.at_risk_strategies }}
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <button 
          class="system-status-indicator"
          :class="{ healthy: systemStatus?.initialized, unhealthy: !systemStatus?.initialized }"
          :title="`System Status: ${systemStatus?.initialized ? 'Operational' : 'Initializing'}`"
        >
          {{ systemStatus?.initialized ? 'Operational' : 'Initializing' }}
        </button>
        
        <button 
          class="refresh-btn"
          @click="refreshData"
          :disabled="isLoading"
          title="Refresh strategy performance data"
        >
          <span class="btn-icon" :class="{ spinning: isLoading }">↻</span>
        </button>
      </div>
    </div>

    <!-- Strategy Selector -->
    <div class="strategy-selector-section">
      <h4 class="section-title">Select Strategy</h4>
      <div class="strategy-selector">
        <select 
          v-model="selectedStrategyId" 
          @change="onStrategyChanged"
          class="strategy-select"
          :disabled="isLoading"
        >
          <option value="">Select Strategy</option>
          <option 
            v-for="summary in allStrategySummaries" 
            :key="summary.strategy_id" 
            :value="summary.strategy_id"
          >
            {{ summary.strategy_name }} ({{ formatMode(summary.current_mode) }})
          </option>
        </select>
        
        <button 
          class="register-strategy-btn"
          @click="showRegisterModal = true"
          :disabled="isLoading"
          title="Register new strategy"
        >
          + Add Strategy
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div v-if="selectedStrategySummary" class="panel-content">
      <!-- Strategy Overview -->
      <div class="overview-section">
        <h4 class="section-title">
          Strategy Overview
          <span class="strategy-mode-badge" :class="getModeColor(selectedStrategySummary.current_mode)">
            {{ formatMode(selectedStrategySummary.current_mode) }}
          </span>
        </h4>
        
        <div class="overview-grid">
          <div class="overview-card">
            <div class="card-label">Current Set Progress</div>
            <div class="card-value">{{ selectedStrategySummary.current_set_progress }}/{{ evaluationPeriod }}</div>
            <div class="card-change">
              Win Rate: {{ formatWinRate(selectedStrategySummary.current_set_win_rate) }}
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-label">Overall Win Rate</div>
            <div class="card-value" :class="getWinRateClass(selectedStrategySummary.overall_win_rate)">
              {{ formatWinRate(selectedStrategySummary.overall_win_rate) }}
            </div>
            <div class="card-change">
              Total Sets: {{ selectedStrategySummary.total_sets_completed }}
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-label">Lifetime P&L</div>
            <div class="card-value" :class="{ positive: selectedStrategySummary.lifetime_pnl > 0, negative: selectedStrategySummary.lifetime_pnl < 0 }">
              {{ formatCurrency(selectedStrategySummary.lifetime_pnl) }}
            </div>
            <div class="card-change">
              Net: {{ formatCurrency(selectedStrategySummary.lifetime_net_pnl) }}
            </div>
          </div>
          
          <div class="overview-card" v-if="selectedStrategySummary.is_at_risk || selectedStrategySummary.can_return_to_live">
            <div class="card-label">Status</div>
            <div class="card-value">
              <span v-if="selectedStrategySummary.is_at_risk" class="status-badge at-risk">At Risk</span>
              <span v-else-if="selectedStrategySummary.can_return_to_live" class="status-badge can-return">Can Return</span>
            </div>
            <div class="card-change">
              Performance evaluation
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Performance -->
      <div class="performance-section">
        <h4 class="section-title">Recent Performance</h4>
        <div class="performance-chart">
          <div 
            v-for="(winRate, index) in selectedStrategySummary.recent_performance" 
            :key="index"
            class="performance-bar"
            :class="getWinRateClass(winRate)"
            :style="{ height: `${Math.max(winRate, 10)}%` }"
            :title="`Set ${selectedStrategySummary.total_sets_completed - selectedStrategySummary.recent_performance.length + index + 1}: ${formatWinRate(winRate)}`"
          >
            <span class="bar-label">{{ formatWinRate(winRate) }}</span>
          </div>
        </div>
        <div class="performance-threshold">
          <span class="threshold-line" :style="{ bottom: `${minWinRate}%` }">
            Minimum: {{ formatWinRate(minWinRate) }}
          </span>
        </div>
      </div>

      <!-- Strategy Actions -->
      <div class="actions-section">
        <h4 class="section-title">Strategy Actions</h4>
        <div class="action-buttons">
          <button 
            v-if="selectedStrategySummary.current_mode === 'live'"
            class="action-btn danger"
            @click="confirmModeChange('paper', 'Manual override to paper trading')"
            :disabled="isLoading"
          >
            Move to Paper
          </button>
          
          <button 
            v-if="selectedStrategySummary.current_mode === 'paper'"
            class="action-btn success"
            @click="confirmModeChange('live', 'Manual override to live trading')"
            :disabled="isLoading"
          >
            Move to Live
          </button>
          
          <button 
            v-if="selectedStrategySummary.current_mode !== 'suspended'"
            class="action-btn warning"
            @click="confirmModeChange('suspended', 'Manual suspension')"
            :disabled="isLoading"
          >
            Suspend Strategy
          </button>
          
          <button 
            v-if="selectedStrategySummary.current_mode === 'suspended'"
            class="action-btn success"
            @click="confirmModeChange('live', 'Resume from suspension')"
            :disabled="isLoading"
          >
            Resume Strategy
          </button>
        </div>
      </div>
    </div>

    <!-- Strategy List (when no strategy selected) -->
    <div v-else class="strategy-list-section">
      <h4 class="section-title">All Strategies</h4>
      <div class="strategy-list">
        <div 
          v-for="summary in allStrategySummaries" 
          :key="summary.strategy_id"
          class="strategy-card"
          :class="getModeColor(summary.current_mode)"
          @click="selectStrategy(summary.strategy_id)"
        >
          <div class="strategy-header">
            <span class="strategy-name">{{ summary.strategy_name }}</span>
            <span class="strategy-mode" :class="getModeColor(summary.current_mode)">
              {{ formatMode(summary.current_mode) }}
            </span>
          </div>
          <div class="strategy-stats">
            <span class="win-rate" :class="getWinRateClass(summary.overall_win_rate)">
              {{ formatWinRate(summary.overall_win_rate) }}
            </span>
            <span class="pnl" :class="{ positive: summary.lifetime_pnl > 0, negative: summary.lifetime_pnl < 0 }">
              {{ formatCurrency(summary.lifetime_pnl) }}
            </span>
            <span class="progress">{{ summary.current_set_progress }}/{{ evaluationPeriod }}</span>
          </div>
          <div class="strategy-status">
            <span v-if="summary.is_at_risk" class="status-badge at-risk">At Risk</span>
            <span v-else-if="summary.can_return_to_live" class="status-badge can-return">Can Return</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Alerts -->
    <div class="alerts-section" v-if="recentAlerts.length > 0">
      <h4 class="section-title">
        Recent Alerts
        <button 
          class="clear-alerts-btn"
          @click="clearAlerts"
          title="Clear all alerts"
        >
          Clear
        </button>
      </h4>
      <div class="alerts-list">
        <div 
          v-for="alert in recentAlerts.slice(0, 5)" 
          :key="`${alert.strategy_id}-${alert.timestamp}`"
          class="alert-item"
          :class="alert.type"
        >
          <div class="alert-content">
            <span class="alert-strategy">{{ alert.strategy_name }}</span>
            <span class="alert-message">{{ alert.reason }}</span>
          </div>
          <div class="alert-timestamp">
            {{ formatTimestamp(alert.timestamp) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Strategy Registration Modal -->
    <div v-if="showRegisterModal" class="modal-overlay" @click="closeRegisterModal">
      <div class="modal-content" @click.stop>
        <h3>Register New Strategy</h3>
        <form @submit.prevent="registerNewStrategy">
          <div class="form-group">
            <label for="strategy-id">Strategy ID:</label>
            <input 
              id="strategy-id"
              v-model="newStrategy.strategy_id" 
              type="text" 
              required 
              placeholder="unique-strategy-id"
            />
          </div>
          <div class="form-group">
            <label for="strategy-name">Strategy Name:</label>
            <input 
              id="strategy-name"
              v-model="newStrategy.strategy_name" 
              type="text" 
              required 
              placeholder="My Trading Strategy"
            />
          </div>
          <div class="form-group">
            <label for="min-win-rate">Minimum Win Rate (%):</label>
            <input 
              id="min-win-rate"
              v-model.number="newStrategy.min_win_rate" 
              type="number" 
              min="0" 
              max="100" 
              step="0.1"
              required 
            />
          </div>
          <div class="form-group">
            <label for="evaluation-period">Evaluation Period (trades):</label>
            <input 
              id="evaluation-period"
              v-model.number="newStrategy.evaluation_period" 
              type="number" 
              min="5" 
              max="100"
              required 
            />
          </div>
          <div class="form-group">
            <label for="initial-mode">Initial Mode:</label>
            <select id="initial-mode" v-model="newStrategy.initial_mode" required>
              <option value="live">Live Trading</option>
              <option value="paper">Paper Trading</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeRegisterModal">Cancel</button>
            <button type="submit" :disabled="isLoading">Register Strategy</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useStrategyPerformanceStore } from '../stores'
import type { 
  StrategyRegistration, 
  StrategyModeChangeRequest,
  TradingMode 
} from '../stores'

// Store
const strategyStore = useStrategyPerformanceStore()

// Reactive refs
const selectedStrategyId = ref<string>('')
const showRegisterModal = ref(false)
const newStrategy = ref<StrategyRegistration>({
  strategy_id: '',
  strategy_name: '',
  min_win_rate: 55.0,
  evaluation_period: 20,
  initial_mode: 'live'
})

// Computed properties
const {
  allStrategySummaries,
  selectedStrategySummary,
  recentAlerts,
  systemStatus,
  isLoading,
  formatMode,
  getModeColor,
  formatWinRate,
  formatCurrency
} = strategyStore

const evaluationPeriod = computed(() => selectedStrategySummary.value?.current_set_progress ? 20 : 20)
const minWinRate = computed(() => selectedStrategySummary.value ? 55.0 : 55.0)

// Methods
const onStrategyChanged = () => {
  if (selectedStrategyId.value) {
    strategyStore.selectStrategy(selectedStrategyId.value)
  }
}

const selectStrategy = (strategyId: string) => {
  selectedStrategyId.value = strategyId
  strategyStore.selectStrategy(strategyId)
}

const refreshData = async () => {
  try {
    await strategyStore.refreshData()
  } catch (error) {
    console.error('Failed to refresh strategy data:', error)
  }
}

const confirmModeChange = async (newMode: TradingMode, reason: string) => {
  if (!selectedStrategyId.value) return
  
  const confirmed = confirm(
    `Are you sure you want to change strategy mode to ${formatMode(newMode)}?\n\nReason: ${reason}`
  )
  
  if (!confirmed) return
  
  try {
    const request: StrategyModeChangeRequest = {
      new_mode: newMode,
      reason: reason
    }
    
    await strategyStore.changeStrategyMode(selectedStrategyId.value, request)
    
    // Show success message
    alert(`Strategy mode changed to ${formatMode(newMode)} successfully!`)
    
  } catch (error) {
    console.error('Failed to change strategy mode:', error)
    alert('Failed to change strategy mode. Please try again.')
  }
}

const registerNewStrategy = async () => {
  try {
    await strategyStore.registerStrategy(newStrategy.value)
    
    // Reset form and close modal
    newStrategy.value = {
      strategy_id: '',
      strategy_name: '',
      min_win_rate: 55.0,
      evaluation_period: 20,
      initial_mode: 'live'
    }
    showRegisterModal.value = false
    
    alert('Strategy registered successfully!')
    
  } catch (error) {
    console.error('Failed to register strategy:', error)
    alert('Failed to register strategy. Please check the form and try again.')
  }
}

const closeRegisterModal = () => {
  showRegisterModal.value = false
  newStrategy.value = {
    strategy_id: '',
    strategy_name: '',
    min_win_rate: 55.0,
    evaluation_period: 20,
    initial_mode: 'live'
  }
}

const clearAlerts = async () => {
  try {
    await strategyStore.clearPerformanceAlerts()
  } catch (error) {
    console.error('Failed to clear alerts:', error)
  }
}

const getWinRateClass = (winRate: number): string => {
  if (winRate >= 60) return 'excellent'
  if (winRate >= 55) return 'good'
  if (winRate >= 45) return 'warning'
  return 'poor'
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// Lifecycle
onMounted(async () => {
  try {
    await refreshData()
  } catch (error) {
    console.error('Failed to initialize strategy performance panel:', error)
  }
})

// Watch for strategy selection changes
watch(() => strategyStore.selectedStrategyId, (newId) => {
  if (newId && newId !== selectedStrategyId.value) {
    selectedStrategyId.value = newId
  }
})
</script>

<style scoped>
.strategy-performance-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--bg-primary);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-height: 100vh;
  overflow-y: auto;
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

.system-summary {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  flex-wrap: wrap;
}

.at-risk-strategies {
  color: var(--danger-color);
  font-weight: 600;
}

.system-status-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.system-status-indicator.healthy {
  background: #d1fae5;
  color: #065f46;
  border-color: #10b981;
}

.system-status-indicator.unhealthy {
  background: #fee2e2;
  color: #991b1b;
  border-color: #ef4444;
}

.refresh-btn {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--primary-color);
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  display: inline-block;
  transition: transform 0.5s;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.section-title {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-mode-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.strategy-mode-badge.success {
  background: #d1fae5;
  color: #065f46;
}

.strategy-mode-badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.strategy-mode-badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.strategy-selector {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.strategy-select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.register-strategy-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--primary-color);
  border-radius: 4px;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.register-strategy-btn:hover:not(:disabled) {
  background: var(--primary-color-dark);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.overview-card {
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.card-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.card-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.card-value.positive {
  color: var(--success-color);
}

.card-value.negative {
  color: var(--danger-color);
}

.card-value.excellent {
  color: #059669;
}

.card-value.good {
  color: #10b981;
}

.card-value.warning {
  color: #f59e0b;
}

.card-value.poor {
  color: #ef4444;
}

.card-change {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.at-risk {
  background: #fee2e2;
  color: #991b1b;
}

.status-badge.can-return {
  background: #d1fae5;
  color: #065f46;
}

.performance-chart {
  display: flex;
  align-items: end;
  gap: 0.5rem;
  height: 120px;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
  position: relative;
}

.performance-bar {
  flex: 1;
  background: var(--primary-color);
  border-radius: 4px 4px 0 0;
  min-height: 10px;
  position: relative;
  display: flex;
  align-items: end;
  justify-content: center;
  transition: all 0.2s;
}

.performance-bar.excellent {
  background: #059669;
}

.performance-bar.good {
  background: #10b981;
}

.performance-bar.warning {
  background: #f59e0b;
}

.performance-bar.poor {
  background: #ef4444;
}

.bar-label {
  font-size: 0.6rem;
  color: white;
  font-weight: 600;
  padding: 0.25rem;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 2px;
  margin-bottom: 2px;
}

.performance-threshold {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--danger-color);
  border-top: 2px dashed var(--danger-color);
}

.threshold-line {
  position: absolute;
  right: 1rem;
  top: -1rem;
  font-size: 0.75rem;
  color: var(--danger-color);
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.action-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.success {
  background: var(--success-color);
  color: white;
}

.action-btn.success:hover:not(:disabled) {
  background: #059669;
}

.action-btn.danger {
  background: var(--danger-color);
  color: white;
}

.action-btn.danger:hover:not(:disabled) {
  background: #dc2626;
}

.action-btn.warning {
  background: #f59e0b;
  color: white;
}

.action-btn.warning:hover:not(:disabled) {
  background: #d97706;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.strategy-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.strategy-card {
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.strategy-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.strategy-name {
  font-weight: 600;
  color: var(--text-primary);
}

.strategy-mode {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.strategy-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alert-item {
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border-left: 4px solid var(--primary-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-item.strategy_mode_change {
  border-left-color: var(--warning-color);
}

.alert-content {
  flex: 1;
}

.alert-strategy {
  font-weight: 600;
  color: var(--text-primary);
  margin-right: 0.5rem;
}

.alert-message {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.alert-timestamp {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.clear-alerts-btn {
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.clear-alerts-btn:hover {
  background: var(--danger-color);
  color: white;
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
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin: 0 0 1.5rem 0;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.modal-actions button {
  padding: 0.75rem 1.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.modal-actions button[type="button"] {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-actions button[type="submit"] {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.modal-actions button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.modal-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>