# Phase 0: Critical Path Futures Trading

**Duration**: Week 1  
**Priority**: 🔴 URGENT - Foundation for all trading operations

## Objective

Implement core futures trading functionality with a **paper-trading-first approach** to ensure system reliability and strategy validation before risking real capital.

### Primary Goals

1. **Paper Trading Infrastructure** (Days 1-3)
   - Set up broker sandbox environments (Tradovate Demo, Tastytrade Sandbox)
   - Implement webhook receivers for TradingView alerts
   - Execute and track 100+ paper trades

2. **Risk Management Systems** (Days 3-4)
   - Funded account rules enforcement
   - Strategy performance monitoring with auto-rotation
   - Position sizing and drawdown protection

3. **Live Trading Preparation** (Day 5)
   - Validate paper trading results (55%+ win rate required)
   - Test with minimum position sizes
   - Emergency stop procedures

## Implementation Priority

**CRITICAL**: All strategies must complete a minimum of 100 paper trades with documented performance before live trading activation. The system enforces automatic rotation to paper trading for any strategy falling below performance thresholds.

---

### Phase 0: Critical Path Futures Trading (Week 1) 🔴 URGENT

Since futures trading through funded accounts is the immediate priority:

#### Step 0.1: TradingView Webhook Setup (Day 1)

##### Task 0.1.1: Create Basic Webhook Receiver
```python
# Create src/backend/webhooks/__init__.py
# Create src/backend/webhooks/models.py
from pydantic import BaseModel
from typing import Optional, Literal

class TradingViewAlert(BaseModel):
    symbol: str
    action: Literal["buy", "sell", "close"]
    quantity: int
    price: Optional[float] = None
    strategy: Optional[str] = None
    account_group: Optional[str] = "main"
    comment: Optional[str] = None
```

##### Task 0.1.2: Implement Webhook Endpoint
```python
# Create src/backend/webhooks/tradingview_receiver.py
from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import json

router = APIRouter(prefix="/webhook", tags=["webhooks"])

@router.post("/tradingview")
async def receive_tradingview_alert(
    request: Request,
    tv_webhook_secret: str = Header(None, alias="X-Webhook-Signature")
):
    """Receive and validate TradingView webhook alerts"""
    # Step 1: Get raw body for signature verification
    body = await request.body()
    
    # Step 2: Verify signature
    if not verify_webhook_signature(body, tv_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Step 3: Parse and validate alert
    try:
        alert_data = json.loads(body)
        alert = TradingViewAlert(**alert_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid alert format: {e}")
    
    # Step 4: Log alert for debugging
    logger.info(f"Received TradingView alert: {alert}")
    
    # Step 5: Queue for processing (implement in next task)
    return {"status": "received", "alert_id": generate_alert_id()}
```

##### Task 0.1.3: Add Webhook Security
```python
# Add to src/backend/webhooks/security.py
import hmac
import hashlib
from datetime import datetime, timedelta
import secrets

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature using HMAC-SHA256"""
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def generate_webhook_secret() -> str:
    """Generate secure webhook secret"""
    return secrets.token_urlsafe(32)
```

### 🎯 **Playwright GUI Testing Integration**

This phase incorporates **automated Playwright GUI testing** for comprehensive validation:

📄 **Framework Reference**: [`../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md`](../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md)

**Phase-Specific Testing:**
- **TradingView Webhook Processing**: End-to-end alert workflow automation
- **Multi-Broker Routing**: Tradovate, Tastytrade, TopstepX integration validation
- **Paper Trading Workflows**: Complete trading cycle testing and validation
- **Funded Account Risk Management**: Position sizing and drawdown monitoring
- **Strategy Performance Monitoring**: Auto-rotation between live and paper trading

##### Task 0.1.4: Phase-Specific Playwright Tests
```typescript
// tests/playwright/phase-specific/futures-trading-tests.spec.ts
import { test, expect } from '../core/base-test'
import { TradingWorkflowTest } from '../test-suites/trading-workflows/base-trading-test'

// Critical futures trading scenarios
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
})
```

**Success Criteria:**
- ✅ All phase-specific Playwright tests pass
- ✅ 100+ paper trades executed and validated
- ✅ Multi-broker routing confirmed functional
- ✅ Funded account risk management enforced
- ✅ Strategy performance monitoring active

##### Task 0.1.4b: Traditional Test Scripts (Backup)
```bash
# Create scripts/test_webhook.sh (for manual testing)
#!/bin/bash
# Test webhook endpoint with mock TradingView alert

WEBHOOK_URL="http://localhost:8000/webhook/tradingview"
WEBHOOK_SECRET="your_test_secret"

# Generate test alert
ALERT_JSON='{
  "symbol": "ES",
  "action": "buy",
  "quantity": 1,
  "strategy": "momentum_breakout",
  "account_group": "topstep"
}'

# Calculate signature
SIGNATURE=$(echo -n "$ALERT_JSON" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

# Send webhook
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d "$ALERT_JSON"

# Run Playwright automation as well
echo "Running automated Playwright tests..."
npx playwright test tests/playwright/tradingview-webhook.spec.ts
```

#### Step 0.2: Tradovate Connector Implementation (Days 1-2)

##### Task 0.2.1: Create Tradovate Authentication
```python
# Create src/backend/feeds/tradovate/__init__.py
# Create src/backend/feeds/tradovate/auth.py
import httpx
from datetime import datetime, timedelta
from typing import Optional

class TradovateAuth:
    def __init__(self, username: str, password: str, app_id: str, demo: bool = True):
        self.username = username
        self.password = password
        self.app_id = app_id
        self.demo = demo
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Set base URLs
        if demo:
            self.auth_url = "https://demo.tradovateapi.com/v1"
        else:
            self.auth_url = "https://live.tradovateapi.com/v1"
    
    async def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed"""
        if self._is_token_valid():
            return self.access_token
            
        return await self._authenticate()
    
    async def _authenticate(self) -> str:
        """Perform OAuth2 authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/auth/accesstokenrequest",
                json={
                    "name": self.username,
                    "password": self.password,
                    "appId": self.app_id,
                    "appVersion": "1.0",
                    "cid": 0,
                    "sec": ""
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data["accessToken"]
            self.token_expiry = datetime.now() + timedelta(seconds=data["expirationTime"])
            
            return self.access_token
```

##### Task 0.2.2: Implement Market Data Methods
```python
# Create src/backend/feeds/tradovate/market_data.py
from typing import List, Dict, AsyncGenerator
import asyncio
import websockets
import json

class TradovateMarketData:
    def __init__(self, auth: TradovateAuth):
        self.auth = auth
        self.ws_url = "wss://md.tradovateapi.com/v1/websocket" if not auth.demo else "wss://md-demo.tradovateapi.com/v1/websocket"
        
    async def get_quote(self, symbol: str) -> Dict:
        """Get single quote for a symbol"""
        # Implementation for REST API quote
        
    async def get_quotes(self, symbols: List[str]) -> List[Dict]:
        """Get quotes for multiple symbols"""
        # Batch implementation
        
    async def subscribe_quotes(self, symbols: List[str]) -> AsyncGenerator[Dict, None]:
        """Subscribe to real-time quotes via WebSocket"""
        token = await self.auth.get_access_token()
        
        async with websockets.connect(f"{self.ws_url}?token={token}") as websocket:
            # Send subscription message
            subscribe_msg = {
                "op": "subscribe",
                "args": ["md/subscribeQuote", {"symbols": symbols}]
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            # Stream quotes
            async for message in websocket:
                data = json.loads(message)
                if data.get("e") == "md":
                    yield self._parse_quote(data)
```

##### Task 0.2.3: Implement Order Execution
```python
# Create src/backend/feeds/tradovate/orders.py
from typing import Dict, Optional
from enum import Enum

class OrderType(Enum):
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"
    STOP_LIMIT = "StopLimit"

class TradovateOrders:
    def __init__(self, auth: TradovateAuth):
        self.auth = auth
        self.base_url = auth.auth_url
        
    async def place_order(
        self,
        account_id: int,
        symbol: str,
        action: str,  # "Buy" or "Sell"
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict:
        """Place a futures order"""
        # Step 1: Get contract ID for symbol
        contract_id = await self._get_contract_id(symbol)
        
        # Step 2: Build order payload
        order_payload = {
            "accountId": account_id,
            "contractId": contract_id,
            "action": action,
            "orderQty": quantity,
            "orderType": order_type.value,
            "isAutomated": True
        }
        
        if order_type == OrderType.LIMIT and price:
            order_payload["price"] = price
        elif order_type == OrderType.STOP and stop_price:
            order_payload["stopPrice"] = stop_price
            
        # Step 3: Submit order
        async with httpx.AsyncClient() as client:
            token = await self.auth.get_access_token()
            response = await client.post(
                f"{self.base_url}/order/placeorder",
                json=order_payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            return response.json()
```

##### Task 0.2.4: Create Account Management
```python
# Create src/backend/feeds/tradovate/account.py
class TradovateAccount:
    def __init__(self, auth: TradovateAuth):
        self.auth = auth
        self.base_url = auth.auth_url
        
    async def get_accounts(self) -> List[Dict]:
        """Get all accounts for the user"""
        # Implementation
        
    async def get_account_balance(self, account_id: int) -> Dict:
        """Get cash balance for position sizing"""
        async with httpx.AsyncClient() as client:
            token = await self.auth.get_access_token()
            response = await client.get(
                f"{self.base_url}/cashBalance/getcashbalancesnapshot",
                params={"accountId": account_id},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            return response.json()
    
    async def get_positions(self, account_id: int) -> List[Dict]:
        """Get open positions"""
        # Implementation
```

#### Step 0.25: Tastytrade Connector Implementation (Days 2-3)

With Tradovate handling primary futures and tastytrade offering both futures **and** options, integrating tastytrade early allows live multi-asset trading while Schwab and TopstepX credentials are pending.

##### Task 0.25.1: OAuth2 Flow
```python
# Create src/backend/feeds/tastytrade/auth.py
"""Handle OAuth2 code-grant for tastytrade."""
class TastytradeAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        # Store creds and tokens
        ...
    async def exchange_code(self, code: str) -> None: ...
    async def refresh(self) -> str: ...  # returns fresh access_token
```

##### Task 0.25.2: Orders & Accounts
```python
# Create src/backend/feeds/tastytrade/orders.py
class TastytradeOrders:
    async def place_order(...): ...
    async def cancel_order(...): ...

# Create src/backend/feeds/tastytrade/account.py
class TastytradeAccount:
    async def get_balances(...): ...
    async def get_positions(...): ...
```

##### Task 0.25.3: Market Data & Streaming
```python
# Create src/backend/feeds/tastytrade/market_data.py
class TastytradeMarketData:
    async def get_quotes(...): ...
# Create src/backend/feeds/tastytrade/stream.py
class TastytradeStream:
    async def connect_ws(...): ...  # real-time fills & quotes
```

##### Task 0.25.4: FastAPI OAuth Callback
```python
# Add to src/backend/routes/oauth.py
@router.get("/oauth/tastytrade/callback")
async def tastytrade_callback(code: str, state: str = None):
    await tasty_auth.exchange_code(code)
    return RedirectResponse(url="traderterminal://oauth-success")
```

##### Task 0.25.5: Electron Deep-Link Handler
Add `linking.ts` in Electron main process to capture `traderterminal://oauth-success` and notify renderer.

##### Task 0.25.6: E2E Test
`tests/e2e/test_tastytrade_flow.py` – mock OAuth → place order → verify status.

#### Step 0.3: TopstepX Integration (Days 2-3)

##### Task 0.3.1: Research TopstepX API
```python
# Create src/backend/feeds/topstepx/README.md
"""
TopstepX API Integration Notes
==============================

1. Contact TopStep Support
   - Email: support@topstep.com
   - Request API documentation
   - Get test credentials

2. Expected Endpoints:
   - Authentication: POST /api/auth/login
   - Account Info: GET /api/accounts/{id}
   - Place Order: POST /api/orders
   - Get Metrics: GET /api/accounts/{id}/metrics

3. Special Considerations:
   - Funded account rules enforcement
   - Daily loss limits
   - Trailing drawdown tracking
   - Position size restrictions
"""
```

##### Task 0.3.2: Create TopstepX Models
```python
# Create src/backend/feeds/topstepx/models.py
from pydantic import BaseModel
from typing import Optional

class FundedAccountRules(BaseModel):
    max_daily_loss: float
    max_contracts: int
    trailing_drawdown: float
    profit_target: float
    current_daily_pnl: float = 0.0
    current_drawdown: float = 0.0
    
    def can_trade(self, contracts: int) -> tuple[bool, Optional[str]]:
        """Check if trade is allowed"""
        if self.current_daily_pnl <= -self.max_daily_loss:
            return False, "Daily loss limit reached"
        
        if contracts > self.max_contracts:
            return False, f"Max contracts is {self.max_contracts}"
            
        if self.current_drawdown >= self.trailing_drawdown:
            return False, "Trailing drawdown limit reached"
            
        return True, None

class TopstepAccount(BaseModel):
    account_id: str
    account_size: float
    rules: FundedAccountRules
    status: str  # "active", "suspended", "passed"
```

##### Task 0.3.3: Implement TopstepX Connector Stub
```python
# Create src/backend/feeds/topstepx/connector.py
class TopstepXConnector:
    """
    TopstepX connector stub - to be implemented after receiving API docs
    """
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "https://api.topstepx.com"  # TODO: Confirm URL
        
        # Note: Implementation pending API documentation
        logger.warning("TopstepX connector initialized in stub mode - awaiting API docs")
    
    async def authenticate(self) -> str:
        """TODO: Implement after receiving API docs"""
        raise NotImplementedError("Awaiting TopstepX API documentation")
    
    async def get_account_metrics(self, account_id: str) -> FundedAccountRules:
        """TODO: Implement after receiving API docs"""
        # For now, return mock data for testing
        return FundedAccountRules(
            max_daily_loss=1000,
            max_contracts=3,
            trailing_drawdown=2000,
            profit_target=3000,
            current_daily_pnl=-250,
            current_drawdown=500
        )
```

#### Step 0.4: Funded Account Dashboard Component (Day 4)

##### Task 0.4.1: Create Funded Account Store
```typescript
// Create src/frontend/renderer/stores/fundedAccounts.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface FundedAccountRules {
  maxDailyLoss: number
  maxContracts: number
  trailingDrawdown: number
  profitTarget: number
}

export interface FundedAccount {
  id: string
  name: string
  platform: 'topstep' | 'apex' | 'tradeday'
  size: number
  rules: FundedAccountRules
  metrics: {
    dailyPnL: number
    totalPnL: number
    currentDrawdown: number
  }
}

export const useFundedAccountsStore = defineStore('fundedAccounts', () => {
  const accounts = ref<FundedAccount[]>([])
  const activeAccountId = ref<string>('')
  
  const activeAccount = computed(() => 
    accounts.value.find(a => a.id === activeAccountId.value)
  )
  
  // Actions
  async function fetchAccounts() {
    // TODO: Implement API call
  }
  
  async function updateMetrics(accountId: string) {
    // TODO: Implement real-time updates
  }
  
  return {
    accounts,
    activeAccountId,
    activeAccount,
    fetchAccounts,
    updateMetrics
  }
})
```

##### Task 0.4.2: Create Risk Meter Component
```vue
<!-- Create src/frontend/renderer/components/RiskMeter.vue -->
<template>
  <div class="risk-meter">
    <div class="meter-container">
      <label>{{ label }}</label>
      <div class="meter-bar" :class="severityClass">
        <div 
          class="meter-fill" 
          :style="{ width: percentage + '%' }"
          :class="{ 'danger-pulse': isDanger }"
        />
      </div>
      <div class="meter-values">
        <span class="current">${{ current.toFixed(2) }}</span>
        <span class="limit">/ ${{ limit.toFixed(2) }}</span>
      </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  current: number
  limit: number
  inverse?: boolean  // For drawdown, higher is worse
}>()

const percentage = computed(() => {
  const pct = (Math.abs(props.current) / props.limit) * 100
  return Math.min(pct, 100)
})

const severityClass = computed(() => {
  const pct = percentage.value
  if (pct >= 80) return 'danger'
  if (pct >= 60) return 'warning'
  return 'safe'
})

const isDanger = computed(() => percentage.value >= 80)
</script>

<style scoped>
.meter-bar {
  height: 24px;
  background: #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.meter-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.safe .meter-fill { background: #4caf50; }
.warning .meter-fill { background: #ff9800; }
.danger .meter-fill { background: #f44336; }

.danger-pulse {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}
</style>
```

##### Task 0.4.3: Create Account Selector Component
```vue
<!-- Create src/frontend/renderer/components/AccountSelector.vue -->
<template>
  <div class="account-selector">
    <select 
      v-model="selectedAccount" 
      @change="onAccountChange"
      class="account-dropdown"
    >
      <option value="">Select Account</option>
      <optgroup 
        v-for="platform in groupedAccounts" 
        :key="platform.name"
        :label="platform.name"
      >
        <option 
          v-for="account in platform.accounts" 
          :key="account.id"
          :value="account.id"
        >
          {{ account.name }} (${{ account.size.toLocaleString() }})
        </option>
      </optgroup>
    </select>
    
    <div v-if="activeAccount" class="account-status">
      <span class="status-indicator" :class="accountStatus"></span>
      {{ accountStatusText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFundedAccountsStore } from '@/stores/fundedAccounts'

const store = useFundedAccountsStore()

const selectedAccount = computed({
  get: () => store.activeAccountId,
  set: (value) => store.activeAccountId = value
})

const groupedAccounts = computed(() => {
  // Group accounts by platform
  const groups = store.accounts.reduce((acc, account) => {
    if (!acc[account.platform]) {
      acc[account.platform] = {
        name: account.platform.toUpperCase(),
        accounts: []
      }
    }
    acc[account.platform].accounts.push(account)
    return acc
  }, {} as Record<string, any>)
  
  return Object.values(groups)
})
</script>
```

##### Task 0.4.4: Assemble Complete Funded Account Panel
```vue
<!-- Update src/frontend/renderer/components/FundedAccountPanel.vue -->
<template>
  <div class="funded-account-panel">
    <div class="panel-header">
      <h3>Funded Accounts</h3>
      <AccountSelector />
    </div>
    
    <div v-if="activeAccount" class="account-details">
      <!-- Risk Metrics Grid -->
      <div class="metrics-grid">
        <RiskMeter
          label="Daily P&L"
          :current="activeAccount.metrics.dailyPnL"
          :limit="activeAccount.rules.maxDailyLoss"
        />
        
        <RiskMeter
          label="Trailing Drawdown"
          :current="activeAccount.metrics.currentDrawdown"
          :limit="activeAccount.rules.trailingDrawdown"
          :inverse="true"
        />
        
        <div class="profit-target-card">
          <label>Profit Target</label>
          <div class="target-progress">
            <span class="current">${{ activeAccount.metrics.totalPnL.toFixed(2) }}</span>
            <span class="target">/ ${{ activeAccount.rules.profitTarget.toFixed(2) }}</span>
          </div>
          <div class="progress-bar success">
            <div 
              class="progress-fill" 
              :style="{ width: profitProgress + '%' }"
            />
          </div>
        </div>
      </div>
      
      <!-- Trading Rules -->
      <div class="trading-rules">
        <h4>Account Rules</h4>
        <table>
          <tr>
            <td>Max Contracts:</td>
            <td>{{ activeAccount.rules.maxContracts }}</td>
          </tr>
          <tr>
            <td>Daily Loss Limit:</td>
            <td>${{ activeAccount.rules.maxDailyLoss }}</td>
          </tr>
          <tr>
            <td>Account Size:</td>
            <td>${{ activeAccount.size.toLocaleString() }}</td>
          </tr>
          <tr>
            <td>Platform:</td>
            <td>{{ activeAccount.platform.toUpperCase() }}</td>
          </tr>
        </table>
      </div>
      
      <!-- Quick Actions -->
      <div class="quick-actions">
        <button @click="flattenPositions" :disabled="!canTrade">
          Flatten All
        </button>
        <button @click="refreshMetrics">
          Refresh
        </button>
      </div>
    </div>
    
    <div v-else class="no-account">
      <p>Select a funded account to view metrics</p>
    </div>
  </div>
</template>
```

#### Step 0.5: Paper Trading Implementation (Day 4-5)

Since TradingView doesn't expose their Paper Trading broker via API, we'll implement a comprehensive paper trading solution using broker sandbox environments and an internal simulator.

##### Task 0.5.1: Create Paper Trading Router
```python
# Create src/backend/trading/paper_router.py
from typing import Dict, Optional
from enum import Enum

class PaperTradingMode(Enum):
    SANDBOX = "sandbox"      # Use broker sandbox (real API, fake money)
    SIMULATOR = "simulator"  # Internal simulation
    HYBRID = "hybrid"       # Sandbox for execution, simulator for fills

class PaperTradingRouter:
    """Route paper trading orders to appropriate sandbox or simulator"""
    
    def __init__(self):
        self.brokers = {
            'tastytrade_sandbox': TastytradeConnector(sandbox=True),
            'tradovate_demo': TradovateConnector(demo=True),
            'alpaca_paper': AlpacaConnector(paper=True),
            'simulator': InternalPaperTradingEngine()
        }
        
    async def route_order(self, alert: TradingViewAlert) -> Dict:
        """Route order based on account_group and paper_mode"""
        
        # Check if paper trading is requested
        if alert.account_group.startswith("paper_"):
            broker_key = self._get_paper_broker(alert.symbol, alert.account_group)
            broker = self.brokers[broker_key]
            
            # Add paper trading metadata
            alert.metadata = {
                "is_paper": True,
                "paper_mode": broker_key,
                "original_account": alert.account_group
            }
            
            return await broker.execute_alert(alert)
        else:
            # Route to live trading
            return await self.live_router.route_order(alert)
    
    def _get_paper_broker(self, symbol: str, account_group: str) -> str:
        """Determine which paper broker to use"""
        
        # Extract preference from account_group
        # Examples: "paper_tastytrade", "paper_simulator", "paper_auto"
        preference = account_group.split("_", 1)[1] if "_" in account_group else "auto"
        
        if preference == "auto":
            # Auto-select based on symbol type
            if symbol in ["ES", "NQ", "YM", "RTY"]:  # Futures
                return "tradovate_demo"  # Free demo account
            elif "/" in symbol:  # Options (SPY 400C)
                return "tastytrade_sandbox"
            else:  # Stocks
                return "alpaca_paper"  # Free, instant access
        else:
            return f"{preference}_sandbox"
```

##### Task 0.5.2: Create Internal Paper Trading Engine
```python
# Create src/backend/trading/paper_engine.py
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

class InternalPaperTradingEngine:
    """Simulate order execution with real market data"""
    
    def __init__(self, initial_balance: float = 100000):
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.fills: List[Fill] = []
        self.pnl_history = []
        
    async def execute_alert(self, alert: TradingViewAlert) -> Dict:
        """Execute paper trade with realistic simulation"""
        
        # Get current market price
        market_price = await self._get_market_price(alert.symbol)
        
        # Simulate order processing delay
        await asyncio.sleep(0.1)  # 100ms latency
        
        # Calculate fill price with slippage
        fill_price = self._calculate_fill_price(
            market_price, 
            alert.action, 
            alert.quantity
        )
        
        # Check buying power
        required_capital = fill_price * alert.quantity * self._get_multiplier(alert.symbol)
        if required_capital > self.balance and alert.action == "buy":
            return {
                "status": "rejected",
                "reason": "Insufficient buying power",
                "required": required_capital,
                "available": self.balance
            }
        
        # Create and fill order
        order = Order(
            id=generate_order_id(),
            symbol=alert.symbol,
            action=alert.action,
            quantity=alert.quantity,
            order_type="market",
            status="filled",
            fill_price=fill_price,
            timestamp=datetime.now()
        )
        
        # Update positions
        self._update_positions(order)
        
        # Record fill
        self.fills.append(Fill(
            order_id=order.id,
            price=fill_price,
            quantity=alert.quantity,
            commission=self._calculate_commission(alert),
            timestamp=datetime.now()
        ))
        
        return {
            "status": "success",
            "order": order.dict(),
            "fill": {
                "price": fill_price,
                "slippage": fill_price - market_price,
                "commission": self._calculate_commission(alert)
            }
        }
    
    def _calculate_fill_price(self, market_price: float, action: str, quantity: int) -> float:
        """Simulate realistic slippage based on order size"""
        
        # Base slippage: 0.01% for liquid instruments
        base_slippage = 0.0001
        
        # Size impact: additional slippage for larger orders
        size_impact = min(quantity / 1000, 0.001)  # Max 0.1% for huge orders
        
        total_slippage = base_slippage + size_impact
        
        if action == "buy":
            return market_price * (1 + total_slippage)
        else:
            return market_price * (1 - total_slippage)
    
    def _calculate_commission(self, alert: TradingViewAlert) -> float:
        """Calculate realistic commission"""
        
        if "ES" in alert.symbol or "NQ" in alert.symbol:
            # Futures commission
            return 2.25 * alert.quantity  # Per contract
        elif "/" in alert.symbol:
            # Options commission
            return 0.65 * alert.quantity  # Per contract
        else:
            # Stock commission (assume free)
            return 0.0
```

##### Task 0.5.3: Create Paper Trading Dashboard
```vue
<!-- Create src/frontend/renderer/components/PaperTradingPanel.vue -->
<template>
  <div class="paper-trading-panel">
    <div class="panel-header">
      <h3>Paper Trading</h3>
      <div class="mode-selector">
        <label>Mode:</label>
        <select v-model="paperMode">
          <option value="sandbox">Broker Sandbox</option>
          <option value="simulator">Internal Simulator</option>
          <option value="hybrid">Hybrid</option>
        </select>
      </div>
    </div>
    
    <div class="paper-accounts">
      <div class="account-card" v-for="account in paperAccounts" :key="account.id">
        <h4>{{ account.name }}</h4>
        <div class="metrics">
          <div class="metric">
            <label>Balance:</label>
            <span>${{ account.balance.toLocaleString() }}</span>
          </div>
          <div class="metric">
            <label>Day P&L:</label>
            <span :class="{ positive: account.dayPnL > 0, negative: account.dayPnL < 0 }">
              ${{ account.dayPnL.toFixed(2) }}
            </span>
          </div>
          <div class="metric">
            <label>Total P&L:</label>
            <span :class="{ positive: account.totalPnL > 0, negative: account.totalPnL < 0 }">
              ${{ account.totalPnL.toFixed(2) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="performance-chart">
      <h4>Paper Trading Performance</h4>
      <canvas ref="performanceChart"></canvas>
    </div>
    
    <div class="recent-trades">
      <h4>Recent Paper Trades</h4>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Price</th>
            <th>P&L</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trade in recentTrades" :key="trade.id">
            <td>{{ formatTime(trade.timestamp) }}</td>
            <td>{{ trade.symbol }}</td>
            <td :class="trade.side">{{ trade.side }}</td>
            <td>{{ trade.quantity }}</td>
            <td>${{ trade.price.toFixed(2) }}</td>
            <td :class="{ positive: trade.pnl > 0, negative: trade.pnl < 0 }">
              ${{ trade.pnl?.toFixed(2) || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePaperTradingStore } from '@/stores/paperTrading'
import Chart from 'chart.js/auto'

const store = usePaperTradingStore()
const performanceChart = ref<HTMLCanvasElement>()

const paperMode = computed({
  get: () => store.mode,
  set: (value) => store.setMode(value)
})

const paperAccounts = computed(() => store.accounts)
const recentTrades = computed(() => store.recentTrades.slice(0, 10))

onMounted(() => {
  // Initialize performance chart
  if (performanceChart.value) {
    new Chart(performanceChart.value, {
      type: 'line',
      data: {
        labels: store.performanceHistory.map(p => p.date),
        datasets: [{
          label: 'Paper Trading P&L',
          data: store.performanceHistory.map(p => p.cumulativePnL),
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Cumulative P&L'
          }
        }
      }
    })
  }
})
</script>
```

##### Task 0.5.4: Configure Webhook for Paper Trading
```python
# Update src/backend/webhooks/tradingview_receiver.py
@router.post("/tradingview")
async def receive_tradingview_alert(
    request: Request,
    tv_webhook_secret: str = Header(None, alias="X-Webhook-Signature")
):
    """Receive and validate TradingView webhook alerts"""
    # ... existing validation code ...
    
    # Parse alert
    alert = TradingViewAlert(**alert_data)
    
    # Route to paper trading if requested
    if alert.account_group.startswith("paper_") or alert.comment == "PAPER":
        paper_router = PaperTradingRouter()
        result = await paper_router.route_order(alert)
        
        # Track paper trading performance
        await track_paper_performance(alert, result)
        
        return {
            "status": "received",
            "alert_id": generate_alert_id(),
            "is_paper": True,
            "result": result
        }
    
    # ... existing live trading code ...
```

##### Task 0.5.5: Create TradingView Alert Templates
```javascript
// Create docs/TRADINGVIEW_ALERTS.md

# TradingView Alert Templates for Paper Trading

## Basic Paper Trading Alert
```json
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "quantity": {{strategy.order.contracts}},
  "account_group": "paper_auto",
  "strategy": "{{strategy.name}}"
}
```

## Specific Broker Paper Trading
```json
// For Tastytrade Sandbox
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "quantity": {{strategy.order.contracts}},
  "account_group": "paper_tastytrade",
  "strategy": "{{strategy.name}}"
}

// For Tradovate Demo
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "quantity": {{strategy.order.contracts}},
  "account_group": "paper_tradovate",
  "strategy": "{{strategy.name}}"
}
```

## Mixed Live/Paper Trading
```json
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "quantity": {{strategy.order.contracts}},
  "account_group": "{{strategy.order.comment}}",  // Use "paper_auto" or "live_topstep"
  "strategy": "{{strategy.name}}"
}
```
```

##### Task 0.5.6: Create Paper Trading Store
```typescript
// Create src/frontend/renderer/stores/paperTrading.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface PaperAccount {
  id: string
  name: string
  broker: 'tastytrade' | 'tradovate' | 'alpaca' | 'simulator'
  balance: number
  dayPnL: number
  totalPnL: number
  positions: Position[]
}

export interface PaperTrade {
  id: string
  timestamp: Date
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  pnl?: number
}

export const usePaperTradingStore = defineStore('paperTrading', () => {
  const mode = ref<'sandbox' | 'simulator' | 'hybrid'>('sandbox')
  const accounts = ref<PaperAccount[]>([])
  const recentTrades = ref<PaperTrade[]>([])
  const performanceHistory = ref<{ date: string, cumulativePnL: number }[]>([])
  
  // Initialize default paper accounts
  const initializeAccounts = async () => {
    accounts.value = [
      {
        id: 'paper_tastytrade',
        name: 'Tastytrade Sandbox',
        broker: 'tastytrade',
        balance: 100000,
        dayPnL: 0,
        totalPnL: 0,
        positions: []
      },
      {
        id: 'paper_tradovate',
        name: 'Tradovate Demo',
        broker: 'tradovate',
        balance: 50000,
        dayPnL: 0,
        totalPnL: 0,
        positions: []
      },
      {
        id: 'paper_simulator',
        name: 'Internal Simulator',
        broker: 'simulator',
        balance: 100000,
        dayPnL: 0,
        totalPnL: 0,
        positions: []
      }
    ]
  }
  
  const setMode = (newMode: typeof mode.value) => {
    mode.value = newMode
  }
  
  const addTrade = (trade: PaperTrade) => {
    recentTrades.value.unshift(trade)
    // Keep only last 100 trades
    if (recentTrades.value.length > 100) {
      recentTrades.value.pop()
    }
  }
  
  return {
    mode,
    accounts,
    recentTrades,
    performanceHistory,
    initializeAccounts,
    setMode,
    addTrade
  }
})
```

#### Step 0.6: Strategy Performance Monitoring & Auto-Rotation (Day 5)

Implement automated strategy performance tracking that monitors win rates in sets of 20 trades and automatically moves underperforming strategies to paper trading until they prove profitable again.

##### Task 0.6.1: Create Strategy Performance Models
```python
# Create src/backend/strategies/models.py
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class TradingMode(Enum):
    LIVE = "live"
    PAPER = "paper"
    SUSPENDED = "suspended"

class TradeResult(BaseModel):
    strategy_id: str
    trade_id: str
    symbol: str
    entry_price: float
    exit_price: float
    quantity: int
    side: Literal["long", "short"]
    pnl: float
    win: bool
    timestamp: datetime
    mode: TradingMode
    set_number: int
    trade_number_in_set: int

class StrategySet(BaseModel):
    """Represents a set of 20 trades for evaluation"""
    set_number: int
    strategy_id: str
    trades: List[TradeResult]
    win_rate: float
    total_pnl: float
    start_date: datetime
    end_date: Optional[datetime] = None
    mode: TradingMode
    
    @property
    def is_complete(self) -> bool:
        return len(self.trades) >= 20
    
    @property
    def calculate_win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for trade in self.trades if trade.win)
        return (wins / len(self.trades)) * 100

class StrategyPerformance(BaseModel):
    strategy_id: str
    strategy_name: str
    current_mode: TradingMode
    current_set: StrategySet
    completed_sets: List[StrategySet]
    mode_transition_history: List[dict]  # Track when strategy moved between live/paper
    
    # Performance thresholds
    min_win_rate: float = 55.0  # Minimum acceptable win rate
    evaluation_period: int = 20  # Trades per set
    consecutive_fails_to_paper: int = 2  # Failed sets before moving to paper
    consecutive_wins_to_live: int = 2  # Successful sets before returning to live
    
    def should_move_to_paper(self) -> bool:
        """Check if strategy should be moved to paper trading"""
        if self.current_mode != TradingMode.LIVE:
            return False
            
        # Need at least 2 completed sets to evaluate
        if len(self.completed_sets) < self.consecutive_fails_to_paper:
            return False
            
        # Check last N sets
        recent_sets = self.completed_sets[-self.consecutive_fails_to_paper:]
        failed_sets = sum(1 for s in recent_sets if s.win_rate < self.min_win_rate)
        
        return failed_sets >= self.consecutive_fails_to_paper
    
    def should_move_to_live(self) -> bool:
        """Check if strategy should be moved back to live trading"""
        if self.current_mode != TradingMode.PAPER:
            return False
            
        # Get paper trading sets only
        paper_sets = [s for s in self.completed_sets if s.mode == TradingMode.PAPER]
        
        if len(paper_sets) < self.consecutive_wins_to_live:
            return False
            
        # Check last N paper sets
        recent_paper_sets = paper_sets[-self.consecutive_wins_to_live:]
        successful_sets = sum(1 for s in recent_paper_sets if s.win_rate >= self.min_win_rate)
        
        return successful_sets >= self.consecutive_wins_to_live
```

##### Task 0.6.2: Create Strategy Performance Tracker
```python
# Create src/backend/strategies/performance_tracker.py
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from collections import defaultdict

class StrategyPerformanceTracker:
    """Track and evaluate strategy performance across live and paper trading"""
    
    def __init__(self):
        self.strategies: Dict[str, StrategyPerformance] = {}
        self.active_trades: Dict[str, TradeResult] = {}  # trade_id -> TradeResult
        self.mode_change_callbacks = []
        
    async def register_strategy(
        self, 
        strategy_id: str, 
        strategy_name: str,
        min_win_rate: float = 55.0,
        evaluation_period: int = 20
    ) -> StrategyPerformance:
        """Register a new strategy for tracking"""
        
        if strategy_id in self.strategies:
            return self.strategies[strategy_id]
            
        strategy = StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            current_mode=TradingMode.LIVE,
            current_set=StrategySet(
                set_number=1,
                strategy_id=strategy_id,
                trades=[],
                win_rate=0.0,
                total_pnl=0.0,
                start_date=datetime.now(),
                mode=TradingMode.LIVE
            ),
            completed_sets=[],
            mode_transition_history=[],
            min_win_rate=min_win_rate,
            evaluation_period=evaluation_period
        )
        
        self.strategies[strategy_id] = strategy
        return strategy
    
    async def record_trade_entry(
        self,
        strategy_id: str,
        trade_id: str,
        symbol: str,
        entry_price: float,
        quantity: int,
        side: Literal["long", "short"]
    ):
        """Record trade entry"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return
            
        trade = TradeResult(
            strategy_id=strategy_id,
            trade_id=trade_id,
            symbol=symbol,
            entry_price=entry_price,
            exit_price=0.0,  # Will be filled on exit
            quantity=quantity,
            side=side,
            pnl=0.0,  # Will be calculated on exit
            win=False,  # Will be determined on exit
            timestamp=datetime.now(),
            mode=strategy.current_mode,
            set_number=strategy.current_set.set_number,
            trade_number_in_set=len(strategy.current_set.trades) + 1
        )
        
        self.active_trades[trade_id] = trade
    
    async def record_trade_exit(
        self,
        trade_id: str,
        exit_price: float
    ):
        """Record trade exit and evaluate performance"""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return
            
        # Calculate P&L
        if trade.side == "long":
            trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        else:  # short
            trade.pnl = (trade.entry_price - exit_price) * trade.quantity
            
        trade.exit_price = exit_price
        trade.win = trade.pnl > 0
        
        # Add to strategy's current set
        strategy = self.strategies[trade.strategy_id]
        strategy.current_set.trades.append(trade)
        
        # Remove from active trades
        del self.active_trades[trade_id]
        
        # Check if set is complete
        if strategy.current_set.is_complete:
            await self._complete_set(strategy)
    
    async def _complete_set(self, strategy: StrategyPerformance):
        """Complete current set and evaluate for mode changes"""
        
        # Calculate final metrics
        strategy.current_set.win_rate = strategy.current_set.calculate_win_rate
        strategy.current_set.total_pnl = sum(t.pnl for t in strategy.current_set.trades)
        strategy.current_set.end_date = datetime.now()
        
        # Add to completed sets
        strategy.completed_sets.append(strategy.current_set)
        
        # Evaluate for mode change
        mode_changed = False
        new_mode = strategy.current_mode
        
        if strategy.should_move_to_paper():
            new_mode = TradingMode.PAPER
            mode_changed = True
            await self._transition_to_paper(strategy)
            
        elif strategy.should_move_to_live():
            new_mode = TradingMode.LIVE
            mode_changed = True
            await self._transition_to_live(strategy)
        
        # Start new set
        strategy.current_set = StrategySet(
            set_number=strategy.current_set.set_number + 1,
            strategy_id=strategy.strategy_id,
            trades=[],
            win_rate=0.0,
            total_pnl=0.0,
            start_date=datetime.now(),
            mode=new_mode
        )
        
        # Notify if mode changed
        if mode_changed:
            await self._notify_mode_change(strategy, new_mode)
    
    async def _transition_to_paper(self, strategy: StrategyPerformance):
        """Transition strategy to paper trading"""
        logger.warning(
            f"Strategy '{strategy.strategy_name}' moving to PAPER trading. "
            f"Last 2 sets win rates: {[s.win_rate for s in strategy.completed_sets[-2:]]}"
        )
        
        strategy.current_mode = TradingMode.PAPER
        strategy.mode_transition_history.append({
            "from": TradingMode.LIVE,
            "to": TradingMode.PAPER,
            "timestamp": datetime.now(),
            "reason": "Underperformance - consecutive sets below 55% win rate",
            "last_sets": [s.dict() for s in strategy.completed_sets[-2:]]
        })
    
    async def _transition_to_live(self, strategy: StrategyPerformance):
        """Transition strategy back to live trading"""
        logger.info(
            f"Strategy '{strategy.strategy_name}' returning to LIVE trading! "
            f"Last 2 paper sets win rates: {[s.win_rate for s in strategy.completed_sets[-2:] if s.mode == TradingMode.PAPER]}"
        )
        
        strategy.current_mode = TradingMode.LIVE
        strategy.mode_transition_history.append({
            "from": TradingMode.PAPER,
            "to": TradingMode.LIVE,
            "timestamp": datetime.now(),
            "reason": "Performance recovered - consecutive paper sets above 55% win rate",
            "last_paper_sets": [s.dict() for s in strategy.completed_sets if s.mode == TradingMode.PAPER][-2:]
        })
    
    async def _notify_mode_change(self, strategy: StrategyPerformance, new_mode: TradingMode):
        """Notify all callbacks about mode change"""
        for callback in self.mode_change_callbacks:
            await callback(strategy, new_mode)
```

##### Task 0.6.3: Update Webhook Router for Strategy Tracking
```python
# Update src/backend/webhooks/tradingview_receiver.py
from src.backend.strategies.performance_tracker import StrategyPerformanceTracker

# Initialize global tracker
strategy_tracker = StrategyPerformanceTracker()

@router.post("/tradingview")
async def receive_tradingview_alert(
    request: Request,
    tv_webhook_secret: str = Header(None, alias="X-Webhook-Signature")
):
    """Receive and validate TradingView webhook alerts"""
    # ... existing validation code ...
    
    # Parse alert
    alert = TradingViewAlert(**alert_data)
    
    # Check strategy performance status
    if alert.strategy:
        strategy = await strategy_tracker.get_strategy(alert.strategy)
        
        # Override account group based on strategy mode
        if strategy and strategy.current_mode == TradingMode.PAPER:
            # Force to paper trading
            original_account = alert.account_group
            alert.account_group = f"paper_{alert.account_group}"
            logger.info(
                f"Strategy '{alert.strategy}' is in PAPER mode. "
                f"Routing to paper account instead of {original_account}"
            )
    
    # ... rest of existing code ...
```

##### Task 0.6.4: Create Strategy Performance Dashboard
```vue
<!-- Create src/frontend/renderer/components/StrategyPerformancePanel.vue -->
<template>
  <div class="strategy-performance-panel">
    <div class="panel-header">
      <h3>Strategy Performance Monitor</h3>
      <div class="controls">
        <button @click="refreshData" class="refresh-btn">
          <i class="fas fa-sync"></i> Refresh
        </button>
      </div>
    </div>
    
    <!-- Strategy Cards -->
    <div class="strategies-grid">
      <div 
        v-for="strategy in strategies" 
        :key="strategy.strategyId"
        class="strategy-card"
        :class="{ 
          'paper-mode': strategy.currentMode === 'paper',
          'warning': strategy.isAtRisk
        }"
      >
        <div class="strategy-header">
          <h4>{{ strategy.strategyName }}</h4>
          <span class="mode-badge" :class="strategy.currentMode">
            {{ strategy.currentMode.toUpperCase() }}
          </span>
        </div>
        
        <!-- Current Set Progress -->
        <div class="current-set">
          <div class="set-info">
            <span>Set #{{ strategy.currentSet.setNumber }}</span>
            <span>{{ strategy.currentSet.trades.length }}/20 trades</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: (strategy.currentSet.trades.length / 20) * 100 + '%' }"
            />
          </div>
          <div class="set-metrics">
            <span class="win-rate" :class="{ low: currentWinRate(strategy) < 55 }">
              Win: {{ currentWinRate(strategy).toFixed(1) }}%
            </span>
            <span class="pnl" :class="{ negative: currentPnL(strategy) < 0 }">
              P&L: ${{ currentPnL(strategy).toFixed(2) }}
            </span>
          </div>
        </div>
        
        <!-- Recent Sets History -->
        <div class="sets-history">
          <h5>Recent Sets</h5>
          <div class="sets-list">
            <div 
              v-for="set in getRecentSets(strategy)" 
              :key="set.setNumber"
              class="set-item"
              :class="{ 
                success: set.winRate >= 55, 
                failure: set.winRate < 55,
                paper: set.mode === 'paper' 
              }"
            >
              <span class="set-number">#{{ set.setNumber }}</span>
              <span class="set-win-rate">{{ set.winRate.toFixed(1) }}%</span>
              <span class="set-pnl">${{ set.totalPnl.toFixed(0) }}</span>
              <span v-if="set.mode === 'paper'" class="paper-indicator">P</span>
            </div>
          </div>
        </div>
        
        <!-- Mode Transition Warning -->
        <div v-if="strategy.isAtRisk" class="risk-warning">
          <i class="fas fa-exclamation-triangle"></i>
          {{ getRiskMessage(strategy) }}
        </div>
        
        <!-- Mode History -->
        <div v-if="strategy.modeTransitionHistory.length > 0" class="mode-history">
          <div class="last-transition">
            Last transition: {{ formatLastTransition(strategy) }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Global Statistics -->
    <div class="global-stats">
      <div class="stat-card">
        <label>Active Strategies</label>
        <div class="value">{{ activeStrategiesCount }}</div>
      </div>
      <div class="stat-card">
        <label>In Paper Mode</label>
        <div class="value warning">{{ paperModeCount }}</div>
      </div>
      <div class="stat-card">
        <label>Overall Win Rate</label>
        <div class="value">{{ overallWinRate.toFixed(1) }}%</div>
      </div>
      <div class="stat-card">
        <label>Total P&L Today</label>
        <div class="value" :class="{ negative: totalDailyPnL < 0 }">
          ${{ totalDailyPnL.toFixed(2) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStrategyPerformanceStore } from '@/stores/strategyPerformance'

const store = useStrategyPerformanceStore()
const strategies = computed(() => store.strategies)

const currentWinRate = (strategy) => {
  const trades = strategy.currentSet.trades
  if (trades.length === 0) return 0
  const wins = trades.filter(t => t.win).length
  return (wins / trades.length) * 100
}

const currentPnL = (strategy) => {
  return strategy.currentSet.trades.reduce((sum, t) => sum + t.pnl, 0)
}

const getRecentSets = (strategy) => {
  return strategy.completedSets.slice(-5).reverse()
}

const getRiskMessage = (strategy) => {
  const recentSets = strategy.completedSets.slice(-2)
  const failedSets = recentSets.filter(s => s.winRate < 55).length
  
  if (strategy.currentMode === 'live' && failedSets >= 1) {
    return `Warning: ${failedSets} set(s) below 55% win rate. One more will trigger paper mode.`
  } else if (strategy.currentMode === 'paper') {
    const paperSets = strategy.completedSets.filter(s => s.mode === 'paper')
    const recentPaperSets = paperSets.slice(-2)
    const successfulSets = recentPaperSets.filter(s => s.winRate >= 55).length
    return `${successfulSets}/2 successful paper sets needed to return to live.`
  }
  return ''
}

const activeStrategiesCount = computed(() => 
  strategies.value.filter(s => s.currentMode === 'live').length
)

const paperModeCount = computed(() => 
  strategies.value.filter(s => s.currentMode === 'paper').length
)

const overallWinRate = computed(() => {
  const allTrades = strategies.value.flatMap(s => [
    ...s.currentSet.trades,
    ...s.completedSets.flatMap(set => set.trades)
  ])
  if (allTrades.length === 0) return 0
  const wins = allTrades.filter(t => t.win).length
  return (wins / allTrades.length) * 100
})

const totalDailyPnL = computed(() => {
  // Calculate P&L for today only
  const today = new Date().toDateString()
  return strategies.value.reduce((total, strategy) => {
    const todayTrades = strategy.currentSet.trades.filter(
      t => new Date(t.timestamp).toDateString() === today
    )
    return total + todayTrades.reduce((sum, t) => sum + t.pnl, 0)
  }, 0)
})

onMounted(() => {
  store.fetchStrategies()
  // Set up real-time updates
  setInterval(() => store.fetchStrategies(), 5000)
})
</script>

<style scoped>
.strategy-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.strategy-card.paper-mode {
  border-color: #ff9800;
  background-color: #fff3e0;
}

.strategy-card.warning {
  border-color: #f44336;
}

.mode-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.mode-badge.live {
  background: #4caf50;
  color: white;
}

.mode-badge.paper {
  background: #ff9800;
  color: white;
}

.sets-list {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.set-item {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 12px;
}

.set-item.success {
  background: #e8f5e9;
  border-color: #4caf50;
}

.set-item.failure {
  background: #ffebee;
  border-color: #f44336;
}

.set-item.paper {
  border-style: dashed;
}

.risk-warning {
  margin-top: 12px;
  padding: 8px;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  color: #856404;
  font-size: 14px;
}
</style>
```

##### Task 0.6.5: Create Strategy Performance Store
```typescript
// Create src/frontend/renderer/stores/strategyPerformance.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface StrategyMetrics {
  strategyId: string
  strategyName: string
  currentMode: 'live' | 'paper' | 'suspended'
  currentSet: {
    setNumber: number
    trades: TradeResult[]
    winRate: number
    totalPnl: number
  }
  completedSets: SetResult[]
  modeTransitionHistory: TransitionEvent[]
  isAtRisk: boolean
}

export interface TradeResult {
  tradeId: string
  symbol: string
  entryPrice: number
  exitPrice: number
  quantity: number
  side: 'long' | 'short'
  pnl: number
  win: boolean
  timestamp: string
}

export interface SetResult {
  setNumber: number
  trades: TradeResult[]
  winRate: number
  totalPnl: number
  startDate: string
  endDate: string
  mode: 'live' | 'paper'
}

export interface TransitionEvent {
  from: string
  to: string
  timestamp: string
  reason: string
}

export const useStrategyPerformanceStore = defineStore('strategyPerformance', () => {
  const strategies = ref<StrategyMetrics[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  async function fetchStrategies() {
    try {
      loading.value = true
      const response = await api.getStrategyPerformance()
      strategies.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }
  
  async function updateStrategyMode(strategyId: string, newMode: 'live' | 'paper') {
    try {
      await api.updateStrategyMode(strategyId, newMode)
      await fetchStrategies()
    } catch (e) {
      error.value = e.message
    }
  }
  
  // Subscribe to real-time mode changes
  function subscribeToModeChanges() {
    api.on('strategy-mode-change', (data) => {
      const strategy = strategies.value.find(s => s.strategyId === data.strategyId)
      if (strategy) {
        strategy.currentMode = data.newMode
        strategy.modeTransitionHistory.push(data.transition)
      }
    })
  }
  
  return {
    strategies,
    loading,
    error,
    fetchStrategies,
    updateStrategyMode,
    subscribeToModeChanges
  }
})
```

##### Task 0.6.6: Create API Endpoints for Strategy Performance
```python
# Add to src/backend/routes/strategies.py
from fastapi import APIRouter, HTTPException
from src.backend.strategies.performance_tracker import strategy_tracker

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

@router.get("/performance")
async def get_strategy_performance():
    """Get performance metrics for all strategies"""
    strategies = []
    
    for strategy_id, strategy in strategy_tracker.strategies.items():
        # Calculate if strategy is at risk
        is_at_risk = False
        if strategy.current_mode == TradingMode.LIVE:
            recent_sets = strategy.completed_sets[-2:]
            if len(recent_sets) >= 1:
                failed_sets = sum(1 for s in recent_sets if s.win_rate < 55)
                is_at_risk = failed_sets >= 1
        
        strategies.append({
            "strategyId": strategy.strategy_id,
            "strategyName": strategy.strategy_name,
            "currentMode": strategy.current_mode.value,
            "currentSet": {
                "setNumber": strategy.current_set.set_number,
                "trades": [t.dict() for t in strategy.current_set.trades],
                "winRate": strategy.current_set.calculate_win_rate,
                "totalPnl": sum(t.pnl for t in strategy.current_set.trades)
            },
            "completedSets": [s.dict() for s in strategy.completed_sets[-10:]],  # Last 10 sets
            "modeTransitionHistory": strategy.mode_transition_history[-5:],  # Last 5 transitions
            "isAtRisk": is_at_risk
        })
    
    return {"strategies": strategies}

@router.post("/register")
async def register_strategy(
    strategy_id: str,
    strategy_name: str,
    min_win_rate: float = 55.0,
    evaluation_period: int = 20
):
    """Register a new strategy for performance tracking"""
    strategy = await strategy_tracker.register_strategy(
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        min_win_rate=min_win_rate,
        evaluation_period=evaluation_period
    )
    
    return {"status": "registered", "strategy": strategy.dict()}

@router.post("/{strategy_id}/mode")
async def manual_mode_override(
    strategy_id: str,
    new_mode: Literal["live", "paper", "suspended"]
):
    """Manually override strategy mode"""
    strategy = strategy_tracker.strategies.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    old_mode = strategy.current_mode
    strategy.current_mode = TradingMode(new_mode)
    
    # Add to transition history
    strategy.mode_transition_history.append({
        "from": old_mode.value,
        "to": new_mode,
        "timestamp": datetime.now(),
        "reason": "Manual override by user"
    })
    
    return {"status": "updated", "oldMode": old_mode.value, "newMode": new_mode}
```

## Final Validation Checklist

- [ ] All webhooks tested and verified
- [ ] Funded account risk management operational
- [ ] Paper trading working across all brokers
- [ ] Strategy performance monitoring active
- [ ] Desktop app packaged and installable

## Risk Mitigation

1. **API Access Delays**: Tastytrade and Alpaca provide instant sandbox access as fallback
2. **TopStepX API Unavailable**: Build adapter for manual order entry with funded rules enforcement
3. **Performance Issues**: Implement circuit breakers and rate limiting on all broker connections
4. **Data Feed Interruptions**: Automatic reconnection with exponential backoff
5. **Strategy Underperformance**: Automatic paper trading rotation prevents live losses

## Post-MVP Roadmap

1. **Month 1**: NinjaTrader integration for alternative execution
2. **Month 2**: Advanced analytics dashboard with ML-based insights
3. **Month 3**: Mobile companion app for monitoring
4. **Month 4**: Social trading features for strategy sharing
5. **Month 6**: Cloud deployment option for 24/7 operation

## Document History

- **v1.0** (2025-01-20): Initial PRP creation
- **v1.1** (2025-01-20): Added strategy performance monitoring & auto-rotation
- **v1.2** (2025-01-20): Added TradeNote integration for trade journaling
- **v1.3** (2025-01-20): Restructured into master + phase-specific documents

## Related Documents

- [`IMPLEMENTATION_SUMMARY.md`](../../IMPLEMENTATION_SUMMARY.md) - Current implementation status
- [`docs/QUICK_START.md`](../../QUICK_START.md) - Getting started guide
- [`docs/TRADINGVIEW_ALERTS.md`](../../TRADINGVIEW_ALERTS.md) - Webhook configuration
- [`docs/TRADE_JOURNAL.md`](../../TRADE_JOURNAL.md) - TradeNote setup guide

#### Step 0.7: Trade Journal Integration with TradeNote (Week 2)

Leverage the open-source [TradeNote](https://github.com/Eleven-Trading/TradeNote) project to provide advanced trade journaling, tag-based analytics, and calendar heat-map performance visualization.

##### Objective
Create a seamless, privacy-first journal inside TraderTerminal where every live and paper trade is automatically logged to TradeNote, enabling rich analytics without rebuilding journaling features from scratch.

##### Task 0.7.1: Containerize TradeNote
```bash
# New directory: docker/tradenote/
# Add docker-compose.override.yml with TradeNote services
services:
  tradenote:
    image: eleventrading/tradenote:latest
    environment:
      - MONGO_URI=mongodb://tradenote:tradenote@mongo:27017/tradenote?authSource=admin
      - TRADENOTE_DATABASE=tradenote
      - APP_ID=${TRADENOTE_APP_ID}
      - MASTER_KEY=${TRADENOTE_MASTER_KEY}
      - TRADENOTE_PORT=8080
    ports:
      - "8080:8080"
    depends_on:
      - mongo
  mongo:
    image: mongo:6.0
    volumes:
      - tradenote_data:/data/db
volumes:
  tradenote_data:
```

##### Task 0.7.2: Authentication Bridge
```python
# Create src/backend/integrations/tradenote/client.py
"""Minimal client for pushing trades to TradeNote via REST API"""
from typing import Dict, Optional
import httpx
from datetime import datetime

class TradeNoteClient:
    def __init__(self, base_url: str, app_id: str, master_key: str):
        self.base_url = base_url
        self.app_id = app_id
        self.master_key = master_key
        self.client = httpx.AsyncClient()
        
    async def log_trade(self, trade: TradeResult) -> Dict:
        """Log a completed trade to TradeNote"""
        tradenote_trade = {
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.exit_price,
            "commission": 2.50,  # TODO: Get from broker
            "date": trade.timestamp.isoformat(),
            "pnl": trade.pnl,
            "notes": f"Strategy: {trade.strategy_id}",
            "tags": [trade.strategy_id, trade.mode.value]
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/trades",
            json=tradenote_trade,
            headers={
                "X-Parse-Application-Id": self.app_id,
                "X-Parse-Master-Key": self.master_key
            }
        )
        return response.json()
        
    async def get_calendar_heatmap(self, year: int) -> Dict:
        """Get calendar heatmap data for the year"""
        response = await self.client.get(
            f"{self.base_url}/api/calendar/{year}",
            headers={
                "X-Parse-Application-Id": self.app_id,
                "X-Parse-Master-Key": self.master_key
            }
        )
        return response.json()
```

##### Task 0.7.3: Trade Logger Hook
Hook into the Order Execution layer (live & paper) and send every fill to TradeNote:
```python
# Update src/backend/strategies/performance_tracker.py
from src.backend.integrations.tradenote.client import TradeNoteClient

class StrategyPerformanceTracker:
    def __init__(self):
        # ... existing init code ...
        self.tradenote_client = TradeNoteClient(
            base_url=os.getenv("TRADENOTE_BASE_URL", "http://localhost:8080"),
            app_id=os.getenv("TRADENOTE_APP_ID"),
            master_key=os.getenv("TRADENOTE_MASTER_KEY")
        )
        
    async def record_trade_exit(self, trade_id: str, exit_price: float):
        """Record trade exit and evaluate performance"""
        # ... existing code ...
        
        # Log to TradeNote after recording exit
        try:
            await self.tradenote_client.log_trade(trade)
            logger.info(f"Trade {trade_id} logged to TradeNote")
        except Exception as e:
            logger.error(f"Failed to log trade to TradeNote: {e}")
```

##### Task 0.7.4: Calendar Performance Widget
```vue
<!-- Create src/frontend/renderer/components/TradeCalendar.vue -->
<template>
  <div class="trade-calendar">
    <h3>Performance Calendar</h3>
    <div class="year-selector">
      <button @click="previousYear">&lt;</button>
      <span>{{ selectedYear }}</span>
      <button @click="nextYear">&gt;</button>
    </div>
    
    <div class="calendar-heatmap" v-if="heatmapData">
      <vue-cal-heatmap 
        :data="heatmapData"
        :year="selectedYear"
        :colorScale="colorScale"
        @day-click="onDayClick"
      />
    </div>
    
    <div class="calendar-legend">
      <span>Loss</span>
      <div class="legend-scale">
        <div v-for="color in legendColors" :key="color" 
             :style="{ backgroundColor: color }" 
             class="legend-block">
        </div>
      </div>
      <span>Profit</span>
    </div>
    
    <div v-if="selectedDayTrades" class="day-trades-modal">
      <h4>Trades for {{ selectedDate }}</h4>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Side</th>
            <th>P&L</th>
            <th>Strategy</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trade in selectedDayTrades" :key="trade.id">
            <td>{{ trade.symbol }}</td>
            <td>{{ trade.side }}</td>
            <td :class="{ profit: trade.pnl > 0, loss: trade.pnl < 0 }">
              ${{ trade.pnl.toFixed(2) }}
            </td>
            <td>{{ trade.strategy }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VueCalHeatmap from 'vue-cal-heatmap'
import { useTradeJournalStore } from '@/stores/tradeJournal'

const store = useTradeJournalStore()
const selectedYear = ref(new Date().getFullYear())
const selectedDayTrades = ref(null)
const selectedDate = ref('')

const heatmapData = computed(() => store.getHeatmapData(selectedYear.value))

const colorScale = computed(() => ({
  min: -500,  // Max daily loss
  max: 500,   // Max daily profit
  scheme: 'RdYlGn'  // Red to Yellow to Green
}))

const legendColors = ['#d32f2f', '#f57c00', '#fbc02d', '#689f38', '#388e3c']

const previousYear = () => {
  selectedYear.value -= 1
  store.fetchYearData(selectedYear.value)
}

const nextYear = () => {
  if (selectedYear.value < new Date().getFullYear()) {
    selectedYear.value += 1
    store.fetchYearData(selectedYear.value)
  }
}

const onDayClick = (date: string) => {
  selectedDate.value = date
  selectedDayTrades.value = store.getTradesForDate(date)
}

onMounted(() => {
  store.fetchYearData(selectedYear.value)
})
</script>

<style scoped>
.trade-calendar {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.year-selector {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
  gap: 20px;
}

.calendar-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 20px;
  gap: 10px;
}

.legend-scale {
  display: flex;
  gap: 2px;
}

.legend-block {
  width: 20px;
  height: 20px;
  border-radius: 2px;
}

.day-trades-modal {
  position: absolute;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1000;
}

.profit { color: #4caf50; }
.loss { color: #f44336; }
</style>
```

##### Task 0.7.5: Sync & Backfill Script
```bash
# scripts/backfill_trades_to_tradenote.sh
#!/bin/bash

echo "Backfilling historical trades to TradeNote..."

# Python script to backfill
cat > /tmp/backfill_tradenote.py << 'EOF'
import asyncio
from datetime import datetime, timedelta
from src.backend.integrations.tradenote.client import TradeNoteClient
from src.backend.database import get_historical_trades

async def backfill_trades(start_date: str, end_date: str):
    client = TradeNoteClient(
        base_url="http://localhost:8080",
        app_id=os.getenv("TRADENOTE_APP_ID"),
        master_key=os.getenv("TRADENOTE_MASTER_KEY")
    )
    
    trades = await get_historical_trades(start_date, end_date)
    
    for trade in trades:
        try:
            await client.log_trade(trade)
            print(f"✓ Backfilled trade {trade.id}")
        except Exception as e:
            print(f"✗ Failed to backfill trade {trade.id}: {e}")
            
    print(f"\nBackfilled {len(trades)} trades")

if __name__ == "__main__":
    import sys
    start = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    end = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y-%m-%d")
    
    asyncio.run(backfill_trades(start, end))
EOF

python /tmp/backfill_tradenote.py "$@"
```

##### Task 0.7.6: Documentation
```markdown
# Create docs/TRADE_JOURNAL.md

# TradeNote Integration Guide

## Overview

TraderTerminal integrates with [TradeNote](https://github.com/Eleven-Trading/TradeNote) to provide comprehensive trade journaling and analytics.

## Features

- Automatic trade logging (live and paper trades)
- Calendar heatmap visualization
- Tag-based analytics
- Performance metrics
- Trade notes and screenshots
- Privacy-first (self-hosted)

## Setup

### 1. Start TradeNote Container

```bash
cd docker/tradenote
docker-compose up -d
```

### 2. Configure Environment

```env
# .env
TRADENOTE_BASE_URL=http://localhost:8080
TRADENOTE_APP_ID=your_app_id_here
TRADENOTE_MASTER_KEY=your_master_key_here
```

### 3. Access TradeNote UI

- TradeNote UI: http://localhost:8080
- Default login: admin/admin (change immediately)

### 4. Backfill Historical Trades

```bash
./scripts/backfill_trades_to_tradenote.sh 2024-01-01 today
```

## Usage

### Automatic Logging

All trades are automatically logged when positions are closed:
- Strategy name as primary tag
- Trading mode (live/paper) as secondary tag
- P&L, commission, and execution details

### Manual Notes

Add notes to trades via TradeNote UI:
1. Navigate to http://localhost:8080
2. Find trade in the list
3. Click "Edit" to add notes/screenshots

### Performance Analysis

View performance metrics:
- Daily P&L calendar
- Win rate by strategy
- Average winner/loser
- Monthly performance

## Backup

TradeNote data is stored in MongoDB. Regular backups recommended:

```bash
# Backup
docker exec tradenote-mongo mongodump --out /backup

# Restore
docker exec tradenote-mongo mongorestore /backup
```

## Troubleshooting

### Trades Not Appearing
1. Check TradeNote container is running: `docker ps`
2. Verify environment variables are set
3. Check logs: `docker logs tradenote`

### Connection Errors
1. Ensure TradeNote is accessible at configured URL
2. Verify app ID and master key are correct
3. Check network connectivity between services
```

##### Environment Variables
```env
# TradeNote Configuration
TRADENOTE_BASE_URL=http://localhost:8080
TRADENOTE_APP_ID=changeme
TRADENOTE_MASTER_KEY=changeme
```

## Summary

Step 0.7 adds professional trade journaling capabilities by integrating the open-source TradeNote project. This provides:

1. **Automatic Trade Logging** - Every trade (live and paper) is automatically logged
2. **Calendar Visualization** - See daily P&L at a glance with color-coded heatmap
3. **Tag-Based Analytics** - Analyze performance by strategy, mode, or custom tags
4. **Privacy-First** - Self-hosted solution keeps all data local
5. **Rich Analytics** - Win rate, average winner/loser, drawdown analysis

The integration is non-intrusive and adds significant value for serious traders who need to track and improve their performance over time.

