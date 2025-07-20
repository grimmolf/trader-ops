"""
Unit tests for Tradovate manager module.

Tests the high-level integration manager that coordinates authentication,
market data, order execution, and account management.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

from src.backend.feeds.tradovate.manager import TradovateManager
from src.backend.feeds.tradovate.auth import TradovateCredentials


class TestTradovateManager:
    """Test TradovateManager class"""
    
    def test_manager_initialization(self, demo_credentials):
        """Test manager initialization"""
        manager = TradovateManager(demo_credentials)
        
        assert manager.credentials == demo_credentials
        assert manager.auth is not None
        assert manager.market_data is not None
        assert manager.orders is not None
        assert manager.account is not None
        assert not manager._initialized
        assert manager._accounts == []
        assert manager._default_account_id is None
        assert not manager._market_data_connected
    
    @pytest_asyncio.async_test
    async def test_successful_initialization(self, demo_credentials, sample_account_info):
        """Test successful manager initialization"""
        manager = TradovateManager(demo_credentials)
        
        # Mock auth test
        mock_auth_test = {"status": "success"}
        
        # Mock accounts
        mock_accounts = [sample_account_info]
        
        # Mock quotes for market data test
        mock_quotes = [
            MagicMock(symbol="ES", bid=4450.25, ask=4450.50),
            MagicMock(symbol="NQ", bid=15799.75, ask=15800.25)
        ]
        
        with patch.object(manager.auth, 'test_connection', return_value=mock_auth_test):
            with patch.object(manager.account, 'get_accounts', return_value=mock_accounts):
                with patch.object(manager.market_data, 'get_quotes', return_value=mock_quotes):
                    
                    result = await manager.initialize()
                    
                    assert result["status"] == "success"
                    assert result["environment"] == "demo"
                    assert result["account_count"] == 1
                    assert result["default_account_id"] == sample_account_info.id
                    assert result["market_data_working"] is True
                    assert manager._initialized is True
    
    @pytest_asyncio.async_test
    async def test_initialization_auth_failure(self, demo_credentials):
        """Test initialization with authentication failure"""
        manager = TradovateManager(demo_credentials)
        
        # Mock auth failure
        mock_auth_test = {"status": "failed", "message": "Invalid credentials"}
        
        with patch.object(manager.auth, 'test_connection', return_value=mock_auth_test):
            result = await manager.initialize()
            
            assert result["status"] == "failed"
            assert result["step"] == "authentication"
            assert "Invalid credentials" in result["error"]
            assert not manager._initialized
    
    @pytest_asyncio.async_test
    async def test_initialization_no_accounts(self, demo_credentials):
        """Test initialization with no accounts"""
        manager = TradovateManager(demo_credentials)
        
        # Mock successful auth but no accounts
        mock_auth_test = {"status": "success"}
        mock_accounts = []
        
        with patch.object(manager.auth, 'test_connection', return_value=mock_auth_test):
            with patch.object(manager.account, 'get_accounts', return_value=mock_accounts):
                
                result = await manager.initialize()
                
                assert result["status"] == "failed"
                assert result["step"] == "accounts"
                assert "No trading accounts found" in result["error"]
    
    @pytest_asyncio.async_test
    async def test_initialization_already_initialized(self, demo_credentials):
        """Test initialization when already initialized"""
        manager = TradovateManager(demo_credentials)
        manager._initialized = True
        
        result = await manager.initialize()
        
        assert result["status"] == "already_initialized"


class TestAlertExecution:
    """Test TradingView alert execution"""
    
    @pytest_asyncio.async_test
    async def test_execute_basic_buy_alert(self, mock_tradovate_manager, sample_alert_data):
        """Test executing basic buy alert"""
        manager = mock_tradovate_manager
        
        # Mock order execution
        mock_order_result = MagicMock()
        mock_order_result.is_filled = True
        mock_order_result.order_id = 98765
        mock_order_result.message = "Order filled"
        mock_order_result.status = "Filled"
        mock_order_result.filled_quantity = 1
        
        with patch.object(manager.orders, 'place_order', return_value=mock_order_result):
            result = await manager.execute_alert(sample_alert_data)
            
            assert result["status"] == "success"
            assert result["action"] == "buy"
            assert result["symbol"] == "ES"
            assert result["quantity"] == 1
            assert result["order_id"] == 98765
    
    @pytest_asyncio.async_test
    async def test_execute_sell_alert(self, mock_tradovate_manager):
        """Test executing sell alert"""
        manager = mock_tradovate_manager
        
        sell_alert = {
            "symbol": "NQ",
            "action": "sell",
            "quantity": 2,
            "price": 15800.00,
            "order_type": "limit"
        }
        
        mock_order_result = MagicMock()
        mock_order_result.is_working = True
        mock_order_result.order_id = 98766
        mock_order_result.message = "Limit order placed"
        mock_order_result.status = "Working"
        mock_order_result.filled_quantity = 0
        
        with patch.object(manager.orders, 'place_order', return_value=mock_order_result):
            result = await manager.execute_alert(sell_alert)
            
            assert result["status"] == "success"
            assert result["action"] == "sell"
            assert result["symbol"] == "NQ"
            assert result["quantity"] == 2
    
    @pytest_asyncio.async_test
    async def test_execute_close_alert(self, mock_tradovate_manager):
        """Test executing close position alert"""
        manager = mock_tradovate_manager
        
        close_alert = {
            "symbol": "ES",
            "action": "close"
        }
        
        mock_flatten_result = MagicMock()
        mock_flatten_result.is_filled = True
        mock_flatten_result.order_id = 98767
        mock_flatten_result.message = "Position flattened"
        mock_flatten_result.status = "Filled"
        
        with patch.object(manager.orders, 'flatten_position', return_value=mock_flatten_result):
            result = await manager.execute_alert(close_alert)
            
            assert result["status"] == "success"
            assert result["action"] == "close"
            assert result["symbol"] == "ES"
    
    @pytest_asyncio.async_test
    async def test_execute_alert_not_initialized(self, demo_credentials):
        """Test executing alert when manager not initialized"""
        manager = TradovateManager(demo_credentials)
        # Don't initialize
        
        alert_data = {"symbol": "ES", "action": "buy", "quantity": 1}
        
        result = await manager.execute_alert(alert_data)
        
        assert result["status"] == "error"
        assert "not initialized" in result["message"]
    
    @pytest_asyncio.async_test
    async def test_execute_alert_missing_parameters(self, mock_tradovate_manager):
        """Test executing alert with missing parameters"""
        manager = mock_tradovate_manager
        
        # Missing symbol
        invalid_alert = {"action": "buy", "quantity": 1}
        
        result = await manager.execute_alert(invalid_alert)
        
        assert result["status"] == "rejected"
        assert "Missing required parameters" in result["message"]
    
    @pytest_asyncio.async_test
    async def test_execute_alert_invalid_action(self, mock_tradovate_manager):
        """Test executing alert with invalid action"""
        manager = mock_tradovate_manager
        
        invalid_alert = {
            "symbol": "ES",
            "action": "invalid_action",
            "quantity": 1
        }
        
        result = await manager.execute_alert(invalid_alert)
        
        assert result["status"] == "rejected"
        assert "Invalid action" in result["message"]


class TestFundedAccountHandling:
    """Test funded account risk management"""
    
    @pytest_asyncio.async_test
    async def test_funded_account_detection(self, mock_tradovate_manager):
        """Test detection of funded account groups"""
        manager = mock_tradovate_manager
        
        assert manager._is_funded_account("topstep")
        assert manager._is_funded_account("apex")
        assert manager._is_funded_account("tradeday")
        assert manager._is_funded_account("fundedtrader")
        assert not manager._is_funded_account("main")
        assert not manager._is_funded_account("personal")
    
    @pytest_asyncio.async_test
    async def test_funded_account_risk_check_pass(self, mock_tradovate_manager, funded_account_alert):
        """Test funded account risk check passing"""
        manager = mock_tradovate_manager
        
        # Mock account performance within limits
        mock_performance = {"day_pnl": -200}  # Under $1000 limit
        mock_positions = []  # No current positions
        
        with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
            with patch.object(manager.account, 'get_positions', return_value=mock_positions):
                
                risk_check = await manager._check_funded_account_rules(12345, funded_account_alert)
                
                assert risk_check["allowed"] is True
                assert risk_check["day_pnl"] == -200
                assert risk_check["contract_count"] == 0
    
    @pytest_asyncio.async_test
    async def test_funded_account_daily_loss_limit(self, mock_tradovate_manager, funded_account_alert):
        """Test funded account daily loss limit enforcement"""
        manager = mock_tradovate_manager
        
        # Mock account performance exceeding daily loss limit
        mock_performance = {"day_pnl": -1500}  # Over $1000 limit
        
        with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
            risk_check = await manager._check_funded_account_rules(12345, funded_account_alert)
            
            assert risk_check["allowed"] is False
            assert "Daily loss limit reached" in risk_check["reason"]
    
    @pytest_asyncio.async_test
    async def test_funded_account_contract_limit(self, mock_tradovate_manager, funded_account_alert):
        """Test funded account contract limit enforcement"""
        manager = mock_tradovate_manager
        
        # Mock account performance within daily loss limit
        mock_performance = {"day_pnl": -200}
        
        # Mock positions at contract limit
        mock_positions = [
            MagicMock(net_position=2),  # 2 contracts
            MagicMock(net_position=1)   # 1 contract = 3 total
        ]
        
        with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
            with patch.object(manager.account, 'get_positions', return_value=mock_positions):
                
                risk_check = await manager._check_funded_account_rules(12345, funded_account_alert)
                
                assert risk_check["allowed"] is False
                assert "Contract limit exceeded" in risk_check["reason"]
    
    @pytest_asyncio.async_test
    async def test_funded_account_alert_execution_blocked(self, mock_tradovate_manager, funded_account_alert):
        """Test funded account alert execution blocked by risk check"""
        manager = mock_tradovate_manager
        
        # Mock risk check failure
        mock_performance = {"day_pnl": -1500}  # Over limit
        
        with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
            result = await manager.execute_alert(funded_account_alert)
            
            assert result["status"] == "rejected"
            assert "Risk check failed" in result["message"]


class TestAccountManagement:
    """Test account management functionality"""
    
    @pytest_asyncio.async_test
    async def test_get_account_summary(self, mock_tradovate_manager, sample_account_info, sample_cash_balance, sample_positions):
        """Test getting comprehensive account summary"""
        manager = mock_tradovate_manager
        
        # Mock account data
        mock_performance = {"day_pnl": 250, "total_pnl": 1500}
        
        with patch.object(manager.account, 'get_account_info', return_value=sample_account_info):
            with patch.object(manager.account, 'get_cash_balance', return_value=sample_cash_balance):
                with patch.object(manager.account, 'get_positions', return_value=sample_positions):
                    with patch.object(manager.account, 'get_account_performance', return_value=mock_performance):
                        
                        summary = await manager.get_account_summary()
                        
                        assert summary["account_info"]["id"] == sample_account_info.id
                        assert summary["balance"]["cash_balance"] == sample_cash_balance.cash_balance
                        assert len(summary["positions"]) == 2
                        assert summary["performance"]["day_pnl"] == 250
                        assert "timestamp" in summary
    
    @pytest_asyncio.async_test
    async def test_get_account_summary_specific_account(self, mock_tradovate_manager, sample_account_info):
        """Test getting account summary for specific account"""
        manager = mock_tradovate_manager
        
        with patch.object(manager.account, 'get_account_info', return_value=sample_account_info):
            with patch.object(manager.account, 'get_cash_balance', return_value=MagicMock()):
                with patch.object(manager.account, 'get_positions', return_value=[]):
                    with patch.object(manager.account, 'get_account_performance', return_value={}):
                        
                        summary = await manager.get_account_summary(account_id=67890)
                        
                        # Should use the specified account ID, not default
                        manager.account.get_account_info.assert_called_with(67890)
    
    @pytest_asyncio.async_test
    async def test_get_account_summary_no_account(self, demo_credentials):
        """Test getting account summary with no account ID"""
        manager = TradovateManager(demo_credentials)
        # Don't set default account ID
        
        summary = await manager.get_account_summary()
        
        assert "error" in summary
        assert "No account ID specified" in summary["error"]


class TestMarketDataStreaming:
    """Test market data streaming functionality"""
    
    @pytest_asyncio.async_test
    async def test_start_market_data_stream(self, mock_tradovate_manager):
        """Test starting market data stream"""
        manager = mock_tradovate_manager
        
        symbols = ["ES", "NQ", "YM"]
        
        with patch.object(manager.market_data, 'start_websocket_stream', return_value=None):
            with patch.object(manager.market_data, 'subscribe_quotes', return_value=None):
                
                result = await manager.start_market_data_stream(symbols)
                
                assert result is True
                assert manager._market_data_connected is True
                
                # Should start stream and subscribe to symbols
                manager.market_data.start_websocket_stream.assert_called_once()
                manager.market_data.subscribe_quotes.assert_called_once_with(symbols)
    
    @pytest_asyncio.async_test
    async def test_start_market_data_stream_already_connected(self, mock_tradovate_manager):
        """Test starting market data stream when already connected"""
        manager = mock_tradovate_manager
        manager._market_data_connected = True
        
        result = await manager.start_market_data_stream(["ES"])
        
        assert result is True
        # Should not start new stream
        manager.market_data.start_websocket_stream.assert_not_called()
    
    @pytest_asyncio.async_test
    async def test_start_market_data_stream_failure(self, mock_tradovate_manager):
        """Test market data stream start failure"""
        manager = mock_tradovate_manager
        
        with patch.object(manager.market_data, 'start_websocket_stream', side_effect=Exception("Connection failed")):
            result = await manager.start_market_data_stream(["ES"])
            
            assert result is False
            assert not manager._market_data_connected
    
    @pytest_asyncio.async_test
    async def test_stop_market_data_stream(self, mock_tradovate_manager):
        """Test stopping market data stream"""
        manager = mock_tradovate_manager
        manager._market_data_connected = True
        
        with patch.object(manager.market_data, 'stop_websocket_stream', return_value=None):
            await manager.stop_market_data_stream()
            
            assert not manager._market_data_connected
            manager.market_data.stop_websocket_stream.assert_called_once()


class TestManagerUtilities:
    """Test manager utility functions"""
    
    @pytest_asyncio.async_test
    async def test_get_target_account_main(self, mock_tradovate_manager):
        """Test getting target account for main group"""
        manager = mock_tradovate_manager
        
        account_id = await manager._get_target_account("main")
        assert account_id == manager._default_account_id
        
        # Empty string should also use default
        account_id = await manager._get_target_account("")
        assert account_id == manager._default_account_id
    
    @pytest_asyncio.async_test
    async def test_get_target_account_funded(self, mock_tradovate_manager):
        """Test getting target account for funded group"""
        manager = mock_tradovate_manager
        
        # For now, funded accounts use default account
        # In production, this would map to specific funded accounts
        account_id = await manager._get_target_account("topstep")
        assert account_id == manager._default_account_id
    
    def test_get_status(self, mock_tradovate_manager):
        """Test getting manager status"""
        manager = mock_tradovate_manager
        
        status = manager.get_status()
        
        assert status["initialized"] is True
        assert status["environment"] == "demo"
        assert status["account_count"] == 1
        assert status["default_account_id"] == 12345
        assert "market_data_connected" in status
        assert "auth_token_valid" in status
    
    def test_manager_repr(self, mock_tradovate_manager):
        """Test manager string representation"""
        manager = mock_tradovate_manager
        
        repr_str = repr(manager)
        
        assert "TradovateManager" in repr_str
        assert "demo" in repr_str
        assert "initialized" in repr_str
        assert "accounts=1" in repr_str


class TestManagerCleanup:
    """Test manager cleanup and resource management"""
    
    @pytest_asyncio.async_test
    async def test_close_manager(self, mock_tradovate_manager):
        """Test closing manager and cleanup"""
        manager = mock_tradovate_manager
        manager._market_data_connected = True
        
        with patch.object(manager, 'stop_market_data_stream', return_value=None):
            with patch.object(manager.market_data, 'close', return_value=None):
                with patch.object(manager.auth, 'close', return_value=None):
                    
                    await manager.close()
                    
                    # Should stop stream and close connections
                    manager.stop_market_data_stream.assert_called_once()
                    manager.market_data.close.assert_called_once()
                    manager.auth.close.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_close_manager_no_stream(self, mock_tradovate_manager):
        """Test closing manager without active stream"""
        manager = mock_tradovate_manager
        manager._market_data_connected = False
        
        with patch.object(manager.market_data, 'close', return_value=None):
            with patch.object(manager.auth, 'close', return_value=None):
                
                await manager.close()
                
                # Should not try to stop stream
                manager.market_data.close.assert_called_once()
                manager.auth.close.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_close_manager_with_errors(self, mock_tradovate_manager):
        """Test closing manager with errors"""
        manager = mock_tradovate_manager
        
        with patch.object(manager.market_data, 'close', side_effect=Exception("Close error")):
            # Should handle errors gracefully
            await manager.close()


class TestManagerIntegration:
    """Integration tests for manager functionality"""
    
    @pytest_asyncio.async_test
    async def test_full_trading_workflow(self, demo_credentials, sample_account_info):
        """Test complete trading workflow"""
        manager = TradovateManager(demo_credentials)
        
        # Mock all dependencies for full workflow
        mock_auth_test = {"status": "success"}
        mock_accounts = [sample_account_info]
        mock_quotes = [MagicMock(symbol="ES")]
        mock_order_result = MagicMock(is_filled=True, order_id=98765)
        
        with patch.object(manager.auth, 'test_connection', return_value=mock_auth_test):
            with patch.object(manager.account, 'get_accounts', return_value=mock_accounts):
                with patch.object(manager.market_data, 'get_quotes', return_value=mock_quotes):
                    with patch.object(manager.orders, 'place_order', return_value=mock_order_result):
                        
                        # Step 1: Initialize
                        init_result = await manager.initialize()
                        assert init_result["status"] == "success"
                        
                        # Step 2: Execute alert
                        alert_result = await manager.execute_alert({
                            "symbol": "ES",
                            "action": "buy", 
                            "quantity": 1
                        })
                        assert alert_result["status"] == "success"
                        
                        # Step 3: Clean up
                        await manager.close()
    
    @pytest_asyncio.async_test
    async def test_concurrent_alert_processing(self, mock_tradovate_manager):
        """Test processing multiple alerts concurrently"""
        manager = mock_tradovate_manager
        
        alerts = [
            {"symbol": "ES", "action": "buy", "quantity": 1},
            {"symbol": "NQ", "action": "sell", "quantity": 1},
            {"symbol": "YM", "action": "buy", "quantity": 2}
        ]
        
        mock_order_result = MagicMock(is_filled=True, order_id=98765)
        
        with patch.object(manager.orders, 'place_order', return_value=mock_order_result):
            # Process alerts concurrently
            results = await asyncio.gather(*[
                manager.execute_alert(alert) for alert in alerts
            ])
            
            # All should succeed
            assert len(results) == 3
            assert all(result["status"] == "success" for result in results)
    
    @pytest_asyncio.async_test
    async def test_error_recovery_workflow(self, mock_tradovate_manager):
        """Test error recovery in trading workflow"""
        manager = mock_tradovate_manager
        
        # First alert succeeds
        mock_success_result = MagicMock(is_filled=True, order_id=98765)
        
        # Second alert fails
        mock_failure = Exception("Order rejected")
        
        with patch.object(manager.orders, 'place_order', side_effect=[mock_success_result, mock_failure]):
            # First alert should succeed
            result1 = await manager.execute_alert({
                "symbol": "ES", "action": "buy", "quantity": 1
            })
            assert result1["status"] == "success"
            
            # Second alert should fail gracefully
            result2 = await manager.execute_alert({
                "symbol": "NQ", "action": "buy", "quantity": 1
            })
            assert result2["status"] == "error"
            assert "Order rejected" in result2["message"]