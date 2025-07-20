/**
 * TraderTerminal API Service
 * 
 * Provides unified interface for communication with backend DataHub server
 * and all integrated broker feeds (Tradovate, Schwab, Tastytrade, TopstepX).
 */

import { ref, reactive } from 'vue'

// Types for API responses
interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

interface Quote {
  symbol: string
  bid: number
  ask: number
  last: number
  change: number
  changePercent: number
  volume: number
  timestamp: string
  feed: string
}

interface Position {
  symbol: string
  quantity: number
  averagePrice: number
  marketValue: number
  unrealizedPnL: number
  realizedPnL: number
  feed: string
  accountNumber: string
}

interface Account {
  accountNumber: string
  accountType: string
  balance: number
  buyingPower: number
  netLiquidatingValue: number
  feed: string
  nickname?: string
}

interface Order {
  orderId: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  orderType: 'market' | 'limit' | 'stop'
  price?: number
  status: string
  filled: number
  remaining: number
  timestamp: string
  feed: string
  accountNumber: string
}

interface FundedAccount {
  accountNumber: string
  provider: 'topstep' | 'apex' | 'tradeday'
  balance: number
  dailyLoss: number
  maxDailyLoss: number
  totalLoss: number
  maxTotalLoss: number
  profitTarget: number
  currentDrawdown: number
  status: 'active' | 'breached' | 'suspended'
  tradingPermissions: string[]
}

interface HistoricalBar {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface OrderRequest {
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  orderType: 'market' | 'limit' | 'stop'
  price?: number
  stopPrice?: number
  timeInForce?: 'day' | 'gtc' | 'ioc' | 'fok'
  accountNumber: string
  feed: string
}

// Connection state
export const connectionState = reactive({
  datahub: false,
  tradovate: false,
  schwab: false,
  tastytrade: false,
  topstepx: false,
  websocket: false
})

// API Base URLs
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

/**
 * Main API service class
 */
class TraderTerminalAPI {
  private baseUrl: string
  private wsUrl: string
  private websocket: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor() {
    this.baseUrl = API_BASE_URL
    this.wsUrl = WS_BASE_URL
  }

  // HTTP request wrapper
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      })

      if (!response.ok) {
        return {
          success: false,
          error: `HTTP ${response.status}: ${response.statusText}`
        }
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  // GET request
  private async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  // POST request
  private async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  // PUT request
  private async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  // DELETE request
  private async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // ==================== CONNECTION MANAGEMENT ====================

  /**
   * Check connection status to all services
   */
  async checkConnectionStatus(): Promise<ApiResponse<typeof connectionState>> {
    const response = await this.get<any>('/api/status')
    
    if (response.success && response.data) {
      connectionState.datahub = response.data.datahub || false
      connectionState.tradovate = response.data.feeds?.tradovate || false
      connectionState.schwab = response.data.feeds?.schwab || false
      connectionState.tastytrade = response.data.feeds?.tastytrade || false
      connectionState.topstepx = response.data.feeds?.topstepx || false
    }

    return {
      success: response.success,
      data: connectionState,
      error: response.error
    }
  }

  /**
   * Connect to WebSocket for real-time updates
   */
  connectWebSocket(onMessage?: (data: any) => void): void {
    if (this.websocket) {
      this.websocket.close()
    }

    this.websocket = new WebSocket(`${this.wsUrl}/ws`)

    this.websocket.onopen = () => {
      console.log('WebSocket connected')
      connectionState.websocket = true
      this.reconnectAttempts = 0
    }

    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (onMessage) {
          onMessage(data)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    this.websocket.onclose = () => {
      console.log('WebSocket disconnected')
      connectionState.websocket = false
      this.handleWebSocketReconnect()
    }

    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      connectionState.websocket = false
    }
  }

  /**
   * Handle WebSocket reconnection
   */
  private handleWebSocketReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting WebSocket reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
        this.connectWebSocket()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  /**
   * Subscribe to real-time data feeds
   */
  subscribeToMarketData(symbols: string[], feeds?: string[]): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const message = {
        action: 'subscribe',
        symbols,
        feeds: feeds || ['tradovate', 'schwab', 'tastytrade']
      }
      this.websocket.send(JSON.stringify(message))
    }
  }

  /**
   * Unsubscribe from market data
   */
  unsubscribeFromMarketData(symbols: string[]): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const message = {
        action: 'unsubscribe',
        symbols
      }
      this.websocket.send(JSON.stringify(message))
    }
  }

  // ==================== MARKET DATA ====================

  /**
   * Get real-time quote for a symbol
   */
  async getQuote(symbol: string, feed?: string): Promise<ApiResponse<Quote>> {
    const params = feed ? `?feed=${feed}` : ''
    return this.get<Quote>(`/api/quotes/${symbol}${params}`)
  }

  /**
   * Get quotes for multiple symbols
   */
  async getQuotes(symbols: string[], feed?: string): Promise<ApiResponse<Quote[]>> {
    const params = new URLSearchParams()
    symbols.forEach(symbol => params.append('symbols', symbol))
    if (feed) params.append('feed', feed)
    
    return this.get<Quote[]>(`/api/quotes?${params.toString()}`)
  }

  /**
   * Get historical data for a symbol
   */
  async getHistoricalData(
    symbol: string,
    timeframe: string,
    startDate?: string,
    endDate?: string,
    feed?: string
  ): Promise<ApiResponse<HistoricalBar[]>> {
    const params = new URLSearchParams({
      timeframe,
      ...(startDate && { start: startDate }),
      ...(endDate && { end: endDate }),
      ...(feed && { feed })
    })

    return this.get<HistoricalBar[]>(`/api/historical/${symbol}?${params.toString()}`)
  }

  /**
   * Search for symbols
   */
  async searchSymbols(query: string, feed?: string): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({ query })
    if (feed) params.append('feed', feed)
    
    return this.get<any[]>(`/api/search?${params.toString()}`)
  }

  // ==================== ACCOUNT MANAGEMENT ====================

  /**
   * Get all accounts across all feeds
   */
  async getAccounts(): Promise<ApiResponse<Account[]>> {
    return this.get<Account[]>('/api/accounts')
  }

  /**
   * Get account details
   */
  async getAccount(accountNumber: string, feed: string): Promise<ApiResponse<Account>> {
    return this.get<Account>(`/api/accounts/${feed}/${accountNumber}`)
  }

  /**
   * Get positions for an account
   */
  async getPositions(accountNumber: string, feed: string): Promise<ApiResponse<Position[]>> {
    return this.get<Position[]>(`/api/accounts/${feed}/${accountNumber}/positions`)
  }

  /**
   * Get all positions across all accounts
   */
  async getAllPositions(): Promise<ApiResponse<Position[]>> {
    return this.get<Position[]>('/api/positions')
  }

  // ==================== TRADING ====================

  /**
   * Place an order
   */
  async placeOrder(order: OrderRequest): Promise<ApiResponse<Order>> {
    return this.post<Order>(`/api/orders/${order.feed}`, order)
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string, feed: string, accountNumber: string): Promise<ApiResponse<any>> {
    return this.delete(`/api/orders/${feed}/${accountNumber}/${orderId}`)
  }

  /**
   * Get order history
   */
  async getOrders(accountNumber?: string, feed?: string): Promise<ApiResponse<Order[]>> {
    const params = new URLSearchParams()
    if (accountNumber) params.append('account', accountNumber)
    if (feed) params.append('feed', feed)
    
    const query = params.toString()
    return this.get<Order[]>(`/api/orders${query ? '?' + query : ''}`)
  }

  /**
   * Get order details
   */
  async getOrder(orderId: string, feed: string, accountNumber: string): Promise<ApiResponse<Order>> {
    return this.get<Order>(`/api/orders/${feed}/${accountNumber}/${orderId}`)
  }

  // ==================== FUNDED ACCOUNTS ====================

  /**
   * Get funded account information
   */
  async getFundedAccounts(): Promise<ApiResponse<FundedAccount[]>> {
    return this.get<FundedAccount[]>('/api/funded-accounts')
  }

  /**
   * Get specific funded account details
   */
  async getFundedAccount(accountNumber: string, provider: string): Promise<ApiResponse<FundedAccount>> {
    return this.get<FundedAccount>(`/api/funded-accounts/${provider}/${accountNumber}`)
  }

  /**
   * Update funded account risk parameters
   */
  async updateFundedAccountRisk(
    accountNumber: string, 
    provider: string, 
    riskParams: any
  ): Promise<ApiResponse<any>> {
    return this.put(`/api/funded-accounts/${provider}/${accountNumber}/risk`, riskParams)
  }

  // ==================== TRADINGVIEW WEBHOOKS ====================

  /**
   * Get webhook configuration
   */
  async getWebhookConfig(): Promise<ApiResponse<any>> {
    return this.get('/api/webhooks/config')
  }

  /**
   * Update webhook configuration
   */
  async updateWebhookConfig(config: any): Promise<ApiResponse<any>> {
    return this.put('/api/webhooks/config', config)
  }

  /**
   * Test webhook endpoint
   */
  async testWebhook(webhookData: any): Promise<ApiResponse<any>> {
    return this.post('/api/webhooks/test', webhookData)
  }

  // ==================== AUTHENTICATION ====================

  /**
   * Get authentication status for all feeds
   */
  async getAuthStatus(): Promise<ApiResponse<any>> {
    return this.get('/api/auth/status')
  }

  /**
   * Initiate OAuth flow for a specific feed
   */
  async initiateOAuth(feed: string): Promise<ApiResponse<{ authUrl: string }>> {
    return this.post(`/api/auth/${feed}/oauth`)
  }

  /**
   * Complete OAuth flow
   */
  async completeOAuth(feed: string, code: string, state?: string): Promise<ApiResponse<any>> {
    return this.post(`/api/auth/${feed}/callback`, { code, state })
  }

  // ==================== BACKTESTING ====================

  /**
   * Start a backtest
   */
  async startBacktest(config: any): Promise<ApiResponse<{ jobId: string }>> {
    return this.post('/api/backtest/start', config)
  }

  /**
   * Get backtest results
   */
  async getBacktestResults(jobId: string): Promise<ApiResponse<any>> {
    return this.get(`/api/backtest/${jobId}/results`)
  }

  /**
   * Get backtest status
   */
  async getBacktestStatus(jobId: string): Promise<ApiResponse<any>> {
    return this.get(`/api/backtest/${jobId}/status`)
  }

  // ==================== ANALYTICS ====================

  /**
   * Get portfolio analytics
   */
  async getPortfolioAnalytics(): Promise<ApiResponse<any>> {
    return this.get('/api/analytics/portfolio')
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(accountNumber?: string, timeframe?: string): Promise<ApiResponse<any>> {
    const params = new URLSearchParams()
    if (accountNumber) params.append('account', accountNumber)
    if (timeframe) params.append('timeframe', timeframe)
    
    const query = params.toString()
    return this.get(`/api/analytics/performance${query ? '?' + query : ''}`)
  }

  // ==================== CLEANUP ====================

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close()
      this.websocket = null
    }
    connectionState.websocket = false
  }
}

// Create singleton instance
export const api = new TraderTerminalAPI()

// Export types
export type {
  ApiResponse,
  Quote,
  Position,
  Account,
  Order,
  FundedAccount,
  HistoricalBar,
  OrderRequest
}