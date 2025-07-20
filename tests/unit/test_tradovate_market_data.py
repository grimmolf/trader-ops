"""
Unit tests for Tradovate market data module.

Tests quote fetching, WebSocket streaming, and symbol management
for real-time market data functionality.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json
import asyncio

from src.backend.feeds.tradovate.market_data import (
    TradovateMarketData, TradovateQuote, MarketDataError
)


class TestTradovateQuote:
    """Test TradovateQuote model"""
    
    def test_create_quote(self, sample_quotes):
        """Test creating quote objects"""
        quote = sample_quotes[0]  # ES quote
        
        assert quote.symbol == "ES"
        assert quote.bid == 4450.25
        assert quote.ask == 4450.50
        assert quote.last == 4450.50
        assert quote.volume == 125000
        assert quote.change == 5.25
        assert quote.change_percent == 0.12
        assert isinstance(quote.timestamp, datetime)
    
    def test_quote_validation(self):
        """Test quote validation"""
        # Valid quote
        quote = TradovateQuote(
            symbol="ES",
            bid=100.0,
            ask=100.25,
            last=100.10,
            volume=1000,
            high=101.0,
            low=99.0,
            change=0.10,
            change_percent=0.1,
            timestamp=datetime.utcnow()
        )
        assert quote is not None
        
        # Invalid bid/ask spread
        with pytest.raises(ValueError):
            TradovateQuote(
                symbol="ES",
                bid=100.50,  # Bid higher than ask
                ask=100.25,
                last=100.10,
                volume=1000,
                high=101.0,
                low=99.0,
                change=0.10,
                change_percent=0.1,
                timestamp=datetime.utcnow()
            )
    
    def test_quote_serialization(self, sample_quotes):
        """Test quote serialization to dict"""
        quote = sample_quotes[0]
        quote_dict = quote.dict()
        
        assert quote_dict["symbol"] == "ES"
        assert quote_dict["bid"] == 4450.25
        assert quote_dict["ask"] == 4450.50
        assert "timestamp" in quote_dict
    
    def test_spread_calculation(self, sample_quotes):
        """Test bid-ask spread calculation"""
        quote = sample_quotes[0]
        spread = quote.ask - quote.bid
        assert spread == 0.25
        
        spread_bps = (spread / quote.last) * 10000
        assert spread_bps > 0


class TestTradovateMarketData:
    """Test TradovateMarketData class"""
    
    def test_market_data_initialization(self, mock_tradovate_auth):
        """Test market data initialization"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        assert market_data.auth == mock_tradovate_auth
        assert market_data._websocket is None
        assert market_data._subscriptions == set()
        assert not market_data._connected
    
    @pytest_asyncio.async_test
    async def test_get_quotes_success(self, mock_tradovate_auth):
        """Test successful quote fetching"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Mock API response
        mock_response = {
            "quotes": [
                {
                    "symbol": "ES",
                    "bid": 4450.25,
                    "ask": 4450.50,
                    "last": 4450.50,
                    "volume": 125000,
                    "high": 4455.75,
                    "low": 4445.00,
                    "change": 5.25,
                    "changePercent": 0.12,
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                {
                    "symbol": "NQ", 
                    "bid": 15799.75,
                    "ask": 15800.25,
                    "last": 15800.00,
                    "volume": 85000,
                    "high": 15825.50,
                    "low": 15775.25,
                    "change": -12.50,
                    "changePercent": -0.08,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request', 
                         return_value=mock_response):
            quotes = await market_data.get_quotes(["ES", "NQ"])
            
            assert len(quotes) == 2
            assert quotes[0].symbol == "ES"
            assert quotes[1].symbol == "NQ"
            assert quotes[0].bid == 4450.25
            assert quotes[1].ask == 15800.25
    
    @pytest_asyncio.async_test
    async def test_get_quotes_empty_symbols(self, mock_tradovate_auth):
        """Test quote fetching with empty symbol list"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        quotes = await market_data.get_quotes([])
        assert quotes == []
    
    @pytest_asyncio.async_test
    async def test_get_quotes_api_error(self, mock_tradovate_auth):
        """Test quote fetching with API error"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Mock API error
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=Exception("API Error")):
            with pytest.raises(MarketDataError):
                await market_data.get_quotes(["ES"])
    
    @pytest_asyncio.async_test
    async def test_get_single_quote(self, mock_tradovate_auth):
        """Test fetching single quote"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        mock_response = {
            "quotes": [{
                "symbol": "ES",
                "bid": 4450.25,
                "ask": 4450.50,
                "last": 4450.50,
                "volume": 125000,
                "high": 4455.75,
                "low": 4445.00,
                "change": 5.25,
                "changePercent": 0.12,
                "timestamp": "2024-01-01T12:00:00Z"
            }]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            quote = await market_data.get_single_quote("ES")
            
            assert quote is not None
            assert quote.symbol == "ES"
            assert quote.bid == 4450.25
    
    @pytest_asyncio.async_test
    async def test_get_single_quote_not_found(self, mock_tradovate_auth):
        """Test fetching single quote that doesn't exist"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        mock_response = {"quotes": []}
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            quote = await market_data.get_single_quote("INVALID")
            assert quote is None


class TestTradovateWebSocket:
    """Test WebSocket functionality"""
    
    @pytest_asyncio.async_test
    async def test_websocket_connection(self, mock_tradovate_auth, mock_websocket):
        """Test WebSocket connection establishment"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        with patch('websockets.connect', return_value=mock_websocket):
            await market_data.start_websocket_stream()
            
            assert market_data._connected is True
            assert market_data._websocket == mock_websocket
    
    @pytest_asyncio.async_test
    async def test_websocket_subscription(self, mock_tradovate_auth, mock_websocket):
        """Test WebSocket symbol subscription"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        market_data._websocket = mock_websocket
        market_data._connected = True
        
        await market_data.subscribe_quotes(["ES", "NQ"])
        
        # Should send subscription message
        mock_websocket.send.assert_called()
        assert "ES" in market_data._subscriptions
        assert "NQ" in market_data._subscriptions
    
    @pytest_asyncio.async_test
    async def test_websocket_unsubscription(self, mock_tradovate_auth, mock_websocket):
        """Test WebSocket symbol unsubscription"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        market_data._websocket = mock_websocket
        market_data._connected = True
        market_data._subscriptions.add("ES")
        market_data._subscriptions.add("NQ")
        
        await market_data.unsubscribe_quotes(["ES"])
        
        # Should send unsubscription message
        mock_websocket.send.assert_called()
        assert "ES" not in market_data._subscriptions
        assert "NQ" in market_data._subscriptions
    
    @pytest_asyncio.async_test
    async def test_websocket_message_handling(self, mock_tradovate_auth, mock_websocket):
        """Test WebSocket message processing"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        market_data._websocket = mock_websocket
        market_data._connected = True
        
        # Mock incoming quote message
        quote_message = {
            "type": "quote",
            "symbol": "ES",
            "bid": 4450.25,
            "ask": 4450.50,
            "last": 4450.50,
            "volume": 125000,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        mock_websocket.recv.return_value = json.dumps(quote_message)
        
        # Process one message
        message = await market_data._process_websocket_message()
        
        assert message["type"] == "quote"
        assert message["symbol"] == "ES"
    
    @pytest_asyncio.async_test
    async def test_websocket_connection_failure(self, mock_tradovate_auth):
        """Test WebSocket connection failure handling"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(MarketDataError):
                await market_data.start_websocket_stream()
            
            assert not market_data._connected
            assert market_data._websocket is None
    
    @pytest_asyncio.async_test
    async def test_websocket_reconnection(self, mock_tradovate_auth, mock_websocket):
        """Test WebSocket automatic reconnection"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        market_data._websocket = mock_websocket
        market_data._connected = True
        market_data._subscriptions.add("ES")
        
        # Simulate connection drop
        mock_websocket.recv.side_effect = Exception("Connection lost")
        
        with patch.object(market_data, 'start_websocket_stream') as mock_start:
            with patch.object(market_data, 'subscribe_quotes') as mock_subscribe:
                await market_data._handle_websocket_error(Exception("Connection lost"))
                
                # Should attempt reconnection
                mock_start.assert_called_once()
                mock_subscribe.assert_called_once_with(["ES"])
    
    @pytest_asyncio.async_test
    async def test_websocket_close(self, mock_tradovate_auth, mock_websocket):
        """Test WebSocket connection cleanup"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        market_data._websocket = mock_websocket
        market_data._connected = True
        
        await market_data.stop_websocket_stream()
        
        mock_websocket.close.assert_called_once()
        assert not market_data._connected
        assert market_data._websocket is None
        assert market_data._subscriptions == set()


class TestMarketDataUtilities:
    """Test market data utility functions"""
    
    @pytest_asyncio.async_test
    async def test_symbol_validation(self, mock_tradovate_auth):
        """Test symbol validation"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Valid futures symbols
        assert market_data._is_valid_symbol("ES")
        assert market_data._is_valid_symbol("NQ")
        assert market_data._is_valid_symbol("YM")
        assert market_data._is_valid_symbol("RTY")
        
        # Invalid symbols
        assert not market_data._is_valid_symbol("")
        assert not market_data._is_valid_symbol("INVALID")
        assert not market_data._is_valid_symbol("123")
    
    def test_quote_formatting(self, mock_tradovate_auth, sample_quotes):
        """Test quote data formatting"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        quote = sample_quotes[0]
        
        # Test formatting with different decimal places
        formatted_price = market_data._format_price(quote.last, "ES")
        assert isinstance(formatted_price, str)
        assert "." in formatted_price
    
    @pytest_asyncio.async_test
    async def test_batch_quote_processing(self, mock_tradovate_auth):
        """Test processing large batches of quotes"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Create mock response with many quotes
        large_symbols = [f"SYM{i}" for i in range(100)]
        mock_response = {
            "quotes": [
                {
                    "symbol": symbol,
                    "bid": 100.0 + i,
                    "ask": 100.25 + i,
                    "last": 100.10 + i,
                    "volume": 1000 + i,
                    "high": 101.0 + i,
                    "low": 99.0 + i,
                    "change": 0.10,
                    "changePercent": 0.1,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
                for i, symbol in enumerate(large_symbols)
            ]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            quotes = await market_data.get_quotes(large_symbols)
            
            assert len(quotes) == 100
            assert all(isinstance(q, TradovateQuote) for q in quotes)


class TestMarketDataIntegration:
    """Integration tests for market data functionality"""
    
    @pytest_asyncio.async_test
    async def test_full_market_data_workflow(self, mock_tradovate_auth, mock_websocket):
        """Test complete market data workflow"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Step 1: Get initial quotes
        mock_quotes_response = {
            "quotes": [{
                "symbol": "ES",
                "bid": 4450.25,
                "ask": 4450.50,
                "last": 4450.50,
                "volume": 125000,
                "high": 4455.75,
                "low": 4445.00,
                "change": 5.25,
                "changePercent": 0.12,
                "timestamp": "2024-01-01T12:00:00Z"
            }]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_quotes_response):
            quotes = await market_data.get_quotes(["ES"])
            assert len(quotes) == 1
            assert quotes[0].symbol == "ES"
        
        # Step 2: Start WebSocket stream
        with patch('websockets.connect', return_value=mock_websocket):
            await market_data.start_websocket_stream()
            assert market_data._connected
        
        # Step 3: Subscribe to symbols
        await market_data.subscribe_quotes(["ES", "NQ"])
        assert "ES" in market_data._subscriptions
        assert "NQ" in market_data._subscriptions
        
        # Step 4: Cleanup
        await market_data.stop_websocket_stream()
        assert not market_data._connected
    
    @pytest_asyncio.async_test
    async def test_concurrent_quote_requests(self, mock_tradovate_auth):
        """Test handling concurrent quote requests"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        mock_response = {
            "quotes": [{
                "symbol": "ES",
                "bid": 4450.25,
                "ask": 4450.50,
                "last": 4450.50,
                "volume": 125000,
                "high": 4455.75,
                "low": 4445.00,
                "change": 5.25,
                "changePercent": 0.12,
                "timestamp": "2024-01-01T12:00:00Z"
            }]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            # Make multiple concurrent requests
            quote_tasks = [
                market_data.get_single_quote("ES") for _ in range(5)
            ]
            
            quotes = await asyncio.gather(*quote_tasks)
            
            # All should succeed and return the same data
            assert all(q.symbol == "ES" for q in quotes)
            assert all(q.bid == 4450.25 for q in quotes)


class TestMarketDataErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest_asyncio.async_test
    async def test_malformed_quote_data(self, mock_tradovate_auth):
        """Test handling of malformed quote data"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Mock response with malformed data
        mock_response = {
            "quotes": [{
                "symbol": "ES",
                "bid": "invalid",  # Invalid bid price
                "ask": 4450.50,
                "last": 4450.50
            }]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            quotes = await market_data.get_quotes(["ES"])
            
            # Should handle gracefully and skip malformed quotes
            assert len(quotes) == 0
    
    @pytest_asyncio.async_test
    async def test_api_timeout_handling(self, mock_tradovate_auth):
        """Test API timeout handling"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=asyncio.TimeoutError("Request timeout")):
            with pytest.raises(MarketDataError):
                await market_data.get_quotes(["ES"])
    
    @pytest_asyncio.async_test
    async def test_rate_limiting_handling(self, mock_tradovate_auth):
        """Test rate limiting response handling"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Mock rate limit error (429)
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=rate_limit_error):
            with pytest.raises(MarketDataError):
                await market_data.get_quotes(["ES"])
    
    @pytest_asyncio.async_test
    async def test_websocket_subscription_without_connection(self, mock_tradovate_auth):
        """Test attempting subscription without WebSocket connection"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Try to subscribe without connecting first
        with pytest.raises(MarketDataError):
            await market_data.subscribe_quotes(["ES"])
    
    @pytest_asyncio.async_test
    async def test_close_without_connection(self, mock_tradovate_auth):
        """Test closing market data without active connection"""
        market_data = TradovateMarketData(mock_tradovate_auth)
        
        # Should handle gracefully
        await market_data.close()
        assert not market_data._connected
        assert market_data._websocket is None