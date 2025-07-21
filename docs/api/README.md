# Trader Dashboard API Documentation

Complete API reference for the Trader Dashboard backend services, including REST endpoints, WebSocket connections, and webhook integrations for automated trading.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [REST API](#rest-api)
- [WebSocket API](#websocket-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The Trader Ops API is a FastAPI-based service providing:
- **Real-time market data** via WebSocket streams
- **TradingView UDF protocol** for chart integration
- **Trading execution** endpoints
- **Portfolio management** functionality
- **Alert system** for price notifications

**Base URL**: `http://localhost:8080` (development)
**API Version**: v1.0.0
**Documentation**: `/docs` (Swagger UI) and `/redoc` (ReDoc)
**WebSocket**: `ws://localhost:8080/stream` (real-time data)

## Authentication

### Development Mode
Currently uses open endpoints for development. Production will implement:
- API key authentication for external access
- JWT tokens for user sessions
- OAuth2 integration with broker APIs

### Headers
```http
Content-Type: application/json
Authorization: Bearer <token>  # Future implementation
```

## REST API

### Health & Configuration

#### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T15:30:00Z"
}
```

#### TradingView UDF Configuration
```http
GET /udf/config
```

**Response**:
```json
{
  "supported_resolutions": ["1", "5", "15", "30", "60", "240", "1D", "1W", "1M"],
  "supports_group_request": false,
  "supports_marks": false,
  "supports_search": true,
  "supports_timescale_marks": false
}
```

### Market Data

#### Get All Symbols
```http
GET /symbols
```

**Response**:
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "asset_class": "equity",
    "exchange": "NASDAQ",
    "currency": "USD",
    "tick_size": 0.01
  }
]
```

#### Get Symbol Information (UDF)
```http
GET /symbol_info?symbol=AAPL
```

**Parameters**:
- `symbol` (required): Trading symbol (e.g., "AAPL")

**Response**:
```json
{
  "symbol": "AAPL",
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "description": "Apple Inc. (NASDAQ)",
  "type": "equity",
  "session": "0930-1600",
  "timezone": "America/New_York",
  "exchange": "NASDAQ",
  "minmov": 1,
  "pricescale": 100,
  "has_intraday": true,
  "has_weekly_and_monthly": true,
  "supported_resolutions": ["1", "5", "15", "30", "60", "240", "1D", "1W", "1M"],
  "volume_precision": 0,
  "data_status": "streaming"
}
```

#### Get Historical Data (UDF)
```http
GET /history?symbol=AAPL&resolution=1D&from=1609459200&to=1640995200
```

**Parameters**:
- `symbol` (required): Trading symbol
- `resolution` (required): Timeframe ("1", "5", "15", "30", "60", "240", "1D", "1W", "1M")
- `from_timestamp` (required): Start time (Unix timestamp)
- `to_timestamp` (required): End time (Unix timestamp)

**Response**:
```json
{
  "s": "ok",
  "t": [1609459200, 1609545600, 1609632000],
  "o": [150.12, 151.45, 152.30],
  "h": [151.75, 153.20, 154.10],
  "l": [149.80, 150.90, 151.50],
  "c": [151.45, 152.30, 153.85],
  "v": [1234567, 987654, 1100000]
}
```

**Error Response**:
```json
{
  "s": "error",
  "errmsg": "Symbol not found"
}
```

**No Data Response**:
```json
{
  "s": "no_data"
}
```

#### Get Real-time Quote
```http
GET /quotes/{symbol}
```

**Parameters**:
- `symbol` (required): Trading symbol

**Response**:
```json
{
  "symbol": "AAPL",
  "bid": 150.45,
  "ask": 150.47,
  "last": 150.46,
  "volume": 1234567,
  "timestamp": 1705751400,
  "change": 1.23,
  "change_percent": 0.82
}
```

#### Search Symbols
```http
GET /search?query=apple
```

**Parameters**:
- `query` (required): Search term

**Response**:
```json
[
  {
    "symbol": "AAPL",
    "full_name": "NASDAQ:AAPL",
    "description": "Apple Inc.",
    "exchange": "NASDAQ",
    "ticker": "AAPL",
    "type": "equity"
  }
]
```

### Trading & Portfolio

#### Get Account Information
```http
GET /api/account
```

**Response**:
```json
{
  "account_id": "test_account_001",
  "broker": "tradier",
  "account_type": "margin",
  "total_equity": 50000.0,
  "cash_balance": 25000.0,
  "buying_power": 100000.0,
  "day_trade_buying_power": 75000.0,
  "day_pnl": 1250.0,
  "total_pnl": 8750.0,
  "is_active": true,
  "pattern_day_trader": false,
  "last_updated": 1752992252
}
```

#### Get Current Positions
```http
GET /api/positions
```

**Response**:
```json
[
  {
    "symbol": "MNQ1!",
    "account_id": "test_account_001",
    "quantity": 2.0,
    "avg_price": 17850.0,
    "market_value": 35800.0,
    "day_pnl": 150.0,
    "total_pnl": 300.0,
    "opened_at": 1752992252,
    "updated_at": 1752992252
  }
]
```

#### Get Order History
```http
GET /api/orders?limit=50
```

**Parameters**:
- `limit` (optional): Maximum number of orders to return (default: 50)

**Response**:
```json
[
  {
    "id": "order_001",
    "broker_order_id": "TRAD_12345",
    "symbol": "NQ1!",
    "order_type": "limit",
    "side": "buy",
    "quantity": 1.0,
    "price": 17900.0,
    "status": "pending",
    "account_id": "test_account_001",
    "created_at": 1752992252
  }
]
```

#### Submit New Order
```http
POST /api/orders
```

**Request Body**:
```json
{
  "symbol": "NQ1!",
  "side": "buy",
  "quantity": 1,
  "type": "market",
  "price": 17900.0
}
```

**Response**:
```json
{
  "order_id": "uuid-string",
  "status": "submitted",
  "message": "Order submitted successfully"
}
```

#### Get Market Status
```http
GET /api/market/status
```

**Response**:
```json
{
  "isOpen": false,
  "session": "closed",
  "next_open": "2025-01-20 09:30:00 ET",
  "timezone": "US/Eastern"
}
```

### Security & Testing

#### Security Health Check
```http
GET /api/security/health
```

**Response**:
```json
{
  "status": "secure",
  "last_scan": "2025-01-21T15:30:00Z",
  "security_level": "enterprise",
  "violations": 0,
  "secret_scan_clean": true
}
```

#### Test Paper Trading
```http
POST /api/paper-trading/test
```

**Request Body**:
```json
{
  "test_type": "comprehensive",
  "symbol": "AAPL",
  "strategy": "test_momentum"
}
```

**Response**:
```json
{
  "test_id": "test_12345",
  "status": "running",
  "estimated_duration": "120s",
  "test_scenarios": 15
}
```

#### Create Alert
```http
POST /alerts
```

**Request Body**:
```json
{
  "symbol": "AAPL",
  "condition": "above",
  "price": 155.00,
  "message": "AAPL broke resistance at $155",
  "expires_at": 1705837800
}
```

**Response**:
```json
{
  "id": "alert_12345",
  "symbol": "AAPL",
  "condition": "above",
  "price": 155.00,
  "message": "AAPL broke resistance at $155",
  "created_at": 1705751400,
  "expires_at": 1705837800,
  "is_active": true
}
```

#### Get Alerts
```http
GET /alerts
```

**Response**:
```json
[
  {
    "id": "alert_12345",
    "symbol": "AAPL",
    "condition": "above",
    "price": 155.00,
    "message": "AAPL broke resistance at $155",
    "created_at": 1705751400,
    "expires_at": 1705837800,
    "is_active": true
  }
]
```

#### Record Trade Execution
```http
POST /executions
```

**Request Body**:
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 100,
  "price": 150.46,
  "order_type": "market",
  "account_id": "account_123"
}
```

**Response**:
```json
{
  "id": "exec_67890",
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 100,
  "price": 150.46,
  "order_type": "market",
  "account_id": "account_123",
  "timestamp": 1705751400,
  "commission": 1.00,
  "fees": 0.10
}
```

#### Get Portfolio
```http
GET /portfolio/{account_id}
```

**Parameters**:
- `account_id` (required): Account identifier

**Response**:
```json
{
  "account_id": "account_123",
  "cash_balance": 10000.00,
  "total_value": 25000.00,
  "buying_power": 15000.00,
  "day_pnl": 250.00,
  "total_pnl": 5000.00,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "avg_price": 145.00,
      "current_price": 150.46,
      "market_value": 15046.00,
      "unrealized_pnl": 546.00
    }
  ],
  "last_updated": 1705751400
}
```

#### Get Market News
```http
GET /news?symbols=AAPL,TSLA&limit=5
```

**Parameters**:
- `symbols` (optional): Comma-separated list of symbols
- `limit` (optional): Maximum number of articles (default: 10)

**Response**:
```json
[
  {
    "id": "news_123",
    "title": "Apple Reports Strong Q4 Earnings",
    "summary": "Apple Inc. reported better-than-expected earnings...",
    "url": "https://example.com/news/apple-earnings",
    "source": "Financial Times",
    "published_at": 1705751400,
    "symbols": ["AAPL"],
    "sentiment": "positive"
  }
]
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8080/stream');
```

### Message Format

All WebSocket messages follow this JSON structure:
```json
{
  "type": "message_type",
  "symbol": "AAPL",
  "data": {...}
}
```

### Subscribe to Symbol
```json
{
  "type": "subscribe",
  "symbol": "AAPL"
}
```

**Response**:
```json
{
  "type": "subscribed",
  "symbol": "AAPL",
  "status": "success"
}
```

### Unsubscribe from Symbol
```json
{
  "type": "unsubscribe",
  "symbol": "AAPL"
}
```

**Response**:
```json
{
  "type": "unsubscribed",
  "symbol": "AAPL",
  "status": "success"
}
```

### Real-time Quote Updates
```json
{
  "type": "quote",
  "symbol": "AAPL",
  "data": {
    "symbol": "AAPL",
    "bid": 150.45,
    "ask": 150.47,
    "last": 150.46,
    "volume": 1234567,
    "timestamp": 1705751400,
    "change": 1.23,
    "change_percent": 0.82
  }
}
```

### Trade Executions
```json
{
  "type": "execution",
  "symbol": "AAPL",
  "data": {
    "id": "exec_67890",
    "symbol": "AAPL",
    "side": "buy",
    "quantity": 100,
    "price": 150.46,
    "timestamp": 1705751400
  }
}
```

### Account Updates
```json
{
  "type": "account",
  "data": {
    "account_id": "test_account_001",
    "total_equity": 50000.0,
    "cash_balance": 25000.0,
    "buying_power": 100000.0,
    "day_pnl": 1250.0,
    "total_pnl": 8750.0
  },
  "timestamp": "2025-07-20T17:45:00.000Z"
}
```

### Position Updates
```json
{
  "type": "positions",
  "data": [
    {
      "symbol": "MNQ1!",
      "quantity": 2.0,
      "avg_price": 17850.0,
      "day_pnl": 150.0,
      "total_pnl": 300.0
    }
  ],
  "timestamp": "2025-07-20T17:45:00.000Z"
}
```

### Multiple Quote Updates
```json
{
  "type": "quotes",
  "data": [
    {
      "symbol": "MNQ1!",
      "price": 17875.0,
      "change": 25.0,
      "change_percent": 0.14,
      "volume": 5432,
      "timestamp": 1752992386
    },
    {
      "symbol": "ES1!",
      "price": 4765.0,
      "change": 15.0,
      "change_percent": 0.32,
      "volume": 8901,
      "timestamp": 1752992386
    }
  ],
  "timestamp": "2025-07-20T17:45:00.000Z"
}
```

### Order Status Updates
```json
{
  "type": "order_update",
  "data": {
    "orderId": "order_001",
    "status": "filled",
    "filled_quantity": 1.0,
    "avg_fill_price": 17900.0
  }
}
```

### Market Status Updates
```json
{
  "type": "market_status",
  "data": {
    "isOpen": true,
    "session": "regular"
  }
}
```

### Alert Notifications
```json
{
  "type": "alert",
  "symbol": "AAPL",
  "data": {
    "id": "alert_12345",
    "message": "AAPL broke resistance at $155",
    "price": 155.00,
    "triggered_at": 1705751400
  }
}
```

## Data Models

### Symbol
```typescript
interface Symbol {
  symbol: string;           // Trading symbol (e.g., "AAPL")
  name: string;            // Company/asset name
  asset_class: string;     // "equity", "option", "future", "crypto"
  exchange: string;        // Exchange identifier
  currency: string;        // Base currency (e.g., "USD")
  tick_size: number;       // Minimum price increment
}
```

### Quote
```typescript
interface Quote {
  symbol: string;          // Trading symbol
  bid: number;            // Bid price
  ask: number;            // Ask price
  last: number;           // Last trade price
  volume: number;         // Trading volume
  timestamp: number;      // Unix timestamp
  change: number;         // Price change from previous close
  change_percent: number; // Percentage change
}
```

### Alert
```typescript
interface Alert {
  id?: string;            // Unique identifier (auto-generated)
  symbol: string;         // Target symbol
  condition: string;      // "above", "below", "equals"
  price: number;          // Trigger price
  message: string;        // Alert message
  created_at?: number;    // Creation timestamp
  expires_at?: number;    // Expiration timestamp
  is_active?: boolean;    // Alert status
}
```

### Execution
```typescript
interface Execution {
  id?: string;            // Unique identifier (auto-generated)
  symbol: string;         // Trading symbol
  side: string;           // "buy" or "sell"
  quantity: number;       // Number of shares/units
  price: number;          // Execution price
  order_type: string;     // "market", "limit", "stop"
  account_id: string;     // Account identifier
  timestamp?: number;     // Execution timestamp
  commission?: number;    // Commission fees
  fees?: number;          // Additional fees
}
```

### Portfolio
```typescript
interface Portfolio {
  account_id: string;     // Account identifier
  cash_balance: number;   // Available cash
  total_value: number;    // Total portfolio value
  buying_power: number;   // Available buying power
  day_pnl: number;        // Daily P&L
  total_pnl: number;      // Total unrealized P&L
  positions: Position[];  // Current positions
  last_updated: number;   // Last update timestamp
}

interface Position {
  symbol: string;         // Position symbol
  quantity: number;       // Number of shares (negative for short)
  avg_price: number;      // Average cost basis
  current_price: number;  // Current market price
  market_value: number;   // Current market value
  unrealized_pnl: number; // Unrealized profit/loss
}
```

### UDF Response
```typescript
interface UDFResponse {
  s: string;              // Status: "ok", "error", "no_data"
  t?: number[];           // Timestamps
  o?: number[];           // Open prices
  h?: number[];           // High prices
  l?: number[];           // Low prices
  c?: number[];           // Close prices
  v?: number[];           // Volumes
  errmsg?: string;        // Error message (if s="error")
}
```

## Error Handling

### HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid parameters or request body |
| 404 | Not Found | Symbol or resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error occurred |

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "SYMBOL_NOT_FOUND",
  "timestamp": "2024-01-20T15:30:00Z"
}
```

### WebSocket Error Messages
```json
{
  "type": "error",
  "error": "Invalid message format",
  "error_code": "INVALID_MESSAGE",
  "timestamp": 1705751400
}
```

## Rate Limiting

### REST API Limits
- **General endpoints**: 100 requests/minute per IP
- **Market data endpoints**: 1000 requests/minute per API key
- **Trading endpoints**: 60 requests/minute per account

### WebSocket Limits
- **Connections**: 10 concurrent connections per IP
- **Subscriptions**: 100 symbols per connection
- **Messages**: 1000 messages/minute per connection

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705751460
```

## Examples

### Complete Trading Workflow

```javascript
// 1. Connect to WebSocket
const ws = new WebSocket('ws://localhost:8080/stream');

// 2. Search for symbol
const searchResponse = await fetch('/search?query=apple');
const symbols = await searchResponse.json();
const symbol = symbols[0].symbol; // "AAPL"

// 3. Get symbol info
const infoResponse = await fetch(`/symbol_info?symbol=${symbol}`);
const symbolInfo = await infoResponse.json();

// 4. Subscribe to real-time data
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: [symbol]
}));

// 5. Handle real-time quotes
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'quote') {
    console.log('Real-time quote:', message.data);
  }
};

// 6. Create price alert
const alertResponse = await fetch('/alerts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbol: symbol,
    condition: 'above',
    price: 155.00,
    message: 'AAPL broke resistance'
  })
});

// 7. Get historical data for chart
const historyResponse = await fetch(
  `/history?symbol=${symbol}&resolution=1D&from=1609459200&to=1640995200`
);
const historicalData = await historyResponse.json();
```

### TradingView Widget Integration

```javascript
// Initialize TradingView widget with UDF
new TradingView.widget({
  symbol: 'AAPL',
  datafeed: new UDFCompatibleDatafeed('http://localhost:8080'),
  container_id: 'tradingview_chart',
  library_path: '/charting_library/',
  // ... other widget options
});

// Custom UDF datafeed implementation
class UDFCompatibleDatafeed {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  onReady(callback) {
    fetch(`${this.baseUrl}/udf/config`)
      .then(response => response.json())
      .then(callback);
  }

  searchSymbols(userInput, exchange, symbolType, onResultReadyCallback) {
    fetch(`${this.baseUrl}/udf/search?query=${userInput}`)
      .then(response => response.json())
      .then(onResultReadyCallback);
  }

  resolveSymbol(symbolName, onSymbolResolvedCallback) {
    fetch(`${this.baseUrl}/udf/symbols?symbol=${symbolName}`)
      .then(response => response.json())
      .then(onSymbolResolvedCallback);
  }

  getBars(symbolInfo, resolution, from, to, onHistoryCallback) {
    fetch(`${this.baseUrl}/udf/history?symbol=${symbolInfo.ticker}&resolution=${resolution}&from=${from}&to=${to}`)
      .then(response => response.json())
      .then(data => {
        if (data.s === 'ok') {
          const bars = data.t.map((time, index) => ({
            time: time * 1000,
            open: data.o[index],
            high: data.h[index],
            low: data.l[index],
            close: data.c[index],
            volume: data.v[index]
          }));
          onHistoryCallback(bars, { noData: false });
        } else {
          onHistoryCallback([], { noData: true });
        }
      });
  }
}
```

---

For additional information, visit the interactive API documentation at `/docs` when running the development server.