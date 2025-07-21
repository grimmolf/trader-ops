#!/usr/bin/env python3
"""
Test script for paper trading engine - validates 100+ trades requirement
"""

import asyncio
import logging
from decimal import Decimal
from typing import List, Dict, Any
import random

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.trading.paper_engine import InternalPaperTradingEngine
from backend.trading.paper_models import (
    PaperOrder, PaperTradingAccount, OrderType, AssetType, 
    PaperTradingMode, OrderAction
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_comprehensive_paper_trading_tests():
    """Run comprehensive paper trading tests - 100+ trades requirement"""
    
    print("🚀 Starting Comprehensive Paper Trading Engine Tests...")
    print("📋 Target: Execute 100+ test trades for validation")
    
    # Initialize engine in testing mode (bypass market hours)
    engine = InternalPaperTradingEngine(testing_mode=True)
    await engine.initialize()
    
    # Create test account
    account = PaperTradingAccount(
        id="test_account_001",
        name="Comprehensive Test Account", 
        broker="simulator",
        mode=PaperTradingMode.SIMULATOR,
        initial_balance=Decimal("1000000"),  # $1M for testing
        current_balance=Decimal("1000000"),
        buying_power=Decimal("2000000")      # 2:1 leverage
    )
    
    # Test symbols across different asset classes
    test_symbols = {
        AssetType.FUTURE: ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL"],
        AssetType.STOCK: ["AAPL", "MSFT", "TSLA", "SPY", "QQQ"],
        AssetType.CRYPTO: ["BTC", "ETH"]
    }
    
    # Generate test orders
    test_orders = []
    target_trades = 120  # Exceed 100 requirement
    
    for i in range(target_trades):
        # Random asset type
        asset_type = random.choice(list(test_symbols.keys()))
        symbol = random.choice(test_symbols[asset_type])
        
        # Random order parameters
        action = random.choice([OrderAction.BUY, OrderAction.SELL])
        order_type = random.choice(list(OrderType))
        
        # Quantity based on asset type
        if asset_type == AssetType.FUTURE:
            quantity = Decimal(str(random.randint(1, 5)))
        elif asset_type == AssetType.STOCK:
            quantity = Decimal(str(random.randint(10, 500)))
        else:  # CRYPTO
            quantity = Decimal(str(round(random.uniform(0.1, 2.0), 2)))
        
        order = PaperOrder(
            symbol=symbol,
            quantity=quantity,
            order_type=order_type,
            action=action,
            asset_type=asset_type,
            account_id=account.id
        )
        test_orders.append(order)
    
    # Execute all orders
    successful_trades = 0
    failed_trades = 0
    total_commission = Decimal("0")
    total_slippage = Decimal("0")
    execution_times = []
    
    print(f"\n📊 Executing {len(test_orders)} test orders...")
    
    for i, order in enumerate(test_orders):
        if i % 20 == 0:  # Progress update every 20 trades
            print(f"  Progress: {i}/{len(test_orders)} trades executed")
        
        result = await engine.execute_paper_order(order, account)
        
        if result["status"] == "success":
            successful_trades += 1
            fill = result["fill"]
            execution = result["execution_details"]
            
            total_commission += Decimal(str(fill["commission"]))
            total_slippage += Decimal(str(fill["slippage"]))
            execution_times.append(execution["execution_delay_ms"])
        else:
            failed_trades += 1
            error_msg = result.get('message', result.get('reason', 'Unknown error'))
            logger.warning(f"Order {i+1} failed: {error_msg}")
    
    # Calculate statistics
    success_rate = (successful_trades / len(test_orders)) * 100
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    
    # Print results
    print(f"\n📈 Test Results Summary:")
    print(f"   Total Orders: {len(test_orders)}")
    print(f"   Successful Trades: {successful_trades}")
    print(f"   Failed Trades: {failed_trades}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Total Commission: ${total_commission:.2f}")
    print(f"   Total Slippage: ${total_slippage:.4f}")
    print(f"   Average Execution Time: {avg_execution_time:.1f}ms")
    
    # Validation criteria
    min_required_trades = 100
    min_success_rate = 95.0  # 95% success rate required
    
    validation_passed = (
        successful_trades >= min_required_trades and 
        success_rate >= min_success_rate
    )
    
    print(f"\n🎯 Validation Results:")
    print(f"   ✅ Minimum trades ({min_required_trades}): {'PASSED' if successful_trades >= min_required_trades else 'FAILED'}")
    print(f"   ✅ Success rate ({min_success_rate}%): {'PASSED' if success_rate >= min_success_rate else 'FAILED'}")
    print(f"   📊 Overall: {'PASSED' if validation_passed else 'FAILED'}")
    
    return validation_passed


async def test_risk_management():
    """Test risk management features"""
    print("\n🛡️  Testing Risk Management Features...")
    
    engine = InternalPaperTradingEngine(testing_mode=True)
    await engine.initialize()
    
    # Create account with limited funds
    account = PaperTradingAccount(
        id="risk_test_account",
        name="Risk Management Test",
        broker="simulator", 
        mode=PaperTradingMode.SIMULATOR,
        initial_balance=Decimal("10000"),
        current_balance=Decimal("10000"),
        buying_power=Decimal("20000")
    )
    
    # Test oversized order (should be rejected)
    oversized_order = PaperOrder(
        symbol="ES",
        quantity=Decimal("100"),  # Way too large for account
        order_type=OrderType.MARKET,
        action=OrderAction.BUY,
        asset_type=AssetType.FUTURE,
        account_id=account.id
    )
    
    result = await engine.execute_paper_order(oversized_order, account)
    risk_management_working = result["status"] == "rejected"
    
    print(f"   Risk Management Test: {'PASSED' if risk_management_working else 'FAILED'}")
    print(f"   Oversized order rejection: {result.get('reason', 'N/A')}")
    
    return risk_management_working


async def main():
    """Main test function"""
    print("=" * 60)
    print("TRADERTERMINAL PAPER TRADING ENGINE VALIDATION")
    print("=" * 60)
    
    # Run comprehensive trading tests
    trading_test_passed = await run_comprehensive_paper_trading_tests()
    
    # Run risk management tests
    risk_test_passed = await test_risk_management()
    
    # Final validation
    all_tests_passed = trading_test_passed and risk_test_passed
    
    print(f"\n{'='*60}")
    print(f"FINAL VALIDATION: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ TESTS FAILED'}")
    print(f"{'='*60}")
    
    return all_tests_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)