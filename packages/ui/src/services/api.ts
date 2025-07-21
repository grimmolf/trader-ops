import { ref } from 'vue'

// Re-export types from stores
export type { Quote, Account, OrderRequest } from '../stores'

// Connection state
export const connectionState = ref<'connected' | 'disconnected' | 'connecting'>('disconnected')

// API client
class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`)
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE'
    })
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  // Trading endpoints
  async getAccounts() {
    return this.get('/api/v1/accounts')
  }

  async getPositions(accountId: string) {
    return this.get(`/api/v1/accounts/${accountId}/positions`)
  }

  async getOrders(accountId: string) {
    return this.get(`/api/v1/accounts/${accountId}/orders`)
  }

  async submitOrder(orderRequest: any) {
    return this.post('/api/v1/orders', orderRequest)
  }

  async cancelOrder(orderId: string) {
    return this.delete(`/api/v1/orders/${orderId}`)
  }

  async getQuotes(symbols: string[]) {
    const symbolsParam = symbols.join(',')
    return this.get(`/api/v1/quotes?symbols=${symbolsParam}`)
  }

  async getQuote(symbol: string) {
    return this.get(`/api/v1/quotes/${symbol}`)
  }

  // Strategy performance endpoints
  async getStrategyPerformance() {
    return this.get('/api/strategies/performance')
  }

  async updateStrategyMode(strategyId: string, newMode: string) {
    return this.post(`/api/strategies/${strategyId}/mode`, { newMode })
  }

  // Paper trading endpoints
  async getPaperAccounts() {
    return this.get('/api/paper-trading/accounts')
  }

  async submitPaperOrder(orderRequest: any) {
    return this.post('/api/paper-trading/alerts', orderRequest)
  }

  async resetPaperAccount(accountId: string) {
    return this.post(`/api/paper-trading/accounts/${accountId}/reset`, {})
  }

  // TradeNote endpoints
  async getTradeNoteData() {
    return this.get('/api/tradenote/trades')
  }

  async getCalendarData(year: number) {
    return this.get(`/api/tradenote/calendar/${year}`)
  }

  // Health check
  async health() {
    return this.get('/health')
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      await this.health()
      connectionState.value = 'connected'
      return true
    } catch (error) {
      connectionState.value = 'disconnected'
      return false
    }
  }
}

// Export singleton instance
export const api = new ApiClient()

// Initialize connection on module load
api.testConnection()