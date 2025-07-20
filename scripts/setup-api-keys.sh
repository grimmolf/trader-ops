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

# Create .env from template
cat > src/backend/.env << 'EOF'
# === CORE CONFIGURATION ===
NODE_ENV=development
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379

# === MARKET DATA FEEDS ===

# Tastytrade (Multi-Asset Trading - FREE)
TASTYTRADE_CLIENT_ID=e3f4389d-8216-40f6-af76-c7dc957977fe
TASTYTRADE_CLIENT_SECRET=
TASTYTRADE_REDIRECT_URI=traderterminal://oauth-callback
TASTYTRADE_SANDBOX=true

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
TRADOVATE_CID=your_cid_value
TRADOVATE_SEC=your_sec_value
TRADOVATE_API_URL=https://api.tradovate.com/v1
TRADOVATE_MD_URL=wss://md.tradovate.com/v1/websocket
TRADOVATE_DEMO=false

# Tradovate Demo (For Testing)
TRADOVATE_DEMO_USERNAME=demo_email@example.com
TRADOVATE_DEMO_PASSWORD=demo_password
TRADOVATE_DEMO_APP_ID=demo_app_id

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

# === FUNDED ACCOUNT PLATFORMS ===

# TopstepX (For TopStep Accounts)
TOPSTEPX_USERNAME=your_topstep_username
TOPSTEPX_PASSWORD=your_topstep_password
TOPSTEPX_API_URL=https://api.topstepx.com
TOPSTEPX_WS_URL=wss://api.topstepx.com/ws

# Apex & TradeDay (Execution Only - Data via Tradovate)
# Note: User does NOT use Rithmic for data
APEX_API_KEY=your_apex_api_key
APEX_API_SECRET=your_apex_api_secret
TRADEDAY_API_KEY=your_tradeday_api_key
TRADEDAY_API_SECRET=your_tradeday_api_secret
USE_RITHMIC_DATA=false  # Important: Set to false

# Funded Account Configuration
DEFAULT_FUNDED_ACCOUNTS=topstep_001,topstep_002,apex_001,tradeday_001
FUNDED_ACCOUNT_CONFIG=/etc/trader-ops/funded_accounts.yaml

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
EOF

echo "✅ Created .env file from template"
echo
echo "Next Steps:"
echo "1. Open src/backend/.env in your editor"
echo "2. Add your API keys following the API_ACCESS_GUIDE.md"
echo "3. NEVER commit .env to git!"
echo
echo "Already Configured:"
echo "- [x] Tastytrade OAuth Client (FREE)"
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
echo "Critical Dependencies:"
echo "- [ ] TradingView Charting Library (Apply first!)"
echo
echo "To generate webhook secrets, run:"
echo "  openssl rand -hex 32"
echo
echo "For detailed setup instructions, see:"
echo "  docs/architecture/API_ACCESS_GUIDE.md" 

echo
echo "Step 2: Configure API Keys"
echo "=========================="
echo
echo "Critical Path APIs (for futures trading):"
echo "1. Tastytrade - Add client secret (already have client ID!)"
echo "2. Tradovate Demo - Sign up at: https://demo.tradovate.com"
echo "3. TopstepX - Contact support@topstep.com for API access"
echo "4. Tradier - For stocks/options: https://developer.tradier.com"
echo
echo "Optional APIs (can be added later):"
echo "5. Apex/TradeDay - Contact for execution-only API access"
echo "6. TheNewsAPI - Financial news: https://www.thenewsapi.com"
echo "7. Alpha Vantage - Free tier: https://www.alphavantage.co/support/#api-key"
echo

# Create funded accounts configuration
echo
echo "Creating funded accounts configuration..."
mkdir -p config
cat > config/funded_accounts.yaml << 'EOF'
# Funded Trading Accounts Configuration
# =====================================

accounts:
  # TopStep Accounts (via TopstepX)
  topstep_001:
    platform: topstep
    connector: topstepx
    account_id: "TS50K001"
    size: 50000
    rules:
      max_daily_loss: 1000
      max_contracts: 3
      trailing_drawdown: 2000
      profit_target: 3000

  topstep_002:
    platform: topstep
    connector: topstepx
    account_id: "TS50K002"
    size: 50000
    rules:
      max_daily_loss: 1000
      max_contracts: 3
      trailing_drawdown: 2000
      profit_target: 3000

  # Apex Accounts (via Tradovate data)
  apex_001:
    platform: apex
    connector: tradovate  # Data via Tradovate, execution via Apex
    account_id: "APX50K001"
    size: 50000
    rules:
      max_daily_loss: 2500
      max_contracts: 10
      trailing_drawdown: 2500
      profit_target: 3000
      news_trading_allowed: false

  # TradeDay Accounts (via Tradovate data)
  tradeday_001:
    platform: tradeday
    connector: tradovate  # Data via Tradovate, execution via TradeDay
    account_id: "TD150K001"
    size: 150000
    rules:
      max_daily_loss: 3000
      max_contracts: 15
      trailing_drawdown: 3000
      profit_target: 9000

# Account Groups for Multi-Account Execution
groups:
  all_topstep:
    accounts: [topstep_001, topstep_002]
    
  all_funded:
    accounts: [topstep_001, topstep_002, apex_001, tradeday_001]
    
  conservative:
    accounts: [topstep_001, apex_001]
    
  aggressive:
    accounts: [topstep_002, tradeday_001]
EOF

echo "✅ Configuration files created!"
echo
echo "Next Steps:"
echo "1. Edit src/backend/.env with your actual API keys"
echo "2. Edit config/funded_accounts.yaml with your account details"
echo "3. Test connection: cd src/backend && python test_connections.py"
echo
echo "For immediate testing with mock data:"
echo "cd src/backend && uv run uvicorn src.backend.datahub.server:app --reload" 