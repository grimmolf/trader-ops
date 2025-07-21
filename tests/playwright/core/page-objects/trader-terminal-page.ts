// tests/playwright/core/page-objects/trader-terminal-page.ts
import { Page, Locator, expect } from '@playwright/test'

export class TraderTerminalPage {
  readonly page: Page
  readonly dashboard: Locator
  readonly connectionStatus: Locator
  readonly tradingPanel: Locator
  readonly portfolioPanel: Locator
  readonly ordersPanel: Locator
  readonly alertsPanel: Locator
  readonly paperTradingPanel: Locator
  readonly strategyPerformancePanel: Locator
  readonly fundedAccountPanel: Locator

  constructor(page: Page) {
    this.page = page
    this.dashboard = page.locator('[data-testid="trading-dashboard"]')
    this.connectionStatus = page.locator('[data-testid="connection-status"]')
    this.tradingPanel = page.locator('[data-testid="trading-panel"]')
    this.portfolioPanel = page.locator('[data-testid="portfolio-panel"]')
    this.ordersPanel = page.locator('[data-testid="orders-panel"]')
    this.alertsPanel = page.locator('[data-testid="alerts-panel"]')
    this.paperTradingPanel = page.locator('[data-testid="paper-trading-panel"]')
    this.strategyPerformancePanel = page.locator('[data-testid="strategy-performance-panel"]')
    this.fundedAccountPanel = page.locator('[data-testid="funded-account-panel"]')
  }

  async initialize() {
    await this.page.goto('http://localhost:8000/app')
    await this.waitForDashboardReady()
  }

  async waitForDashboardReady() {
    await this.dashboard.waitFor({ state: 'visible', timeout: 30000 })
    await this.connectionStatus.waitFor({ state: 'visible', timeout: 10000 })
    
    // Wait for all critical panels to load
    await Promise.all([
      this.tradingPanel.waitFor({ state: 'visible' }),
      this.portfolioPanel.waitFor({ state: 'visible' }),
      this.ordersPanel.waitFor({ state: 'visible' })
    ])
  }

  async verifyAllBrokerConnections() {
    const brokers = ['tradovate', 'tastytrade', 'simulator']
    
    for (const broker of brokers) {
      const brokerStatus = this.page.locator(`[data-testid="broker-status-${broker}"]`)
      await expect(brokerStatus).toContainText('Connected', { timeout: 15000 })
    }
  }

  async sendTradingViewWebhook(alertData: any) {
    return await this.page.evaluate(async (data) => {
      const response = await fetch('/webhook/tradingview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Signature': 'test_signature'
        },
        body: JSON.stringify(data)
      })
      
      return {
        status: response.status,
        data: await response.json()
      }
    }, alertData)
  }

  async waitForTradeExecution(symbol: string, action: string) {
    const alertSelector = `[data-testid="alert-${symbol}-${action}"]`
    const orderWorkingSelector = `[data-testid="order-${symbol}-working"]`
    const orderFilledSelector = `[data-testid="order-${symbol}-filled"]`
    
    // Wait for alert to appear
    await this.page.waitForSelector(alertSelector, { timeout: 10000 })
    
    // Wait for order execution
    await this.page.waitForSelector(orderWorkingSelector, { timeout: 15000 })
    await this.page.waitForSelector(orderFilledSelector, { timeout: 20000 })
    
    // Verify position update
    const positionSelector = `[data-testid="position-${symbol}"]`
    await expect(this.page.locator(positionSelector)).toBeVisible()
  }

  async testPaperTradingWorkflow() {
    // Navigate to paper trading panel
    await this.paperTradingPanel.click()
    
    // Verify paper trading accounts are loaded
    await expect(this.page.locator('[data-testid="paper-account-simulator"]')).toBeVisible()
    await expect(this.page.locator('[data-testid="paper-account-tastytrade"]')).toBeVisible()
    await expect(this.page.locator('[data-testid="paper-account-tradovate"]')).toBeVisible()
    
    // Check initial balance
    const simulatorBalance = await this.page.locator('[data-testid="balance-simulator"]').textContent()
    expect(simulatorBalance).toContain('100,000')
  }

  async testStrategyPerformanceMonitoring() {
    // Navigate to strategy performance panel
    await this.strategyPerformancePanel.click()
    
    // Verify strategy cards are loaded
    await expect(this.page.locator('[data-testid="strategy-card"]').first()).toBeVisible()
    
    // Check for strategy metrics
    await expect(this.page.locator('[data-testid="win-rate"]')).toBeVisible()
    await expect(this.page.locator('[data-testid="current-set-progress"]')).toBeVisible()
  }

  async testFundedAccountRiskManagement() {
    // Navigate to funded account panel
    await this.fundedAccountPanel.click()
    
    // Verify risk meters are visible
    await expect(this.page.locator('[data-testid="daily-pnl-meter"]')).toBeVisible()
    await expect(this.page.locator('[data-testid="drawdown-meter"]')).toBeVisible()
    await expect(this.page.locator('[data-testid="profit-target-progress"]')).toBeVisible()
    
    // Check account selector
    await expect(this.page.locator('[data-testid="account-selector"]')).toBeVisible()
  }

  async testMultiBrokerOrderEntry() {
    const brokers = ['tradovate', 'tastytrade', 'simulator']
    
    for (const broker of brokers) {
      // Select broker
      await this.page.selectOption('[data-testid="broker-selector"]', broker)
      
      // Fill order form
      await this.page.fill('[data-testid="order-symbol"]', 'ES')
      await this.page.fill('[data-testid="order-quantity"]', '1')
      await this.page.selectOption('[data-testid="order-action"]', 'buy')
      
      // Submit order
      await this.page.click('[data-testid="submit-order"]')
      
      // Verify order submission
      await expect(this.page.locator(`[data-testid="order-${broker}-submitted"]`)).toBeVisible()
    }
  }

  async takeFullPageScreenshot(filename: string) {
    await this.page.screenshot({
      path: `tests/screenshots/${filename}`,
      fullPage: true
    })
  }

  async verifyWebSocketConnection() {
    // Check WebSocket connection status
    await expect(this.page.locator('[data-testid="websocket-status"]')).toContainText('Connected')
    
    // Verify real-time data updates
    const quoteElement = this.page.locator('[data-testid="quote-ES"]')
    await expect(quoteElement).toBeVisible()
    
    // Wait for quote to update (indicates WebSocket is working)
    const initialQuote = await quoteElement.textContent()
    await this.page.waitForFunction(
      (element, initial) => element.textContent !== initial,
      quoteElement,
      initialQuote,
      { timeout: 10000 }
    )
  }

  async verifyRealTimeUpdates() {
    // Test real-time portfolio updates
    const portfolioValue = this.page.locator('[data-testid="portfolio-value"]')
    await expect(portfolioValue).toBeVisible()
    
    // Test real-time position updates
    const positionsCount = this.page.locator('[data-testid="positions-count"]')
    await expect(positionsCount).toBeVisible()
    
    // Test real-time order updates
    const ordersCount = this.page.locator('[data-testid="orders-count"]')
    await expect(ordersCount).toBeVisible()
  }
}