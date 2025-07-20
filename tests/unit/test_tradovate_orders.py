"""
Unit tests for Tradovate orders module.

Tests order placement, execution, cancellation, and status tracking
for all supported order types and market conditions.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

from src.backend.feeds.tradovate.orders import (
    TradovateOrders, OrderType, TradovateOrderResponse, OrderError
)


class TestOrderType:
    """Test OrderType enumeration"""
    
    def test_order_types(self):
        """Test all order type values"""
        assert OrderType.MARKET.value == "Market"
        assert OrderType.LIMIT.value == "Limit"
        assert OrderType.STOP.value == "Stop"
        assert OrderType.STOP_LIMIT.value == "StopLimit"
    
    def test_order_type_from_string(self):
        """Test creating OrderType from string"""
        assert OrderType("Market") == OrderType.MARKET
        assert OrderType("Limit") == OrderType.LIMIT
        assert OrderType("Stop") == OrderType.STOP
        assert OrderType("StopLimit") == OrderType.STOP_LIMIT


class TestTradovateOrderResponse:
    """Test TradovateOrderResponse model"""
    
    def test_create_order_response(self, sample_order_response):
        """Test creating order response"""
        assert sample_order_response.order_id == 98765
        assert sample_order_response.status == "Working"
        assert sample_order_response.symbol == "ES"
        assert sample_order_response.action == "Buy"
        assert sample_order_response.quantity == 1
        assert isinstance(sample_order_response.timestamp, datetime)
    
    def test_order_response_properties(self, sample_order_response):
        """Test order response computed properties"""
        # Working order
        assert sample_order_response.is_working
        assert not sample_order_response.is_filled
        assert not sample_order_response.is_rejected
        assert not sample_order_response.is_cancelled
        
        # Filled order
        filled_response = TradovateOrderResponse(
            order_id=98765,
            status="Filled",
            message="Order filled",
            filled_quantity=1,
            remaining_quantity=0,
            average_fill_price=4450.50,
            order_type="Market",
            symbol="ES",
            action="Buy",
            quantity=1,
            timestamp=datetime.utcnow()
        )
        
        assert not filled_response.is_working
        assert filled_response.is_filled
        assert not filled_response.is_rejected
        assert not filled_response.is_cancelled
    
    def test_order_response_serialization(self, sample_order_response):
        """Test order response serialization"""
        response_dict = sample_order_response.dict()
        
        assert response_dict["order_id"] == 98765
        assert response_dict["status"] == "Working"
        assert response_dict["symbol"] == "ES"
        assert "timestamp" in response_dict


class TestTradovateOrders:
    """Test TradovateOrders class"""
    
    def test_orders_initialization(self, mock_tradovate_auth):
        """Test orders initialization"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        assert orders.auth == mock_tradovate_auth
        assert orders._active_orders == {}
    
    @pytest_asyncio.async_test
    async def test_place_market_order_buy(self, mock_tradovate_auth):
        """Test placing market buy order"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Mock API response
        mock_response = {
            "orderId": 98765,
            "orderStatus": "Working",
            "message": "Order placed successfully",
            "filledQty": 0,
            "remainingQty": 1,
            "orderType": "Market",
            "symbol": "ES",
            "action": "Buy",
            "qty": 1,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.MARKET
            )
            
            assert result.order_id == 98765
            assert result.status == "Working"
            assert result.symbol == "ES"
            assert result.action == "Buy"
            assert result.quantity == 1
    
    @pytest_asyncio.async_test
    async def test_place_limit_order_sell(self, mock_tradovate_auth):
        """Test placing limit sell order"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": 98766,
            "orderStatus": "Working",
            "message": "Limit order placed",
            "filledQty": 0,
            "remainingQty": 2,
            "orderType": "Limit",
            "symbol": "NQ", 
            "action": "Sell",
            "qty": 2,
            "limitPrice": 15800.00,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.place_order(
                account_id=12345,
                symbol="NQ",
                action="Sell",
                quantity=2,
                order_type=OrderType.LIMIT,
                price=15800.00
            )
            
            assert result.order_id == 98766
            assert result.symbol == "NQ"
            assert result.action == "Sell"
            assert result.quantity == 2
    
    @pytest_asyncio.async_test
    async def test_place_stop_order(self, mock_tradovate_auth):
        """Test placing stop order"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": 98767,
            "orderStatus": "Working",
            "message": "Stop order placed",
            "filledQty": 0,
            "remainingQty": 1,
            "orderType": "Stop",
            "symbol": "ES",
            "action": "Sell",
            "qty": 1,
            "stopPrice": 4440.00,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Sell",
                quantity=1,
                order_type=OrderType.STOP,
                stop_price=4440.00
            )
            
            assert result.order_id == 98767
            assert result.order_type == "Stop"
    
    @pytest_asyncio.async_test
    async def test_place_stop_limit_order(self, mock_tradovate_auth):
        """Test placing stop-limit order"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": 98768,
            "orderStatus": "Working",
            "message": "Stop-limit order placed",
            "filledQty": 0,
            "remainingQty": 1,
            "orderType": "StopLimit",
            "symbol": "ES",
            "action": "Buy",
            "qty": 1,
            "limitPrice": 4450.00,
            "stopPrice": 4445.00,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.STOP_LIMIT,
                price=4450.00,
                stop_price=4445.00
            )
            
            assert result.order_id == 98768
            assert result.order_type == "StopLimit"
    
    @pytest_asyncio.async_test
    async def test_cancel_order(self, mock_tradovate_auth):
        """Test canceling order"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": 98765,
            "orderStatus": "Cancelled",
            "message": "Order cancelled successfully",
            "timestamp": "2024-01-01T12:05:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.cancel_order(order_id=98765)
            
            assert result["orderId"] == 98765
            assert result["orderStatus"] == "Cancelled"
    
    @pytest_asyncio.async_test
    async def test_get_order_status(self, mock_tradovate_auth):
        """Test getting order status"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": 98765,
            "orderStatus": "Filled",
            "filledQty": 1,
            "remainingQty": 0,
            "avgFillPrice": 4450.50,
            "symbol": "ES",
            "action": "Buy",
            "qty": 1,
            "timestamp": "2024-01-01T12:03:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.get_order_status(order_id=98765)
            
            assert result.order_id == 98765
            assert result.status == "Filled"
            assert result.filled_quantity == 1
            assert result.average_fill_price == 4450.50
    
    @pytest_asyncio.async_test
    async def test_flatten_position(self, mock_tradovate_auth):
        """Test flattening position"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Mock position query
        mock_position_response = {
            "positions": [{
                "symbol": "ES",
                "netPosition": 2,  # Long 2 contracts
                "avgPrice": 4445.00
            }]
        }
        
        # Mock flatten order response
        mock_order_response = {
            "orderId": 98769,
            "orderStatus": "Filled",
            "message": "Position flattened",
            "filledQty": 2,
            "remainingQty": 0,
            "avgFillPrice": 4450.00,
            "orderType": "Market",
            "symbol": "ES",
            "action": "Sell",
            "qty": 2,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=[mock_position_response, mock_order_response]):
            result = await orders.flatten_position(account_id=12345, symbol="ES")
            
            assert result.order_id == 98769
            assert result.action == "Sell"
            assert result.quantity == 2
            assert result.is_filled
    
    @pytest_asyncio.async_test
    async def test_flatten_position_no_position(self, mock_tradovate_auth):
        """Test flattening position when no position exists"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Mock empty position response
        mock_response = {"positions": []}
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.flatten_position(account_id=12345, symbol="ES")
            
            # Should return a response indicating no position
            assert result.message == "No position to flatten"
            assert result.quantity == 0
    
    @pytest_asyncio.async_test
    async def test_get_working_orders(self, mock_tradovate_auth):
        """Test getting working orders"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orders": [
                {
                    "orderId": 98765,
                    "orderStatus": "Working",
                    "symbol": "ES",
                    "action": "Buy",
                    "qty": 1,
                    "orderType": "Limit",
                    "limitPrice": 4445.00,
                    "timestamp": "2024-01-01T11:00:00Z"
                },
                {
                    "orderId": 98766,
                    "orderStatus": "Working",
                    "symbol": "NQ",
                    "action": "Sell",
                    "qty": 1,
                    "orderType": "Stop",
                    "stopPrice": 15850.00,
                    "timestamp": "2024-01-01T11:30:00Z"
                }
            ]
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            working_orders = await orders.get_working_orders(account_id=12345)
            
            assert len(working_orders) == 2
            assert all(order.is_working for order in working_orders)
            assert working_orders[0].symbol == "ES"
            assert working_orders[1].symbol == "NQ"
    
    @pytest_asyncio.async_test
    async def test_modify_order(self, mock_tradovate_auth):
        """Test modifying existing order"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": 98765,
            "orderStatus": "Working",
            "message": "Order modified successfully",
            "symbol": "ES",
            "action": "Buy",
            "qty": 2,  # Modified quantity
            "limitPrice": 4440.00,  # Modified price
            "orderType": "Limit",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.modify_order(
                order_id=98765,
                quantity=2,
                price=4440.00
            )
            
            assert result.order_id == 98765
            assert result.quantity == 2
            assert result.message == "Order modified successfully"


class TestOrderValidation:
    """Test order validation and error handling"""
    
    @pytest_asyncio.async_test
    async def test_invalid_symbol_validation(self, mock_tradovate_auth):
        """Test validation of invalid symbols"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="",  # Empty symbol
                action="Buy",
                quantity=1,
                order_type=OrderType.MARKET
            )
    
    @pytest_asyncio.async_test
    async def test_invalid_quantity_validation(self, mock_tradovate_auth):
        """Test validation of invalid quantities"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=0,  # Invalid quantity
                order_type=OrderType.MARKET
            )
        
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES", 
                action="Buy",
                quantity=-1,  # Negative quantity
                order_type=OrderType.MARKET
            )
    
    @pytest_asyncio.async_test
    async def test_invalid_action_validation(self, mock_tradovate_auth):
        """Test validation of invalid actions"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Invalid",  # Invalid action
                quantity=1,
                order_type=OrderType.MARKET
            )
    
    @pytest_asyncio.async_test
    async def test_limit_order_without_price(self, mock_tradovate_auth):
        """Test limit order validation without price"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.LIMIT
                # Missing price parameter
            )
    
    @pytest_asyncio.async_test
    async def test_stop_order_without_stop_price(self, mock_tradovate_auth):
        """Test stop order validation without stop price"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Sell",
                quantity=1,
                order_type=OrderType.STOP
                # Missing stop_price parameter
            )
    
    @pytest_asyncio.async_test
    async def test_stop_limit_order_validation(self, mock_tradovate_auth):
        """Test stop-limit order validation"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Missing both price and stop_price
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.STOP_LIMIT
            )
        
        # Missing stop_price
        with pytest.raises(OrderError):
            await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.STOP_LIMIT,
                price=4450.00
                # Missing stop_price
            )


class TestOrderErrorHandling:
    """Test error handling scenarios"""
    
    @pytest_asyncio.async_test
    async def test_api_error_handling(self, mock_tradovate_auth):
        """Test handling of API errors"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Mock API error
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=Exception("API Error")):
            with pytest.raises(OrderError):
                await orders.place_order(
                    account_id=12345,
                    symbol="ES",
                    action="Buy",
                    quantity=1,
                    order_type=OrderType.MARKET
                )
    
    @pytest_asyncio.async_test
    async def test_order_rejection_handling(self, mock_tradovate_auth):
        """Test handling of order rejections"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_response = {
            "orderId": None,
            "orderStatus": "Rejected",
            "message": "Insufficient buying power",
            "rejectReason": "INSUFFICIENT_FUNDS"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            result = await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.MARKET
            )
            
            assert result.is_rejected
            assert "Insufficient buying power" in result.message
    
    @pytest_asyncio.async_test
    async def test_invalid_order_id_handling(self, mock_tradovate_auth):
        """Test handling of invalid order IDs"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Mock "order not found" response
        mock_response = {"error": "Order not found"}
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=mock_response):
            with pytest.raises(OrderError):
                await orders.get_order_status(order_id=999999)
    
    @pytest_asyncio.async_test
    async def test_network_timeout_handling(self, mock_tradovate_auth):
        """Test handling of network timeouts"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=asyncio.TimeoutError("Request timeout")):
            with pytest.raises(OrderError):
                await orders.place_order(
                    account_id=12345,
                    symbol="ES",
                    action="Buy",
                    quantity=1,
                    order_type=OrderType.MARKET
                )


class TestOrderIntegration:
    """Integration tests for order functionality"""
    
    @pytest_asyncio.async_test
    async def test_complete_order_lifecycle(self, mock_tradovate_auth):
        """Test complete order lifecycle"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Step 1: Place order
        place_response = {
            "orderId": 98765,
            "orderStatus": "Working",
            "message": "Order placed successfully",
            "symbol": "ES",
            "action": "Buy",
            "qty": 1,
            "orderType": "Limit",
            "limitPrice": 4445.00,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Step 2: Check status (still working)
        status_response = {
            "orderId": 98765,
            "orderStatus": "Working",
            "filledQty": 0,
            "remainingQty": 1,
            "symbol": "ES",
            "timestamp": "2024-01-01T12:01:00Z"
        }
        
        # Step 3: Order filled
        filled_response = {
            "orderId": 98765,
            "orderStatus": "Filled",
            "filledQty": 1,
            "remainingQty": 0,
            "avgFillPrice": 4445.00,
            "symbol": "ES",
            "timestamp": "2024-01-01T12:02:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=[place_response, status_response, filled_response]):
            
            # Place order
            place_result = await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.LIMIT,
                price=4445.00
            )
            assert place_result.is_working
            
            # Check status
            status_result = await orders.get_order_status(order_id=98765)
            assert status_result.is_working
            
            # Check final status
            final_result = await orders.get_order_status(order_id=98765)
            assert final_result.is_filled
            assert final_result.average_fill_price == 4445.00
    
    @pytest_asyncio.async_test
    async def test_concurrent_order_operations(self, mock_tradovate_auth):
        """Test concurrent order operations"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        mock_responses = [
            {
                "orderId": 98765 + i,
                "orderStatus": "Working",
                "message": f"Order {i} placed",
                "symbol": "ES",
                "action": "Buy",
                "qty": 1,
                "orderType": "Market",
                "timestamp": "2024-01-01T12:00:00Z"
            }
            for i in range(5)
        ]
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         side_effect=mock_responses):
            
            # Place multiple orders concurrently
            order_tasks = [
                orders.place_order(
                    account_id=12345,
                    symbol="ES",
                    action="Buy",
                    quantity=1,
                    order_type=OrderType.MARKET
                )
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*order_tasks)
            
            # All orders should be placed successfully
            assert len(results) == 5
            assert all(result.is_working for result in results)
            assert all(result.symbol == "ES" for result in results)
    
    @pytest_asyncio.async_test
    async def test_order_tracking(self, mock_tradovate_auth):
        """Test order tracking functionality"""
        orders = TradovateOrders(mock_tradovate_auth)
        
        # Place order
        place_response = {
            "orderId": 98765,
            "orderStatus": "Working",
            "symbol": "ES",
            "action": "Buy",
            "qty": 1,
            "orderType": "Market",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch.object(mock_tradovate_auth, 'make_authenticated_request',
                         return_value=place_response):
            result = await orders.place_order(
                account_id=12345,
                symbol="ES",
                action="Buy",
                quantity=1,
                order_type=OrderType.MARKET
            )
            
            # Order should be tracked
            assert 98765 in orders._active_orders
            assert orders._active_orders[98765].symbol == "ES"