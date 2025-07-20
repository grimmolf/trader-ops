# TraderTerminal User Guide

## 🚀 Welcome to Your Bloomberg Terminal Alternative

TraderTerminal provides institutional-grade trading capabilities at **99.8% cost savings** compared to Bloomberg Terminal ($41/month vs $24,000/year). This guide will get you trading in minutes.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [TradingView Integration](#tradingview-integration)
3. [Broker Setup](#broker-setup)
4. [Trading Workflows](#trading-workflows)
5. [Strategy Development](#strategy-development)
6. [Risk Management](#risk-management)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Launch TraderTerminal

```bash
# Start the backend server
uv run uvicorn src.backend.datahub.server:app --reload --port 8000

# Optional: Start desktop frontend
cd src/frontend && npm run dev
```

### 2. Verify Setup

1. **Test webhook endpoint**: `http://localhost:8000/webhook/test`
2. **Open dashboard**: `http://localhost:8000` (web) or desktop app
3. **Check broker status**: All integrations should show as available

### 3. Start with Paper Trading

Use `paper_simulator` account group for risk-free testing:

```json
{
  "symbol": "AAPL",
  "action": "buy",
  "quantity": 100,
  "account_group": "paper_simulator",
  "strategy": "test_strategy"
}
```

---

## TradingView Integration

### Core Workflow

1. **Create Strategy** in TradingView (Pine Script)
2. **Set Webhook** → `http://localhost:8000/webhook/tradingview`
3. **Configure Alert** with proper JSON format
4. **Choose Broker** using `account_group` parameter
5. **Monitor Execution** in TraderTerminal dashboard

### Alert Configuration

#### Basic Stock Trade
```json
{
  "symbol": "AAPL",
  "action": "buy",
  "quantity": 100,
  "order_type": "market",
  "account_group": "paper_tastytrade",
  "strategy": "momentum_strategy",
  "comment": "Breakout signal"
}
```

#### Futures Trade with Risk Management
```json
{
  "symbol": "ES",
  "action": "buy",
  "quantity": 1,
  "order_type": "market",
  "account_group": "topstep",
  "strategy": "futures_breakout",
  "stop_loss": 4495.00,
  "comment": "Support break with 10 point stop"
}
```

#### Options Trade
```json
{
  "symbol": "AAPL240119C00150000",
  "action": "buy",
  "quantity": 5,
  "order_type": "limit",
  "price": 2.50,
  "account_group": "paper_tastytrade",
  "strategy": "options_flow",
  "comment": "Call option entry"
}
```

### Pine Script Template

```pinescript
//@version=5
strategy("TraderTerminal Auto-Trading", overlay=true)

// Configure account routing
account_group = input.string("paper_simulator", "Account", 
    options=["paper_simulator", "paper_tastytrade", "main", "topstep"])

// Your strategy logic
fast_ma = ta.sma(close, 10)
slow_ma = ta.sma(close, 20)

// Entry signals with webhook alerts
if ta.crossover(fast_ma, slow_ma)
    strategy.entry("Long", strategy.long)
    alert('{"symbol": "' + syminfo.ticker + 
          '", "action": "buy", "quantity": 1, "order_type": "market"' +
          ', "account_group": "' + account_group + 
          '", "strategy": "ma_crossover", "timeframe": "' + timeframe.period + 
          '", "comment": "MA crossover bullish"}', alert.freq_once_per_bar)

if ta.crossunder(fast_ma, slow_ma)
    strategy.close("Long")
    alert('{"symbol": "' + syminfo.ticker + 
          '", "action": "sell", "quantity": 1, "order_type": "market"' +
          ', "account_group": "' + account_group + 
          '", "strategy": "ma_crossover", "timeframe": "' + timeframe.period + 
          '", "comment": "MA crossover bearish"}', alert.freq_once_per_bar)
```

---

## Broker Setup

### Account Group Routing

| Account Group | Broker | Asset Types | Use Case |
|---------------|--------|-------------|----------|
| `paper_simulator` | Internal engine | All | Strategy testing |
| `paper_tastytrade` | Tastytrade sandbox | Stocks, Options | API testing |
| `paper_tradovate` | Tradovate demo | Futures | Futures testing |
| `main` | Live Tradovate | Futures | Live futures trading |
| `topstep` | TopStep + Tradovate | Futures | Funded account trading |
| `apex` | Apex + Tradovate | Futures | Funded account trading |
| `schwab_stocks` | Charles Schwab | Stocks, ETFs | Live stock trading |

### Broker Authentication

#### Tastytrade (OAuth2)
1. **Get authorization URL**: TraderTerminal generates OAuth URL
2. **Complete browser flow**: Authorize TraderTerminal access
3. **Test connection**: Verify sandbox access works
4. **Switch to live**: Update credentials for live trading

#### Tradovate (Username/Password)
1. **Set credentials**: Username, password, app ID
2. **Choose environment**: Demo vs Live
3. **Test connection**: Verify API access
4. **Configure symbols**: Add futures contracts to trade

#### TopStep/Apex (API Integration)
1. **Get API credentials**: From funded account provider
2. **Configure risk rules**: Daily loss, position limits
3. **Test with demo**: Verify risk monitoring works
4. **Go live**: Connect to funded account

---

## Trading Workflows

### 1. Strategy Development Cycle

1. **Develop in TradingView**: Create Pine Script strategy
2. **Test with paper trading**: Use `paper_simulator` account
3. **Validate with broker sandbox**: Use `paper_tastytrade` or `paper_tradovate`
4. **Monitor performance**: Review strategy metrics
5. **Go live gradually**: Start with small position sizes

### 2. Multi-Timeframe Trading

```pinescript
// Route different timeframes to different accounts
account_group = timeframe.period == "1" ? "main" :         // 1min to live
                timeframe.period == "5" ? "topstep" :      // 5min to funded
                "paper_simulator"                          // Others to paper
```

### 3. Asset-Specific Routing

```pinescript
// Route based on asset type
account_group = syminfo.type == "futures" ? "topstep" :    // Futures to funded
                syminfo.type == "stock" ? "schwab_stocks" : // Stocks to Schwab
                "paper_simulator"                           // Others to paper
```

### 4. Risk-Based Routing

```pinescript
// Route based on risk tolerance
risk_level = input.string("conservative", "Risk Level",
    options=["conservative", "moderate", "aggressive"])

account_group = risk_level == "conservative" ? "paper_simulator" :
                risk_level == "moderate" ? "main" :
                "topstep"  // High risk to funded account
```

---

## Strategy Development

### Performance Monitoring

TraderTerminal automatically tracks:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Average Trade**: Mean profit/loss per trade

### Auto-Rotation Logic

The system automatically switches strategies between modes:
- **Live → Paper**: If drawdown exceeds threshold
- **Paper → Live**: If performance improves
- **Suspended**: If strategy shows persistent losses

### Custom Metrics

Add custom performance tracking:

```json
{
  "symbol": "ES",
  "action": "buy",
  "quantity": 1,
  "account_group": "main",
  "strategy": "breakout_v2",
  "custom_metrics": {
    "signal_strength": 0.85,
    "market_regime": "trending",
    "volatility_percentile": 25
  }
}
```

---

## Risk Management

### Funded Account Rules

TopStep/Apex accounts have strict rules:
- **Daily Loss Limit**: Automatically enforced
- **Maximum Position Size**: Prevented at order level
- **Drawdown Monitoring**: Real-time tracking
- **Emergency Flatten**: One-click position closure

### Position Sizing

```json
{
  "symbol": "ES",
  "action": "buy",
  "quantity": 1,
  "account_group": "topstep",
  "position_sizing": {
    "risk_percent": 1.0,
    "stop_distance": 10,
    "account_size": 150000
  }
}
```

### Stop Loss Management

```json
{
  "symbol": "AAPL",
  "action": "buy",
  "quantity": 100,
  "order_type": "market",
  "stop_loss": 175.00,
  "take_profit": 185.00,
  "account_group": "main"
}
```

---

## Troubleshooting

### Common Issues

#### Webhook Not Received
1. **Check URL**: Ensure `http://localhost:8000/webhook/tradingview`
2. **Test endpoint**: Visit `http://localhost:8000/webhook/test`
3. **Check logs**: Look for error messages in console
4. **Verify JSON**: Ensure alert message is valid JSON

#### Order Rejected
1. **Check account group**: Verify broker is configured
2. **Verify credentials**: Ensure broker authentication works
3. **Check position limits**: May exceed account limits
4. **Market hours**: Some markets may be closed

#### Strategy Not Performing
1. **Review metrics**: Check win rate and profit factor
2. **Analyze drawdown**: May be in temporary decline
3. **Check market conditions**: Strategy may not suit current regime
4. **Backtest thoroughly**: Ensure strategy has edge

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
uv run uvicorn src.backend.datahub.server:app --reload
```

### Support Resources

- **Documentation**: `docs/` directory
- **Examples**: `docs/TRADINGVIEW_STRATEGY_EXAMPLES.md`
- **API Reference**: `http://localhost:8000/docs`
- **GitHub Issues**: Report bugs and feature requests

---

## Advanced Features

### Multi-Account Management

Trade across multiple funded accounts:

```json
{
  "symbol": "ES",
  "action": "buy", 
  "quantity": 1,
  "account_group": "topstep_account_1",
  "backup_accounts": ["topstep_account_2", "apex_account_1"]
}
```

### Custom Indicators

Integrate custom TradingView indicators:

```pinescript
// Custom indicator webhook
if custom_signal
    alert('{"symbol": "' + syminfo.ticker + 
          '", "signal_type": "custom_indicator"' +
          ', "signal_strength": ' + str.tostring(signal_strength) +
          ', "account_group": "main"}', alert.freq_once_per_bar)
```

### Portfolio Management

Track portfolio across all brokers:
- **Real-time P&L**: Aggregated across all accounts
- **Risk Metrics**: Portfolio-level risk monitoring
- **Correlation Analysis**: Position correlation tracking
- **Sector Exposure**: Industry concentration limits

---

## Next Steps

1. **Start with paper trading**: Test your strategies risk-free
2. **Connect one broker**: Begin with your preferred platform
3. **Deploy one strategy**: Start with a simple, proven system
4. **Monitor performance**: Use built-in analytics
5. **Scale gradually**: Add more strategies and brokers over time

**🎯 Your Bloomberg Terminal alternative is ready to trade!**