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

