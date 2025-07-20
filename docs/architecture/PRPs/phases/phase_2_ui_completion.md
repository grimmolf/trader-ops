# Phase 2: UI Completion Sprint (Week 2) - Detailed Breakdown

## 🎯 **Playwright GUI Testing Integration**

This phase incorporates **automated Playwright GUI testing** for comprehensive UI validation:

📄 **Framework Reference**: [`../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md`](../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md)

**Phase-Specific Testing:**
- **Real-Time Data Integration**: Live WebSocket connection and market data validation
- **Multi-Broker UI Components**: Order entry and account management interface testing
- **Interactive Dashboard**: User interaction workflows and responsiveness testing
- **Visual Consistency**: UI component state validation and regression testing
- **Performance Under Load**: Real-time data handling and rendering performance

**Test Implementation:**
```typescript
// tests/playwright/phase-specific/ui-completion-tests.spec.ts
import { test, expect } from '../core/base-test'

test.describe('Phase 2: UI Completion', () => {
  test('Real-time data integration validation', async ({ 
    traderTerminalPage, 
    networkMonitor, 
    performanceTracker 
  }) => {
    await traderTerminalPage.initialize()
    
    // Verify WebSocket connections
    await traderTerminalPage.verifyAllBrokerConnections()
    
    // Test real-time quote updates
    await expect(page.locator('[data-testid="live-quotes"]')).toBeVisible()
    await expect(page.locator('[data-testid="quote-ES"]')).toContainText(/\d+\.\d+/)
    
    // Test performance under real-time load
    const metrics = await performanceTracker.measurePageLoad()
    expect(metrics.firstContentfulPaint).toBeLessThan(1500)
  })
  
  test('Multi-broker order entry validation', async ({ traderTerminalPage }) => {
    await traderTerminalPage.initialize()
    
    // Test order entry for each broker
    const brokers = ['tradovate', 'tastytrade', 'simulator']
    
    for (const broker of brokers) {
      await page.selectOption('[data-testid="broker-selector"]', broker)
      await page.fill('[data-testid="order-symbol"]', 'ES')
      await page.fill('[data-testid="order-quantity"]', '1')
      await page.click('[data-testid="submit-order"]')
      
      await expect(page.locator(`[data-testid="order-${broker}-submitted"]`)).toBeVisible()
    }
  })
})
```

**Success Criteria:**
- ✅ All UI components render correctly with real data
- ✅ WebSocket connections maintain stability under load
- ✅ Order entry workflows validated across all brokers
- ✅ Visual regression tests confirm UI consistency
- ✅ Performance metrics meet requirements (< 1.5s FCP)

#### Step 2.1: Wire Up Real Data (Days 3-4)

##### Task 2.1.1: Update API Service
```typescript
// Update src/frontend/renderer/services/api.ts
import { io, Socket } from 'socket.io-client'

class TradingAPI {
  private socket: Socket | null = null
  private baseURL: string
  
  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }
  
  // WebSocket connection
  connectWebSocket() {
    this.socket = io(`${this.baseURL}/ws`, {
      transports: ['websocket']
    })
    
    this.socket.on('connect', () => {
      console.log('WebSocket connected')
    })
    
    this.socket.on('quote', (data) => {
      // Update quote store
    })
    
    this.socket.on('order_update', (data) => {
      // Update order store
    })
  }
  
  // Market data methods
  async subscribeQuotes(symbols: string[]) {
    if (!this.socket) return
    
    this.socket.emit('subscribe', {
      type: 'quotes',
      symbols
    })
  }
  
  // Order methods
  async placeOrder(order: OrderRequest) {
    const response = await fetch(`${this.baseURL}/api/v1/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(order)
    })
    
    if (!response.ok) {
      throw new Error(`Order failed: ${response.statusText}`)
    }
    
    return response.json()
  }
}

export const api = new TradingAPI()
```

##### Task 2.1.2: Create Data Synchronization
```typescript
// Create src/frontend/renderer/composables/useRealTimeData.ts
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/api'
import { useMarketDataStore } from '@/stores/marketData'
import { useFundedAccountsStore } from '@/stores/fundedAccounts'

export function useRealTimeData() {
  const marketStore = useMarketDataStore()
  const accountStore = useFundedAccountsStore()
  const isConnected = ref(false)
  
  const connect = async () => {
    try {
      api.connectWebSocket()
      
      // Subscribe to relevant data
      const symbols = marketStore.watchlistSymbols
      await api.subscribeQuotes(symbols)
      
      // Start polling for account updates
      startAccountPolling()
      
      isConnected.value = true
    } catch (error) {
      console.error('Failed to connect:', error)
    }
  }
  
  const startAccountPolling = () => {
    // Poll every 5 seconds for account metrics
    setInterval(async () => {
      if (accountStore.activeAccountId) {
        await accountStore.updateMetrics(accountStore.activeAccountId)
      }
    }, 5000)
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    api.disconnect()
  })
  
  return {
    isConnected,
    reconnect: connect
  }
}
```

