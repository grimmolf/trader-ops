// tests/playwright/core/utilities/performance-tracker.ts
import { Page } from '@playwright/test'
import { writeFileSync } from 'fs'

export class PerformanceTracker {
  private page: Page
  private metrics: any = {}
  private startTime: number
  private memorySnapshots: any[] = []

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

    // Start periodic memory monitoring
    this.startMemoryMonitoring()
  }

  private startMemoryMonitoring() {
    const interval = setInterval(async () => {
      try {
        const memoryUsage = await this.measureMemoryUsage()
        if (memoryUsage) {
          this.memorySnapshots.push({
            ...memoryUsage,
            timestamp: Date.now()
          })
        }
      } catch (e) {
        // Memory API not available in this browser
      }
    }, 5000) // Every 5 seconds

    // Stop monitoring after 5 minutes
    setTimeout(() => clearInterval(interval), 300000)
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
        renderTime: navigation.loadEventEnd - navigation.responseEnd,
        domInteractive: navigation.domInteractive - navigation.navigationStart,
        totalPageLoad: navigation.loadEventEnd - navigation.navigationStart
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
          limit: (performance as any).memory.jsHeapSizeLimit,
          usedMB: Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024),
          totalMB: Math.round((performance as any).memory.totalJSHeapSize / 1024 / 1024)
        }
      }
      return null
    })

    if (memoryMetrics) {
      this.metrics.memory = memoryMetrics
    }
    return memoryMetrics
  }

  async measureNetworkTiming() {
    const networkMetrics = await this.page.evaluate(() => {
      const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[]
      
      const apiCalls = entries.filter(entry => 
        entry.name.includes('/api/') || 
        entry.name.includes('/webhook/') ||
        entry.name.includes('/ws')
      )

      const totalApiTime = apiCalls.reduce((sum, entry) => 
        sum + (entry.responseEnd - entry.requestStart), 0
      )

      const slowestApi = apiCalls.reduce((slowest, entry) => {
        const duration = entry.responseEnd - entry.requestStart
        return duration > (slowest?.duration || 0) 
          ? { name: entry.name, duration } 
          : slowest
      }, null)

      return {
        totalApiCalls: apiCalls.length,
        averageApiTime: apiCalls.length > 0 ? totalApiTime / apiCalls.length : 0,
        slowestApi,
        totalNetworkTime: totalApiTime
      }
    })

    this.metrics.network = networkMetrics
    return networkMetrics
  }

  async measureComponentRenderTime(componentSelector: string) {
    const renderTime = await this.page.evaluate((selector) => {
      const startTime = performance.now()
      const element = document.querySelector(selector)
      
      if (!element) {
        return { error: `Component ${selector} not found` }
      }

      // Wait for component to be fully rendered
      return new Promise((resolve) => {
        const observer = new MutationObserver(() => {
          const endTime = performance.now()
          observer.disconnect()
          resolve({
            selector,
            renderTime: endTime - startTime,
            timestamp: Date.now()
          })
        })

        observer.observe(element, { 
          childList: true, 
          subtree: true, 
          attributes: true 
        })

        // Fallback timeout
        setTimeout(() => {
          observer.disconnect()
          resolve({
            selector,
            renderTime: performance.now() - startTime,
            timeout: true,
            timestamp: Date.now()
          })
        }, 5000)
      })
    }, componentSelector)

    return renderTime
  }

  async measureWebSocketLatency() {
    const latencyMetrics = await this.page.evaluate(() => {
      // Send a ping message and measure response time
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws')
        const startTime = performance.now()
        
        ws.onopen = () => {
          ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }))
        }

        ws.onmessage = (event) => {
          const endTime = performance.now()
          const data = JSON.parse(event.data)
          
          if (data.type === 'pong') {
            resolve({
              latency: endTime - startTime,
              roundTripTime: Date.now() - data.timestamp,
              timestamp: Date.now()
            })
            ws.close()
          }
        }

        ws.onerror = () => {
          resolve({ error: 'WebSocket connection failed' })
        }

        // Timeout after 10 seconds
        setTimeout(() => {
          resolve({ error: 'WebSocket ping timeout' })
          ws.close()
        }, 10000)
      })
    })

    this.metrics.webSocketLatency = latencyMetrics
    return latencyMetrics
  }

  async benchmarkTradingWorkflow() {
    const startTime = performance.now()
    
    // Measure complete trading workflow performance
    const benchmarks = {
      dashboardLoad: await this.measureComponentRenderTime('[data-testid="trading-dashboard"]'),
      chartLoad: await this.measureComponentRenderTime('[data-testid="tradingview-chart"]'),
      websocketConnect: await this.measureWebSocketLatency(),
      orderEntry: await this.measureComponentRenderTime('[data-testid="order-entry"]'),
      portfolioUpdate: await this.measureComponentRenderTime('[data-testid="portfolio-panel"]')
    }

    const totalBenchmarkTime = performance.now() - startTime

    this.metrics.tradingWorkflowBenchmark = {
      ...benchmarks,
      totalTime: totalBenchmarkTime,
      timestamp: Date.now()
    }

    return this.metrics.tradingWorkflowBenchmark
  }

  async saveMetrics() {
    const report = {
      ...this.metrics,
      testDuration: Date.now() - this.startTime,
      memorySnapshots: this.memorySnapshots,
      summary: {
        pageLoadTime: this.metrics.pageLoad?.totalPageLoad || 0,
        memoryUsageMB: this.metrics.memory?.usedMB || 0,
        networkCalls: this.metrics.network?.totalApiCalls || 0,
        webSocketLatency: this.metrics.webSocketLatency?.latency || 0
      },
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
      `${reportsDir}/performance-${Date.now()}.json`,
      JSON.stringify(report, null, 2)
    )

    return report
  }

  // Performance validation helpers
  validatePageLoadTime(maxLoadTime: number = 3000) {
    const loadTime = this.metrics.pageLoad?.totalPageLoad || 0
    if (loadTime > maxLoadTime) {
      throw new Error(`Page load time ${loadTime}ms exceeds maximum ${maxLoadTime}ms`)
    }
    return true
  }

  validateMemoryUsage(maxMemoryMB: number = 100) {
    const memoryUsage = this.metrics.memory?.usedMB || 0
    if (memoryUsage > maxMemoryMB) {
      throw new Error(`Memory usage ${memoryUsage}MB exceeds maximum ${maxMemoryMB}MB`)
    }
    return true
  }

  validateWebSocketLatency(maxLatency: number = 1000) {
    const latency = this.metrics.webSocketLatency?.latency || 0
    if (latency > maxLatency) {
      throw new Error(`WebSocket latency ${latency}ms exceeds maximum ${maxLatency}ms`)
    }
    return true
  }
}