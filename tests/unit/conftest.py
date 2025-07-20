"""
Test configuration for Tradovate integration tests.

Provides fixtures, mock data, and test utilities for comprehensive
testing of the Tradovate trading system.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import the classes we'll be testing
from src.backend.feeds.tradovate.auth import TradovateAuth, TradovateCredentials, TokenResponse
from src.backend.feeds.tradovate.market_data import TradovateMarketData, TradovateQuote
from src.backend.feeds.tradovate.orders import TradovateOrders, OrderType, TradovateOrderResponse
from src.backend.feeds.tradovate.account import TradovateAccount, TradovateAccountInfo, CashBalance, Position
from src.backend.feeds.tradovate.manager import TradovateManager


@pytest.fixture
def demo_credentials():
    """Demo trading credentials for testing"""
    return TradovateCredentials(
        username="demo_user",
        password="demo_password",
        api_key="demo_api_key",
        api_secret="demo_api_secret",
        demo=True
    )


@pytest.fixture
def live_credentials():
    """Live trading credentials for testing"""
    return TradovateCredentials(
        username="live_user", 
        password="live_password",
        api_key="live_api_key",
        api_secret="live_api_secret",
        demo=False
    )


@pytest.fixture
def valid_token_response():
    """Valid token response for authentication testing"""
    return TokenResponse(
        access_token="valid_access_token_12345",
        refresh_token="valid_refresh_token_67890",
        expires_in=3600,
        token_type="Bearer",
        scope="trading",
        user_id=12345,
        account_id=67890
    )


@pytest.fixture
def expired_token_response():
    """Expired token response for authentication testing"""
    expired_time = datetime.utcnow() - timedelta(hours=2)
    return TokenResponse(
        access_token="expired_access_token_12345",
        refresh_token="expired_refresh_token_67890", 
        expires_in=3600,
        token_type="Bearer",
        scope="trading",
        user_id=12345,
        account_id=67890,
        created_at=expired_time
    )


@pytest.fixture
def sample_account_info():
    """Sample account information for testing"""
    return TradovateAccountInfo(
        id=12345,
        name="Demo Futures Account",
        account_type="Futures",
        user_id=67890,
        risk_category="Standard",
        margin_account_type="Standard",
        clearing_house_id=1,
        risk_discount_rate=0.05,
        max_open_orders=50,
        max_positions=20,
        archived=False,
        auto_liquidation_threshold=0.8,
        daily_loss_limit=2000.0,
        margin_percentage=0.1
    )


@pytest.fixture
def sample_cash_balance():
    """Sample cash balance for testing"""
    return CashBalance(
        account_id=12345,
        cash_balance=50000.0,
        open_pl=1250.0,
        close_pl=750.0,
        day_pl=2000.0,
        margin_requirement=5000.0,
        buying_power=45000.0,
        currency="USD",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def sample_positions():
    """Sample positions for testing"""
    return [
        Position(
            account_id=12345,
            symbol="ES",
            product_type="Future",
            net_position=2,
            average_price=4450.50,
            market_value=178020.0,
            unrealized_pnl=500.0,
            realized_pnl=250.0,
            timestamp=datetime.utcnow()
        ),
        Position(
            account_id=12345,
            symbol="NQ", 
            product_type="Future",
            net_position=-1,
            average_price=15800.25,
            market_value=-63201.0,
            unrealized_pnl=-150.0,
            realized_pnl=75.0,
            timestamp=datetime.utcnow()
        )
    ]


@pytest.fixture
def sample_quotes():
    """Sample market quotes for testing"""
    return [
        TradovateQuote(
            symbol="ES",
            bid=4450.25,
            ask=4450.50,
            last=4450.50,
            volume=125000,
            high=4455.75,
            low=4445.00,
            change=5.25,
            change_percent=0.12,
            timestamp=datetime.utcnow()
        ),
        TradovateQuote(
            symbol="NQ",
            bid=15799.75,
            ask=15800.25,
            last=15800.00,
            volume=85000,
            high=15825.50,
            low=15775.25,
            change=-12.50,
            change_percent=-0.08,
            timestamp=datetime.utcnow()
        )
    ]


@pytest.fixture
def sample_order_response():
    """Sample order response for testing"""
    return TradovateOrderResponse(
        order_id=98765,
        status="Working",
        message="Order placed successfully",
        filled_quantity=0,
        remaining_quantity=1,
        average_fill_price=None,
        order_type="Market",
        symbol="ES",
        action="Buy",
        quantity=1,
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def sample_alert_data():
    """Sample TradingView alert data for testing"""
    return {
        "symbol": "ES",
        "action": "buy",
        "quantity": 1,
        "price": 4450.50,
        "order_type": "market",
        "account_group": "main",
        "strategy": "momentum_breakout",
        "timeframe": "5m",
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def funded_account_alert():
    """Sample funded account alert for testing"""
    return {
        "symbol": "NQ",
        "action": "sell", 
        "quantity": 1,
        "account_group": "topstep",
        "strategy": "mean_reversion",
        "timeframe": "15m",
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_http_response():
    """Mock HTTP response for API testing"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "success", "data": {}}
    return response


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for market data testing"""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


# Async test event loop configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mock_tradovate_auth(demo_credentials, valid_token_response):
    """Mock TradovateAuth for testing"""
    auth = TradovateAuth(demo_credentials)
    auth.tokens = valid_token_response
    auth._authenticated = True
    
    # Mock API calls
    auth.authenticate = AsyncMock(return_value=valid_token_response)
    auth.refresh_token = AsyncMock(return_value=valid_token_response)
    auth.test_connection = AsyncMock(return_value={"status": "success"})
    auth.get_access_token = AsyncMock(return_value="valid_access_token_12345")
    
    return auth


@pytest_asyncio.fixture
async def mock_tradovate_manager(demo_credentials, mock_tradovate_auth):
    """Mock TradovateManager for integration testing"""
    manager = TradovateManager(demo_credentials)
    
    # Replace auth with mock
    manager.auth = mock_tradovate_auth
    
    # Mock initialization
    manager._initialized = True
    manager._default_account_id = 12345
    manager._accounts = [
        TradovateAccountInfo(
            id=12345,
            name="Demo Account",
            account_type="Futures", 
            user_id=67890,
            risk_category="Standard",
            margin_account_type="Standard",
            clearing_house_id=1,
            archived=False
        )
    ]
    
    return manager


class MockSymbolMapping:
    """Mock symbol mapping for testing"""
    
    FUTURES_SYMBOLS = {
        "ES": {
            "name": "E-mini S&P 500",
            "exchange": "CME",
            "contract_size": 50,
            "tick_size": 0.25,
            "tick_value": 12.50,
            "session_times": "17:00-16:00 ET",
            "margin_requirement": 12000
        },
        "NQ": {
            "name": "E-mini NASDAQ-100", 
            "exchange": "CME",
            "contract_size": 20,
            "tick_size": 0.25,
            "tick_value": 5.00,
            "session_times": "17:00-16:00 ET",
            "margin_requirement": 16000
        },
        "YM": {
            "name": "E-mini Dow Jones",
            "exchange": "CBOT",
            "contract_size": 5,
            "tick_size": 1.00,
            "tick_value": 5.00,
            "session_times": "17:00-16:00 ET", 
            "margin_requirement": 8000
        },
        "RTY": {
            "name": "E-mini Russell 2000",
            "exchange": "CME",
            "contract_size": 50,
            "tick_size": 0.10,
            "tick_value": 5.00,
            "session_times": "17:00-16:00 ET",
            "margin_requirement": 7500
        }
    }
    
    @classmethod
    def get_symbol_info(cls, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        return cls.FUTURES_SYMBOLS.get(symbol.upper())
    
    @classmethod
    def is_valid_symbol(cls, symbol: str) -> bool:
        """Check if symbol is valid"""
        return symbol.upper() in cls.FUTURES_SYMBOLS
    
    @classmethod
    def get_all_symbols(cls) -> List[str]:
        """Get all available symbols"""
        return list(cls.FUTURES_SYMBOLS.keys())


@pytest.fixture
def mock_symbol_mapping():
    """Mock symbol mapping fixture"""
    return MockSymbolMapping()


# Test environment variables
@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing"""
    with patch.dict("os.environ", {
        "TRADOVATE_API_KEY": "test_api_key",
        "TRADOVATE_API_SECRET": "test_api_secret", 
        "TRADOVATE_USERNAME": "test_user",
        "TRADOVATE_PASSWORD": "test_password",
        "TRADOVATE_DEMO": "true"
    }):
        yield


# Global test utilities
class TestUtilities:
    """Utilities for testing Tradovate integration"""
    
    @staticmethod
    def create_mock_response(status_code: int = 200, data: Dict[str, Any] = None) -> MagicMock:
        """Create a mock HTTP response"""
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = data or {"status": "success"}
        return response
    
    @staticmethod
    def assert_order_response(response: TradovateOrderResponse, expected_symbol: str):
        """Assert order response properties"""
        assert response.symbol == expected_symbol
        assert response.order_id is not None
        assert response.status in ["Working", "Filled", "Rejected"]
        assert isinstance(response.timestamp, datetime)
    
    @staticmethod
    def assert_quote_response(quote: TradovateQuote, expected_symbol: str):
        """Assert quote response properties"""
        assert quote.symbol == expected_symbol
        assert quote.bid > 0
        assert quote.ask > 0
        assert quote.last > 0
        assert isinstance(quote.timestamp, datetime)


@pytest.fixture
def test_utils():
    """Test utilities fixture"""
    return TestUtilities()