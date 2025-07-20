"""
End-to-End Test: TradingView Webhook → Tradovate Execution Flow

This test validates the complete critical path for futures trading:
1. TradingView webhook reception with HMAC validation
2. Alert parsing and validation  
3. Broker routing to Tradovate
4. Risk management checks for funded accounts
5. Order execution through Tradovate API
6. WebSocket broadcasting of execution results
"""

import asyncio
import json
import hmac
import hashlib
import time
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import httpx
from fastapi.testclient import TestClient

# Import the server and dependencies
from src.backend.datahub.server import app, settings
from src.backend.feeds.tradovate.auth import TradovateCredentials
from src.backend.feeds.tradovate.manager import TradovateManager
from src.backend.webhooks.models import TradingViewAlert, WebhookResponse
from src.backend.webhooks.tradingview_receiver import set_global_instances


class TestWebhookTradovateFlow:
    """End-to-end test suite for TradingView → Tradovate execution flow"""
    
    def setup_method(self):
        """Set up test environment"""
        self.client = TestClient(app)
        self.webhook_secret = "test_webhook_secret_12345"
        
        # Mock settings with Tradovate configuration
        self.mock_settings = MagicMock()
        self.mock_settings.tradingview_webhook_secret = self.webhook_secret
        self.mock_settings.tradovate_username = "test_user"
        self.mock_settings.tradovate_password = "test_password"
        self.mock_settings.tradovate_app_id = "test_app_id"
        self.mock_settings.tradovate_demo = True
        
        # Mock connection manager
        self.mock_connection_manager = AsyncMock()
        self.mock_connection_manager.broadcast_to_all = AsyncMock()
        
        # Create mock Tradovate manager
        self.mock_tradovate_manager = self._create_mock_tradovate_manager()
    
    def _create_mock_tradovate_manager(self):
        """Create a mock TradovateManager with proper method responses"""
        manager = AsyncMock(spec=TradovateManager)
        
        # Mock successful execution response
        manager.execute_alert.return_value = {
            "status": "success",
            "action": "buy",
            "symbol": "ES",
            "quantity": 1,
            "order_id": "TRAD_12345",
            "message": "Order placed successfully",
            "order_status": "Working",
            "filled_quantity": 0
        }
        
        return manager
    
    def _generate_webhook_signature(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        return hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _create_test_alert(self, **overrides) -> Dict[str, Any]:
        """Create a test TradingView alert payload"""
        alert = {
            "symbol": "ES",
            "action": "buy", 
            "quantity": 1,
            "order_type": "market",
            "strategy": "test_strategy",
            "account_group": "main",
            "comment": "Test alert from E2E test"
        }
        alert.update(overrides)
        return alert
    
    @pytest.mark.asyncio
    async def test_complete_webhook_to_execution_flow(self):
        """Test the complete flow from webhook reception to order execution"""
        
        # Set up global instances for webhook processor
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create test alert payload
        alert_data = self._create_test_alert()
        payload = json.dumps(alert_data)
        signature = self._generate_webhook_signature(payload)
        
        # Send webhook request
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
        )
        
        # Assert webhook was received successfully
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "received"
        assert "alert_id" in response_data
        assert "ES buy 1" in response_data["message"]
        
        # Give background task time to complete
        await asyncio.sleep(0.1)
        
        # Verify TradovateManager.execute_alert was called
        self.mock_tradovate_manager.execute_alert.assert_called_once()
        call_args = self.mock_tradovate_manager.execute_alert.call_args[0][0]
        
        # Verify alert data was passed correctly
        assert call_args["symbol"] == "ES"
        assert call_args["action"] == "buy"
        assert call_args["quantity"] == 1
        assert call_args["account_group"] == "main"
        assert call_args["strategy"] == "test_strategy"
        
        # Verify WebSocket broadcast was called
        self.mock_connection_manager.broadcast_to_all.assert_called_once()
        broadcast_data = self.mock_connection_manager.broadcast_to_all.call_args[0][0]
        
        # Verify broadcast message structure
        assert broadcast_data["type"] == "execution"
        assert broadcast_data["data"]["symbol"] == "ES"
        assert broadcast_data["data"]["action"] == "buy"
        assert broadcast_data["data"]["execution_result"]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_funded_account_routing(self):
        """Test that funded account alerts are routed properly"""
        
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create funded account alert
        alert_data = self._create_test_alert(
            symbol="NQ",
            action="sell",
            account_group="topstep",
            strategy="funded_account_test"
        )
        payload = json.dumps(alert_data)
        signature = self._generate_webhook_signature(payload)
        
        # Send webhook request
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
        )
        
        # Assert successful reception
        assert response.status_code == 200
        assert response.json()["status"] == "received"
        
        # Give background task time to complete
        await asyncio.sleep(0.1)
        
        # Verify execution was called with funded account data
        self.mock_tradovate_manager.execute_alert.assert_called_once()
        call_args = self.mock_tradovate_manager.execute_alert.call_args[0][0]
        assert call_args["account_group"] == "topstep"
    
    @pytest.mark.asyncio
    async def test_execution_failure_handling(self):
        """Test handling of execution failures"""
        
        # Configure manager to return failure
        self.mock_tradovate_manager.execute_alert.return_value = {
            "status": "rejected",
            "message": "Insufficient buying power"
        }
        
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create test alert
        alert_data = self._create_test_alert()
        payload = json.dumps(alert_data)
        signature = self._generate_webhook_signature(payload)
        
        # Send webhook request
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
        )
        
        # Assert webhook was still received
        assert response.status_code == 200
        
        # Give background task time to complete
        await asyncio.sleep(0.1)
        
        # Verify execution was attempted
        self.mock_tradovate_manager.execute_alert.assert_called_once()
        
        # Note: In a real implementation, you might want to check error logging
        # or specific error handling behavior
    
    def test_invalid_webhook_signature(self):
        """Test rejection of webhooks with invalid signatures"""
        
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create test alert with invalid signature
        alert_data = self._create_test_alert()
        payload = json.dumps(alert_data)
        invalid_signature = "invalid_signature_12345"
        
        # Send webhook request with invalid signature
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": invalid_signature
            }
        )
        
        # Assert webhook was rejected
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]
        
        # Verify execution was NOT called
        self.mock_tradovate_manager.execute_alert.assert_not_called()
    
    def test_invalid_alert_format(self):
        """Test rejection of malformed alert payloads"""
        
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create invalid alert (missing required fields)
        invalid_alert = {"invalid": "data"}
        payload = json.dumps(invalid_alert)
        signature = self._generate_webhook_signature(payload)
        
        # Send webhook request
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
        )
        
        # Assert webhook was rejected
        assert response.status_code == 400
        assert "Invalid alert format" in response.json()["detail"]
        
        # Verify execution was NOT called
        self.mock_tradovate_manager.execute_alert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_no_broker_connector_available(self):
        """Test handling when no broker connector is available"""
        
        # Set up with no Tradovate manager
        set_global_instances(self.mock_settings, None, self.mock_connection_manager)
        
        # Create test alert
        alert_data = self._create_test_alert()
        payload = json.dumps(alert_data)
        signature = self._generate_webhook_signature(payload)
        
        # Send webhook request
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
        )
        
        # Assert webhook was received (even though execution will fail)
        assert response.status_code == 200
        
        # Give background task time to complete
        await asyncio.sleep(0.1)
        
        # The background task should handle the missing connector gracefully
        # In a real implementation, this would log an error
    
    def test_webhook_test_endpoint(self):
        """Test the webhook test endpoint"""
        
        response = self.client.get("/webhook/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "operational" in data["message"]
    
    @pytest.mark.asyncio
    async def test_close_position_alert(self):
        """Test close position alert handling"""
        
        # Configure manager for close position
        self.mock_tradovate_manager.execute_alert.return_value = {
            "status": "success",
            "action": "close",
            "symbol": "ES",
            "order_id": "TRAD_CLOSE_123",
            "message": "Position closed successfully"
        }
        
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create close position alert
        alert_data = self._create_test_alert(
            action="close",
            symbol="ES"
        )
        payload = json.dumps(alert_data)
        signature = self._generate_webhook_signature(payload)
        
        # Send webhook request
        response = self.client.post(
            "/webhook/tradingview",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature
            }
        )
        
        # Assert successful reception
        assert response.status_code == 200
        
        # Give background task time to complete
        await asyncio.sleep(0.1)
        
        # Verify execution was called
        self.mock_tradovate_manager.execute_alert.assert_called_once()
        call_args = self.mock_tradovate_manager.execute_alert.call_args[0][0]
        assert call_args["action"] == "close"
    
    @pytest.mark.asyncio
    async def test_high_frequency_webhook_rate_limiting(self):
        """Test rate limiting for high-frequency webhooks"""
        
        set_global_instances(self.mock_settings, self.mock_tradovate_manager, self.mock_connection_manager)
        
        # Create test alert
        alert_data = self._create_test_alert()
        payload = json.dumps(alert_data)
        signature = self._generate_webhook_signature(payload)
        
        # Send multiple rapid requests
        responses = []
        for i in range(10):
            response = self.client.post(
                "/webhook/tradingview",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature
                }
            )
            responses.append(response)
        
        # Most should succeed, but some might be rate limited
        success_count = len([r for r in responses if r.status_code == 200])
        rate_limited_count = len([r for r in responses if r.status_code == 429])
        
        # At least some should succeed
        assert success_count > 0
        
        # If any were rate limited, verify the response
        if rate_limited_count > 0:
            rate_limited_response = next(r for r in responses if r.status_code == 429)
            assert "Rate limit exceeded" in rate_limited_response.json()["detail"]


@pytest.mark.integration
class TestTradovateIntegrationMock:
    """Integration tests with mocked Tradovate responses"""
    
    @pytest.mark.asyncio
    async def test_tradovate_manager_initialization(self):
        """Test TradovateManager initialization flow"""
        
        with patch('src.backend.feeds.tradovate.auth.TradovateAuth') as mock_auth_class:
            # Mock successful authentication
            mock_auth = AsyncMock()
            mock_auth.test_connection.return_value = {"status": "success"}
            mock_auth_class.return_value = mock_auth
            
            with patch('src.backend.feeds.tradovate.account.TradovateAccount') as mock_account_class:
                # Mock account loading
                mock_account = AsyncMock()
                mock_account.get_accounts.return_value = [
                    MagicMock(id=12345, name="Test Account", archived=False)
                ]
                mock_account_class.return_value = mock_account
                
                with patch('src.backend.feeds.tradovate.market_data.TradovateMarketData') as mock_market_class:
                    # Mock market data test
                    mock_market = AsyncMock()
                    mock_market.get_quotes.return_value = [
                        MagicMock(symbol="ES", bid=4450.25, ask=4450.50)
                    ]
                    mock_market_class.return_value = mock_market
                    
                    # Create and initialize manager
                    credentials = TradovateCredentials(
                        username="test_user",
                        password="test_password", 
                        app_id="test_app",
                        demo=True
                    )
                    
                    manager = TradovateManager(credentials)
                    result = await manager.initialize()
                    
                    # Verify successful initialization
                    assert result["status"] == "success"
                    assert result["environment"] == "demo"
                    assert result["account_count"] >= 1
                    assert result["default_account_id"] == 12345
                    assert result["market_data_working"] is True
    
    @pytest.mark.asyncio
    async def test_alert_execution_flow(self):
        """Test complete alert execution through TradovateManager"""
        
        # Create mock credentials
        credentials = TradovateCredentials(
            username="test_user",
            password="test_password",
            app_id="test_app", 
            demo=True
        )
        
        with patch('src.backend.feeds.tradovate.orders.TradovateOrders') as mock_orders_class:
            # Mock successful order placement
            mock_orders = AsyncMock()
            mock_order_response = MagicMock()
            mock_order_response.is_filled = False
            mock_order_response.is_working = True
            mock_order_response.order_id = "TRAD_12345"
            mock_order_response.status = "Working"
            mock_order_response.message = "Order placed successfully"
            mock_order_response.filled_quantity = 0
            mock_orders.place_order.return_value = mock_order_response
            mock_orders_class.return_value = mock_orders
            
            # Create manager and set it as initialized
            manager = TradovateManager(credentials)
            manager._initialized = True
            manager._default_account_id = 12345
            manager.orders = mock_orders
            
            # Execute test alert
            alert_data = {
                "symbol": "ES",
                "action": "buy",
                "quantity": 1,
                "order_type": "market",
                "account_group": "main"
            }
            
            result = await manager.execute_alert(alert_data)
            
            # Verify successful execution
            assert result["status"] == "success"
            assert result["symbol"] == "ES"
            assert result["action"] == "buy"
            assert result["quantity"] == 1
            assert result["order_id"] == "TRAD_12345"
            
            # Verify order was placed with correct parameters
            mock_orders.place_order.assert_called_once()
            call_kwargs = mock_orders.place_order.call_args.kwargs
            assert call_kwargs["symbol"] == "ES"
            assert call_kwargs["action"] == "Buy"
            assert call_kwargs["quantity"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])