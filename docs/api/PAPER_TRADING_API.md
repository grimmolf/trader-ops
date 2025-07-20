# Paper Trading API Documentation

**Version**: 1.0.0  
**Base URL**: `/api/paper-trading`  
**Authentication**: None (for development)  

## Overview

The Paper Trading API provides comprehensive functionality for risk-free trading simulation with multiple execution modes. The system supports broker sandbox environments, internal simulation, and hybrid execution modes with realistic market modeling.

## Features

- **Multiple Execution Modes**: Sandbox, simulator, and hybrid environments
- **Realistic Market Simulation**: Dynamic slippage, commission modeling, market conditions
- **Performance Analytics**: Win rate, profit factor, drawdown analysis, trade statistics
- **Account Management**: Multiple accounts with reset capabilities and position tracking
- **TradingView Integration**: Seamless webhook processing for paper trading alerts
- **Real-Time Updates**: WebSocket integration for live data updates

---

## Accounts

### List Paper Trading Accounts

**GET** `/api/paper-trading/accounts`

Returns all available paper trading accounts.

**Response**:
```json
[
  {
    "id": "paper_simulator",
    "name": "Internal Simulator",
    "broker": "simulator",
    "mode": "simulator",
    "initial_balance": 100000.0,
    "current_balance": 98750.50,
    "day_pnl": -1250.50,
    "total_pnl": -1249.50,
    "buying_power": 97500.00,
    "positions": {
      "ES": {
        "symbol": "ES",
        "asset_type": "future",
        "quantity": 2,
        "avg_price": 4750.25,
        "market_price": 4745.00,
        "unrealized_pnl": -525.00,
        "multiplier": 50
      }
    },
    "created_at": "2025-01-20T10:00:00Z",
    "last_updated": "2025-01-20T15:30:00Z"
  }
]
```

### Get Specific Account

**GET** `/api/paper-trading/accounts/{account_id}`

Returns details for a specific paper trading account.

**Parameters**:
- `account_id` (path): Account identifier

**Response**: Same as single account object above

### Reset Account

**POST** `/api/paper-trading/accounts/{account_id}/reset`

Resets paper trading account to initial state.

**Request Body**:
```json
{
  "confirm": true
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Account paper_simulator has been reset to initial state",
  "account": {
    "id": "paper_simulator",
    "current_balance": 100000.0,
    "day_pnl": 0.0,
    "total_pnl": 0.0,
    "positions": {}
  }
}
```

---

## Orders

### Get Account Orders

**GET** `/api/paper-trading/accounts/{account_id}/orders`

Returns orders for a specific account.

**Parameters**:
- `account_id` (path): Account identifier
- `limit` (query, optional): Maximum number of orders to return (default: 100)

**Response**:
```json
[
  {
    "id": "order_12345",
    "account_id": "paper_simulator",
    "symbol": "ES",
    "asset_type": "future",
    "action": "buy",
    "order_type": "market",
    "quantity": 1,
    "price": null,
    "filled_quantity": 1,
    "avg_fill_price": 4750.25,
    "status": "filled",
    "broker": "simulator",
    "strategy": "momentum_strategy",
    "comment": "TradingView alert",
    "created_at": "2025-01-20T15:30:00Z",
    "filled_at": "2025-01-20T15:30:02Z"
  }
]
```

### Cancel Order

**POST** `/api/paper-trading/orders/{order_id}/cancel`

Cancels a pending paper trading order.

**Parameters**:
- `order_id` (path): Order identifier

**Response**:
```json
{
  "status": "success",
  "order_id": "order_12345"
}
```

---

## Fills

### Get Account Fills

**GET** `/api/paper-trading/accounts/{account_id}/fills`

Returns fills (executed trades) for a specific account.

**Parameters**:
- `account_id` (path): Account identifier
- `limit` (query, optional): Maximum number of fills to return (default: 100)

**Response**:
```json
[
  {
    "id": "fill_67890",
    "order_id": "order_12345",
    "account_id": "paper_simulator",
    "symbol": "ES",
    "side": "buy",
    "quantity": 1,
    "price": 4750.25,
    "commission": 2.25,
    "fees": 1.27,
    "slippage": 0.25,
    "timestamp": "2025-01-20T15:30:02Z",
    "broker": "simulator"
  }
]
```

---

## Trading

### Submit Paper Trading Alert

**POST** `/api/paper-trading/alerts`

Submits a paper trading order/alert for execution.

**Request Body**:
```json
{
  "symbol": "ES",
  "action": "buy",
  "quantity": 1,
  "orderType": "market",
  "price": 4750.00,
  "accountGroup": "paper_simulator",
  "strategy": "test_strategy",
  "comment": "Manual test order"
}
```

**Response**:
```json
{
  "status": "success",
  "order_id": "order_12346",
  "account_id": "paper_simulator",
  "execution_engine": "simulator",
  "order": {
    "id": "order_12346",
    "symbol": "ES",
    "action": "buy",
    "quantity": 1,
    "status": "filled"
  },
  "result": {
    "status": "success",
    "fill": {
      "price": 4750.25,
      "quantity": 1,
      "commission": 2.25,
      "fees": 1.27,
      "slippage": 0.25
    },
    "execution_details": {
      "execution_delay_ms": 125,
      "market_conditions": {
        "session": "regular",
        "liquidity_factor": 1.0,
        "volatility_multiplier": 1.0
      }
    }
  },
  "is_paper": true
}
```

### Flatten All Positions

**POST** `/api/paper-trading/accounts/{account_id}/flatten`

Closes all open positions in the account.

**Parameters**:
- `account_id` (path): Account identifier

**Response**:
```json
{
  "status": "success",
  "account_id": "paper_simulator",
  "positions_closed": 2,
  "results": [
    {
      "status": "success",
      "order_id": "order_12347",
      "symbol": "ES"
    },
    {
      "status": "success", 
      "order_id": "order_12348",
      "symbol": "NQ"
    }
  ]
}
```

---

## Analytics

### Get Performance Metrics

**GET** `/api/paper-trading/accounts/{account_id}/metrics`

Returns comprehensive performance metrics for the account.

**Parameters**:
- `account_id` (path): Account identifier

**Response**:
```json
{
  "account_id": "paper_simulator",
  "period_start": "2025-01-20T10:00:00Z",
  "period_end": "2025-01-20T15:30:00Z",
  "total_trades": 15,
  "winning_trades": 9,
  "losing_trades": 6,
  "win_rate": 60.0,
  "avg_win": 125.50,
  "avg_loss": -87.25,
  "largest_win": 285.00,
  "largest_loss": -150.00,
  "total_pnl": -1249.50,
  "gross_profit": 1129.50,
  "gross_loss": -523.50,
  "profit_factor": 2.16,
  "max_drawdown": -285.00,
  "total_commissions": 45.75,
  "total_volume": 15,
  "avg_trade_duration": null
}
```

---

## System

### Get System Status

**GET** `/api/paper-trading/status`

Returns paper trading system status and health information.

**Response**:
```json
{
  "status": "active",
  "total_accounts": 4,
  "total_orders": 25,
  "total_fills": 18,
  "available_engines": [
    "simulator",
    "tastytrade_sandbox",
    "tradovate_demo"
  ],
  "initialized": true,
  "timestamp": "2025-01-20T15:30:00Z"
}
```

### Health Check

**GET** `/api/paper-trading/health`

Paper trading system health check.

**Response**:
```json
{
  "status": "healthy",
  "accounts_available": 4,
  "engines_available": 3,
  "timestamp": "2025-01-20T15:30:00Z"
}
```

---

## Execution Modes

The paper trading system supports three execution modes:

### 1. Sandbox Mode (`sandbox`)
- Uses real broker APIs with fake money
- Available for Tastytrade, Tradovate, and Alpaca
- Provides realistic order management and execution
- Requires broker sandbox credentials

### 2. Simulator Mode (`simulator`) 
- Internal simulation engine with market data
- Realistic slippage and commission calculation
- Market hours and liquidity simulation
- No external dependencies

### 3. Hybrid Mode (`hybrid`)
- Sandbox order management with simulated fills
- Combines real API validation with controlled execution
- Best of both worlds for testing

---

## Account Groups

When submitting TradingView alerts, use these account group prefixes:

- `paper_simulator` - Routes to internal simulator
- `paper_tastytrade` - Routes to Tastytrade sandbox (if available)
- `paper_tradovate` - Routes to Tradovate demo (if available)
- `paper_alpaca` - Routes to Alpaca paper (if available)

---

## Error Responses

All endpoints return standardized error responses:

**400 Bad Request**:
```json
{
  "detail": "Invalid request format: Missing required field 'symbol'"
}
```

**404 Not Found**:
```json
{
  "detail": "Account not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Paper trading execution error: Failed to connect to simulation engine"
}
```

---

## TradingView Integration

### Webhook URL
`POST /webhook/tradingview`

### Alert Format
```json
{
  "symbol": "ES",
  "action": "buy", 
  "quantity": 1,
  "order_type": "market",
  "account_group": "paper_simulator",
  "strategy": "{{strategy.order.comment}}",
  "comment": "{{strategy.order.alert_message}}"
}
```

### Paper Trading Account Groups
Any alert with `account_group` starting with `paper_` will be automatically routed to the paper trading system.

---

## Real-Time Updates

The paper trading system integrates with the main WebSocket stream for real-time updates:

**WebSocket URL**: `ws://localhost:8080/stream`

**Message Types**:
- `paper_account_update` - Account balance and position changes
- `paper_order_update` - Order status changes
- `paper_fill_update` - New fills/executions

**Example Update**:
```json
{
  "type": "paper_account_update",
  "data": {
    "account_id": "paper_simulator",
    "current_balance": 98750.50,
    "day_pnl": -1250.50,
    "positions": {...}
  },
  "timestamp": "2025-01-20T15:30:00Z"
}
```

---

## Rate Limits

- **Order Submission**: 100 requests per minute per account
- **Account Queries**: 1000 requests per minute
- **System Status**: 60 requests per minute

---

## Examples

### Complete Trading Workflow

1. **Get Available Accounts**:
   ```bash
   curl -X GET "http://localhost:8080/api/paper-trading/accounts"
   ```

2. **Submit Test Order**:
   ```bash
   curl -X POST "http://localhost:8080/api/paper-trading/alerts" \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "ES",
       "action": "buy",
       "quantity": 1,
       "accountGroup": "paper_simulator",
       "comment": "Test order"
     }'
   ```

3. **Check Order Status**:
   ```bash
   curl -X GET "http://localhost:8080/api/paper-trading/accounts/paper_simulator/orders?limit=5"
   ```

4. **View Performance**:
   ```bash
   curl -X GET "http://localhost:8080/api/paper-trading/accounts/paper_simulator/metrics"
   ```

5. **Reset Account**:
   ```bash
   curl -X POST "http://localhost:8080/api/paper-trading/accounts/paper_simulator/reset" \
     -H "Content-Type: application/json" \
     -d '{"confirm": true}'
   ```

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**