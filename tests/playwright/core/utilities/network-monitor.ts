// tests/playwright/core/utilities/network-monitor.ts
import { Page } from '@playwright/test'
import { writeFileSync } from 'fs'

export class NetworkMonitor {
  private page: Page
  private requests: any[] = []
  private responses: any[] = []
  private failures: any[] = []
  private webSocketMessages: any[] = []

  constructor(page: Page) {
    this.page = page
  }

  async startMonitoring() {
    this.page.on('request', (request) => {
      this.requests.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        postData: request.postData(),
        timestamp: new Date().toISOString()
      })
    })

    this.page.on('response', (response) => {
      const responseData = {
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers(),
        timestamp: new Date().toISOString()
      }
      
      this.responses.push(responseData)
      
      if (response.status() >= 400) {
        this.failures.push(responseData)
      }
    })

    // Monitor WebSocket connections
    this.page.on('websocket', (webSocket) => {
      webSocket.on('framereceived', (frame) => {
        this.webSocketMessages.push({
          type: 'received',
          payload: frame.payload,
          timestamp: new Date().toISOString()
        })
      })

      webSocket.on('framesent', (frame) => {
        this.webSocketMessages.push({
          type: 'sent',
          payload: frame.payload,
          timestamp: new Date().toISOString()
        })
      })
    })
  }

  async generateReport() {
    const report = {
      summary: {
        totalRequests: this.requests.length,
        totalResponses: this.responses.length,
        failedRequests: this.failures.length,
        successRate: this.responses.length > 0 
          ? ((this.responses.length - this.failures.length) / this.responses.length * 100).toFixed(2) 
          : 100,
        webSocketMessages: this.webSocketMessages.length
      },
      requests: this.requests,
      responses: this.responses,
      failures: this.failures,
      webSocketActivity: this.webSocketMessages,
      timestamp: new Date().toISOString()
    }

    // Ensure reports directory exists
    const reportsDir = 'tests/reports'
    try {
      require('fs').mkdirSync(reportsDir, { recursive: true })
    } catch (e) {
      // Directory already exists
    }

    writeFileSync(
      `${reportsDir}/network-report-${Date.now()}.json`,
      JSON.stringify(report, null, 2)
    )

    return report
  }

  getFailures() { return this.failures }
  getRequests() { return this.requests }
  getResponses() { return this.responses }
  getWebSocketMessages() { return this.webSocketMessages }

  // Helper methods for common network validations
  async verifyAPIEndpoint(endpoint: string, expectedStatus: number = 200) {
    const matchingResponses = this.responses.filter(r => r.url.includes(endpoint))
    if (matchingResponses.length === 0) {
      throw new Error(`No requests found for endpoint: ${endpoint}`)
    }
    
    const lastResponse = matchingResponses[matchingResponses.length - 1]
    if (lastResponse.status !== expectedStatus) {
      throw new Error(`Expected status ${expectedStatus} for ${endpoint}, got ${lastResponse.status}`)
    }
    
    return lastResponse
  }

  async verifyWebSocketActivity() {
    if (this.webSocketMessages.length === 0) {
      throw new Error('No WebSocket activity detected')
    }
    
    const recentMessages = this.webSocketMessages.filter(
      msg => Date.now() - new Date(msg.timestamp).getTime() < 30000
    )
    
    if (recentMessages.length === 0) {
      throw new Error('No recent WebSocket activity (last 30 seconds)')
    }
    
    return recentMessages
  }

  async validateTradingViewWebhook() {
    const webhookRequests = this.requests.filter(r => r.url.includes('/webhook/tradingview'))
    if (webhookRequests.length === 0) {
      throw new Error('No TradingView webhook requests detected')
    }
    
    const webhookResponses = this.responses.filter(r => r.url.includes('/webhook/tradingview'))
    const successfulWebhooks = webhookResponses.filter(r => r.status === 200)
    
    return {
      totalWebhooks: webhookRequests.length,
      successfulWebhooks: successfulWebhooks.length,
      failureRate: ((webhookRequests.length - successfulWebhooks.length) / webhookRequests.length * 100).toFixed(2)
    }
  }
}