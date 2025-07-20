"""
Integration tests for complete Tradovate trading workflows.

Tests end-to-end scenarios including authentication, market data streaming,
order execution, and complete trading workflows with real-like conditions.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from datetime import datetime

from src.backend.feeds.tradovate.manager import TradovateManager
from src.backend.feeds.tradovate.auth import TradovateCredentials
from src.backend.feeds.tradovate.symbol_mapping import TradovateSymbolMapping


class TestTradovateIntegration:
    """Integration tests for complete Tradovate workflows"""
    
    @pytest_asyncio.async_test
    async def test_complete_initialization_workflow(self, demo_credentials, sample_account_info):
        """Test complete manager initialization workflow"""
        manager = TradovateManager(demo_credentials)
        
        # Mock successful authentication
        mock_auth_test = {"status": "success", "response_time": 150}
        
        # Mock account retrieval
        mock_accounts = [sample_account_info]
        
        # Mock market data test with multiple symbols
        mock_quotes = [
            MagicMock(symbol="ES", bid=4450.25, ask=4450.50),
            MagicMock(symbol="NQ", bid=15799.75, ask=15800.25)
        ]
        
        with patch.object(manager.auth, 'test_connection', return_value=mock_auth_test):
            with patch.object(manager.account, 'get_accounts', return_value=mock_accounts):
                with patch.object(manager.market_data, 'get_quotes', return_value=mock_quotes):
                    
                    # Initialize manager
                    result = await manager.initialize()
                    
                    # Verify successful initialization
                    assert result["status"] == "success"
                    assert result["environment"] == "demo"
                    assert result["account_count"] == 1
                    assert result["default_account_id"] == sample_account_info.id
                    assert result["market_data_working"] is True
                    assert len(result["accounts"]) == 1
                    
                    # Verify internal state
                    assert manager._initialized is True
                    assert len(manager._accounts) == 1
                    assert manager._default_account_id == sample_account_info.id
    
    @pytest_asyncio.async_test
    async def test_market_data_streaming_workflow(self, mock_tradovate_manager, mock_websocket):
        """Test complete market data streaming workflow"""
        manager = mock_tradovate_manager
        
        # Test symbols
        symbols = ["ES", "NQ", "YM", "RTY"]
        
        with patch.object(manager.market_data, 'start_websocket_stream', return_value=None):
            with patch.object(manager.market_data, 'subscribe_quotes', return_value=None):
                with patch.object(manager.market_data, 'unsubscribe_quotes', return_value=None):
                    with patch.object(manager.market_data, 'stop_websocket_stream', return_value=None):
                        
                        # Start streaming
                        start_result = await manager.start_market_data_stream(symbols)
                        assert start_result is True
                        assert manager._market_data_connected is True
                        
                        # Verify subscription calls
                        manager.market_data.start_websocket_stream.assert_called_once()
                        manager.market_data.subscribe_quotes.assert_called_once_with(symbols)
                        
                        # Stop streaming
                        await manager.stop_market_data_stream()
                        assert manager._market_data_connected is False
                        
                        # Verify cleanup
                        manager.market_data.stop_websocket_stream.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_basic_trading_workflow(self, mock_tradovate_manager):
        """Test basic buy/sell trading workflow"""
        manager = mock_tradovate_manager
        
        # Mock successful order execution
        mock_buy_result = MagicMock()
        mock_buy_result.is_filled = True
        mock_buy_result.order_id = 98765
        mock_buy_result.message = "Buy order filled"
        mock_buy_result.status = "Filled"
        mock_buy_result.filled_quantity = 1
        
        mock_sell_result = MagicMock()
        mock_sell_result.is_filled = True
        mock_sell_result.order_id = 98766
        mock_sell_result.message = "Sell order filled"
        mock_sell_result.status = "Filled"
        mock_sell_result.filled_quantity = 1
        
        with patch.object(manager.orders, 'place_order', side_effect=[mock_buy_result, mock_sell_result]):
            
            # Execute buy alert
            buy_alert = {
                "symbol": "ES",
                "action": "buy",
                "quantity": 1,
                "account_group": "main"
            }
            
            buy_result = await manager.execute_alert(buy_alert)
            
            assert buy_result["status"] == "success"
            assert buy_result["action"] == "buy"
            assert buy_result["symbol"] == "ES"
            assert buy_result["order_id"] == 98765
            
            # Execute sell alert to close position
            sell_alert = {
                "symbol": "ES",
                "action": "sell",
                "quantity": 1,
                "account_group": "main"
            }
            
            sell_result = await manager.execute_alert(sell_alert)
            
            assert sell_result["status"] == "success"
            assert sell_result["action"] == "sell"
            assert sell_result["symbol"] == "ES"
            assert sell_result["order_id"] == 98766
    
    @pytest_asyncio.async_test
    async def test_funded_account_trading_workflow(self, mock_tradovate_manager):
        """Test funded account trading with risk management"""
        manager = mock_tradovate_manager
        
        # Mock account performance within limits
        mock_performance = {"day_pnl": -200}  # Under $1000 limit
        mock_positions = []  # No current positions
        
        # Mock successful order execution
        mock_order_result = MagicMock()
        mock_order_result.is_filled = True
        mock_order_result.order_id = 98765
        mock_order_result.message = "Order filled"
        mock_order_result.status = "Filled"
        
        with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
            with patch.object(manager.account, 'get_positions', return_value=mock_positions):
                with patch.object(manager.orders, 'place_order', return_value=mock_order_result):
                    
                    # Execute funded account alert
                    funded_alert = {
                        "symbol": "NQ",
                        "action": "buy",
                        "quantity": 1,
                        "account_group": "topstep"
                    }
                    
                    result = await manager.execute_alert(funded_alert)
                    
                    # Should pass risk checks and execute
                    assert result["status"] == "success"
                    assert result["symbol"] == "NQ"
                    assert result["order_id"] == 98765
    
    @pytest_asyncio.async_test
    async def test_funded_account_risk_rejection(self, mock_tradovate_manager):
        """Test funded account risk management rejection"""
        manager = mock_tradovate_manager
        
        # Mock account performance exceeding daily loss limit
        mock_performance = {"day_pnl": -1500}  # Over $1000 limit
        
        with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
            
            # Execute funded account alert
            funded_alert = {
                "symbol": "ES",
                "action": "buy",
                "quantity": 1,
                "account_group": "topstep"
            }
            
            result = await manager.execute_alert(funded_alert)
            
            # Should be rejected due to risk limits
            assert result["status"] == "rejected"
            assert "Risk check failed" in result["message"]
            assert "Daily loss limit reached" in result["message"]
    
    @pytest_asyncio.async_test
    async def test_position_flattening_workflow(self, mock_tradovate_manager):
        """Test position flattening workflow"""
        manager = mock_tradovate_manager
        
        # Mock flatten order result
        mock_flatten_result = MagicMock()
        mock_flatten_result.is_filled = True
        mock_flatten_result.order_id = 98767
        mock_flatten_result.message = "Position flattened"
        mock_flatten_result.status = "Filled"
        
        with patch.object(manager.orders, 'flatten_position', return_value=mock_flatten_result):
            
            # Execute close alert
            close_alert = {
                "symbol": "ES",
                "action": "close"
            }
            
            result = await manager.execute_alert(close_alert)
            
            assert result["status"] == "success"
            assert result["action"] == "close"
            assert result["symbol"] == "ES"
            assert result["order_id"] == 98767
    
    @pytest_asyncio.async_test
    async def test_concurrent_alert_processing(self, mock_tradovate_manager):
        """Test processing multiple alerts concurrently"""
        manager = mock_tradovate_manager
        
        # Mock order results
        order_results = [
            MagicMock(is_filled=True, order_id=98765+i, status="Filled")
            for i in range(5)
        ]
        
        # Mock account performance for funded account checks
        mock_performance = {"day_pnl": -100}
        mock_positions = []
        
        with patch.object(manager.orders, 'place_order', side_effect=order_results):
            with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
                with patch.object(manager.account, 'get_positions', return_value=mock_positions):
                    
                    # Create multiple alerts
                    alerts = [
                        {"symbol": "ES", "action": "buy", "quantity": 1, "account_group": "main"},
                        {"symbol": "NQ", "action": "sell", "quantity": 1, "account_group": "main"},
                        {"symbol": "YM", "action": "buy", "quantity": 2, "account_group": "main"},
                        {"symbol": "RTY", "action": "sell", "quantity": 1, "account_group": "topstep"},
                        {"symbol": "CL", "action": "buy", "quantity": 1, "account_group": "main"}
                    ]
                    
                    # Process alerts concurrently
                    results = await asyncio.gather(*[
                        manager.execute_alert(alert) for alert in alerts
                    ])
                    
                    # All should succeed
                    assert len(results) == 5
                    assert all(result["status"] == "success" for result in results)
                    assert all(98765 <= result["order_id"] <= 98769 for result in results)
    
    @pytest_asyncio.async_test
    async def test_account_summary_workflow(self, mock_tradovate_manager, sample_account_info, sample_cash_balance, sample_positions):
        """Test comprehensive account summary workflow"""
        manager = mock_tradovate_manager
        
        # Mock all account data
        mock_performance = {
            "day_pnl": 750.0,
            "total_pnl": 2500.0,
            "trades_today": 8,
            "win_rate": 0.625
        }
        
        with patch.object(manager.account, 'get_account_info', return_value=sample_account_info):
            with patch.object(manager.account, 'get_cash_balance', return_value=sample_cash_balance):
                with patch.object(manager.account, 'get_positions', return_value=sample_positions):
                    with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
                        
                        summary = await manager.get_account_summary()
                        
                        # Verify comprehensive summary
                        assert summary["account_info"]["id"] == sample_account_info.id
                        assert summary["account_info"]["name"] == sample_account_info.name
                        assert summary["balance"]["cash_balance"] == sample_cash_balance.cash_balance
                        assert summary["balance"]["day_pl"] == sample_cash_balance.day_pl
                        assert len(summary["positions"]) == 2
                        assert summary["performance"]["day_pnl"] == 750.0
                        assert summary["performance"]["total_pnl"] == 2500.0
                        assert "timestamp" in summary
    
    @pytest_asyncio.async_test
    async def test_error_recovery_workflow(self, mock_tradovate_manager):
        """Test error recovery in trading workflows"""
        manager = mock_tradovate_manager
        
        # Mock mixed success/failure results
        mock_success = MagicMock(is_filled=True, order_id=98765, status="Filled")
        mock_failure = Exception("Order rejected - insufficient margin")
        mock_recovery = MagicMock(is_filled=True, order_id=98766, status="Filled")
        
        with patch.object(manager.orders, 'place_order', side_effect=[mock_success, mock_failure, mock_recovery]):
            
            # First alert - should succeed
            alert1 = {"symbol": "ES", "action": "buy", "quantity": 1}
            result1 = await manager.execute_alert(alert1)
            assert result1["status"] == "success"
            
            # Second alert - should fail gracefully
            alert2 = {"symbol": "NQ", "action": "buy", "quantity": 10}  # Large quantity
            result2 = await manager.execute_alert(alert2)
            assert result2["status"] == "error"
            assert "Order rejected" in result2["message"]
            
            # Third alert - should succeed (system recovered)
            alert3 = {"symbol": "YM", "action": "buy", "quantity": 1}
            result3 = await manager.execute_alert(alert3)
            assert result3["status"] == "success"
    
    @pytest_asyncio.async_test
    async def test_symbol_mapping_integration(self, mock_tradovate_manager):
        """Test integration with symbol mapping functionality"""
        manager = mock_tradovate_manager
        mapping = TradovateSymbolMapping()
        
        # Test symbols from different sectors
        test_symbols = ["ES", "CL", "GC", "ZB", "6E"]
        
        # Mock quote responses for all symbols
        mock_quotes = [
            MagicMock(symbol=symbol, bid=100.0+i, ask=100.25+i)
            for i, symbol in enumerate(test_symbols)
        ]
        
        with patch.object(manager.market_data, 'get_quotes', return_value=mock_quotes):
            
            # Get quotes for all symbols
            quotes = await manager.market_data.get_quotes(test_symbols)
            
            assert len(quotes) == 5
            
            # Verify each symbol has valid contract specifications
            for quote in quotes:
                symbol_info = mapping.get_symbol_info(quote.symbol)
                assert symbol_info is not None
                assert symbol_info.tick_size > 0
                assert symbol_info.tick_value > 0
                assert symbol_info.contract_size > 0
                
                # Verify price formatting works
                formatted_price = mapping.format_price(quote.symbol, quote.bid)
                assert isinstance(formatted_price, str)
                
                # Verify price validation
                assert mapping.validate_price(quote.symbol, quote.bid)
    
    @pytest_asyncio.async_test
    async def test_complete_trading_session(self, mock_tradovate_manager):
        """Test complete trading session from start to finish"""
        manager = mock_tradovate_manager
        
        # Mock market data streaming
        streaming_symbols = ["ES", "NQ", "CL"]
        
        # Mock order executions
        order_results = [
            MagicMock(is_filled=True, order_id=98765, status="Filled"),  # ES buy
            MagicMock(is_filled=True, order_id=98766, status="Filled"),  # NQ sell  
            MagicMock(is_filled=True, order_id=98767, status="Filled"),  # CL buy
            MagicMock(is_filled=True, order_id=98768, status="Filled"),  # ES close
        ]
        
        # Mock account data
        mock_performance = {"day_pnl": 500.0}
        mock_positions = []
        
        with patch.object(manager.market_data, 'start_websocket_stream', return_value=None):
            with patch.object(manager.market_data, 'subscribe_quotes', return_value=None):
                with patch.object(manager.market_data, 'stop_websocket_stream', return_value=None):
                    with patch.object(manager.orders, 'place_order', side_effect=order_results[:3]):
                        with patch.object(manager.orders, 'flatten_position', return_value=order_results[3]):
                            with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
                                with patch.object(manager.account, 'get_positions', return_value=mock_positions):
                                    
                                    # 1. Start market data streaming
                                    stream_result = await manager.start_market_data_stream(streaming_symbols)
                                    assert stream_result is True
                                    
                                    # 2. Execute multiple trading alerts
                                    alerts = [
                                        {"symbol": "ES", "action": "buy", "quantity": 2},
                                        {"symbol": "NQ", "action": "sell", "quantity": 1},
                                        {"symbol": "CL", "action": "buy", "quantity": 1}
                                    ]
                                    
                                    alert_results = []
                                    for alert in alerts:
                                        result = await manager.execute_alert(alert)
                                        alert_results.append(result)
                                        assert result["status"] == "success"
                                    
                                    # 3. Close all positions
                                    close_result = await manager.execute_alert({
                                        "symbol": "ES", "action": "close"
                                    })
                                    assert close_result["status"] == "success"
                                    
                                    # 4. Get final account summary
                                    final_summary = await manager.get_account_summary()
                                    assert "performance" in final_summary
                                    
                                    # 5. Stop streaming and cleanup
                                    await manager.stop_market_data_stream()
                                    await manager.close()
                                    
                                    # Verify all operations completed successfully
                                    assert len(alert_results) == 3
                                    assert all(r["status"] == "success" for r in alert_results)


class TestTradovateErrorScenarios:
    """Test error scenarios and edge cases"""
    
    @pytest_asyncio.async_test
    async def test_authentication_failure_recovery(self, demo_credentials):
        """Test recovery from authentication failures"""
        manager = TradovateManager(demo_credentials)
        
        # Mock initial auth failure followed by success
        auth_responses = [
            {"status": "failed", "message": "Invalid credentials"},
            {"status": "success", "response_time": 200}
        ]
        
        mock_accounts = [MagicMock(id=12345, name="Test Account", archived=False)]
        mock_quotes = [MagicMock(symbol="ES")]
        
        with patch.object(manager.auth, 'test_connection', side_effect=auth_responses):
            with patch.object(manager.account, 'get_accounts', return_value=mock_accounts):
                with patch.object(manager.market_data, 'get_quotes', return_value=mock_quotes):
                    
                    # First initialization should fail
                    result1 = await manager.initialize()
                    assert result1["status"] == "failed"
                    assert result1["step"] == "authentication"
                    
                    # Second initialization should succeed
                    result2 = await manager.initialize()
                    assert result2["status"] == "success"
    
    @pytest_asyncio.async_test
    async def test_market_data_connection_failure(self, mock_tradovate_manager):
        """Test handling of market data connection failures"""
        manager = mock_tradovate_manager
        
        # Mock streaming failure followed by recovery
        with patch.object(manager.market_data, 'start_websocket_stream', side_effect=Exception("Connection failed")):
            
            # First attempt should fail
            result1 = await manager.start_market_data_stream(["ES"])
            assert result1 is False
            assert not manager._market_data_connected
            
            # After connection issue resolved
            with patch.object(manager.market_data, 'start_websocket_stream', return_value=None):
                with patch.object(manager.market_data, 'subscribe_quotes', return_value=None):
                    
                    # Second attempt should succeed
                    result2 = await manager.start_market_data_stream(["ES"])
                    assert result2 is True
                    assert manager._market_data_connected
    
    @pytest_asyncio.async_test
    async def test_order_execution_failures(self, mock_tradovate_manager):
        """Test handling of various order execution failures"""
        manager = mock_tradovate_manager
        
        # Test different failure scenarios
        failure_scenarios = [
            Exception("Insufficient margin"),
            Exception("Invalid symbol"),
            Exception("Market closed"),
            Exception("Position limit exceeded")
        ]
        
        for i, failure in enumerate(failure_scenarios):
            with patch.object(manager.orders, 'place_order', side_effect=failure):
                
                alert = {
                    "symbol": "ES",
                    "action": "buy", 
                    "quantity": 1
                }
                
                result = await manager.execute_alert(alert)
                assert result["status"] == "error"
                assert str(failure) in result["message"]
    
    @pytest_asyncio.async_test
    async def test_partial_system_failure(self, mock_tradovate_manager, sample_account_info):
        """Test handling when some system components fail"""
        manager = mock_tradovate_manager
        
        # Mock partial failure - account info works, but balance fails
        with patch.object(manager.account, 'get_account_info', return_value=sample_account_info):
            with patch.object(manager.account, 'get_cash_balance', side_effect=Exception("Balance service unavailable")):
                with patch.object(manager.account, 'get_positions', return_value=[]):
                    with patch.object(manager.account, 'get_account_performance', return_value={}):
                        
                        summary = await manager.get_account_summary()
                        
                        # Should have partial data
                        assert summary["account_info"]["id"] == sample_account_info.id
                        assert summary["balance"] is None  # Failed component
                        assert summary["positions"] == []  # Working component
    
    @pytest_asyncio.async_test
    async def test_cleanup_after_errors(self, mock_tradovate_manager):
        """Test proper cleanup after errors occur"""
        manager = mock_tradovate_manager
        manager._market_data_connected = True
        
        # Mock cleanup with some failures
        with patch.object(manager.market_data, 'close', side_effect=Exception("Close error")):
            with patch.object(manager.auth, 'close', return_value=None):
                
                # Should handle cleanup errors gracefully
                await manager.close()
                
                # Auth close should still be called
                manager.auth.close.assert_called_once()


class TestTradovatePerformance:
    """Test performance characteristics under load"""
    
    @pytest_asyncio.async_test
    async def test_high_volume_alert_processing(self, mock_tradovate_manager):
        """Test processing high volume of alerts"""
        manager = mock_tradovate_manager
        
        # Create large number of alerts
        num_alerts = 100
        alerts = [
            {
                "symbol": "ES",
                "action": "buy" if i % 2 == 0 else "sell",
                "quantity": 1,
                "timestamp": f"2024-01-01T12:{i:02d}:00Z"
            }
            for i in range(num_alerts)
        ]
        
        # Mock successful order execution
        mock_result = MagicMock(is_filled=True, order_id=98765, status="Filled")
        
        with patch.object(manager.orders, 'place_order', return_value=mock_result):
            
            start_time = datetime.utcnow()
            
            # Process alerts in batches for performance
            batch_size = 10
            results = []
            
            for i in range(0, num_alerts, batch_size):
                batch = alerts[i:i+batch_size]
                batch_results = await asyncio.gather(*[
                    manager.execute_alert(alert) for alert in batch
                ])
                results.extend(batch_results)
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Verify all processed successfully
            assert len(results) == num_alerts
            assert all(result["status"] == "success" for result in results)
            
            # Performance check - should process alerts quickly
            avg_time_per_alert = processing_time / num_alerts
            assert avg_time_per_alert < 0.1  # Less than 100ms per alert
    
    @pytest_asyncio.async_test
    async def test_concurrent_operations_performance(self, mock_tradovate_manager):
        """Test performance of concurrent operations"""
        manager = mock_tradovate_manager
        
        # Mock various operations
        mock_quotes = [MagicMock(symbol="ES", bid=4450.0)]
        mock_summary = {"account_info": {"id": 12345}}
        mock_order = MagicMock(is_filled=True, order_id=98765)
        
        with patch.object(manager.market_data, 'get_quotes', return_value=mock_quotes):
            with patch.object(manager, 'get_account_summary', return_value=mock_summary):
                with patch.object(manager.orders, 'place_order', return_value=mock_order):
                    
                    start_time = datetime.utcnow()
                    
                    # Run multiple operations concurrently
                    operations = await asyncio.gather(
                        manager.market_data.get_quotes(["ES", "NQ", "YM"]),
                        manager.get_account_summary(),
                        manager.execute_alert({"symbol": "ES", "action": "buy", "quantity": 1}),
                        manager.execute_alert({"symbol": "NQ", "action": "sell", "quantity": 1})
                    )
                    
                    end_time = datetime.utcnow()
                    total_time = (end_time - start_time).total_seconds()
                    
                    # Should complete quickly when operations are concurrent
                    assert total_time < 1.0  # Less than 1 second total
                    assert len(operations) == 4
    
    @pytest_asyncio.async_test
    async def test_memory_usage_stability(self, mock_tradovate_manager):
        """Test memory usage remains stable under sustained operation"""
        manager = mock_tradovate_manager
        
        # Simulate sustained trading activity
        mock_result = MagicMock(is_filled=True, order_id=98765, status="Filled")
        
        with patch.object(manager.orders, 'place_order', return_value=mock_result):
            
            # Process many alerts to test memory stability
            for i in range(1000):
                alert = {
                    "symbol": "ES",
                    "action": "buy" if i % 2 == 0 else "sell",
                    "quantity": 1
                }
                
                result = await manager.execute_alert(alert)
                assert result["status"] == "success"
                
                # Verify no memory leaks in order tracking
                # In real implementation, old orders should be cleaned up
                if hasattr(manager.orders, '_active_orders'):
                    # Should not accumulate indefinitely
                    assert len(manager.orders._active_orders) < 100