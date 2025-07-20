/**
 * Real-time Data Synchronization Composable
 * 
 * Provides reactive real-time data management for quotes, positions, orders,
 * and account information from multiple broker feeds.
 */

import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { api, connectionState, type Quote, type Position, type Account, type Order } from '../services/api'

// Real-time data stores
const quotes = reactive<Map<string, Quote>>(new Map())
const positions = reactive<Map<string, Position>>(new Map())
const accounts = reactive<Map<string, Account>>(new Map())
const orders = reactive<Map<string, Order>>(new Map())
const fundedAccounts = reactive<Map<string, any>>(new Map())

// Subscription tracking
const subscribedSymbols = ref<Set<string>>(new Set())
const subscriptionCallbacks = reactive<Map<string, ((data: any) => void)[]>>(new Map())

// Connection status
const isConnected = computed(() => connectionState.websocket)
const feedsConnected = computed(() => ({
  tradovate: connectionState.tradovate,
  schwab: connectionState.schwab,
  tastytrade: connectionState.tastytrade,
  topstepx: connectionState.topstepx
}))

/**
 * Main real-time data composable
 */
export function useRealTimeData() {
  let wsConnected = false

  /**
   * Initialize real-time data connection
   */
  const initialize = async () => {
    // Check initial connection status
    await api.checkConnectionStatus()

    // Connect to WebSocket
    api.connectWebSocket(handleWebSocketMessage)
    wsConnected = true

    // Load initial data
    await loadInitialData()
  }

  /**
   * Handle incoming WebSocket messages
   */
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'quote':
        handleQuoteUpdate(data.data)
        break
      case 'position':
        handlePositionUpdate(data.data)
        break
      case 'account':
        handleAccountUpdate(data.data)
        break
      case 'order':
        handleOrderUpdate(data.data)
        break
      case 'funded_account':
        handleFundedAccountUpdate(data.data)
        break
      case 'connection_status':
        handleConnectionStatusUpdate(data.data)
        break
      default:
        console.log('Unknown message type:', data.type)
    }

    // Trigger callbacks for this message type
    const callbacks = subscriptionCallbacks.get(data.type) || []
    callbacks.forEach(callback => callback(data))
  }

  /**
   * Load initial data from API
   */
  const loadInitialData = async () => {
    try {
      // Load accounts
      const accountsResponse = await api.getAccounts()
      if (accountsResponse.success && accountsResponse.data) {
        accountsResponse.data.forEach(account => {
          accounts.set(`${account.feed}:${account.accountNumber}`, account)
        })
      }

      // Load all positions
      const positionsResponse = await api.getAllPositions()
      if (positionsResponse.success && positionsResponse.data) {
        positionsResponse.data.forEach(position => {
          positions.set(`${position.feed}:${position.accountNumber}:${position.symbol}`, position)
        })
      }

      // Load funded accounts
      const fundedAccountsResponse = await api.getFundedAccounts()
      if (fundedAccountsResponse.success && fundedAccountsResponse.data) {
        fundedAccountsResponse.data.forEach(account => {
          fundedAccounts.set(`${account.provider}:${account.accountNumber}`, account)
        })
      }

      // Load recent orders
      const ordersResponse = await api.getOrders()
      if (ordersResponse.success && ordersResponse.data) {
        ordersResponse.data.forEach(order => {
          orders.set(`${order.feed}:${order.orderId}`, order)
        })
      }

    } catch (error) {
      console.error('Error loading initial data:', error)
    }
  }

  /**
   * Handle quote updates
   */
  const handleQuoteUpdate = (quote: Quote) => {
    quotes.set(quote.symbol, quote)
  }

  /**
   * Handle position updates
   */
  const handlePositionUpdate = (position: Position) => {
    const key = `${position.feed}:${position.accountNumber}:${position.symbol}`
    if (position.quantity === 0) {
      positions.delete(key)
    } else {
      positions.set(key, position)
    }
  }

  /**
   * Handle account updates
   */
  const handleAccountUpdate = (account: Account) => {
    accounts.set(`${account.feed}:${account.accountNumber}`, account)
  }

  /**
   * Handle order updates
   */
  const handleOrderUpdate = (order: Order) => {
    orders.set(`${order.feed}:${order.orderId}`, order)
  }

  /**
   * Handle funded account updates
   */
  const handleFundedAccountUpdate = (account: any) => {
    fundedAccounts.set(`${account.provider}:${account.accountNumber}`, account)
  }

  /**
   * Handle connection status updates
   */
  const handleConnectionStatusUpdate = (status: any) => {
    Object.assign(connectionState, status)
  }

  /**
   * Subscribe to market data for symbols
   */
  const subscribeToSymbols = (symbols: string[], feeds?: string[]) => {
    const newSymbols = symbols.filter(symbol => !subscribedSymbols.value.has(symbol))
    
    if (newSymbols.length > 0) {
      api.subscribeToMarketData(newSymbols, feeds)
      newSymbols.forEach(symbol => subscribedSymbols.value.add(symbol))
    }
  }

  /**
   * Unsubscribe from market data
   */
  const unsubscribeFromSymbols = (symbols: string[]) => {
    const symbolsToUnsubscribe = symbols.filter(symbol => subscribedSymbols.value.has(symbol))
    
    if (symbolsToUnsubscribe.length > 0) {
      api.unsubscribeFromMarketData(symbolsToUnsubscribe)
      symbolsToUnsubscribe.forEach(symbol => subscribedSymbols.value.delete(symbol))
    }
  }

  /**
   * Subscribe to specific data type updates
   */
  const subscribe = (type: string, callback: (data: any) => void) => {
    const callbacks = subscriptionCallbacks.get(type) || []
    callbacks.push(callback)
    subscriptionCallbacks.set(type, callbacks)

    // Return unsubscribe function
    return () => {
      const currentCallbacks = subscriptionCallbacks.get(type) || []
      const index = currentCallbacks.indexOf(callback)
      if (index !== -1) {
        currentCallbacks.splice(index, 1)
        subscriptionCallbacks.set(type, currentCallbacks)
      }
    }
  }

  /**
   * Cleanup when component unmounts
   */
  const cleanup = () => {
    if (wsConnected) {
      api.disconnect()
      wsConnected = false
    }
    quotes.clear()
    subscribedSymbols.value.clear()
    subscriptionCallbacks.clear()
  }

  return {
    // Data stores
    quotes: computed(() => Object.fromEntries(quotes)),
    positions: computed(() => Object.fromEntries(positions)),
    accounts: computed(() => Object.fromEntries(accounts)),
    orders: computed(() => Object.fromEntries(orders)),
    fundedAccounts: computed(() => Object.fromEntries(fundedAccounts)),
    
    // Connection status
    isConnected,
    feedsConnected,
    connectionState,
    
    // Subscription management
    subscribedSymbols: computed(() => Array.from(subscribedSymbols.value)),
    subscribeToSymbols,
    unsubscribeFromSymbols,
    subscribe,
    
    // Lifecycle
    initialize,
    cleanup
  }
}

/**
 * Composable for specific symbol quotes
 */
export function useQuotes(symbols: string[], feeds?: string[]) {
  const { quotes, subscribeToSymbols, unsubscribeFromSymbols, isConnected } = useRealTimeData()

  onMounted(() => {
    subscribeToSymbols(symbols, feeds)
  })

  onUnmounted(() => {
    unsubscribeFromSymbols(symbols)
  })

  // Watch for symbol changes
  watch(() => symbols, (newSymbols, oldSymbols) => {
    if (oldSymbols) {
      unsubscribeFromSymbols(oldSymbols)
    }
    subscribeToSymbols(newSymbols, feeds)
  })

  const symbolQuotes = computed(() => {
    const result: Record<string, Quote> = {}
    symbols.forEach(symbol => {
      const quote = quotes.value[symbol]
      if (quote) {
        result[symbol] = quote
      }
    })
    return result
  })

  return {
    quotes: symbolQuotes,
    isConnected,
    hasData: computed(() => Object.keys(symbolQuotes.value).length > 0)
  }
}

/**
 * Composable for account positions
 */
export function usePositions(accountNumber?: string, feed?: string) {
  const { positions, accounts, isConnected } = useRealTimeData()

  const filteredPositions = computed(() => {
    const result: Position[] = []
    
    for (const [key, position] of Object.entries(positions.value)) {
      if (accountNumber && position.accountNumber !== accountNumber) continue
      if (feed && position.feed !== feed) continue
      result.push(position)
    }
    
    return result
  })

  const totalMarketValue = computed(() => {
    return filteredPositions.value.reduce((total, position) => total + position.marketValue, 0)
  })

  const totalUnrealizedPnL = computed(() => {
    return filteredPositions.value.reduce((total, position) => total + position.unrealizedPnL, 0)
  })

  const accountInfo = computed(() => {
    if (!accountNumber || !feed) return null
    return accounts.value[`${feed}:${accountNumber}`] || null
  })

  return {
    positions: filteredPositions,
    totalMarketValue,
    totalUnrealizedPnL,
    accountInfo,
    isConnected,
    hasPositions: computed(() => filteredPositions.value.length > 0)
  }
}

/**
 * Composable for funded account monitoring
 */
export function useFundedAccounts() {
  const { fundedAccounts, isConnected } = useRealTimeData()

  const activeAccounts = computed(() => {
    return Object.values(fundedAccounts.value).filter(account => account.status === 'active')
  })

  const riskAlerts = computed(() => {
    const alerts: Array<{ account: any, type: string, message: string }> = []
    
    Object.values(fundedAccounts.value).forEach(account => {
      // Daily loss approaching limit
      if (account.dailyLoss / account.maxDailyLoss > 0.8) {
        alerts.push({
          account,
          type: 'warning',
          message: `Daily loss approaching limit: $${account.dailyLoss.toFixed(2)} / $${account.maxDailyLoss.toFixed(2)}`
        })
      }

      // Total loss approaching limit
      if (account.totalLoss / account.maxTotalLoss > 0.8) {
        alerts.push({
          account,
          type: 'warning',
          message: `Total loss approaching limit: $${account.totalLoss.toFixed(2)} / $${account.maxTotalLoss.toFixed(2)}`
        })
      }

      // Account breached
      if (account.status === 'breached') {
        alerts.push({
          account,
          type: 'error',
          message: `Account breached - trading suspended`
        })
      }
    })

    return alerts
  })

  return {
    fundedAccounts: computed(() => Object.values(fundedAccounts.value)),
    activeAccounts,
    riskAlerts,
    isConnected,
    hasAccounts: computed(() => Object.keys(fundedAccounts.value).length > 0)
  }
}

/**
 * Composable for order management
 */
export function useOrders(accountNumber?: string, feed?: string) {
  const { orders, isConnected } = useRealTimeData()

  const filteredOrders = computed(() => {
    const result: Order[] = []
    
    for (const [key, order] of Object.entries(orders.value)) {
      if (accountNumber && order.accountNumber !== accountNumber) continue
      if (feed && order.feed !== feed) continue
      result.push(order)
    }
    
    // Sort by timestamp (most recent first)
    return result.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  })

  const workingOrders = computed(() => {
    return filteredOrders.value.filter(order => 
      ['pending', 'working', 'partial'].includes(order.status.toLowerCase())
    )
  })

  const filledOrders = computed(() => {
    return filteredOrders.value.filter(order => 
      order.status.toLowerCase() === 'filled'
    )
  })

  return {
    orders: filteredOrders,
    workingOrders,
    filledOrders,
    isConnected,
    hasOrders: computed(() => filteredOrders.value.length > 0),
    hasWorkingOrders: computed(() => workingOrders.value.length > 0)
  }
}

// Global real-time data instance
export const globalRealTimeData = useRealTimeData()