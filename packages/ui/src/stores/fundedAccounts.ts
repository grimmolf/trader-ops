/**
 * Funded Accounts Pinia Store
 * 
 * Manages funded accounts (TopstepX, Apex, TradeDay) with real-time risk monitoring,
 * account selection, and comprehensive rule enforcement tracking.
 */

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

// Types
export interface FundedAccount {
  id: string
  name: string
  provider: 'topstepx' | 'apex' | 'tradeday' | 'ftmo' | 'other'
  type: 'evaluation' | 'funded' | 'express' | 'swing'
  status: 'active' | 'paused' | 'violated' | 'suspended' | 'passed'
  
  // Balance and P&L
  balance: number
  equity: number
  dailyPnL: number
  totalPnL: number
  maxDrawdown: number
  currentDrawdown: number
  
  // Risk Limits
  rules: AccountRules
  
  // Trading Activity
  todayTrades: number
  positions: Position[]
  
  // Metadata
  createdAt: Date
  lastUpdated: Date
  connectionStatus: 'connected' | 'disconnected' | 'error'
}

export interface AccountRules {
  // Loss Limits
  maxDailyLoss: number          // Maximum daily loss allowed
  maxTotalLoss: number          // Maximum total loss (trailing drawdown)
  maxDrawdownPercent: number    // Maximum drawdown percentage
  
  // Position Limits
  maxPositionSize: number       // Maximum position size
  maxDailyTrades: number        // Maximum trades per day
  maxConcurrentPositions: number // Maximum concurrent positions
  
  // Time Restrictions
  tradingHours: TimeRestriction[]
  minimumTradingDays: number    // Minimum trading days required
  
  // Other Rules
  newsTrading: boolean          // Allow trading during news events
  weekendTrading: boolean       // Allow weekend trading
  consistencyRule: boolean      // Consistency rule enforcement
}

export interface TimeRestriction {
  startTime: string   // HH:MM format
  endTime: string     // HH:MM format
  timezone: string    // Timezone identifier
  days: number[]      // Array of day numbers (0-6, Sunday=0)
}

export interface Position {
  symbol: string
  side: 'long' | 'short'
  quantity: number
  entryPrice: number
  currentPrice: number
  unrealizedPnL: number
  entryTime: Date
}

export interface RiskViolation {
  id: string
  accountId: string
  type: 'daily_loss' | 'total_loss' | 'drawdown' | 'position_size' | 'trading_hours' | 'max_trades'
  severity: 'warning' | 'critical' | 'violation'
  message: string
  value: number
  limit: number
  timestamp: Date
  acknowledged: boolean
}

export interface AccountMetrics {
  accountId: string
  
  // Risk Metrics
  dailyLossPercent: number      // Current daily loss as % of limit
  totalLossPercent: number      // Current total loss as % of limit
  drawdownPercent: number       // Current drawdown as % of limit
  
  // Trading Metrics
  tradeCount: number           // Trades today
  positionUtilization: number  // Current position size utilization
  avgWinRate: number          // Average win rate (last 30 days)
  profitFactor: number        // Profit factor calculation
  
  // Status
  riskLevel: 'safe' | 'warning' | 'danger' | 'violation'
  canTrade: boolean
  violations: RiskViolation[]
  
  lastCalculated: Date
}

export const useFundedAccountsStore = defineStore('fundedAccounts', () => {
  // State
  const accounts = ref<Map<string, FundedAccount>>(new Map())
  const selectedAccountId = ref<string | null>(null)
  const metrics = ref<Map<string, AccountMetrics>>(new Map())
  const violations = ref<RiskViolation[]>([])
  const loading = ref(false)
  const realtimeEnabled = ref(true)
  const lastUpdate = ref<Date | null>(null)

  // Computed
  const accountsList = computed(() => Array.from(accounts.value.values()))
  
  const activeAccount = computed(() => {
    if (!selectedAccountId.value) return null
    return accounts.value.get(selectedAccountId.value) || null
  })

  const activeAccountMetrics = computed(() => {
    if (!selectedAccountId.value) return null
    return metrics.value.get(selectedAccountId.value) || null
  })

  const groupedAccounts = computed(() => {
    const grouped: Record<string, FundedAccount[]> = {}
    
    for (const account of accountsList.value) {
      if (!grouped[account.provider]) {
        grouped[account.provider] = []
      }
      grouped[account.provider].push(account)
    }
    
    return grouped
  })

  const totalAccountValue = computed(() => {
    return accountsList.value.reduce((total, account) => total + account.equity, 0)
  })

  const totalDailyPnL = computed(() => {
    return accountsList.value.reduce((total, account) => total + account.dailyPnL, 0)
  })

  const criticalViolations = computed(() => {
    return violations.value.filter(v => v.severity === 'critical' || v.severity === 'violation')
  })

  const canTradeAny = computed(() => {
    return accountsList.value.some(account => {
      const accountMetrics = metrics.value.get(account.id)
      return accountMetrics?.canTrade === true
    })
  })

  // Actions
  async function initialize() {
    loading.value = true
    try {
      await loadAccounts()
      await updateAllMetrics()
      
      if (accountsList.value.length > 0 && !selectedAccountId.value) {
        selectAccount(accountsList.value[0].id)
      }
      
      startRealtimeUpdates()
    } catch (error) {
      console.error('Failed to initialize funded accounts:', error)
    } finally {
      loading.value = false
    }
  }

  async function loadAccounts() {
    try {
      const response = await fetch('/api/v1/funded-accounts')
      const accountsData = await response.json()
      
      accounts.value.clear()
      for (const accountData of accountsData) {
        const account: FundedAccount = {
          ...accountData,
          createdAt: new Date(accountData.createdAt),
          lastUpdated: new Date(accountData.lastUpdated)
        }
        accounts.value.set(account.id, account)
      }
      
      lastUpdate.value = new Date()
    } catch (error) {
      console.error('Failed to load accounts:', error)
      throw error
    }
  }

  async function updateMetrics(accountId: string) {
    try {
      const response = await fetch(`/api/v1/funded-accounts/${accountId}/metrics`)
      const metricsData = await response.json()
      
      const accountMetrics: AccountMetrics = {
        ...metricsData,
        lastCalculated: new Date(metricsData.lastCalculated),
        violations: metricsData.violations.map((v: any) => ({
          ...v,
          timestamp: new Date(v.timestamp)
        }))
      }
      
      metrics.value.set(accountId, accountMetrics)
      
      // Update global violations list
      updateViolations(accountMetrics.violations)
      
    } catch (error) {
      console.error(`Failed to update metrics for account ${accountId}:`, error)
    }
  }

  async function updateAllMetrics() {
    const promises = accountsList.value.map(account => updateMetrics(account.id))
    await Promise.allSettled(promises)
  }

  function selectAccount(accountId: string) {
    if (accounts.value.has(accountId)) {
      selectedAccountId.value = accountId
      updateMetrics(accountId) // Refresh metrics for selected account
    }
  }

  function updateViolations(accountViolations: RiskViolation[]) {
    // Remove old violations for this account
    const otherViolations = violations.value.filter(v => 
      !accountViolations.some(av => av.id === v.id)
    )
    
    // Add new violations
    violations.value = [...otherViolations, ...accountViolations]
  }

  async function acknowledgeViolation(violationId: string) {
    try {
      await fetch(`/api/v1/violations/${violationId}/acknowledge`, {
        method: 'POST'
      })
      
      // Update local state
      const violation = violations.value.find(v => v.id === violationId)
      if (violation) {
        violation.acknowledged = true
      }
    } catch (error) {
      console.error('Failed to acknowledge violation:', error)
    }
  }

  async function flattenPositions(accountId: string) {
    try {
      loading.value = true
      await fetch(`/api/v1/funded-accounts/${accountId}/flatten-positions`, {
        method: 'POST'
      })
      
      // Refresh account data
      await updateMetrics(accountId)
    } catch (error) {
      console.error('Failed to flatten positions:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function pauseTrading(accountId: string) {
    try {
      await fetch(`/api/v1/funded-accounts/${accountId}/pause`, {
        method: 'POST'
      })
      
      const account = accounts.value.get(accountId)
      if (account) {
        account.status = 'paused'
      }
    } catch (error) {
      console.error('Failed to pause trading:', error)
      throw error
    }
  }

  async function resumeTrading(accountId: string) {
    try {
      await fetch(`/api/v1/funded-accounts/${accountId}/resume`, {
        method: 'POST'
      })
      
      const account = accounts.value.get(accountId)
      if (account) {
        account.status = 'active'
      }
    } catch (error) {
      console.error('Failed to resume trading:', error)
      throw error
    }
  }

  function startRealtimeUpdates() {
    if (!realtimeEnabled.value) return
    
    // Update every 5 seconds
    setInterval(async () => {
      if (realtimeEnabled.value && selectedAccountId.value) {
        try {
          await updateMetrics(selectedAccountId.value)
        } catch (error) {
          console.error('Realtime update failed:', error)
        }
      }
    }, 5000)
  }

  function toggleRealtime() {
    realtimeEnabled.value = !realtimeEnabled.value
    if (realtimeEnabled.value) {
      startRealtimeUpdates()
    }
  }

  // Risk calculation utilities
  function calculateRiskLevel(accountMetrics: AccountMetrics): 'safe' | 'warning' | 'danger' | 'violation' {
    const { dailyLossPercent, totalLossPercent, drawdownPercent } = accountMetrics
    
    // Check for violations first
    if (dailyLossPercent >= 100 || totalLossPercent >= 100 || drawdownPercent >= 100) {
      return 'violation'
    }
    
    // Check for danger level (80%+ of any limit)
    if (dailyLossPercent >= 80 || totalLossPercent >= 80 || drawdownPercent >= 80) {
      return 'danger'
    }
    
    // Check for warning level (60%+ of any limit)
    if (dailyLossPercent >= 60 || totalLossPercent >= 60 || drawdownPercent >= 60) {
      return 'warning'
    }
    
    return 'safe'
  }

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  function formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`
  }

  // Watch for account changes to update metrics
  watch(selectedAccountId, (newAccountId) => {
    if (newAccountId) {
      updateMetrics(newAccountId)
    }
  })

  return {
    // State
    accounts: accountsList,
    selectedAccountId,
    activeAccount,
    activeAccountMetrics,
    groupedAccounts,
    violations,
    criticalViolations,
    loading,
    realtimeEnabled,
    lastUpdate,
    
    // Computed
    totalAccountValue,
    totalDailyPnL,
    canTradeAny,
    
    // Actions
    initialize,
    loadAccounts,
    updateMetrics,
    updateAllMetrics,
    selectAccount,
    acknowledgeViolation,
    flattenPositions,
    pauseTrading,
    resumeTrading,
    toggleRealtime,
    
    // Utilities
    calculateRiskLevel,
    formatCurrency,
    formatPercentage
  }
})

export type {
  FundedAccount,
  AccountRules,
  Position,
  RiskViolation,
  AccountMetrics,
  TimeRestriction
}