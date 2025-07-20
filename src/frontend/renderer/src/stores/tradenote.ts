/**
 * TradeNote Pinia Store for TraderTerminal
 * 
 * Manages TradeNote integration state, configuration, and API communication.
 * Provides reactive data for TradeNote components and handles trade syncing.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface TradeNoteConfig {
  base_url: string
  app_id: string
  master_key: string
  enabled: boolean
  auto_sync: boolean
  timeout_seconds: number
  retry_attempts: number
}

export interface TradeNoteCalendarData {
  date: string
  value: number
  trades_count: number
  win_rate?: number
}

export interface TradeNoteStatistics {
  totalPnL: number
  totalTrades: number
  winRate: number
  avgTradeSize: number
  pnlChange?: number
  tradesChange?: number
  winRateChange?: number
  avgTradeSizeChange?: number
  bestDay: number
  worstDay: number
  avgDailyPnL: number
  largestWin: number
  largestLoss: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  recoveryFactor: number
  maxConsecutiveWins: number
  maxConsecutiveLosses: number
  avgTimeInTrade: number
  tradingDays: number
  avgTradesPerDay: number
  mostActiveSymbol: string
  totalCommission: number
  commissionPercentage: number
  paperTrades: number
  liveTrades: number
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  errors?: string[]
}

export const useTradeNoteStore = defineStore('tradenote', () => {
  // State
  const config = ref<TradeNoteConfig>({
    base_url: 'http://localhost:8082',
    app_id: '',
    master_key: '',
    enabled: false,
    auto_sync: false,
    timeout_seconds: 30,
    retry_attempts: 3
  })

  const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const lastError = ref<string | null>(null)
  const isInitialized = ref(false)

  // Sync status
  const syncStatus = ref({
    status: 'idle' as 'idle' | 'syncing' | 'success' | 'error',
    lastSync: null as string | null,
    message: null as string | null
  })

  // Cache
  const calendarCache = ref<Map<string, TradeNoteCalendarData[]>>(new Map())
  const statisticsCache = ref<Map<string, TradeNoteStatistics>>(new Map())
  const cacheExpiry = ref<Map<string, number>>(new Map())

  // Cache duration (5 minutes)
  const CACHE_DURATION = 5 * 60 * 1000

  // Computed
  const isConnected = computed(() => connectionStatus.value === 'connected')
  const isEnabled = computed(() => config.value.enabled)

  // Private methods
  function generateCacheKey(method: string, params?: any): string {
    return params ? `${method}_${JSON.stringify(params)}` : method
  }

  function isCacheValid(key: string): boolean {
    const expiry = cacheExpiry.value.get(key)
    return expiry ? Date.now() < expiry : false
  }

  function setCacheExpiry(key: string): void {
    cacheExpiry.value.set(key, Date.now() + CACHE_DURATION)
  }

  async function makeApiRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    if (!config.value.enabled) {
      return {
        success: false,
        message: 'TradeNote integration is disabled'
      }
    }

    if (connectionStatus.value !== 'connected') {
      return {
        success: false,
        message: 'Not connected to TradeNote'
      }
    }

    try {
      const url = `${config.value.base_url.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        signal: AbortSignal.timeout(config.value.timeout_seconds * 1000)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      return {
        success: true,
        data: data.result || data
      }
    } catch (error: any) {
      console.error('TradeNote API request failed:', error)
      
      return {
        success: false,
        message: error.message || 'API request failed',
        errors: [error.message]
      }
    }
  }

  // Public methods
  async function initialize(): Promise<void> {
    if (isInitialized.value) return

    try {
      // Load config from electron main process or localStorage
      const savedConfig = await loadConfig()
      if (savedConfig) {
        config.value = { ...config.value, ...savedConfig }
      }

      isInitialized.value = true

      // Auto-connect if enabled
      if (config.value.enabled) {
        await checkConnection()
      }
    } catch (error: any) {
      console.error('Failed to initialize TradeNote store:', error)
      lastError.value = error.message
    }
  }

  async function loadConfig(): Promise<Partial<TradeNoteConfig> | null> {
    try {
      // Try to load from electron main process first
      if (window.electron?.getTradeNoteConfig) {
        return await window.electron.getTradeNoteConfig()
      }

      // Fallback to localStorage
      const saved = localStorage.getItem('tradenote_config')
      return saved ? JSON.parse(saved) : null
    } catch (error) {
      console.error('Failed to load TradeNote config:', error)
      return null
    }
  }

  async function saveConfig(): Promise<void> {
    try {
      // Save to electron main process if available
      if (window.electron?.setTradeNoteConfig) {
        await window.electron.setTradeNoteConfig(config.value)
      }

      // Also save to localStorage as fallback
      localStorage.setItem('tradenote_config', JSON.stringify(config.value))
    } catch (error) {
      console.error('Failed to save TradeNote config:', error)
      throw error
    }
  }

  async function checkConnection(): Promise<boolean> {
    if (!config.value.enabled) {
      connectionStatus.value = 'disconnected'
      return false
    }

    connectionStatus.value = 'connecting'
    lastError.value = null

    try {
      // Test connection with health check
      const response = await makeApiRequest('health')
      
      if (response.success) {
        connectionStatus.value = 'connected'
        return true
      } else {
        connectionStatus.value = 'error'
        lastError.value = response.message || 'Connection failed'
        return false
      }
    } catch (error: any) {
      connectionStatus.value = 'error'
      lastError.value = error.message || 'Connection failed'
      return false
    }
  }

  async function testConnection(testConfig: Partial<TradeNoteConfig>): Promise<ApiResponse> {
    try {
      const testUrl = `${testConfig.base_url?.replace(/\/$/, '')}/health`
      
      const response = await fetch(testUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout for test
      })

      if (response.ok) {
        return {
          success: true,
          message: 'Connection successful'
        }
      } else {
        return {
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`
        }
      }
    } catch (error: any) {
      return {
        success: false,
        message: error.message || 'Connection test failed'
      }
    }
  }

  async function updateConfig(newConfig: Partial<TradeNoteConfig>): Promise<ApiResponse> {
    try {
      // Update config
      config.value = { ...config.value, ...newConfig }

      // Save config
      await saveConfig()

      // Test connection if enabled
      if (config.value.enabled) {
        const connected = await checkConnection()
        if (!connected) {
          return {
            success: false,
            message: 'Config saved but connection failed'
          }
        }
      } else {
        connectionStatus.value = 'disconnected'
      }

      return {
        success: true,
        message: 'Configuration updated successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        message: error.message || 'Failed to update configuration'
      }
    }
  }

  async function getCalendarData(
    startDate: Date, 
    endDate: Date
  ): Promise<ApiResponse<TradeNoteCalendarData[]>> {
    const cacheKey = generateCacheKey('calendar', { 
      start: startDate.toISOString(), 
      end: endDate.toISOString() 
    })

    // Check cache first
    if (isCacheValid(cacheKey)) {
      const cached = calendarCache.value.get(cacheKey)
      if (cached) {
        return {
          success: true,
          data: cached
        }
      }
    }

    const params = new URLSearchParams({
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0]
    })

    const response = await makeApiRequest<TradeNoteCalendarData[]>(`api/calendar?${params}`)

    // Cache successful response
    if (response.success && response.data) {
      calendarCache.value.set(cacheKey, response.data)
      setCacheExpiry(cacheKey)
    }

    return response
  }

  async function getTradeStatistics(timeframe: string = '30d'): Promise<ApiResponse<TradeNoteStatistics>> {
    const cacheKey = generateCacheKey('statistics', { timeframe })

    // Check cache first
    if (isCacheValid(cacheKey)) {
      const cached = statisticsCache.value.get(cacheKey)
      if (cached) {
        return {
          success: true,
          data: cached
        }
      }
    }

    const params = new URLSearchParams({ timeframe })
    const response = await makeApiRequest<TradeNoteStatistics>(`api/stats?${params}`)

    // Cache successful response
    if (response.success && response.data) {
      statisticsCache.value.set(cacheKey, response.data)
      setCacheExpiry(cacheKey)
    }

    return response
  }

  async function syncData(): Promise<ApiResponse> {
    if (syncStatus.value.status === 'syncing') {
      return {
        success: false,
        message: 'Sync already in progress'
      }
    }

    syncStatus.value.status = 'syncing'
    syncStatus.value.message = 'Syncing with TradeNote...'

    try {
      // Clear caches to force fresh data
      calendarCache.value.clear()
      statisticsCache.value.clear()
      cacheExpiry.value.clear()

      // Trigger a sync by calling the sync endpoint
      const response = await makeApiRequest('api/sync', {
        method: 'POST'
      })

      if (response.success) {
        syncStatus.value.status = 'success'
        syncStatus.value.lastSync = new Date().toISOString()
        syncStatus.value.message = 'Sync completed successfully'
      } else {
        syncStatus.value.status = 'error'
        syncStatus.value.message = response.message || 'Sync failed'
      }

      return response
    } catch (error: any) {
      syncStatus.value.status = 'error'
      syncStatus.value.message = error.message || 'Sync failed'

      return {
        success: false,
        message: error.message || 'Sync failed'
      }
    }
  }

  async function uploadTrades(trades: any[]): Promise<ApiResponse> {
    return await makeApiRequest('api/trades', {
      method: 'POST',
      body: JSON.stringify({
        data: trades,
        selectedBroker: 'TraderTerminal',
        uploadMfePrices: false
      })
    })
  }

  function clearCache(): void {
    calendarCache.value.clear()
    statisticsCache.value.clear()
    cacheExpiry.value.clear()
  }

  function disconnect(): void {
    connectionStatus.value = 'disconnected'
    lastError.value = null
    syncStatus.value.status = 'idle'
    clearCache()
  }

  // Return store interface
  return {
    // State
    config,
    connectionStatus,
    lastError,
    isInitialized,
    syncStatus,

    // Computed
    isConnected,
    isEnabled,

    // Actions
    initialize,
    checkConnection,
    testConnection,
    updateConfig,
    getCalendarData,
    getTradeStatistics,
    syncData,
    uploadTrades,
    clearCache,
    disconnect
  }
})

// Extend window interface for electron integration
declare global {
  interface Window {
    electron?: {
      getTradeNoteConfig?: () => Promise<Partial<TradeNoteConfig>>
      setTradeNoteConfig?: (config: TradeNoteConfig) => Promise<void>
      openExternal?: (url: string) => void
    }
  }
}