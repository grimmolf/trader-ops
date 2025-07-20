# TopstepX API Integration

## Overview

TopstepX API integration for funded futures trading accounts in TraderTerminal. This connector provides real-time market data, order execution, and account management for Topstep funded traders.

## API Documentation

### Official Resources
- **Developer Portal**: https://dashboard.projectx.com/
- **Help Center**: https://help.topstep.com/en/articles/11187768-topstepx-api-access
- **Community Python Library**: https://github.com/mceesincus/tsxapi4py
- **Discord Support**: #api-trading channel in Topstep Discord

### API Products
- **REST API**: Account management, order placement, historical data
- **WebSocket API**: Real-time market data and account updates
- **Market Data**: Level 1 and Level 2 data for futures contracts

## Authentication Setup

### 1. API Access Subscription
1. Access TopstepX dashboard at https://dashboard.projectx.com/
2. Navigate to "Subscriptions" → "ProjectX API Access"
3. Subscribe for $29/month (use "topstep" promo code for 50% off = $14.50/month)
4. Generate API key in ProjectX settings

### 2. Authentication Flow
- **Authentication**: OAuth using API key
- **Token Management**: Bearer tokens with automatic refresh
- **Environment**: LIVE and DEMO environments supported

## API Endpoints

### Base URLs
- **REST API**: `https://api.projectx.com/v1`
- **WebSocket Market Data**: `wss://api.projectx.com/markethub`
- **WebSocket User Data**: `wss://api.projectx.com/userhub`

### Key Endpoints
```
Authentication:
POST /auth/token                        # OAuth token exchange

Account Management:
GET  /accounts                          # Get account list
GET  /accounts/{accountId}              # Get account details
GET  /accounts/{accountId}/balances     # Get account balances

Market Data:
GET  /contracts                         # Search contracts
GET  /contracts/{contractId}            # Get contract details
GET  /market/historical                 # Get historical data
WS   /markethub                         # Real-time market data

Trading:
POST /orders                            # Place order
GET  /orders                            # Get orders
PUT  /orders/{orderId}                  # Modify order
DELETE /orders/{orderId}                # Cancel order

Positions:
GET  /positions                         # Get positions
POST /positions/{positionId}/close      # Close position
```

## Rate Limits
- **API Calls**: Standard rate limiting (not publicly documented)
- **WebSocket**: Real-time streaming with connection limits
- **Production**: Monitor for rate limit responses

## Security Considerations & Restrictions

### Critical Restrictions
- **Device Requirement**: All activity must originate from personal device
- **No VPS/VPN**: Use of VPS, VPNs, or remote servers is strictly prohibited
- **No Sandbox**: Production environment only, no test/sandbox available
- **Final Trades**: All API trades are final and non-reversible

### Security Best practices
- Store API keys securely using environment variables
- Implement proper token rotation
- Use HTTPS only for REST API calls
- Validate all WebSocket connections

## Critical Features for Implementation

### 1. Funded Account Rules Engine

The system must enforce these common funded account rules:

- **Daily Loss Limits**: Maximum daily loss (e.g., $1,000)
- **Max Drawdown**: Trailing drawdown limit (e.g., $2,000)
- **Position Size Limits**: Maximum contracts per trade (e.g., 3 contracts)
- **Profit Targets**: Account passing thresholds (e.g., $3,000 profit)
- **Consistency Rules**: Minimum trading days and profit consistency

### 2. Real-time Monitoring

- Continuous P&L tracking
- Rule violation detection
- Automatic position flattening on violations
- WebSocket notifications for rule status changes

### 3. Risk Management Integration

The TopstepX connector must integrate with:
- TradingView webhook processing
- Tradovate order execution
- Real-time position monitoring
- Emergency stop-loss mechanisms

## Integration Features

### Real-Time Capabilities
- Live market data streaming (quotes, trades, depth)
- Real-time account updates (orders, positions, balances)
- Connection state management (connected, disconnected, error)

### Trading Operations
- Multiple order types (Market, Limit, Stop, Stop-Limit)
- Order modification and cancellation
- Position management and partial closes
- Trade history and order status tracking

### Account Management
- Multi-account support for funded accounts
- Real-time balance and buying power updates
- Position tracking with P&L calculations
- Risk management integration for funded account rules

## Funded Account Specific Features

### Account Rules Integration
- **Daily Loss Limits**: Automated monitoring of daily drawdown limits
- **Trailing Drawdown**: Track maximum account balance and trailing stops
- **Position Sizing**: Enforce maximum position size limits per contract
- **Risk Management**: Real-time risk checks before order placement

### Performance Tracking
- Daily P&L monitoring
- Account balance progression
- Trading statistics and metrics
- Rule compliance reporting

## Environment Variables
```bash
TOPSTEPX_API_KEY=your_api_key
TOPSTEPX_USERNAME=your_username
TOPSTEPX_ENVIRONMENT=LIVE  # or DEMO
TOPSTEPX_WEBHOOK_SECRET=webhook_secret_for_validation
```

## Integration Status
- 🚧 **In Development**: Authentication and API client
- 📅 **Planned**: Market data connector
- 📅 **Planned**: Trading connector with funded account rules
- 📅 **Planned**: Real-time WebSocket streaming
- 📅 **Planned**: Integration with TraderTerminal webhook system

## Implementation Notes

### Funded Account Considerations
- Each funded account has specific risk parameters
- Daily loss limits must be enforced in real-time
- Trailing drawdown monitoring is critical
- Position sizing must respect account rules

### WebSocket Implementation
- SignalR-based WebSocket connections
- Automatic reconnection handling
- Callback system for data handling
- Connection state monitoring

### Error Handling
- API error response parsing
- Network failure recovery
- Rate limit handling
- Connection loss recovery

## Testing Strategy

### Development Testing
- Use personal funded accounts for testing
- Implement comprehensive logging
- Test all order types and scenarios
- Validate risk rule enforcement

### Risk Management Testing
- Test daily loss limit enforcement
- Validate trailing drawdown calculations
- Test position size limits
- Verify real-time risk checks

## Integration Points

### TradingView Webhook Flow
```
TradingView Alert → Webhook Receiver → TopstepX Rules Check → Tradovate Execution
```

### Rule Enforcement Points
1. **Pre-execution**: Check rules before placing orders
2. **Real-time**: Monitor positions during market hours
3. **Post-execution**: Validate trades against account rules
4. **Emergency**: Flatten positions on rule violations

---

**Important**: This integration is designed for personal use with Topstep funded accounts. Ensure compliance with Topstep's Terms of Service and funded account rules. All trading activities must originate from your personal device.