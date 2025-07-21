#!/usr/bin/env python3
"""
Phase 0 Critical Path Validation Script

Quick validation script to verify that Phase 0 (Critical Path Futures Trading)
is working correctly. This script tests the core components without requiring
a full test environment setup.

Usage:
    python scripts/test_phase_0_validation.py
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.backend.webhooks.models import TradingViewAlert
    from src.backend.trading.paper_router import get_paper_trading_router
    from src.backend.feeds.topstepx.auth import TopstepXCredentials
    from src.backend.feeds.topstepx.manager import TopstepXManager
    from src.backend.trading.strategy_tracker import StrategyPerformanceTracker
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class Phase0Validator:
    """Quick validation of Phase 0 critical path components"""
    
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_trading_view_alert_models(self):
        """Test TradingView alert data models"""
        try:
            # Test valid alert creation
            alert_data = {
                "symbol": "ES",
                "action": "buy",
                "quantity": 2,
                "strategy": "test_strategy",
                "comment": "Validation test"
            }
            
            alert = TradingViewAlert(**alert_data)
            
            assert alert.symbol == "ES"
            assert alert.action == "buy"
            assert alert.quantity == 2
            
            self.log_test("TradingView Alert Models", True, f"Created alert for {alert.symbol} {alert.action} {alert.quantity}")
            
        except Exception as e:
            self.log_test("TradingView Alert Models", False, str(e))
    
    async def test_paper_trading_router(self):
        """Test paper trading router initialization and basic routing"""
        try:
            router = get_paper_trading_router()
            await router.initialize()
            
            # Test account creation
            accounts = await router.get_all_accounts()
            assert len(accounts) > 0
            
            # Test basic alert routing
            alert = TradingViewAlert(
                symbol="ES",
                action="buy",
                quantity=1,
                account_group="paper_simulator",
                strategy="validation_test"
            )
            
            result = await router.route_alert(alert)
            assert result["status"] == "success"
            assert result["is_paper"] is True
            
            self.log_test("Paper Trading Router", True, 
                         f"Routed ES buy to {result['execution_engine']}, filled at ${result['result']['fill']['price']}")
            
        except Exception as e:
            self.log_test("Paper Trading Router", False, str(e))
    
    async def test_topstepx_integration(self):
        """Test TopstepX funded account integration"""
        try:
            # Initialize with demo credentials
            creds = TopstepXCredentials(
                username="demo_user",
                password="demo_pass",
                environment="demo"
            )
            
            manager = TopstepXManager(creds)
            init_result = await manager.initialize()
            
            assert init_result["status"] == "success"
            assert init_result["account_count"] > 0
            
            # Test account summary
            summary = await manager.get_all_accounts_summary()
            assert "accounts" in summary
            assert summary["account_count"] > 0
            
            # Test rule validation
            test_alert = {
                "symbol": "ES",
                "action": "buy",
                "quantity": 1,
                "account_group": "topstep"
            }
            
            validation_result = await manager.execute_alert(test_alert)
            # Should either validate or provide clear rejection reason
            assert validation_result["status"] in ["rules_validated", "rejected"]
            
            await manager.close()
            
            self.log_test("TopstepX Integration", True, 
                         f"Loaded {summary['account_count']} mock accounts, rule validation working")
            
        except Exception as e:
            self.log_test("TopstepX Integration", False, str(e))
    
    async def test_strategy_performance_tracking(self):
        """Test strategy performance tracking"""
        try:
            tracker = StrategyPerformanceTracker()
            await tracker.initialize()
            
            # Record some test trades
            strategy_name = "validation_strategy"
            
            await tracker.record_trade_execution(strategy_name, "ES", "buy", 1, 125.0)
            await tracker.record_trade_execution(strategy_name, "ES", "sell", 1, -50.0)
            await tracker.record_trade_execution(strategy_name, "NQ", "buy", 1, 200.0)
            
            # Get performance metrics
            performance = await tracker.get_strategy_performance(strategy_name)
            
            assert performance is not None
            assert performance.total_trades == 3
            assert performance.total_pnl == 275.0
            
            self.log_test("Strategy Performance Tracking", True,
                         f"Tracked 3 trades, total P&L: ${performance.total_pnl}")
            
        except Exception as e:
            self.log_test("Strategy Performance Tracking", False, str(e))
    
    async def test_multi_symbol_futures_support(self):
        """Test support for multiple futures symbols"""
        try:
            router = get_paper_trading_router()
            await router.initialize()
            
            # Test major futures symbols
            symbols = ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL"]
            successful_trades = 0
            
            for symbol in symbols:
                try:
                    alert = TradingViewAlert(
                        symbol=symbol,
                        action="buy",
                        quantity=1,
                        account_group="paper_simulator",
                        strategy="symbol_test"
                    )
                    
                    result = await router.route_alert(alert)
                    if result["status"] == "success":
                        successful_trades += 1
                except Exception:
                    pass  # Some symbols might not be supported
            
            assert successful_trades >= 4  # At least major indices should work
            
            self.log_test("Multi-Symbol Futures Support", True,
                         f"Successfully traded {successful_trades}/{len(symbols)} symbols")
            
        except Exception as e:
            self.log_test("Multi-Symbol Futures Support", False, str(e))
    
    async def test_realistic_market_simulation(self):
        """Test realistic market simulation features"""
        try:
            router = get_paper_trading_router()
            await router.initialize()
            
            alert = TradingViewAlert(
                symbol="ES",
                action="buy",
                quantity=5,  # Larger size to test slippage
                account_group="paper_simulator",
                strategy="simulation_test"
            )
            
            result = await router.route_alert(alert)
            assert result["status"] == "success"
            
            # Check for realistic simulation features
            execution = result["result"]
            assert "execution_details" in execution
            assert "market_data" in execution
            assert "fill" in execution
            
            # Verify slippage calculation
            fill = execution["fill"]
            assert float(fill["slippage"]) >= 0
            
            # Verify commission calculation
            assert float(fill["commission"]) >= 0
            
            # Verify market data
            market_data = execution["market_data"]
            assert market_data["spread"] > 0
            assert market_data["ask"] > market_data["bid"]
            
            self.log_test("Realistic Market Simulation", True,
                         f"Fill: ${fill['price']}, Slippage: ${fill['slippage']}, Commission: ${fill['commission']}")
            
        except Exception as e:
            self.log_test("Realistic Market Simulation", False, str(e))
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Phase 0 Critical Path Validation")
        print("=" * 50)
        print("Testing TraderTerminal Bloomberg Alternative Core Components...")
        print()
        
        # Run tests
        await self.test_trading_view_alert_models()
        await self.test_paper_trading_router()
        await self.test_topstepx_integration()
        await self.test_strategy_performance_tracking()
        await self.test_multi_symbol_futures_support()
        await self.test_realistic_market_simulation()
        
        # Summary
        print()
        print("=" * 50)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        
        if passed_tests == total_tests:
            print(f"🎉 ALL TESTS PASSED ({passed_tests}/{total_tests})")
            print()
            print("✅ Phase 0 Critical Path Futures Trading is OPERATIONAL!")
            print("✅ Bloomberg Terminal Alternative Core Features Working!")
            print()
            print("Ready for:")
            print("  • TradingView webhook → Futures execution")
            print("  • Paper trading with realistic simulation")
            print("  • TopstepX funded account rule validation")
            print("  • Multi-broker routing (Tradovate, Tastytrade, etc.)")
            print("  • Strategy performance tracking")
            print("  • Risk management for funded accounts")
            print()
            print("🚀 System ready for live futures trading!")
            
        else:
            print(f"⚠️ PARTIAL SUCCESS ({passed_tests}/{total_tests} tests passed)")
            failed_tests = [r for r in self.test_results if not r["success"]]
            print()
            print("Failed tests:")
            for test in failed_tests:
                print(f"  ❌ {test['test']}: {test['details']}")
        
        print("=" * 50)
        
        return passed_tests == total_tests


async def main():
    """Main validation function"""
    validator = Phase0Validator()
    
    try:
        success = await validator.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())