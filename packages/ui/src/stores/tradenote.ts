import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface TradeJournalEntry {
  id: string
  timestamp: Date
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  pnl?: number
  notes?: string
  tags?: string[]
  strategy?: string
}

export interface CalendarData {
  date: string
  pnl: number
  trades: number
  winRate: number
}

export const useTradeNoteStore = defineStore('tradenote', () => {
  // State
  const connectionStatus = ref<'connected' | 'disconnected' | 'connecting'>('disconnected')
  const trades = ref<TradeJournalEntry[]>([])
  const calendarData = ref<CalendarData[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const connectionStatusText = computed(() => {
    switch (connectionStatus.value) {
      case 'connected':
        return 'Connected to TradeNote'
      case 'connecting':
        return 'Connecting...'
      case 'disconnected':
        return 'Disconnected'
      default:
        return 'Unknown'
    }
  })

  const totalTrades = computed(() => trades.value.length)
  const totalPnL = computed(() => trades.value.reduce((sum, trade) => sum + (trade.pnl || 0), 0))
  const winRate = computed(() => {
    const wins = trades.value.filter(trade => (trade.pnl || 0) > 0).length
    return totalTrades.value > 0 ? (wins / totalTrades.value) * 100 : 0
  })

  // Actions
  async function connect() {
    connectionStatus.value = 'connecting'
    try {
      // TODO: Implement actual TradeNote connection
      await new Promise(resolve => setTimeout(resolve, 1000))
      connectionStatus.value = 'connected'
      await fetchTrades()
    } catch (err) {
      connectionStatus.value = 'disconnected'
      error.value = err instanceof Error ? err.message : 'Connection failed'
    }
  }

  async function disconnect() {
    connectionStatus.value = 'disconnected'
    trades.value = []
    calendarData.value = []
  }

  async function fetchTrades() {
    if (connectionStatus.value !== 'connected') return

    loading.value = true
    try {
      // TODO: Implement actual API call to TradeNote
      // For now, use mock data
      trades.value = [
        {
          id: '1',
          timestamp: new Date(),
          symbol: 'ES',
          side: 'buy',
          quantity: 1,
          price: 4750.0,
          pnl: 125.50,
          strategy: 'momentum_breakout',
          tags: ['futures', 'live']
        }
      ]
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch trades'
    } finally {
      loading.value = false
    }
  }

  async function addTrade(trade: Omit<TradeJournalEntry, 'id'>) {
    const newTrade: TradeJournalEntry = {
      ...trade,
      id: Math.random().toString(36).substr(2, 9)
    }
    trades.value.unshift(newTrade)
    
    // TODO: Send to TradeNote API
  }

  async function fetchCalendarData(year: number) {
    loading.value = true
    try {
      // TODO: Implement actual API call
      // Mock calendar data for now
      calendarData.value = []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch calendar data'
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    connectionStatus,
    trades,
    calendarData,
    loading,
    error,
    
    // Computed
    connectionStatusText,
    totalTrades,
    totalPnL,
    winRate,
    
    // Actions
    connect,
    disconnect,
    fetchTrades,
    addTrade,
    fetchCalendarData
  }
})