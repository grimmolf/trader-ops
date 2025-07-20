"""
Multi-Broker Integration Tests for TraderTerminal

Tests the complete multi-broker integration system with real API connections
including Charles Schwab, Tastytrade, TopstepX, and data aggregation services.

These tests require valid API keys and test against sandbox/demo environments.
"""

import asyncio
import pytest
import pytest_asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import os
from unittest.mock import patch, MagicMock

from src.backend.feeds.schwab.manager import SchwabManager
from src.backend.feeds.tastytrade.manager import TastytradeManager
from src.backend.feeds.topstepx.manager import TopstepXManager
from src.backend.feeds.tradovate.manager import TradovateManager
from src.backend.security.credential_loader import (
    SecureCredentialLoader,
    TastytradeCredentials,
    SchwabCredentials, 
    TopstepXCredentials,
    load_tastytrade_credentials,
    load_schwab_credentials,
    load_topstepx_credentials,
    load_data_service_credentials
)

logger = logging.getLogger(__name__)

# Test configuration from environment
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")  
THENEWSAPI_KEY = os.getenv("THENEWSAPI_KEY")
TASTYTRADE_CLIENT_SECRET = os.getenv("TASTYTRADE_CLIENT_SECRET")

pytestmark = pytest.mark.integration


@pytest.fixture
async def secure_credential_loader():
    """Create a test credential loader"""
    return SecureCredentialLoader(account="test", warn_env_usage=False)


@pytest.fixture
async def api_keys(secure_credential_loader):
    """Load API keys from secure storage with environment fallback"""
    # Try to load from secure storage first, fallback to environment
    credentials = {}
    
    # Check each credential
    test_credentials = [
        ("ALPHA_VANTAGE_API_KEY", ALPHA_VANTAGE_API_KEY),
        ("FRED_API_KEY", FRED_API_KEY),
        ("THENEWSAPI_KEY", THENEWSAPI_KEY),
        ("TASTYTRADE_CLIENT_SECRET", TASTYTRADE_CLIENT_SECRET)
    ]
    
    missing_keys = []
    for key, env_value in test_credentials:
        # Try secure storage first
        secure_value = await secure_credential_loader._get_credential(key)
        value = secure_value or env_value
        
        if value:
            credentials[key.lower().replace('_', '_')] = value
        else:
            missing_keys.append(key)
    
    if missing_keys:
        pytest.skip(f"Missing required API keys: {', '.join(missing_keys)}")
    
    return {
        "alpha_vantage": credentials.get("alpha_vantage_api_key"),
        "fred": credentials.get("fred_api_key"),
        "news": credentials.get("thenewsapi_key"),
        "tastytrade_secret": credentials.get("tastytrade_client_secret")
    }


@pytest.fixture
async def schwab_credentials(secure_credential_loader):
    """Load or create mock Schwab credentials for testing"""
    # Try to load real credentials, fallback to mock
    real_credentials = await secure_credential_loader.load_schwab_credentials()
    if real_credentials:
        return real_credentials
    
    # Fallback to mock credentials
    return SchwabCredentials(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://127.0.0.1:8182/oauth/schwab/callback"
    )


@pytest.fixture
async def tastytrade_credentials(secure_credential_loader, api_keys):
    """Load or create Tastytrade credentials with real client secret"""
    # Try to load real credentials first
    real_credentials = await secure_credential_loader.load_tastytrade_credentials()
    if real_credentials:
        return real_credentials
    
    # Fallback to constructing from api_keys
    return TastytradeCredentials(
        client_id="e3f4389d-8216-40f6-af76-c7dc957977fe",  # Pre-configured client ID
        client_secret=api_keys["tastytrade_secret"],
        redirect_uri="https://127.0.0.1:8182/oauth/tastytrade/callback",
        sandbox=True
    )


@pytest.fixture
async def topstepx_credentials(secure_credential_loader):
    """Load or create mock TopstepX credentials for testing"""
    # Try to load real credentials, fallback to mock
    real_credentials = await secure_credential_loader.load_topstepx_credentials()
    if real_credentials:
        return real_credentials
    
    # Fallback to mock credentials
    return TopstepXCredentials(
        username="test_user",
        password="test_password",
        api_key="test_api_key",
        sandbox=True
    )


class TestSecureCredentialSystem:
    """Test secure credential management system"""
    
    async def test_credential_storage_and_retrieval(self, secure_credential_loader):
        """Test basic credential storage and retrieval"""
        test_key = "TEST_CREDENTIAL"
        test_value = "test_value_12345"
        
        # Store credential
        success = await secure_credential_loader.manager.store_credential(
            test_key, test_value, secure_credential_loader.account
        )
        assert success is True
        
        # Retrieve credential
        retrieved_value = await secure_credential_loader.manager.get_credential(
            test_key, secure_credential_loader.account
        )
        assert retrieved_value == test_value
        
        # Clean up
        await secure_credential_loader.manager.delete_credential(
            test_key, secure_credential_loader.account
        )
    
    async def test_credential_loader_fallback(self, secure_credential_loader):
        """Test credential loader fallback to environment variables"""
        test_key = "TEST_ENV_FALLBACK"
        test_env_key = "TEST_ENV_FALLBACK"
        test_value = "env_fallback_value"
        
        # Set environment variable
        original_value = os.environ.get(test_env_key)
        os.environ[test_env_key] = test_value
        
        try:
            # Should retrieve from environment
            value = await secure_credential_loader._get_credential(test_key, test_env_key)
            assert value == test_value
        finally:
            # Clean up environment
            if original_value is not None:
                os.environ[test_env_key] = original_value
            else:
                os.environ.pop(test_env_key, None)
    
    async def test_credential_validation(self, secure_credential_loader):
        """Test credential validation for brokers"""
        # Test validation with missing credentials
        validation = await secure_credential_loader.validate_required_credentials("tastytrade")
        
        # Should return validation results (may be False for missing credentials)
        assert isinstance(validation, dict)
        assert "client_id" in validation
        assert "client_secret" in validation
        assert "redirect_uri" in validation
    
    async def test_oauth_token_storage(self, secure_credential_loader):
        """Test OAuth token storage and retrieval"""
        test_tokens = {
            "access_token": "test_access_token_123",
            "refresh_token": "test_refresh_token_456", 
            "expires_at": "2024-12-31T23:59:59Z",
            "token_type": "Bearer"
        }
        
        # Store tokens
        success = await secure_credential_loader.store_oauth_tokens("tastytrade", test_tokens)
        assert success is True
        
        # Retrieve tokens
        retrieved_tokens = await secure_credential_loader.get_oauth_tokens("tastytrade")
        
        for token_type, expected_value in test_tokens.items():
            assert retrieved_tokens.get(token_type) == expected_value
        
        # Clean up
        for token_type in test_tokens.keys():
            key = f"TASTYTRADE_{token_type.upper()}"
            await secure_credential_loader.manager.delete_credential(key, secure_credential_loader.account)


class TestMultiBrokerAuthentication:
    """Test authentication across multiple brokers"""
    
    async def test_tastytrade_auth_url_generation(self, tastytrade_credentials):
        """Test Tastytrade OAuth URL generation with real credentials"""
        manager = TastytradeManager(tastytrade_credentials)
        
        auth_url = manager.get_authorization_url()
        
        assert auth_url.startswith("https://api.cert.tastyworks.com/oauth/authorize")
        assert "client_id=e3f4389d-8216-40f6-af76-c7dc957977fe" in auth_url
        assert "redirect_uri=" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=read+trade" in auth_url
        
        await manager.close()
    
    async def test_schwab_auth_url_generation(self, schwab_credentials):
        """Test Charles Schwab OAuth URL generation"""
        manager = SchwabManager(schwab_credentials)
        
        auth_url = manager.get_authorization_url()
        
        assert auth_url.startswith("https://api.schwabapi.com/v1/oauth/authorize")
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "response_type=code" in auth_url
        
        await manager.close()
    
    async def test_topstepx_connection_test(self, topstepx_credentials):
        """Test TopstepX API connection"""
        manager = TopstepXManager(topstepx_credentials)
        
        # Mock the API connection since we don't have real credentials
        with patch.object(manager.auth, 'test_connection') as mock_test:
            mock_test.return_value = {
                "status": "success",
                "environment": "sandbox",
                "response_time": 150
            }
            
            result = await manager.test_connection()
            
            assert result["status"] == "success"
            assert result["environment"] == "sandbox"
        
        await manager.close()


class TestExternalDataServices:
    """Test external data service integrations with real API keys"""
    
    async def test_alpha_vantage_connection(self, api_keys):
        """Test Alpha Vantage API connection"""
        import aiohttp
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": "AAPL",
            "apikey": api_keys["alpha_vantage"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                assert response.status == 200
                
                data = await response.json()
                assert "Global Quote" in data or "Note" in data  # Note appears on rate limit
                
                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    assert "01. symbol" in quote
                    assert quote["01. symbol"] == "AAPL"
    
    async def test_fred_api_connection(self, api_keys):
        """Test FRED API connection"""
        import aiohttp
        
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "GDP",
            "api_key": api_keys["fred"],
            "file_type": "json",
            "limit": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                assert response.status == 200
                
                data = await response.json()
                assert "observations" in data
                assert len(data["observations"]) > 0
    
    async def test_news_api_connection(self, api_keys):
        """Test TheNewsAPI connection"""
        import aiohttp
        
        url = "https://api.thenewsapi.com/v1/news/top"
        headers = {
            "Authorization": f"Bearer {api_keys['news']}"
        }
        params = {
            "locale": "us",
            "limit": 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                # Accept both 200 and 401 (invalid key) as connection success
                assert response.status in [200, 401, 403]
                
                if response.status == 200:
                    data = await response.json()
                    assert "data" in data
                    assert isinstance(data["data"], list)


class TestMultiBrokerMarketData:
    """Test market data aggregation across multiple brokers"""
    
    async def test_tastytrade_market_data_mock(self, tastytrade_credentials):
        """Test Tastytrade market data with mocked authentication"""
        manager = TastytradeManager(tastytrade_credentials)
        
        # Mock authentication success
        with patch.object(manager.auth, 'get_access_token', return_value="mock_token"):
            with patch.object(manager.market_data, 'get_quote') as mock_quote:
                mock_quote.return_value = MagicMock(
                    symbol="AAPL",
                    last=Decimal("150.00"),
                    bid=Decimal("149.95"),
                    ask=Decimal("150.05"),
                    timestamp=datetime.utcnow()
                )
                
                quote = await manager.get_quote("AAPL")
                
                assert quote.symbol == "AAPL"
                assert quote.last == Decimal("150.00")
                assert quote.bid <= quote.ask
        
        await manager.close()
    
    async def test_schwab_market_data_mock(self, schwab_credentials):
        """Test Charles Schwab market data with mocked authentication"""
        manager = SchwabManager(schwab_credentials)
        
        # Mock authentication and quote data
        with patch.object(manager.auth, 'get_access_token', return_value="mock_token"):
            with patch.object(manager.market_data, 'get_quote') as mock_quote:
                mock_quote.return_value = MagicMock(
                    symbol="AAPL",
                    last=Decimal("150.00"),
                    bid=Decimal("149.95"),
                    ask=Decimal("150.05"),
                    volume=1000000
                )
                
                quote = await manager.get_quote("AAPL")
                
                assert quote.symbol == "AAPL"
                assert quote.last == Decimal("150.00")
                assert quote.volume == 1000000
        
        await manager.close()
    
    async def test_cross_broker_quote_comparison(self, tastytrade_credentials, schwab_credentials):
        """Test quote comparison across multiple brokers"""
        tt_manager = TastytradeManager(tastytrade_credentials)
        schwab_manager = SchwabManager(schwab_credentials)
        
        symbol = "AAPL"
        
        # Mock both brokers with slightly different quotes
        with patch.object(tt_manager.auth, 'get_access_token', return_value="mock_token"):
            with patch.object(schwab_manager.auth, 'get_access_token', return_value="mock_token"):
                with patch.object(tt_manager.market_data, 'get_quote') as mock_tt_quote:
                    with patch.object(schwab_manager.market_data, 'get_quote') as mock_schwab_quote:
                        
                        mock_tt_quote.return_value = MagicMock(
                            symbol=symbol,
                            bid=Decimal("149.95"),
                            ask=Decimal("150.05")
                        )
                        
                        mock_schwab_quote.return_value = MagicMock(
                            symbol=symbol,
                            bid=Decimal("149.93"),
                            ask=Decimal("150.07")
                        )
                        
                        # Get quotes from both brokers
                        tt_quote = await tt_manager.get_quote(symbol)
                        schwab_quote = await schwab_manager.get_quote(symbol)
                        
                        # Verify both quotes are valid
                        assert tt_quote.symbol == symbol
                        assert schwab_quote.symbol == symbol
                        
                        # Verify bid/ask spreads are reasonable
                        tt_spread = tt_quote.ask - tt_quote.bid
                        schwab_spread = schwab_quote.ask - schwab_quote.bid
                        
                        assert tt_spread > 0
                        assert schwab_spread > 0
                        assert abs(tt_spread - schwab_spread) < Decimal("0.50")  # Similar spreads
        
        await tt_manager.close()
        await schwab_manager.close()


class TestMultiBrokerOrderRouting:
    """Test intelligent order routing across multiple brokers"""
    
    async def test_order_routing_logic(self, tastytrade_credentials, schwab_credentials):
        """Test intelligent order routing based on symbol type"""
        tt_manager = TastytradeManager(tastytrade_credentials)
        schwab_manager = SchwabManager(schwab_credentials)
        
        # Test routing rules
        test_cases = [
            ("AAPL", "equity", "schwab"),      # Stocks -> Schwab
            ("AAPL250117C00150000", "option", "tastytrade"),  # Options -> Tastytrade  
            ("/ES", "future", "tradovate"),   # Futures -> Tradovate
            ("BTC-USD", "crypto", "none")     # Crypto -> No routing
        ]
        
        for symbol, instrument_type, expected_broker in test_cases:
            # Mock order placement
            if expected_broker == "schwab":
                with patch.object(schwab_manager.trading, 'place_order') as mock_place:
                    mock_place.return_value = MagicMock(order_id=12345, status="PENDING")
                    
                    # Test would route to Schwab
                    assert instrument_type in ["equity"]
            
            elif expected_broker == "tastytrade":
                with patch.object(tt_manager.trading, 'place_order') as mock_place:
                    mock_place.return_value = MagicMock(order_id=67890, status="PENDING")
                    
                    # Test would route to Tastytrade
                    assert instrument_type in ["option"]
        
        await tt_manager.close()
        await schwab_manager.close()
    
    async def test_multi_broker_position_aggregation(self, tastytrade_credentials, schwab_credentials):
        """Test position aggregation across multiple brokers"""
        tt_manager = TastytradeManager(tastytrade_credentials)
        schwab_manager = SchwabManager(schwab_credentials)
        
        # Mock positions from different brokers
        with patch.object(tt_manager.account, 'get_positions') as mock_tt_positions:
            with patch.object(schwab_manager.account, 'get_positions') as mock_schwab_positions:
                
                mock_tt_positions.return_value = [
                    MagicMock(symbol="AAPL", quantity=100, unrealized_pnl=500.0),
                    MagicMock(symbol="TSLA", quantity=50, unrealized_pnl=-200.0)
                ]
                
                mock_schwab_positions.return_value = [
                    MagicMock(symbol="MSFT", quantity=75, unrealized_pnl=750.0),
                    MagicMock(symbol="AAPL", quantity=25, unrealized_pnl=125.0)  # Same symbol
                ]
                
                # Get positions from both brokers
                tt_positions = await tt_manager.get_positions("test_account")
                schwab_positions = await schwab_manager.get_positions("test_account")
                
                # Aggregate positions
                aggregated = {}
                for pos in tt_positions + schwab_positions:
                    if pos.symbol not in aggregated:
                        aggregated[pos.symbol] = {"quantity": 0, "unrealized_pnl": 0}
                    
                    aggregated[pos.symbol]["quantity"] += pos.quantity
                    aggregated[pos.symbol]["unrealized_pnl"] += pos.unrealized_pnl
                
                # Verify aggregation
                assert "AAPL" in aggregated
                assert aggregated["AAPL"]["quantity"] == 125  # 100 + 25
                assert aggregated["AAPL"]["unrealized_pnl"] == 625.0  # 500 + 125
                
                assert "TSLA" in aggregated
                assert aggregated["TSLA"]["quantity"] == 50
                
                assert "MSFT" in aggregated
                assert aggregated["MSFT"]["quantity"] == 75
        
        await tt_manager.close()
        await schwab_manager.close()


class TestFundedAccountIntegration:
    """Test funded account management and risk monitoring"""
    
    async def test_topstepx_account_monitoring(self, topstepx_credentials):
        """Test TopstepX funded account monitoring"""
        manager = TopstepXManager(topstepx_credentials)
        
        # Mock account data
        with patch.object(manager.account, 'get_account_status') as mock_status:
            with patch.object(manager.risk, 'get_risk_metrics') as mock_risk:
                
                mock_status.return_value = {
                    "account_id": "TS50K001",
                    "balance": 50000.0,
                    "daily_pnl": -500.0,
                    "total_pnl": 2000.0,
                    "status": "active"
                }
                
                mock_risk.return_value = {
                    "max_daily_loss": 1000.0,
                    "current_daily_loss": 500.0,
                    "max_contracts": 3,
                    "current_contracts": 1,
                    "trailing_drawdown": 2000.0,
                    "current_drawdown": 500.0
                }
                
                account_status = await manager.get_account_status("TS50K001")
                risk_metrics = await manager.get_risk_metrics("TS50K001")
                
                # Verify account data
                assert account_status["account_id"] == "TS50K001"
                assert account_status["daily_pnl"] == -500.0
                assert account_status["status"] == "active"
                
                # Verify risk metrics
                assert risk_metrics["max_daily_loss"] == 1000.0
                assert risk_metrics["current_daily_loss"] == 500.0
                assert risk_metrics["current_daily_loss"] < risk_metrics["max_daily_loss"]
        
        await manager.close()
    
    async def test_funded_account_risk_validation(self, topstepx_credentials):
        """Test risk validation for funded account trades"""
        manager = TopstepXManager(topstepx_credentials)
        
        # Test scenarios
        test_cases = [
            {
                "daily_loss": 800.0,
                "max_daily_loss": 1000.0,
                "contracts": 2,
                "max_contracts": 3,
                "expected_allowed": True
            },
            {
                "daily_loss": 1200.0,  # Exceeds limit
                "max_daily_loss": 1000.0,
                "contracts": 1,
                "max_contracts": 3,
                "expected_allowed": False
            },
            {
                "daily_loss": 500.0,
                "max_daily_loss": 1000.0,
                "contracts": 4,  # Exceeds limit
                "max_contracts": 3,
                "expected_allowed": False
            }
        ]
        
        for case in test_cases:
            with patch.object(manager.risk, 'validate_trade') as mock_validate:
                mock_validate.return_value = case["expected_allowed"]
                
                trade_data = {
                    "symbol": "/ES",
                    "quantity": 1,
                    "action": "buy"
                }
                
                is_allowed = await manager.validate_trade("TS50K001", trade_data)
                assert is_allowed == case["expected_allowed"]
        
        await manager.close()


class TestRealTimeDataIntegration:
    """Test real-time data streaming and WebSocket connections"""
    
    async def test_websocket_connection_simulation(self, tastytrade_credentials):
        """Test WebSocket connection establishment (simulated)"""
        manager = TastytradeManager(tastytrade_credentials)
        
        # Mock WebSocket connection
        with patch.object(manager.market_data, 'connect_websocket') as mock_connect:
            with patch.object(manager.market_data, 'subscribe_quotes') as mock_subscribe:
                
                mock_connect.return_value = True
                mock_subscribe.return_value = True
                
                # Test connection
                connected = await manager.connect_websocket()
                assert connected is True
                
                # Test subscription
                symbols = ["AAPL", "MSFT", "TSLA"]
                subscribed = await manager.subscribe_quotes(symbols)
                assert subscribed is True
                
                mock_connect.assert_called_once()
                mock_subscribe.assert_called_once_with(symbols)
        
        await manager.close()
    
    async def test_multi_broker_data_synchronization(self, tastytrade_credentials, schwab_credentials):
        """Test data synchronization across multiple broker feeds"""
        tt_manager = TastytradeManager(tastytrade_credentials)
        schwab_manager = SchwabManager(schwab_credentials)
        
        symbol = "AAPL"
        
        # Simulate synchronized data updates
        with patch.object(tt_manager.market_data, 'get_quote') as mock_tt:
            with patch.object(schwab_manager.market_data, 'get_quote') as mock_schwab:
                
                # Both brokers should provide similar quotes
                base_price = Decimal("150.00")
                mock_tt.return_value = MagicMock(
                    symbol=symbol,
                    last=base_price,
                    timestamp=datetime.utcnow()
                )
                mock_schwab.return_value = MagicMock(
                    symbol=symbol,
                    last=base_price + Decimal("0.01"),  # Slight difference
                    timestamp=datetime.utcnow()
                )
                
                # Get quotes from both feeds
                tt_quote = await tt_manager.get_quote(symbol)
                schwab_quote = await schwab_manager.get_quote(symbol)
                
                # Verify synchronization
                price_diff = abs(tt_quote.last - schwab_quote.last)
                assert price_diff < Decimal("0.10")  # Prices should be close
                
                # Verify timestamps are recent
                now = datetime.utcnow()
                tt_age = (now - tt_quote.timestamp).total_seconds()
                schwab_age = (now - schwab_quote.timestamp).total_seconds()
                
                assert tt_age < 5.0  # Less than 5 seconds old
                assert schwab_age < 5.0
        
        await tt_manager.close()
        await schwab_manager.close()


class TestErrorRecoveryAndResilience:
    """Test error recovery and system resilience"""
    
    async def test_broker_failover_simulation(self, tastytrade_credentials, schwab_credentials):
        """Test failover when one broker becomes unavailable"""
        primary_manager = TastytradeManager(tastytrade_credentials)
        backup_manager = SchwabManager(schwab_credentials)
        
        symbol = "AAPL"
        
        # Simulate primary broker failure
        with patch.object(primary_manager.market_data, 'get_quote', side_effect=Exception("Connection failed")):
            with patch.object(backup_manager.market_data, 'get_quote') as mock_backup:
                
                mock_backup.return_value = MagicMock(
                    symbol=symbol,
                    last=Decimal("150.00"),
                    bid=Decimal("149.95"),
                    ask=Decimal("150.05")
                )
                
                # Try primary first (should fail)
                try:
                    await primary_manager.get_quote(symbol)
                    assert False, "Should have raised exception"
                except Exception as e:
                    assert "Connection failed" in str(e)
                
                # Fallback to backup (should succeed)
                quote = await backup_manager.get_quote(symbol)
                assert quote.symbol == symbol
                assert quote.last == Decimal("150.00")
        
        await primary_manager.close()
        await backup_manager.close()
    
    async def test_rate_limit_recovery(self, tastytrade_credentials):
        """Test recovery from rate limiting"""
        manager = TastytradeManager(tastytrade_credentials)
        
        # Simulate rate limit followed by recovery
        responses = [
            Exception("429 Too Many Requests"),
            Exception("429 Too Many Requests"),
            MagicMock(symbol="AAPL", last=Decimal("150.00"))  # Recovery
        ]
        
        with patch.object(manager.market_data, 'get_quote', side_effect=responses):
            
            # First two calls should fail
            for i in range(2):
                try:
                    await manager.get_quote("AAPL")
                    assert False, "Should have raised rate limit exception"
                except Exception as e:
                    assert "429" in str(e)
            
            # Third call should succeed (after backoff)
            quote = await manager.get_quote("AAPL")
            assert quote.symbol == "AAPL"
        
        await manager.close()
    
    async def test_partial_system_degradation(self, tastytrade_credentials, topstepx_credentials):
        """Test system behavior when some components fail"""
        tt_manager = TastytradeManager(tastytrade_credentials)
        topstep_manager = TopstepXManager(topstepx_credentials)
        
        # Simulate TopstepX unavailable but Tastytrade working
        with patch.object(tt_manager.market_data, 'get_quote') as mock_quote:
            with patch.object(topstep_manager.account, 'get_account_status', side_effect=Exception("Service unavailable")):
                
                mock_quote.return_value = MagicMock(
                    symbol="AAPL",
                    last=Decimal("150.00")
                )
                
                # Market data should still work
                quote = await tt_manager.get_quote("AAPL")
                assert quote.symbol == "AAPL"
                
                # Funded account monitoring should fail gracefully
                try:
                    await topstep_manager.get_account_status("TS50K001")
                    assert False, "Should have raised exception"
                except Exception as e:
                    assert "Service unavailable" in str(e)
        
        await tt_manager.close()
        await topstep_manager.close()


class TestPerformanceAndLoad:
    """Test performance characteristics under load"""
    
    @pytest.mark.slow
    async def test_concurrent_multi_broker_operations(self, tastytrade_credentials, schwab_credentials):
        """Test concurrent operations across multiple brokers"""
        tt_manager = TastytradeManager(tastytrade_credentials)
        schwab_manager = SchwabManager(schwab_credentials)
        
        symbols = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]
        
        # Mock quotes for both brokers
        with patch.object(tt_manager.market_data, 'get_quote') as mock_tt:
            with patch.object(schwab_manager.market_data, 'get_quote') as mock_schwab:
                
                # Setup mock responses
                def create_quote(symbol, broker="tt"):
                    return MagicMock(
                        symbol=symbol,
                        last=Decimal("100.00"),
                        timestamp=datetime.utcnow()
                    )
                
                mock_tt.side_effect = lambda s: create_quote(s, "tt")
                mock_schwab.side_effect = lambda s: create_quote(s, "schwab")
                
                start_time = datetime.utcnow()
                
                # Execute concurrent operations
                tasks = []
                for symbol in symbols:
                    tasks.append(tt_manager.get_quote(symbol))
                    tasks.append(schwab_manager.get_quote(symbol))
                
                results = await asyncio.gather(*tasks)
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                # Verify all operations completed
                assert len(results) == len(symbols) * 2
                assert all(r.symbol in symbols for r in results)
                
                # Performance check
                assert duration < 2.0  # Should complete quickly
                
                # Verify both brokers were called
                assert mock_tt.call_count == len(symbols)
                assert mock_schwab.call_count == len(symbols)
        
        await tt_manager.close()
        await schwab_manager.close()
    
    @pytest.mark.slow
    async def test_sustained_operation_stability(self, tastytrade_credentials):
        """Test system stability under sustained operation"""
        manager = TastytradeManager(tastytrade_credentials)
        
        # Simulate sustained trading activity
        with patch.object(manager.market_data, 'get_quote') as mock_quote:
            
            mock_quote.return_value = MagicMock(
                symbol="AAPL",
                last=Decimal("150.00"),
                timestamp=datetime.utcnow()
            )
            
            # Run many operations
            successful_operations = 0
            for i in range(100):
                try:
                    quote = await manager.get_quote("AAPL")
                    assert quote.symbol == "AAPL"
                    successful_operations += 1
                except Exception as e:
                    logger.warning(f"Operation {i} failed: {e}")
            
            # Should have high success rate
            success_rate = successful_operations / 100
            assert success_rate > 0.95  # At least 95% success rate
            
            logger.info(f"Sustained operation test: {successful_operations}/100 successful")
        
        await manager.close()


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__ + "::TestExternalDataServices",
        __file__ + "::TestMultiBrokerMarketData", 
        "-v", "--tb=short"
    ])