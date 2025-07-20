# Critical Path APIs for TraderTerminal Frontend Testing

## Overview

This document outlines the critical APIs needed for immediate frontend testing, with a focus on futures trading through funded account platforms.

## User's Actual Trading Setup

### Data Feeds
- **Futures Data**: Tradovate or NinjaTrader (NOT Rithmic)
- **Stocks/Options**: Charles Schwab with thinkorswim
- **Charting**: TradingView Premium (already active)

### Execution Platforms
- **Futures**: TopstepX (TopStep), Tradovate direct
- **Stocks/Options**: Charles Schwab (thinkorswim)
- **Funded Accounts**: Apex and TradeDay (execution only, data via Tradovate/NinjaTrader)

## Priority 1: Immediate Testing Needs

### 1. Mock Data Service (Day 1 - Already Complete)
- **Status**: ✅ Already implemented in `src/backend/datahub/server.py`
- **Purpose**: Test frontend without live feeds
- **Features**: Mock quotes, positions, orders, account data

### 2. Tradovate API (Week 1 - CRITICAL)
- **Cost**: $12/month for CME Bundle
- **Purpose**: Primary futures data AND execution
- **Note**: User already uses this for data, no Rithmic needed
- **Critical Endpoints**:
  ```python
  # Data endpoints needed
  GET /md/subscribeQuote      # Real-time quotes
  GET /md/subscribeDOM        # Depth of market
  GET /md/getCandleChart      # Historical data
  
  # Trading endpoints needed  
  POST /order/placeOrder      # Order placement
  GET /account/cashBalance    # Account balance
  GET /position/list          # Open positions
  POST /order/modifyOrder     # Modify orders
  POST /order/cancelOrder     # Cancel orders
  ```

### 3. TopstepX API (Week 1 - CRITICAL)
- **Purpose**: Execute trades on TopStep funded accounts
- **Documentation**: Request from TopStep support
- **Required Integration**:
  ```python
  class TopstepXConnector:
      """TopstepX execution connector for funded accounts"""
      
      async def authenticate(self, username: str, password: str):
          """TopstepX specific authentication"""
          
      async def get_account_metrics(self):
          """Get drawdown, profit target, daily loss"""
          
      async def place_futures_order(self, symbol: str, 
                                   action: str, quantity: int):
          """Place order with TopStep risk rules"""
  ```

### 4. TradingView Webhook Integration (Week 1 - HIGH PRIORITY)
- **Status**: User has Premium account ✅
- **Purpose**: Automated strategy execution
- **Implementation**:
  ```python
  # Webhook receiver for TradingView alerts
  @app.post("/webhook/tradingview")
  async def receive_tradingview_alert(
      request: Request,
      signature: str = Header(None)
  ):
      """Receive and process TradingView alerts"""
      # Verify webhook signature
      # Parse alert JSON
      # Route to appropriate broker
      # Execute trade with risk checks
  ```

## Priority 2: Enhanced Execution (Week 2)

### 5. Charles Schwab API (Week 2 - Stocks/Options)
- **Purpose**: Execute stock and options trades
- **Access**: Via existing Schwab account
- **Documentation**: https://developer.schwab.com/
- **Benefits**:
  - Direct integration with thinkorswim
  - Real-time options chains
  - Complex order types
  - No additional data fees (included with account)

### 6. NinjaTrader Integration (Optional)
- **Purpose**: Alternative futures data feed
- **Note**: User already has this as Tradovate alternative
- **Integration Options**:
  - NinjaTrader API (C# based)
  - Export data via CSV/API bridge
  - Use for backtesting comparison

### 7. Apex/TradeDay Execution
- **Data**: Via Tradovate or NinjaTrader (NOT Rithmic)
- **Execution**: Platform-specific APIs
- **Note**: Contact each platform for execution-only API access

## Testing Strategy for Frontend

### Phase 1: Mock Testing (Immediate)
```bash
# Backend already running with mock data
cd src/backend
uv run uvicorn src.backend.datahub.server:app --reload

# Frontend connects to mock endpoints
# Test all UI components with simulated data
```

### Phase 2: Tradovate Integration (Week 1)
1. **Get Tradovate Demo Account**:
   - Sign up at https://demo.tradovate.com
   - Free demo with delayed data
   - Test execution without risk

2. **Implement Tradovate Connector**:
   ```python
   # src/backend/feeds/tradovate.py
   class TradovateConnector:
       def __init__(self, demo: bool = True):
           self.base_url = "https://demo.tradovateapi.com/v1" if demo else "https://api.tradovate.com/v1"
   ```

3. **Test Order Flow**:
   - Place orders via frontend
   - Verify execution in Tradovate
   - Check position updates
   - Monitor P&L in real-time

### Phase 3: TradingView Webhook Setup (Week 1)
1. **Configure Webhook Endpoint**:
   ```javascript
   // TradingView Alert Message Format
   {
     "symbol": "ES",
     "action": "buy",
     "quantity": 1,
     "account_group": "topstep",
     "strategy": "momentum_breakout"
   }
   ```

2. **Create Pine Script Alerts**:
   - Use existing TradingView Premium
   - Set webhook URL to TraderTerminal
   - Test with paper trading first

### Phase 4: Charles Schwab Integration (Week 2)
1. **Enable API Access**:
   - Log into Schwab account
   - Enable developer API access
   - Generate OAuth credentials

2. **Implement Connector**:
   ```python
   class SchwabConnector:
       """Charles Schwab/thinkorswim connector"""
       
       async def get_option_chain(self, symbol: str):
           """Get full option chain with Greeks"""
           
       async def place_option_order(self, order: OptionOrder):
           """Place complex option orders"""
   ```

## Funded Account Specific Features

### Risk Management Integration
```python
class FundedAccountRiskManager:
    """Enforce funded account rules"""
    
    rules = {
        'topstep': {
            'max_daily_loss': 500,      # $500 daily loss limit
            'max_contracts': 3,          # Position size limit
            'trailing_drawdown': 2000,   # $2000 trailing drawdown
            'profit_target': 3000        # $3000 profit target
        },
        'apex': {
            'max_daily_loss': 1000,
            'max_contracts': 10,
            'trailing_drawdown': 2500,
            'profit_target': 6000,
            'data_feed': 'tradovate'     # NOT Rithmic
        },
        'tradeday': {
            'max_daily_loss': 3000,
            'max_contracts': 15,
            'trailing_drawdown': 3000,
            'profit_target': 9000,
            'data_feed': 'tradovate'     # NOT Rithmic
        }
    }
```

## Environment Variables Update

Add to your `.env`:

```bash
# === CRITICAL PATH APIS ===

# Tradovate (Futures Data & Execution)
TRADOVATE_USERNAME=your_username
TRADOVATE_PASSWORD=your_password
TRADOVATE_APP_ID=your_app_id

# TopstepX (TopStep Execution)
TOPSTEPX_USERNAME=your_username
TOPSTEPX_PASSWORD=your_password

# TradingView (Webhooks)
TRADINGVIEW_WEBHOOK_SECRET=generate_unique_secret_here

# Charles Schwab (Stocks/Options - Week 2)
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
SCHWAB_ACCOUNT_ID=your_account_id

# NinjaTrader (Optional Alternative)
NINJATRADER_API_ENABLED=false
NINJATRADER_DATA_PATH=/path/to/data

# Account Configuration
DEFAULT_FUNDED_ACCOUNTS=topstep_001,topstep_002,apex_001,tradeday_001
USE_RITHMIC_DATA=false  # Important: Set to false
```

## Quick Start Testing Plan

### Day 1: Frontend with Mock Data
- [x] Backend running with mock data
- [ ] Test all UI components
- [ ] Verify order flow
- [ ] Check real-time updates

### Week 1: Critical Path
- [ ] Sign up for Tradovate demo
- [ ] Implement Tradovate connector
- [ ] Contact TopStep for API docs
- [ ] Setup TradingView webhooks
- [ ] Test futures execution flow

### Week 2: Extended Features  
- [ ] Enable Schwab API access
- [ ] Implement Schwab connector
- [ ] Test options trading
- [ ] Multi-account testing

## Important Notes

1. **No Rithmic Data Needed**: User has Tradovate/NinjaTrader for all futures data
2. **TradingView Premium**: Already active - ready for webhook automation
3. **Charles Schwab**: Next priority after futures for stocks/options
4. **Apex/TradeDay**: Execution only, data comes from Tradovate

## Support Resources

### Tradovate
- Demo: https://demo.tradovate.com
- API Docs: https://api.tradovate.com
- Support: api@tradovate.com

### TopStep
- Platform: https://topstepx.com
- Support: support@topstep.com
- Request API access via support ticket

### Charles Schwab
- Developer Portal: https://developer.schwab.com
- API Docs: Available after login
- Support: Via your Schwab account

### TradingView
- Webhook Docs: https://www.tradingview.com/support/solutions/43000529348
- Pine Script: https://www.tradingview.com/pine-script-docs
- Already have Premium ✅ 