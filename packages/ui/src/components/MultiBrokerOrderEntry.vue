<!--
Multi-Broker Order Entry Component

Enhanced order entry interface supporting multiple brokers, accounts, 
and intelligent order routing with risk management.
-->

<template>
  <div class="multi-broker-order-entry">
    <!-- Header with Symbol and Quote -->
    <div class="order-header">
      <div class="header-left">
        <h3>Order Entry</h3>
        <div class="symbol-info">
          <span class="symbol">{{ symbol || 'No Symbol' }}</span>
          <div v-if="bestQuote" class="quick-quote">
            <span class="bid">{{ formatPrice(bestQuote.bid) }}</span>
            <span class="separator">×</span>
            <span class="ask">{{ formatPrice(bestQuote.ask) }}</span>
            <span class="spread" :class="getSpreadClass()">
              {{ formatSpread(bestQuote.ask - bestQuote.bid) }}
            </span>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <div class="feed-selector">
          <label>Feed:</label>
          <select v-model="selectedFeed" class="feed-select">
            <option value="auto">Auto Route</option>
            <option v-for="feed in availableFeeds" :key="feed" :value="feed">
              {{ getFeedDisplayName(feed) }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Account Selection -->
    <div class="account-section">
      <div class="account-selector">
        <label>Account:</label>
        <select v-model="selectedAccountKey" class="account-select" :disabled="!hasAccounts">
          <option value="" disabled>Select Account</option>
          <optgroup v-for="group in groupedAccounts" :key="group.feed" :label="group.label">
            <option 
              v-for="account in group.accounts" 
              :key="`${account.feed}:${account.accountNumber}`"
              :value="`${account.feed}:${account.accountNumber}`"
            >
              {{ account.nickname || account.accountNumber }} 
              ({{ formatCurrency(account.buyingPower || account.balance) }})
            </option>
          </optgroup>
        </select>
      </div>
      
      <!-- Account Info Display -->
      <div v-if="selectedAccount" class="account-info">
        <div class="account-detail">
          <span class="detail-label">Buying Power:</span>
          <span class="detail-value">{{ formatCurrency(selectedAccount.buyingPower || selectedAccount.balance) }}</span>
        </div>
        <div v-if="isFundedAccount" class="account-detail risk-warning">
          <span class="detail-label">Daily Remaining:</span>
          <span class="detail-value" :class="getDailyRiskClass()">
            {{ formatCurrency(getDailyRiskRemaining()) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Order Type and Side -->
    <div class="order-controls">
      <div class="side-buttons">
        <button 
          @click="orderSide = 'buy'"
          class="side-btn buy"
          :class="{ active: orderSide === 'buy' }"
        >
          BUY
        </button>
        <button 
          @click="orderSide = 'sell'"
          class="side-btn sell"
          :class="{ active: orderSide === 'sell' }"
        >
          SELL
        </button>
      </div>
      
      <div class="type-selector">
        <label>Type:</label>
        <select v-model="orderType" class="form-select">
          <option value="market">Market</option>
          <option value="limit">Limit</option>
          <option value="stop">Stop Market</option>
          <option value="stop_limit">Stop Limit</option>
        </select>
      </div>
    </div>

    <!-- Order Parameters -->
    <div class="order-params">
      <div class="param-row">
        <label>Quantity:</label>
        <div class="quantity-input">
          <button @click="adjustQuantity(-1)" class="qty-btn">-</button>
          <input 
            v-model.number="quantity" 
            type="number" 
            class="form-input qty-input" 
            min="1" 
            :max="maxQuantity"
          />
          <button @click="adjustQuantity(1)" class="qty-btn">+</button>
        </div>
        <div class="quantity-presets">
          <button 
            v-for="preset in quantityPresets" 
            :key="preset"
            @click="quantity = preset"
            class="preset-btn"
            :class="{ active: quantity === preset }"
          >
            {{ preset }}
          </button>
        </div>
      </div>
      
      <div v-if="needsPrice" class="param-row">
        <label>{{ getPriceLabel() }}:</label>
        <div class="price-input">
          <input 
            v-model.number="price" 
            type="number" 
            class="form-input price-input-field" 
            step="0.01"
            :placeholder="getSuggestedPrice()"
          />
          <div class="price-buttons">
            <button @click="setQuotePrice('bid')" class="quote-btn" :disabled="!bestQuote">
              Bid
            </button>
            <button @click="setQuotePrice('mid')" class="quote-btn" :disabled="!bestQuote">
              Mid
            </button>
            <button @click="setQuotePrice('ask')" class="quote-btn" :disabled="!bestQuote">
              Ask
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="orderType.includes('stop')" class="param-row">
        <label>Stop Price:</label>
        <input 
          v-model.number="stopPrice" 
          type="number" 
          class="form-input" 
          step="0.01"
          :placeholder="getSuggestedStopPrice()"
        />
      </div>
      
      <div class="param-row">
        <label>Time in Force:</label>
        <select v-model="timeInForce" class="form-select">
          <option value="day">Day</option>
          <option value="gtc">GTC</option>
          <option value="ioc">IOC</option>
          <option value="fok">FOK</option>
        </select>
      </div>
    </div>

    <!-- Order Preview -->
    <div v-if="orderPreview" class="order-preview">
      <div class="preview-header">
        <span>Order Preview</span>
        <span class="estimated-cost">Est. Cost: {{ formatCurrency(orderPreview.estimatedCost) }}</span>
      </div>
      <div class="preview-details">
        <div class="preview-row">
          <span>{{ orderPreview.action }}</span>
          <span>{{ quantity }} {{ symbol }}</span>
        </div>
        <div class="preview-row">
          <span>{{ orderType.toUpperCase() }}{{ price ? ` @ ${formatPrice(price)}` : '' }}</span>
          <span>via {{ getFeedDisplayName(orderPreview.selectedFeed) }}</span>
        </div>
        <div v-if="orderPreview.warnings.length > 0" class="preview-warnings">
          <div v-for="warning in orderPreview.warnings" :key="warning" class="warning-item">
            ⚠️ {{ warning }}
          </div>
        </div>
      </div>
    </div>

    <!-- Submit Button -->
    <div class="submit-section">
      <button 
        @click="submitOrder" 
        class="submit-btn" 
        :class="submitButtonClass"
        :disabled="!canSubmit || submitting"
      >
        <span v-if="submitting" class="loading-spinner"></span>
        {{ submitButtonText }}
      </button>
      
      <!-- Risk Check Display -->
      <div v-if="riskCheck" class="risk-check" :class="riskCheck.level">
        <div class="risk-header">
          <span class="risk-icon">{{ getRiskIcon(riskCheck.level) }}</span>
          <span class="risk-title">{{ riskCheck.title }}</span>
        </div>
        <div v-if="riskCheck.messages.length > 0" class="risk-messages">
          <div v-for="message in riskCheck.messages" :key="message" class="risk-message">
            {{ message }}
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Orders -->
    <div v-if="recentOrders.length > 0" class="recent-orders">
      <div class="recent-header">
        <span>Recent Orders</span>
        <button @click="showAllOrders = !showAllOrders" class="toggle-btn">
          {{ showAllOrders ? 'Hide' : 'Show All' }}
        </button>
      </div>
      <div class="orders-list">
        <div 
          v-for="order in displayedRecentOrders" 
          :key="order.orderId"
          class="order-item"
          :class="order.status.toLowerCase()"
        >
          <div class="order-main">
            <span class="order-symbol">{{ order.symbol }}</span>
            <span class="order-side" :class="order.side">{{ order.side.toUpperCase() }}</span>
            <span class="order-qty">{{ order.quantity }}</span>
            <span class="order-price">{{ order.price ? formatPrice(order.price) : 'MKT' }}</span>
          </div>
          <div class="order-meta">
            <span class="order-status">{{ order.status }}</span>
            <span class="order-feed">{{ order.feed.toUpperCase() }}</span>
            <span class="order-time">{{ formatTime(order.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRealTimeData, usePositions, useFundedAccounts, useOrders } from '../composables'
import { api, connectionState, type Quote, type Account, type OrderRequest } from '../services/api'

const props = defineProps<{
  symbol?: string
  preselectedAccount?: string
  preselectedFeed?: string
}>()

const emit = defineEmits<{
  'order-submitted': [order: any]
  'order-error': [error: string]
}>()

// Composables
const realTimeData = useRealTimeData()
const allPositions = usePositions()
const fundedAccountsData = useFundedAccounts()
const ordersData = useOrders()

// Form state
const selectedFeed = ref(props.preselectedFeed || 'auto')
const selectedAccountKey = ref(props.preselectedAccount || '')
const orderSide = ref<'buy' | 'sell'>('buy')
const orderType = ref<'market' | 'limit' | 'stop' | 'stop_limit'>('market')
const quantity = ref(1)
const price = ref(0)
const stopPrice = ref(0)
const timeInForce = ref<'day' | 'gtc' | 'ioc' | 'fok'>('day')
const submitting = ref(false)
const showAllOrders = ref(false)

// Computed properties
const availableFeeds = computed(() => {
  const feeds = []
  if (connectionState.tradovate) feeds.push('tradovate')
  if (connectionState.schwab) feeds.push('schwab')
  if (connectionState.tastytrade) feeds.push('tastytrade')
  return feeds
})

const allAccounts = computed(() => {
  return Object.values(realTimeData.accounts.value) as Account[]
})

const hasAccounts = computed(() => allAccounts.value.length > 0)

const groupedAccounts = computed(() => {
  const groups: Array<{ feed: string; label: string; accounts: Account[] }> = []
  
  const feedGroups = allAccounts.value.reduce((acc, account) => {
    if (!acc[account.feed]) {
      acc[account.feed] = []
    }
    acc[account.feed].push(account)
    return acc
  }, {} as Record<string, Account[]>)
  
  Object.entries(feedGroups).forEach(([feed, accounts]) => {
    groups.push({
      feed,
      label: getFeedDisplayName(feed),
      accounts: accounts.sort((a, b) => (a.nickname || a.accountNumber).localeCompare(b.nickname || b.accountNumber))
    })
  })
  
  return groups.sort((a, b) => a.label.localeCompare(b.label))
})

const selectedAccount = computed(() => {
  if (!selectedAccountKey.value) return null
  const [feed, accountNumber] = selectedAccountKey.value.split(':')
  return allAccounts.value.find(acc => acc.feed === feed && acc.accountNumber === accountNumber) || null
})

const isFundedAccount = computed(() => {
  if (!selectedAccount.value) return false
  return fundedAccountsData.fundedAccounts.value.some(
    acc => acc.accountNumber === selectedAccount.value?.accountNumber
  )
})

const quotes = computed(() => {
  if (!props.symbol) return {}
  return realTimeData.quotes.value
})

const bestQuote = computed(() => {
  if (!props.symbol) return null
  return quotes.value[props.symbol] || null
})

const needsPrice = computed(() => {
  return orderType.value === 'limit' || orderType.value === 'stop_limit'
})

const maxQuantity = computed(() => {
  if (!selectedAccount.value || !bestQuote.value) return 999999
  const buyingPower = selectedAccount.value.buyingPower || selectedAccount.value.balance || 0
  const estimatedPrice = price.value || bestQuote.value.ask || bestQuote.value.last || 100
  return Math.floor(buyingPower / estimatedPrice)
})

const quantityPresets = computed(() => {
  const max = maxQuantity.value
  const presets = [1, 5, 10, 25, 50, 100]
  return presets.filter(preset => preset <= max).slice(0, 6)
})

const orderPreview = computed(() => {
  if (!props.symbol || !selectedAccount.value || quantity.value <= 0) return null
  
  const estimatedPrice = getEstimatedPrice()
  const estimatedCost = quantity.value * estimatedPrice
  const selectedOrderFeed = selectedFeed.value === 'auto' ? getBestFeed() : selectedFeed.value
  
  const warnings = []
  
  // Check buying power
  const buyingPower = selectedAccount.value.buyingPower || selectedAccount.value.balance || 0
  if (estimatedCost > buyingPower) {
    warnings.push(`Insufficient buying power. Need ${formatCurrency(estimatedCost)}, have ${formatCurrency(buyingPower)}`)
  }
  
  // Check funded account risks
  if (isFundedAccount.value) {
    const fundedAcc = fundedAccountsData.fundedAccounts.value.find(
      acc => acc.accountNumber === selectedAccount.value?.accountNumber
    )
    if (fundedAcc) {
      const remainingDaily = fundedAcc.maxDailyLoss - Math.abs(fundedAcc.dailyLoss)
      if (estimatedCost > remainingDaily * 0.1) { // 10% of remaining
        warnings.push('Large position relative to daily loss limit')
      }
    }
  }
  
  return {
    action: `${orderSide.value.toUpperCase()} ${orderType.value.toUpperCase()}`,
    estimatedCost,
    selectedFeed: selectedOrderFeed,
    warnings
  }
})

const riskCheck = computed(() => {
  if (!orderPreview.value) return null
  
  const warnings = orderPreview.value.warnings
  if (warnings.length === 0) {
    return {
      level: 'safe',
      title: 'Order Ready',
      messages: []
    }
  }
  
  const hasInsufficientFunds = warnings.some(w => w.includes('Insufficient buying power'))
  const hasRiskWarnings = warnings.some(w => w.includes('Large position'))
  
  if (hasInsufficientFunds) {
    return {
      level: 'error',
      title: 'Cannot Place Order',
      messages: warnings.filter(w => w.includes('Insufficient'))
    }
  }
  
  if (hasRiskWarnings) {
    return {
      level: 'warning',
      title: 'Risk Warning',
      messages: warnings.filter(w => w.includes('Large position'))
    }
  }
  
  return {
    level: 'warning',
    title: 'Review Required',
    messages: warnings
  }
})

const canSubmit = computed(() => {
  return (
    props.symbol &&
    selectedAccount.value &&
    quantity.value > 0 &&
    (!needsPrice.value || price.value > 0) &&
    (!orderType.value.includes('stop') || stopPrice.value > 0) &&
    riskCheck.value?.level !== 'error'
  )
})

const submitButtonClass = computed(() => {
  if (!canSubmit.value) return 'disabled'
  if (riskCheck.value?.level === 'error') return 'error'
  if (riskCheck.value?.level === 'warning') return 'warning'
  return orderSide.value === 'buy' ? 'buy' : 'sell'
})

const submitButtonText = computed(() => {
  if (submitting.value) return 'Submitting...'
  if (!canSubmit.value) return 'Review Order'
  return `${orderSide.value.toUpperCase()} ${quantity.value} ${props.symbol || 'Symbol'}`
})

const recentOrders = computed(() => {
  return ordersData.orders.value
    .filter(order => order.symbol === props.symbol)
    .slice(0, showAllOrders.value ? 10 : 3)
})

const displayedRecentOrders = computed(() => recentOrders.value)

// Methods
function getFeedDisplayName(feed: string): string {
  const names: Record<string, string> = {
    tradovate: 'Tradovate',
    schwab: 'Charles Schwab',
    tastytrade: 'Tastytrade',
    topstepx: 'TopstepX'
  }
  return names[feed] || feed.toUpperCase()
}

function formatPrice(price: number): string {
  return price.toFixed(2)
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

function formatSpread(spread: number): string {
  return spread.toFixed(2)
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

function getSpreadClass(): string {
  if (!bestQuote.value) return ''
  const spread = bestQuote.value.ask - bestQuote.value.bid
  const price = bestQuote.value.last || bestQuote.value.ask
  const spreadPercent = (spread / price) * 100
  
  if (spreadPercent > 1) return 'wide-spread'
  if (spreadPercent > 0.5) return 'medium-spread'
  return 'tight-spread'
}

function getPriceLabel(): string {
  if (orderType.value === 'stop_limit') return 'Limit Price'
  return 'Price'
}

function getSuggestedPrice(): string {
  if (!bestQuote.value) return ''
  if (orderSide.value === 'buy') {
    return formatPrice(bestQuote.value.bid)
  } else {
    return formatPrice(bestQuote.value.ask)
  }
}

function getSuggestedStopPrice(): string {
  if (!bestQuote.value) return ''
  const currentPrice = bestQuote.value.last || bestQuote.value.ask
  const offset = orderSide.value === 'buy' ? 0.05 : -0.05
  return formatPrice(currentPrice + offset)
}

function setQuotePrice(type: 'bid' | 'mid' | 'ask'): void {
  if (!bestQuote.value) return
  
  switch (type) {
    case 'bid':
      price.value = bestQuote.value.bid
      break
    case 'ask':
      price.value = bestQuote.value.ask
      break
    case 'mid':
      price.value = (bestQuote.value.bid + bestQuote.value.ask) / 2
      break
  }
}

function adjustQuantity(delta: number): void {
  const newQty = quantity.value + delta
  if (newQty >= 1 && newQty <= maxQuantity.value) {
    quantity.value = newQty
  }
}

function getEstimatedPrice(): number {
  if (orderType.value === 'market') {
    return orderSide.value === 'buy' 
      ? (bestQuote.value?.ask || 0)
      : (bestQuote.value?.bid || 0)
  }
  return price.value || 0
}

function getBestFeed(): string {
  // Simple routing logic - can be enhanced
  if (connectionState.tradovate) return 'tradovate'
  if (connectionState.schwab) return 'schwab'
  if (connectionState.tastytrade) return 'tastytrade'
  return availableFeeds.value[0] || ''
}

function getDailyRiskRemaining(): number {
  if (!isFundedAccount.value) return 0
  const fundedAcc = fundedAccountsData.fundedAccounts.value.find(
    acc => acc.accountNumber === selectedAccount.value?.accountNumber
  )
  return fundedAcc ? fundedAcc.maxDailyLoss - Math.abs(fundedAcc.dailyLoss) : 0
}

function getDailyRiskClass(): string {
  const remaining = getDailyRiskRemaining()
  const fundedAcc = fundedAccountsData.fundedAccounts.value.find(
    acc => acc.accountNumber === selectedAccount.value?.accountNumber
  )
  if (!fundedAcc) return ''
  
  const percentage = (remaining / fundedAcc.maxDailyLoss) * 100
  if (percentage <= 10) return 'critical'
  if (percentage <= 25) return 'danger'
  if (percentage <= 50) return 'warning'
  return 'safe'
}

function getRiskIcon(level: string): string {
  const icons = {
    safe: '✅',
    warning: '⚠️',
    error: '❌'
  }
  return icons[level as keyof typeof icons] || '❓'
}

async function submitOrder(): Promise<void> {
  if (!canSubmit.value || submitting.value) return
  
  submitting.value = true
  
  try {
    const orderRequest: OrderRequest = {
      symbol: props.symbol!,
      side: orderSide.value,
      quantity: quantity.value,
      orderType: orderType.value,
      price: needsPrice.value ? price.value : undefined,
      stopPrice: orderType.value.includes('stop') ? stopPrice.value : undefined,
      timeInForce: timeInForce.value,
      accountNumber: selectedAccount.value!.accountNumber,
      feed: selectedFeed.value === 'auto' ? getBestFeed() : selectedFeed.value
    }
    
    const response = await api.placeOrder(orderRequest)
    
    if (response.success) {
      emit('order-submitted', response.data)
      
      // Reset form
      resetForm()
      
      console.log('Order submitted successfully:', response.data)
    } else {
      emit('order-error', response.error || 'Failed to submit order')
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    emit('order-error', errorMessage)
  } finally {
    submitting.value = false
  }
}

function resetForm(): void {
  quantity.value = 1
  price.value = 0
  stopPrice.value = 0
  orderType.value = 'market'
  timeInForce.value = 'day'
}

// Watchers
watch(() => props.symbol, (newSymbol) => {
  if (newSymbol && realTimeData.isConnected.value) {
    // Subscribe to this symbol's quotes
    realTimeData.subscribeToSymbols([newSymbol])
  }
})

watch(orderSide, () => {
  // Reset price when switching sides
  if (needsPrice.value && bestQuote.value) {
    setQuotePrice(orderSide.value === 'buy' ? 'bid' : 'ask')
  }
})

// Lifecycle
onMounted(() => {
  // Auto-select first account if none selected
  if (!selectedAccountKey.value && allAccounts.value.length > 0) {
    selectedAccountKey.value = `${allAccounts.value[0].feed}:${allAccounts.value[0].accountNumber}`
  }
  
  // Subscribe to symbol quotes if available
  if (props.symbol && realTimeData.isConnected.value) {
    realTimeData.subscribeToSymbols([props.symbol])
  }
})
</script>

<style scoped>
.multi-broker-order-entry {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  max-width: 400px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.header-left h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.symbol-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.symbol {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent-blue);
}

.quick-quote {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.bid { color: var(--accent-red); }
.ask { color: var(--accent-green); }
.separator { color: var(--text-secondary); }

.spread {
  font-size: 0.75rem;
  padding: 2px 4px;
  border-radius: 3px;
  background: var(--bg-tertiary);
}

.spread.tight-spread { background: var(--accent-green-light); }
.spread.medium-spread { background: var(--accent-yellow-light); }
.spread.wide-spread { background: var(--accent-red-light); }

.feed-selector {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.feed-selector label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.feed-select {
  padding: 4px 8px;
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.875rem;
}

.account-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.account-selector {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.account-selector label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.account-select {
  padding: 8px;
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.875rem;
}

.account-info {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 0.75rem;
}

.account-detail {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.detail-label {
  color: var(--text-secondary);
}

.detail-value {
  font-weight: 600;
}

.detail-value.safe { color: var(--accent-green); }
.detail-value.warning { color: var(--accent-yellow); }
.detail-value.danger { color: var(--accent-orange); }
.detail-value.critical { color: var(--accent-red); }

.order-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.side-buttons {
  display: flex;
  gap: 0.5rem;
}

.side-btn {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid var(--border-primary);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.side-btn:hover {
  background: var(--bg-hover);
}

.side-btn.buy.active {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: white;
}

.side-btn.sell.active {
  background: var(--accent-red);
  border-color: var(--accent-red);
  color: white;
}

.type-selector {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-selector label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.order-params {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.param-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-row label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.quantity-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.qty-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-primary);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
}

.qty-btn:hover {
  background: var(--bg-hover);
}

.qty-input {
  flex: 1;
  text-align: center;
  font-weight: 600;
}

.quantity-presets {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 4px 8px;
  border: 1px solid var(--border-primary);
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
}

.preset-btn:hover {
  background: var(--bg-hover);
}

.preset-btn.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.price-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.price-input-field {
  font-weight: 600;
}

.price-buttons {
  display: flex;
  gap: 0.25rem;
}

.quote-btn {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--border-primary);
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
}

.quote-btn:hover:not(:disabled) {
  background: var(--bg-hover);
}

.quote-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-input,
.form-select {
  padding: 8px;
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.875rem;
}

.order-preview {
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 6px;
  border: 1px solid var(--border-primary);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
}

.estimated-cost {
  color: var(--accent-blue);
}

.preview-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.preview-row {
  display: flex;
  justify-content: space-between;
}

.preview-warnings {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-primary);
}

.warning-item {
  color: var(--accent-orange);
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

.submit-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.submit-btn {
  padding: 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.submit-btn.buy {
  background: var(--accent-green);
  color: white;
}

.submit-btn.sell {
  background: var(--accent-red);
  color: white;
}

.submit-btn.warning {
  background: var(--accent-orange);
  color: white;
}

.submit-btn.error,
.submit-btn.disabled {
  background: var(--bg-hover);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.submit-btn:hover:not(.disabled):not(.error) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.risk-check {
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid;
}

.risk-check.safe {
  background: var(--accent-green-light);
  border-color: var(--accent-green);
  color: var(--accent-green-dark);
}

.risk-check.warning {
  background: var(--accent-orange-light);
  border-color: var(--accent-orange);
  color: var(--accent-orange-dark);
}

.risk-check.error {
  background: var(--accent-red-light);
  border-color: var(--accent-red);
  color: var(--accent-red-dark);
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.risk-messages {
  font-size: 0.75rem;
}

.risk-message {
  margin-bottom: 0.125rem;
}

.recent-orders {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.recent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 600;
}

.toggle-btn {
  padding: 4px 8px;
  border: 1px solid var(--border-primary);
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.order-item {
  padding: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 4px;
  border-left: 3px solid var(--border-primary);
}

.order-item.filled {
  border-left-color: var(--accent-green);
}

.order-item.working {
  border-left-color: var(--accent-blue);
}

.order-item.cancelled {
  border-left-color: var(--accent-red);
}

.order-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.order-side.buy { color: var(--accent-green); }
.order-side.sell { color: var(--accent-red); }

.order-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
</style>