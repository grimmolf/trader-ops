"""
End-to-End Tests: Paper Trading Integration

Tests the complete paper trading system including:
1. Paper trading router initialization with broker sandbox integration
2. TradingView webhook → Paper trading execution
3. Multiple execution modes (simulator, sandbox, hybrid)
4. Performance tracking and analytics
5. Account management and position tracking
"""

import asyncio
import json
import pytest
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

from src.backend.trading.paper_router import PaperTradingRouter, get_paper_trading_router
from src.backend.trading.paper_models import PaperTradingAlert, PaperTradingMode
from src.backend.feeds.tastytrade.manager import TastytradeManager
from src.backend.feeds.tradovate.manager import TradovateManager
from src.backend.feeds.tastytrade.auth import TastytradeCredentials
from src.backend.feeds.tradovate.auth import TradovateCredentials

logger = logging.getLogger(__name__)


class TestPaperTradingIntegration:
    """End-to-end paper trading integration tests"""
    
    @pytest.fixture
    async def paper_router(self):
        """Create and initialize paper trading router"""
        router = PaperTradingRouter()
        await router.initialize()
        return router
    
    @pytest.fixture
    def mock_tastytrade_manager(self):
        """Create mock TastytradeManager with execute_alert method"""
        manager = AsyncMock(spec=TastytradeManager)
        
        # Mock successful execution
        manager.execute_alert.return_value = {
            "status": "success",
            "order": {
                "id": "TT_12345",
                "status": "filled"
            },
            "fill": {
                "price": 150.50,
                "quantity": 10,
                "commission": 0.0,
                "slippage": 0.001
            },
            "execution": {
                "account": "test_account",
                "broker": "tastytrade_sandbox",
                "timestamp": datetime.utcnow().isoformat()
            },
            "message": "Tastytrade sandbox order executed: AAPL buy 10"
        }
        
        return manager
    
    @pytest.fixture
    def mock_tradovate_manager(self):
        """Create mock TradovateManager with execute_alert method"""
        manager = AsyncMock(spec=TradovateManager)
        
        # Mock successful execution
        manager.execute_alert.return_value = {
            "status": "success",
            "action": "buy",
            "symbol": "ES",
            "quantity": 1,
            "order_id": "TRAD_67890",
            "message": "Tradovate demo order executed"
        }
        
        return manager
    
    @pytest.mark.asyncio
    async def test_paper_router_initialization(self, paper_router):
        """Test paper trading router initialization"""
        
        # Verify router is initialized
        assert paper_router._initialized is True
        
        # Verify execution engines are available
        assert "simulator" in paper_router.execution_engines
        
        # Verify default accounts are created
        assert len(paper_router.accounts) > 0
        assert "paper_simulator" in paper_router.accounts
        
        # Verify simulator account is properly configured
        simulator_account = paper_router.accounts["paper_simulator"]
        assert simulator_account.mode == PaperTradingMode.SIMULATOR
        assert simulator_account.initial_balance == Decimal("100000")
    
    @pytest.mark.asyncio
    async def test_paper_trading_alert_routing(self, paper_router):
        """Test routing of paper trading alerts"""
        
        # Create test alert
        alert = PaperTradingAlert(
            symbol="AAPL",
            action="buy",
            quantity=10,
            account_group="paper_simulator",
            strategy="test_strategy",
            comment="E2E test alert"
        )
        
        # Route alert
        result = await paper_router.route_alert(alert)
        
        # Verify successful routing
        assert result["status"] == "success"
        assert result["is_paper"] is True
        assert result["execution_engine"] == "simulator"
        assert result["account_id"] == "paper_simulator"
        
        # Verify order was created
        assert "order_id" in result
        assert "order" in result
        
        # Verify order details
        order = result["order"]
        assert order["symbol"] == "AAPL"
        assert order["action"] == "buy"
        assert order["quantity"] == 10
    
    @pytest.mark.asyncio
    async def test_broker_sandbox_integration(self, paper_router, mock_tastytrade_manager):
        """Test integration with broker sandbox environments"""
        
        # Add mock Tastytrade manager to execution engines
        paper_router.execution_engines["tastytrade_sandbox"] = mock_tastytrade_manager
        
        # Create alert targeting Tastytrade sandbox
        alert = PaperTradingAlert(
            symbol="AAPL",
            action="buy",
            quantity=10,
            account_group="paper_tastytrade",  # Routes to Tastytrade
            strategy="sandbox_test",
            comment="Testing broker sandbox integration"
        )
        
        # Add Tastytrade account
        from src.backend.trading.paper_models import PaperTradingAccount
        tastytrade_account = PaperTradingAccount(
            id="paper_tastytrade",
            name="Tastytrade Sandbox",
            broker="tastytrade_sandbox",
            mode=PaperTradingMode.SANDBOX,
            initial_balance=Decimal("100000")
        )
        paper_router.accounts["paper_tastytrade"] = tastytrade_account
        
        # Route alert
        result = await paper_router.route_alert(alert)
        
        # Verify successful execution through sandbox
        assert result["status"] == "success"
        assert result["execution_engine"] == "tastytrade_sandbox"
        assert result["account_id"] == "paper_tastytrade"
        
        # Verify TastytradeManager.execute_alert was called
        mock_tastytrade_manager.execute_alert.assert_called_once()
        
        # Verify result includes broker execution details
        assert "result" in result
        broker_result = result["result"]
        assert broker_result["execution"]["broker"] == "tastytrade_sandbox"
    
    @pytest.mark.asyncio
    async def test_auto_broker_routing(self, paper_router, mock_tradovate_manager):
        """Test automatic broker routing based on symbol type"""
        
        # Add mock Tradovate manager
        paper_router.execution_engines["tradovate_demo"] = mock_tradovate_manager
        
        # Add Tradovate account
        from src.backend.trading.paper_models import PaperTradingAccount
        tradovate_account = PaperTradingAccount(
            id="paper_tradovate",
            name="Tradovate Demo",
            broker="tradovate_demo",
            mode=PaperTradingMode.SANDBOX,
            initial_balance=Decimal("50000")
        )
        paper_router.accounts["paper_tradovate"] = tradovate_account
        
        # Create futures alert (should auto-route to Tradovate)
        alert = PaperTradingAlert(
            symbol="ES",  # Futures symbol
            action="buy",
            quantity=1,
            account_group="paper_auto",  # Auto routing
            strategy="futures_test",
            comment="Testing auto-routing for futures"
        )
        
        # Route alert
        result = await paper_router.route_alert(alert)
        
        # Verify routing to Tradovate for futures
        assert result["status"] == "success"
        assert result["execution_engine"] == "tradovate_demo"
        assert result["account_id"] == "paper_tradovate"
        
        # Verify TradovateManager.execute_alert was called
        mock_tradovate_manager.execute_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_execution_modes(self, paper_router):
        """Test different paper trading execution modes"""
        
        test_cases = [
            {
                "account_id": "paper_simulator",
                "mode": PaperTradingMode.SIMULATOR,
                "expected_engine": "simulator"
            },
            {
                "account_id": "paper_hybrid",
                "mode": PaperTradingMode.HYBRID,
                "expected_engine": "simulator"  # Falls back to simulator
            }
        ]
        
        for case in test_cases:
            alert = PaperTradingAlert(
                symbol="TSLA",
                action="sell",
                quantity=5,
                account_group=case["account_id"],
                strategy=f"test_{case['mode'].value}",
                comment=f"Testing {case['mode'].value} mode"
            )
            
            result = await paper_router.route_alert(alert)
            
            assert result["status"] == "success"
            assert result["execution_engine"] == case["expected_engine"]
            assert result["account_id"] == case["account_id"]
    
    @pytest.mark.asyncio
    async def test_position_management(self, paper_router):
        """Test position management in paper trading"""
        
        account_id = "paper_simulator"
        symbol = "GOOGL"
        
        # Execute buy order
        buy_alert = PaperTradingAlert(
            symbol=symbol,
            action="buy",
            quantity=5,
            account_group=account_id,
            strategy="position_test",
            comment="Opening position"
        )
        
        buy_result = await paper_router.route_alert(buy_alert)
        assert buy_result["status"] == "success"
        
        # Check account positions
        account = await paper_router.get_account(account_id)
        assert symbol in account.positions
        
        position = account.positions[symbol]
        assert position.quantity == 5
        assert position.symbol == symbol
        
        # Execute partial sell order
        sell_alert = PaperTradingAlert(
            symbol=symbol,
            action="sell",
            quantity=2,
            account_group=account_id,
            strategy="position_test",
            comment="Partial close"
        )
        
        sell_result = await paper_router.route_alert(sell_alert)
        assert sell_result["status"] == "success"
        
        # Verify position updated
        updated_account = await paper_router.get_account(account_id)
        updated_position = updated_account.positions[symbol]
        assert updated_position.quantity == 3  # 5 - 2
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self, paper_router):
        """Test order cancellation in paper trading"""
        
        # Create and route an alert
        alert = PaperTradingAlert(
            symbol="NFLX",
            action="buy",
            quantity=3,
            order_type="limit",
            price=500.00,
            account_group="paper_simulator",
            strategy="cancel_test",
            comment="Order to be cancelled"
        )
        
        result = await paper_router.route_alert(alert)
        assert result["status"] == "success"
        
        order_id = result["order_id"]
        
        # Cancel the order
        cancel_result = await paper_router.cancel_order(order_id)
        
        assert cancel_result["status"] == "success"
        assert cancel_result["order_id"] == order_id
        
        # Verify order is in cancelled state
        assert order_id in paper_router.active_orders
        cancelled_order = paper_router.active_orders[order_id]
        assert cancelled_order.status.value == "cancelled"
    
    @pytest.mark.asyncio
    async def test_account_flattening(self, paper_router):
        """Test flattening all positions in an account"""
        
        account_id = "paper_simulator"
        
        # Build up multiple positions
        symbols = ["META", "AMZN", "NVDA"]
        
        for symbol in symbols:
            alert = PaperTradingAlert(
                symbol=symbol,
                action="buy",
                quantity=10,
                account_group=account_id,
                strategy="flatten_test",
                comment=f"Building position in {symbol}"
            )
            
            result = await paper_router.route_alert(alert)
            assert result["status"] == "success"
        
        # Verify positions exist
        account = await paper_router.get_account(account_id)
        for symbol in symbols:
            assert symbol in account.positions
            assert account.positions[symbol].quantity == 10
        
        # Flatten all positions
        flatten_result = await paper_router.flatten_account_positions(account_id)
        
        assert flatten_result["status"] == "success"
        assert flatten_result["account_id"] == account_id
        assert flatten_result["positions_closed"] == len(symbols)
        
        # Verify all positions are closed
        flattened_account = await paper_router.get_account(account_id)
        for symbol in symbols:
            if symbol in flattened_account.positions:
                assert flattened_account.positions[symbol].quantity == 0
    
    @pytest.mark.asyncio
    async def test_paper_trading_execute_alert_interface(self, paper_router):
        """Test paper trading router execute_alert interface compatibility"""
        
        # Create mock TradingView alert object
        class MockTradingViewAlert:
            def __init__(self):
                self.symbol = "MSFT"
                self.action = "buy"
                self.quantity = 15
                self.order_type = "market"
                self.price = None
                self.account_group = "paper_simulator"
                self.strategy = "interface_test"
                self.comment = "Testing execute_alert interface"
        
        mock_alert = MockTradingViewAlert()
        
        # Test execute_alert interface
        result = await paper_router.execute_alert(mock_alert)
        
        assert result["status"] == "success"
        assert "order" in result
        assert result["order"]["status"] == "filled"
        assert "execution" in result
        assert "message" in result
        
        # Verify message format
        assert "Paper trading order executed" in result["message"]
    
    @pytest.mark.asyncio
    async def test_global_paper_router_singleton(self):
        """Test global paper trading router singleton"""
        
        # Get router instances
        router1 = get_paper_trading_router()
        router2 = get_paper_trading_router()
        
        # Should be the same instance
        assert router1 is router2
        
        # Initialize if needed
        await router1.initialize()
        
        # Should be initialized
        assert router1._initialized is True
        assert router2._initialized is True


class TestPaperTradingPerformance:
    """Test paper trading performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_high_frequency_paper_trading(self):
        """Test high-frequency paper trading operations"""
        router = PaperTradingRouter()
        await router.initialize()
        
        symbols = ["SPY", "QQQ", "IWM", "VTI", "VEA"]
        
        # Execute many rapid trades
        start_time = datetime.utcnow()
        results = []
        
        for i in range(50):
            symbol = symbols[i % len(symbols)]
            action = "buy" if i % 2 == 0 else "sell"
            
            alert = PaperTradingAlert(
                symbol=symbol,
                action=action,
                quantity=1,
                account_group="paper_simulator",
                strategy="performance_test",
                comment=f"High frequency test {i}"
            )
            
            result = await router.route_alert(alert)
            results.append(result)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Verify all operations completed successfully
        successful_trades = len([r for r in results if r["status"] == "success"])
        assert successful_trades == 50
        
        # Performance check (should handle 50 trades quickly)
        assert duration < 2.0  # Less than 2 seconds
        
        # Verify no memory leaks (basic check)
        assert len(router.active_orders) == 50
        assert len(router.fills) == 50
    
    @pytest.mark.asyncio
    async def test_concurrent_paper_trading_operations(self):
        """Test concurrent paper trading operations"""
        router = PaperTradingRouter()
        await router.initialize()
        
        # Create concurrent tasks
        async def execute_trade(symbol, action, quantity):
            alert = PaperTradingAlert(
                symbol=symbol,
                action=action,
                quantity=quantity,
                account_group="paper_simulator",
                strategy="concurrent_test",
                comment=f"Concurrent {action} {symbol}"
            )
            return await router.route_alert(alert)
        
        # Execute concurrent trades
        tasks = [
            execute_trade("AAPL", "buy", 10),
            execute_trade("GOOGL", "sell", 5),
            execute_trade("MSFT", "buy", 15),
            execute_trade("TSLA", "sell", 3),
            execute_trade("NVDA", "buy", 8)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for result in results:
            assert result["status"] == "success"
            assert "order_id" in result
        
        # Verify unique order IDs
        order_ids = [r["order_id"] for r in results]
        assert len(set(order_ids)) == len(order_ids)  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])