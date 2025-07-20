import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Quote {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  lastUpdate: Date
}

export interface Position {
  symbol: string
  quantity: number
  averagePrice: number
  currentPrice: number
  unrealizedPnL: number
  side: 'long' | 'short'
}

export interface Order {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  type: 'market' | 'limit' | 'stop'
  status: 'pending' | 'filled' | 'cancelled'
  timestamp: Date
}

export interface Account {
  accountId: string
  balance: number
  buyingPower: number
  dayPnL: number
  totalPnL: number
}

export const useTradingStore = defineStore('trading', () => {
  // State
  const activeSymbol = ref('MNQ1!')
  const watchlist = ref<string[]>(['MNQ1!', 'ES1!', 'NQ1!', 'RTY1!', 'YM1!'])
  const quotes = ref<Map<string, Quote>>(new Map())
  const positions = ref<Position[]>([])
  const orders = ref<Order[]>([])
  const account = ref<Account | null>(null)
  const isMarketOpen = ref(false)

  // Getters
  const currentQuote = computed(() => 
    quotes.value.get(activeSymbol.value)
  )

  const watchlistQuotes = computed(() => 
    watchlist.value.map(symbol => quotes.value.get(symbol)).filter(Boolean) as Quote[]
  )

  const openPositions = computed(() => 
    positions.value.filter(p => p.quantity !== 0)
  )

  const totalPnL = computed(() => 
    positions.value.reduce((total, pos) => total + pos.unrealizedPnL, 0)
  )

  const pendingOrders = computed(() => 
    orders.value.filter(order => order.status === 'pending')
  )

  // Actions
  function setActiveSymbol(symbol: string) {
    activeSymbol.value = symbol
    console.log(`Active symbol changed to: ${symbol}`)
  }

  function addToWatchlist(symbol: string) {
    if (!watchlist.value.includes(symbol)) {
      watchlist.value.push(symbol)
      console.log(`Added ${symbol} to watchlist`)
    }
  }

  function removeFromWatchlist(symbol: string) {
    const index = watchlist.value.indexOf(symbol)
    if (index > -1) {
      watchlist.value.splice(index, 1)
      quotes.value.delete(symbol)
      console.log(`Removed ${symbol} from watchlist`)
    }
  }

  function updateQuote(quote: Quote) {
    quotes.value.set(quote.symbol, {
      ...quote,
      lastUpdate: new Date()
    })
  }

  function updateQuotes(newQuotes: Quote[]) {
    newQuotes.forEach(quote => updateQuote(quote))
  }

  function updatePositions(newPositions: Position[]) {
    positions.value = newPositions
  }

  function updateAccount(newAccount: Account) {
    account.value = newAccount
  }

  function addOrder(order: Omit<Order, 'id' | 'timestamp'>) {
    const newOrder: Order = {
      ...order,
      id: `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }
    orders.value.unshift(newOrder)
    return newOrder
  }

  function updateOrderStatus(orderId: string, status: Order['status']) {
    const order = orders.value.find(o => o.id === orderId)
    if (order) {
      order.status = status
      console.log(`Order ${orderId} status updated to: ${status}`)
    }
  }

  async function loadInitialData() {
    try {
      console.log('Loading initial trading data...')
      
      // Load account data
      if (window.electronAPI) {
        const accountData = await window.electronAPI.apiRequest('/api/account')
        if (accountData) {
          updateAccount(accountData)
        }

        // Load positions
        const positionsData = await window.electronAPI.apiRequest('/api/positions')
        if (positionsData) {
          updatePositions(positionsData)
        }

        // Load recent orders
        const ordersData = await window.electronAPI.apiRequest('/api/orders?limit=50')
        if (ordersData) {
          orders.value = ordersData
        }

        // Check market status
        const marketStatus = await window.electronAPI.apiRequest('/api/market/status')
        if (marketStatus) {
          isMarketOpen.value = marketStatus.isOpen
        }
      }
      
      console.log('Initial trading data loaded successfully')
    } catch (error) {
      console.error('Failed to load initial trading data:', error)
      throw error
    }
  }

  async function submitOrder(orderRequest: Omit<Order, 'id' | 'timestamp' | 'status'>) {
    try {
      console.log('Submitting order:', orderRequest)
      
      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest('/api/orders', {
          method: 'POST',
          body: JSON.stringify(orderRequest)
        })
        
        if (response) {
          const order = addOrder({ ...orderRequest, status: 'pending' })
          console.log('Order submitted successfully:', response)
          return order
        }
      }
      
      throw new Error('Failed to submit order')
    } catch (error) {
      console.error('Order submission failed:', error)
      throw error
    }
  }

  function setMarketStatus(isOpen: boolean) {
    isMarketOpen.value = isOpen
  }

  return {
    // State
    activeSymbol,
    watchlist,
    quotes,
    positions,
    orders,
    account,
    isMarketOpen,
    
    // Getters
    currentQuote,
    watchlistQuotes,
    openPositions,
    totalPnL,
    pendingOrders,
    
    // Actions
    setActiveSymbol,
    addToWatchlist,
    removeFromWatchlist,
    updateQuote,
    updateQuotes,
    updatePositions,
    updateAccount,
    addOrder,
    updateOrderStatus,
    loadInitialData,
    submitOrder,
    setMarketStatus
  }
})