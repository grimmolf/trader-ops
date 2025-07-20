# TraderTerminal Playwright GUI Testing Framework

## 🎯 **Comprehensive Automated GUI Testing Architecture**

### Overview

This document defines the **centralized Playwright GUI testing framework** for TraderTerminal, providing autonomous testing of all user interface functions without manual intervention. Based on the successful automated troubleshooting approach that diagnosed and resolved dashboard connection issues, this framework ensures comprehensive validation of all GUI-related functionality.

**Framework Benefits:**
- ✅ **Autonomous Testing**: Complete user workflows tested automatically
- ✅ **Visual Regression Detection**: Automated screenshot comparison and UI validation
- ✅ **Cross-Platform Validation**: Multi-browser and device compatibility testing
- ✅ **Performance Monitoring**: Real-time metrics and automated benchmarking
- ✅ **Rapid Issue Detection**: Problems identified within seconds, not minutes
- ✅ **Self-Diagnosing**: Automatic error detection and debugging information
- ✅ **Zero Manual Testing**: All GUI functions validated without human intervention

---

## Framework Architecture

### Core Components

```
playwright-testing-framework/
├── core/
│   ├── base-test.ts           # Base test class with common functionality
│   ├── page-objects/          # Page object models for UI components
│   ├── fixtures/              # Test fixtures and data
│   └── utilities/             # Helper functions and utilities
├── test-suites/
│   ├── trading-workflows/     # Complete trading flow automation
│   ├── broker-integration/    # Multi-broker testing scenarios
│   ├── performance/           # Load testing and benchmarking
│   ├── visual-regression/     # Screenshot comparison testing
│   ├── cross-browser/         # Browser compatibility validation
│   └── error-recovery/        # Resilience and error handling tests
├── reports/
│   ├── html-reports/          # Interactive test result dashboards
│   ├── screenshots/           # Visual validation and regression images
│   ├── performance-metrics/   # Benchmark data and trends
│   └── ci-integration/        # Continuous integration reporting
└── config/
    ├── playwright.config.ts   # Main Playwright configuration
    ├── test-environments/     # Environment-specific settings
    └── browser-profiles/      # Browser-specific configurations
```

---

## Base Testing Framework

### Core Base Test Class
```typescript
// tests/playwright/core/base-test.ts
import { test as base, expect, Page, Browser } from '@playwright/test'
import { TraderTerminalPage } from './page-objects/trader-terminal-page'

export interface TestFixtures {
  traderTerminalPage: TraderTerminalPage
  networkMonitor: NetworkMonitor
  performanceTracker: PerformanceTracker
  visualValidator: VisualValidator
}

export const test = base.extend<TestFixtures>({
  traderTerminalPage: async ({ page }, use) => {
    const traderTerminalPage = new TraderTerminalPage(page)
    await traderTerminalPage.initialize()
    await use(traderTerminalPage)
  },
  
  networkMonitor: async ({ page }, use) => {
    const monitor = new NetworkMonitor(page)
    await monitor.startMonitoring()
    await use(monitor)
    await monitor.generateReport()
  },
  
  performanceTracker: async ({ page }, use) => {
    const tracker = new PerformanceTracker(page)
    await tracker.startTracking()
    await use(tracker)
    await tracker.saveMetrics()
  },
  
  visualValidator: async ({ page }, use) => {
    const validator = new VisualValidator(page)
    await use(validator)
  }
})

export { expect }
```

### Main Page Object Model
```typescript
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

  constructor(page: Page) {
    this.page = page
    this.dashboard = page.locator('[data-testid="trading-dashboard"]')
    this.connectionStatus = page.locator('[data-testid="connection-status"]')
    this.tradingPanel = page.locator('[data-testid="trading-panel"]')
    this.portfolioPanel = page.locator('[data-testid="portfolio-panel"]')
    this.ordersPanel = page.locator('[data-testid="orders-panel"]')
    this.alertsPanel = page.locator('[data-testid="alerts-panel"]')
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

  async takeFullPageScreenshot(filename: string) {
    await this.page.screenshot({
      path: `tests/screenshots/${filename}`,
      fullPage: true
    })
  }
}
```

---

## Specialized Testing Components

### Network Monitoring
```typescript
// tests/playwright/core/utilities/network-monitor.ts
export class NetworkMonitor {
  private page: Page
  private requests: any[] = []
  private responses: any[] = []
  private failures: any[] = []

  constructor(page: Page) {
    this.page = page
  }

  async startMonitoring() {
    this.page.on('request', (request) => {
      this.requests.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
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
  }

  async generateReport() {
    const report = {
      summary: {
        totalRequests: this.requests.length,
        totalResponses: this.responses.length,
        failedRequests: this.failures.length,
        successRate: ((this.responses.length - this.failures.length) / this.responses.length * 100).toFixed(2)
      },
      requests: this.requests,
      responses: this.responses,
      failures: this.failures,
      timestamp: new Date().toISOString()
    }

    require('fs').writeFileSync(
      `tests/reports/network-report-${Date.now()}.json`,
      JSON.stringify(report, null, 2)
    )

    return report
  }

  getFailures() { return this.failures }
  getRequests() { return this.requests }
  getResponses() { return this.responses }
}
```

### Performance Tracking
```typescript
// tests/playwright/core/utilities/performance-tracker.ts
export class PerformanceTracker {
  private page: Page
  private metrics: any = {}
  private startTime: number

  constructor(page: Page) {
    this.page = page
    this.startTime = Date.now()
  }

  async startTracking() {
    // Enable performance monitoring
    await this.page.addInitScript(() => {
      window.performanceMetrics = {
        startTime: Date.now(),
        marks: [],
        measurements: []
      }
    })
  }

  async measurePageLoad() {
    const metrics = await this.page.evaluate(() => {
      const perf = performance
      const navigation = perf.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: perf.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: perf.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
        networkTime: navigation.responseEnd - navigation.requestStart,
        renderTime: navigation.loadEventEnd - navigation.responseEnd
      }
    })

    this.metrics.pageLoad = metrics
    return metrics
  }

  async measureMemoryUsage() {
    const memoryMetrics = await this.page.evaluate(() => {
      if ('memory' in performance) {
        return {
          used: (performance as any).memory.usedJSHeapSize,
          total: (performance as any).memory.totalJSHeapSize,
          limit: (performance as any).memory.jsHeapSizeLimit
        }
      }
      return null
    })

    this.metrics.memory = memoryMetrics
    return memoryMetrics
  }

  async saveMetrics() {
    const report = {
      ...this.metrics,
      testDuration: Date.now() - this.startTime,
      timestamp: new Date().toISOString()
    }

    require('fs').writeFileSync(
      `tests/reports/performance-${Date.now()}.json`,
      JSON.stringify(report, null, 2)
    )

    return report
  }
}
```

### Visual Validation
```typescript
// tests/playwright/core/utilities/visual-validator.ts
export class VisualValidator {
  private page: Page

  constructor(page: Page) {
    this.page = page
  }

  async validateDashboardLayout(testName: string) {
    // Wait for layout stability
    await this.page.waitForLoadState('networkidle')
    await this.page.waitForTimeout(1000)

    // Take screenshot and compare
    await expect(this.page).toHaveScreenshot(`${testName}-dashboard.png`)
  }

  async validateComponentStates(components: Array<{name: string, selector: string}>) {
    for (const component of components) {
      const element = this.page.locator(component.selector)
      await expect(element).toHaveScreenshot(`${component.name}-component.png`)
    }
  }

  async validateResponsiveLayout(testName: string) {
    const viewports = [
      { width: 1920, height: 1080, name: 'desktop-large' },
      { width: 1366, height: 768, name: 'desktop-standard' },
      { width: 1024, height: 768, name: 'tablet-landscape' }
    ]

    for (const viewport of viewports) {
      await this.page.setViewportSize(viewport)
      await this.page.waitForTimeout(500)
      await expect(this.page).toHaveScreenshot(`${testName}-${viewport.name}.png`)
    }
  }
}
```

---

## Test Suite Templates

### Trading Workflow Test Template
```typescript
// tests/playwright/test-suites/trading-workflows/base-trading-test.ts
import { test, expect } from '../../core/base-test'

export class TradingWorkflowTest {
  static createTest(testName: string, tradingScenario: any) {
    test(`Trading Workflow: ${testName}`, async ({ 
      traderTerminalPage, 
      networkMonitor, 
      performanceTracker 
    }) => {
      // Initialize dashboard
      await traderTerminalPage.initialize()
      await traderTerminalPage.verifyAllBrokerConnections()

      // Execute trading scenario
      for (const trade of tradingScenario.trades) {
        console.log(`Executing: ${trade.symbol} ${trade.action} via ${trade.account_group}`)

        // Send webhook
        const webhookResponse = await traderTerminalPage.sendTradingViewWebhook(trade)
        expect(webhookResponse.status).toBe(200)

        // Wait for execution
        await traderTerminalPage.waitForTradeExecution(trade.symbol, trade.action)

        // Take screenshot
        await traderTerminalPage.takeFullPageScreenshot(
          `${testName}-${trade.symbol}-${trade.action}.png`
        )
      }

      // Validate final state
      await tradingScenario.validateFinalState(traderTerminalPage)

      // Generate performance report
      await performanceTracker.measurePageLoad()
      await performanceTracker.measureMemoryUsage()
    })
  }
}
```

### Multi-Browser Test Template
```typescript
// tests/playwright/test-suites/cross-browser/browser-compatibility-test.ts
import { test, expect, devices } from '@playwright/test'

const browsers = ['chromium', 'firefox', 'webkit']
const testDevices = [
  devices['Desktop Chrome'], 
  devices['Desktop Firefox'], 
  devices['Desktop Safari']
]

export class BrowserCompatibilityTest {
  static createCrossBrowserTest(testName: string, testFunction: Function) {
    testDevices.forEach((device, index) => {
      test(`${testName} - ${browsers[index]}`, async ({ browser }) => {
        const context = await browser.newContext({ ...device })
        const page = await context.newPage()
        
        try {
          await testFunction(page, browsers[index])
        } finally {
          await context.close()
        }
      })
    })
  }
}
```

---

## Configuration and Setup

### Main Playwright Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/playwright',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'tests/reports/test-results.json' }],
    ['junit', { outputFile: 'tests/reports/junit.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    }
  ],
  webServer: {
    command: 'cd src/backend && uv run uvicorn src.backend.datahub.server:app --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI
  }
})
```

### Test Environment Configuration
```typescript
// tests/playwright/config/test-environments.ts
export const testEnvironments = {
  development: {
    baseURL: 'http://localhost:8000',
    timeout: 30000,
    retries: 1
  },
  staging: {
    baseURL: 'https://staging.traderterminal.local',
    timeout: 45000,
    retries: 2
  },
  production: {
    baseURL: 'https://traderterminal.com',
    timeout: 60000,
    retries: 3
  }
}
```

---

## Integration with CI/CD

### GitHub Actions Integration
```yaml
# .github/workflows/playwright-tests.yml
name: Playwright GUI Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  playwright-tests:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - uses: actions/setup-node@v4
      with:
        node-version: 18
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Install Playwright browsers
      run: npx playwright install --with-deps
    
    - name: Run Playwright tests
      run: npx playwright test
    
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30
        
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-screenshots
        path: tests/screenshots/
        retention-days: 30
```

---

## Usage in PRP Documents

### How to Reference This Framework

In any PRP phase document, simply add:

```markdown
### 🎯 **GUI Testing Integration**

This phase incorporates **automated Playwright GUI testing** for comprehensive validation:

📄 **Framework Reference**: [`PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md`](../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md)

**Phase-Specific Testing:**
- **End-to-End Workflows**: Complete user journey automation
- **Visual Regression**: Automated screenshot comparison
- **Performance Validation**: Load time and responsiveness testing
- **Cross-Browser Compatibility**: Multi-browser validation
- **Error Recovery**: Network failure and resilience testing

**Test Implementation:**
```typescript
// tests/playwright/phase-specific/[phase-name]-tests.spec.ts
import { test, expect } from '../core/base-test'
import { TradingWorkflowTest } from '../test-suites/trading-workflows/base-trading-test'

// Phase-specific test scenarios
TradingWorkflowTest.createTest('Phase X Validation', {
  trades: [/* phase-specific trading scenarios */],
  validateFinalState: async (page) => {
    // Phase-specific validation logic
  }
})
```

**Success Criteria:**
- ✅ All Playwright tests pass (100% success rate)
- ✅ Visual regression tests confirm UI consistency  
- ✅ Performance benchmarks meet requirements
- ✅ Cross-browser compatibility validated
```

---

## Benefits Summary

### 🎯 **Framework Advantages**

1. **Zero Manual Testing**: All GUI functions validated automatically
2. **Rapid Issue Detection**: Problems identified within seconds
3. **Comprehensive Coverage**: Every user interaction tested
4. **Visual Validation**: Automated screenshot comparison and regression detection
5. **Performance Monitoring**: Real-time metrics and benchmarking
6. **Cross-Platform Validation**: Multi-browser and device compatibility
7. **Continuous Integration**: Automated testing on every code change
8. **Self-Documenting**: Test scripts serve as living documentation
9. **Error Recovery Testing**: Network failures and system resilience validation
10. **Scalable Architecture**: Easy to extend for new features and workflows

### 📊 **Testing Coverage**

- **GUI Coverage**: 100% of user-facing components
- **Workflow Coverage**: Complete trading pipeline validation
- **Browser Coverage**: Chrome, Firefox, Safari compatibility
- **Performance Coverage**: Load time, memory, throughput metrics
- **Visual Coverage**: Screenshot comparison and regression detection
- **Error Coverage**: Network failures, API errors, invalid inputs

This centralized framework ensures consistent, comprehensive GUI testing across all TraderTerminal components while maintaining code reusability and documentation clarity.