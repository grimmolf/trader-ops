/**
 * Funded Accounts Store
 * 
 * Pinia store for managing funded trading accounts including TopStep, Apex, 
 * and TradeDay accounts with real-time rule monitoring and risk management.
 */

import { defineStore } from 'pinia'
import { ref, computed, nextTick } from 'vue'

export interface FundedAccountRules {
  maxDailyLoss: number
  maxContracts: number
  trailingDrawdown: number
  profitTarget: number
  allowOvernightPositions: boolean
  allowNewsTrading: boolean
  restrictedSymbols: string[]
}

export interface FundedAccountMetrics {
  dailyPnL: number
  totalPnL: number
  currentDrawdown: number
  maxPeakEquity: number
  openPositions: number
  totalContracts: number
  winRate: number
  profitFactor: number
  totalTrades: number
  tradingDays: number
}

export interface RuleViolation {
  id: string
  type: 'daily_loss_limit' | 'trailing_drawdown' | 'max_contracts' | 'consistency_violation'
  triggeredAt: string
  ruleLimit: number
  actualValue: number
  message: string
  resolved: boolean
}

export interface FundedAccount {
  id: string
  name: string
  platform: 'topstep' | 'apex' | 'tradeday' | 'fundedtrader'
  accountType: string
  phase: 'evaluation' | 'funded' | 'scaling'
  status: 'active' | 'suspended' | 'passed' | 'failed'
  size: number
  currentBalance: number
  
  rules: FundedAccountRules
  metrics: FundedAccountMetrics
  violations: RuleViolation[]
  
  createdAt: string
  lastTradeDate?: string
  lastUpdated: string
  
  // UI state
  isLoading?: boolean
  isConnected?: boolean
}

export const useFundedAccountsStore = defineStore('fundedAccounts', () => {
  // State
  const accounts = ref<FundedAccount[]>([])
  const activeAccountId = ref<string>('')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdate = ref<Date | null>(null)
  
  // Real-time updates
  const realtimeEnabled = ref(false)
  const updateInterval = ref<number | null>(null)
  
  // Computed getters
  const activeAccount = computed(() => 
    accounts.value.find(acc => acc.id === activeAccountId.value)
  )
  
  const accountsByPlatform = computed(() => {
    const grouped = accounts.value.reduce((acc, account) => {
      if (!acc[account.platform]) {
        acc[account.platform] = []
      }
      acc[account.platform].push(account)
      return acc
    }, {} as Record<string, FundedAccount[]>)
    
    return Object.entries(grouped).map(([platform, accounts]) => ({
      platform: platform.toUpperCase(),
      accounts
    }))
  })
  
  const totalAccountValue = computed(() => 
    accounts.value.reduce((total, acc) => total + acc.currentBalance, 0)
  )
  
  const totalDailyPnL = computed(() =>
    accounts.value.reduce((total, acc) => total + acc.metrics.dailyPnL, 0)
  )
  
  const activeViolations = computed(() => 
    accounts.value.flatMap(acc => 
      acc.violations.filter(v => !v.resolved)
    )
  )
  
  const accountsAtRisk = computed(() =>
    accounts.value.filter(acc => {
      const rules = acc.rules
      const metrics = acc.metrics
      
      // Check if close to limits (within 20%)
      const dailyLossRisk = Math.abs(metrics.dailyPnL) >= (rules.maxDailyLoss * 0.8)
      const drawdownRisk = metrics.currentDrawdown >= (rules.trailingDrawdown * 0.8)
      const contractRisk = metrics.totalContracts >= (rules.maxContracts * 0.8)
      
      return dailyLossRisk || drawdownRisk || contractRisk
    })
  )
  
  // Actions
  async function fetchAccounts() {
    loading.value = true
    error.value = null
    
    try {
      // In development, load mock data
      if (import.meta.env.DEV) {
        await loadMockAccounts()
        return
      }
      
      // TODO: Replace with actual API call
      const response = await fetch('/api/funded-accounts')
      if (!response.ok) {
        throw new Error(`Failed to fetch accounts: ${response.statusText}`)
      }
      
      const data = await response.json()
      accounts.value = data.accounts
      lastUpdate.value = new Date()
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch accounts'
      console.error('Error fetching funded accounts:', err)
    } finally {
      loading.value = false
    }
  }
  
  async function loadMockAccounts() {
    // Mock data for development
    const mockAccounts: FundedAccount[] = [
      {
        id: 'topstep_eval_001',
        name: 'TopStep Evaluation $50K',
        platform: 'topstep',
        accountType: 'Express Evaluation',
        phase: 'evaluation',
        status: 'active',
        size: 50000,
        currentBalance: 51750,
        
        rules: {
          maxDailyLoss: 1000,
          maxContracts: 3,
          trailingDrawdown: 2000,
          profitTarget: 3000,
          allowOvernightPositions: false,
          allowNewsTrading: false,
          restrictedSymbols: ['BTCUSD', 'ETHUSD']
        },
        
        metrics: {
          dailyPnL: -250,
          totalPnL: 1750,
          currentDrawdown: 500,
          maxPeakEquity: 51750,
          openPositions: 1,
          totalContracts: 2,
          winRate: 65.5,
          profitFactor: 1.8,
          totalTrades: 47,
          tradingDays: 12
        },
        
        violations: [],
        createdAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
        lastTradeDate: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        lastUpdated: new Date().toISOString(),
        isConnected: true
      },
      
      {
        id: 'topstep_funded_001',
        name: 'TopStep Funded $125K',
        platform: 'topstep',
        accountType: 'Funded Account',
        phase: 'funded',
        status: 'active',
        size: 125000,
        currentBalance: 133500,
        
        rules: {
          maxDailyLoss: 2000,
          maxContracts: 5,
          trailingDrawdown: 4000,
          profitTarget: 0, // No target for funded accounts
          allowOvernightPositions: true,
          allowNewsTrading: true,
          restrictedSymbols: []
        },
        
        metrics: {
          dailyPnL: 150,
          totalPnL: 8500,
          currentDrawdown: 200,
          maxPeakEquity: 133500,
          openPositions: 0,
          totalContracts: 0,
          winRate: 72.3,
          profitFactor: 2.1,
          totalTrades: 156,
          tradingDays: 45
        },
        
        violations: [],
        createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
        lastTradeDate: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        lastUpdated: new Date().toISOString(),
        isConnected: true
      },
      
      {
        id: 'apex_eval_001',
        name: 'Apex Evaluation $25K',
        platform: 'apex',
        accountType: 'Standard Evaluation',
        phase: 'evaluation',
        status: 'active',
        size: 25000,
        currentBalance: 25850,
        
        rules: {
          maxDailyLoss: 750,
          maxContracts: 2,
          trailingDrawdown: 1500,
          profitTarget: 2000,
          allowOvernightPositions: false,
          allowNewsTrading: false,
          restrictedSymbols: []
        },
        
        metrics: {
          dailyPnL: 45,
          totalPnL: 850,
          currentDrawdown: 125,
          maxPeakEquity: 25975,
          openPositions: 0,
          totalContracts: 0,
          winRate: 58.2,
          profitFactor: 1.4,
          totalTrades: 28,
          tradingDays: 8
        },
        
        violations: [],
        createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        lastTradeDate: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        lastUpdated: new Date().toISOString(),
        isConnected: true
      }
    ]
    
    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 800))
    
    accounts.value = mockAccounts
    lastUpdate.value = new Date()
    
    // Set first account as active if none selected
    if (!activeAccountId.value && mockAccounts.length > 0) {
      activeAccountId.value = mockAccounts[0].id
    }
  }
  
  async function updateMetrics(accountId: string) {
    const account = accounts.value.find(acc => acc.id === accountId)
    if (!account) return
    
    account.isLoading = true
    
    try {
      if (import.meta.env.DEV) {
        // Mock real-time updates for development
        await simulateMetricsUpdate(account)
        return
      }
      
      // TODO: Replace with actual API call
      const response = await fetch(`/api/funded-accounts/${accountId}/metrics`)
      if (!response.ok) {
        throw new Error(`Failed to update metrics: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Update account metrics
      Object.assign(account.metrics, data.metrics)
      Object.assign(account.rules, data.rules)
      account.violations = data.violations || []
      account.lastUpdated = new Date().toISOString()
      
    } catch (err) {
      console.error(`Error updating metrics for account ${accountId}:`, err)
      account.isConnected = false
    } finally {
      account.isLoading = false
    }
  }
  
  async function simulateMetricsUpdate(account: FundedAccount) {
    // Simulate small random changes for development
    const pnlChange = (Math.random() - 0.5) * 50 // +/- $25
    const newDailyPnL = account.metrics.dailyPnL + pnlChange
    
    // Update metrics
    account.metrics.dailyPnL = newDailyPnL
    account.metrics.totalPnL += pnlChange
    
    // Update drawdown if we made new lows
    if (newDailyPnL < 0) {
      const currentEquity = account.currentBalance + newDailyPnL
      const drawdown = Math.max(0, account.metrics.maxPeakEquity - currentEquity)
      account.metrics.currentDrawdown = drawdown
    }
    
    account.lastUpdated = new Date().toISOString()
    
    // Check for new violations
    checkForViolations(account)
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  
  function checkForViolations(account: FundedAccount) {
    const { rules, metrics } = account
    
    // Check daily loss limit
    if (metrics.dailyPnL <= -rules.maxDailyLoss) {
      const violation: RuleViolation = {
        id: `daily_loss_${account.id}_${Date.now()}`,
        type: 'daily_loss_limit',
        triggeredAt: new Date().toISOString(),
        ruleLimit: rules.maxDailyLoss,
        actualValue: Math.abs(metrics.dailyPnL),
        message: `Daily loss limit exceeded: $${Math.abs(metrics.dailyPnL).toFixed(2)} > $${rules.maxDailyLoss}`,
        resolved: false
      }
      
      account.violations.push(violation)
      account.status = 'suspended'
    }
    
    // Check trailing drawdown
    if (metrics.currentDrawdown >= rules.trailingDrawdown) {
      const violation: RuleViolation = {
        id: `drawdown_${account.id}_${Date.now()}`,
        type: 'trailing_drawdown',
        triggeredAt: new Date().toISOString(),
        ruleLimit: rules.trailingDrawdown,
        actualValue: metrics.currentDrawdown,
        message: `Trailing drawdown limit exceeded: $${metrics.currentDrawdown.toFixed(2)} > $${rules.trailingDrawdown}`,
        resolved: false
      }
      
      account.violations.push(violation)
      account.status = 'suspended'
    }
  }
  
  async function flattenPositions(accountId: string) {
    const account = accounts.value.find(acc => acc.id === accountId)
    if (!account) return
    
    try {
      if (import.meta.env.DEV) {
        // Mock position flattening
        account.metrics.openPositions = 0
        account.metrics.totalContracts = 0
        account.lastUpdated = new Date().toISOString()
        return { success: true, message: 'All positions flattened' }
      }
      
      const response = await fetch(`/api/funded-accounts/${accountId}/flatten`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to flatten positions')
      }
      
      const result = await response.json()
      
      // Update local state
      account.metrics.openPositions = 0
      account.metrics.totalContracts = 0
      account.lastUpdated = new Date().toISOString()
      
      return result
      
    } catch (err) {
      console.error('Error flattening positions:', err)
      throw err
    }
  }
  
  function startRealtimeUpdates() {
    if (realtimeEnabled.value) return
    
    realtimeEnabled.value = true
    
    // Update active account every 5 seconds
    updateInterval.value = window.setInterval(async () => {
      if (activeAccountId.value) {
        await updateMetrics(activeAccountId.value)
      }
    }, 5000)
  }
  
  function stopRealtimeUpdates() {
    if (updateInterval.value) {
      clearInterval(updateInterval.value)
      updateInterval.value = null
    }
    realtimeEnabled.value = false
  }
  
  function setActiveAccount(accountId: string) {
    if (accounts.value.find(acc => acc.id === accountId)) {
      activeAccountId.value = accountId
      
      // Immediately update metrics for new active account
      nextTick(() => {
        updateMetrics(accountId)
      })
    }
  }
  
  function getAccountById(accountId: string): FundedAccount | undefined {
    return accounts.value.find(acc => acc.id === accountId)
  }
  
  function getAccountsWithViolations(): FundedAccount[] {
    return accounts.value.filter(acc => 
      acc.violations.some(v => !v.resolved)
    )
  }
  
  // Return store interface
  return {
    // State
    accounts,
    activeAccountId,
    loading,
    error,
    lastUpdate,
    realtimeEnabled,
    
    // Computed
    activeAccount,
    accountsByPlatform,
    totalAccountValue,
    totalDailyPnL,
    activeViolations,
    accountsAtRisk,
    
    // Actions
    fetchAccounts,
    updateMetrics,
    flattenPositions,
    startRealtimeUpdates,
    stopRealtimeUpdates,
    setActiveAccount,
    getAccountById,
    getAccountsWithViolations
  }
})