import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface Position {
  id: string
  symbol: string
  quantity: number
  avgPrice: number
  currentPrice: number
  unrealizedPnL: number
  realizedPnL: number
  side: 'long' | 'short'
}

export interface Order {
  id: string
  symbol: string
  quantity: number
  price: number
  type: 'market' | 'limit' | 'stop'
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  side: 'buy' | 'sell'
  timestamp: Date
}

export interface FundedAccount {
  id: string
  name: string
  balance: number
  dayPnL: number
  maxDailyLoss: number
  maxContracts: number
  status: 'active' | 'suspended' | 'violated'
}

export interface RealTimeData {
  quotes: Record<string, any>
  positions: Position[]
  orders: Order[]
  accounts: FundedAccount[]
  connected: boolean
}

export function useRealTimeData() {
  const data = ref<RealTimeData>({
    quotes: {},
    positions: [],
    orders: [],
    accounts: [],
    connected: false
  })

  const isConnected = computed(() => data.value.connected)
  const totalPnL = computed(() => 
    data.value.positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0)
  )

  let ws: WebSocket | null = null

  const connect = () => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/stream'
    
    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        data.value.connected = true
        console.log('WebSocket connected')
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        data.value.connected = false
        console.log('WebSocket disconnected')
        
        // Reconnect after 3 seconds
        setTimeout(connect, 3000)
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        data.value.connected = false
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'quotes':
        if (message.data) {
          message.data.forEach((quote: any) => {
            data.value.quotes[quote.symbol] = quote
          })
        }
        break
        
      case 'positions':
        if (message.data) {
          data.value.positions = message.data
        }
        break
        
      case 'orders':
        if (message.data) {
          data.value.orders = message.data
        }
        break
        
      case 'accounts':
        if (message.data) {
          data.value.accounts = message.data
        }
        break
        
      default:
        console.log('Unknown message type:', message.type)
    }
  }

  const disconnect = () => {
    if (ws) {
      ws.close()
      ws = null
    }
    data.value.connected = false
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    data,
    isConnected,
    totalPnL,
    connect,
    disconnect
  }
}

export function usePositions() {
  const { data } = useRealTimeData()
  
  const positions = computed(() => data.value.positions)
  const totalValue = computed(() => 
    positions.value.reduce((sum, pos) => sum + (pos.quantity * pos.currentPrice), 0)
  )
  
  return {
    positions,
    totalValue
  }
}

export function useFundedAccounts() {
  const { data } = useRealTimeData()
  
  const accounts = computed(() => data.value.accounts)
  const activeAccounts = computed(() => 
    accounts.value.filter(acc => acc.status === 'active')
  )
  
  return {
    accounts,
    activeAccounts
  }
}

export function useOrders() {
  const { data } = useRealTimeData()
  
  const orders = computed(() => data.value.orders)
  const pendingOrders = computed(() => 
    orders.value.filter(order => order.status === 'pending')
  )
  
  return {
    orders,
    pendingOrders
  }
}