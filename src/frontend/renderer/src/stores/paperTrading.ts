import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Paper Trading Types
export interface PaperTradingAccount {
  id: string
  name: string
  broker: string
  mode: 'sandbox' | 'simulator' | 'hybrid'
  initialBalance: number
  currentBalance: number
  dayPnL: number
  totalPnL: number
  buyingPower: number
  positions: Record<string, PaperPosition>
  createdAt: string
  lastUpdated: string
}

export interface PaperPosition {
  symbol: string
  assetType: 'stock' | 'option' | 'future' | 'crypto' | 'forex'
  quantity: number
  avgPrice: number
  marketPrice: number
  unrealizedPnL: number
  realizedPnL: number
  dayPnL: number
  costBasis: number
  multiplier: number
  openedAt: string
  lastUpdated: string
}

export interface PaperOrder {
  id: string
  accountId: string
  symbol: string
  assetType: 'stock' | 'option' | 'future' | 'crypto' | 'forex'
  action: 'buy' | 'sell' | 'buy_to_open' | 'sell_to_open' | 'buy_to_close' | 'sell_to_close'
  orderType: 'market' | 'limit' | 'stop' | 'stop_limit'
  quantity: number
  price?: number
  stopPrice?: number
  filledQuantity: number
  avgFillPrice: number
  status: 'pending' | 'working' | 'filled' | 'partially_filled' | 'cancelled' | 'rejected' | 'expired'
  broker: string
  strategy?: string
  comment?: string
  createdAt: string
  updatedAt: string
  filledAt?: string
}

export interface PaperFill {
  id: string
  orderId: string
  accountId: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  commission: number
  fees: number
  slippage: number
  timestamp: string
  broker: string
}

export interface PaperTradingMetrics {
  accountId: string
  periodStart: string
  periodEnd: string
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  avgWin: number
  avgLoss: number
  largestWin: number
  largestLoss: number
  totalPnL: number
  grossProfit: number
  grossLoss: number
  profitFactor: number
  maxDrawdown: number
  totalCommissions: number
  totalVolume: number
  avgTradeDuration?: string
}

export const usePaperTradingStore = defineStore('paperTrading', () => {
  // State
  const accounts = ref<Map<string, PaperTradingAccount>>(new Map())
  const activeAccountId = ref<string | null>(null)
  const orders = ref<PaperOrder[]>([])
  const fills = ref<PaperFill[]>([])
  const metrics = ref<Map<string, PaperTradingMetrics>>(new Map())
  const isLoading = ref(false)
  const lastError = ref<string | null>(null)

  // Getters
  const activeAccount = computed(() => 
    activeAccountId.value ? accounts.value.get(activeAccountId.value) : null
  )

  const allAccounts = computed(() => 
    Array.from(accounts.value.values())
  )

  const activeAccountOrders = computed(() => 
    activeAccountId.value 
      ? orders.value.filter(order => order.accountId === activeAccountId.value)
      : []
  )

  const activeAccountFills = computed(() => 
    activeAccountId.value 
      ? fills.value.filter(fill => fill.accountId === activeAccountId.value)
      : []
  )

  const activeAccountPositions = computed(() => 
    activeAccount.value ? Object.values(activeAccount.value.positions) : []
  )

  const openPositions = computed(() => 
    activeAccountPositions.value.filter(pos => pos.quantity !== 0)
  )

  const totalPnL = computed(() => 
    activeAccountPositions.value.reduce((total, pos) => total + pos.unrealizedPnL, 0)
  )

  const todaysPnL = computed(() => 
    activeAccountPositions.value.reduce((total, pos) => total + pos.dayPnL, 0)
  )

  const currentMetrics = computed(() => 
    activeAccountId.value ? metrics.value.get(activeAccountId.value) : null
  )

  // Actions
  async function loadAccounts() {
    try {
      isLoading.value = true
      lastError.value = null

      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest('/api/paper-trading/accounts')
        if (response && Array.isArray(response)) {
          accounts.value.clear()
          response.forEach(account => {
            accounts.value.set(account.id, account)
          })

          // Set first account as active if none selected
          if (!activeAccountId.value && response.length > 0) {
            activeAccountId.value = response[0].id
          }

          console.log(`Loaded ${response.length} paper trading accounts`)
        }
      }
    } catch (error) {
      lastError.value = `Failed to load paper trading accounts: ${error}`
      console.error('Failed to load paper trading accounts:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function loadAccountData(accountId: string) {
    try {
      isLoading.value = true
      lastError.value = null

      if (window.electronAPI) {
        // Load orders
        const ordersResponse = await window.electronAPI.apiRequest(
          `/api/paper-trading/accounts/${accountId}/orders?limit=100`
        )
        if (ordersResponse && Array.isArray(ordersResponse)) {
          orders.value = ordersResponse
        }

        // Load fills
        const fillsResponse = await window.electronAPI.apiRequest(
          `/api/paper-trading/accounts/${accountId}/fills?limit=100`
        )
        if (fillsResponse && Array.isArray(fillsResponse)) {
          fills.value = fillsResponse
        }

        // Load metrics
        const metricsResponse = await window.electronAPI.apiRequest(
          `/api/paper-trading/accounts/${accountId}/metrics`
        )
        if (metricsResponse) {
          metrics.value.set(accountId, metricsResponse)
        }

        console.log(`Loaded data for paper trading account: ${accountId}`)
      }
    } catch (error) {
      lastError.value = `Failed to load account data: ${error}`
      console.error('Failed to load account data:', error)
    } finally {
      isLoading.value = false
    }
  }

  function setActiveAccount(accountId: string) {
    if (accounts.value.has(accountId)) {
      activeAccountId.value = accountId
      loadAccountData(accountId)
      console.log(`Switched to paper trading account: ${accountId}`)
    }
  }

  async function submitPaperOrder(orderRequest: {
    symbol: string
    action: string
    quantity: number
    orderType?: string
    price?: number
    stopPrice?: number
    strategy?: string
    comment?: string
  }) {
    try {
      isLoading.value = true
      lastError.value = null

      if (!activeAccountId.value) {
        throw new Error('No active paper trading account selected')
      }

      const requestBody = {
        ...orderRequest,
        accountGroup: `paper_${activeAccount.value?.broker || 'simulator'}`,
        paperMode: activeAccount.value?.mode || 'simulator'
      }

      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest('/api/paper-trading/alerts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestBody)
        })

        if (response && response.status === 'success') {
          // Refresh account data
          await loadAccountData(activeAccountId.value)
          console.log('Paper order submitted successfully:', response)
          return response
        } else {
          throw new Error(response?.message || 'Unknown error')
        }
      }

      throw new Error('Electron API not available')
    } catch (error) {
      lastError.value = `Failed to submit paper order: ${error}`
      console.error('Failed to submit paper order:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function cancelPaperOrder(orderId: string) {
    try {
      isLoading.value = true
      lastError.value = null

      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest(
          `/api/paper-trading/orders/${orderId}/cancel`,
          { method: 'POST' }
        )

        if (response && response.status === 'success') {
          // Update local order status
          const order = orders.value.find(o => o.id === orderId)
          if (order) {
            order.status = 'cancelled'
            order.updatedAt = new Date().toISOString()
          }
          console.log('Paper order cancelled successfully:', orderId)
          return response
        } else {
          throw new Error(response?.message || 'Unknown error')
        }
      }

      throw new Error('Electron API not available')
    } catch (error) {
      lastError.value = `Failed to cancel paper order: ${error}`
      console.error('Failed to cancel paper order:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function flattenAllPositions() {
    try {
      isLoading.value = true
      lastError.value = null

      if (!activeAccountId.value) {
        throw new Error('No active paper trading account selected')
      }

      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest(
          `/api/paper-trading/accounts/${activeAccountId.value}/flatten`,
          { method: 'POST' }
        )

        if (response && response.status === 'success') {
          // Refresh account data
          await loadAccountData(activeAccountId.value)
          console.log('All positions flattened successfully:', response)
          return response
        } else {
          throw new Error(response?.message || 'Unknown error')
        }
      }

      throw new Error('Electron API not available')
    } catch (error) {
      lastError.value = `Failed to flatten positions: ${error}`
      console.error('Failed to flatten positions:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function resetAccount(accountId: string) {
    try {
      isLoading.value = true
      lastError.value = null

      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest(
          `/api/paper-trading/accounts/${accountId}/reset`,
          { method: 'POST' }
        )

        if (response && response.status === 'success') {
          // Refresh account data
          await loadAccounts()
          if (accountId === activeAccountId.value) {
            await loadAccountData(accountId)
          }
          console.log('Paper trading account reset successfully:', accountId)
          return response
        } else {
          throw new Error(response?.message || 'Unknown error')
        }
      }

      throw new Error('Electron API not available')
    } catch (error) {
      lastError.value = `Failed to reset account: ${error}`
      console.error('Failed to reset account:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function updateAccountFromWebSocket(accountUpdate: Partial<PaperTradingAccount>) {
    if (accountUpdate.id && accounts.value.has(accountUpdate.id)) {
      const account = accounts.value.get(accountUpdate.id)!
      accounts.value.set(accountUpdate.id, { ...account, ...accountUpdate })
    }
  }

  function addOrderFromWebSocket(order: PaperOrder) {
    // Remove old order if exists, add new one
    const existingIndex = orders.value.findIndex(o => o.id === order.id)
    if (existingIndex >= 0) {
      orders.value[existingIndex] = order
    } else {
      orders.value.unshift(order)
    }
  }

  function addFillFromWebSocket(fill: PaperFill) {
    // Add fill if it doesn't exist
    const exists = fills.value.some(f => f.id === fill.id)
    if (!exists) {
      fills.value.unshift(fill)
    }
  }

  function clearError() {
    lastError.value = null
  }

  // Initialize paper trading data
  async function initialize() {
    try {
      await loadAccounts()
      if (activeAccountId.value) {
        await loadAccountData(activeAccountId.value)
      }
    } catch (error) {
      console.error('Failed to initialize paper trading store:', error)
    }
  }

  return {
    // State
    accounts,
    activeAccountId,
    orders,
    fills,
    metrics,
    isLoading,
    lastError,

    // Getters
    activeAccount,
    allAccounts,
    activeAccountOrders,
    activeAccountFills,
    activeAccountPositions,
    openPositions,
    totalPnL,
    todaysPnL,
    currentMetrics,

    // Actions
    loadAccounts,
    loadAccountData,
    setActiveAccount,
    submitPaperOrder,
    cancelPaperOrder,
    flattenAllPositions,
    resetAccount,
    updateAccountFromWebSocket,
    addOrderFromWebSocket,
    addFillFromWebSocket,
    clearError,
    initialize
  }
})