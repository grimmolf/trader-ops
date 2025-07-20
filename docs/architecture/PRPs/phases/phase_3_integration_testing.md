# Phase 3: Enhanced Integration Testing with Playwright Automation (Week 2, Day 5)

## 🎯 **Playwright GUI Testing Integration**

This phase incorporates **automated Playwright GUI testing** for comprehensive integration validation:

📄 **Framework Reference**: [`../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md`](../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md)

**Phase-Specific Testing:**
- **End-to-End Trading Flows**: Complete TradingView → Dashboard → Broker execution validation
- **Multi-Broker Integration**: All broker platforms tested simultaneously
- **Performance Benchmarking**: Load testing and concurrent user validation
- **Visual Regression**: UI consistency across all trading scenarios
- **Error Recovery**: Network failures and system resilience testing

### Task 3.1: Comprehensive Integration Test Implementation

##### Task 3.1.1: Phase-Specific Integration Tests
```typescript
// tests/playwright/phase-specific/integration-testing.spec.ts
import { test, expect } from '../core/base-test'
import { TradingWorkflowTest } from '../test-suites/trading-workflows/base-trading-test'

// Complete integration test scenario
const fullIntegrationScenario = {
  trades: [
    { symbol: 'ES', action: 'buy', quantity: 1, account_group: 'paper_simulator', strategy: 'integration_simulator' },
    { symbol: 'NQ', action: 'buy', quantity: 1, account_group: 'paper_tradovate', strategy: 'integration_tradovate' },
    { symbol: 'AAPL', action: 'buy', quantity: 100, account_group: 'paper_tastytrade', strategy: 'integration_tastytrade' }
  ],
  validateFinalState: async (page) => {
    await expect(page.locator('[data-testid="integration-test-complete"]')).toBeVisible()
  }
}

TradingWorkflowTest.createTest('Phase 3: Full Integration', fullIntegrationScenario)
```

##### Task 3.1.2: Legacy API Testing (Backup)
```python
# Create tests/e2e/test_trading_flow.py
import asyncio
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_trading_flow():
    """Test complete flow from TradingView alert to execution"""
    
    # Step 1: Start backend services
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Step 2: Send mock TradingView webhook
        webhook_data = {
            "symbol": "ES",
            "action": "buy",
            "quantity": 1,
            "strategy": "test_strategy",
            "account_group": "topstep"
        }
        
        response = await client.post(
            "/webhook/tradingview",
            json=webhook_data,
            headers={"X-Webhook-Signature": generate_test_signature(webhook_data)}
        )
        
    assert response.status_code == 200
        alert_id = response.json()["alert_id"]
        
        # Step 3: Verify order was placed
        await asyncio.sleep(2)  # Wait for processing
        
        order_response = await client.get(f"/api/v1/orders/{alert_id}")
        assert order_response.status_code == 200
        
        order = order_response.json()
        assert order["status"] in ["filled", "working"]
        assert order["symbol"] == "ES"
        assert order["quantity"] == 1
```

##### Task 3.2: Create Integration Test Suite
```bash
# Create scripts/integration_test.sh
#!/bin/bash

echo "Starting TraderTerminal Integration Tests"
echo "========================================"

# Start backend in test mode
export TRADING_ENV=test
export USE_MOCK_BROKERS=true

# Start services
cd src/backend
uv run uvicorn src.backend.datahub.server:app --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Run integration tests
cd ../..
pytest tests/e2e/ -v

# Cleanup
kill $BACKEND_PID

echo "Integration tests complete!"
```

