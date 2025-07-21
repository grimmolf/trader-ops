// tests/playwright/core/base-test.ts
import { test as base, expect, Page, Browser } from '@playwright/test'
import { TraderTerminalPage } from './page-objects/trader-terminal-page'
import { NetworkMonitor } from './utilities/network-monitor'
import { PerformanceTracker } from './utilities/performance-tracker'
import { VisualValidator } from './utilities/visual-validator'

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