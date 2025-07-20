# PRP: Unified TraderTerminal Dashboard with Backtesting & Containerization

## Metadata
- **Feature Name**: TraderTerminal Desktop Dashboard with Integrated Backtesting
- **Date**: July 2025
- **Confidence Score**: 9/10
- **Estimated Implementation Time**: 2-3 weeks for MVP (reduced from 3-4 weeks)
- **Primary Technologies**: Electron/Tauri, FastAPI, TradingView Premium Webhooks, Tradovate, Tastytrade, Charles Schwab
- **Target Platforms**: macOS (Apple Silicon) primary, Fedora 40+ secondary

## Executive Summary

This PRP defines the completion of the TraderTerminal ecosystem - an open-source Bloomberg Terminal alternative that provides institutional-grade trading capabilities at minimal cost ($41/month for additional data feeds). The project aims to create a professional desktop trading platform that rivals Bloomberg Terminal functionality while leveraging the user's existing premium services.

### Vision
Create a comprehensive trading workstation that provides:
- **Real-time market data** via existing Tradovate (futures) and Charles Schwab (stocks/options)
- **Professional charting** via TradingView Premium webhooks (user already has)
- **Automated trading** through TradingView alerts → TraderTerminal → Broker execution
- **Funded account management** for TopStep, Apex, and TradeDay accounts
- **News and economic data** aggregation from multiple sources
- **Risk management** with funded account rules and drawdown tracking
- **Quick deployment** on macOS with Fedora as secondary target

### User's Existing Infrastructure
- ✅ **TradingView Premium** - For charting and alert generation
- ✅ **Tradovate Account** - Futures data and execution
- ✅ **Charles Schwab/thinkorswim** - Stocks/options data and execution
- ✅ **NinjaTrader** - Alternative futures platform
- ✅ **Multiple Funded Accounts** - TopStep, Apex, TradeDay

## Current State (as of January 2025)

Based on development logs and code review, the project has made substantial progress:

### ✅ Completed Components

#### Backend Infrastructure (95% Complete)
- **DataHub Server** - FastAPI with TradingView UDF protocol, WebSocket streaming, mock data generation
- **Data Models** - Comprehensive Pydantic models with full type safety
- **Tradier Integration** - Complete API wrapper for equities/options with WebSocket support
- **Execution Engine** - Multi-layer risk management with webhook-driven alert processing
- **Kairos Automation** - Momentum and mean reversion strategies with SystemD integration
- **Backtesting Service** - Complete API with job queue management

#### Frontend Infrastructure (60% Complete)
- **Electron Application** - Main process with IPC bridge and macOS menu integration
- **Vue 3 Components** - TradingDashboard, TradingViewChart, Watchlist, OrderEntry, etc.
- **Missing**: Real data connections, funded account dashboards

#### DevOps Infrastructure (70% Complete)
- **GitHub Actions** - Comprehensive CI/CD pipeline
- **Containerization** - Containerfiles for all services, install scripts for Fedora/macOS
- **Missing**: Chronos container, TimescaleDB integration

### 🚧 Remaining Work (2-3 Weeks)

#### Critical Path Items (Revised for User's Setup)
1. **TradingView Webhook Integration** (Week 1 - Already has Premium)
2. **Tradovate Futures Integration** (Week 1 - CRITICAL for funded accounts)
3. **Tastytrade Integration** (Week 1 - Futures & options while waiting on other keys)
4. **TopstepX API Integration** (Week 1 - CRITICAL for TopStep execution)
5. **Charles Schwab Integration** (Week 2 - For stocks/options)
6. **Funded Account Risk Management** (Week 1 - CRITICAL)
7. **Desktop UI Polish** (Week 2 - Connect real feeds, add dashboards)
8. **Deployment & Packaging** (Week 3 - macOS primary)

## LLM Orchestration Directives

You are **Claude**, acting as an orchestrator for the TraderTerminal project.

### Goal
- Spawn **planning-agents** (OpenAI MCP · o3) to break work into milestones.  
- Spawn **file-analysis-agents** (Gemini MCP · 2.5 Pro) to scan code slices and return `{file, findings}` JSON.  
- Merge all agent outputs and continue execution.

### Allowed
✓ Calling both MCPs  
✓ Installing / running external tooling (brew, dnf, go install, podman, etc.)  
✓ Reading & writing repo files
✓ Container orchestration via Podman

### Forbidden
✗ Hallucinating paths or docs—mark `TODO:` if unsure  
✗ Pushing to protected branches without user confirmation
✗ Scraping TradingView sockets  
✗ Hard-coding API keys or credentials

### Warnings
- Double-check OS-specific steps (macOS vs Fedora)
- Label assumptions with `ASSUMPTION:` for auditability
- Respect TradingView license terms (display-only widgets)
- Ensure containers run rootless for security

## Detailed Implementation Plan

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

##### Task 0.1.4: Create Test Scripts
```bash
# Create scripts/test_webhook.sh
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

### Phase 1: Broker Integration Sprint (Week 1) - Detailed Breakdown

#### Step 1.1: Complete Tradovate Integration (Days 4-5)

##### Task 1.1.1: Create Comprehensive Test Suite
```python
# Create tests/test_tradovate.py
import pytest
from unittest.mock import AsyncMock, patch
from src.backend.feeds.tradovate import TradovateConnector

@pytest.fixture
def tradovate_config():
    return {
        "username": "test_user",
        "password": "test_pass",
        "app_id": "test_app",
        "demo": True
    }

@pytest.mark.asyncio
async def test_authentication(tradovate_config):
    """Test Tradovate authentication flow"""
    connector = TradovateConnector(**tradovate_config)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.json.return_value = {
            "accessToken": "test_token",
            "expirationTime": 3600
        }
        
        token = await connector.authenticate()
        assert token == "test_token"

@pytest.mark.asyncio
async def test_place_order_with_risk_checks(tradovate_config):
    """Test order placement with funded account rules"""
    # Implementation
```

##### Task 1.1.2: Implement Symbol Mapping
```python
# Create src/backend/feeds/tradovate/symbols.py
class TradovateSymbolMapper:
    """Map between TradingView and Tradovate symbols"""
    
    SYMBOL_MAP = {
        # TradingView -> Tradovate
        "ES": "ES",
        "NQ": "NQ",
        "YM": "YM",
        "RTY": "RTY",
        "GC": "GC",
        "SI": "SI",
        "CL": "CL",
        "NG": "NG",
        "ZB": "ZB",
        "ZN": "ZN",
        "ZC": "ZC",
        "ZS": "ZS",
        "ZW": "ZW"
    }
    
    CONTRACT_SPECS = {
        "ES": {"tick_size": 0.25, "tick_value": 12.50},
        "NQ": {"tick_size": 0.25, "tick_value": 5.00},
        "YM": {"tick_size": 1.0, "tick_value": 5.00},
        "RTY": {"tick_size": 0.10, "tick_value": 5.00},
        "GC": {"tick_size": 0.10, "tick_value": 10.00},
        "SI": {"tick_size": 0.005, "tick_value": 25.00},
        "CL": {"tick_size": 0.01, "tick_value": 10.00},
    }
    
    def get_active_contract(self, symbol: str) -> str:
        """Get current active contract month"""
        # Implementation to determine active month
```

##### Task 1.1.3: Create Integration Manager
```python
# Create src/backend/feeds/tradovate/manager.py
class TradovateManager:
    """High-level manager for all Tradovate operations"""
    
    def __init__(self, config: dict):
        self.auth = TradovateAuth(**config)
        self.market_data = TradovateMarketData(self.auth)
        self.orders = TradovateOrders(self.auth)
        self.account = TradovateAccount(self.auth)
        self.symbols = TradovateSymbolMapper()
        
    async def initialize(self):
        """Initialize connection and get account info"""
        await self.auth.get_access_token()
        self.accounts = await self.account.get_accounts()
        logger.info(f"Initialized Tradovate with {len(self.accounts)} accounts")
        
    async def execute_alert(self, alert: TradingViewAlert) -> Dict:
        """Execute a TradingView alert"""
        # Map symbol
        tradovate_symbol = self.symbols.get_active_contract(alert.symbol)
        
        # Get account
        account = self._select_account(alert.account_group)
        
        # Check funded account rules if applicable
        if self._is_funded_account(account):
            can_trade, reason = await self._check_funded_rules(account, alert)
            if not can_trade:
                return {"status": "rejected", "reason": reason}
        
        # Place order
        result = await self.orders.place_order(
            account_id=account["id"],
            symbol=tradovate_symbol,
            action="Buy" if alert.action == "buy" else "Sell",
            quantity=alert.quantity
        )
        
        return {"status": "success", "order": result}
```

#### Step 1.2: Charles Schwab Integration (Week 2, Days 1-2)

##### Task 1.2.1: Research Schwab API
```python
# Create src/backend/feeds/schwab/README.md
"""
Charles Schwab API Integration Notes
====================================

1. API Access Setup
   - Log into Schwab account
   - Visit: https://developer.schwab.com
   - Create application for personal use
   - OAuth2 flow required

2. Key Endpoints
   - Auth: POST /oauth/token
   - Quotes: GET /marketdata/{symbol}/quotes
   - Options: GET /marketdata/options/chains
   - Orders: POST /accounts/{accountId}/orders

3. Rate Limits
   - 120 requests per minute
   - 2 requests per second for quotes
"""
```

##### Task 1.2.2: Implement Schwab OAuth2
```python
# Create src/backend/feeds/schwab/auth.py
import httpx
from typing import Optional
import asyncio

class SchwabAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.refresh_token: Optional[str] = None
        self.access_token: Optional[str] = None
        
    async def get_authorization_url(self) -> str:
        """Get URL for user to authorize the app"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read write trade"
        }
        # Build authorization URL
        
    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for tokens"""
        # Implementation
        
    async def refresh_access_token(self) -> str:
        """Refresh access token using refresh token"""
        # Implementation
```

### Phase 2: UI Completion Sprint (Week 2) - Detailed Breakdown

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

### Phase 3: Integration Testing (Week 2, Day 5)

##### Task 3.1: Create End-to-End Test Flow
```python
# Create tests/e2e/test_trading_flow.py
import asyncio
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_trading_flow():
    """Test complete flow from TradingView alert to execution"""
    
    # Step 1: Start backend services
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Step 2: Send mock TradingView webhook
        webhook_data = {
            "symbol": "ES",
            "action": "buy",
            "quantity": 1,
            "strategy": "test_strategy",
            "account_group": "topstep"
        }
        
        response = await client.post(
            "/webhook/tradingview",
            json=webhook_data,
            headers={"X-Webhook-Signature": generate_test_signature(webhook_data)}
        )
        
    assert response.status_code == 200
        alert_id = response.json()["alert_id"]
        
        # Step 3: Verify order was placed
        await asyncio.sleep(2)  # Wait for processing
        
        order_response = await client.get(f"/api/v1/orders/{alert_id}")
        assert order_response.status_code == 200
        
        order = order_response.json()
        assert order["status"] in ["filled", "working"]
        assert order["symbol"] == "ES"
        assert order["quantity"] == 1
```

##### Task 3.2: Create Integration Test Suite
```bash
# Create scripts/integration_test.sh
#!/bin/bash

echo "Starting TraderTerminal Integration Tests"
echo "========================================"

# Start backend in test mode
export TRADING_ENV=test
export USE_MOCK_BROKERS=true

# Start services
cd src/backend
uv run uvicorn src.backend.datahub.server:app --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Run integration tests
cd ../..
pytest tests/e2e/ -v

# Cleanup
kill $BACKEND_PID

echo "Integration tests complete!"
```

### Phase 4: Deployment Preparation (Week 3)

##### Task 4.1: macOS Code Signing Preparation
```javascript
// Update electron-builder.yml
appId: com.grimmolf.traderterminal
productName: TraderTerminal
directories:
  output: dist
  buildResources: build

mac:
  category: public.app-category.finance
  icon: assets/icon.icns
  hardenedRuntime: true
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist
  gatekeeperAssess: false
  notarize:
    teamId: "YOUR_TEAM_ID"

dmg:
  contents:
    - x: 130
      y: 220
    - x: 410
      y: 220
      type: link
      path: /Applications
```

##### Task 4.2: Create Installation Scripts
```bash
# Create scripts/package_macos.sh
#!/bin/bash

echo "Building TraderTerminal for macOS"
echo "================================="

# Clean previous builds
rm -rf dist/

# Build backend
cd src/backend
uv build --wheel
cd ../..

# Build frontend
cd src/frontend
npm run build
cd ../..

# Package with Electron
cd src/frontend
npm run dist:mac

echo "Build complete! Check dist/ directory for .dmg file"
```

### Additional Support Tasks

##### Task S.1: Create Development Dashboard
```markdown
# Create docs/DEVELOPMENT_DASHBOARD.md

# TraderTerminal Development Dashboard

## Week 1 Checklist

### Day 1: Webhook Foundation
- [ ] Create webhook receiver endpoint
- [ ] Implement signature verification
- [ ] Create test scripts
- [ ] Test with curl/Postman

### Day 2: Tradovate Authentication
- [ ] Implement OAuth2 flow
- [ ] Create token management
- [ ] Test with demo account
- [ ] Handle token refresh

### Day 3: Tradovate Market Data
- [ ] Implement quote fetching
- [ ] Set up WebSocket streaming
- [ ] Create symbol mapping
- [ ] Test real-time updates

### Day 4: Order Execution
- [ ] Implement order placement
- [ ] Add funded account checks
- [ ] Create position management
- [ ] Test with paper trading

### Day 5: Integration Testing
- [ ] Complete E2E test suite
- [ ] Fix any issues found
- [ ] Document API endpoints
- [ ] Prepare for Week 2

## Progress Tracking

Use this to track daily progress:

```bash
# Day 1 Complete
git commit -m "feat: implement TradingView webhook receiver with HMAC verification"

# Day 2 Complete  
git commit -m "feat: add Tradovate OAuth2 authentication with token management"
```
```

##### Task S.2: Create Quick Start Guide
```markdown
# Create docs/QUICK_START.md

# TraderTerminal Quick Start Guide

## Prerequisites
- macOS (Apple Silicon)
- Python 3.11+
- Node.js 18+
- Tradovate account (demo or live)
- TradingView Premium account

## Day 1: Get Started

1. **Clone and Setup**
```bash
git clone https://github.com/grimmolf/trader-ops.git
cd trader-ops

# Backend setup
cd src/backend
python -m venv venv
source venv/bin/activate
pip install uv
uv sync

# Frontend setup
cd ../frontend
npm install
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Test Mock Data**
```bash
# Terminal 1: Start backend
cd src/backend
uv run uvicorn src.backend.datahub.server:app --reload

# Terminal 2: Start frontend
cd src/frontend
npm run dev
```

4. **Test Webhook**
```bash
# Terminal 3: Send test webhook
./scripts/test_webhook.sh
```

## Next Steps
- Get Tradovate API credentials
- Contact TopStep for API access
- Configure TradingView webhooks
```

This breakdown provides much more granular tasks that are:
1. **Smaller and more manageable** - Each task is 1-2 hours of work
2. **Clear dependencies** - Shows what needs to be done before each step
3. **Testable** - Each task has a clear completion criteria
4. **Documented** - Includes setup guides and progress tracking

The key improvements:
- Webhook setup broken into 4 subtasks (models, endpoint, security, testing)
- Tradovate broken into auth, market data, orders, and account management
- UI components broken into individual pieces (store, risk meter, selector, panel)
- Added support tasks for documentation and testing
- Created clear daily goals with checklists

Would you like me to break down any specific section even further?

