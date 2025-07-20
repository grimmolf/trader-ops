#!/bin/bash

# TradingView Webhook Test Script
# Tests the enhanced webhook endpoint with various scenarios

set -e

# Configuration
WEBHOOK_URL="http://localhost:8000/webhook/tradingview"
WEBHOOK_SECRET="test_secret_key_for_development"
TEST_DIR="$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}TradingView Webhook Test Suite${NC}"
echo "================================"
echo "Testing webhook endpoint: $WEBHOOK_URL"
echo ""

# Function to generate HMAC signature
generate_signature() {
    local data="$1"
    local secret="$2"
    echo -n "$data" | openssl dgst -sha256 -hmac "$secret" | cut -d' ' -f2
}

# Function to run test case
run_test() {
    local test_name="$1"
    local alert_json="$2"
    local expect_success="$3"
    local extra_headers="$4"
    
    echo -e "${YELLOW}Test: $test_name${NC}"
    
    # Generate signature if secret is provided
    if [ -n "$WEBHOOK_SECRET" ]; then
        signature=$(generate_signature "$alert_json" "$WEBHOOK_SECRET")
        signature_header="-H \"X-Webhook-Signature: $signature\""
    else
        signature_header=""
    fi
    
    # Run the request
    response=$(eval curl -s -w "\\n%{http_code}" -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        $signature_header \
        $extra_headers \
        -d "'$alert_json'")
    
    # Parse response
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    # Check result
    if [ "$expect_success" = "true" ] && [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        echo "Response: $response_body"
    elif [ "$expect_success" = "false" ] && [ "$http_code" != "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code - Expected failure)"
        echo "Response: $response_body"
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "Response: $response_body"
        echo "Expected success: $expect_success"
    fi
    echo ""
}

# Check if server is running
echo "Checking if server is running..."
if ! curl -s "$WEBHOOK_URL/test" > /dev/null; then
    echo -e "${RED}Error: Server not running at $WEBHOOK_URL${NC}"
    echo "Please start the backend server first:"
    echo "  cd src/backend"
    echo "  uv run uvicorn src.backend.datahub.server:app --reload"
    exit 1
fi
echo -e "${GREEN}✓ Server is running${NC}"
echo ""

# Test Case 1: Valid futures buy alert
run_test "Valid Futures Buy Alert" '{
    "symbol": "ES",
    "action": "buy",
    "quantity": 1,
    "strategy": "momentum_breakout",
    "account_group": "topstep",
    "alert_name": "ES_Momentum_Long",
    "comment": "Strong momentum breakout above resistance"
}' "true"

# Test Case 2: Valid stock sell alert with limit price
run_test "Valid Stock Sell with Limit" '{
    "symbol": "AAPL",
    "action": "sell",
    "quantity": 100,
    "price": 185.50,
    "order_type": "limit",
    "strategy": "mean_reversion",
    "account_group": "main",
    "alert_name": "AAPL_MeanRev_Short"
}' "true"

# Test Case 3: Close position alert
run_test "Close Position Alert" '{
    "symbol": "NQ",
    "action": "close",
    "quantity": 2,
    "strategy": "risk_management",
    "account_group": "apex",
    "alert_name": "NQ_StopLoss",
    "comment": "Stop loss triggered"
}' "true"

# Test Case 4: Invalid symbol (empty)
run_test "Invalid Empty Symbol" '{
    "symbol": "",
    "action": "buy",
    "quantity": 1,
    "account_group": "main"
}' "false"

# Test Case 5: Invalid action
run_test "Invalid Action" '{
    "symbol": "SPY",
    "action": "hold",
    "quantity": 100,
    "account_group": "main"
}' "false"

# Test Case 6: Invalid quantity (zero)
run_test "Invalid Zero Quantity" '{
    "symbol": "QQQ",
    "action": "buy",
    "quantity": 0,
    "account_group": "main"
}' "false"

# Test Case 7: Missing required fields
run_test "Missing Required Fields" '{
    "symbol": "IWM",
    "action": "buy"
}' "false"

# Test Case 8: Invalid JSON
echo -e "${YELLOW}Test: Invalid JSON${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "invalid json")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code - Expected failure)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
fi
echo ""

# Test Case 9: Wrong content type
echo -e "${YELLOW}Test: Wrong Content Type${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: text/plain" \
    -d '{"symbol": "TEST", "action": "buy", "quantity": 1}')
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code - Expected failure)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
fi
echo ""

# Test Case 10: Rate limiting test (if enabled)
echo -e "${YELLOW}Test: Rate Limiting${NC}"
echo "Sending 10 rapid requests to test rate limiting..."
for i in {1..10}; do
    curl -s -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d '{"symbol": "TEST", "action": "buy", "quantity": 1}' > /dev/null &
done
wait
echo -e "${GREEN}✓ Rate limiting test completed${NC}"
echo ""

# Test Case 11: Health check
echo -e "${YELLOW}Test: Health Check${NC}"
response=$(curl -s "$WEBHOOK_URL/test")
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASS${NC} - Health check successful"
    echo "Response: $response"
else
    echo -e "${RED}✗ FAIL${NC} - Health check failed"
    echo "Response: $response"
fi
echo ""

echo -e "${BLUE}Test Suite Complete!${NC}"
echo "Check server logs for detailed processing information."
echo ""
echo "Next steps:"
echo "1. Configure webhook secret in .env: TRADINGVIEW_WEBHOOK_SECRET=$WEBHOOK_SECRET"
echo "2. Set up TradingView alerts to point to: $WEBHOOK_URL"
echo "3. Implement broker connectors (Tradovate, TopstepX)"
echo "4. Add funded account rule validation"