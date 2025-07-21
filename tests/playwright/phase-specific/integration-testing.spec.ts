// tests/playwright/phase-specific/integration-testing.spec.ts
import { test, expect } from '../core/base-test'
import { TradingWorkflowTest } from '../test-suites/trading-workflows/base-trading-test'

// Complete integration test scenario as defined in Phase 3
const fullIntegrationScenario = {
  trades: [
    { symbol: 'ES', action: 'buy', quantity: 1, account_group: 'paper_simulator', strategy: 'integration_simulator' },
    { symbol: 'NQ', action: 'buy', quantity: 1, account_group: 'paper_tradovate', strategy: 'integration_tradovate' },
    { symbol: 'AAPL', action: 'buy', quantity: 100, account_group: 'paper_tastytrade', strategy: 'integration_tastytrade' }
  ],
  validateFinalState: async (page) => {
    await expect(page.locator('[data-testid="integration-test-complete"]')).toBeVisible()
  }
}

// Create the full integration test
TradingWorkflowTest.createTest('Phase 3: Full Integration', fullIntegrationScenario)

test.describe('Phase 3: Enhanced Integration Testing', () => {
  test('End-to-end trading flow validation', async ({ 
    traderTerminalPage, 
    networkMonitor, 
    performanceTracker,
    visualValidator 
  }) => {
    // Initialize and verify all systems
    await traderTerminalPage.initialize()
    await traderTerminalPage.verifyAllBrokerConnections()
    
    // Test complete TradingView → Dashboard → Broker flow
    const endToEndTrade = {
      symbol: 'SPY',
      action: 'buy',
      quantity: 100,
      account_group: 'paper_simulator',
      strategy: 'e2e_integration_test'
    }
    
    // Measure complete workflow performance
    const workflowStart = Date.now()
    
    // Step 1: Send TradingView webhook
    const webhookResponse = await traderTerminalPage.sendTradingViewWebhook(endToEndTrade)
    expect(webhookResponse.status).toBe(200)
    
    // Step 2: Verify webhook processing
    await networkMonitor.verifyAPIEndpoint('/webhook/tradingview', 200)
    
    // Step 3: Wait for trade execution
    await traderTerminalPage.waitForTradeExecution(endToEndTrade.symbol, endToEndTrade.action)
    
    // Step 4: Verify real-time updates
    await traderTerminalPage.verifyRealTimeUpdates()
    
    // Step 5: Verify position appears in portfolio
    await expect(page.locator(`[data-testid="position-${endToEndTrade.symbol}"]`)).toBeVisible()
    
    const workflowTime = Date.now() - workflowStart
    console.log(`Complete E2E workflow time: ${workflowTime}ms`)
    
    // Validate performance requirements
    expect(workflowTime).toBeLessThan(10000) // < 10 seconds for E2E flow
    
    // Take final validation screenshot
    await visualValidator.validateDashboardLayout('e2e-integration-complete')
  })

  test('Multi-broker simultaneous execution', async ({ 
    traderTerminalPage, 
    performanceTracker 
  }) => {
    await traderTerminalPage.initialize()
    
    // Execute trades simultaneously across all brokers
    const simultaneousTrades = [
      { symbol: 'ES', action: 'buy', quantity: 1, account_group: 'paper_tradovate', strategy: 'simul_tradovate' },
      { symbol: 'AAPL', action: 'buy', quantity: 100, account_group: 'paper_tastytrade', strategy: 'simul_tastytrade' },
      { symbol: 'SPY', action: 'buy', quantity: 50, account_group: 'paper_simulator', strategy: 'simul_simulator' }
    ]
    
    // Send all webhooks rapidly
    const webhookPromises = simultaneousTrades.map(trade => 
      traderTerminalPage.sendTradingViewWebhook(trade)
    )
    
    const responses = await Promise.all(webhookPromises)
    
    // Verify all webhooks succeeded
    responses.forEach(response => {
      expect(response.status).toBe(200)
    })
    
    // Verify all trades were executed
    for (const trade of simultaneousTrades) {
      await expect(page.locator(`[data-testid="position-${trade.symbol}"]`))
        .toBeVisible({ timeout: 20000 })
    }
    
    // Verify broker routing worked correctly
    await expect(page.locator('[data-testid="trade-count-tradovate"]')).toContainText('1')
    await expect(page.locator('[data-testid="trade-count-tastytrade"]')).toContainText('1')
    await expect(page.locator('[data-testid="trade-count-simulator"]')).toContainText('1')
  })

  test('Performance under load testing', async ({ 
    traderTerminalPage, 
    performanceTracker,
    networkMonitor 
  }) => {
    await traderTerminalPage.initialize()
    
    // Execute high-frequency trading simulation
    const loadTestTrades = 50
    const startTime = Date.now()
    
    const tradePromises = []
    
    for (let i = 0; i < loadTestTrades; i++) {
      const trade = {
        symbol: i % 2 === 0 ? 'ES' : 'NQ',
        action: i % 3 === 0 ? 'buy' : 'sell',
        quantity: 1,
        account_group: 'paper_simulator',
        strategy: `load_test_${Math.floor(i/10)}`
      }
      
      tradePromises.push(traderTerminalPage.sendTradingViewWebhook(trade))
    }
    
    // Execute all trades
    const responses = await Promise.all(tradePromises)
    const totalTime = Date.now() - startTime
    
    // Verify all trades succeeded
    const successfulTrades = responses.filter(r => r.status === 200).length
    expect(successfulTrades).toBe(loadTestTrades)
    
    // Verify performance under load
    expect(totalTime).toBeLessThan(30000) // < 30 seconds for 50 trades
    console.log(`Load test: ${loadTestTrades} trades in ${totalTime}ms`)
    
    // Measure system performance under load
    await performanceTracker.measureMemoryUsage()
    performanceTracker.validateMemoryUsage(200) // Max 200MB under load
    
    // Verify network stability
    const networkReport = await networkMonitor.generateReport()
    expect(parseFloat(networkReport.summary.successRate)).toBeGreaterThan(95)
  })

  test('Error recovery and resilience testing', async ({ 
    traderTerminalPage, 
    networkMonitor 
  }) => {
    await traderTerminalPage.initialize()
    
    // Test network interruption recovery
    console.log('Testing network interruption recovery...')
    
    // Simulate network failure
    await page.route('**/api/**', route => route.abort())
    
    // Try to send trade during network failure
    const failedTrade = {
      symbol: 'ES',
      action: 'buy',
      quantity: 1,
      account_group: 'paper_simulator',
      strategy: 'network_failure_test'
    }
    
    const failedResponse = await traderTerminalPage.sendTradingViewWebhook(failedTrade)
    expect(failedResponse.status).toBeGreaterThanOrEqual(400) // Should fail
    
    // Restore network
    await page.unroute('**/api/**')
    
    // Wait for reconnection
    await page.waitForTimeout(2000)
    
    // Verify system recovery
    const recoveryTrade = {
      symbol: 'ES',
      action: 'buy',
      quantity: 1,
      account_group: 'paper_simulator',
      strategy: 'recovery_test'
    }
    
    const recoveryResponse = await traderTerminalPage.sendTradingViewWebhook(recoveryTrade)
    expect(recoveryResponse.status).toBe(200) // Should succeed after recovery
    
    // Verify trade execution after recovery
    await traderTerminalPage.waitForTradeExecution(recoveryTrade.symbol, recoveryTrade.action)
  })

  test('WebSocket connection stability', async ({ 
    traderTerminalPage, 
    networkMonitor 
  }) => {
    await traderTerminalPage.initialize()
    
    // Verify initial WebSocket connection
    await traderTerminalPage.verifyWebSocketConnection()
    
    // Test WebSocket interruption and recovery
    console.log('Testing WebSocket interruption recovery...')
    
    // Simulate WebSocket disconnection
    await page.route('**/ws', route => route.abort())
    
    // Wait for disconnection detection
    await page.waitForTimeout(3000)
    
    // Verify disconnection is detected
    const wsStatus = page.locator('[data-testid="websocket-status"]')
    await expect(wsStatus).toContainText('Disconnected', { timeout: 10000 })
    
    // Restore WebSocket connection
    await page.unroute('**/ws')
    
    // Wait for automatic reconnection
    await page.waitForTimeout(5000)
    
    // Verify reconnection
    await expect(wsStatus).toContainText('Connected', { timeout: 15000 })
    
    // Verify WebSocket functionality after reconnection
    const wsActivity = await networkMonitor.verifyWebSocketActivity()
    expect(wsActivity.length).toBeGreaterThan(0)
  })

  test('Strategy performance monitoring integration', async ({ 
    traderTerminalPage 
  }) => {
    await traderTerminalPage.initialize()
    
    // Create a complete strategy set (20 trades)
    const strategyName = 'integration_performance_test'
    
    for (let i = 0; i < 20; i++) {
      const trade = {
        symbol: 'ES',
        action: i % 2 === 0 ? 'buy' : 'sell',
        quantity: 1,
        account_group: 'paper_simulator',
        strategy: strategyName
      }
      
      await traderTerminalPage.sendTradingViewWebhook(trade)
      
      // Wait for every 5th trade to avoid overwhelming
      if (i % 5 === 0) {
        await traderTerminalPage.waitForTradeExecution(trade.symbol, trade.action)
      }
    }
    
    // Navigate to strategy performance panel
    await page.click('[data-testid="strategy-performance-tab"]')
    
    // Verify strategy set completion
    const strategyCard = page.locator(`[data-testid="strategy-card-${strategyName}"]`)
    await expect(strategyCard).toBeVisible()
    
    // Verify set completion (20/20 trades)
    await expect(strategyCard.locator('[data-testid="current-set-trades"]'))
      .toContainText('20/20')
    
    // Verify performance metrics are calculated
    await expect(strategyCard.locator('[data-testid="strategy-win-rate"]')).toBeVisible()
    await expect(strategyCard.locator('[data-testid="strategy-pnl"]')).toBeVisible()
    
    // Verify set is marked as complete
    await expect(strategyCard.locator('[data-testid="set-status"]'))
      .toContainText('Complete')
  })

  test('Funded account integration validation', async ({ 
    traderTerminalPage 
  }) => {
    await traderTerminalPage.initialize()
    
    // Navigate to funded account panel
    await page.click('[data-testid="funded-account-tab"]')
    
    // Test funded account selection
    const accountSelector = page.locator('[data-testid="account-selector"]')
    await expect(accountSelector).toBeVisible()
    
    // Select a TopStep account (if available)
    if (await page.locator('option[value*="topstep"]').count() > 0) {
      await accountSelector.selectOption('topstep_demo')
      
      // Verify account details load
      await expect(page.locator('[data-testid="account-details"]')).toBeVisible()
      await expect(page.locator('[data-testid="daily-pnl-meter"]')).toBeVisible()
      await expect(page.locator('[data-testid="drawdown-meter"]')).toBeVisible()
      
      // Test risk limits validation
      const riskTrade = {
        symbol: 'ES',
        action: 'buy',
        quantity: 10, // Large position to test limits
        account_group: 'topstep',
        strategy: 'funded_risk_test'
      }
      
      const riskResponse = await traderTerminalPage.sendTradingViewWebhook(riskTrade)
      
      // Should be rejected or show risk warning
      if (riskResponse.status === 400) {
        console.log('✅ Risk limits properly enforced')
      } else {
        // Check for risk warning in UI
        await expect(page.locator('[data-testid="risk-warning"]')).toBeVisible()
      }
    }
  })

  test('Visual regression validation', async ({ 
    traderTerminalPage, 
    visualValidator 
  }) => {
    await traderTerminalPage.initialize()
    
    // Test all major UI components for visual consistency
    await visualValidator.validateTradingPanelComponents()
    await visualValidator.validateBrokerConnectionIndicators()
    await visualValidator.validatePaperTradingInterface()
    await visualValidator.validateStrategyPerformancePanel()
    await visualValidator.validateFundedAccountDashboard()
    
    // Test responsive design
    await visualValidator.validateResponsiveLayout('integration-responsive')
    
    // Test dark theme consistency
    await visualValidator.validateDarkThemeConsistency()
    
    console.log('✅ Visual regression validation completed')
  })

  test('Complete system health check', async ({ 
    traderTerminalPage, 
    networkMonitor, 
    performanceTracker 
  }) => {
    await traderTerminalPage.initialize()
    
    // Perform comprehensive system health check
    const healthChecks = {
      dashboard: false,
      webSocket: false,
      api: false,
      brokers: false,
      paperTrading: false,
      strategyTracking: false,
      performance: false
    }
    
    // Check dashboard load
    await expect(page.locator('[data-testid="trading-dashboard"]')).toBeVisible()
    healthChecks.dashboard = true
    
    // Check WebSocket connection
    await traderTerminalPage.verifyWebSocketConnection()
    healthChecks.webSocket = true
    
    // Check API endpoints
    await networkMonitor.verifyAPIEndpoint('/api/health', 200)
    healthChecks.api = true
    
    // Check broker connections
    await traderTerminalPage.verifyAllBrokerConnections()
    healthChecks.brokers = true
    
    // Check paper trading
    await traderTerminalPage.testPaperTradingWorkflow()
    healthChecks.paperTrading = true
    
    // Check strategy performance monitoring
    await traderTerminalPage.testStrategyPerformanceMonitoring()
    healthChecks.strategyTracking = true
    
    // Check performance metrics
    await performanceTracker.measurePageLoad()
    performanceTracker.validatePageLoadTime(5000)
    performanceTracker.validateMemoryUsage(150)
    healthChecks.performance = true
    
    // Verify all health checks passed
    Object.entries(healthChecks).forEach(([check, passed]) => {
      expect(passed).toBe(true)
      console.log(`✅ ${check} health check passed`)
    })
    
    console.log('🎉 Complete system health check PASSED!')
  })
})