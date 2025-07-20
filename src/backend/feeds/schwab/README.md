# Charles Schwab API Integration

## Overview

Charles Schwab API integration for stocks and options trading in TraderTerminal. This connector provides market data and trading capabilities for equity markets.

## API Documentation

### Official Resources
- **Developer Portal**: https://developer.schwab.com/
- **Community Library**: https://schwab-py.readthedocs.io/
- **GitHub**: https://github.com/itsjafer/schwab-api

### API Products
- **Accounts and Trading Production**: Full trading capabilities
- **Market Data Production**: Real-time quotes and historical data

## Authentication Setup

### 1. Developer Account Setup
1. Create account at https://developer.schwab.com/
2. Register new application
3. Choose callback URL: `https://127.0.0.1:8182` (recommended)
4. Select "Accounts and Trading Production" for full access
5. Wait for approval (typically 1-3 days)

### 2. OAuth2 Flow
- **Authorization URL**: `https://api.schwabapi.com/v1/oauth/authorize`
- **Token URL**: `https://api.schwabapi.com/v1/oauth/token`
- **Access Token Lifetime**: 30 minutes
- **Refresh Token Lifetime**: 7 days

## API Endpoints

### Base URLs
- **Trading API**: `https://api.schwabapi.com/trader/v1`
- **OAuth**: `https://api.schwabapi.com/v1/oauth/`

### Key Endpoints
```
Authentication:
POST /v1/oauth/token                    # Token exchange and refresh

Account Management:
GET  /trader/v1/accounts                # Get account numbers
GET  /trader/v1/accounts/{accountHash}  # Get account details
GET  /trader/v1/accounts/{accountHash}/positions  # Get positions

Market Data:
GET  /trader/v1/marketdata/quotes       # Get quotes for symbols
GET  /trader/v1/marketdata/chains       # Get options chains
GET  /trader/v1/marketdata/history      # Get historical data

Trading:
POST /trader/v1/accounts/{accountHash}/orders     # Place order
GET  /trader/v1/accounts/{accountHash}/orders     # Get orders
DELETE /trader/v1/accounts/{accountHash}/orders/{orderId}  # Cancel order
```

## Rate Limits
- **Recommended**: 120 requests per minute
- **Burst**: Higher rates possible but not documented
- **Production**: Monitor for 429 responses

## Security Considerations
- Account numbers are hashed in API responses
- Use HTTPS only
- Store refresh tokens securely
- Implement proper token rotation

## Implementation Notes
- Community-maintained Python library (schwab-py) available
- OAuth callback handling required for token exchange
- Account hash values used instead of account numbers
- Sandbox testing available in developer portal

## Environment Variables
```bash
SCHWAB_CLIENT_ID=your_app_key
SCHWAB_CLIENT_SECRET=your_app_secret
SCHWAB_REDIRECT_URI=https://127.0.0.1:8182
SCHWAB_REFRESH_TOKEN=your_refresh_token  # After initial OAuth
```

## Integration Status
- 🚧 **In Development**: OAuth2 authentication
- 📅 **Planned**: Market data connector
- 📅 **Planned**: Trading connector
- 📅 **Planned**: Account management
- 📅 **Planned**: Integration with TraderTerminal webhook system

## Testing
- Use Schwab sandbox environment for development
- Validate with paper trading before live trading
- Test OAuth flow thoroughly
- Verify rate limiting compliance

---

**Important**: This integration is designed for personal use within TraderTerminal. Ensure compliance with Schwab's API terms of service and trading regulations.