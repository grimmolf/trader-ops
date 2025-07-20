<template>
  <div class="trading-dashboard">
    <!-- Header Bar -->
    <div class="header-bar">
      <div class="header-left">
        <div class="logo">
          <span class="logo-text">TraderTerminal</span>
        </div>
        <SymbolSearch @symbol-selected="onSymbolSelected" />
      </div>
      
      <div class="header-center">
        <div class="market-status" :class="{ 'open': tradingStore.isMarketOpen }">
          <div class="status-indicator"></div>
          <span>{{ tradingStore.isMarketOpen ? 'Market Open' : 'Market Closed' }}</span>
        </div>
        
        <!-- Connection Status Indicators -->
        <div class="connection-indicators">
          <div class="feed-status" :class="{ 'connected': connectionState.tradovate }" title="Tradovate">TV</div>
          <div class="feed-status" :class="{ 'connected': connectionState.schwab }" title="Charles Schwab">CS</div>
          <div class="feed-status" :class="{ 'connected': connectionState.tastytrade }" title="Tastytrade">TT</div>
          <div class="feed-status" :class="{ 'connected': connectionState.topstepx }" title="TopstepX">TS</div>
        </div>
      </div>
      
      <div class="header-right">
        <AccountInfo :account="tradingStore.account" />
        <div class="window-controls" v-if="showWindowControls">
          <button @click="minimizeWindow" class="window-btn minimize">−</button>
          <button @click="maximizeWindow" class="window-btn maximize">□</button>
          <button @click="closeWindow" class="window-btn close">×</button>
        </div>
      </div>
    </div>
    
    <!-- Main Layout -->
    <div class="main-layout">
      <!-- Left Panel -->
      <div class="left-panel" :style="{ width: leftPanelWidth + 'px' }">
        <div class="panel-tabs">
          <button 
            class="tab" 
            :class="{ active: activeLeftTab === 'watchlist' }"
            @click="activeLeftTab = 'watchlist'"
          >
            Watchlist
          </button>
          <button 
            class="tab" 
            :class="{ active: activeLeftTab === 'orders' }"
            @click="activeLeftTab = 'orders'"
          >
            Orders
          </button>
        </div>
        
        <div class="panel-content">
          <Watchlist 
            v-if="activeLeftTab === 'watchlist'"
            :symbols="tradingStore.watchlist" 
            :quotes="tradingStore.watchlistQuotes"
            :active-symbol="tradingStore.activeSymbol"
            @symbol-clicked="onSymbolSelected"
            @symbol-removed="onSymbolRemoved"
          />
          
          <OrderHistory 
            v-if="activeLeftTab === 'orders'"
            :orders="allOrders.orders"
            :working-orders="allOrders.workingOrders"
            :filled-orders="allOrders.filledOrders"
          />
        </div>
        
        <!-- Order Entry Panel -->
        <div class="order-panel">
          <OrderEntry 
            :symbol="tradingStore.activeSymbol" 
            :account="tradingStore.account"
            :current-quote="tradingStore.currentQuote"
            @order-submitted="onOrderSubmitted"
          />
        </div>
      </div>
      
      <!-- Resizer -->
      <div class="resizer left-resizer" @mousedown="startResize('left')"></div>
      
      <!-- Center Panel -->
      <div class="center-panel" :style="{ width: centerPanelWidth + 'px' }">
        <div class="chart-container">
          <TradingViewChart 
            :symbol="tradingStore.activeSymbol"
            :datafeed-url="datafeedUrl"
            @alert-created="onAlertCreated"
          />
        </div>
      </div>
      
      <!-- Resizer -->
      <div class="resizer right-resizer" @mousedown="startResize('right')"></div>
      
      <!-- Right Panel -->
      <div class="right-panel" :style="{ width: rightPanelWidth + 'px' }">
        <div class="panel-tabs">
          <button 
            class="tab" 
            :class="{ active: activeRightTab === 'positions' }"
            @click="activeRightTab = 'positions'"
          >
            Positions
          </button>
          <button 
            class="tab" 
            :class="{ active: activeRightTab === 'alerts' }"
            @click="activeRightTab = 'alerts'"
          >
            Alerts
          </button>
          <button 
            class="tab" 
            :class="{ active: activeRightTab === 'backtest' }"
            @click="activeRightTab = 'backtest'"
          >
            Backtest
          </button>
        </div>
        
        <div class="panel-content">
          <Positions 
            v-if="activeRightTab === 'positions'"
            :positions="allPositions.positions" 
            :total-market-value="allPositions.totalMarketValue"
            :total-unrealized-pnl="allPositions.totalUnrealizedPnL"
          />
          
          <AlertPanel 
            v-if="activeRightTab === 'alerts'"
            :alerts="fundedAccountsData.riskAlerts" 
          />
          
          <BacktestPanel 
            v-if="activeRightTab === 'backtest'"
            :symbol="tradingStore.activeSymbol"
          />
        </div>
      </div>
    </div>
    
    <!-- Bottom Panel (News Feed) -->
    <div class="bottom-panel" :style="{ height: bottomPanelHeight + 'px' }">
      <div class="resizer bottom-resizer" @mousedown="startResize('bottom')"></div>
      <NewsFeed :symbol="tradingStore.activeSymbol" />
    </div>
    
    <!-- Connection Status -->
    <div class="connection-status" :class="{ 'connected': realTimeData.isConnected }">
      <div class="status-dot"></div>
      <span>{{ realTimeData.isConnected ? 'Connected' : 'Disconnected' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTradingStore } from '../src/stores/trading'
import { useAppStore } from '../src/stores/app'
import { useRealTimeData, usePositions, useFundedAccounts, useOrders } from '../src/composables/useRealTimeData'
import { api, connectionState } from '../src/services/api'

// Import components (these will be created next)
import SymbolSearch from './SymbolSearch.vue'
import AccountInfo from './AccountInfo.vue'
import Watchlist from './Watchlist.vue'
import OrderEntry from './OrderEntry.vue'
import OrderHistory from './OrderHistory.vue'
import TradingViewChart from './TradingViewChart.vue'
import Positions from './Positions.vue'
import AlertPanel from './AlertPanel.vue'
import BacktestPanel from './BacktestPanel.vue'
import NewsFeed from './NewsFeed.vue'

// Stores
const tradingStore = useTradingStore()
const appStore = useAppStore()

// Real-time data
const realTimeData = useRealTimeData()
const allPositions = usePositions()
const fundedAccountsData = useFundedAccounts()
const allOrders = useOrders()

// Panel state
const activeLeftTab = ref('watchlist')
const activeRightTab = ref('positions')

// Panel dimensions
const leftPanelWidth = ref(300)
const rightPanelWidth = ref(350)
const bottomPanelHeight = ref(200)

const centerPanelWidth = computed(() => {
  return window.innerWidth - leftPanelWidth.value - rightPanelWidth.value - 20 // Account for resizers
})

// Configuration
const datafeedUrl = 'http://localhost:8080/udf'
const activeAlerts = ref([])
const showWindowControls = computed(() => appStore.platform === 'darwin')

// Resizing functionality
let isResizing = false
let resizeType = ''
let startX = 0
let startY = 0
let startWidth = 0
let startHeight = 0

function startResize(type: string) {
  isResizing = true
  resizeType = type
  
  if (type === 'left') {
    startX = event?.clientX || 0
    startWidth = leftPanelWidth.value
  } else if (type === 'right') {
    startX = event?.clientX || 0
    startWidth = rightPanelWidth.value
  } else if (type === 'bottom') {
    startY = event?.clientY || 0
    startHeight = bottomPanelHeight.value
  }
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = type === 'bottom' ? 'ns-resize' : 'ew-resize'
  document.body.style.userSelect = 'none'
}

function handleResize(event: MouseEvent) {
  if (!isResizing) return
  
  if (resizeType === 'left') {
    const deltaX = event.clientX - startX
    leftPanelWidth.value = Math.max(200, Math.min(600, startWidth + deltaX))
  } else if (resizeType === 'right') {
    const deltaX = event.clientX - startX
    rightPanelWidth.value = Math.max(250, Math.min(700, startWidth - deltaX))
  } else if (resizeType === 'bottom') {
    const deltaY = event.clientY - startY
    bottomPanelHeight.value = Math.max(100, Math.min(400, startHeight - deltaY))
  }
}

function stopResize() {
  isResizing = false
  resizeType = ''
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// Event handlers
function onSymbolSelected(symbol: string) {
  tradingStore.setActiveSymbol(symbol)
  console.log(`Symbol selected: ${symbol}`)
}

function onSymbolRemoved(symbol: string) {
  tradingStore.removeFromWatchlist(symbol)
}

async function onOrderSubmitted(orderData: any) {
  try {
    const response = await api.placeOrder({
      symbol: orderData.symbol,
      side: orderData.side,
      quantity: orderData.quantity,
      orderType: orderData.orderType,
      price: orderData.price,
      stopPrice: orderData.stopPrice,
      timeInForce: orderData.timeInForce || 'day',
      accountNumber: orderData.accountNumber,
      feed: orderData.feed
    })
    
    if (response.success) {
      console.log('Order submitted successfully:', response.data)
      // Order will appear in real-time orders via WebSocket
    } else {
      console.error('Failed to submit order:', response.error)
      // Show error notification
    }
  } catch (error) {
    console.error('Failed to submit order:', error)
    // Show error notification
  }
}

function onAlertCreated(alertData: any) {
  console.log('Alert created:', alertData)
  // Handle alert creation
}

// Window controls
async function minimizeWindow() {
  if (window.electronAPI) {
    await window.electronAPI.minimizeWindow()
  }
}

async function maximizeWindow() {
  if (window.electronAPI) {
    await window.electronAPI.maximizeWindow()
  }
}

async function closeWindow() {
  if (window.electronAPI) {
    await window.electronAPI.closeWindow()
  }
}

// Lifecycle
onMounted(async () => {
  try {
    // Initialize real-time data connection
    await realTimeData.initialize()
    
    // Load initial trading store data
    await tradingStore.loadInitialData()
    
    // Check connection status
    await api.checkConnectionStatus()
    
    console.log('Trading dashboard initialized')
  } catch (error) {
    console.error('Failed to initialize trading dashboard:', error)
  }
})

onUnmounted(() => {
  if (isResizing) {
    stopResize()
  }
  
  // Cleanup real-time data connections
  realTimeData.cleanup()
})
</script>

<style scoped>
.trading-dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
  overflow: hidden;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 50px;
  padding: 0 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
  -webkit-app-region: drag;
}

.header-left,
.header-center,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  -webkit-app-region: no-drag;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-blue);
}

.market-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  font-size: 12px;
  color: var(--text-secondary);
}

.market-status.open {
  color: var(--accent-green);
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
}

.market-status.open .status-indicator {
  background: var(--accent-green);
}

.connection-indicators {
  display: flex;
  gap: 4px;
}

.feed-status {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 18px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 500;
  border: 1px solid var(--border-primary);
}

.feed-status.connected {
  background: var(--accent-green);
  color: white;
  border-color: var(--accent-green);
}

.window-controls {
  display: flex;
  gap: 8px;
}

.window-btn {
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 3px;
  background: var(--bg-hover);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.window-btn:hover {
  background: var(--border-primary);
}

.window-btn.close:hover {
  background: var(--accent-red);
  color: white;
}

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
}

.right-panel {
  border-right: none;
  border-left: 1px solid var(--border-primary);
}

.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  min-width: 400px;
}

.chart-container {
  flex: 1;
  overflow: hidden;
}

.panel-tabs {
  display: flex;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-primary);
}

.tab {
  flex: 1;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  border-bottom: 2px solid transparent;
}

.tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.panel-content {
  flex: 1;
  overflow: hidden;
}

.order-panel {
  border-top: 1px solid var(--border-primary);
  background: var(--bg-tertiary);
}

.bottom-panel {
  position: relative;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
  min-height: 100px;
}

.resizer {
  background: transparent;
  position: relative;
  z-index: 1;
}

.left-resizer,
.right-resizer {
  width: 4px;
  cursor: ew-resize;
}

.left-resizer:hover,
.right-resizer:hover {
  background: var(--accent-blue);
}

.bottom-resizer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  cursor: ns-resize;
}

.bottom-resizer:hover {
  background: var(--accent-blue);
}

.connection-status {
  position: fixed;
  bottom: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  z-index: 1000;
}

.connection-status.connected {
  color: var(--accent-green);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-red);
}

.connection-status.connected .status-dot {
  background: var(--accent-green);
}
</style>