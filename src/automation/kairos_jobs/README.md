# Kairos Trading Strategy Automation

This directory contains Kairos job configurations for automated trading strategy execution. Kairos serves as the strategy orchestration layer that generates alerts and webhooks for the trading execution engine.

## Architecture Overview

```
Kairos Strategies → Webhooks → DataHub → Execution Engine → Broker APIs
```

1. **Kairos** runs scheduled strategy jobs based on market data
2. **Webhooks** send trading signals to the DataHub server
3. **DataHub** processes alerts and forwards to the execution engine
4. **Execution Engine** validates, applies risk management, and executes trades
5. **Broker APIs** (Tradier) handle actual order placement and fills

## Strategy Configurations

### Current Strategies

1. **Momentum Strategy** (`momentum_strategy.yml`)
   - **Schedule**: Every 5 minutes during market hours
   - **Logic**: RSI + Volume breakout strategy
   - **Symbols**: Large-cap tech stocks (AAPL, GOOGL, MSFT, TSLA, AMD, NVDA)
   - **Risk**: 5% position size, 3% stop loss, 6% take profit

2. **Mean Reversion Strategy** (`mean_reversion_strategy.yml`)
   - **Schedule**: Every 15 minutes during market hours
   - **Logic**: Bollinger Bands + RSI extremes
   - **Symbols**: ETFs (SPY, QQQ, IWM, DIA, VTI)
   - **Risk**: 8% position size, 5% stop loss, 4% take profit

3. **Portfolio Rebalancing** (`portfolio_rebalance.yml`)
   - **Schedule**: Daily at 4:30 PM (after market close)
   - **Logic**: Target allocation maintenance with risk budgeting
   - **Allocation**: 40% SPY, 20% QQQ, 15% VTI, 10% IWM, 15% sector ETFs
   - **Rebalance Threshold**: 5% deviation from target

## Installation & Setup

### Quick Start

```bash
# 1. System setup (requires sudo)
sudo ./setup_kairos.sh system

# 2. Configure environment variables
sudo nano /etc/trader-ops/kairos.env

# 3. User setup
./setup_kairos.sh user

# 4. Start services
./setup_kairos.sh start
```

### Development Setup

```bash
# For development/testing
./setup_kairos.sh dev

# Start in development mode
./scripts/start_kairos_dev.sh
```

### Environment Configuration

Edit `/etc/trader-ops/kairos.env` with your actual credentials:

```bash
# Required
TRADIER_API_KEY=your_actual_api_key
TRADIER_ACCOUNT_ID=your_account_id
TRADINGVIEW_WEBHOOK_SECRET=your_webhook_secret

# Optional
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Strategy Development

### Creating New Strategies

1. **Copy Template**: Start with an existing strategy YAML file
2. **Modify Parameters**: Adjust symbols, indicators, and risk settings
3. **Test Configuration**: Validate YAML syntax and logic
4. **Deploy**: Add to the kairos_jobs directory

### Strategy YAML Structure

```yaml
name: strategy_name
description: "Strategy description"
schedule: "*/5 9-16 * * 1-5"  # Cron format

job:
  type: "strategy"
  strategy_id: "unique_id"
  
  parameters:
    symbols: ["AAPL", "GOOGL"]
    # Technical indicators
    rsi_period: 14
    # Risk management
    position_size: 0.05
    stop_loss: 0.03
    
  conditions:
    entry_long:
      - "rsi < 30"
      - "volume > average_volume * 1.5"
    
  webhooks:
    datahub_alerts:
      url: "http://localhost:8000/webhook/tradingview"
      payload_templates:
        long_entry:
          action: "buy"
          ticker: "{symbol}"
          # ... other fields
```

### Webhook Payload Format

Kairos sends webhooks to the DataHub in TradingView-compatible format:

```json
{
  "strategy": {
    "name": "momentum_strategy",
    "version": "1.0",
    "signal_type": "entry"
  },
  "action": "buy",
  "ticker": "AAPL",
  "contracts": 100,
  "position_size": 0.05,
  "price": 150.25,
  "timestamp": "2025-01-20T14:30:00Z",
  "alert_name": "momentum_long_entry",
  "message": "Momentum long entry signal for AAPL - RSI: 25, Volume: 2.1x"
}
```

## Monitoring & Management

### Service Management

```bash
# Check status
./setup_kairos.sh status

# View logs
./setup_kairos.sh logs

# Start/stop services
sudo systemctl start trader-kairos.timer
sudo systemctl stop trader-kairos.timer
```

### Log Files

- **Service Logs**: `journalctl -u trader-kairos.service`
- **Strategy Logs**: `/var/log/kairos/strategy_name.log`
- **Error Logs**: `/var/log/kairos/errors.log`

### Performance Monitoring

Kairos tracks execution metrics:
- Strategy execution times
- Webhook delivery success rates
- Data fetch latencies
- Signal generation frequency

## Integration with Trading System

### DataHub Integration

Kairos integrates with the DataHub server for:
- **Market Data**: Real-time quotes and historical data
- **Alert Delivery**: Webhook endpoints for trading signals
- **Portfolio Data**: Current positions and allocations

### Execution Engine Integration

The execution engine processes Kairos alerts:
1. **Risk Validation**: Checks position limits and account balance
2. **Position Sizing**: Optimizes trade size based on portfolio
3. **Order Placement**: Submits orders to broker APIs
4. **Monitoring**: Tracks fills and manages positions

### Risk Management

Multi-layer risk management:
- **Strategy Level**: Individual strategy risk parameters
- **Portfolio Level**: Overall exposure and correlation limits
- **Account Level**: Buying power and daily loss limits
- **System Level**: Circuit breakers and emergency stops

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   sudo journalctl -u trader-kairos.service
   # Check environment variables and permissions
   ```

2. **Strategies Not Executing**
   ```bash
   # Check schedule format
   systemd-analyze calendar "*/5 9-16 * * 1-5"
   
   # Verify market hours
   date
   ```

3. **Webhook Delivery Failures**
   ```bash
   # Test DataHub endpoint
   curl -X POST http://localhost:8000/webhook/tradingview \
     -H "Content-Type: application/json" \
     -d '{"action":"test","ticker":"TEST"}'
   ```

4. **Permission Errors**
   ```bash
   # Fix ownership
   sudo chown -R trader:trader /var/log/kairos
   sudo chown -R trader:trader /var/lib/kairos
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Edit environment
sudo nano /etc/trader-ops/kairos.env
# Add: KAIROS_LOG_LEVEL=DEBUG

# Restart service
sudo systemctl restart trader-kairos.service
```

## Security Considerations

### API Key Protection

- Store sensitive keys in `/etc/trader-ops/kairos.env`
- Set restrictive permissions (600)
- Use environment variables, never hardcode

### Webhook Security

- Configure webhook secrets for validation
- Use HTTPS in production
- Implement rate limiting

### System Security

- Run Kairos as dedicated user (`trader`)
- Use systemd security features
- Enable firewall rules for production

## Customization

### Adding New Indicators

1. **Extend Data Sources**: Add new endpoints for custom indicators
2. **Update Conditions**: Include new indicator logic in strategy conditions
3. **Webhook Payloads**: Include indicator values in alert messages

### Multi-Timeframe Strategies

```yaml
data_sources:
  - name: "5min_data"
    endpoint: "http://localhost:8000/udf/history"
    resolution: "5"
  - name: "1hour_data"
    endpoint: "http://localhost:8000/udf/history"
    resolution: "60"
```

### Custom Notification Channels

```yaml
webhooks:
  slack_alerts:
    url: "${SLACK_WEBHOOK_URL}"
    condition: "signal_strength > 0.8"
  
  email_alerts:
    url: "${EMAIL_SERVICE_URL}"
    condition: "risk_level == 'high'"
```

## Best Practices

1. **Start Small**: Begin with paper trading and single strategies
2. **Test Thoroughly**: Validate strategies in development mode
3. **Monitor Closely**: Watch logs and performance metrics
4. **Risk Management**: Always set stop losses and position limits
5. **Diversification**: Use multiple uncorrelated strategies
6. **Regular Review**: Analyze strategy performance weekly

## Support

For issues or questions:
1. Check the logs first
2. Review configuration files
3. Test individual components
4. Create GitHub issues for bugs
5. Document improvements in the development logs

---

**⚠️ Trading Risk Warning**: Automated trading involves substantial risk. Never risk more than you can afford to lose. This software is for educational purposes and comes with no warranty.