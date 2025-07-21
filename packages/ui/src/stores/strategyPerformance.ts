import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface StrategyMetrics {
  strategyId: string
  strategyName: string
  currentMode: 'live' | 'paper' | 'suspended'
  currentSet: {
    setNumber: number
    trades: TradeResult[]
    winRate: number
    totalPnl: number
  }
  completedSets: SetResult[]
  modeTransitionHistory: TransitionEvent[]
  isAtRisk: boolean
}

export interface TradeResult {
  tradeId: string
  symbol: string
  entryPrice: number
  exitPrice: number
  quantity: number
  side: 'long' | 'short'
  pnl: number
  win: boolean
  timestamp: string
}

export interface SetResult {
  setNumber: number
  trades: TradeResult[]
  winRate: number
  totalPnl: number
  startDate: string
  endDate: string
  mode: 'live' | 'paper'
}

export interface TransitionEvent {
  from: string
  to: string
  timestamp: string
  reason: string
}

export interface StrategyRegistration {
  strategyId: string
  strategyName: string
  minWinRate?: number
  evaluationPeriod?: number
}

export interface StrategyModeChangeRequest {
  strategyId: string
  newMode: TradingMode
  reason?: string
}

export type TradingMode = 'live' | 'paper' | 'suspended'

export const useStrategyPerformanceStore = defineStore('strategyPerformance', () => {
  const strategies = ref<StrategyMetrics[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const activeStrategies = computed(() => 
    strategies.value.filter(s => s.currentMode === 'live')
  )

  const paperModeStrategies = computed(() => 
    strategies.value.filter(s => s.currentMode === 'paper')
  )

  const overallWinRate = computed(() => {
    const allTrades = strategies.value.flatMap(s => [
      ...s.currentSet.trades,
      ...s.completedSets.flatMap(set => set.trades)
    ])
    if (allTrades.length === 0) return 0
    const wins = allTrades.filter(t => t.win).length
    return (wins / allTrades.length) * 100
  })

  const totalDailyPnL = computed(() => {
    const today = new Date().toDateString()
    return strategies.value.reduce((total, strategy) => {
      const todayTrades = strategy.currentSet.trades.filter(
        t => new Date(t.timestamp).toDateString() === today
      )
      return total + todayTrades.reduce((sum, t) => sum + t.pnl, 0)
    }, 0)
  })

  // Actions
  async function fetchStrategies() {
    try {
      loading.value = true
      // TODO: Replace with actual API call
      // const response = await api.getStrategyPerformance()
      // strategies.value = response.data
      
      // Mock data for now
      strategies.value = [
        {
          strategyId: 'momentum_breakout',
          strategyName: 'Momentum Breakout',
          currentMode: 'live',
          currentSet: {
            setNumber: 5,
            trades: [],
            winRate: 0,
            totalPnl: 0
          },
          completedSets: [
            {
              setNumber: 4,
              trades: [],
              winRate: 65.0,
              totalPnl: 1250.50,
              startDate: '2025-01-15',
              endDate: '2025-01-20',
              mode: 'live'
            }
          ],
          modeTransitionHistory: [],
          isAtRisk: false
        }
      ]
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch strategies'
    } finally {
      loading.value = false
    }
  }

  async function updateStrategyMode(strategyId: string, newMode: 'live' | 'paper') {
    try {
      // TODO: Replace with actual API call
      // await api.updateStrategyMode(strategyId, newMode)
      
      const strategy = strategies.value.find(s => s.strategyId === strategyId)
      if (strategy) {
        const oldMode = strategy.currentMode
        strategy.currentMode = newMode
        strategy.modeTransitionHistory.push({
          from: oldMode,
          to: newMode,
          timestamp: new Date().toISOString(),
          reason: 'Manual override'
        })
      }
      
      await fetchStrategies()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update strategy mode'
    }
  }

  function getStrategyById(strategyId: string) {
    return strategies.value.find(s => s.strategyId === strategyId)
  }

  function getStrategyRiskLevel(strategy: StrategyMetrics): 'low' | 'medium' | 'high' {
    if (strategy.currentMode === 'paper') return 'low'
    
    const recentSets = strategy.completedSets.slice(-2)
    const failedSets = recentSets.filter(s => s.winRate < 55).length
    
    if (failedSets >= 2) return 'high'
    if (failedSets >= 1) return 'medium'
    return 'low'
  }

  // Subscribe to real-time mode changes
  function subscribeToModeChanges() {
    // TODO: Implement WebSocket subscription
    // api.on('strategy-mode-change', (data) => {
    //   const strategy = strategies.value.find(s => s.strategyId === data.strategyId)
    //   if (strategy) {
    //     strategy.currentMode = data.newMode
    //     strategy.modeTransitionHistory.push(data.transition)
    //   }
    // })
  }

  return {
    strategies,
    loading,
    error,
    
    // Computed
    activeStrategies,
    paperModeStrategies,
    overallWinRate,
    totalDailyPnL,
    
    // Actions
    fetchStrategies,
    updateStrategyMode,
    getStrategyById,
    getStrategyRiskLevel,
    subscribeToModeChanges
  }
})