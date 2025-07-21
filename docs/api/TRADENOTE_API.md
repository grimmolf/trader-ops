# TradeNote Integration API Documentation

Complete API documentation for TradeNote trade journal integration in TraderTerminal platform.

## 📋 Table of Contents

- [Overview](#overview)
- [Backend API](#backend-api)
- [Frontend Store API](#frontend-store-api)
- [Configuration](#configuration)
- [Data Models](#data-models)
- [Integration Examples](#integration-examples)
- [Error Handling](#error-handling)
- [Performance Guidelines](#performance-guidelines)

## 🔍 Overview

The TradeNote integration provides automated trade journaling with professional analytics for all trading activities in TraderTerminal. It captures trades from live execution, paper trading, and strategy performance tracking, converting them to TradeNote format and providing rich analytics dashboards.

### Key Features
- **Automated Logging**: Real-time trade capture across all execution pipelines
- **Professional Analytics**: 20+ performance metrics with calendar heat-maps
- **Batch Processing**: Intelligent queuing with configurable batch sizes
- **Background Processing**: Non-blocking async operations
- **Rich UI**: Vue 3 components with calendar and analytics views
- **Secure Configuration**: Encrypted credential storage

## 🔧 Backend API

### TradeNote Service (`src/backend/integrations/tradenote/service.py`)

#### Initialize Service

```python
from src.backend.integrations.tradenote.service import TradeNoteService
from src.backend.integrations.tradenote.models import TradeNoteConfig

# Create configuration
config = TradeNoteConfig(
    base_url="http://localhost:8082",
    app_id="your_app_id",
    master_key="your_master_key",
    enabled=True,
    auto_sync=True,
    timeout_seconds=30,
    retry_attempts=3
)

# Initialize service
tradenote_service = TradeNoteService(config)
await tradenote_service.initialize()
```

#### Live Trading Integration

```python
async def log_live_execution(
    execution: Execution,
    account_name: str,
    strategy_name: Optional[str] = None,
    notes: Optional[str] = None
) -> bool:
    """
    Log a live trading execution to TradeNote.
    
    Args:
        execution: Live execution data from trading engine
        account_name: Trading account identifier
        strategy_name: Strategy name if available
        notes: Additional notes for the trade
        
    Returns:
        True if logged successfully, False otherwise
    """
```

**Example Usage:**
```python
# Log live execution
success = await tradenote_service.log_live_execution(
    execution=execution_data,
    account_name="live_account_001",
    strategy_name="momentum_strategy",
    notes="TradingView alert execution"
)
```

#### Paper Trading Integration

```python
async def log_paper_execution(
    fill: Fill,
    order: PaperOrder,
    account_name: str,
    strategy_name: Optional[str] = None,
    notes: Optional[str] = None
) -> bool:
    """
    Log a paper trading execution to TradeNote.
    
    Args:
        fill: Paper trading fill data
        order: Original paper order
        account_name: Paper trading account identifier
        strategy_name: Strategy name if available
        notes: Additional notes for the trade
        
    Returns:
        True if logged successfully, False otherwise
    """
```

**Example Usage:**
```python
# Log paper execution
success = await tradenote_service.log_paper_execution(
    fill=paper_fill,
    order=paper_order,
    account_name="paper_sim_001",
    strategy_name="mean_reversion",
    notes=f"Slippage: ${fill.slippage:.4f}"
)
```

#### Strategy Performance Integration

```python
async def log_strategy_trade(
    trade_result: TradeResult,
    account_name: str,
    strategy_name: str,
    is_paper: bool = False,
    notes: Optional[str] = None
) -> bool:
    """
    Log a completed strategy trade to TradeNote.
    
    Args:
        trade_result: Strategy trade result from performance tracker
        account_name: Trading account identifier
        strategy_name: Strategy name
        is_paper: Whether this is a paper trade
        notes: Additional notes for the trade
        
    Returns:
        True if logged successfully, False otherwise
    """
```

**Example Usage:**
```python
# Log strategy trade result
success = await tradenote_service.log_strategy_trade(
    trade_result=strategy_result,
    account_name="strategy_account",
    strategy_name="portfolio_rebalance",
    is_paper=False,
    notes="Monthly rebalancing trade"
)
```

#### Bulk Operations

```python
async def bulk_upload_trades(
    trades: List[TradeNoteTradeData]
) -> TradeNoteResponse:
    """
    Upload multiple trades directly to TradeNote.
    
    Args:
        trades: List of trade data to upload
        
    Returns:
        Upload response with success status and details
    """

async def sync_account_history(
    account_name: str,
    trades: List[TradeNoteTradeData]
) -> TradeNoteResponse:
    """
    Sync historical trades for an account.
    
    Args:
        account_name: Account identifier
        trades: Historical trade data
        
    Returns:
        Sync response with status and details
    """
```

### TradeNote Client (`src/backend/integrations/tradenote/client.py`)

#### HTTP Client Operations

```python
from src.backend.integrations.tradenote.client import TradeNoteClient

# Initialize client
client = TradeNoteClient(config)
await client.connect()

# Upload single trade
response = await client.upload_trade(trade_data)

# Upload multiple trades
response = await client.upload_trades(trades_list)

# Get calendar data
calendar_data = await client.get_calendar_data(start_date, end_date)

# Get trade statistics
stats = await client.get_trade_statistics()

# Delete trades
response = await client.delete_trades(trade_ids)

# Close connection
await client.disconnect()
```

#### Context Manager Usage

```python
# Recommended: Use context manager
async with TradeNoteClient(config) as client:
    response = await client.upload_trade(trade_data)
    # Client automatically disconnects
```

### Integration Hooks

```python
# Hook functions for execution engines
from src.backend.integrations.tradenote.hooks import (
    live_execution_hook,
    paper_execution_hook,
    strategy_trade_hook
)

# Live execution hook
await live_execution_hook(
    tradenote_service=service,
    execution=execution,
    account_name="live_account",
    strategy_name="momentum",
    notes="Alert-driven execution"
)

# Paper execution hook
await paper_execution_hook(
    tradenote_service=service,
    fill=fill,
    order=order,
    account_name="paper_account",
    strategy_name="mean_reversion"
)

# Strategy trade hook
await strategy_trade_hook(
    tradenote_service=service,
    trade_result=result,
    account_name="strategy_account",
    strategy_name="portfolio_rebalance",
    is_paper=False
)
```

## 🎨 Frontend Store API

### Pinia Store (`src/frontend/renderer/src/stores/tradenote.ts`)

#### Store Initialization

```typescript
import { useTradeNoteStore } from '../stores/tradenote'

// Initialize store
const tradeNoteStore = useTradeNoteStore()
await tradeNoteStore.initialize()
```

#### Configuration Management

```typescript
// Update configuration
const result = await tradeNoteStore.updateConfig({
  base_url: 'http://localhost:8082',
  app_id: 'your_app_id',
  master_key: 'your_master_key',
  enabled: true,
  auto_sync: true
})

// Test connection
const testResult = await tradeNoteStore.testConnection({
  base_url: 'http://localhost:8082',
  app_id: 'test_app_id',
  master_key: 'test_master_key'
})

if (testResult.success) {
  console.log('Connection successful!')
}
```

#### Data Retrieval

```typescript
// Get calendar heat-map data
const startDate = new Date('2024-01-01')
const endDate = new Date('2024-12-31')
const calendarResponse = await tradeNoteStore.getCalendarData(startDate, endDate)

if (calendarResponse.success) {
  const calendarData = calendarResponse.data
  // Process calendar data for heat-map visualization
}

// Get trade statistics
const statsResponse = await tradeNoteStore.getTradeStatistics('30d')

if (statsResponse.success) {
  const statistics = statsResponse.data
  // Display performance metrics
}
```

#### Synchronization

```typescript
// Manual sync
const syncResponse = await tradeNoteStore.syncData()

if (syncResponse.success) {
  console.log('Sync completed successfully')
}

// Check sync status
const syncStatus = tradeNoteStore.syncStatus
console.log(`Status: ${syncStatus.status}`)
console.log(`Last sync: ${syncStatus.lastSync}`)
```

#### State Management

```typescript
// Reactive state access
const isConnected = tradeNoteStore.isConnected
const isEnabled = tradeNoteStore.isEnabled
const connectionStatus = tradeNoteStore.connectionStatus
const lastError = tradeNoteStore.lastError

// Configuration access
const config = tradeNoteStore.config
console.log(`TradeNote URL: ${config.base_url}`)
```

## ⚙️ Configuration

### Backend Configuration

```python
from src.backend.integrations.tradenote.models import TradeNoteConfig

config = TradeNoteConfig(
    base_url="http://localhost:8082",           # TradeNote instance URL
    app_id="traderterminal_app_123",           # Parse Server app ID
    master_key="secure_master_key_456",        # Parse Server master key
    enabled=True,                              # Enable integration
    auto_sync=True,                            # Auto-sync every 5 minutes
    timeout_seconds=30,                        # API request timeout
    retry_attempts=3,                          # Retry failed requests
    broker_name="TraderTerminal",              # Broker identifier
    upload_mfe_prices=False                    # Upload MAE/MFE prices
)
```

### Frontend Configuration

```typescript
interface TradeNoteConfig {
  base_url: string           // TradeNote instance URL
  app_id: string            // Parse Server application ID
  master_key: string        // Parse Server master key
  enabled: boolean          // Integration toggle
  auto_sync: boolean        // Automatic sync every 5 minutes
  timeout_seconds: number   // API request timeout
  retry_attempts: number    // Failed request retry count
}
```

### Environment Variables

```bash
# Development configuration
TRADENOTE_BASE_URL=http://localhost:8082
TRADENOTE_APP_ID=<YOUR_APP_ID>
TRADENOTE_MASTER_KEY=<YOUR_MASTER_KEY>

# Production configuration (use secure secret management)
TRADENOTE_BASE_URL=https://tradenote.yourdomain.com
TRADENOTE_APP_ID_FILE=/etc/traderterminal/secrets/tradenote_app_id.txt
TRADENOTE_MASTER_KEY_FILE=/etc/traderterminal/secrets/tradenote_master_key.txt
```

## 📊 Data Models

### Trade Data Model

```python
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class TradeNoteTradeData(BaseModel):
    """Trade data in TradeNote format"""
    
    account: str                    # Trading account name
    trade_date: str                 # Trade date (MM/DD/YYYY)
    settlement_date: str            # Settlement date (MM/DD/YYYY)
    currency: str                   # Currency (e.g., "USD")
    type: str                       # Instrument type (stock, option, future, etc.)
    side: str                       # Trade side ("Buy" or "Sell")
    symbol: str                     # Trading symbol
    quantity: int                   # Number of shares/contracts
    price: Decimal                  # Execution price
    exec_time: str                  # Execution time (HH:MM:SS)
    gross_proceeds: Decimal         # Gross proceeds (positive for sales)
    commissions_fees: Decimal       # Total commissions and fees
    net_proceeds: Decimal           # Net proceeds after fees
    strategy: Optional[str]         # Strategy name
    notes: Optional[str]            # Additional notes
    is_paper_trade: bool           # Whether this is a paper trade
    trade_id: Optional[str]        # Unique trade identifier
```

### Response Models

```python
class TradeNoteResponse(BaseModel):
    """TradeNote API response"""
    
    success: bool                   # Operation success status
    message: Optional[str]          # Response message
    data: Optional[Dict[str, Any]]  # Response data
    errors: Optional[List[str]]     # Error details
```

### Calendar Data Model

```python
class TradeNoteCalendarData(BaseModel):
    """Calendar heat-map data point"""
    
    date: str                       # Date (YYYY-MM-DD)
    value: float                    # P&L value for the date
    trades_count: int              # Number of trades
    win_rate: Optional[float]      # Win rate for the date
```

### Statistics Model

```typescript
interface TradeNoteStatistics {
  // Core metrics
  totalPnL: number
  totalTrades: number
  winRate: number
  avgTradeSize: number
  
  // Performance metrics
  bestDay: number
  worstDay: number
  avgDailyPnL: number
  largestWin: number
  largestLoss: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  recoveryFactor: number
  
  // Trading activity
  maxConsecutiveWins: number
  maxConsecutiveLosses: number
  avgTimeInTrade: number
  tradingDays: number
  avgTradesPerDay: number
  mostActiveSymbol: string
  
  // Cost analysis
  totalCommission: number
  commissionPercentage: number
  
  // Trade breakdown
  paperTrades: number
  liveTrades: number
  
  // Change metrics (optional)
  pnlChange?: number
  tradesChange?: number
  winRateChange?: number
  avgTradeSizeChange?: number
}
```

## 💡 Integration Examples

### Complete Live Trading Integration

```python
from src.backend.integrations.tradenote.service import create_tradenote_service
from src.backend.models.execution import Execution, OrderSide

# Initialize TradeNote service
config = TradeNoteConfig(
    base_url="http://localhost:8082",
    app_id="traderterminal_123",
    master_key="secure_key_456",
    enabled=True
)

tradenote_service = create_tradenote_service(config)
await tradenote_service.initialize()

# Example live execution
execution = Execution(
    id="exec_001",
    order_id="order_123",
    symbol="AAPL",
    side=OrderSide.BUY,
    quantity=100,
    price=150.50,
    timestamp=datetime.now(),
    commission=1.00,
    broker="Tradier"
)

# Log to TradeNote
success = await tradenote_service.log_live_execution(
    execution=execution,
    account_name="live_trading_001",
    strategy_name="momentum_breakout",
    notes="TradingView RSI signal"
)

if success:
    print("Trade logged successfully to TradeNote")
```

### Paper Trading Integration

```python
from src.backend.trading.paper_models import Fill, PaperOrder

# Example paper trading fill
fill = Fill(
    id="fill_001",
    order_id="paper_order_123",
    symbol="MSFT",
    side="buy",
    quantity=50,
    price=280.25,
    timestamp=datetime.now(),
    commission=0.50,
    fees=0.10,
    slippage=0.02,
    broker="paper_broker"
)

paper_order = PaperOrder(
    id="paper_order_123",
    symbol="MSFT",
    quantity=50,
    order_type="market",
    strategy="mean_reversion"
)

# Log paper trade
success = await tradenote_service.log_paper_execution(
    fill=fill,
    order=paper_order,
    account_name="paper_simulation",
    strategy_name="mean_reversion_v2",
    notes="Bollinger Band reversal signal"
)
```

### Frontend Integration Example

```vue
<template>
  <div class="tradenote-dashboard">
    <TradeNotePanel />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useTradeNoteStore } from '../stores/tradenote'
import TradeNotePanel from '../components/TradeNotePanel.vue'

const tradeNoteStore = useTradeNoteStore()

onMounted(async () => {
  // Initialize TradeNote integration
  await tradeNoteStore.initialize()
  
  // Check connection status
  if (tradeNoteStore.isEnabled) {
    await tradeNoteStore.checkConnection()
  }
})
</script>
```

## 🚨 Error Handling

### Backend Error Handling

```python
from src.backend.integrations.tradenote.client import (
    TradeNoteClientError,
    TradeNoteAuthError,
    TradeNoteAPIError
)

try:
    response = await tradenote_service.log_live_execution(execution, account)
    if not response:
        logger.warning("Trade logging failed but didn't raise exception")
        
except TradeNoteAuthError as e:
    logger.error(f"Authentication error: {e}")
    # Handle credential issues
    
except TradeNoteAPIError as e:
    logger.error(f"API error: {e.status_code} - {e}")
    # Handle API-specific errors
    
except TradeNoteClientError as e:
    logger.error(f"Client error: {e}")
    # Handle general client errors
    
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle unexpected errors
```

### Frontend Error Handling

```typescript
// Error handling in store
const tradeNoteStore = useTradeNoteStore()

try {
  const result = await tradeNoteStore.getTradeStatistics('30d')
  
  if (!result.success) {
    console.error('Failed to load statistics:', result.message)
    // Show user-friendly error message
    showErrorToast(result.message || 'Failed to load data')
  }
  
} catch (error) {
  console.error('Unexpected error:', error)
  showErrorToast('An unexpected error occurred')
}

// Check connection status
if (tradeNoteStore.connectionStatus === 'error') {
  const lastError = tradeNoteStore.lastError
  console.log('Connection error:', lastError)
}
```

### Retry Logic

```python
# Built-in retry logic in client
class TradeNoteClient:
    async def _make_request(self, method, endpoint, data=None, retry_count=0):
        try:
            # Make request
            response = await self._client.request(method, url, json=data)
            return response
            
        except (RequestError, TimeoutException) as e:
            if retry_count < self.config.retry_attempts:
                wait_time = 2 ** retry_count  # Exponential backoff
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, retry_count + 1)
            raise TradeNoteAPIError(f"Request failed after {retry_count} retries: {e}")
```

## ⚡ Performance Guidelines

### Batch Processing

```python
# Configure batch processing
tradenote_service._batch_size = 20        # Increase batch size
tradenote_service._batch_timeout = 60     # Increase timeout

# Manual batch upload for large datasets
trades = []  # List of TradeNoteTradeData
batch_size = 50

for i in range(0, len(trades), batch_size):
    batch = trades[i:i + batch_size]
    response = await tradenote_service.bulk_upload_trades(batch)
    
    if not response.success:
        logger.error(f"Batch upload failed: {response.message}")
        break
```

### Caching Strategy

```typescript
// Frontend caching (built into store)
const tradeNoteStore = useTradeNoteStore()

// Data is automatically cached for 5 minutes
const stats1 = await tradeNoteStore.getTradeStatistics('30d')  // API call
const stats2 = await tradeNoteStore.getTradeStatistics('30d')  // From cache

// Force cache refresh
tradeNoteStore.clearCache()
const freshStats = await tradeNoteStore.getTradeStatistics('30d')  // API call
```

### Connection Management

```python
# Recommended: Use connection pooling
# Client automatically manages connection pool
client = TradeNoteClient(config)
await client.connect()  # Creates connection pool

# Multiple concurrent requests use same pool
tasks = [
    client.upload_trade(trade1),
    client.upload_trade(trade2),
    client.upload_trade(trade3)
]
results = await asyncio.gather(*tasks)

await client.disconnect()  # Clean up connections
```

### Memory Management

```python
# Process large datasets in chunks
async def process_large_trade_history(trades: List[TradeNoteTradeData]):
    chunk_size = 100
    
    for i in range(0, len(trades), chunk_size):
        chunk = trades[i:i + chunk_size]
        
        # Process chunk
        response = await tradenote_service.bulk_upload_trades(chunk)
        
        # Clear references to help garbage collection
        del chunk
        
        if not response.success:
            logger.error(f"Chunk {i//chunk_size + 1} failed: {response.message}")
            break
            
        # Optional: Add delay between chunks
        await asyncio.sleep(0.1)
```

## 🔧 Development Tips

### Testing Configuration

```python
# Test configuration for development
test_config = TradeNoteConfig(
    base_url="http://localhost:8082",
    app_id="test_app_id",
    master_key="test_master_key",
    enabled=True,
    timeout_seconds=10,  # Shorter timeout for testing
    retry_attempts=1     # Single retry for faster failure
)
```

### Mock Integration

```python
# Mock TradeNote service for testing
class MockTradeNoteService:
    async def log_live_execution(self, *args, **kwargs) -> bool:
        # Mock successful logging
        return True
    
    async def bulk_upload_trades(self, trades) -> TradeNoteResponse:
        return TradeNoteResponse(
            success=True,
            message=f"Mock upload of {len(trades)} trades"
        )

# Use in tests
tradenote_service = MockTradeNoteService()
```

### Debugging

```python
import logging

# Enable debug logging
logging.getLogger('src.backend.integrations.tradenote').setLevel(logging.DEBUG)

# This will log:
# - API requests and responses
# - Batch processing operations
# - Connection status changes
# - Error details with stack traces
```

---

This comprehensive API documentation provides everything needed to integrate TradeNote trade journaling into trading applications, with practical examples and performance guidelines for production use.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>