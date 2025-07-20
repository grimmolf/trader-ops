# Complete TradingView → TraderTerminal Integration Guide

## 🎯 Overview: Your Trading Automation Solution

This guide shows you how to set up **complete trading automation** from TradingView strategies to live broker execution. Whether you use Google Workspace authentication or any other TradingView login method, this webhook-based integration works seamlessly.

**What You'll Achieve:**
- ✅ TradingView strategies automatically execute trades
- ✅ Intelligent broker routing (Tastytrade, Tradovate, TopStep, etc.)
- ✅ Real-time strategy performance monitoring
- ✅ Automatic risk management and position sizing
- ✅ Paper trading for strategy development

## Authentication for All Login Methods

### Google Workspace Federated Authentication (Your Setup)

Since you use Google Workspace federated login (grimm@greysson.com), TradingView webhooks work differently than traditional API authentication. Webhooks use **URL-based authentication** and **HMAC signatures** instead of OAuth tokens.

**No Changes Required:** Your existing TradingView login works perfectly with webhooks - no additional authentication setup needed!

## 1. Webhook URL Configuration

Your TraderTerminal webhook endpoint is:
```
http://localhost:8000/webhook/tradingview
```

For production deployment, this will be:
```
https://your-domain.com/webhook/tradingview
```

## 2. TradingView Alert Setup

### Step 1: Create Alert in TradingView
1. Open any chart on TradingView
2. Click the **Alert** button (bell icon) or press `Alt+A`
3. Configure your alert conditions
4. In the **Notifications** tab, check **Webhook URL**

### Step 2: Configure Webhook URL
Enter your webhook URL with optional authentication:
```
http://localhost:8000/webhook/tradingview?secret=your_optional_secret
```

### Step 3: Alert Message Format
In the **Message** field, use this JSON format:
```json
{
  "symbol": "{{ticker}}",
  "action": "buy",
  "quantity": 1,
  "price": {{close}},
  "order_type": "market",
  "account_group": "paper_simulator",
  "strategy": "momentum_breakout",
  "timeframe": "{{interval}}",
  "timestamp": "{{time}}"
}
```

## 3. Authentication Methods

### Method 1: No Authentication (Development)
For local testing, you can disable webhook authentication:

```bash
# In your terminal
export TRADINGVIEW_WEBHOOK_SECRET=""
```

### Method 2: HMAC Signature Authentication (Recommended)
Set up a webhook secret for HMAC-SHA256 signature verification:

```bash
# Generate a secure secret
export TRADINGVIEW_WEBHOOK_SECRET="your_secure_secret_key_here"
```

Then configure TradingView to include the signature:
1. In TradingView alert, use this webhook URL:
   ```
   http://localhost:8000/webhook/tradingview
   ```
2. TradingView will automatically sign the payload with your secret

### Method 3: URL-based Secret (Simple)
Include a secret parameter in the URL:
```
http://localhost:8000/webhook/tradingview?auth_token=your_secret_token
```

## 4. Testing Webhook Connection

### Test 1: Basic Connectivity
```bash
curl http://localhost:8000/webhook/test
```

Expected response:
```json
{
  "status": "healthy",
  "message": "TradingView webhook endpoint is operational",
  "timestamp": 1642781234.567,
  "rate_limit_status": "operational"
}
```

### Test 2: Send Test Alert
```bash
curl -X POST http://localhost:8000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=your_hmac_signature" \
  -d '{
    "symbol": "AAPL",
    "action": "buy",
    "quantity": 100,
    "price": 150.00,
    "order_type": "market",
    "account_group": "paper_simulator",
    "strategy": "test_strategy"
  }'
```

Expected response:
```json
{
  "status": "received",
  "alert_id": "alert_abc123",
  "message": "Alert queued for processing: AAPL buy 100"
}
```

## 5. Account Group Routing

Configure different account groups for different trading modes:

### Paper Trading (Recommended for Testing)
```json
{
  "account_group": "paper_simulator",     // Internal simulator
  "account_group": "paper_tastytrade",    // Tastytrade sandbox
  "account_group": "paper_tradovate"      // Tradovate demo
}
```

### Live Trading (Production)
```json
{
  "account_group": "main",                // Default Tradovate
  "account_group": "topstep",            // TopStep funded account
  "account_group": "apex",               // Apex funded account
  "account_group": "tradeday"            // TradeDay funded account
}
```

## 6. Strategy Performance Integration

The webhook system includes automatic strategy performance monitoring:

```json
{
  "strategy": "momentum_breakout",
  "account_group": "main"
}
```

If a strategy becomes unprofitable:
- Alerts automatically route to paper trading
- You receive notifications about mode changes
- Live trading resumes when performance improves

## 7. Security Best Practices

### For Development
- Use `paper_` account groups only
- Test with small quantities
- Monitor logs for errors

### For Production
- Always use HMAC signature verification
- Set up proper SSL/TLS certificates
- Use environment variables for secrets
- Configure rate limiting
- Monitor for unauthorized access

## 8. Troubleshooting

### Common Issues

**"Rate limit exceeded"**
- TradingView is sending alerts too frequently
- Default limit: 10 alerts/minute per IP
- Solution: Reduce alert frequency or contact support

**"Invalid webhook signature"**
- HMAC secret mismatch between TradingView and TraderTerminal
- Solution: Verify `TRADINGVIEW_WEBHOOK_SECRET` environment variable

**"No broker connector configured"**
- Account group not recognized
- Solution: Use supported account groups or configure new broker

**"Strategy not registered"**
- Strategy name not found in performance tracker
- Solution: Strategy will be auto-created on first alert

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
```

View webhook logs:
```bash
tail -f logs/tradingview_webhooks.log
```

## 9. Example TradingView Strategy

Here's a complete TradingView Pine Script strategy with webhook integration:

```pinescript
//@version=5
strategy("TraderTerminal Integration", overlay=true)

// Strategy parameters
fast_ma = ta.sma(close, 10)
slow_ma = ta.sma(close, 20)

// Entry conditions
buy_signal = ta.crossover(fast_ma, slow_ma)
sell_signal = ta.crossunder(fast_ma, slow_ma)

// Execute trades
if buy_signal
    strategy.entry("Long", strategy.long)
    alert('{"symbol": "' + syminfo.ticker + '", "action": "buy", "quantity": 1, "order_type": "market", "account_group": "paper_simulator", "strategy": "ma_crossover", "price": ' + str.tostring(close) + '}', alert.freq_once_per_bar)

if sell_signal
    strategy.close("Long")
    alert('{"symbol": "' + syminfo.ticker + '", "action": "sell", "quantity": 1, "order_type": "market", "account_group": "paper_simulator", "strategy": "ma_crossover", "price": ' + str.tostring(close) + '}', alert.freq_once_per_bar)

plot(fast_ma, color=color.blue)
plot(slow_ma, color=color.red)
```

## 10. Environment Setup

Create a `.env` file in your project root:
```bash
# TradingView Webhook Configuration
TRADINGVIEW_WEBHOOK_SECRET=your_secure_secret_here

# Broker Credentials (for paper trading)
TASTYTRADE_CLIENT_ID=your_tastytrade_client_id
TASTYTRADE_CLIENT_SECRET=your_tastytrade_client_secret
TRADOVATE_USERNAME=your_tradovate_demo_username
TRADOVATE_PASSWORD=your_tradovate_demo_password

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true
```

## Next Steps

1. **Start with paper trading**: Use `paper_simulator` account group
2. **Test with small alerts**: Send a few manual alerts to verify connectivity
3. **Set up one strategy**: Create a simple moving average crossover strategy
4. **Monitor performance**: Watch the strategy performance dashboard
5. **Scale gradually**: Add more strategies and eventually move to live trading

The federated Google login doesn't affect webhook functionality - TradingView sends HTTP POST requests directly to your webhook endpoint regardless of how you authenticate with TradingView's web interface.