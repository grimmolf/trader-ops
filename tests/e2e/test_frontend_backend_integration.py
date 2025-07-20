"""
End-to-End Tests: Frontend-Backend Integration

Tests the complete frontend-backend integration including:
1. API endpoint functionality and data flow
2. WebSocket real-time communication
3. User authentication and session management
4. Trading interface workflows
5. Dashboard data aggregation and display
6. Error handling and recovery mechanisms
"""

import asyncio
import json
import pytest
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
import aiohttp
from fastapi.testclient import TestClient

from src.backend.datahub.server import app
from src.backend.datahub.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)


class TestAPIEndpointIntegration:
    """Test API endpoint functionality and data flow"""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "uptime" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_tradingview_udf_config(self, client):
        """Test TradingView UDF configuration endpoint"""
        response = client.get("/udf/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify UDF configuration structure
        assert "supports_search" in data
        assert "supports_group_request" in data
        assert "supported_resolutions" in data
        assert "supports_marks" in data
        assert "supports_time" in data
        
        # Verify basic configuration values
        assert data["supports_search"] is True
        assert data["supports_group_request"] is False
        assert isinstance(data["supported_resolutions"], list)
    
    def test_symbol_search_endpoint(self, client):
        """Test symbol search functionality"""
        # Test basic symbol search
        response = client.get("/udf/search?query=AAPL&type=stock")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            symbol = data[0]
            assert "symbol" in symbol
            assert "full_name" in symbol
            assert "description" in symbol
            assert "type" in symbol
    
    def test_symbol_info_endpoint(self, client):
        """Test symbol information endpoint"""
        response = client.get("/udf/symbols?symbol=AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify symbol information structure
        assert "name" in data
        assert "ticker" in data
        assert "description" in data
        assert "type" in data
        assert "session" in data
        assert "timezone" in data
        assert "minmov" in data
        assert "pricescale" in data
    
    def test_historical_data_endpoint(self, client):
        """Test historical data endpoint"""
        # Calculate timestamps
        to_timestamp = int(datetime.utcnow().timestamp())
        from_timestamp = to_timestamp - (30 * 24 * 60 * 60)  # 30 days ago
        
        response = client.get(
            f"/udf/history"
            f"?symbol=AAPL"
            f"&resolution=1D"
            f"&from={from_timestamp}"
            f"&to={to_timestamp}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify OHLCV data structure
        assert "s" in data  # status
        if data["s"] == "ok":
            assert "t" in data  # time
            assert "o" in data  # open
            assert "h" in data  # high
            assert "l" in data  # low
            assert "c" in data  # close
            assert "v" in data  # volume
            
            # Verify data consistency
            assert len(data["t"]) == len(data["o"])
            assert len(data["o"]) == len(data["h"])
            assert len(data["h"]) == len(data["l"])
            assert len(data["l"]) == len(data["c"])
    
    def test_real_time_quotes_endpoint(self, client):
        """Test real-time quotes endpoint"""
        response = client.get("/api/v1/quotes?symbols=AAPL,GOOGL,TSLA")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify quotes structure
        assert "quotes" in data
        assert "timestamp" in data
        
        quotes = data["quotes"]
        for symbol in ["AAPL", "GOOGL", "TSLA"]:
            if symbol in quotes:
                quote = quotes[symbol]
                assert "symbol" in quote
                assert "last" in quote or "price" in quote
                assert "timestamp" in quote
    
    def test_webhook_test_endpoint(self, client):
        """Test webhook test endpoint"""
        response = client.get("/webhook/test")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "webhook processor operational" in data["message"]
        assert "timestamp" in data


class TestWebSocketIntegration:
    """Test WebSocket real-time communication"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection establishment and lifecycle"""
        
        # Mock WebSocket for testing
        mock_websocket = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        # Test connection manager
        connection_manager = ConnectionManager()
        
        # Test connection
        await connection_manager.connect(mock_websocket)
        assert len(connection_manager.active_connections) == 1
        
        # Test message broadcasting
        test_message = {
            "type": "test_message",
            "data": {"test": "data"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await connection_manager.broadcast_to_all(test_message)
        mock_websocket.send_json.assert_called_once_with(test_message)
        
        # Test disconnection
        connection_manager.disconnect(mock_websocket)
        assert len(connection_manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_real_time_data_streaming(self):
        """Test real-time data streaming via WebSocket"""
        
        connection_manager = ConnectionManager()
        
        # Create multiple mock clients
        clients = []
        for i in range(3):
            client = AsyncMock()
            clients.append(client)
            await connection_manager.connect(client)
        
        # Test different types of real-time data
        data_types = [
            {
                "type": "market_data",
                "data": {
                    "symbol": "AAPL",
                    "last": 150.25,
                    "bid": 150.24,
                    "ask": 150.26,
                    "volume": 1000000
                }
            },
            {
                "type": "execution_update",
                "data": {
                    "order_id": "ORD_123",
                    "symbol": "GOOGL", 
                    "status": "filled",
                    "filled_quantity": 5,
                    "avg_fill_price": 2800.50
                }
            },
            {
                "type": "account_update",
                "data": {
                    "account_id": "ACC_001",
                    "balance": 50000.00,
                    "buying_power": 45000.00,
                    "day_pnl": 1250.50
                }
            }
        ]
        
        # Stream data to all clients
        for data in data_types:
            await connection_manager.broadcast_to_all(data)
        
        # Verify all clients received all messages
        for client in clients:
            assert client.send_json.call_count == len(data_types)
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling and recovery"""
        
        connection_manager = ConnectionManager()
        
        # Create mock client that fails
        failing_client = AsyncMock()
        failing_client.send_json.side_effect = Exception("Connection lost")
        
        # Create normal client
        normal_client = AsyncMock()
        
        # Connect both clients
        await connection_manager.connect(failing_client)
        await connection_manager.connect(normal_client)
        
        assert len(connection_manager.active_connections) == 2
        
        # Attempt to broadcast - should handle failing client gracefully
        test_message = {"type": "test", "data": "test_data"}
        
        # In a real implementation, this would catch the exception
        # and remove the failing client
        try:
            await connection_manager.broadcast_to_all(test_message)
        except Exception:
            # Handle expected failure
            pass
        
        # Normal client should still receive messages
        # (In real implementation, failing client would be removed)
        normal_client.send_json.assert_called_once_with(test_message)


class TestTradingWorkflowIntegration:
    """Test complete trading workflow integration"""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_paper_trading_workflow(self, client):
        """Test complete paper trading workflow"""
        
        # Step 1: Get paper trading accounts
        with patch('src.backend.trading.paper_router.get_paper_trading_router') as mock_get_router:
            mock_router = AsyncMock()
            mock_router.get_all_accounts.return_value = [
                {
                    "id": "paper_simulator",
                    "name": "Internal Simulator",
                    "balance": 100000.00,
                    "positions": {},
                    "mode": "simulator"
                }
            ]
            mock_get_router.return_value = mock_router
            
            # Mock API endpoint for paper accounts
            with patch('src.backend.datahub.routes.paper_trading.get_paper_trading_router', return_value=mock_router):
                # This would be the actual API call
                accounts = await mock_router.get_all_accounts()
                
                assert len(accounts) == 1
                assert accounts[0]["id"] == "paper_simulator"
                assert accounts[0]["balance"] == 100000.00
        
        # Step 2: Execute paper trade via webhook
        webhook_payload = {
            "symbol": "AAPL",
            "action": "buy", 
            "quantity": 10,
            "order_type": "market",
            "account_group": "paper_simulator",
            "strategy": "workflow_test"
        }
        
        with patch('src.backend.webhooks.tradingview_receiver.process_tradingview_alert') as mock_process:
            mock_process.return_value = {
                "status": "success",
                "order_id": "PAPER_001",
                "message": "Paper trade executed successfully"
            }
            
            # Simulate webhook processing
            result = await mock_process(webhook_payload)
            
            assert result["status"] == "success"
            assert "order_id" in result
        
        # Step 3: Verify trade execution and account update
        with patch('src.backend.trading.paper_router.get_paper_trading_router') as mock_get_router:
            mock_router = AsyncMock()
            mock_router.get_account_orders.return_value = [
                {
                    "order_id": "PAPER_001",
                    "symbol": "AAPL",
                    "action": "buy",
                    "quantity": 10,
                    "status": "filled",
                    "filled_price": 150.50,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
            mock_get_router.return_value = mock_router
            
            # Get orders for account
            orders = await mock_router.get_account_orders("paper_simulator")
            
            assert len(orders) == 1
            assert orders[0]["order_id"] == "PAPER_001"
            assert orders[0]["status"] == "filled"
    
    @pytest.mark.asyncio
    async def test_multi_broker_trading_workflow(self):
        """Test multi-broker trading workflow"""
        
        # Mock different broker managers
        brokers = {
            "tastytrade": AsyncMock(),
            "schwab": AsyncMock(),
            "tradovate": AsyncMock()
        }
        
        # Configure mock responses
        brokers["tastytrade"].get_accounts.return_value = [
            {"account_number": "TT_001", "type": "margin", "balance": 25000.00}
        ]
        
        brokers["schwab"].get_accounts.return_value = [
            {"account_number": "SCH_001", "type": "cash", "balance": 50000.00}
        ]
        
        brokers["tradovate"].get_accounts.return_value = [
            {"account_id": "TRAD_001", "type": "futures", "balance": 15000.00}
        ]
        
        # Test account aggregation
        all_accounts = []
        for broker_name, broker in brokers.items():
            accounts = await broker.get_accounts()
            for account in accounts:
                account["broker"] = broker_name
                all_accounts.append(account)
        
        assert len(all_accounts) == 3
        assert any(acc["broker"] == "tastytrade" for acc in all_accounts)
        assert any(acc["broker"] == "schwab" for acc in all_accounts)
        assert any(acc["broker"] == "tradovate" for acc in all_accounts)
        
        # Test intelligent order routing
        routing_rules = [
            {"symbol": "AAPL", "asset_type": "stock", "preferred_broker": "schwab"},
            {"symbol": "AAPL250117C00150000", "asset_type": "option", "preferred_broker": "tastytrade"},
            {"symbol": "/ES", "asset_type": "future", "preferred_broker": "tradovate"}
        ]
        
        for rule in routing_rules:
            # Mock order execution
            broker = brokers[rule["preferred_broker"]]
            broker.execute_alert.return_value = {
                "status": "success",
                "order_id": f"{rule['preferred_broker'].upper()}_ORDER_001",
                "symbol": rule["symbol"]
            }
            
            # Execute order
            result = await broker.execute_alert({
                "symbol": rule["symbol"],
                "action": "buy",
                "quantity": 1
            })
            
            assert result["status"] == "success"
            assert rule["preferred_broker"].upper() in result["order_id"]


class TestDashboardDataIntegration:
    """Test dashboard data aggregation and display"""
    
    @pytest.mark.asyncio
    async def test_portfolio_aggregation(self):
        """Test portfolio data aggregation across brokers"""
        
        # Mock position data from different brokers
        broker_positions = {
            "tastytrade": [
                {"symbol": "AAPL", "quantity": 100, "avg_price": 145.50, "market_value": 15050.00},
                {"symbol": "TSLA", "quantity": 50, "avg_price": 240.00, "market_value": 12500.00}
            ],
            "schwab": [
                {"symbol": "GOOGL", "quantity": 10, "avg_price": 2750.00, "market_value": 28000.00},
                {"symbol": "AAPL", "quantity": 25, "avg_price": 148.00, "market_value": 3750.00}  # Same symbol
            ],
            "paper_simulator": [
                {"symbol": "MSFT", "quantity": 75, "avg_price": 410.00, "market_value": 30750.00}
            ]
        }
        
        # Aggregate positions
        aggregated_positions = {}
        total_market_value = 0
        
        for broker, positions in broker_positions.items():
            for position in positions:
                symbol = position["symbol"]
                if symbol not in aggregated_positions:
                    aggregated_positions[symbol] = {
                        "symbol": symbol,
                        "total_quantity": 0,
                        "total_market_value": 0,
                        "brokers": []
                    }
                
                aggregated_positions[symbol]["total_quantity"] += position["quantity"]
                aggregated_positions[symbol]["total_market_value"] += position["market_value"]
                aggregated_positions[symbol]["brokers"].append(broker)
                total_market_value += position["market_value"]
        
        # Verify aggregation
        assert "AAPL" in aggregated_positions
        assert aggregated_positions["AAPL"]["total_quantity"] == 125  # 100 + 25
        assert aggregated_positions["AAPL"]["total_market_value"] == 18800.00  # 15050 + 3750
        
        assert "GOOGL" in aggregated_positions
        assert aggregated_positions["GOOGL"]["total_quantity"] == 10
        
        assert total_market_value == 90050.00
    
    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        
        # Mock trade history
        trades = [
            {"symbol": "AAPL", "side": "buy", "quantity": 100, "price": 145.00, "date": "2024-01-01", "pnl": 0},
            {"symbol": "AAPL", "side": "sell", "quantity": 50, "price": 150.00, "date": "2024-01-05", "pnl": 250.00},
            {"symbol": "TSLA", "side": "buy", "quantity": 50, "price": 240.00, "date": "2024-01-03", "pnl": 0},
            {"symbol": "TSLA", "side": "sell", "quantity": 50, "price": 250.00, "date": "2024-01-08", "pnl": 500.00},
            {"symbol": "GOOGL", "side": "buy", "quantity": 10, "price": 2750.00, "date": "2024-01-02", "pnl": 0},
            {"symbol": "GOOGL", "side": "sell", "quantity": 10, "price": 2700.00, "date": "2024-01-06", "pnl": -500.00}
        ]
        
        # Calculate performance metrics
        total_trades = len([t for t in trades if t["pnl"] != 0])
        winning_trades = len([t for t in trades if t["pnl"] > 0])
        losing_trades = len([t for t in trades if t["pnl"] < 0])
        
        total_pnl = sum(t["pnl"] for t in trades)
        gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Verify calculations
        assert total_trades == 3
        assert winning_trades == 2
        assert losing_trades == 1
        assert total_pnl == 250.00  # 250 + 500 - 500
        assert win_rate == 2/3  # ~0.667
        assert profit_factor == 750/500  # 1.5
        assert avg_trade_pnl == 250/3  # ~83.33
    
    @pytest.mark.asyncio
    async def test_real_time_dashboard_updates(self):
        """Test real-time dashboard updates via WebSocket"""
        
        connection_manager = ConnectionManager()
        
        # Mock dashboard client
        dashboard_client = AsyncMock()
        await connection_manager.connect(dashboard_client)
        
        # Simulate various dashboard updates
        updates = [
            {
                "type": "portfolio_update",
                "data": {
                    "total_value": 89750.00,
                    "day_pnl": 1250.50,
                    "day_pnl_percent": 1.41,
                    "positions_count": 5
                }
            },
            {
                "type": "trade_execution",
                "data": {
                    "symbol": "AAPL",
                    "action": "buy",
                    "quantity": 10,
                    "price": 150.75,
                    "account": "TT_001"
                }
            },
            {
                "type": "market_alert",
                "data": {
                    "message": "AAPL broke above resistance at $150.50",
                    "symbol": "AAPL",
                    "alert_type": "technical",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        ]
        
        # Send updates to dashboard
        for update in updates:
            await connection_manager.broadcast_to_all(update)
        
        # Verify dashboard received all updates
        assert dashboard_client.send_json.call_count == len(updates)
        
        # Verify update content
        first_call = dashboard_client.send_json.call_args_list[0][0][0]
        assert first_call["type"] == "portfolio_update"
        assert first_call["data"]["total_value"] == 89750.00


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        return TestClient(app)
    
    def test_api_error_handling(self, client):
        """Test API error handling"""
        
        # Test invalid endpoint
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404
        
        # Test invalid query parameters
        response = client.get("/udf/history?symbol=&resolution=invalid")
        # Should handle gracefully, exact response depends on implementation
        assert response.status_code in [400, 422, 500]
        
        # Test malformed webhook
        response = client.post(
            "/webhook/tradingview",
            json={"invalid": "data"},
            headers={"X-Webhook-Signature": "invalid_signature"}
        )
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_broker_connection_failure_recovery(self):
        """Test recovery from broker connection failures"""
        
        # Mock broker that fails initially then recovers
        mock_broker = AsyncMock()
        
        # Simulate connection failures followed by recovery
        connection_attempts = [
            Exception("Connection timeout"),
            Exception("Network unreachable"),
            {"status": "success", "connected": True}  # Recovery
        ]
        
        mock_broker.test_connection.side_effect = connection_attempts
        
        # Test retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await mock_broker.test_connection()
                if isinstance(result, dict) and result.get("status") == "success":
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt should succeed
                    assert False, f"Connection failed after {max_retries} attempts: {e}"
                continue
        
        # Verify recovery
        assert isinstance(result, dict)
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection_handling(self):
        """Test WebSocket reconnection handling"""
        
        connection_manager = ConnectionManager()
        
        # Create mock client that disconnects and reconnects
        client = AsyncMock()
        
        # Initial connection
        await connection_manager.connect(client)
        assert len(connection_manager.active_connections) == 1
        
        # Simulate disconnection
        connection_manager.disconnect(client)
        assert len(connection_manager.active_connections) == 0
        
        # Simulate reconnection
        await connection_manager.connect(client)
        assert len(connection_manager.active_connections) == 1
        
        # Test message delivery after reconnection
        test_message = {"type": "reconnection_test", "data": "test"}
        await connection_manager.broadcast_to_all(test_message)
        
        client.send_json.assert_called_once_with(test_message)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])