import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface PaperAccount {
  id: string
  name: string
  broker: 'tastytrade' | 'tradovate' | 'alpaca' | 'simulator'
  balance: number
  dayPnL: number
  totalPnL: number
  positions: Position[]
  mode: 'sandbox' | 'simulator' | 'hybrid'
}

export interface Position {
  id: string
  symbol: string
  quantity: number
  avgPrice: number
  currentPrice: number
  unrealizedPnL: number
  side: 'long' | 'short'
}

export interface PaperTrade {
  id: string
  timestamp: Date
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  pnl?: number
  commission: number
  slippage: number
  strategy?: string
}

export interface PerformanceMetrics {
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  profitFactor: number
  averageWin: number
  averageLoss: number
  maxDrawdown: number
  totalCommissions: number
  totalSlippage: number
}

export const usePaperTradingStore = defineStore('paperTrading', () => {
  // State
  const mode = ref<'sandbox' | 'simulator' | 'hybrid'>('sandbox')
  const accounts = ref<PaperAccount[]>([])
  const activeAccountId = ref<string>('')
  const recentTrades = ref<PaperTrade[]>([])
  const performanceHistory = ref<{ date: string, cumulativePnL: number }[]>([])
  const isInitialized = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const activeAccount = computed(() => 
    accounts.value.find(acc => acc.id === activeAccountId.value)
  )

  const totalBalance = computed(() => 
    accounts.value.reduce((sum, acc) => sum + acc.balance, 0)
  )

  const totalDayPnL = computed(() => 
    accounts.value.reduce((sum, acc) => sum + acc.dayPnL, 0)
  )

  const totalPnL = computed(() => 
    accounts.value.reduce((sum, acc) => sum + acc.totalPnL, 0)
  )

  const performanceMetrics = computed<PerformanceMetrics>(() => {
    const trades = recentTrades.value
    const winningTrades = trades.filter(t => (t.pnl || 0) > 0)
    const losingTrades = trades.filter(t => (t.pnl || 0) < 0)
    
    const totalWins = winningTrades.length
    const totalLosses = losingTrades.length
    const totalTrades = trades.length
    
    const grossProfit = winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
    const grossLoss = Math.abs(losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0))
    
    return {
      totalTrades,
      winningTrades: totalWins,
      losingTrades: totalLosses,
      winRate: totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0,
      profitFactor: grossLoss > 0 ? grossProfit / grossLoss : 0,
      averageWin: totalWins > 0 ? grossProfit / totalWins : 0,
      averageLoss: totalLosses > 0 ? grossLoss / totalLosses : 0,
      maxDrawdown: calculateMaxDrawdown(),
      totalCommissions: trades.reduce((sum, t) => sum + t.commission, 0),
      totalSlippage: trades.reduce((sum, t) => sum + t.slippage, 0)
    }
  })

  // Actions
  async function initializeAccounts() {
    if (isInitialized.value) return

    loading.value = true
    try {
      // Initialize default paper accounts
      accounts.value = [
        {
          id: 'paper_tastytrade',
          name: 'Tastytrade Sandbox',
          broker: 'tastytrade',
          balance: 100000,
          dayPnL: 0,
          totalPnL: 0,
          positions: [],
          mode: 'sandbox'
        },
        {
          id: 'paper_tradovate',
          name: 'Tradovate Demo',
          broker: 'tradovate',
          balance: 50000,
          dayPnL: 0,
          totalPnL: 0,
          positions: [],
          mode: 'sandbox'
        },
        {
          id: 'paper_simulator',
          name: 'Internal Simulator',
          broker: 'simulator',
          balance: 100000,
          dayPnL: 0,
          totalPnL: 0,
          positions: [],
          mode: 'simulator'
        }
      ]

      activeAccountId.value = accounts.value[0].id
      isInitialized.value = true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to initialize accounts'
    } finally {
      loading.value = false
    }
  }

  function setMode(newMode: typeof mode.value) {
    mode.value = newMode
  }

  function setActiveAccount(accountId: string) {
    activeAccountId.value = accountId
  }

  async function addTrade(trade: Omit<PaperTrade, 'id'>) {
    const newTrade: PaperTrade = {
      ...trade,
      id: Math.random().toString(36).substr(2, 9)
    }
    
    recentTrades.value.unshift(newTrade)
    
    // Keep only last 1000 trades
    if (recentTrades.value.length > 1000) {
      recentTrades.value = recentTrades.value.slice(0, 1000)
    }

    // Update account P&L
    const account = accounts.value.find(acc => acc.id === activeAccountId.value)
    if (account && newTrade.pnl) {
      account.dayPnL += newTrade.pnl
      account.totalPnL += newTrade.pnl
    }

    // Update performance history
    updatePerformanceHistory()
  }

  async function resetAccount(accountId: string) {
    const account = accounts.value.find(acc => acc.id === accountId)
    if (account) {
      account.balance = account.broker === 'tradovate' ? 50000 : 100000
      account.dayPnL = 0
      account.totalPnL = 0
      account.positions = []
    }
  }

  async function flattenAllPositions(accountId: string) {
    const account = accounts.value.find(acc => acc.id === accountId)
    if (account) {
      // TODO: Implement position flattening logic
      account.positions = []
    }
  }

  function updatePerformanceHistory() {
    const today = new Date().toISOString().split('T')[0]
    const existingEntry = performanceHistory.value.find(entry => entry.date === today)
    
    if (existingEntry) {
      existingEntry.cumulativePnL = totalPnL.value
    } else {
      performanceHistory.value.push({
        date: today,
        cumulativePnL: totalPnL.value
      })
    }
    
    // Keep only last 365 days
    if (performanceHistory.value.length > 365) {
      performanceHistory.value = performanceHistory.value.slice(-365)
    }
  }

  function calculateMaxDrawdown(): number {
    let maxDrawdown = 0
    let peak = 0
    
    for (const entry of performanceHistory.value) {
      if (entry.cumulativePnL > peak) {
        peak = entry.cumulativePnL
      }
      
      const drawdown = peak - entry.cumulativePnL
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown
      }
    }
    
    return maxDrawdown
  }

  return {
    // State
    mode,
    accounts,
    activeAccountId,
    recentTrades,
    performanceHistory,
    isInitialized,
    loading,
    error,
    
    // Computed
    activeAccount,
    totalBalance,
    totalDayPnL,
    totalPnL,
    performanceMetrics,
    
    // Actions
    initializeAccounts,
    setMode,
    setActiveAccount,
    addTrade,
    resetAccount,
    flattenAllPositions
  }
})