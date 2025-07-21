# TraderTerminal Playwright GUI Testing Framework

## 🎯 **Comprehensive Automated GUI Testing**

This directory contains the complete Playwright GUI testing framework for TraderTerminal, providing autonomous testing of all user interface functions without manual intervention.

### ✅ **Framework Benefits**
- **Autonomous Testing**: Complete user workflows tested automatically
- **Visual Regression Detection**: Automated screenshot comparison and UI validation
- **Cross-Platform Validation**: Multi-browser and device compatibility testing
- **Performance Monitoring**: Real-time metrics and automated benchmarking
- **Rapid Issue Detection**: Problems identified within seconds, not minutes
- **Self-Diagnosing**: Automatic error detection and debugging information
- **Zero Manual Testing**: All GUI functions validated without human intervention

---

## 🏗️ **Framework Architecture**

```
tests/playwright/
├── core/
│   ├── base-test.ts                    # Base test class with fixtures
│   ├── page-objects/
│   │   └── trader-terminal-page.ts     # Main page object model
│   └── utilities/
│       ├── network-monitor.ts          # Network activity monitoring
│       ├── performance-tracker.ts      # Performance metrics collection
│       └── visual-validator.ts         # Visual regression testing
├── test-suites/
│   ├── trading-workflows/
│   │   └── base-trading-test.ts        # Trading workflow automation
│   └── cross-browser/
│       └── browser-compatibility-test.ts # Cross-browser validation
├── phase-specific/
│   ├── futures-trading-tests.spec.ts   # Phase 0 critical path tests
│   └── integration-testing.spec.ts     # Phase 3 integration tests
├── global-setup.ts                     # Global test setup
├── global-teardown.ts                  # Global test teardown
└── README.md                           # This file
```

---

## 🚀 **Quick Start**

### Prerequisites
```bash
# Ensure backend is running
cd src/backend
uv run uvicorn src.backend.datahub.server:app --port 8000

# Install Playwright browsers (if not already installed)
npx playwright install
```

### Run Tests
```bash
# Run all tests
./scripts/run-playwright-tests.sh

# Run specific test mode
./scripts/run-playwright-tests.sh --mode phase0      # Phase 0 tests
./scripts/run-playwright-tests.sh --mode integration # Integration tests
./scripts/run-playwright-tests.sh --mode smoke      # Quick smoke tests

# Run with visible browser
./scripts/run-playwright-tests.sh --headed

# Run in specific browser
./scripts/run-playwright-tests.sh --browser firefox
./scripts/run-playwright-tests.sh --browser webkit

# Run with specific configuration
./scripts/run-playwright-tests.sh --headed --browser firefox --workers 1
```

### View Results
```bash
# View detailed HTML report
npx playwright show-report

# Check test artifacts
ls tests/reports/          # JSON reports, performance data
ls tests/screenshots/      # Screenshot captures
ls playwright-report/     # HTML report files
```

---

## 📋 **Test Categories**

### Phase-Specific Tests
- **Phase 0 (futures-trading-tests.spec.ts)**: Critical futures trading validation
  - Paper trading validation (100+ trade requirement)
  - Funded account risk management
  - TradingView webhook integration
  - Multi-broker routing
  - Strategy performance monitoring

- **Phase 3 (integration-testing.spec.ts)**: Comprehensive integration validation
  - End-to-end trading flows
  - Multi-broker simultaneous execution
  - Performance under load testing
  - Error recovery and resilience
  - WebSocket connection stability

### Test Suites
- **Trading Workflows**: Complete trading scenario automation
- **Cross-Browser**: Chrome, Firefox, Safari compatibility
- **Performance**: Load testing and benchmarking
- **Visual Regression**: UI consistency validation

---

## 🔧 **Key Features**

### 1. **Autonomous Trading Workflow Testing**
```typescript
// Example: Complete trading flow automation
const tradingScenario = {
  trades: [
    { symbol: 'ES', action: 'buy', quantity: 1, account_group: 'paper_simulator' },
    { symbol: 'NQ', action: 'buy', quantity: 1, account_group: 'paper_tradovate' }
  ],
  validateFinalState: async (page) => {
    await expect(page.locator('[data-testid="positions"]')).toHaveCount(2)
  }
}

TradingWorkflowTest.createTest('Multi-Broker Trading', tradingScenario)
```

### 2. **Real-Time Performance Monitoring**
```typescript
// Automatic performance tracking
await performanceTracker.measurePageLoad()
await performanceTracker.measureMemoryUsage()
await performanceTracker.measureWebSocketLatency()

// Validation with thresholds
performanceTracker.validatePageLoadTime(5000)  // < 5 seconds
performanceTracker.validateMemoryUsage(150)    // < 150MB
```

### 3. **Network Activity Validation**
```typescript
// Comprehensive network monitoring
await networkMonitor.verifyAPIEndpoint('/webhook/tradingview', 200)
await networkMonitor.verifyWebSocketActivity()
await networkMonitor.validateTradingViewWebhook()
```

### 4. **Visual Regression Testing**
```typescript
// Automated visual validation
await visualValidator.validateDashboardLayout('test-name')
await visualValidator.validateTradingPanelComponents()
await visualValidator.validateResponsiveLayout('responsive-test')
```

### 5. **Cross-Browser Compatibility**
```typescript
// Multi-browser test creation
BrowserCompatibilityTest.createCrossBrowserTest('Feature Test', async (page, browser) => {
  await page.goto('http://localhost:8000/app')
  await expect(page.locator('[data-testid="dashboard"]')).toBeVisible()
  console.log(`✅ Feature working in ${browser}`)
})
```

---

## 📊 **Test Data & Validation**

### Paper Trading Validation
- **Requirement**: 100+ paper trades before live trading
- **Validation**: Automated execution and performance tracking
- **Metrics**: Win rate, P&L, execution time, strategy performance

### Multi-Broker Integration
- **Brokers**: Tradovate, Tastytrade, TopstepX, Simulator
- **Validation**: Order routing, execution, status updates
- **Real-time**: WebSocket updates, position tracking

### Funded Account Risk Management
- **Rules**: Daily loss limits, position sizing, drawdown tracking
- **Validation**: Risk enforcement, violation detection, emergency controls
- **Monitoring**: Real-time metrics, compliance tracking

---

## 🎯 **Test Scenarios**

### Critical Path Scenarios
1. **TradingView Webhook → Broker Execution**
   - Webhook reception and validation
   - Multi-broker routing
   - Order execution and fills
   - Real-time position updates

2. **Paper Trading Workflow**
   - 100+ automated paper trades
   - Performance monitoring
   - Win rate calculation
   - Strategy tracking

3. **Funded Account Management**
   - Risk limit enforcement
   - Real-time monitoring
   - Violation detection
   - Emergency procedures

### Performance Scenarios
1. **Load Testing**
   - 50+ simultaneous trades
   - Memory usage monitoring
   - Network stability
   - Response time validation

2. **Endurance Testing**
   - Extended trading sessions
   - Memory leak detection
   - Connection stability
   - Performance degradation

### Error Recovery Scenarios
1. **Network Interruption**
   - API failure recovery
   - WebSocket reconnection
   - Data synchronization
   - User notification

2. **System Resilience**
   - Browser crash recovery
   - Backend restart handling
   - Data persistence
   - State restoration

---

## 🔍 **Advanced Features**

### Custom Test Fixtures
```typescript
// Enhanced base test with custom fixtures
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
  }
})
```

### Page Object Model
```typescript
// Comprehensive page interactions
export class TraderTerminalPage {
  async sendTradingViewWebhook(alertData: any) {
    return await this.page.evaluate(async (data) => {
      const response = await fetch('/webhook/tradingview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return { status: response.status, data: await response.json() }
    }, alertData)
  }

  async waitForTradeExecution(symbol: string, action: string) {
    await this.page.waitForSelector(`[data-testid="alert-${symbol}-${action}"]`)
    await this.page.waitForSelector(`[data-testid="order-${symbol}-filled"]`)
  }
}
```

### Performance Benchmarking
```typescript
// Comprehensive performance measurement
await performanceTracker.benchmarkTradingWorkflow()
const metrics = {
  dashboardLoad: await measureComponentRenderTime('[data-testid="dashboard"]'),
  chartLoad: await measureComponentRenderTime('[data-testid="chart"]'),
  websocketLatency: await measureWebSocketLatency(),
  orderEntryResponse: await measureComponentRenderTime('[data-testid="order-entry"]')
}
```

---

## 📈 **Reporting & Analytics**

### Automated Reports
- **HTML Report**: Interactive test results with screenshots
- **JSON Report**: Machine-readable test data
- **Performance Reports**: Metrics and benchmarks
- **Network Reports**: API calls and WebSocket activity
- **Visual Reports**: Screenshot comparisons

### Key Metrics
- **Test Coverage**: 100% of user-facing components
- **Performance Thresholds**: Load time, memory usage, latency
- **Success Rates**: API calls, WebSocket connections, trade executions
- **Visual Consistency**: Layout, styling, responsive behavior

### Report Locations
```
tests/reports/
├── test-results.json              # Main test results
├── network-report-*.json          # Network activity logs
├── performance-*.json             # Performance metrics
└── test-run-summary.json          # Test execution summary

tests/screenshots/
├── *.png                          # Test screenshots
├── error-state-*.png              # Error condition captures
└── visual-regression-*.png        # Baseline comparisons

playwright-report/
├── index.html                     # Interactive HTML report
├── trace-*.zip                    # Execution traces
└── test-results/                  # Detailed test artifacts
```

---

## 🛠️ **Configuration**

### Environment Variables
```bash
# Test environment configuration
export TRADING_ENV=test
export USE_MOCK_BROKERS=true
export ENABLE_PAPER_TRADING=true
export PLAYWRIGHT_HEADLESS=true
export PLAYWRIGHT_BROWSER=chromium
```

### Playwright Configuration
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests/playwright',
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } }
  ]
})
```

---

## 🚨 **Troubleshooting**

### Common Issues

#### Backend Not Running
```bash
# Check backend status
curl http://localhost:8000/health

# Start backend manually
cd src/backend
uv run uvicorn src.backend.datahub.server:app --port 8000
```

#### Browser Installation Issues
```bash
# Reinstall Playwright browsers
npx playwright install --force

# Install system dependencies
npx playwright install-deps
```

#### Test Failures
```bash
# Run with debug mode
./scripts/run-playwright-tests.sh --headed --browser chromium

# Check test traces
npx playwright show-trace tests/test-results/trace.zip

# View detailed HTML report
npx playwright show-report
```

#### Network/WebSocket Issues
```bash
# Check WebSocket connection manually
wscat -c ws://localhost:8000/ws

# Verify API endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/webhook/test
```

### Debug Commands
```bash
# Run single test with debug
npx playwright test tests/playwright/phase-specific/futures-trading-tests.spec.ts --debug

# Generate trace for failed test
npx playwright test --trace on

# Take screenshot during test development
npx playwright test --headed --screenshot only-on-failure
```

---

## 🎉 **Success Criteria**

### Phase 0 Validation
- ✅ 100+ paper trades executed and validated
- ✅ Multi-broker routing confirmed functional
- ✅ Funded account risk management enforced
- ✅ Strategy performance monitoring active
- ✅ TradingView webhook integration working

### Integration Testing
- ✅ End-to-end trading workflows validated
- ✅ Multi-broker simultaneous execution confirmed
- ✅ Performance under load meets requirements
- ✅ Error recovery and resilience validated
- ✅ WebSocket connection stability confirmed

### Performance Requirements
- ✅ Page load time < 5 seconds
- ✅ Memory usage < 150MB
- ✅ WebSocket latency < 1 second
- ✅ API response time < 2 seconds
- ✅ Trade execution time < 10 seconds

### Visual Validation
- ✅ UI components render consistently
- ✅ Responsive design works across viewports
- ✅ Dark theme applied consistently
- ✅ Cross-browser compatibility validated
- ✅ Error states display correctly

---

This comprehensive testing framework ensures that TraderTerminal maintains high quality and reliability across all user interactions and system integrations.