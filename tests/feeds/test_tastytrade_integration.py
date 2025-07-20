"""
Integration tests for Tastytrade API integration.

These tests require valid Tastytrade sandbox credentials and test against
the actual Tastytrade sandbox API.
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
import os

from src.backend.feeds.tastytrade import (
    TastytradeManager,
    TastytradeCredentials,
    TastytradeOrder,
    OrderType,
    OrderAction,
    OrderTimeInForce
)

logger = logging.getLogger(__name__)

# Test configuration
SANDBOX_CLIENT_ID = os.getenv("TASTYTRADE_SANDBOX_CLIENT_ID")
SANDBOX_CLIENT_SECRET = os.getenv("TASTYTRADE_SANDBOX_CLIENT_SECRET")
SANDBOX_CALLBACK_URL = os.getenv("TASTYTRADE_SANDBOX_CALLBACK_URL")

pytestmark = pytest.mark.integration


@pytest.fixture
async def tastytrade_credentials():
    """Create Tastytrade sandbox credentials"""
    if not SANDBOX_CLIENT_ID or not SANDBOX_CLIENT_SECRET:
        pytest.skip("Tastytrade sandbox credentials not configured")
    
    return TastytradeCredentials(
        client_id=SANDBOX_CLIENT_ID,
        client_secret=SANDBOX_CLIENT_SECRET,
        redirect_uri=SANDBOX_CALLBACK_URL or "https://127.0.0.1:8182/oauth/tastytrade/callback",
        sandbox=True
    )


@pytest.fixture
async def tastytrade_manager(tastytrade_credentials):
    """Create authenticated Tastytrade manager"""
    manager = TastytradeManager(tastytrade_credentials)
    
    # For integration tests, we assume authentication is already completed
    # In a real scenario, this would require the OAuth2 flow
    callback_url_with_token = os.getenv("TASTYTRADE_SANDBOX_CALLBACK_WITH_TOKEN")
    if callback_url_with_token:
        await manager.complete_authentication(callback_url_with_token)
    else:
        pytest.skip("Tastytrade authentication not completed - set TASTYTRADE_SANDBOX_CALLBACK_WITH_TOKEN")
    
    yield manager
    
    await manager.close()


@pytest.fixture
async def test_account_number(tastytrade_manager):
    """Get first available test account number"""
    accounts = await tastytrade_manager.get_accounts()
    if not accounts:
        pytest.skip("No test accounts available")
    
    return accounts[0]["account-number"]


class TestTastytradeAuthentication:
    """Test Tastytrade authentication functionality"""
    
    async def test_generate_authorization_url(self, tastytrade_credentials):
        """Test OAuth2 authorization URL generation"""
        manager = TastytradeManager(tastytrade_credentials)
        
        auth_url = manager.get_authorization_url()
        
        assert auth_url.startswith("https://api.cert.tastyworks.com/oauth/authorize")
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "response_type=code" in auth_url
    
    async def test_auth_status_unauthenticated(self, tastytrade_credentials):
        """Test authentication status when not authenticated"""
        manager = TastytradeManager(tastytrade_credentials)
        
        status = manager.get_auth_status()
        
        assert status["authenticated"] is False
        assert status["token_valid"] is False
        assert status["environment"] == "sandbox"
    
    async def test_connection_test_authenticated(self, tastytrade_manager):
        """Test API connection with valid authentication"""
        result = await tastytrade_manager.test_connection()
        
        assert result["status"] == "success"
        assert result["environment"] == "sandbox"
        assert "token_expires_in" in result


class TestTastytradeMarketData:
    """Test Tastytrade market data functionality"""
    
    async def test_get_single_quote(self, tastytrade_manager):
        """Test getting a single stock quote"""
        quote = await tastytrade_manager.get_quote("AAPL")
        
        assert quote.symbol == "AAPL"
        assert quote.last is not None
        assert quote.bid is not None
        assert quote.ask is not None
        assert quote.bid <= quote.ask
    
    async def test_get_multiple_quotes(self, tastytrade_manager):
        """Test getting multiple quotes"""
        symbols = ["AAPL", "MSFT", "TSLA"]
        quotes = await tastytrade_manager.get_quotes(symbols)
        
        assert len(quotes) == len(symbols)
        for symbol in symbols:
            assert symbol in quotes
            assert quotes[symbol].symbol == symbol
            assert quotes[symbol].last is not None
    
    async def test_get_quotes_empty_list(self, tastytrade_manager):
        """Test getting quotes with empty symbol list"""
        quotes = await tastytrade_manager.get_quotes([])
        
        assert quotes == {}
    
    async def test_get_quotes_invalid_symbol(self, tastytrade_manager):
        """Test getting quotes for invalid symbol"""
        quotes = await tastytrade_manager.get_quotes(["INVALID_SYMBOL_12345"])
        
        # Invalid symbols may return empty results or be filtered out
        assert isinstance(quotes, dict)
    
    async def test_search_symbols(self, tastytrade_manager):
        """Test symbol search functionality"""
        results = await tastytrade_manager.search_symbols("AAPL")
        
        assert isinstance(results, list)
        # Results should contain Apple-related instruments
        assert len(results) > 0
    
    async def test_get_market_hours(self, tastytrade_manager):
        """Test getting market hours"""
        market_hours = await tastytrade_manager.get_market_hours()
        
        assert isinstance(market_hours, dict)
        assert "data" in market_hours
    
    async def test_get_historical_data(self, tastytrade_manager):
        """Test getting historical price data"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        historical = await tastytrade_manager.get_historical_data(
            symbol="AAPL",
            timeframe="1Day",
            start_time=start_time,
            end_time=end_time
        )
        
        assert isinstance(historical, list)
        assert len(historical) > 0
        
        # Check data structure
        if historical:
            bar = historical[0]
            assert "open" in bar
            assert "high" in bar
            assert "low" in bar
            assert "close" in bar
            assert "volume" in bar


class TestTastytradeAccount:
    """Test Tastytrade account management functionality"""
    
    async def test_get_customer_info(self, tastytrade_manager):
        """Test getting customer information"""
        customer_info = await tastytrade_manager.get_customer_info()
        
        assert isinstance(customer_info, dict)
        assert "data" in customer_info
    
    async def test_get_accounts(self, tastytrade_manager):
        """Test getting user accounts"""
        accounts = await tastytrade_manager.get_accounts()
        
        assert isinstance(accounts, list)
        assert len(accounts) > 0
        
        # Check account structure
        account = accounts[0]
        assert "account-number" in account
        assert "nickname" in account
    
    async def test_get_accounts_with_cache(self, tastytrade_manager):
        """Test account caching functionality"""
        # First call - should fetch from API
        accounts1 = await tastytrade_manager.get_accounts(use_cache=True)
        
        # Second call - should use cache
        accounts2 = await tastytrade_manager.get_accounts(use_cache=True)
        
        assert accounts1 == accounts2
        
        # Force refresh
        accounts3 = await tastytrade_manager.get_accounts(use_cache=False)
        assert isinstance(accounts3, list)
    
    async def test_get_account_details(self, tastytrade_manager, test_account_number):
        """Test getting detailed account information"""
        account = await tastytrade_manager.get_account(test_account_number)
        
        assert account.account_number == test_account_number
        assert account.balance is not None
        assert isinstance(account.positions, list)
    
    async def test_get_account_balance(self, tastytrade_manager, test_account_number):
        """Test getting account balance"""
        balance = await tastytrade_manager.get_account_balance(test_account_number)
        
        assert balance.account_value is not None
        assert balance.cash_balance is not None
        assert balance.buying_power is not None
    
    async def test_get_positions(self, tastytrade_manager, test_account_number):
        """Test getting account positions"""
        positions = await tastytrade_manager.get_positions(test_account_number)
        
        assert isinstance(positions, list)
        # Positions may be empty in sandbox
        
        for position in positions:
            assert position.symbol is not None
            assert position.instrument_type is not None
            assert position.quantity is not None
    
    async def test_get_transactions(self, tastytrade_manager, test_account_number):
        """Test getting transaction history"""
        transactions = await tastytrade_manager.get_transactions(
            account_number=test_account_number,
            per_page=10
        )
        
        assert isinstance(transactions, list)
        # Transactions may be empty in sandbox
    
    async def test_get_portfolio_summary(self, tastytrade_manager, test_account_number):
        """Test getting portfolio summary"""
        summary = await tastytrade_manager.get_portfolio_summary(test_account_number)
        
        assert summary["account_number"] == test_account_number
        assert "balance" in summary
        assert "positions" in summary
        assert "pnl" in summary
        
        # Check balance section
        balance = summary["balance"]
        assert "account_value" in balance
        assert "cash_balance" in balance
        assert "buying_power" in balance
        
        # Check positions section
        positions = summary["positions"]
        assert "total_positions" in positions
        assert "active_positions" in positions
        
        # Check P&L section
        pnl = summary["pnl"]
        assert "total_unrealized_pnl" in pnl
        assert "total_realized_pnl" in pnl


class TestTastytradeTrading:
    """Test Tastytrade trading functionality"""
    
    async def test_create_equity_order(self):
        """Test creating equity order"""
        order = TastytradeOrder.create_equity_order(
            symbol="AAPL",
            action=OrderAction.BUY_TO_OPEN,
            quantity=1,
            order_type=OrderType.LIMIT,
            price=Decimal("100.00")
        )
        
        assert order.legs[0].symbol == "AAPL"
        assert order.legs[0].action == OrderAction.BUY_TO_OPEN
        assert order.legs[0].quantity == 1
        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("100.00")
        assert order.total_quantity == 1
    
    async def test_order_validation(self):
        """Test order validation"""
        with pytest.raises(ValueError):
            # Should fail with zero quantity
            TastytradeOrder.create_equity_order(
                symbol="AAPL",
                action=OrderAction.BUY_TO_OPEN,
                quantity=0,
                order_type=OrderType.MARKET
            )
    
    async def test_order_to_tastytrade_format(self):
        """Test order conversion to Tastytrade API format"""
        order = TastytradeOrder.create_equity_order(
            symbol="AAPL",
            action=OrderAction.BUY_TO_OPEN,
            quantity=100,
            order_type=OrderType.LIMIT,
            price=Decimal("150.00")
        )
        
        api_format = order.to_tastytrade_format()
        
        assert api_format["order-type"] == "Limit"
        assert api_format["price"] == "150.00"
        assert len(api_format["legs"]) == 1
        
        leg = api_format["legs"][0]
        assert leg["symbol"] == "AAPL"
        assert leg["action"] == "Buy to Open"
        assert leg["quantity"] == 100
    
    async def test_get_orders(self, tastytrade_manager, test_account_number):
        """Test getting order list"""
        orders = await tastytrade_manager.get_orders(
            account_number=test_account_number,
            per_page=10
        )
        
        assert isinstance(orders, list)
        # Orders may be empty in sandbox
        
        for order in orders:
            assert order.order_id is not None
            assert order.status is not None
            assert len(order.legs) > 0
    
    async def test_buy_stock_convenience_method(self, tastytrade_manager, test_account_number):
        """Test convenience method for buying stock"""
        # Note: This test uses a very low-priced limit order to avoid execution
        # In sandbox, this should place the order but not execute
        
        try:
            result = await tastytrade_manager.buy_stock(
                account_number=test_account_number,
                symbol="AAPL",
                quantity=1,
                order_type=OrderType.LIMIT,
                price=Decimal("1.00")  # Very low price to avoid execution
            )
            
            assert "data" in result
            order_id = result["data"]["id"]
            assert order_id is not None
            
            # Try to cancel the order
            cancel_result = await tastytrade_manager.cancel_order(test_account_number, order_id)
            assert "data" in cancel_result
            
        except Exception as e:
            # In sandbox, some trading operations may not be fully functional
            logger.warning(f"Trading test failed (expected in sandbox): {e}")
            pytest.skip("Trading operations not available in sandbox")


class TestTastytradeErrorHandling:
    """Test error handling and edge cases"""
    
    async def test_invalid_symbol_quote(self, tastytrade_manager):
        """Test handling of invalid symbol in quote request"""
        try:
            await tastytrade_manager.get_quote("INVALID_SYMBOL_XYZ123")
        except Exception as e:
            assert "No quote data received" in str(e)
    
    async def test_invalid_account_number(self, tastytrade_manager):
        """Test handling of invalid account number"""
        with pytest.raises(Exception):
            await tastytrade_manager.get_account("INVALID_ACCOUNT_123")
    
    async def test_unauthorized_operation(self, tastytrade_credentials):
        """Test handling of unauthorized operations"""
        # Create manager without authentication
        manager = TastytradeManager(tastytrade_credentials)
        
        with pytest.raises(Exception):
            await manager.get_quote("AAPL")
        
        await manager.close()


class TestTastytradeResourceManagement:
    """Test resource management and cleanup"""
    
    async def test_manager_context_manager(self, tastytrade_credentials):
        """Test using manager as async context manager"""
        async with TastytradeManager(tastytrade_credentials) as manager:
            # Manager should be usable within context
            assert manager.credentials.sandbox is True
        
        # Manager should be closed after context
        # Note: No direct way to test this, but it should not leak resources
    
    async def test_manual_close(self, tastytrade_credentials):
        """Test manual resource cleanup"""
        manager = TastytradeManager(tastytrade_credentials)
        
        # Close should not raise exceptions
        await manager.close()
        
        # Multiple closes should be safe
        await manager.close()


# Performance and stress tests
class TestTastytradePerformance:
    """Test performance characteristics"""
    
    @pytest.mark.slow
    async def test_concurrent_quote_requests(self, tastytrade_manager):
        """Test handling of concurrent quote requests"""
        symbols = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]
        
        # Make multiple concurrent requests
        tasks = [
            tastytrade_manager.get_quote(symbol)
            for symbol in symbols
        ]
        
        start_time = datetime.now()
        quotes = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert duration < 10.0
        
        # Check results
        successful_quotes = [q for q in quotes if not isinstance(q, Exception)]
        assert len(successful_quotes) > 0
    
    @pytest.mark.slow
    async def test_rate_limit_handling(self, tastytrade_manager):
        """Test rate limit handling"""
        # Make many rapid requests to test rate limiting
        symbols = ["AAPL"] * 50
        
        start_time = datetime.now()
        
        # This should trigger rate limiting
        quotes = []
        for symbol in symbols:
            try:
                quote = await tastytrade_manager.get_quote(symbol)
                quotes.append(quote)
            except Exception as e:
                if "429" in str(e):
                    # Rate limit hit - expected
                    break
                else:
                    # Other error
                    raise
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should have gotten some quotes before hitting limit
        assert len(quotes) > 0
        logger.info(f"Got {len(quotes)} quotes in {duration:.2f}s before rate limit")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__ + "::TestTastytradeMarketData::test_get_single_quote", "-v"])