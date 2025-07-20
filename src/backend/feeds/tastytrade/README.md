# Tastytrade API Integration

This module provides comprehensive integration with the Tastytrade API, offering market data, trading capabilities, and account management for stocks, options, and futures.

## Overview

Tastytrade is a commission-free brokerage platform that provides access to:
- **Stocks and ETFs** - Commission-free equity trading
- **Options** - Advanced options strategies with competitive pricing
- **Futures** - Small and micro futures contracts
- **Real-time market data** - Live quotes and market information
- **Advanced order types** - Market, limit, stop, and complex multi-leg orders

## Features

### ✅ Implemented Features

- **OAuth2 Authentication** - Secure token-based authentication
- **Market Data API** - Real-time quotes, historical data, options chains
- **Trading API** - Order placement, management, and execution
- **Account Management** - Account info, positions, balances, transactions
- **Multi-leg Orders** - Support for complex options strategies
- **Error Handling** - Comprehensive error handling and logging
- **Token Management** - Automatic token refresh and validation

### 🔧 Integration Components

1. **Authentication (`auth.py`)** - OAuth2 flow and token management
2. **Market Data (`market_data.py`)** - Quotes, historical data, options chains
3. **Trading (`orders.py`)** - Order placement and management
4. **Account Management (`account.py`)** - Account info, positions, balances
5. **Unified Manager (`manager.py`)** - High-level API interface

## Quick Start

### 1. Setup Credentials

```python
from src.backend.feeds.tastytrade import TastytradeCredentials, TastytradeManager

credentials = TastytradeCredentials(
    client_id="your_tastytrade_client_id",
    client_secret="your_tastytrade_client_secret",
    redirect_uri="https://127.0.0.1:8182/oauth/tastytrade/callback",
    sandbox=True  # Use sandbox for testing
)

manager = TastytradeManager(credentials)
```

### 2. Authentication Flow

```python
# Generate authorization URL
auth_url = manager.get_authorization_url()
print(f"Visit this URL to authorize: {auth_url}")

# After user authorization, complete the flow
callback_url = "https://127.0.0.1:8182/oauth/tastytrade/callback?code=AUTH_CODE"
auth_result = await manager.complete_authentication(callback_url)
print(f"Authentication status: {auth_result['status']}")
```

### 3. Market Data

```python
# Get single quote
quote = await manager.get_quote("AAPL")
print(f"AAPL: ${quote.last} (${quote.change:+.2f})")

# Get multiple quotes
quotes = await manager.get_quotes(["AAPL", "MSFT", "TSLA"])
for symbol, quote in quotes.items():
    print(f"{symbol}: ${quote.last}")

# Get options chain
options = await manager.get_option_chain("AAPL", expiration_date="2024-02-16")
print(f"Found {len(options)} options for AAPL")

# Get historical data
historical = await manager.get_historical_data(
    symbol="AAPL",
    timeframe="1Day",
    start_time=datetime.now() - timedelta(days=30)
)
print(f"Retrieved {len(historical)} historical bars")
```

### 4. Account Management

```python
# Get accounts
accounts = await manager.get_accounts()
account_number = accounts[0]["account-number"]

# Get account details
account = await manager.get_account(account_number)
print(f"Account Value: ${account.balance.account_value}")
print(f"Buying Power: ${account.balance.buying_power}")

# Get positions
positions = await manager.get_positions(account_number)
for position in positions:
    if not position.is_flat:
        print(f"{position.symbol}: {position.quantity} shares")

# Get portfolio summary
summary = await manager.get_portfolio_summary(account_number)
print(f"Total P&L: ${summary['pnl']['total_day_pnl']}")
```

### 5. Trading

```python
from src.backend.feeds.tastytrade import TastytradeOrder, OrderType, OrderAction

# Simple stock purchase
result = await manager.buy_stock(
    account_number=account_number,
    symbol="AAPL",
    quantity=100,
    order_type=OrderType.MARKET
)
print(f"Order placed: {result}")

# Custom order
order = TastytradeOrder.create_equity_order(
    symbol="AAPL",
    action=OrderAction.BUY_TO_OPEN,
    quantity=100,
    order_type=OrderType.LIMIT,
    price=Decimal("150.00")
)

result = await manager.place_order(account_number, order)
order_id = result["data"]["id"]

# Cancel order
await manager.cancel_order(account_number, order_id)
```

## API Coverage

### Market Data API
- ✅ Real-time quotes (stocks, options, futures)
- ✅ Historical OHLCV data
- ✅ Options chains with filtering
- ✅ Symbol search
- ✅ Market hours information

### Trading API
- ✅ Order placement (market, limit, stop orders)
- ✅ Order cancellation and modification
- ✅ Order status tracking
- ✅ Multi-leg options strategies
- ✅ Order history

### Account API
- ✅ Customer information
- ✅ Account details and metadata
- ✅ Real-time account balances
- ✅ Position tracking with P&L
- ✅ Transaction history
- ✅ Buying power calculations

## Configuration

### Environment Variables

```bash
# Required
TASTYTRADE_CLIENT_ID=your_client_id
TASTYTRADE_CLIENT_SECRET=your_client_secret

# Optional
TASTYTRADE_REDIRECT_URI=https://127.0.0.1:8182/oauth/tastytrade/callback
TASTYTRADE_SANDBOX=true  # Use sandbox environment
```

### Rate Limits

Tastytrade API has the following rate limits:
- **Market Data**: 120 requests per minute
- **Trading**: 60 requests per minute  
- **Account Data**: 120 requests per minute

The integration includes automatic rate limiting and retry logic.

## Data Models

### Market Data Models
- `TastytradeQuote` - Real-time quote with bid/ask/last prices
- `InstrumentType` - Equity, Option, Future, etc.

### Trading Models
- `TastytradeOrder` - Order request/response with legs
- `TastytradeOrderLeg` - Individual order leg for multi-leg strategies
- `OrderType`, `OrderAction`, `OrderTimeInForce` - Order parameters

### Account Models
- `TastytradeAccountInfo` - Complete account information
- `TastytradePosition` - Position with P&L and Greeks
- `TastytradeBalance` - Account balance and buying power
- `TastytradeTransaction` - Transaction history entry

## Error Handling

The integration provides comprehensive error handling:

```python
try:
    quote = await manager.get_quote("INVALID_SYMBOL")
except Exception as e:
    logger.error(f"Error getting quote: {e}")
    # Handle error appropriately
```

Common error scenarios:
- **Authentication failures** - Invalid credentials or expired tokens
- **Rate limit exceeded** - Automatic retry with exponential backoff
- **Invalid symbols** - Symbol not found or delisted
- **Trading errors** - Insufficient buying power, invalid order parameters
- **Network issues** - Connection timeouts and retries

## Testing

### Unit Tests
```bash
# Run Tastytrade-specific tests
pytest tests/feeds/test_tastytrade/ -v

# Run with coverage
pytest tests/feeds/test_tastytrade/ --cov=src.backend.feeds.tastytrade
```

### Integration Tests
```bash
# Requires valid sandbox credentials
TASTYTRADE_CLIENT_ID=test_id TASTYTRADE_CLIENT_SECRET=test_secret \
pytest tests/integration/test_tastytrade_integration.py -v
```

## Security

### OAuth2 Security
- Uses PKCE (Proof Key for Code Exchange) for enhanced security
- Secure token storage with automatic refresh
- State parameter for CSRF protection

### API Security
- All requests use HTTPS
- Bearer token authentication
- Request signing for sensitive operations
- No sensitive data in logs

### Best Practices
- Store credentials securely (environment variables)
- Use sandbox environment for testing
- Implement proper error handling
- Monitor rate limits
- Log security events

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   Error: Token exchange failed: 401
   ```
   - Verify client ID and secret
   - Check redirect URI matches registered URI
   - Ensure proper OAuth2 flow

2. **Rate Limit Errors**
   ```
   Error: Failed to get quotes: 429
   ```
   - Reduce request frequency
   - Implement exponential backoff
   - Cache frequently accessed data

3. **Invalid Symbol Errors**
   ```
   Error: No quote data received for symbol: INVALID
   ```
   - Verify symbol exists and is tradeable
   - Use symbol search to find correct symbols
   - Check market hours for the instrument

### Debug Mode

Enable debug logging for detailed request/response information:

```python
import logging
logging.getLogger('src.backend.feeds.tastytrade').setLevel(logging.DEBUG)
```

## Integration with TraderTerminal

### DataHub Integration

The Tastytrade connector integrates with the main DataHub server:

```python
# In datahub server
from src.backend.feeds.tastytrade import TastytradeManager

# Initialize manager
tastytrade_manager = TastytradeManager(credentials)

# Add to feed managers
feed_managers["tastytrade"] = tastytrade_manager
```

### WebSocket Streaming

Real-time market data is provided through the DataHub WebSocket interface:

```python
# Subscribe to Tastytrade quotes
await websocket.send(json.dumps({
    "action": "subscribe",
    "feed": "tastytrade",
    "symbols": ["AAPL", "MSFT", "TSLA"]
}))
```

### Frontend Integration

The Vue.js frontend can access Tastytrade data through the unified API:

```javascript
// Get Tastytrade account data
const response = await fetch('/api/accounts/tastytrade');
const accounts = await response.json();

// Place order through Tastytrade
const orderResult = await fetch('/api/orders/tastytrade', {
  method: 'POST',
  body: JSON.stringify(orderData)
});
```

## Support and Documentation

- **Tastytrade API Documentation**: [https://developer.tastyworks.com/](https://developer.tastyworks.com/)
- **OAuth2 Guide**: See official Tastytrade OAuth2 documentation
- **Rate Limits**: Check current limits in developer portal
- **Status Page**: Monitor API status for outages

For TraderTerminal-specific issues, see the main project documentation.

## License

This integration is part of the TraderTerminal project and follows the same licensing terms.