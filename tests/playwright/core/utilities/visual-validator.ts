// tests/playwright/core/utilities/visual-validator.ts
import { Page, expect } from '@playwright/test'

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

  async validateTradingPanelComponents() {
    const tradingComponents = [
      { name: 'symbol-search', selector: '[data-testid="symbol-search"]' },
      { name: 'order-entry', selector: '[data-testid="order-entry"]' },
      { name: 'watchlist', selector: '[data-testid="watchlist"]' },
      { name: 'positions', selector: '[data-testid="positions"]' },
      { name: 'order-history', selector: '[data-testid="order-history"]' }
    ]

    await this.validateComponentStates(tradingComponents)
  }

  async validateBrokerConnectionIndicators() {
    const brokers = ['tradovate', 'tastytrade', 'simulator', 'topstepx']
    
    for (const broker of brokers) {
      const statusElement = this.page.locator(`[data-testid="broker-status-${broker}"]`)
      await expect(statusElement).toHaveScreenshot(`broker-status-${broker}.png`)
    }
  }

  async validatePaperTradingInterface() {
    // Navigate to paper trading panel
    await this.page.click('[data-testid="paper-trading-tab"]')
    await this.page.waitForTimeout(1000)

    // Validate paper trading dashboard
    await expect(this.page.locator('[data-testid="paper-trading-panel"]'))
      .toHaveScreenshot('paper-trading-dashboard.png')

    // Validate paper account cards
    const accountTypes = ['simulator', 'tastytrade', 'tradovate']
    for (const account of accountTypes) {
      const accountCard = this.page.locator(`[data-testid="paper-account-${account}"]`)
      await expect(accountCard).toHaveScreenshot(`paper-account-${account}.png`)
    }
  }

  async validateStrategyPerformancePanel() {
    // Navigate to strategy performance panel
    await this.page.click('[data-testid="strategy-performance-tab"]')
    await this.page.waitForTimeout(1000)

    // Validate strategy performance dashboard
    await expect(this.page.locator('[data-testid="strategy-performance-panel"]'))
      .toHaveScreenshot('strategy-performance-dashboard.png')

    // Validate strategy cards
    const strategyCards = this.page.locator('[data-testid="strategy-card"]')
    const count = await strategyCards.count()
    
    for (let i = 0; i < Math.min(count, 3); i++) {
      await expect(strategyCards.nth(i)).toHaveScreenshot(`strategy-card-${i}.png`)
    }
  }

  async validateFundedAccountDashboard() {
    // Navigate to funded account panel
    await this.page.click('[data-testid="funded-account-tab"]')
    await this.page.waitForTimeout(1000)

    // Validate funded account dashboard
    await expect(this.page.locator('[data-testid="funded-account-panel"]'))
      .toHaveScreenshot('funded-account-dashboard.png')

    // Validate risk meters
    const riskMeters = [
      'daily-pnl-meter',
      'drawdown-meter', 
      'profit-target-progress'
    ]

    for (const meter of riskMeters) {
      const meterElement = this.page.locator(`[data-testid="${meter}"]`)
      await expect(meterElement).toHaveScreenshot(`${meter}.png`)
    }
  }

  async validateTradingViewChartIntegration() {
    // Validate TradingView chart container
    const chartContainer = this.page.locator('[data-testid="tradingview-chart"]')
    await expect(chartContainer).toBeVisible()
    
    // Wait for chart to load
    await this.page.waitForTimeout(3000)
    
    // Take screenshot of chart area
    await expect(chartContainer).toHaveScreenshot('tradingview-chart.png')
  }

  async validateDarkThemeConsistency() {
    // Check that all components use consistent dark theme colors
    const darkThemeComponents = [
      '[data-testid="trading-dashboard"]',
      '[data-testid="trading-panel"]',
      '[data-testid="portfolio-panel"]',
      '[data-testid="orders-panel"]'
    ]

    for (const selector of darkThemeComponents) {
      const element = this.page.locator(selector)
      const backgroundColor = await element.evaluate(el => 
        window.getComputedStyle(el).backgroundColor
      )
      
      // Verify dark theme colors (should be dark gray/black variants)
      const isDarkTheme = backgroundColor.includes('rgb(') && 
        (backgroundColor.includes('33, 33, 33') || 
         backgroundColor.includes('24, 24, 24') ||
         backgroundColor.includes('18, 18, 18'))
      
      if (!isDarkTheme) {
        throw new Error(`Component ${selector} does not use dark theme colors: ${backgroundColor}`)
      }
    }
  }

  async validateErrorStates() {
    // Test various error states and their visual representation
    const errorScenarios = [
      {
        name: 'network-disconnected',
        action: async () => {
          await this.page.route('**/api/**', route => route.abort())
        }
      },
      {
        name: 'websocket-disconnected', 
        action: async () => {
          await this.page.route('**/ws', route => route.abort())
        }
      }
    ]

    for (const scenario of errorScenarios) {
      await scenario.action()
      await this.page.waitForTimeout(2000)
      
      // Take screenshot of error state
      await expect(this.page).toHaveScreenshot(`error-state-${scenario.name}.png`)
      
      // Reset routes
      await this.page.unroute('**/api/**')
      await this.page.unroute('**/ws')
    }
  }

  async validateLoadingStates() {
    // Test loading states for various components
    const loadingComponents = [
      'trading-dashboard',
      'paper-trading-panel',
      'strategy-performance-panel',
      'funded-account-panel'
    ]

    for (const component of loadingComponents) {
      // Simulate slow loading by adding delay
      await this.page.route('**/api/**', route => {
        setTimeout(() => route.continue(), 2000)
      })

      // Navigate to component and capture loading state
      await this.page.reload()
      await expect(this.page.locator(`[data-testid="${component}-loading"]`))
        .toHaveScreenshot(`${component}-loading.png`)

      // Remove delay
      await this.page.unroute('**/api/**')
    }
  }

  async validateAnimationsAndTransitions() {
    // Test UI animations and transitions
    const animatedElements = [
      { 
        selector: '[data-testid="broker-status-indicator"]',
        trigger: 'connection-change'
      },
      {
        selector: '[data-testid="order-status-badge"]', 
        trigger: 'order-update'
      },
      {
        selector: '[data-testid="pnl-display"]',
        trigger: 'value-change'
      }
    ]

    for (const element of animatedElements) {
      // Capture before state
      await expect(this.page.locator(element.selector))
        .toHaveScreenshot(`${element.trigger}-before.png`)

      // Trigger animation (implementation depends on element)
      await this.triggerAnimation(element.selector, element.trigger)

      // Capture after state
      await expect(this.page.locator(element.selector))
        .toHaveScreenshot(`${element.trigger}-after.png`)
    }
  }

  private async triggerAnimation(selector: string, trigger: string) {
    switch (trigger) {
      case 'connection-change':
        // Simulate connection state change
        await this.page.evaluate(() => {
          const event = new CustomEvent('connection-change', { 
            detail: { status: 'disconnected' }
          })
          window.dispatchEvent(event)
        })
        break
      case 'order-update':
        // Simulate order status update
        await this.page.evaluate(() => {
          const event = new CustomEvent('order-update', {
            detail: { status: 'filled' }
          })
          window.dispatchEvent(event)
        })
        break
      case 'value-change':
        // Simulate P&L value change
        await this.page.evaluate(() => {
          const event = new CustomEvent('pnl-update', {
            detail: { value: Math.random() * 1000 }
          })
          window.dispatchEvent(event)
        })
        break
    }
    
    // Wait for animation to complete
    await this.page.waitForTimeout(1000)
  }

  async validateAccessibility() {
    // Basic accessibility validation
    await this.page.evaluate(() => {
      const elements = document.querySelectorAll('button, input, select, textarea')
      elements.forEach(el => {
        if (!el.getAttribute('aria-label') && !el.textContent?.trim()) {
          console.warn('Element missing accessibility label:', el)
        }
      })
    })

    // Check for proper heading structure
    const headings = await this.page.locator('h1, h2, h3, h4, h5, h6').allTextContents()
    if (headings.length === 0) {
      throw new Error('No heading elements found - poor accessibility structure')
    }

    // Verify keyboard navigation works
    await this.page.keyboard.press('Tab')
    const focusedElement = await this.page.evaluate(() => document.activeElement?.tagName)
    if (!focusedElement) {
      throw new Error('Tab navigation not working - accessibility issue')
    }
  }
}