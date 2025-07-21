#!/bin/bash

# TraderTerminal Playwright Test Runner
# Comprehensive GUI testing automation

set -e

echo "🎭 TraderTerminal Playwright Testing Suite"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_MODE="all"
HEADLESS=true
BROWSER="chromium"
WORKERS=1
RETRIES=1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --headed)
      HEADLESS=false
      shift
      ;;
    --browser)
      BROWSER="$2"
      shift 2
      ;;
    --workers)
      WORKERS="$2"
      shift 2
      ;;
    --retries)
      RETRIES="$2"
      shift 2
      ;;
    --mode)
      TEST_MODE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --headed          Run tests in headed mode (visible browser)"
      echo "  --browser BROWSER Browser to use (chromium, firefox, webkit)"
      echo "  --workers N       Number of parallel workers"
      echo "  --retries N       Number of retries for failed tests"
      echo "  --mode MODE       Test mode (all, smoke, integration, phase0, phase3)"
      echo "  --help            Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                              # Run all tests"
      echo "  $0 --headed --browser firefox   # Run in Firefox with visible browser"
      echo "  $0 --mode smoke                 # Run smoke tests only"
      echo "  $0 --mode phase0                # Run Phase 0 tests only"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}Configuration:${NC}"
echo "  Mode: $TEST_MODE"
echo "  Browser: $BROWSER"
echo "  Headless: $HEADLESS"
echo "  Workers: $WORKERS"
echo "  Retries: $RETRIES"
echo ""

# Check if backend is running
echo -e "${YELLOW}Checking backend status...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running${NC}"
    echo "Starting backend..."
    
    # Start backend in background
    cd src/backend
    uv run uvicorn src.backend.datahub.server:app --port 8000 --env TRADING_ENV=test &
    BACKEND_PID=$!
    cd ../..
    
    # Wait for backend to start
    echo "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Backend started successfully${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend failed to start after 60 seconds${NC}"
            exit 1
        fi
    done
fi

# Install Playwright browsers if needed
echo -e "${YELLOW}Checking Playwright browsers...${NC}"
if ! npx playwright --version > /dev/null 2>&1; then
    echo "Installing Playwright browsers..."
    npx playwright install
fi

# Prepare test environment
echo -e "${YELLOW}Preparing test environment...${NC}"

# Create test directories
mkdir -p tests/reports
mkdir -p tests/screenshots
mkdir -p playwright-report

# Set environment variables
export TRADING_ENV=test
export USE_MOCK_BROKERS=true
export ENABLE_PAPER_TRADING=true

# Build Playwright command based on options
PLAYWRIGHT_CMD="npx playwright test"

if [ "$HEADLESS" = false ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --headed"
fi

PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=$BROWSER --workers=$WORKERS --retries=$RETRIES"

# Add test mode specific filters
case $TEST_MODE in
    smoke)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --grep 'smoke|basic|health'"
        ;;
    integration)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD tests/playwright/phase-specific/integration-testing.spec.ts"
        ;;
    phase0)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD tests/playwright/phase-specific/futures-trading-tests.spec.ts"
        ;;
    phase3)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD tests/playwright/phase-specific/integration-testing.spec.ts"
        ;;
    cross-browser)
        PLAYWRIGHT_CMD="npx playwright test tests/playwright/test-suites/cross-browser/"
        ;;
    workflows)
        PLAYWRIGHT_CMD="npx playwright test tests/playwright/test-suites/trading-workflows/"
        ;;
    all)
        # Run all tests - no additional filter
        ;;
    *)
        echo -e "${RED}Unknown test mode: $TEST_MODE${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}Running Playwright tests...${NC}"
echo "Command: $PLAYWRIGHT_CMD"
echo ""

# Run the tests
if eval $PLAYWRIGHT_CMD; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    TEST_RESULT=0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    TEST_RESULT=1
fi

# Generate test report
echo -e "${YELLOW}Generating test report...${NC}"

# Show test results summary
if [ -f "tests/reports/test-results.json" ]; then
    echo -e "${BLUE}Test Results Summary:${NC}"
    # Extract summary from test results (basic parsing)
    TOTAL_TESTS=$(grep -o '"tests":\[' tests/reports/test-results.json | wc -l)
    echo "  Total test files: $TOTAL_TESTS"
fi

# Show where to find reports
echo ""
echo -e "${BLUE}📊 Test Reports Available:${NC}"
echo "  HTML Report: playwright-report/index.html"
echo "  JSON Report: tests/reports/test-results.json"
echo "  Screenshots: tests/screenshots/"
echo "  Performance Reports: tests/reports/"

# Show command to view HTML report
echo ""
echo -e "${BLUE}🔍 View detailed report:${NC}"
echo "  npx playwright show-report"

# Cleanup
if [ ! -z "$BACKEND_PID" ]; then
    echo ""
    echo -e "${YELLOW}Stopping backend...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
fi

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ TraderTerminal Playwright testing completed successfully!${NC}"
else
    echo -e "${RED}❌ TraderTerminal Playwright testing completed with failures${NC}"
    echo -e "${YELLOW}Check the HTML report for detailed failure information${NC}"
fi

exit $TEST_RESULT