<template>
  <div class="dashboard-view">
    <!-- Use the shared Trading Dashboard Component -->
    <TradingDashboard
      :tradingStore="mockTradingStore"
      :connectionState="mockConnectionState"
      :realTimeData="mockRealTimeData"
      :api="mockApi"
      :allPositions="mockPositions"
      :fundedAccountsData="mockFundedAccounts"
      :allOrders="mockOrders"
      :appStore="mockAppStore"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { TradingDashboard } from '@trader-terminal/ui'

// Mock implementations for development
// In a real app, these would come from proper stores/services
const mockTradingStore = reactive({
  isMarketOpen: true,
  watchlist: ['MNQ1!', 'ES1!', 'NQ1!', 'RTY1!'],
  watchlistQuotes: [],
  activeSymbol: 'MNQ1!',
  account: {
    accountId: 'web-demo-001',
    broker: 'demo',
    totalEquity: 50000,
    cashBalance: 25000,
    buyingPower: 100000
  },
  currentQuote: {
    symbol: 'MNQ1!',
    price: 17850.0,
    change: 25.5,
    changePercent: 0.14
  },
  setActiveSymbol: (symbol: string) => {
    mockTradingStore.activeSymbol = symbol
    console.log('Symbol selected:', symbol)
  },
  removeFromWatchlist: (symbol: string) => {
    const index = mockTradingStore.watchlist.indexOf(symbol)
    if (index > -1) {
      mockTradingStore.watchlist.splice(index, 1)
    }
  },
  loadInitialData: async () => {
    console.log('Loading initial trading data...')
  }
})

const mockConnectionState = reactive({
  tradovate: true,
  schwab: false,
  tastytrade: true,
  topstepx: false
})

const mockRealTimeData = reactive({
  isConnected: true,
  initialize: async () => {
    console.log('Initializing real-time data connection...')
  },
  cleanup: () => {
    console.log('Cleaning up real-time data connection...')
  }
})

const mockApi = {
  placeOrder: async (orderData: any) => {
    console.log('Mock order placement:', orderData)
    return { success: true, data: { orderId: 'mock-' + Date.now() } }
  },
  checkConnectionStatus: async () => {
    console.log('Checking connection status...')
  }
}

const mockPositions = reactive({
  positions: [
    {
      symbol: 'MNQ1!',
      quantity: 2,
      avgPrice: 17825.0,
      marketValue: 35650.0,
      dayPnl: 150.0,
      totalPnl: 300.0
    }
  ],
  totalMarketValue: 35650.0,
  totalUnrealizedPnL: 300.0
})

const mockFundedAccounts = reactive({
  riskAlerts: []
})

const mockOrders = reactive({
  orders: [],
  workingOrders: [],
  filledOrders: []
})

const mockAppStore = reactive({
  platform: 'web'
})
</script>

<style scoped>
.dashboard-view {
  padding: 2rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.card {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin: 0 0 1rem 0;
  color: #1f2937;
}

.card p {
  margin: 0;
  color: #6b7280;
}
</style>