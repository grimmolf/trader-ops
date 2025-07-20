# Backtesting API Documentation

## Overview

The TraderTerminal Backtesting API provides comprehensive strategy testing capabilities through integration with the Kairos automation engine. This API allows users to submit Pine Script strategies for backtesting across multiple symbols and timeframes, with real-time progress tracking and detailed results analysis.

## Base URL

```
http://localhost:8080/api/backtest
```

## Authentication

Currently, the API does not require authentication for development. Production deployments should implement proper authentication mechanisms.

## API Endpoints

### 1. Submit Backtest

Submit a new strategy backtest job for execution.

**Endpoint**: `POST /api/backtest/strategy`

**Request Body**:
```json
{
  "pine_script": "string",
  "symbols": ["string"],
  "timeframes": ["string"],
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "initial_capital": 10000.0,
  "commission": 0.01,
  "slippage": 0.0
}
```

**Request Parameters**:
- `pine_script` (required): Pine Script strategy code
- `symbols` (required): Array of symbols to test (e.g., ["AAPL", "GOOGL"])
- `timeframes` (optional): Array of timeframes (default: ["1h"])
- `start_date` (required): Backtest start date in YYYY-MM-DD format
- `end_date` (required): Backtest end date in YYYY-MM-DD format
- `initial_capital` (optional): Starting capital (default: 10000.0)
- `commission` (optional): Commission per trade (default: 0.01)
- `slippage` (optional): Slippage percentage (default: 0.0)

**Response**:
```json
{
  "backtest_id": "uuid-string",
  "status": "queued",
  "message": "Backtest submitted successfully"
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8080/api/backtest/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "pine_script": "//@version=5\nstrategy(\"Test Strategy\", overlay=true)\nif close > close[1]\n    strategy.entry(\"Long\", strategy.long)",
    "symbols": ["AAPL", "MSFT"],
    "timeframes": ["1h"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000.0
  }'
```

### 2. Get Backtest Status

Check the progress and status of a running backtest.

**Endpoint**: `GET /api/backtest/{backtest_id}/status`

**Path Parameters**:
- `backtest_id`: UUID of the backtest job

**Response**:
```json
{
  "backtest_id": "uuid-string",
  "status": "running",
  "progress": 45,
  "created_at": "2025-07-19T22:30:00.000Z",
  "started_at": "2025-07-19T22:30:05.000Z",
  "completed_at": null,
  "error_message": null
}
```

**Status Values**:
- `queued`: Job is waiting to be executed
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with error
- `cancelled`: Job was cancelled by user

**Example Request**:
```bash
curl http://localhost:8080/api/backtest/12345678-1234-1234-1234-123456789012/status
```

### 3. Get Backtest Results

Retrieve the results of a completed backtest.

**Endpoint**: `GET /api/backtest/{backtest_id}/results`

**Path Parameters**:
- `backtest_id`: UUID of the backtest job

**Response**:
```json
{
  "backtest_id": "uuid-string",
  "status": "completed",
  "request": {
    "pine_script": "string",
    "symbols": ["AAPL", "MSFT"],
    "timeframes": ["1h"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000.0,
    "commission": 0.01,
    "slippage": 0.0
  },
  "results": {
    "total_return": 0.125,
    "max_drawdown": 0.15,
    "sharpe_ratio": 1.8,
    "win_rate": 0.65,
    "total_trades": 245,
    "profit_factor": 1.45,
    "avg_win": 125.50,
    "avg_loss": -85.25,
    "largest_win": 1250.00,
    "largest_loss": -850.00,
    "equity_curve": [
      {
        "date": "2024-01-01",
        "equity": 10000.00
      },
      {
        "date": "2024-01-02", 
        "equity": 10125.50
      }
    ],
    "trades": [
      {
        "entry_date": "2024-01-02",
        "exit_date": "2024-01-03",
        "side": "long",
        "entry_price": 150.25,
        "exit_price": 152.75,
        "quantity": 100,
        "pnl": 250.00
      }
    ]
  }
}
```

**Result Metrics**:
- `total_return`: Overall return percentage
- `max_drawdown`: Maximum drawdown percentage
- `sharpe_ratio`: Risk-adjusted return ratio
- `win_rate`: Percentage of winning trades
- `total_trades`: Total number of trades executed
- `profit_factor`: Gross profit / gross loss ratio
- `avg_win`: Average winning trade amount
- `avg_loss`: Average losing trade amount
- `largest_win`: Largest single winning trade
- `largest_loss`: Largest single losing trade
- `equity_curve`: Daily equity progression
- `trades`: Detailed trade-by-trade analysis

**Example Request**:
```bash
curl http://localhost:8080/api/backtest/12345678-1234-1234-1234-123456789012/results
```

### 4. Cancel Backtest

Cancel a running or queued backtest job.

**Endpoint**: `DELETE /api/backtest/{backtest_id}`

**Path Parameters**:
- `backtest_id`: UUID of the backtest job

**Response**:
```json
{
  "backtest_id": "uuid-string",
  "status": "cancelled",
  "message": "Backtest cancelled successfully"
}
```

**Example Request**:
```bash
curl -X DELETE http://localhost:8080/api/backtest/12345678-1234-1234-1234-123456789012
```

### 5. List Backtests

Retrieve a list of recent backtest jobs.

**Endpoint**: `GET /api/backtest`

**Query Parameters**:
- `limit` (optional): Maximum number of results (default: 20)

**Response**:
```json
{
  "backtests": [
    {
      "backtest_id": "uuid-string",
      "status": "completed",
      "progress": 100,
      "symbols": ["AAPL", "MSFT"],
      "created_at": "2025-07-19T22:30:00.000Z",
      "completed_at": "2025-07-19T22:35:00.000Z"
    }
  ]
}
```

**Example Request**:
```bash
curl "http://localhost:8080/api/backtest?limit=10"
```

### 6. Real-time Progress Updates

WebSocket endpoint for real-time backtest progress updates.

**Endpoint**: `WebSocket /api/backtest/{backtest_id}/progress`

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8080/api/backtest/12345678-1234-1234-1234-123456789012/progress');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress update:', data);
};
```

**Message Types**:

**Progress Update**:
```json
{
  "type": "progress",
  "backtest_id": "uuid-string",
  "status": "running",
  "progress": 45
}
```

**Completion**:
```json
{
  "type": "completed",
  "backtest_id": "uuid-string", 
  "status": "completed",
  "progress": 100,
  "error_message": null
}
```

**Error**:
```json
{
  "type": "error",
  "message": "Backtest not found"
}
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Backtest job not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Errors

**400 Bad Request**:
- Invalid Pine Script syntax
- Missing required parameters
- Invalid date format
- Invalid symbol format

**404 Not Found**:
- Backtest ID does not exist

**500 Internal Server Error**:
- Kairos execution failure
- Database connection error
- Internal processing error

## Rate Limiting

- Maximum 5 concurrent backtests per client
- Request rate limit: 60 requests per minute
- WebSocket connections: 10 concurrent connections per client

## Pine Script Requirements

### Supported Features
- TradingView Pine Script v5
- Basic strategy functions (entry, exit, close)
- Technical indicators (SMA, EMA, RSI, etc.)
- Custom variables and calculations

### Limitations
- No external data sources
- Limited to supported timeframes
- Maximum 10,000 bars per symbol
- No plotting functions (charts not generated)

### Example Pine Script
```pinescript
//@version=5
strategy("Simple Moving Average Cross", overlay=true)

// Input parameters
fast_length = input(20, title="Fast MA Length")
slow_length = input(50, title="Slow MA Length")

// Calculate moving averages
fast_ma = ta.sma(close, fast_length)
slow_ma = ta.sma(close, slow_length)

// Entry conditions
long_condition = ta.crossover(fast_ma, slow_ma)
short_condition = ta.crossunder(fast_ma, slow_ma)

// Execute trades
if long_condition
    strategy.entry("Long", strategy.long)
if short_condition
    strategy.entry("Short", strategy.short)
```

## Best Practices

### Performance Optimization
- Limit backtests to essential symbols
- Use appropriate timeframes for strategy
- Avoid overly complex Pine Scripts
- Monitor progress via WebSocket

### Strategy Development
- Test with small symbol sets first
- Validate Pine Script syntax before submission
- Use realistic commission and slippage values
- Consider multiple timeframes for robustness

### Error Handling
- Always check backtest status before retrieving results
- Implement proper WebSocket error handling
- Use exponential backoff for failed requests
- Monitor rate limits to avoid throttling

## SDK Examples

### Python Example
```python
import requests
import json

# Submit backtest
backtest_data = {
    "pine_script": "//@version=5\nstrategy(\"Test\", overlay=true)\nif close > close[1]\n    strategy.entry(\"Long\", strategy.long)",
    "symbols": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}

response = requests.post(
    "http://localhost:8080/api/backtest/strategy",
    json=backtest_data
)

backtest_id = response.json()["backtest_id"]

# Check status
status_response = requests.get(
    f"http://localhost:8080/api/backtest/{backtest_id}/status"
)

print(f"Status: {status_response.json()['status']}")
```

### JavaScript Example
```javascript
// Submit backtest
const backtestData = {
  pine_script: "//@version=5\nstrategy(\"Test\", overlay=true)\nif close > close[1]\n    strategy.entry(\"Long\", strategy.long)",
  symbols: ["AAPL"],
  start_date: "2024-01-01", 
  end_date: "2024-12-31"
};

const response = await fetch("http://localhost:8080/api/backtest/strategy", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(backtestData)
});

const { backtest_id } = await response.json();

// WebSocket progress tracking
const ws = new WebSocket(`ws://localhost:8080/api/backtest/${backtest_id}/progress`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "completed") {
    console.log("Backtest completed!");
    // Fetch results
    fetchResults(backtest_id);
  }
};
```

---

**Note**: This API is currently in development with mock Kairos integration. Production deployment will require proper Kairos configuration and database setup.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>