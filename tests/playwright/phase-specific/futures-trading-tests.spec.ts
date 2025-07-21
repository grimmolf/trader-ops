// tests/playwright/phase-specific/futures-trading-tests.spec.ts
import { test, expect } from '../core/base-test'
import { TradingWorkflowTest } from '../test-suites/trading-workflows/base-trading-test'

// Critical futures trading scenarios as defined in Phase 0
const futuresTradingScenarios = {
  trades: [
    { symbol: 'ES', action: 'buy', quantity: 1, account_group: 'paper_simulator', strategy: 'futures_breakout' },
    { symbol: 'NQ', action: 'buy', quantity: 1, account_group: 'paper_tradovate', strategy: 'momentum_scalp' },
    { symbol: 'ES', action: 'sell', quantity: 1, account_group: 'topstep', strategy: 'funded_account_test' }
  ],
  validateFinalState: async (page) => {
    // Verify strategy performance tracking
    await expect(page.locator('[data-testid="strategy-performance"]')).toBeVisible()
    await expect(page.locator('[data-testid="paper-trades-count"]')).toContainText('3')
    
    // Verify funded account risk monitoring
    await expect(page.locator('[data-testid="funded-account-status"]')).toContainText('Within Limits')
  }
}

// Create automated futures trading test
TradingWorkflowTest.createTest('Phase 0: Futures Trading MVP', futuresTradingScenarios)

test.describe('Phase 0: Critical Futures Trading', () => {
  test('Paper trading validation - 100+ trades requirement', async ({ 
    traderTerminalPage, 
    performanceTracker 
  }) => {
    await traderTerminalPage.initialize()
    
    // Execute 100+ paper trades rapidly
    const tradeCount = 100
    const startTime = Date.now()
    
    for (let i = 0; i < tradeCount; i++) {
      const trade = {
        symbol: 'ES',
        action: i % 2 === 0 ? 'buy' : 'sell',
        quantity: 1,
        account_group: 'paper_simulator',
        strategy: `paper_validation_${Math.floor(i/10)}`
      }
      
      await traderTerminalPage.sendTradingViewWebhook(trade)
      
      // Verify every 10th trade to avoid overwhelming
      if (i % 10 === 0) {
        await traderTerminalPage.waitForTradeExecution(trade.symbol, trade.action)
      }
    }
    
    const totalTime = Date.now() - startTime
    
    // Verify performance requirements
    expect(totalTime).toBeLessThan(300000) // < 5 minutes for 100 trades
    
    // Verify paper trading metrics
    await expect(page.locator('[data-testid="total-paper-trades"]')).toContainText('100')
    
    // Check win rate calculation
    const winRate = await page.locator('[data-testid="win-rate"]').textContent()
    expect(parseFloat(winRate.replace('%', ''))).toBeGreaterThan(0)
  })
  
  test('Funded account risk management validation', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    // Test risk limits enforcement
    const riskTestTrade = {
      symbol: 'ES',
      action: 'buy',
      quantity: 10, // Large position to test limits
      account_group: 'topstep',
      strategy: 'risk_test'
    }
    
    const response = await traderTerminalPage.sendTradingViewWebhook(riskTestTrade)
    
    // Should be rejected due to position size limits
    expect(response.status).toBe(400)
    
    // Verify risk violation appears in UI
    await page.waitForSelector('[data-testid="risk-violation"]')
    await expect(page.locator('[data-testid="risk-violation"]')).toContainText('Position size exceeds limit')
  })

  test('TradingView webhook integration', async ({ traderTerminalPage, networkMonitor }) => {
    await traderTerminalPage.initialize()
    
    // Test basic webhook reception
    const testAlert = {
      symbol: 'ES',
      action: 'buy',
      quantity: 1,
      strategy: 'webhook_test',
      account_group: 'paper_simulator'
    }
    
    const response = await traderTerminalPage.sendTradingViewWebhook(testAlert)
    expect(response.status).toBe(200)
    expect(response.data.status).toBe('received')
    
    // Verify webhook was processed
    await networkMonitor.verifyAPIEndpoint('/webhook/tradingview', 200)
    
    // Verify alert appears in UI
    await expect(page.locator('[data-testid="alert-ES-buy"]')).toBeVisible()
  })

  test('Multi-broker paper trading routing', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    const brokerTests = [
      { symbol: 'ES', account_group: 'paper_tradovate', broker: 'tradovate' },
      { symbol: 'AAPL', account_group: 'paper_tastytrade', broker: 'tastytrade' },
      { symbol: 'SPY', account_group: 'paper_simulator', broker: 'simulator' }
    ]
    
    for (const test of brokerTests) {
      const trade = {
        symbol: test.symbol,
        action: 'buy',
        quantity: 1,
        account_group: test.account_group,
        strategy: `routing_test_${test.broker}`
      }
      
      const response = await traderTerminalPage.sendTradingViewWebhook(trade)
      expect(response.status).toBe(200)
      
      // Verify trade was routed to correct broker
      await expect(page.locator(`[data-testid="trade-${test.broker}"]`)).toBeVisible()
    }
  })

  test('Strategy performance monitoring', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    // Execute trades for a strategy to trigger performance tracking
    const strategyTrades = Array.from({ length: 20 }, (_, i) => ({
      symbol: 'ES',
      action: i % 2 === 0 ? 'buy' : 'sell',
      quantity: 1,
      account_group: 'paper_simulator',
      strategy: 'performance_test_strategy'
    }))
    
    for (const trade of strategyTrades) {
      await traderTerminalPage.sendTradingViewWebhook(trade)
    }
    
    // Navigate to strategy performance panel
    await page.click('[data-testid="strategy-performance-tab"]')
    
    // Verify strategy appears in performance tracking
    await expect(page.locator('[data-testid="strategy-card-performance_test_strategy"]')).toBeVisible()
    
    // Verify performance metrics are calculated
    await expect(page.locator('[data-testid="strategy-win-rate"]')).toBeVisible()
    await expect(page.locator('[data-testid="current-set-progress"]')).toContainText('20/20')
  })

  test('Real-time position and P&L updates', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    // Execute a trade
    const trade = {
      symbol: 'ES',
      action: 'buy',
      quantity: 1,
      account_group: 'paper_simulator',
      strategy: 'realtime_test'
    }
    
    await traderTerminalPage.sendTradingViewWebhook(trade)
    await traderTerminalPage.waitForTradeExecution(trade.symbol, trade.action)
    
    // Verify position appears in real-time
    await expect(page.locator('[data-testid="position-ES"]')).toBeVisible()
    
    // Verify P&L is calculated and displayed
    const pnlElement = page.locator('[data-testid="position-ES-pnl"]')
    await expect(pnlElement).toBeVisible()
    
    // Execute opposite trade to close position
    const closeTrade = {
      symbol: 'ES',
      action: 'sell',
      quantity: 1,
      account_group: 'paper_simulator',
      strategy: 'realtime_test'
    }
    
    await traderTerminalPage.sendTradingViewWebhook(closeTrade)
    
    // Verify position is closed
    await expect(page.locator('[data-testid="position-ES"]')).not.toBeVisible()
  })

  test('Tradovate demo account integration', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    // Test Tradovate demo account paper trading
    const tradovateTrade = {
      symbol: 'ES',
      action: 'buy',
      quantity: 1,
      account_group: 'paper_tradovate',
      strategy: 'tradovate_demo_test'
    }
    
    const response = await traderTerminalPage.sendTradingViewWebhook(tradovateTrade)
    expect(response.status).toBe(200)
    
    // Verify Tradovate connection status
    await expect(page.locator('[data-testid="broker-status-tradovate"]')).toContainText('Connected')
    
    // Verify trade execution via Tradovate
    await traderTerminalPage.waitForTradeExecution(tradovateTrade.symbol, tradovateTrade.action)
    
    // Check that trade was processed by Tradovate demo
    await expect(page.locator('[data-testid="order-tradovate-demo"]')).toBeVisible()
  })

  test('Emergency stop and position flattening', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    // Create multiple positions
    const positions = [
      { symbol: 'ES', action: 'buy', quantity: 1 },
      { symbol: 'NQ', action: 'buy', quantity: 1 },
      { symbol: 'YM', action: 'sell', quantity: 1 }
    ]
    
    for (const pos of positions) {
      await traderTerminalPage.sendTradingViewWebhook({
        ...pos,
        account_group: 'paper_simulator',
        strategy: 'emergency_test'
      })
    }
    
    // Verify positions are created
    await expect(page.locator('[data-testid="position-ES"]')).toBeVisible()
    await expect(page.locator('[data-testid="position-NQ"]')).toBeVisible()
    await expect(page.locator('[data-testid="position-YM"]')).toBeVisible()
    
    // Trigger emergency stop
    await page.click('[data-testid="emergency-stop"]')
    await page.click('[data-testid="confirm-emergency-stop"]')
    
    // Verify all positions are closed
    await expect(page.locator('[data-testid="position-ES"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="position-NQ"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="position-YM"]')).not.toBeVisible()
    
    // Verify emergency stop status
    await expect(page.locator('[data-testid="emergency-status"]')).toContainText('All positions flattened')
  })
})