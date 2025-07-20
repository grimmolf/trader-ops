# TradingView Strategy Examples for TraderTerminal

## Complete UX Flow

**Your Workflow:**
1. **TradingView Strategy** → Generates trading signals
2. **Webhook Alert** → Sends JSON to TraderTerminal
3. **TraderTerminal** → Routes to specified broker and executes order
4. **Real-time Updates** → Dashboard shows execution results

## Example 1: Simple Moving Average Crossover

```pinescript
//@version=5
strategy("TraderTerminal MA Crossover", overlay=true)

// Input parameters
fast_length = input.int(10, title="Fast MA Length")
slow_length = input.int(20, title="Slow MA Length")
account_group = input.string("paper_simulator", title="Account Group", 
    options=["paper_simulator", "paper_tastytrade", "main", "topstep", "apex"])

// Calculate moving averages
fast_ma = ta.sma(close, fast_length)
slow_ma = ta.sma(close, slow_length)

// Entry and exit conditions
buy_signal = ta.crossover(fast_ma, slow_ma)
sell_signal = ta.crossunder(fast_ma, slow_ma)

// Execute trades with webhook alerts
if buy_signal
    strategy.entry("Long", strategy.long)
    // Send webhook alert to TraderTerminal
    alert('{"symbol": "' + syminfo.ticker + '", "action": "buy", "quantity": 100, "order_type": "market", "account_group": "' + account_group + '", "strategy": "ma_crossover_' + str.tostring(fast_length) + '_' + str.tostring(slow_length) + '", "timeframe": "' + timeframe.period + '", "price": ' + str.tostring(close) + ', "comment": "Fast MA crossed above Slow MA"}', alert.freq_once_per_bar)

if sell_signal
    strategy.close("Long")
    // Send webhook alert to TraderTerminal
    alert('{"symbol": "' + syminfo.ticker + '", "action": "sell", "quantity": 100, "order_type": "market", "account_group": "' + account_group + '", "strategy": "ma_crossover_' + str.tostring(fast_length) + '_' + str.tostring(slow_length) + '", "timeframe": "' + timeframe.period + '", "price": ' + str.tostring(close) + ', "comment": "Fast MA crossed below Slow MA"}', alert.freq_once_per_bar)

// Plot moving averages
plot(fast_ma, color=color.blue, title="Fast MA")
plot(slow_ma, color=color.red, title="Slow MA")
```

## Example 2: RSI with Multiple Brokers

```pinescript
//@version=5
strategy("TraderTerminal RSI Multi-Broker", overlay=false)

// Input parameters
rsi_length = input.int(14, title="RSI Length")
rsi_overbought = input.int(70, title="RSI Overbought")
rsi_oversold = input.int(30, title="RSI Oversold")

// Account routing (you can change this per chart)
futures_account = input.string("topstep", title="Futures Account", 
    options=["paper_tradovate", "main", "topstep", "apex", "tradeday"])
stocks_account = input.string("paper_tastytrade", title="Stocks Account",
    options=["paper_tastytrade", "schwab_stocks", "paper_simulator"])

// Calculate RSI
rsi = ta.rsi(close, rsi_length)

// Entry conditions
buy_condition = rsi < rsi_oversold
sell_condition = rsi > rsi_overbought

// Determine account based on symbol type
account_to_use = syminfo.type == "futures" ? futures_account : stocks_account

// Entry signals
if buy_condition
    strategy.entry("Long", strategy.long)
    alert('{"symbol": "' + syminfo.ticker + '", "action": "buy", "quantity": ' + 
          (syminfo.type == "futures" ? "1" : "100") + 
          ', "order_type": "market", "account_group": "' + account_to_use + 
          '", "strategy": "rsi_mean_reversion", "timeframe": "' + timeframe.period + 
          '", "rsi_value": ' + str.tostring(rsi) + 
          ', "comment": "RSI oversold condition"}', alert.freq_once_per_bar)

if sell_condition
    strategy.close("Long")
    alert('{"symbol": "' + syminfo.ticker + '", "action": "sell", "quantity": ' + 
          (syminfo.type == "futures" ? "1" : "100") + 
          ', "order_type": "market", "account_group": "' + account_to_use + 
          '", "strategy": "rsi_mean_reversion", "timeframe": "' + timeframe.period + 
          '", "rsi_value": ' + str.tostring(rsi) + 
          ', "comment": "RSI overbought condition"}', alert.freq_once_per_bar)

// Plot RSI
plot(rsi, title="RSI", color=color.purple)
hline(rsi_overbought, "Overbought", color=color.red)
hline(rsi_oversold, "Oversold", color=color.green)
hline(50, "Midline", color=color.gray)
```

## Example 3: Futures Trading with Position Sizing

```pinescript
//@version=5
strategy("TraderTerminal Futures Breakout", overlay=true)

// Input parameters
lookback = input.int(20, title="Breakout Lookback")
account_group = input.string("topstep", title="Funded Account", 
    options=["paper_tradovate", "topstep", "apex", "tradeday", "main"])
risk_percent = input.float(1.0, title="Risk Percent", minval=0.1, maxval=5.0)

// Calculate breakout levels
highest_high = ta.highest(high, lookback)
lowest_low = ta.lowest(low, lookback)

// Entry conditions
long_breakout = close > highest_high[1]
short_breakout = close < lowest_low[1]

// Position sizing based on account size (approximate)
account_sizes = map.new<string, float>()
map.put(account_sizes, "topstep", 150000.0)    // $150k TopStep account
map.put(account_sizes, "apex", 100000.0)       // $100k Apex account
map.put(account_sizes, "tradeday", 100000.0)   // $100k TradeDay account
map.put(account_sizes, "main", 50000.0)        // $50k personal account

account_size = map.get(account_sizes, account_group, 100000.0)
risk_amount = account_size * (risk_percent / 100.0)

// Calculate position size (simplified for ES futures)
atr = ta.atr(14)
stop_distance = atr * 2
contract_value = 50  // ES contract multiplier
position_size = math.floor(risk_amount / (stop_distance * contract_value))
position_size := math.max(position_size, 1)  // Minimum 1 contract

// Long entry
if long_breakout
    strategy.entry("Long", strategy.long, qty=position_size)
    stop_price = close - stop_distance
    alert('{"symbol": "' + syminfo.ticker + '", "action": "buy", "quantity": ' + 
          str.tostring(position_size) + ', "order_type": "market", "account_group": "' + 
          account_group + '", "strategy": "breakout_momentum", "timeframe": "' + 
          timeframe.period + '", "stop_loss": ' + str.tostring(stop_price) + 
          ', "comment": "Breakout above ' + str.tostring(highest_high[1]) + '"}', 
          alert.freq_once_per_bar)

// Short entry
if short_breakout
    strategy.entry("Short", strategy.short, qty=position_size)
    stop_price = close + stop_distance
    alert('{"symbol": "' + syminfo.ticker + '", "action": "sell", "quantity": ' + 
          str.tostring(position_size) + ', "order_type": "market", "account_group": "' + 
          account_group + '", "strategy": "breakout_momentum", "timeframe": "' + 
          timeframe.period + '", "stop_loss": ' + str.tostring(stop_price) + 
          ', "comment": "Breakdown below ' + str.tostring(lowest_low[1]) + '"}', 
          alert.freq_once_per_bar)

// Plot breakout levels
plot(highest_high[1], color=color.green, title="Resistance")
plot(lowest_low[1], color=color.red, title="Support")
```

## Setup Instructions

### 1. Configure Strategy in TradingView

1. **Create new strategy** or copy one of the examples above
2. **Set webhook URL** in strategy alerts:
   ```
   http://localhost:8000/webhook/tradingview
   ```
3. **Configure account routing** using the `account_group` parameter

### 2. Account Group Options

| Account Group | Destination | Use Case |
|---------------|-------------|----------|
| `paper_simulator` | Internal simulator | Strategy development |
| `paper_tastytrade` | Tastytrade sandbox | API testing |
| `paper_tradovate` | Tradovate demo | Futures testing |
| `main` | Primary live account | Live trading |
| `topstep` | TopStep funded account | Funded futures |
| `apex` | Apex funded account | Funded futures |
| `tradeday` | TradeDay funded account | Funded futures |
| `schwab_stocks` | Charles Schwab | Stock/ETF trading |

### 3. Alert JSON Format

Your TradingView alerts should send JSON in this format:

```json
{
  "symbol": "ES",
  "action": "buy",
  "quantity": 1,
  "order_type": "market",
  "account_group": "topstep",
  "strategy": "your_strategy_name",
  "timeframe": "5m",
  "price": 4500.25,
  "comment": "Strategy signal description"
}
```

### 4. Testing Your Strategy

1. **Start with paper trading**: Use `paper_simulator` account group
2. **Test with small sizes**: Start with 1 contract for futures, 10 shares for stocks
3. **Monitor execution**: Check TraderTerminal dashboard for order results
4. **Verify strategy performance**: Use the strategy performance tracker

### 5. Going Live

1. **Complete broker setup**: Configure your live broker credentials
2. **Test with minimal size**: Start with smallest possible position sizes
3. **Gradually increase**: Scale up as you gain confidence
4. **Monitor funded account rules**: If using prop firm accounts

## Advanced Features

### Strategy Performance Monitoring

TraderTerminal automatically tracks your strategy performance:
- Win/loss ratios
- Average profit/loss
- Maximum drawdown
- Automatic mode switching (live → paper if strategy becomes unprofitable)

### Risk Management

Built-in risk management features:
- Position size limits
- Daily loss limits for funded accounts
- Automatic strategy suspension
- Real-time P&L monitoring

### Multi-Timeframe Support

You can run the same strategy on multiple timeframes:
- Each timeframe can route to different account groups
- Strategy performance is tracked separately per timeframe
- Automatic coordination to prevent over-positioning

## Common Patterns

### 1. Paper → Live Progression
```pinescript
// Start with paper trading
account_group = input.string("paper_simulator", "Account", 
    options=["paper_simulator", "paper_tastytrade", "main"])
```

### 2. Asset-Specific Routing
```pinescript
// Route futures to Tradovate, stocks to Tastytrade
account_group = syminfo.type == "futures" ? "main" : "tastytrade_stocks"
```

### 3. Time-Based Routing
```pinescript
// Paper trading outside market hours
is_market_hours = hour >= 9 and hour <= 16
account_group = is_market_hours ? "main" : "paper_simulator"
```

This setup gives you complete control over where your TradingView strategies execute, with automatic risk management and performance tracking!