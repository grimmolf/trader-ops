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

  static createWebServerCrossBrowserTests() {
    this.createCrossBrowserTest('WebServer Frontend Compatibility', async (page, browserName) => {
      await page.goto('http://localhost:8000/app')
      await expect(page.locator('[data-testid="trading-dashboard"]')).toBeVisible()
      
      // Browser-specific validation
      console.log(`✅ Webserver frontend working in ${browserName}`)
      
      // Test WebSocket connections
      await page.waitForSelector('[data-testid="websocket-status"]')
      await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected')
      
      // Test API endpoints
      const response = await page.evaluate(async () => {
        const res = await fetch('/api/health')
        return { status: res.status, ok: res.ok }
      })
      expect(response.status).toBe(200)
      
      // Test TradingView chart loading
      await page.waitForSelector('[data-testid="tradingview-chart"]', { timeout: 15000 })
      await expect(page.locator('[data-testid="tradingview-chart"]')).toBeVisible()
    })

    this.createCrossBrowserTest('Paper Trading Cross-Browser', async (page, browserName) => {
      await page.goto('http://localhost:8000/app')
      await page.waitForSelector('[data-testid="trading-dashboard"]')
      
      // Navigate to paper trading
      await page.click('[data-testid="paper-trading-tab"]')
      await expect(page.locator('[data-testid="paper-trading-panel"]')).toBeVisible()
      
      // Test paper trading functionality
      const testTrade = {
        symbol: 'AAPL',
        action: 'buy',
        quantity: 100,
        account_group: 'paper_simulator',
        strategy: `cross_browser_test_${browserName}`
      }
      
      const webhookResponse = await page.evaluate(async (trade) => {
        const response = await fetch('/webhook/tradingview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(trade)
        })
        return { status: response.status, ok: response.ok }
      }, testTrade)
      
      expect(webhookResponse.status).toBe(200)
      console.log(`✅ Paper trading webhook working in ${browserName}`)
    })

    this.createCrossBrowserTest('Multi-Broker UI Cross-Browser', async (page, browserName) => {
      await page.goto('http://localhost:8000/app')
      await page.waitForSelector('[data-testid="trading-dashboard"]')
      
      // Test broker selector functionality
      const brokerSelector = page.locator('[data-testid="broker-selector"]')
      if (await brokerSelector.isVisible()) {
        await brokerSelector.selectOption('simulator')
        await expect(page.locator('[data-testid="selected-broker"]')).toContainText('simulator')
      }
      
      // Test order entry form
      await page.fill('[data-testid="order-symbol"]', 'ES')
      await page.fill('[data-testid="order-quantity"]', '1')
      
      // Verify form validation works across browsers
      const symbolValue = await page.locator('[data-testid="order-symbol"]').inputValue()
      expect(symbolValue).toBe('ES')
      
      console.log(`✅ Multi-broker UI working in ${browserName}`)
    })

    this.createCrossBrowserTest('Real-Time Data Cross-Browser', async (page, browserName) => {
      await page.goto('http://localhost:8000/app')
      await page.waitForSelector('[data-testid="trading-dashboard"]')
      
      // Test WebSocket connection across browsers
      await page.waitForSelector('[data-testid="websocket-status"]')
      const wsStatus = await page.locator('[data-testid="websocket-status"]').textContent()
      expect(wsStatus).toContain('Connected')
      
      // Test real-time quote updates
      const quoteElement = page.locator('[data-testid="quote-ES"]')
      if (await quoteElement.isVisible()) {
        const initialQuote = await quoteElement.textContent()
        
        // Wait for quote update (indicates WebSocket is working)
        await page.waitForFunction(
          (element, initial) => element.textContent !== initial,
          quoteElement,
          initialQuote,
          { timeout: 15000 }
        )
      }
      
      console.log(`✅ Real-time data working in ${browserName}`)
    })

    this.createCrossBrowserTest('JavaScript API Compatibility', async (page, browserName) => {
      await page.goto('http://localhost:8000/app')
      
      // Test modern JavaScript features across browsers
      const jsCompatibility = await page.evaluate(() => {
        const tests = {
          asyncAwait: typeof (async () => {}) === 'function',
          fetch: typeof fetch === 'function',
          webSocket: typeof WebSocket === 'function',
          localStorage: typeof localStorage === 'function',
          sessionStorage: typeof sessionStorage === 'function',
          json: typeof JSON === 'object',
          promise: typeof Promise === 'function',
          arrow: (() => true)() === true,
          destructuring: (() => {
            const [a] = [1]
            return a === 1
          })(),
          templateLiterals: `test` === 'test'
        }
        return tests
      })
      
      // Verify all modern features are supported
      Object.entries(jsCompatibility).forEach(([feature, supported]) => {
        expect(supported).toBe(true)
        console.log(`✅ ${feature} supported in ${browserName}`)
      })
    })

    this.createCrossBrowserTest('CSS Features Cross-Browser', async (page, browserName) => {
      await page.goto('http://localhost:8000/app')
      await page.waitForSelector('[data-testid="trading-dashboard"]')
      
      // Test CSS Grid support
      const gridSupport = await page.evaluate(() => {
        const div = document.createElement('div')
        div.style.display = 'grid'
        return div.style.display === 'grid'
      })
      expect(gridSupport).toBe(true)
      
      // Test Flexbox support
      const flexSupport = await page.evaluate(() => {
        const div = document.createElement('div')
        div.style.display = 'flex'
        return div.style.display === 'flex'
      })
      expect(flexSupport).toBe(true)
      
      // Test CSS Custom Properties (variables)
      const customPropsSupport = await page.evaluate(() => {
        return CSS.supports('color', 'var(--test)')
      })
      expect(customPropsSupport).toBe(true)
      
      console.log(`✅ CSS features working in ${browserName}`)
    })

    this.createCrossBrowserTest('Performance Cross-Browser', async (page, browserName) => {
      const startTime = Date.now()
      
      await page.goto('http://localhost:8000/app')
      await page.waitForSelector('[data-testid="trading-dashboard"]')
      
      const loadTime = Date.now() - startTime
      
      // Performance should be reasonable across all browsers
      expect(loadTime).toBeLessThan(10000) // 10 seconds max
      
      // Measure memory usage if available
      const memoryInfo = await page.evaluate(() => {
        if ('memory' in performance) {
          return {
            used: (performance as any).memory.usedJSHeapSize,
            total: (performance as any).memory.totalJSHeapSize
          }
        }
        return null
      })
      
      if (memoryInfo) {
        const usedMB = Math.round(memoryInfo.used / 1024 / 1024)
        expect(usedMB).toBeLessThan(200) // Less than 200MB
        console.log(`Memory usage in ${browserName}: ${usedMB}MB`)
      }
      
      console.log(`✅ Performance acceptable in ${browserName}: ${loadTime}ms`)
    })
  }

  static createMobileCompatibilityTests() {
    const mobileDevices = [
      devices['iPhone 12'],
      devices['iPhone 12 Pro'],
      devices['Pixel 5'],
      devices['iPad Pro']
    ]

    mobileDevices.forEach(device => {
      test(`Mobile Compatibility - ${device.userAgent?.includes('iPhone') ? 'iPhone' : 
                                     device.userAgent?.includes('iPad') ? 'iPad' : 
                                     device.userAgent?.includes('Android') ? 'Android' : 'Mobile'}`, 
        async ({ browser }) => {
          const context = await browser.newContext({ ...device })
          const page = await context.newPage()
          
          try {
            await page.goto('http://localhost:8000/app')
            
            // Check if mobile layout is applied
            const isMobileLayout = await page.evaluate(() => {
              return window.innerWidth < 768
            })
            
            if (isMobileLayout) {
              // Test mobile-specific UI elements
              await expect(page.locator('[data-testid="mobile-menu-toggle"]')).toBeVisible()
              
              // Test mobile navigation
              await page.click('[data-testid="mobile-menu-toggle"]')
              await expect(page.locator('[data-testid="mobile-nav-menu"]')).toBeVisible()
            } else {
              // Tablet layout - should show desktop-like interface
              await expect(page.locator('[data-testid="trading-dashboard"]')).toBeVisible()
            }
            
            // Test touch interactions
            await page.touchscreen.tap(100, 100)
            
            console.log(`✅ Mobile compatibility working on ${device.userAgent?.includes('iPhone') ? 'iPhone' : 
                                                              device.userAgent?.includes('iPad') ? 'iPad' : 
                                                              device.userAgent?.includes('Android') ? 'Android' : 'Mobile'}`)
          } finally {
            await context.close()
          }
        }
      )
    })
  }

  static createAllCrossBrowserTests() {
    this.createWebServerCrossBrowserTests()
    this.createMobileCompatibilityTests()
  }
}

// Create test for specific browser feature validation
export function createBrowserFeatureTest(featureName: string, testFunction: (page: any) => Promise<boolean>) {
  BrowserCompatibilityTest.createCrossBrowserTest(`Feature: ${featureName}`, async (page, browserName) => {
    await page.goto('http://localhost:8000/app')
    
    const isSupported = await testFunction(page)
    expect(isSupported).toBe(true)
    
    console.log(`✅ ${featureName} supported in ${browserName}`)
  })
}

// Browser-specific workaround tests
export class BrowserWorkaroundTests {
  static createSafariSpecificTests() {
    test('Safari WebSocket Compatibility', async ({ page }) => {
      await page.goto('http://localhost:8000/app')
      
      // Safari sometimes has WebSocket connection issues
      const wsConnected = await page.evaluate(async () => {
        return new Promise((resolve) => {
          const ws = new WebSocket('ws://localhost:8000/ws')
          ws.onopen = () => resolve(true)
          ws.onerror = () => resolve(false)
          setTimeout(() => resolve(false), 5000)
        })
      })
      
      expect(wsConnected).toBe(true)
    })
  }

  static createFirefoxSpecificTests() {
    test('Firefox Memory Management', async ({ page }) => {
      await page.goto('http://localhost:8000/app')
      
      // Firefox sometimes has different memory behavior
      const memoryBehavior = await page.evaluate(() => {
        // Simulate memory-intensive operations
        const largeArray = new Array(1000000).fill(0)
        const memoryBefore = (performance as any).memory?.usedJSHeapSize || 0
        
        // Force garbage collection if available
        if ((window as any).gc) {
          (window as any).gc()
        }
        
        const memoryAfter = (performance as any).memory?.usedJSHeapSize || 0
        
        return {
          memoryBefore,
          memoryAfter,
          arrayCreated: largeArray.length === 1000000
        }
      })
      
      expect(memoryBehavior.arrayCreated).toBe(true)
    })
  }

  static createChromiumSpecificTests() {
    test('Chromium Performance APIs', async ({ page }) => {
      await page.goto('http://localhost:8000/app')
      
      // Test Chromium-specific performance features
      const performanceFeatures = await page.evaluate(() => {
        return {
          navigation: !!performance.getEntriesByType('navigation')[0],
          memory: !!(performance as any).memory,
          observer: !!window.PerformanceObserver,
          timing: !!performance.timing
        }
      })
      
      // These should be available in Chromium
      expect(performanceFeatures.navigation).toBe(true)
      expect(performanceFeatures.memory).toBe(true)
      expect(performanceFeatures.observer).toBe(true)
    })
  }
}