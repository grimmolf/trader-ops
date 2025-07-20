import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Strategy Performance Types
export type TradingMode = 'live' | 'paper' | 'suspended'

export interface StrategyTradeResult {
  strategy_id: string
  trade_id: string
  symbol: string
  entry_price: number
  exit_price: number
  quantity: number
  side: 'long' | 'short'
  pnl: number
  win: boolean
  timestamp: string
  mode: TradingMode
  set_number: number
  trade_number_in_set: number
  commission: number
  slippage: number
  net_pnl: number
}

export interface StrategySet {
  set_number: number
  strategy_id: string
  trades: StrategyTradeResult[]
  win_rate: number
  total_pnl: number
  net_pnl: number
  start_date: string
  end_date?: string
  mode: TradingMode
  evaluation_threshold: number
  is_complete: boolean
  average_trade_pnl: number
  profit_factor: number
}

export interface ModeTransition {
  from_mode: TradingMode
  to_mode: TradingMode
  timestamp: string
  reason: string
  trigger_set_number: number
  trigger_win_rates: number[]
}

export interface StrategyPerformance {
  strategy_id: string
  strategy_name: string
  current_mode: TradingMode
  current_set: StrategySet
  completed_sets: StrategySet[]
  mode_transition_history: ModeTransition[]
  
  // Performance thresholds
  min_win_rate: number
  evaluation_period: number
  consecutive_failures_threshold: number
  consecutive_successes_threshold: number
  
  // Statistics
  total_trades: number
  total_winning_trades: number
  total_losing_trades: number
  lifetime_pnl: number
  lifetime_net_pnl: number
  
  // Computed properties
  overall_win_rate: number
  recent_performance: number[]
  is_at_risk: boolean
  can_return_to_live: boolean
  
  created_at: string
  last_updated: string
}

export interface StrategyPerformanceSummary {
  strategy_id: string
  strategy_name: string
  current_mode: TradingMode
  current_set_progress: number
  current_set_win_rate: number
  overall_win_rate: number
  total_sets_completed: number
  recent_performance: number[]
  is_at_risk: boolean
  can_return_to_live: boolean
  lifetime_pnl: number
  lifetime_net_pnl: number
  last_trade_time?: string
  last_updated: string
}

export interface StrategyRegistration {
  strategy_id: string
  strategy_name: string
  min_win_rate: number
  evaluation_period: number
  initial_mode: TradingMode
}

export interface StrategyModeChangeRequest {
  new_mode: TradingMode
  reason: string
}

export interface PerformanceAlert {
  type: 'strategy_mode_change' | 'performance_warning' | 'set_completed'
  strategy_id: string
  strategy_name: string
  from_mode?: string
  to_mode?: string
  reason: string
  timestamp: string
  recent_performance?: number[]
}

export interface SystemStatus {
  initialized: boolean
  total_strategies: number
  live_strategies: number
  paper_strategies: number
  suspended_strategies: number
  at_risk_strategies: number
  can_return_strategies: number
  total_completed_sets: number
  total_trades: number
  recent_alerts: number
  timestamp: string
}

export const useStrategyPerformanceStore = defineStore('strategyPerformance', () => {
  // State
  const strategies = ref<Map<string, StrategyPerformance>>(new Map())
  const strategySummaries = ref<Map<string, StrategyPerformanceSummary>>(new Map())
  const performanceAlerts = ref<PerformanceAlert[]>([])
  const systemStatus = ref<SystemStatus | null>(null)
  const selectedStrategyId = ref<string | null>(null)
  const isLoading = ref(false)
  const lastUpdated = ref<Date | null>(null)

  // Computed
  const allStrategies = computed(() => Array.from(strategies.value.values()))
  const allStrategySummaries = computed(() => Array.from(strategySummaries.value.values()))
  
  const selectedStrategy = computed(() => {
    return selectedStrategyId.value ? strategies.value.get(selectedStrategyId.value) : null
  })
  
  const selectedStrategySummary = computed(() => {
    return selectedStrategyId.value ? strategySummaries.value.get(selectedStrategyId.value) : null
  })

  const liveStrategies = computed(() => 
    allStrategySummaries.value.filter(s => s.current_mode === 'live')
  )
  
  const paperStrategies = computed(() => 
    allStrategySummaries.value.filter(s => s.current_mode === 'paper')
  )
  
  const suspendedStrategies = computed(() => 
    allStrategySummaries.value.filter(s => s.current_mode === 'suspended')
  )
  
  const atRiskStrategies = computed(() => 
    allStrategySummaries.value.filter(s => s.is_at_risk)
  )
  
  const canReturnStrategies = computed(() => 
    allStrategySummaries.value.filter(s => s.can_return_to_live)
  )

  const recentAlerts = computed(() => 
    performanceAlerts.value.slice(0, 20)
  )

  // Actions
  const fetchStrategySummaries = async (): Promise<void> => {
    try {
      isLoading.value = true
      const response = await fetch('/api/strategies/summaries')
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const summaries: StrategyPerformanceSummary[] = await response.json()
      
      // Update summaries map
      strategySummaries.value.clear()
      summaries.forEach(summary => {
        strategySummaries.value.set(summary.strategy_id, summary)
      })
      
      lastUpdated.value = new Date()
      
    } catch (error) {
      console.error('Failed to fetch strategy summaries:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const fetchStrategy = async (strategyId: string): Promise<StrategyPerformance | null> => {
    try {
      isLoading.value = true
      const response = await fetch(`/api/strategies/${strategyId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const strategy: StrategyPerformance = await response.json()
      strategies.value.set(strategy.strategy_id, strategy)
      
      return strategy
      
    } catch (error) {
      console.error(`Failed to fetch strategy ${strategyId}:`, error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const registerStrategy = async (registration: StrategyRegistration): Promise<StrategyPerformance> => {
    try {
      isLoading.value = true
      const response = await fetch('/api/strategies/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registration),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const strategy: StrategyPerformance = await response.json()
      strategies.value.set(strategy.strategy_id, strategy)
      
      // Refresh summaries
      await fetchStrategySummaries()
      
      return strategy
      
    } catch (error) {
      console.error('Failed to register strategy:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const changeStrategyMode = async (
    strategyId: string, 
    request: StrategyModeChangeRequest
  ): Promise<ModeTransition | null> => {
    try {
      isLoading.value = true
      const response = await fetch(`/api/strategies/${strategyId}/mode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const transition: ModeTransition = await response.json()
      
      // Refresh strategy data
      await fetchStrategy(strategyId)
      await fetchStrategySummaries()
      
      return transition
      
    } catch (error) {
      console.error(`Failed to change strategy mode for ${strategyId}:`, error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const fetchPerformanceAlerts = async (limit: number = 50): Promise<void> => {
    try {
      const response = await fetch(`/api/strategies/alerts?limit=${limit}`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const alerts: PerformanceAlert[] = await response.json()
      performanceAlerts.value = alerts
      
    } catch (error) {
      console.error('Failed to fetch performance alerts:', error)
      throw error
    }
  }

  const fetchSystemStatus = async (): Promise<void> => {
    try {
      const response = await fetch('/api/strategies/status')
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const status: SystemStatus = await response.json()
      systemStatus.value = status
      
    } catch (error) {
      console.error('Failed to fetch system status:', error)
      throw error
    }
  }

  const clearPerformanceAlerts = async (): Promise<void> => {
    try {
      const response = await fetch('/api/strategies/alerts', {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      performanceAlerts.value = []
      
    } catch (error) {
      console.error('Failed to clear performance alerts:', error)
      throw error
    }
  }

  const selectStrategy = (strategyId: string | null): void => {
    selectedStrategyId.value = strategyId
    if (strategyId && !strategies.value.has(strategyId)) {
      // Fetch full strategy data if not already loaded
      fetchStrategy(strategyId)
    }
  }

  const refreshData = async (): Promise<void> => {
    await Promise.all([
      fetchStrategySummaries(),
      fetchPerformanceAlerts(),
      fetchSystemStatus(),
    ])
  }

  // WebSocket event handlers
  const handleStrategyModeChange = (event: any): void => {
    const alert: PerformanceAlert = {
      type: 'strategy_mode_change',
      strategy_id: event.strategy_id,
      strategy_name: event.strategy_name || event.strategy_id,
      from_mode: event.old_mode,
      to_mode: event.new_mode,
      reason: event.transition?.reason || 'Mode changed',
      timestamp: new Date().toISOString(),
    }
    
    performanceAlerts.value.unshift(alert)
    
    // Refresh affected strategy
    if (strategies.value.has(event.strategy_id)) {
      fetchStrategy(event.strategy_id)
    }
    
    // Refresh summaries
    fetchStrategySummaries()
  }

  const handleStrategyUpdate = (event: any): void => {
    // Handle real-time strategy updates from WebSocket
    if (event.strategy_id && strategySummaries.value.has(event.strategy_id)) {
      // Update summary if we have it
      fetchStrategySummaries()
    }
  }

  // Utility functions
  const formatMode = (mode: TradingMode): string => {
    switch (mode) {
      case 'live': return 'Live'
      case 'paper': return 'Paper'
      case 'suspended': return 'Suspended'
      default: return 'Unknown'
    }
  }

  const getModeColor = (mode: TradingMode): string => {
    switch (mode) {
      case 'live': return 'success'
      case 'paper': return 'warning'
      case 'suspended': return 'danger'
      default: return 'secondary'
    }
  }

  const formatWinRate = (winRate: number): string => {
    return `${winRate.toFixed(1)}%`
  }

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  return {
    // State
    strategies,
    strategySummaries,
    performanceAlerts,
    systemStatus,
    selectedStrategyId,
    isLoading,
    lastUpdated,
    
    // Computed
    allStrategies,
    allStrategySummaries,
    selectedStrategy,
    selectedStrategySummary,
    liveStrategies,
    paperStrategies,
    suspendedStrategies,
    atRiskStrategies,
    canReturnStrategies,
    recentAlerts,
    
    // Actions
    fetchStrategySummaries,
    fetchStrategy,
    registerStrategy,
    changeStrategyMode,
    fetchPerformanceAlerts,
    fetchSystemStatus,
    clearPerformanceAlerts,
    selectStrategy,
    refreshData,
    
    // WebSocket handlers
    handleStrategyModeChange,
    handleStrategyUpdate,
    
    // Utilities
    formatMode,
    getModeColor,
    formatWinRate,
    formatCurrency,
  }
})