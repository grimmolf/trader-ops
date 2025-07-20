<template>
  <div class="paper-trading-panel">
    <!-- Panel Header -->
    <div class="panel-header">
      <div class="header-title">
        <h3>Paper Trading</h3>
        <div class="account-summary" v-if="activeAccount">
          <span class="total-value">
            Balance: {{ formatCurrency(activeAccount.currentBalance) }}
          </span>
          <span class="daily-pnl" :class="{ negative: todaysPnL < 0 }">
            Day: {{ formatCurrency(todaysPnL) }}
          </span>
          <span class="total-pnl" :class="{ negative: totalPnL < 0 }">
            Total: {{ formatCurrency(totalPnL) }}
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <button 
          class="mode-indicator"
          :class="activeAccount?.mode"
          :title="`Mode: ${formatMode(activeAccount?.mode)}`"
        >
          {{ formatMode(activeAccount?.mode) }}
        </button>
        
        <button 
          class="refresh-btn"
          @click="refreshData"
          :disabled="isLoading"
          title="Refresh paper trading data"
        >
          <span class="btn-icon" :class="{ spinning: isLoading }">↻</span>
        </button>
      </div>
    </div>

    <!-- Account Selector -->
    <div class="account-selector-section">
      <h4 class="section-title">Paper Trading Account</h4>
      <div class="account-selector">
        <select 
          v-model="selectedAccountId" 
          @change="onAccountChanged"
          class="account-select"
          :disabled="isLoading"
        >
          <option value="">Select Account</option>
          <option 
            v-for="account in allAccounts" 
            :key="account.id" 
            :value="account.id"
          >
            {{ account.name }} ({{ formatMode(account.mode) }})
          </option>
        </select>
        
        <button 
          v-if="activeAccount"
          class="reset-account-btn"
          @click="confirmResetAccount"
          :disabled="isLoading"
          title="Reset account to initial state"
        >
          🔄 Reset
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div v-if="activeAccount" class="panel-content">
      <!-- Account Overview -->
      <div class="overview-section">
        <h4 class="section-title">Account Overview</h4>
        
        <div class="overview-grid">
          <div class="overview-card">
            <div class="card-label">Account Balance</div>
            <div class="card-value balance">{{ formatCurrency(activeAccount.currentBalance) }}</div>
            <div class="card-change">
              Initial: {{ formatCurrency(activeAccount.initialBalance) }}
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-label">Buying Power</div>
            <div class="card-value">{{ formatCurrency(activeAccount.buyingPower) }}</div>
            <div class="card-change">
              Available for trading
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-label">Today's P&L</div>
            <div class="card-value" :class="{ positive: todaysPnL > 0, negative: todaysPnL < 0 }">
              {{ formatCurrency(todaysPnL) }}
            </div>
            <div class="card-change">
              {{ todaysPnL >= 0 ? '+' : '' }}{{ ((todaysPnL / activeAccount.initialBalance) * 100).toFixed(2) }}%
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-label">Total P&L</div>
            <div class="card-value" :class="{ positive: totalPnL > 0, negative: totalPnL < 0 }">
              {{ formatCurrency(totalPnL) }}
            </div>
            <div class="card-change">
              {{ totalPnL >= 0 ? '+' : '' }}{{ ((totalPnL / activeAccount.initialBalance) * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- Positions -->
      <div class="positions-section">
        <h4 class="section-title">
          Open Positions ({{ openPositions.length }})
          <button 
            v-if="openPositions.length > 0"
            class="flatten-all-btn"
            @click="confirmFlattenAll"
            :disabled="isLoading"
            title="Close all positions"
          >
            🚨 Flatten All
          </button>
        </h4>
        
        <div v-if="openPositions.length === 0" class="no-positions">
          <div class="no-positions-icon">📊</div>
          <p>No open positions</p>
        </div>
        
        <div v-else class="positions-list">
          <div 
            v-for="position in openPositions" 
            :key="position.symbol"
            class="position-item"
            :class="{ positive: position.unrealizedPnL > 0, negative: position.unrealizedPnL < 0 }"
          >
            <div class="position-header">
              <span class="position-symbol">{{ position.symbol }}</span>
              <span class="position-type">{{ formatAssetType(position.assetType) }}</span>
              <span class="position-pnl">{{ formatCurrency(position.unrealizedPnL) }}</span>
            </div>
            <div class="position-details">
              <span>Qty: {{ position.quantity }}</span>
              <span>Avg: {{ formatPrice(position.avgPrice) }}</span>
              <span>Last: {{ formatPrice(position.marketPrice) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Metrics -->
      <div v-if="currentMetrics" class="performance-section">
        <h4 class="section-title">Performance Metrics</h4>
        
        <div class="performance-grid">
          <div class="perf-card">
            <div class="perf-label">Total Trades</div>
            <div class="perf-value">{{ currentMetrics.totalTrades }}</div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Win Rate</div>
            <div class="perf-value" :class="getWinRateClass(currentMetrics.winRate)">
              {{ currentMetrics.winRate.toFixed(1) }}%
            </div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Profit Factor</div>
            <div class="perf-value" :class="getProfitFactorClass(currentMetrics.profitFactor)">
              {{ currentMetrics.profitFactor.toFixed(2) }}
            </div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Max Drawdown</div>
            <div class="perf-value negative">
              {{ formatCurrency(currentMetrics.maxDrawdown) }}
            </div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Avg Win</div>
            <div class="perf-value positive">
              {{ formatCurrency(currentMetrics.avgWin) }}
            </div>
          </div>
          
          <div class="perf-card">
            <div class="perf-label">Avg Loss</div>
            <div class="perf-value negative">
              {{ formatCurrency(currentMetrics.avgLoss) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Orders -->
      <div class="orders-section">
        <h4 class="section-title">Recent Orders ({{ activeAccountOrders.length }})</h4>
        
        <div v-if="activeAccountOrders.length === 0" class="no-orders">
          <div class="no-orders-icon">📝</div>
          <p>No recent orders</p>
        </div>
        
        <div v-else class="orders-list">
          <div 
            v-for="order in activeAccountOrders.slice(0, 10)" 
            :key="order.id"
            class="order-item"
            :class="order.status"
          >
            <div class="order-header">
              <span class="order-symbol">{{ order.symbol }}</span>
              <span class="order-action" :class="order.action">{{ formatAction(order.action) }}</span>
              <span class="order-status" :class="order.status">{{ formatStatus(order.status) }}</span>
            </div>
            <div class="order-details">
              <span>{{ order.quantity }} @ {{ order.price ? formatPrice(order.price) : 'Market' }}</span>
              <span>{{ formatTime(order.createdAt) }}</span>
              <button 
                v-if="order.status === 'pending' || order.status === 'working'"
                class="cancel-order-btn"
                @click="cancelOrder(order.id)"
                :disabled="isLoading"
                title="Cancel order"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Fills -->
      <div class="fills-section">
        <h4 class="section-title">Recent Fills ({{ activeAccountFills.length }})</h4>
        
        <div v-if="activeAccountFills.length === 0" class="no-fills">
          <div class="no-fills-icon">✅</div>
          <p>No recent fills</p>
        </div>
        
        <div v-else class="fills-list">
          <div 
            v-for="fill in activeAccountFills.slice(0, 10)" 
            :key="fill.id"
            class="fill-item"
          >
            <div class="fill-header">
              <span class="fill-symbol">{{ fill.symbol }}</span>
              <span class="fill-side" :class="fill.side">{{ fill.side.toUpperCase() }}</span>
              <span class="fill-price">{{ formatPrice(fill.price) }}</span>
            </div>
            <div class="fill-details">
              <span>Qty: {{ fill.quantity }}</span>
              <span>Commission: {{ formatCurrency(fill.commission) }}</span>
              <span>{{ formatTime(fill.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Paper Trading Settings -->
      <div class="settings-section">
        <h4 class="section-title">Simulation Settings</h4>
        
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">Execution Mode</label>
            <select class="setting-select" disabled>
              <option :value="activeAccount.mode">{{ formatMode(activeAccount.mode) }}</option>
            </select>
            <div class="setting-description">
              {{ getModeDescription(activeAccount.mode) }}
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">Broker</label>
            <div class="setting-value">{{ formatBroker(activeAccount.broker) }}</div>
            <div class="setting-description">
              {{ getBrokerDescription(activeAccount.broker) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="actions-section">
        <h4 class="section-title">Quick Actions</h4>
        
        <div class="actions-grid">
          <button 
            class="action-button test-order-btn"
            @click="showTestOrderModal = true"
            :disabled="isLoading"
            title="Submit a test order"
          >
            <span class="action-icon">🧪</span>
            <span class="action-text">Test Order</span>
          </button>
          
          <button 
            class="action-button flatten-btn"
            @click="confirmFlattenAll"
            :disabled="openPositions.length === 0 || isLoading"
            title="Close all positions"
          >
            <span class="action-icon">🚨</span>
            <span class="action-text">Flatten All</span>
          </button>
          
          <button 
            class="action-button reset-btn"
            @click="confirmResetAccount"
            :disabled="isLoading"
            title="Reset account to initial state"
          >
            <span class="action-icon">🔄</span>
            <span class="action-text">Reset Account</span>
          </button>
          
          <button 
            class="action-button refresh-btn"
            @click="refreshData"
            :disabled="isLoading"
            title="Refresh data"
          >
            <span class="action-icon" :class="{ spinning: isLoading }">📊</span>
            <span class="action-text">
              {{ isLoading ? 'Loading...' : 'Refresh' }}
            </span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- No Account Selected State -->
    <div v-else-if="!isLoading" class="no-account-state">
      <div class="no-account-icon">📊</div>
      <div class="no-account-text">
        <h4>No Paper Trading Account Selected</h4>
        <p>Select a paper trading account to start simulated trading</p>
      </div>
      <button v-if="allAccounts.length === 0" @click="initializeStore" class="load-accounts-btn">
        Load Paper Trading Accounts
      </button>
    </div>

    <!-- Loading State -->
    <div v-else class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading paper trading data...</div>
    </div>

    <!-- Test Order Modal -->
    <div v-if="showTestOrderModal" class="modal-overlay" @click="showTestOrderModal = false">
      <div class="modal-content test-order-modal" @click.stop>
        <div class="modal-header">
          <h3>Submit Test Order</h3>
          <button class="modal-close" @click="showTestOrderModal = false">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="submitTestOrder" class="test-order-form">
            <div class="form-group">
              <label for="test-symbol">Symbol</label>
              <input 
                id="test-symbol"
                v-model="testOrder.symbol" 
                type="text" 
                placeholder="ES, NQ, AAPL, etc."
                required
              />
            </div>
            
            <div class="form-group">
              <label for="test-action">Action</label>
              <select id="test-action" v-model="testOrder.action" required>
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="test-quantity">Quantity</label>
              <input 
                id="test-quantity"
                v-model.number="testOrder.quantity" 
                type="number" 
                min="1"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="test-order-type">Order Type</label>
              <select id="test-order-type" v-model="testOrder.orderType">
                <option value="market">Market</option>
                <option value="limit">Limit</option>
              </select>
            </div>
            
            <div v-if="testOrder.orderType === 'limit'" class="form-group">
              <label for="test-price">Price</label>
              <input 
                id="test-price"
                v-model.number="testOrder.price" 
                type="number" 
                step="0.01"
              />
            </div>
            
            <div class="form-group">
              <label for="test-comment">Comment (Optional)</label>
              <input 
                id="test-comment"
                v-model="testOrder.comment" 
                type="text" 
                placeholder="Test order comment"
              />
            </div>
            
            <div class="form-actions">
              <button type="button" @click="showTestOrderModal = false" class="cancel-btn">
                Cancel
              </button>
              <button type="submit" :disabled="isLoading" class="submit-btn">
                {{ isLoading ? 'Submitting...' : 'Submit Test Order' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="lastError" class="error-display">
      <div class="error-message">
        <span class="error-icon">⚠️</span>
        {{ lastError }}
        <button class="error-close" @click="clearError">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { usePaperTradingStore } from '../src/stores/paperTrading'

// Paper trading store
const paperTradingStore = usePaperTradingStore()

// Local state
const selectedAccountId = ref<string>('')
const showTestOrderModal = ref(false)
const testOrder = ref({
  symbol: 'ES',
  action: 'buy',
  quantity: 1,
  orderType: 'market',
  price: undefined,
  comment: ''
})

// Computed properties from store
const {
  allAccounts,
  activeAccount,
  activeAccountOrders,
  activeAccountFills,
  openPositions,
  totalPnL,
  todaysPnL,
  currentMetrics,
  isLoading,
  lastError
} = paperTradingStore

// Methods
function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
  }).format(price)
}

function formatMode(mode?: string): string {
  switch (mode) {
    case 'sandbox': return 'Sandbox'
    case 'simulator': return 'Simulator'
    case 'hybrid': return 'Hybrid'
    default: return 'Unknown'
  }
}

function formatAssetType(type: string): string {
  switch (type) {
    case 'future': return 'Future'
    case 'stock': return 'Stock'
    case 'option': return 'Option'
    case 'crypto': return 'Crypto'
    case 'forex': return 'Forex'
    default: return type.toUpperCase()
  }
}

function formatAction(action: string): string {
  return action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatBroker(broker: string): string {
  switch (broker) {
    case 'tastytrade_sandbox': return 'Tastytrade Sandbox'
    case 'tradovate_demo': return 'Tradovate Demo'
    case 'simulator': return 'Internal Simulator'
    default: return broker.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString()
}

function getModeDescription(mode?: string): string {
  switch (mode) {
    case 'sandbox': return 'Uses real broker APIs with fake money'
    case 'simulator': return 'Internal simulation with market data'
    case 'hybrid': return 'Sandbox execution with simulated fills'
    default: return ''
  }
}

function getBrokerDescription(broker: string): string {
  switch (broker) {
    case 'tastytrade_sandbox': return 'Tastytrade sandbox environment'
    case 'tradovate_demo': return 'Tradovate demo account'
    case 'simulator': return 'Internal paper trading simulator'
    default: return 'Paper trading environment'
  }
}

function getWinRateClass(rate: number): string {
  if (rate >= 70) return 'excellent'
  if (rate >= 60) return 'good'
  if (rate >= 50) return 'average'
  return 'poor'
}

function getProfitFactorClass(factor: number): string {
  if (factor >= 2.0) return 'excellent'
  if (factor >= 1.5) return 'good'
  if (factor >= 1.0) return 'average'
  return 'poor'
}

// Event handlers
async function onAccountChanged() {
  if (selectedAccountId.value) {
    paperTradingStore.setActiveAccount(selectedAccountId.value)
  }
}

async function refreshData() {
  await paperTradingStore.loadAccounts()
  if (selectedAccountId.value) {
    await paperTradingStore.loadAccountData(selectedAccountId.value)
  }
}

async function submitTestOrder() {
  try {
    await paperTradingStore.submitPaperOrder({
      symbol: testOrder.value.symbol.toUpperCase(),
      action: testOrder.value.action,
      quantity: testOrder.value.quantity,
      orderType: testOrder.value.orderType,
      price: testOrder.value.price,
      comment: testOrder.value.comment || 'Test order'
    })
    
    showTestOrderModal.value = false
    
    // Reset form
    testOrder.value = {
      symbol: 'ES',
      action: 'buy',
      quantity: 1,
      orderType: 'market',
      price: undefined,
      comment: ''
    }
  } catch (error) {
    console.error('Failed to submit test order:', error)
  }
}

async function cancelOrder(orderId: string) {
  try {
    await paperTradingStore.cancelPaperOrder(orderId)
  } catch (error) {
    console.error('Failed to cancel order:', error)
  }
}

async function confirmFlattenAll() {
  if (openPositions.value.length === 0) return
  
  const confirmed = confirm(
    '⚠️ FLATTEN ALL POSITIONS ⚠️\n\n' +
    `This will close all ${openPositions.value.length} open position(s).\n` +
    'This action cannot be undone.\n\n' +
    'Are you sure you want to proceed?'
  )
  
  if (!confirmed) return
  
  try {
    await paperTradingStore.flattenAllPositions()
  } catch (error) {
    console.error('Failed to flatten positions:', error)
  }
}

async function confirmResetAccount() {
  if (!activeAccount.value) return
  
  const confirmed = confirm(
    '⚠️ RESET PAPER TRADING ACCOUNT ⚠️\n\n' +
    'This will reset the account to its initial state:\n' +
    '• Close all positions\n' +
    '• Cancel all orders\n' +
    '• Reset balance to initial amount\n' +
    '• Clear all trade history\n\n' +
    'This action cannot be undone.\n\n' +
    'Are you sure you want to proceed?'
  )
  
  if (!confirmed) return
  
  try {
    await paperTradingStore.resetAccount(activeAccount.value.id)
  } catch (error) {
    console.error('Failed to reset account:', error)
  }
}

function clearError() {
  paperTradingStore.clearError()
}

async function initializeStore() {
  await paperTradingStore.initialize()
}

// Lifecycle
onMounted(async () => {
  await paperTradingStore.initialize()
  
  // Select first account if available
  if (allAccounts.value.length > 0 && !selectedAccountId.value) {
    selectedAccountId.value = allAccounts.value[0].id
    await onAccountChanged()
  }
})

// Watch for accounts changes and auto-select first if none selected
watch(allAccounts, (newAccounts) => {
  if (newAccounts.length > 0 && !selectedAccountId.value) {
    selectedAccountId.value = newAccounts[0].id
    onAccountChanged()
  }
}, { immediate: true })

// Update selected account when activeAccountId changes
watch(() => paperTradingStore.activeAccountId, (newId) => {
  if (newId && newId !== selectedAccountId.value) {
    selectedAccountId.value = newId
  }
})
</script>

<style scoped>
.paper-trading-panel {
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

.account-summary {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  flex-wrap: wrap;
}

.daily-pnl.negative,
.total-pnl.negative {
  color: var(--danger-color);
}

.mode-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.mode-indicator.sandbox {
  background: #fef3c7;
  color: #92400e;
  border-color: #fbbf24;
}

.mode-indicator.simulator {
  background: #dbeafe;
  color: #1e40af;
  border-color: #60a5fa;
}

.mode-indicator.hybrid {
  background: #f3e8ff;
  color: #7c3aed;
  border-color: #a78bfa;
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

.account-selector {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.account-select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.overview-card {
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.card-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.card-value {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.card-value.balance {
  color: var(--primary-color);
}

.card-value.positive {
  color: #16a34a;
}

.card-value.negative {
  color: var(--danger-color);
}

.card-change {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.positions-list,
.orders-list,
.fills-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.position-item,
.order-item,
.fill-item {
  padding: 0.75rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  border-left: 3px solid var(--border-color);
}

.position-item.positive {
  border-left-color: #16a34a;
}

.position-item.negative {
  border-left-color: var(--danger-color);
}

.order-item.filled {
  border-left-color: #16a34a;
}

.order-item.cancelled,
.order-item.rejected {
  border-left-color: var(--danger-color);
}

.order-item.pending,
.order-item.working {
  border-left-color: #f59e0b;
}

.position-header,
.order-header,
.fill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.position-details,
.order-details,
.fill-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.order-action.buy,
.fill-side.buy {
  color: #16a34a;
}

.order-action.sell,
.fill-side.sell {
  color: var(--danger-color);
}

.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.perf-card {
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  text-align: center;
}

.perf-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.perf-value {
  font-size: 1.25rem;
  font-weight: 600;
}

.perf-value.excellent {
  color: #16a34a;
}

.perf-value.good {
  color: #22c55e;
}

.perf-value.average {
  color: #f59e0b;
}

.perf-value.poor {
  color: var(--danger-color);
}

.perf-value.positive {
  color: #16a34a;
}

.perf-value.negative {
  color: var(--danger-color);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.setting-item {
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.setting-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.setting-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.setting-value {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.setting-description {
  font-size: 0.75rem;
  color: var(--text-muted);
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

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.flatten-btn,
.flatten-all-btn {
  border-color: #f87171;
  color: #dc2626;
}

.flatten-btn:hover:not(:disabled),
.flatten-all-btn:hover:not(:disabled) {
  background: #fef2f2;
}

.no-positions,
.no-orders,
.no-fills,
.no-account-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
}

.no-positions-icon,
.no-orders-icon,
.no-fills-icon,
.no-account-icon {
  font-size: 2rem;
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
  max-width: 500px;
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

.test-order-form {
  padding: 1.5rem;
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

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.cancel-btn,
.submit-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.submit-btn {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.cancel-order-btn {
  padding: 0.25rem 0.5rem;
  background: var(--danger-color);
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
}

.error-display {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1100;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.error-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #dc2626;
  margin-left: auto;
}

.reset-account-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.refresh-btn .spinning {
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