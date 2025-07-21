// tests/playwright/test-suites/trading-workflows/base-trading-test.ts
import { test, expect } from '../../core/base-test'

export interface TradingScenario {
  trades: Array<{
    symbol: string
    action: 'buy' | 'sell' | 'close'
    quantity: number
    account_group: string
    strategy: string
    order_type?: 'market' | 'limit' | 'stop'
    price?: number
  }>
  validateFinalState: (traderTerminalPage: any) => Promise<void>
}

export class TradingWorkflowTest {
  static createTest(testName: string, tradingScenario: TradingScenario) {
    test(`Trading Workflow: ${testName}`, async ({ 
      traderTerminalPage, 
      networkMonitor, 
      performanceTracker,
      visualValidator
    }) => {
      // Initialize dashboard and verify connections
      await traderTerminalPage.initialize()
      await traderTerminalPage.verifyAllBrokerConnections()

      // Take baseline screenshot
      await visualValidator.validateDashboardLayout(`${testName}-baseline`)

      let tradeIndex = 0
      
      // Execute trading scenario
      for (const trade of tradingScenario.trades) {
        console.log(`Executing Trade ${tradeIndex + 1}: ${trade.symbol} ${trade.action} ${trade.quantity} via ${trade.account_group}`)

        // Measure performance for this trade
        const tradeStartTime = Date.now()

        // Send webhook for this trade
        const webhookResponse = await traderTerminalPage.sendTradingViewWebhook(trade)
        expect(webhookResponse.status).toBe(200)

        // Wait for trade execution
        await traderTerminalPage.waitForTradeExecution(trade.symbol, trade.action)

        // Take screenshot after each trade
        await traderTerminalPage.takeFullPageScreenshot(
          `${testName}-trade-${tradeIndex}-${trade.symbol}-${trade.action}.png`
        )

        // Verify network activity for this trade
        await networkMonitor.verifyAPIEndpoint('/webhook/tradingview', 200)

        const tradeExecutionTime = Date.now() - tradeStartTime
        console.log(`Trade ${tradeIndex + 1} executed in ${tradeExecutionTime}ms`)

        tradeIndex++
      }

      // Validate final state
      await tradingScenario.validateFinalState(traderTerminalPage)

      // Generate comprehensive performance report
      await performanceTracker.measurePageLoad()
      await performanceTracker.measureMemoryUsage()
      await performanceTracker.measureNetworkTiming()

      // Validate performance requirements
      performanceTracker.validatePageLoadTime(5000) // Max 5 seconds for complex workflows
      performanceTracker.validateMemoryUsage(150) // Max 150MB for trading workflows

      // Take final screenshot
      await visualValidator.validateDashboardLayout(`${testName}-final`)

      console.log(`✅ Trading workflow "${testName}" completed successfully`)
    })
  }

  static createPaperTradingValidationTest(testName: string, tradeCount: number = 100) {
    test(`Paper Trading Validation: ${testName}`, async ({ 
      traderTerminalPage, 
      performanceTracker 
    }) => {
      await traderTerminalPage.initialize()
      
      // Execute rapid paper trades for validation
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
      await expect(page.locator('[data-testid="total-paper-trades"]')).toContainText(tradeCount.toString())
      
      // Check win rate calculation
      const winRate = await page.locator('[data-testid="win-rate"]').textContent()
      expect(parseFloat(winRate.replace('%', ''))).toBeGreaterThan(0)

      console.log(`✅ Paper trading validation completed: ${tradeCount} trades in ${totalTime}ms`)
    })
  }

  static createMultiBrokerIntegrationTest() {
    const multiBrokerScenario: TradingScenario = {
      trades: [
        { 
          symbol: 'ES', 
          action: 'buy', 
          quantity: 1, 
          account_group: 'paper_tradovate', 
          strategy: 'futures_momentum' 
        },
        { 
          symbol: 'AAPL', 
          action: 'buy', 
          quantity: 100, 
          account_group: 'paper_tastytrade', 
          strategy: 'equity_breakout' 
        },
        { 
          symbol: 'SPY', 
          action: 'buy', 
          quantity: 50, 
          account_group: 'paper_simulator', 
          strategy: 'etf_momentum' 
        }
      ],
      validateFinalState: async (traderTerminalPage) => {
        // Verify all trades were executed across different brokers
        await expect(page.locator('[data-testid="paper-trades-tradovate"]')).toContainText('1')
        await expect(page.locator('[data-testid="paper-trades-tastytrade"]')).toContainText('1')
        await expect(page.locator('[data-testid="paper-trades-simulator"]')).toContainText('1')
        
        // Verify portfolio shows positions across all brokers
        await expect(page.locator('[data-testid="position-ES"]')).toBeVisible()
        await expect(page.locator('[data-testid="position-AAPL"]')).toBeVisible()
        await expect(page.locator('[data-testid="position-SPY"]')).toBeVisible()
      }
    }

    this.createTest('Multi-Broker Integration', multiBrokerScenario)
  }

  static createFundedAccountRiskTest() {
    const riskTestScenario: TradingScenario = {
      trades: [
        { 
          symbol: 'ES', 
          action: 'buy', 
          quantity: 10, // Large position to test limits
          account_group: 'topstep', 
          strategy: 'risk_test' 
        }
      ],
      validateFinalState: async (traderTerminalPage) => {
        // Should be rejected due to position size limits
        await expect(page.locator('[data-testid="risk-violation"]')).toBeVisible()
        await expect(page.locator('[data-testid="risk-violation"]')).toContainText('Position size exceeds limit')
      }
    }

    test('Funded Account Risk Management', async ({ traderTerminalPage }) => {
      await traderTerminalPage.initialize()
      
      // Test risk limits enforcement
      const riskTestTrade = riskTestScenario.trades[0]
      
      const response = await traderTerminalPage.sendTradingViewWebhook(riskTestTrade)
      
      // Should be rejected due to position size limits
      expect(response.status).toBe(400)
      
      // Verify risk violation appears in UI
      await riskTestScenario.validateFinalState(traderTerminalPage)
    })
  }

  static createStrategyPerformanceTest() {
    const strategyScenario: TradingScenario = {
      trades: [
        // Simulate a strategy that will trigger performance monitoring
        ...Array.from({ length: 20 }, (_, i) => ({
          symbol: 'ES',
          action: i % 3 === 0 ? 'buy' : 'sell' as 'buy' | 'sell',
          quantity: 1,
          account_group: 'paper_simulator',
          strategy: 'performance_test_strategy'
        }))
      ],
      validateFinalState: async (traderTerminalPage) => {
        // Verify strategy performance tracking
        await expect(page.locator('[data-testid="strategy-performance-panel"]')).toBeVisible()
        await expect(page.locator('[data-testid="strategy-card-performance_test_strategy"]')).toBeVisible()
        
        // Check that set is completed (20 trades)
        await expect(page.locator('[data-testid="current-set-trades"]')).toContainText('20/20')
        
        // Verify performance metrics are calculated
        await expect(page.locator('[data-testid="strategy-win-rate"]')).toBeVisible()
        await expect(page.locator('[data-testid="strategy-pnl"]')).toBeVisible()
      }
    }

    this.createTest('Strategy Performance Monitoring', strategyScenario)
  }

  static createRealTimeUpdatesTest() {
    test('Real-Time Data Updates', async ({ 
      traderTerminalPage, 
      networkMonitor 
    }) => {
      await traderTerminalPage.initialize()
      
      // Verify WebSocket connection
      await traderTerminalPage.verifyWebSocketConnection()
      
      // Test real-time quote updates
      await traderTerminalPage.verifyRealTimeUpdates()
      
      // Verify WebSocket activity in network monitor
      await networkMonitor.verifyWebSocketActivity()
      
      // Send a trade and verify real-time updates
      const trade = {
        symbol: 'ES',
        action: 'buy',
        quantity: 1,
        account_group: 'paper_simulator',
        strategy: 'realtime_test'
      }
      
      await traderTerminalPage.sendTradingViewWebhook(trade)
      
      // Verify real-time position update
      await expect(page.locator('[data-testid="position-ES"]')).toBeVisible({ timeout: 10000 })
      
      console.log('✅ Real-time updates test completed')
    })
  }

  static createComprehensiveUITest() {
    test('Comprehensive UI Component Validation', async ({ 
      traderTerminalPage, 
      visualValidator 
    }) => {
      await traderTerminalPage.initialize()
      
      // Test all major UI components
      await traderTerminalPage.testPaperTradingWorkflow()
      await traderTerminalPage.testStrategyPerformanceMonitoring()
      await traderTerminalPage.testFundedAccountRiskManagement()
      await traderTerminalPage.testMultiBrokerOrderEntry()
      
      // Validate visual consistency
      await visualValidator.validateTradingPanelComponents()
      await visualValidator.validateBrokerConnectionIndicators()
      await visualValidator.validatePaperTradingInterface()
      await visualValidator.validateStrategyPerformancePanel()
      await visualValidator.validateFundedAccountDashboard()
      await visualValidator.validateTradingViewChartIntegration()
      
      // Test responsive design
      await visualValidator.validateResponsiveLayout('comprehensive-ui')
      
      // Test dark theme consistency
      await visualValidator.validateDarkThemeConsistency()
      
      // Test error and loading states
      await visualValidator.validateErrorStates()
      await visualValidator.validateLoadingStates()
      
      // Test accessibility
      await visualValidator.validateAccessibility()
      
      console.log('✅ Comprehensive UI validation completed')
    })
  }

  // Create all predefined test scenarios
  static createAllTests() {
    this.createMultiBrokerIntegrationTest()
    this.createFundedAccountRiskTest()
    this.createStrategyPerformanceTest()
    this.createRealTimeUpdatesTest()
    this.createComprehensiveUITest()
    this.createPaperTradingValidationTest('100-Trade Validation', 100)
  }
}