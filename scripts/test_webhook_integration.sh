#!/bin/bash

echo "====================================================="
echo "TradingView → Tradovate Integration Test Suite"
echo "====================================================="
echo ""

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project Root: $PROJECT_ROOT"
echo ""

# Set test environment variables
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src:$PYTHONPATH"
export TRADING_ENV="test"
export USE_MOCK_BROKERS="true"

# Test configuration
export TRADOVATE_USERNAME="test_user"
export TRADOVATE_PASSWORD="test_password"
export TRADOVATE_APP_ID="test_app_id"
export TRADOVATE_DEMO="true"
export TRADINGVIEW_WEBHOOK_SECRET="test_webhook_secret_12345"

echo "Environment Configuration:"
echo "- TRADING_ENV: $TRADING_ENV"
echo "- USE_MOCK_BROKERS: $USE_MOCK_BROKERS"
echo "- TRADOVATE_DEMO: $TRADOVATE_DEMO"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -f "uv.lock" ]; then
    echo "❌ No virtual environment found. Please run setup first:"
    echo "   uv sync"
    exit 1
fi

echo "🔧 Installing test dependencies..."
if command -v uv &> /dev/null; then
    uv add --dev pytest pytest-asyncio httpx
else
    pip install pytest pytest-asyncio httpx
fi

echo ""
echo "🧪 Running End-to-End Tests..."
echo "-----------------------------------------------------"

# Run the E2E tests specifically
if command -v uv &> /dev/null; then
    uv run pytest tests/e2e/test_webhook_tradovate_flow.py -v --tb=short
else
    python -m pytest tests/e2e/test_webhook_tradovate_flow.py -v --tb=short
fi

TEST_EXIT_CODE=$?

echo ""
echo "-----------------------------------------------------"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "🎯 Critical Path Validation:"
    echo "   ✓ TradingView webhook reception with HMAC validation"
    echo "   ✓ Alert parsing and validation"
    echo "   ✓ Broker routing to Tradovate"
    echo "   ✓ Risk management for funded accounts"
    echo "   ✓ Order execution simulation"
    echo "   ✓ WebSocket broadcasting"
    echo ""
    echo "🚀 The TradingView → Tradovate integration is ready!"
else
    echo "❌ Some tests failed. Please review the output above."
    echo ""
    echo "💡 Common issues:"
    echo "   - Missing dependencies (run: uv sync)"
    echo "   - Import path issues (check PYTHONPATH)"
    echo "   - Mock configuration problems"
    echo ""
    echo "🔍 For detailed debugging, run:"
    echo "   uv run pytest tests/e2e/test_webhook_tradovate_flow.py -v -s --tb=long"
fi

echo ""
echo "====================================================="

exit $TEST_EXIT_CODE