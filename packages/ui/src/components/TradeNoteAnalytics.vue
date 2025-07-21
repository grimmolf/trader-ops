<template>
  <div class="tradenote-analytics">
    <!-- Analytics Header -->
    <div class="analytics-header">
      <div class="header-title">
        <h4>Trading Analytics</h4>
        <div class="sync-status" v-if="syncStatus">
          <span class="status-indicator" :class="syncStatus.status"></span>
          Last sync: {{ formatDate(syncStatus.lastSync) }}
        </div>
      </div>
      
      <div class="header-actions">
        <select v-model="selectedTimeframe" @change="onTimeframeChanged" class="timeframe-select">
          <option value="7d">7 Days</option>
          <option value="30d">30 Days</option>
          <option value="90d">90 Days</option>
          <option value="1y">1 Year</option>
          <option value="all">All Time</option>
        </select>
        
        <button 
          class="sync-btn"
          @click="syncWithTradeNote"
          :disabled="isSyncing"
          title="Sync latest data from TradeNote"
        >
          <span class="btn-icon" :class="{ spinning: isSyncing }">⟲</span>
          {{ isSyncing ? 'Syncing...' : 'Sync' }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="analytics-loading">
      <div class="loading-spinner"></div>
      <p>Loading analytics data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="analytics-error">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="refreshAnalytics" class="retry-btn">Retry</button>
    </div>

    <!-- Analytics Content -->
    <div v-else class="analytics-content">
      <!-- Key Metrics Overview -->
      <div class="metrics-overview">
        <div class="metric-card" :class="getPnLClass(statistics.totalPnL)">
          <div class="metric-value">
            ${{ formatCurrency(statistics.totalPnL) }}
          </div>
          <div class="metric-label">Total P&L</div>
          <div class="metric-change" v-if="statistics.pnlChange">
            <span :class="getPnLClass(statistics.pnlChange)">
              {{ statistics.pnlChange > 0 ? '+' : '' }}{{ formatCurrency(statistics.pnlChange) }}
            </span>
            <span class="change-period">({{ selectedTimeframe }})</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-value">{{ statistics.totalTrades || 0 }}</div>
          <div class="metric-label">Total Trades</div>
          <div class="metric-change" v-if="statistics.tradesChange">
            <span class="neutral">
              {{ statistics.tradesChange > 0 ? '+' : '' }}{{ statistics.tradesChange }}
            </span>
            <span class="change-period">({{ selectedTimeframe }})</span>
          </div>
        </div>

        <div class="metric-card" :class="getWinRateClass(statistics.winRate)">
          <div class="metric-value">{{ formatPercentage(statistics.winRate) }}%</div>
          <div class="metric-label">Win Rate</div>
          <div class="metric-change" v-if="statistics.winRateChange">
            <span :class="getWinRateClass(statistics.winRateChange)">
              {{ statistics.winRateChange > 0 ? '+' : '' }}{{ formatPercentage(statistics.winRateChange) }}%
            </span>
            <span class="change-period">({{ selectedTimeframe }})</span>
          </div>
        </div>

        <div class="metric-card" :class="getPnLClass(statistics.avgTradeSize)">
          <div class="metric-value">${{ formatCurrency(statistics.avgTradeSize) }}</div>
          <div class="metric-label">Avg Trade Size</div>
          <div class="metric-change" v-if="statistics.avgTradeSizeChange">
            <span :class="getPnLClass(statistics.avgTradeSizeChange)">
              {{ statistics.avgTradeSizeChange > 0 ? '+' : '' }}${{ formatCurrency(statistics.avgTradeSizeChange) }}
            </span>
            <span class="change-period">({{ selectedTimeframe }})</span>
          </div>
        </div>
      </div>

      <!-- Trading Performance Charts -->
      <div class="performance-charts">
        <div class="chart-container">
          <div class="chart-header">
            <h5>P&L Over Time</h5>
            <div class="chart-controls">
              <button 
                v-for="period in chartPeriods" 
                :key="period.value"
                @click="selectedChartPeriod = period.value"
                :class="{ active: selectedChartPeriod === period.value }"
                class="period-btn"
              >
                {{ period.label }}
              </button>
            </div>
          </div>
          <div class="chart-placeholder">
            <!-- Placeholder for chart - would integrate with Chart.js or similar -->
            <canvas ref="pnlChart" width="400" height="200"></canvas>
          </div>
        </div>

        <div class="chart-container">
          <div class="chart-header">
            <h5>Win/Loss Distribution</h5>
          </div>
          <div class="chart-placeholder">
            <canvas ref="winLossChart" width="400" height="200"></canvas>
          </div>
        </div>
      </div>

      <!-- Detailed Statistics -->
      <div class="detailed-statistics">
        <div class="stats-section">
          <h5>Trading Performance</h5>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">Best Day:</span>
              <span class="stat-value profit">${{ formatCurrency(statistics.bestDay) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Worst Day:</span>
              <span class="stat-value loss">${{ formatCurrency(statistics.worstDay) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Average Daily P&L:</span>
              <span class="stat-value" :class="getPnLClass(statistics.avgDailyPnL)">
                ${{ formatCurrency(statistics.avgDailyPnL) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Largest Win:</span>
              <span class="stat-value profit">${{ formatCurrency(statistics.largestWin) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Largest Loss:</span>
              <span class="stat-value loss">${{ formatCurrency(Math.abs(statistics.largestLoss)) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Profit Factor:</span>
              <span class="stat-value" :class="getProfitFactorClass(statistics.profitFactor)">
                {{ formatNumber(statistics.profitFactor, 2) }}
              </span>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h5>Risk Metrics</h5>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">Sharpe Ratio:</span>
              <span class="stat-value" :class="getSharpeRatioClass(statistics.sharpeRatio)">
                {{ formatNumber(statistics.sharpeRatio, 2) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Max Drawdown:</span>
              <span class="stat-value loss">{{ formatPercentage(statistics.maxDrawdown) }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Recovery Factor:</span>
              <span class="stat-value" :class="getRecoveryFactorClass(statistics.recoveryFactor)">
                {{ formatNumber(statistics.recoveryFactor, 2) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Consecutive Wins:</span>
              <span class="stat-value">{{ statistics.maxConsecutiveWins || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Consecutive Losses:</span>
              <span class="stat-value">{{ statistics.maxConsecutiveLosses || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Time in Trade:</span>
              <span class="stat-value">{{ formatDuration(statistics.avgTimeInTrade) }}</span>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h5>Trading Activity</h5>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">Trading Days:</span>
              <span class="stat-value">{{ statistics.tradingDays || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Trades/Day:</span>
              <span class="stat-value">{{ formatNumber(statistics.avgTradesPerDay, 1) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Most Active Symbol:</span>
              <span class="stat-value">{{ statistics.mostActiveSymbol || 'N/A' }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Total Commission:</span>
              <span class="stat-value loss">${{ formatCurrency(statistics.totalCommission) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Commission %:</span>
              <span class="stat-value">{{ formatPercentage(statistics.commissionPercentage) }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Paper vs Live:</span>
              <span class="stat-value">
                {{ statistics.paperTrades || 0 }} / {{ statistics.liveTrades || 0 }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- External TradeNote Link -->
      <div class="external-link-section">
        <button @click="openTradeNote" class="open-tradenote-btn">
          <span class="external-icon">🔗</span>
          Open TradeNote Dashboard
        </button>
        <p class="link-description">
          View detailed trade journal, advanced analytics, and trade notes in TradeNote
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useTradeNoteStore } from '../stores/tradenote'

// Store
const tradeNoteStore = useTradeNoteStore()

// Reactive data
const isLoading = ref(false)
const isSyncing = ref(false)
const error = ref(null)
const selectedTimeframe = ref('30d')
const selectedChartPeriod = ref('30d')
const statistics = ref({})

// Chart references
const pnlChart = ref(null)
const winLossChart = ref(null)

// Chart periods
const chartPeriods = [
  { value: '7d', label: '7D' },
  { value: '30d', label: '30D' },
  { value: '90d', label: '90D' },
  { value: '1y', label: '1Y' }
]

// Sync status
const syncStatus = computed(() => tradeNoteStore.syncStatus)

// Load analytics data
async function loadAnalytics() {
  isLoading.value = true
  error.value = null
  
  try {
    const response = await tradeNoteStore.getTradeStatistics(selectedTimeframe.value)
    
    if (response.success) {
      statistics.value = response.data || {}
    } else {
      error.value = response.message || 'Failed to load analytics data'
    }
  } catch (err) {
    console.error('Error loading analytics:', err)
    error.value = 'Failed to load analytics data'
  } finally {
    isLoading.value = false
  }
}

// Sync with TradeNote
async function syncWithTradeNote() {
  isSyncing.value = true
  
  try {
    const response = await tradeNoteStore.syncData()
    
    if (response.success) {
      // Reload analytics after sync
      await loadAnalytics()
    } else {
      error.value = response.message || 'Sync failed'
    }
  } catch (err) {
    console.error('Error syncing with TradeNote:', err)
    error.value = 'Sync failed'
  } finally {
    isSyncing.value = false
  }
}

// Event handlers
function onTimeframeChanged() {
  loadAnalytics()
}

function refreshAnalytics() {
  loadAnalytics()
}

function openTradeNote() {
  const url = tradeNoteStore.config.base_url
  window.electron.openExternal(url)
}

// Utility functions for CSS classes
function getPnLClass(value) {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return 'neutral'
}

function getWinRateClass(value) {
  if (value >= 60) return 'excellent'
  if (value >= 50) return 'good'
  if (value >= 40) return 'fair'
  return 'poor'
}

function getProfitFactorClass(value) {
  if (value >= 2) return 'excellent'
  if (value >= 1.5) return 'good'
  if (value >= 1) return 'fair'
  return 'poor'
}

function getSharpeRatioClass(value) {
  if (value >= 2) return 'excellent'
  if (value >= 1) return 'good'
  if (value >= 0.5) return 'fair'
  return 'poor'
}

function getRecoveryFactorClass(value) {
  if (value >= 3) return 'excellent'
  if (value >= 2) return 'good'
  if (value >= 1) return 'fair'
  return 'poor'
}

// Formatting functions
function formatCurrency(value) {
  if (value == null) return '0.00'
  return Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function formatPercentage(value) {
  if (value == null) return '0.0'
  return (value * 100).toFixed(1)
}

function formatNumber(value, decimals = 0) {
  if (value == null) return '0'
  return value.toFixed(decimals)
}

function formatDuration(minutes) {
  if (!minutes) return '0m'
  
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins}m`
}

function formatDate(dateString) {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Watchers
watch(selectedTimeframe, () => {
  loadAnalytics()
})

// Lifecycle
onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.tradenote-analytics {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 16px;
  color: #e5e5e5;
}

/* Header */
.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
}

.header-title h4 {
  margin: 0 0 4px 0;
  color: #fff;
  font-size: 18px;
}

.sync-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.online {
  background: #22c55e;
}

.status-indicator.syncing {
  background: #f59e0b;
  animation: pulse 1.5s infinite;
}

.status-indicator.offline {
  background: #ef4444;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeframe-select {
  background: #2a2a2a;
  border: 1px solid #444;
  color: #e5e5e5;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.sync-btn {
  background: #0ea5e9;
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.sync-btn:hover {
  background: #0284c7;
}

.sync-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Loading/Error States */
.analytics-loading,
.analytics-error {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #333;
  border-top: 3px solid #0ea5e9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.error-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.retry-btn {
  background: #0ea5e9;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
}

/* Metrics Overview */
.metrics-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 16px;
  text-align: center;
}

.metric-card.profit {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.metric-card.loss {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.metric-card.excellent {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.metric-card.good {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.metric-card.fair {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.metric-card.poor {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #fff;
}

.metric-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}

.metric-change {
  font-size: 11px;
}

.change-period {
  color: #666;
}

/* Performance Charts */
.performance-charts {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-container {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  overflow: hidden;
}

.chart-header {
  padding: 12px 16px;
  background: #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-header h5 {
  margin: 0;
  color: #fff;
  font-size: 14px;
}

.chart-controls {
  display: flex;
  gap: 4px;
}

.period-btn {
  background: #444;
  border: 1px solid #555;
  color: #e5e5e5;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 10px;
  cursor: pointer;
}

.period-btn.active,
.period-btn:hover {
  background: #0ea5e9;
  border-color: #0ea5e9;
}

.chart-placeholder {
  padding: 16px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

/* Detailed Statistics */
.detailed-statistics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stats-section {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 16px;
}

.stats-section h5 {
  margin: 0 0 12px 0;
  color: #fff;
  font-size: 14px;
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
}

.stats-grid {
  display: grid;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.stat-label {
  color: #888;
  font-size: 12px;
}

.stat-value {
  font-weight: 500;
  font-size: 12px;
}

.stat-value.profit {
  color: #22c55e;
}

.stat-value.loss {
  color: #ef4444;
}

.stat-value.neutral {
  color: #888;
}

.stat-value.excellent {
  color: #10b981;
}

.stat-value.good {
  color: #22c55e;
}

.stat-value.fair {
  color: #f59e0b;
}

.stat-value.poor {
  color: #ef4444;
}

/* External Link Section */
.external-link-section {
  text-align: center;
  padding: 20px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
}

.open-tradenote-btn {
  background: #0ea5e9;
  border: none;
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 auto 8px;
}

.open-tradenote-btn:hover {
  background: #0284c7;
}

.external-icon {
  font-size: 16px;
}

.link-description {
  color: #888;
  font-size: 12px;
  margin: 0;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .performance-charts {
    grid-template-columns: 1fr;
  }
  
  .metrics-overview {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}

@media (max-width: 768px) {
  .detailed-statistics {
    grid-template-columns: 1fr;
  }
  
  .analytics-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .header-actions {
    justify-content: space-between;
  }
}
</style>