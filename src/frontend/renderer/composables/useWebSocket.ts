import { ref, onUnmounted } from 'vue'
import { useTradingStore } from '../src/stores/trading'
import { useAppStore } from '../src/stores/app'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export function useWebSocket(url: string) {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = ref(1000)

  const tradingStore = useTradingStore()
  const appStore = useAppStore()

  let reconnectTimer: number | null = null

  function connect() {
    try {
      console.log(`Connecting to WebSocket: ${url}`)
      
      socket.value = new WebSocket(url)
      
      socket.value.onopen = () => {
        console.log('WebSocket connected successfully')
        isConnected.value = true
        error.value = null
        reconnectAttempts.value = 0
        reconnectDelay.value = 1000
        
        appStore.updateConnectionStatus(true)
        
        // Subscribe to watchlist symbols
        tradingStore.watchlist.forEach(symbol => {
          subscribe('quotes', symbol)
        })
        
        // Subscribe to account updates
        subscribe('account', '')
        subscribe('positions', '')
        subscribe('orders', '')
      }
      
      socket.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }
      
      socket.value.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        isConnected.value = false
        appStore.updateConnectionStatus(false)
        
        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
          scheduleReconnect()
        }
      }
      
      socket.value.onerror = (event) => {
        console.error('WebSocket error:', event)
        error.value = 'WebSocket connection error'
        isConnected.value = false
        appStore.updateConnectionStatus(false)
      }
      
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err)
      error.value = err instanceof Error ? err.message : 'Unknown WebSocket error'
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    if (socket.value) {
      socket.value.close(1000, 'Manual disconnect')
      socket.value = null
    }
    
    isConnected.value = false
    reconnectAttempts.value = 0
  }

  function scheduleReconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }
    
    reconnectAttempts.value++
    const delay = Math.min(reconnectDelay.value * Math.pow(2, reconnectAttempts.value - 1), 30000)
    
    console.log(`Scheduling reconnect attempt ${reconnectAttempts.value} in ${delay}ms`)
    
    reconnectTimer = setTimeout(() => {
      connect()
    }, delay) as unknown as number
  }

  function send(message: any) {
    if (socket.value && isConnected.value) {
      try {
        socket.value.send(JSON.stringify(message))
      } catch (err) {
        console.error('Failed to send WebSocket message:', err)
      }
    } else {
      console.warn('Cannot send message: WebSocket not connected')
    }
  }

  function subscribe(type: string, symbol: string) {
    send({
      action: 'subscribe',
      type,
      symbol
    })
  }

  function unsubscribe(type: string, symbol: string) {
    send({
      action: 'unsubscribe',
      type,
      symbol
    })
  }

  function handleMessage(message: WebSocketMessage) {
    try {
      switch (message.type) {
        case 'quote':
          if (message.data) {
            tradingStore.updateQuote({
              symbol: message.data.symbol,
              price: message.data.price,
              change: message.data.change,
              changePercent: message.data.changePercent,
              volume: message.data.volume,
              lastUpdate: new Date(message.timestamp)
            })
          }
          break
          
        case 'quotes':
          if (Array.isArray(message.data)) {
            tradingStore.updateQuotes(message.data.map(quote => ({
              ...quote,
              lastUpdate: new Date(message.timestamp)
            })))
          }
          break
          
        case 'account':
          if (message.data) {
            tradingStore.updateAccount(message.data)
          }
          break
          
        case 'positions':
          if (Array.isArray(message.data)) {
            tradingStore.updatePositions(message.data)
          }
          break
          
        case 'order_update':
          if (message.data && message.data.orderId) {
            tradingStore.updateOrderStatus(message.data.orderId, message.data.status)
          }
          break
          
        case 'market_status':
          if (message.data && typeof message.data.isOpen === 'boolean') {
            tradingStore.setMarketStatus(message.data.isOpen)
          }
          break
          
        case 'error':
          console.error('WebSocket server error:', message.data)
          error.value = message.data.message || 'Server error'
          break
          
        default:
          console.log('Unknown message type:', message.type, message.data)
      }
    } catch (err) {
      console.error('Error handling WebSocket message:', err, message)
    }
  }

  // Auto-connect on creation
  connect()

  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    error,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe
  }
}