# TraderTerminal API Access & Data Feed Setup Guide

This guide provides comprehensive instructions for obtaining all necessary API keys and data feeds to power your TraderTerminal platform. Total monthly cost: **$41/month** for professional-grade market data.

## Table of Contents

1. [Cost Summary](#cost-summary)
2. [User's Current Setup](#users-current-setup)
3. [Critical Dependencies](#critical-dependencies)
4. [Market Data Feeds](#market-data-feeds)
5. [News & Economic Data](#news--economic-data)
6. [Broker APIs](#broker-apis)
7. [Funded Account Platform APIs](#funded-account-platform-apis)
8. [Additional Tools](#additional-tools)
9. [Environment Configuration](#environment-configuration)

## Cost Summary

| Service | Type | Monthly Cost | Purpose | Status |
|---------|------|--------------|---------|--------|
| **Tradier Pro** | Equities/Options | $10/month | Real-time US stocks & options | ⬜ Need |
| **Tradovate CME Bundle** | Futures | $12/month | CME futures Level I data | ✅ Have |
| **TheNewsAPI Basic** | News | $19/month | Real-time financial news | ⬜ Need |
| **TradingView Premium** | Charting | Paid | Advanced charts & webhooks | ✅ Have |
| **Charles Schwab** | Broker | $0* | Stocks/options execution | ✅ Have |
| **Alpha Vantage** | Historical | Free | Historical data & fundamentals | ⬜ Need |
| **FRED API** | Economic | Free | US economic indicators | ⬜ Need |
| **CCXT** | Crypto | Free | Cryptocurrency data | ⬜ Need |
| **TopstepX** | Execution | Free** | TopStep account execution | ⬜ Need API |
| **TOTAL NEW COSTS** | - | **$41/month** | Additional services needed | - |

*Included with brokerage account
**Included with TopStep funded account

## User's Current Setup

### Already Have:
- ✅ **TradingView Premium** - Ready for webhook automation
- ✅ **Tradovate Account** - Futures data and execution
- ✅ **Charles Schwab with thinkorswim** - Stocks/options data and execution
- ✅ **NinjaTrader** - Alternative futures platform (if needed)
- ✅ **TopStep, Apex, TradeDay Accounts** - Funded trading accounts

### Need to Set Up:
- ⬜ **API Access** for all platforms
- ⬜ **Webhook Integration** with TradingView
- ⬜ **News Feed** (TheNewsAPI recommended)
- ⬜ **Historical Data** (Alpha Vantage for backtesting)

## Critical Dependencies

### 1. TradingView Webhook Setup (You Already Have Premium! ✅)

Since you have TradingView Premium, you just need to configure webhooks:

**Webhook Configuration**:
1. In your Pine Script strategy, add alert conditions
2. When creating alerts, use webhook URL option
3. Point to your TraderTerminal instance: `https://your-server.com/webhook/tradingview`
4. Use JSON format for alert messages:
   ```json
   {
     "symbol": "ES",
     "action": "buy",
     "quantity": 1,
     "account_group": "topstep",
     "strategy": "{{strategy.name}}"
   }
   ```

**Security Setup**:
```bash
# Generate webhook secret
openssl rand -hex 32
# Add to your .env file as TRADINGVIEW_WEBHOOK_SECRET
```

## Market Data Feeds

### 2. Tradier Brokerage API

**Cost**: $10/month (Pro plan)
**Website**: https://developer.tradier.com/
**Coverage**: US Equities & Options with real-time quotes

**Account Setup**:
1. Go to https://developer.tradier.com/
2. Click "Open Account" → "Brokerage Account"
3. Complete application (requires SSN for US residents)
4. Fund account with minimum $100 (for Pro plan eligibility)
5. Wait for account approval (1-2 business days)

**API Key Setup**:
1. Log into https://dash.tradier.com/
2. Navigate to "API Access" in settings
3. Create new application:
   - Name: "TraderTerminal"
   - Type: "Personal Use"
   - Description: "Desktop trading terminal"
4. Copy your API Access Token
5. **For Testing**: Also get a Sandbox token from the sandbox environment

**Environment Variables**:
```bash
TRADIER_API_KEY=your_production_api_key
TRADIER_ACCOUNT_ID=your_account_number
TRADIER_SANDBOX_KEY=your_sandbox_key
TRADIER_SANDBOX_ACCOUNT=your_sandbox_account
```

**What You Get**:
- Real-time stock quotes (NYSE, NASDAQ)
- Options chains with Greeks
- WebSocket streaming
- Order execution capabilities
- Market hours and calendar

### 3. Tradovate Futures API (You Already Have This! ✅)

Since you already use Tradovate, you just need API access:

**API Access Setup**:
1. Log into your existing Tradovate account
2. Navigate to "Settings" → "API Access"
3. Create new application for TraderTerminal
4. Save your API credentials

**Note**: You do NOT need Rithmic for data since you use Tradovate/NinjaTrader

**Demo Account (IMMEDIATE TESTING)**:
1. Go to https://demo.tradovate.com/
2. Sign up for free demo account
3. Get instant access to paper trading
4. API credentials available immediately

**API Access**:
1. Log into https://trader.tradovate.com/
2. Navigate to "Settings" → "API Access"
3. Create new application:
   - Name: "TraderTerminal"
   - App Version: "1.0"
   - Device ID: Generate unique ID
4. Save credentials:
   - Username (your email)
   - Password
   - App ID
   - CID and SEC values

**Environment Variables**:
```bash
# Production
TRADOVATE_USERNAME=your_email@example.com
TRADOVATE_PASSWORD=your_password
TRADOVATE_APP_ID=your_app_id
TRADOVATE_CID=your_cid_value
TRADOVATE_SEC=your_sec_value

# Demo (for testing)
TRADOVATE_DEMO=true
TRADOVATE_DEMO_USERNAME=demo_email@example.com
TRADOVATE_DEMO_PASSWORD=demo_password
```

**What You Get**:
- Real-time CME futures quotes
- Order execution for all futures markets
- WebSocket streaming for market data
- Historical data access
- Account balances and positions

### 4. Cryptocurrency Data (CCXT)

**Cost**: Free
**Website**: https://github.com/ccxt/ccxt
**Coverage**: 100+ crypto exchanges

**No Setup Required** - CCXT accesses public exchange APIs

**Recommended Exchanges** (all free public data):
- **Binance**: Largest volume, most pairs
- **Coinbase**: USD pairs, US-regulated
- **Kraken**: EUR pairs, good API stability

**Optional API Keys** (for higher rate limits):
1. **Binance** (optional):
   - Go to https://www.binance.com/en/my/settings/api-management
   - Create API key with read-only permissions
   - No trading permissions needed

2. **Coinbase** (optional):
   - Go to https://www.coinbase.com/settings/api
   - Create new API key
   - Permissions: "View" only

**Environment Variables** (optional):
```bash
# Optional - only if you need higher rate limits
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
COINBASE_API_KEY=your_coinbase_key
COINBASE_API_SECRET=your_coinbase_secret
```

## News & Economic Data

### 5. TheNewsAPI

**Cost**: $19/month (Basic plan)
**Website**: https://www.thenewsapi.com/
**Coverage**: Real-time news from 50,000+ sources

**Account Setup**:
1. Go to https://www.thenewsapi.com/
2. Click "Get Started"
3. Create account with email
4. Start with free trial (100 requests/day)
5. Upgrade to Basic plan ($19/month) for:
   - 10,000 requests/day
   - Real-time news (no delay)
   - All news sources

**API Key**:
1. Log into dashboard
2. Go to "API Keys" section
3. Copy your API key

**Environment Variables**:
```bash
THENEWSAPI_KEY=your_api_key
```

### 6. Alpha Vantage

**Cost**: Free
**Website**: https://www.alphavantage.co/
**Coverage**: Historical data, fundamentals, technical indicators

**Setup**:
1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Click "Get Free API Key"
4. Key is sent instantly to your email

**Environment Variables**:
```bash
ALPHA_VANTAGE_API_KEY=your_api_key
```

**What You Get**:
- 20+ years historical daily data
- 2 years of intraday data
- Company fundamentals
- 50+ technical indicators
- 5 API requests per minute (free tier)

### 7. FRED Economic Data

**Cost**: Free
**Website**: https://fred.stlouisfed.org/
**Coverage**: 800,000+ US economic time series

**Setup**:
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Click "Request API Key"
3. Create account or login
4. Fill out API key request form:
   - Purpose: "Economic data for trading terminal"
   - Description: "Personal trading application"
5. Key is generated instantly

**Environment Variables**:
```bash
FRED_API_KEY=your_api_key
```

**What You Get**:
- GDP, inflation, employment data
- Interest rates and yield curves
- Housing and construction data
- Fed meeting calendars
- Historical data back to 1940s

## Broker APIs

### 8. Interactive Brokers (Optional Alternative)

**Cost**: Variable (commissions + data)
**Website**: https://www.interactivebrokers.com/
**Coverage**: Global markets, all asset classes

**If you prefer IBKR over Tradier/Tradovate**:
1. Open IBKR Pro account
2. Fund with $2,000 minimum
3. Subscribe to market data ($4.50-$14.50/month per exchange)
4. Enable API access in TWS/Gateway

**API Setup**:
1. Download TWS or IB Gateway
2. Enable API in Configuration
3. Note the port (default: 7497 paper, 7496 live)

### 9. Alpaca (Free Alternative)

**Cost**: Free (commission-free trading)
**Website**: https://alpaca.markets/
**Coverage**: US Equities & Crypto

**Good for testing without funding**:
1. Sign up at https://app.alpaca.markets/signup
2. Get instant paper trading access
3. Real-time data included free
4. API keys available immediately

## Funded Account Platform APIs

### 6. TopstepX API (CRITICAL)

**Cost**: Free (you already have TopStep accounts)
**Purpose**: Execute trades on your TopStep funded accounts

**Getting API Access**:
1. Contact TopStep support (as a current customer)
2. Request API documentation for TopstepX
3. Mention you need programmatic access for your funded accounts

### 7. Apex & TradeDay Notes

**Important**: You do NOT need Rithmic data subscription since you use:
- **Tradovate** for futures data (primary)
- **NinjaTrader** as alternative

For Apex and TradeDay:
- Contact their support for execution-only API access
- Mention you have your own data feed via Tradovate
- This may reduce complexity and cost

### 8. Charles Schwab API (Stocks & Options)

**Cost**: Free (you already have a Schwab account with thinkorswim)
**Documentation**: https://developer.schwab.com/

**Setup Process**:
1. Log into your Schwab account
2. Go to the Developer Portal
3. Create an app for personal use
4. Get OAuth credentials

**What You Get**:
- Direct access to your existing account
- Real-time stock and options data
- Options chains with Greeks
- Complex order types
- No additional data fees

**Environment Variables**:
```bash
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
SCHWAB_REFRESH_TOKEN=your_refresh_token
SCHWAB_ACCOUNT_ID=your_account_id
```

## Additional Tools

### 10. GitHub Repository Forks

**Kairos** (TradingView Automation):
```bash
# Fork to your GitHub account:
https://github.com/timelyart/Kairos

# Clone your fork:
git clone https://github.com/YOUR_USERNAME/Kairos.git grimm-kairos
```

**Chronos** (Trade Execution):
```bash
# Fork to your GitHub account:
https://github.com/timelyart/chronos

# Clone your fork:
git clone https://github.com/YOUR_USERNAME/chronos.git grimm-chronos
```

### 11. Webhook Security

**Generate Webhook Secrets**:
```bash
# Generate secure webhook secret
openssl rand -hex 32

# Add to environment:
TRADINGVIEW_WEBHOOK_SECRET=your_generated_secret
CHRONOS_WEBHOOK_SECRET=your_generated_secret
```

## Environment Configuration

### Complete .env.example File

Create `src/backend/.env.example`:

```bash
# === CORE CONFIGURATION ===
NODE_ENV=development
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379

# === MARKET DATA FEEDS ===

# Tradier (Required - $10/month)
TRADIER_API_KEY=your_production_api_key
TRADIER_ACCOUNT_ID=your_account_number
TRADIER_SANDBOX_KEY=your_sandbox_key
TRADIER_SANDBOX_ACCOUNT=your_sandbox_account
TRADIER_BASE_URL=https://api.tradier.com
TRADIER_WS_URL=wss://ws.tradier.com

# Tradovate Futures (Required - $12/month)
TRADOVATE_USERNAME=your_email@example.com
TRADOVATE_PASSWORD=your_password
TRADOVATE_APP_ID=your_app_id
TRADOVATE_APP_VERSION=1.0
TRADOVATE_API_URL=https://api.tradovate.com/v1
TRADOVATE_MD_URL=wss://md.tradovate.com/v1/websocket
TRADOVATE_DEMO=false

# News Services (Required - $19/month)
THENEWSAPI_KEY=your_api_key
THENEWSAPI_BASE_URL=https://api.thenewsapi.com/v1

# Free Data Services
ALPHA_VANTAGE_API_KEY=your_api_key
FRED_API_KEY=your_api_key

# Optional Crypto Exchange APIs (Higher Rate Limits)
BINANCE_API_KEY=optional_key
BINANCE_API_SECRET=optional_secret
COINBASE_API_KEY=optional_key
COINBASE_API_SECRET=optional_secret

# === AUTOMATION & EXECUTION ===

# Webhook Security
TRADINGVIEW_WEBHOOK_SECRET=generate_with_openssl
CHRONOS_WEBHOOK_SECRET=generate_with_openssl

# Kairos Configuration
KAIROS_PATH=/opt/grimm-kairos
KAIROS_CHROME_PATH=/usr/bin/chromium-browser

# Chronos Configuration
CHRONOS_URL=http://localhost:5000
CHRONOS_API_KEY=your_chronos_key

# === OPTIONAL BROKERS ===

# Interactive Brokers (Alternative)
IB_GATEWAY_HOST=localhost
IB_GATEWAY_PORT=7497
IB_CLIENT_ID=1

# Alpaca (Free Alternative)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://api.alpaca.markets
ALPACA_PAPER=true
```

### Setup Script

Create `scripts/setup-api-keys.sh`:

```bash
#!/bin/bash
# TraderTerminal API Setup Helper

echo "TraderTerminal API Setup Helper"
echo "==============================="
echo

# Check if .env exists
if [ -f "src/backend/.env" ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp src/backend/.env src/backend/.env.backup
fi

# Copy template
cp src/backend/.env.example src/backend/.env

echo "✅ Created .env file from template"
echo
echo "Next Steps:"
echo "1. Open src/backend/.env in your editor"
echo "2. Add your API keys following this guide"
echo "3. NEVER commit .env to git!"
echo
echo "Required APIs ($41/month total):"
echo "- [ ] Tradier API Key ($10/month)"
echo "- [ ] Tradovate API Credentials ($12/month)"  
echo "- [ ] TheNewsAPI Key ($19/month)"
echo
echo "Free APIs:"
echo "- [ ] Alpha Vantage API Key"
echo "- [ ] FRED API Key"
echo
echo "Critical:"
echo "- [ ] TradingView Charting Library (Apply first!)"
```

Make it executable:
```bash
chmod +x scripts/setup-api-keys.sh
```

## Setup Checklist

Use this checklist to track your progress:

### Day 1 - Critical Dependencies
- [ ] Apply for TradingView Charting Library
- [ ] Generate webhook secrets
- [ ] Create .env file from template
- [ ] Fork Kairos and Chronos repositories

### Day 2 - Trading Accounts
- [ ] Open Tradier account and fund with $100
- [ ] Open Tradovate account
- [ ] Subscribe to CME Bundle data

### Day 3 - Data Feeds
- [ ] Get TheNewsAPI key (start free trial)
- [ ] Get Alpha Vantage key (instant)
- [ ] Get FRED API key (instant)
- [ ] Optional: Exchange API keys for crypto

### Day 4 - Configuration
- [ ] Receive TradingView library approval
- [ ] Download and extract charting library
- [ ] Complete .env configuration
- [ ] Test all API connections

## Troubleshooting

### Common Issues

**TradingView Library Rejection**:
- Ensure you specify "personal use" not commercial
- Mention it's for a desktop application
- If rejected, try lightweight-charts as alternative

**Tradier Account Delays**:
- International users may face longer approval
- Consider Alpaca as free alternative for testing

**Tradovate Data Subscription**:
- Data fees are separate from account
- Must explicitly subscribe to CME Bundle
- Charges begin immediately upon activation

**API Rate Limits**:
- Alpha Vantage: 5 requests/minute (free)
- TheNewsAPI: Varies by plan
- Implement caching to avoid limits

## Security Best Practices

1. **Never commit API keys**:
   ```bash
   # Add to .gitignore
   .env
   .env.*
   !.env.example
   ```

2. **Use environment variables**:
   ```python
   # Good
   api_key = os.getenv("TRADIER_API_KEY")
   
   # Bad
   api_key = "abc123..."  # Never hardcode!
   ```

3. **Rotate keys regularly**:
   - Set calendar reminders every 90 days
   - Keep backup keys for critical services

4. **Use read-only permissions**:
   - For data feeds, never enable trading
   - Separate keys for data vs execution

5. **Monitor usage**:
   - Check API dashboards weekly
   - Set up billing alerts

## Support Resources

### API Documentation
- **Tradier**: https://developer.tradier.com/documentation
- **Tradovate**: https://api.tradovate.com/
- **TheNewsAPI**: https://www.thenewsapi.com/documentation
- **Alpha Vantage**: https://www.alphavantage.co/documentation/
- **FRED**: https://fred.stlouisfed.org/docs/api/fred/

### Community Support
- **TradingView**: https://www.tradingview.com/support/
- **CCXT**: https://github.com/ccxt/ccxt/wiki
- **Kairos**: https://github.com/timelyart/Kairos/issues
- **Chronos**: https://github.com/timelyart/chronos/issues

### Status Pages
- **Tradier**: https://status.tradier.com/
- **Tradovate**: https://www.tradovate.com/support/
- **Alpha Vantage**: https://www.alphavantage.co/support/

---

*Last Updated: January 2025*

## Quick Start for Your Setup

### Immediate Actions (Today):
1. ✅ Configure TradingView webhook format
2. ⬜ Get Tradovate API credentials from your account
3. ⬜ Contact TopStep support for API access
4. ⬜ Enable Schwab Developer API access

### Week 1 Priorities:
1. ⬜ Implement Tradovate connector (futures)
2. ⬜ Set up TradingView webhook receiver
3. ⬜ Get TopstepX API documentation
4. ⬜ Test futures execution flow

### Week 2 Priorities:
1. ⬜ Implement Schwab connector (stocks/options)
2. ⬜ Add TheNewsAPI for news feed
3. ⬜ Set up multi-account execution
4. ⬜ Production deployment

### Optional/Later:
- ⬜ NinjaTrader integration (if needed)
- ⬜ Apex/TradeDay execution APIs
- ⬜ Additional data providers

**Remember**: You already have most of the expensive pieces (TradingView Premium, broker accounts). The additional $41/month is just for enhanced data feeds! 