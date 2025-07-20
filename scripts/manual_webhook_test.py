#!/usr/bin/env python3
"""
Manual Webhook Test Script

This script allows manual testing of the TradingView webhook endpoint
with various alert scenarios. Useful for development and debugging.
"""

import json
import hmac
import hashlib
import time
import argparse
from typing import Dict, Any

import httpx


class WebhookTester:
    """Manual webhook testing utility"""
    
    def __init__(self, webhook_url: str = "http://localhost:8000/webhook/tradingview", 
                 webhook_secret: str = "test_webhook_secret"):
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        
    def generate_signature(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        return hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def create_alert(self, **kwargs) -> Dict[str, Any]:
        """Create a TradingView alert with default values"""
        default_alert = {
            "symbol": "ES",
            "action": "buy",
            "quantity": 1,
            "order_type": "market",
            "strategy": "manual_test",
            "account_group": "main",
            "comment": f"Manual test at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        default_alert.update(kwargs)
        return default_alert
    
    async def send_webhook(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook alert to the server"""
        payload = json.dumps(alert_data)
        signature = self.generate_signature(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    content=payload,
                    headers=headers
                )
                
                return {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code < 500 else response.text,
                    "success": response.status_code == 200
                }
                
            except httpx.RequestError as e:
                return {
                    "status_code": 0,
                    "response": f"Connection error: {e}",
                    "success": False
                }
    
    async def test_basic_buy_alert(self):
        """Test basic buy alert"""
        print("🔸 Testing basic buy alert...")
        alert = self.create_alert(
            symbol="ES",
            action="buy",
            quantity=1
        )
        
        result = await self.send_webhook(alert)
        self._print_result("Basic Buy Alert", result, alert)
        return result
    
    async def test_sell_alert(self):
        """Test sell alert"""
        print("🔸 Testing sell alert...")
        alert = self.create_alert(
            symbol="NQ",
            action="sell",
            quantity=2
        )
        
        result = await self.send_webhook(alert)
        self._print_result("Sell Alert", result, alert)
        return result
    
    async def test_close_position_alert(self):
        """Test close position alert"""
        print("🔸 Testing close position alert...")
        alert = self.create_alert(
            symbol="ES",
            action="close",
            quantity=1
        )
        
        result = await self.send_webhook(alert)
        self._print_result("Close Position Alert", result, alert)
        return result
    
    async def test_funded_account_alert(self):
        """Test funded account alert"""
        print("🔸 Testing funded account alert...")
        alert = self.create_alert(
            symbol="ES",
            action="buy",
            quantity=1,
            account_group="topstep",
            strategy="funded_momentum"
        )
        
        result = await self.send_webhook(alert)
        self._print_result("Funded Account Alert", result, alert)
        return result
    
    async def test_limit_order_alert(self):
        """Test limit order alert"""
        print("🔸 Testing limit order alert...")
        alert = self.create_alert(
            symbol="ES",
            action="buy",
            quantity=1,
            order_type="limit",
            price=4450.25
        )
        
        result = await self.send_webhook(alert)
        self._print_result("Limit Order Alert", result, alert)
        return result
    
    async def test_invalid_signature(self):
        """Test webhook with invalid signature"""
        print("🔸 Testing invalid signature (should fail)...")
        alert = self.create_alert()
        payload = json.dumps(alert)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": "invalid_signature_12345"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    content=payload,
                    headers=headers
                )
                
                result = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code < 500 else response.text,
                    "success": response.status_code == 200
                }
                
            except httpx.RequestError as e:
                result = {
                    "status_code": 0,
                    "response": f"Connection error: {e}",
                    "success": False
                }
        
        self._print_result("Invalid Signature Test", result, alert)
        return result
    
    async def test_malformed_alert(self):
        """Test malformed alert (should fail)"""
        print("🔸 Testing malformed alert (should fail)...")
        invalid_alert = {"invalid": "data", "missing": "required_fields"}
        payload = json.dumps(invalid_alert)
        signature = self.generate_signature(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    content=payload,
                    headers=headers
                )
                
                result = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code < 500 else response.text,
                    "success": response.status_code == 200
                }
                
            except httpx.RequestError as e:
                result = {
                    "status_code": 0,
                    "response": f"Connection error: {e}",
                    "success": False
                }
        
        self._print_result("Malformed Alert Test", result, invalid_alert)
        return result
    
    async def test_server_status(self):
        """Test if server is running"""
        print("🔸 Testing server status...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Test health endpoint
                health_response = await client.get("http://localhost:8000/health")
                health_data = health_response.json()
                
                # Test webhook test endpoint
                webhook_test_response = await client.get("http://localhost:8000/webhook/test")
                webhook_test_data = webhook_test_response.json()
                
                print(f"   Health Status: {health_data.get('status', 'unknown')}")
                print(f"   Tradovate Connected: {health_data.get('tradovate_connected', False)}")
                print(f"   Active Connections: {health_data.get('active_connections', 0)}")
                print(f"   Webhook Status: {webhook_test_data.get('status', 'unknown')}")
                
                return {
                    "health": health_data,
                    "webhook_test": webhook_test_data,
                    "server_running": True
                }
                
            except httpx.RequestError as e:
                print(f"   ❌ Server not accessible: {e}")
                return {
                    "server_running": False,
                    "error": str(e)
                }
    
    def _print_result(self, test_name: str, result: Dict[str, Any], alert_data: Dict[str, Any]):
        """Print formatted test result"""
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"   {status} - {test_name}")
        print(f"   Status Code: {result['status_code']}")
        
        if result["success"]:
            response = result["response"]
            print(f"   Alert ID: {response.get('alert_id', 'N/A')}")
            print(f"   Message: {response.get('message', 'N/A')}")
        else:
            print(f"   Error: {result['response']}")
        
        print(f"   Sent: {alert_data['symbol']} {alert_data['action']} {alert_data.get('quantity', 'N/A')}")
        print()
    
    async def run_all_tests(self):
        """Run all webhook tests"""
        print("🚀 Starting comprehensive webhook testing...")
        print("=" * 60)
        
        # Check server status first
        server_status = await self.test_server_status()
        if not server_status.get("server_running"):
            print("❌ Server is not running. Please start the backend server first:")
            print("   cd src/backend && uv run uvicorn src.backend.datahub.server:app --reload")
            return False
        
        print()
        
        # Run all tests
        tests = [
            self.test_basic_buy_alert(),
            self.test_sell_alert(),
            self.test_close_position_alert(),
            self.test_funded_account_alert(),
            self.test_limit_order_alert(),
            self.test_invalid_signature(),
            self.test_malformed_alert()
        ]
        
        results = []
        for test in tests:
            result = await test
            results.append(result)
        
        # Summary
        print("=" * 60)
        successful_tests = len([r for r in results if r.get("success")])
        total_tests = len(results)
        
        print(f"📊 Test Summary: {successful_tests}/{total_tests} tests passed")
        
        if successful_tests == total_tests - 2:  # Expecting 2 failures (invalid signature, malformed)
            print("🎉 All expected tests passed! Webhook system is working correctly.")
            return True
        else:
            print("⚠️  Some unexpected test failures occurred.")
            return False


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Manual TradingView webhook testing")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000/webhook/tradingview",
        help="Webhook URL (default: http://localhost:8000/webhook/tradingview)"
    )
    parser.add_argument(
        "--secret",
        default="test_webhook_secret",
        help="Webhook secret (default: test_webhook_secret)"
    )
    parser.add_argument(
        "--test",
        choices=["all", "buy", "sell", "close", "funded", "limit", "status"],
        default="all",
        help="Specific test to run (default: all)"
    )
    
    args = parser.parse_args()
    
    tester = WebhookTester(args.url, args.secret)
    
    if args.test == "all":
        success = await tester.run_all_tests()
        exit(0 if success else 1)
    elif args.test == "buy":
        result = await tester.test_basic_buy_alert()
    elif args.test == "sell":
        result = await tester.test_sell_alert()
    elif args.test == "close":
        result = await tester.test_close_position_alert()
    elif args.test == "funded":
        result = await tester.test_funded_account_alert()
    elif args.test == "limit":
        result = await tester.test_limit_order_alert()
    elif args.test == "status":
        result = await tester.test_server_status()
        print(f"Server Status: {result}")
        return
    
    exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())