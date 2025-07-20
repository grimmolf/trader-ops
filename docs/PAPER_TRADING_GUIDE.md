# Paper Trading Guide

## Overview

TraderTerminal enforces a strict progression for all trading strategies:

**Backtest → Paper Trade (100+ trades) → Live Trade**

This guide explains how to properly validate strategies in paper trading before risking real capital.

## Why Paper Trading First?

1. **System Validation** - Ensure webhooks, execution, and risk management work correctly
2. **Strategy Validation** - Confirm win rates and risk/reward ratios in real market conditions
3. **Cost-Free Testing** - Find and fix bugs without financial risk
4. **Performance Baseline** - Establish expected metrics before live trading

## Paper Trading Requirements

### Minimum Requirements Before Live Trading

- ✅ **100 trades executed** in paper trading mode
- ✅ **55% win rate** achieved across the test period
- ✅ **All market conditions** tested (trending, ranging, volatile)
- ✅ **Risk management** validated (stops, position sizing)
- ✅ **Performance tracked** in TradeNote

### Broker Sandbox Environments

TraderTerminal supports multiple paper trading environments:

1. **Tradovate Demo**
   - Free demo account with real-time data
   - Futures: ES, NQ, YM, RTY, GC, CL
   - No time limits

2. **Tastytrade Sandbox**
   - OAuth2 authentication required
   - Futures and options support
   - Real market data

3. **Alpaca Paper Trading**
   - Instant activation
   - Stocks and ETFs
   - Free real-time data

4. **Internal Simulator**
   - When broker sandboxes unavailable
   - Uses real market data
   - Simulates realistic slippage

## Setting Up Paper Trading

### Step 1: Configure TradingView Alerts

Use the paper trading account group in your alerts:

```json
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "quantity": {{strategy.order.contracts}},
  "account_group": "paper_tradovate",  // Use paper_ prefix
  "strategy": "momentum_breakout"
}
```

### Step 2: Verify Paper Trading Mode

Check the dashboard to confirm paper trading is active:
- Look for "PAPER" badge on positions
- Verify P&L shows in paper account
- Check TradeNote tags show "paper"

### Step 3: Execute Test Trades

1. Start with single contract/share sizes
2. Test all strategy signals:
   - Entry signals (long and short)
   - Exit signals (profit targets and stops)
   - Position management (scaling in/out)
3. Run during different market conditions
4. Test error scenarios (rejected orders, disconnections)

## Monitoring Paper Performance

### Real-Time Tracking

The Strategy Performance Panel shows:
- Current win rate
- Average win/loss
- Maximum drawdown
- Trade count progress (X/100)

### TradeNote Integration

All paper trades are automatically logged with:
- "paper" tag for filtering
- Strategy name for analysis
- Entry/exit details
- P&L tracking

### Performance Evaluation

After 100 trades, evaluate:

```
Win Rate: Must be ≥ 55%
Profit Factor: Should be > 1.5
Max Drawdown: Should be < daily loss limit
Average Win/Loss Ratio: Should be > 1.2
```

## Transitioning to Live Trading

### Automatic Progression

When a strategy completes 100 paper trades with 55%+ win rate:
1. System sends notification
2. Strategy becomes eligible for live trading
3. User must manually approve live activation

### Manual Override

To force a strategy to live mode (NOT RECOMMENDED):
```bash
# Use the API endpoint
curl -X POST http://localhost:8000/api/strategies/{strategy_id}/mode \
  -H "Content-Type: application/json" \
  -d '{"new_mode": "live"}'
```

### First Live Trades

When transitioning to live:
1. Start with minimum position size
2. Monitor first 20 trades closely
3. Be ready to manually intervene
4. Keep paper trading running in parallel

## Automatic Paper Trading Rotation

TraderTerminal automatically protects your capital by rotating underperforming strategies back to paper trading:

### Rotation Triggers

- Win rate drops below 55% over 20 trades
- Daily loss limit exceeded
- Maximum drawdown breached
- Manual intervention triggered

### Rotation Process

1. Current positions closed (if any)
2. Strategy mode changes to "paper"
3. Notification sent to dashboard
4. Must complete 40 successful paper trades to return to live

## Best Practices

### DO ✅

- Test during high volatility events
- Include overnight holds in testing
- Test partial fills and slippage
- Document any strategy adjustments
- Review paper trades weekly

### DON'T ❌

- Skip paper trading "because you know it works"
- Test with unrealistic position sizes
- Ignore paper trading losses
- Modify strategy without restarting count
- Rush to live trading

## Troubleshooting

### Paper Trades Not Executing

1. Verify account_group includes "paper_" prefix
2. Check broker sandbox is connected
3. Confirm webhook is firing
4. Review logs for errors

### Performance Tracking Issues

1. Ensure TradeNote is running
2. Check strategy is registered
3. Verify trades have exit prices
4. Confirm set completion logic

### Sandbox Connection Problems

1. Re-authenticate with broker
2. Check API credentials
3. Verify network connectivity
4. Try alternative sandbox

## Emergency Procedures

If issues arise during paper trading:

1. **Stop New Trades**: Disable TradingView alerts
2. **Check Status**: Review dashboard for errors
3. **Review Logs**: Check for execution problems
4. **Reset If Needed**: Clear paper positions and restart

## Summary

Paper trading is not optional—it's a critical safety mechanism that:
- Validates system functionality
- Proves strategy viability
- Protects trading capital
- Builds confidence

Every successful trader tests thoroughly before risking real money. TraderTerminal enforces this discipline automatically.

Remember: **The goal is consistent profits, not fast profits.** 