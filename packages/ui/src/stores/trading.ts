import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Account {
  id: string
  name: string
  type: 'brokerage' | 'funded' | 'paper'
  broker: 'tastytrade' | 'tradovate' | 'schwab' | 'topstepx' | 'simulator'
  balance: number
  buyingPower: number
  dayPnL: number
  totalPnL: number
  isActive: boolean
  status: 'active' | 'suspended' | 'restricted'
}

export interface Position {
  id: string
  symbol: string
  quantity: number
  avgPrice: number
  currentPrice: number
  marketValue: number
  unrealizedPnL: number
  realizedPnL: number
  dayPnL: number
  side: 'long' | 'short'
  account: string
  assetType: 'stock' | 'option' | 'future' | 'crypto'
}

export interface Quote {
  symbol: string
  price: number
  bid: number
  ask: number
  bidSize: number
  askSize: number
  change: number
  changePercent: number
  volume: number
  high: number
  low: number
  open: number
  close: number
  timestamp: number
}

export interface Order {
  id: string
  symbol: string
  quantity: number
  price: number
  stopPrice?: number
  type: 'market' | 'limit' | 'stop' | 'stop_limit'
  timeInForce: 'DAY' | 'GTC' | 'IOC' | 'FOK'
  side: 'buy' | 'sell'
  status: 'pending' | 'submitted' | 'filled' | 'cancelled' | 'rejected'
  filledQuantity: number
  avgFillPrice: number
  account: string
  strategy?: string
  timestamp: Date
  updatedAt: Date
}

export interface OrderRequest {
  symbol: string
  quantity: number
  price?: number
  stopPrice?: number
  type: 'market' | 'limit' | 'stop' | 'stop_limit'
  timeInForce?: 'DAY' | 'GTC' | 'IOC' | 'FOK'
  side: 'buy' | 'sell'
  account: string
  strategy?: string
}

export const useTradingStore = defineStore('trading', () => {
  // State
  const accounts = ref<Account[]>([])
  const positions = ref<Position[]>([])
  const orders = ref<Order[]>([])
  const quotes = ref<Record<string, Quote>>({})
  const activeAccountId = ref<string>('')
  const watchlist = ref<string[]>(['ES', 'NQ', 'YM', 'RTY'])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const connected = ref(false)

  // Computed
  const activeAccount = computed(() => 
    accounts.value.find(acc => acc.id === activeAccountId.value)
  )

  const activePositions = computed(() => 
    positions.value.filter(pos => pos.quantity !== 0)
  )

  const pendingOrders = computed(() => 
    orders.value.filter(order => order.status === 'pending' || order.status === 'submitted')
  )

  const totalPortfolioValue = computed(() => 
    positions.value.reduce((sum, pos) => sum + pos.marketValue, 0)
  )

  const totalUnrealizedPnL = computed(() => 
    positions.value.reduce((sum, pos) => sum + pos.unrealizedPnL, 0)
  )

  const totalDayPnL = computed(() => 
    positions.value.reduce((sum, pos) => sum + pos.dayPnL, 0)
  )

  const watchlistQuotes = computed(() => 
    watchlist.value.map(symbol => quotes.value[symbol]).filter(Boolean)
  )

  // Actions
  async function fetchAccounts() {
    try {
      loading.value = true
      // TODO: Replace with actual API call
      // const response = await api.getAccounts()
      // accounts.value = response.data
      
      // Mock data for now
      accounts.value = [
        {
          id: 'tastytrade_main',
          name: 'Tastytrade Main',
          type: 'brokerage',
          broker: 'tastytrade',
          balance: 50000,
          buyingPower: 48500,
          dayPnL: 125.50,
          totalPnL: 2450.75,
          isActive: true,
          status: 'active'
        },
        {
          id: 'topstep_eval',
          name: 'TopStep Evaluation',
          type: 'funded',
          broker: 'topstepx',
          balance: 150000,
          buyingPower: 150000,
          dayPnL: -85.25,
          totalPnL: 1850.00,
          isActive: false,
          status: 'active'
        }
      ]
      
      if (!activeAccountId.value && accounts.value.length > 0) {
        activeAccountId.value = accounts.value[0].id
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch accounts'
    } finally {
      loading.value = false
    }
  }

  async function fetchPositions() {
    try {
      // TODO: Replace with actual API call
      // const response = await api.getPositions(activeAccountId.value)
      // positions.value = response.data
      
      // Mock data for now
      positions.value = []
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch positions'
    }
  }

  async function fetchOrders() {
    try {
      // TODO: Replace with actual API call
      // const response = await api.getOrders(activeAccountId.value)
      // orders.value = response.data
      
      // Mock data for now
      orders.value = []
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch orders'
    }
  }

  async function submitOrder(orderRequest: OrderRequest): Promise<Order> {
    try {
      // TODO: Replace with actual API call
      // const response = await api.submitOrder(orderRequest)
      // const order = response.data
      
      // Mock order for now
      const order: Order = {
        id: Math.random().toString(36).substr(2, 9),
        ...orderRequest,
        timeInForce: orderRequest.timeInForce || 'DAY',
        status: 'pending',
        filledQuantity: 0,
        avgFillPrice: 0,
        timestamp: new Date(),
        updatedAt: new Date()
      }
      
      orders.value.unshift(order)
      return order
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to submit order'
      throw e
    }
  }

  async function cancelOrder(orderId: string) {
    try {
      // TODO: Replace with actual API call
      // await api.cancelOrder(orderId)
      
      const order = orders.value.find(o => o.id === orderId)
      if (order) {
        order.status = 'cancelled'
        order.updatedAt = new Date()
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to cancel order'
    }
  }

  function setActiveAccount(accountId: string) {
    activeAccountId.value = accountId
    // Refresh data for new account
    fetchPositions()
    fetchOrders()
  }

  function updateQuote(quote: Quote) {
    quotes.value[quote.symbol] = quote
  }

  function addSymbolToWatchlist(symbol: string) {
    if (!watchlist.value.includes(symbol)) {
      watchlist.value.push(symbol)
    }
  }

  function removeSymbolFromWatchlist(symbol: string) {
    const index = watchlist.value.indexOf(symbol)
    if (index > -1) {
      watchlist.value.splice(index, 1)
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    accounts,
    positions,
    orders,
    quotes,
    activeAccountId,
    watchlist,
    loading,
    error,
    connected,
    
    // Computed
    activeAccount,
    activePositions,
    pendingOrders,
    totalPortfolioValue,
    totalUnrealizedPnL,
    totalDayPnL,
    watchlistQuotes,
    
    // Actions
    fetchAccounts,
    fetchPositions,
    fetchOrders,
    submitOrder,
    cancelOrder,
    setActiveAccount,
    updateQuote,
    addSymbolToWatchlist,
    removeSymbolFromWatchlist,
    clearError
  }
})