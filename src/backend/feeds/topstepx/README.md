# TopstepX API Integration Notes

## Overview

TopstepX integration for funded account management and rule enforcement.
This module provides connectivity to TopStep's API for monitoring account
metrics, enforcing trading rules, and managing funded account lifecycle.

## API Research Status

**Status**: Research Required
**Priority**: Critical Path - Week 1

### Required Actions

1. **Contact TopStep Support**
   - Email: support@topstep.com
   - Request API documentation for TopstepX platform
   - Request developer sandbox/demo credentials
   - Inquire about webhook notifications for rule violations

2. **Expected API Endpoints** (To be confirmed)
   ```
   Authentication:
   POST /api/auth/login
   POST /api/auth/refresh
   
   Account Management:
   GET /api/accounts/{id}
   GET /api/accounts/{id}/metrics
   GET /api/accounts/{id}/rules
   GET /api/accounts/{id}/violations
   
   Trading Activity:
   GET /api/accounts/{id}/trades
   GET /api/accounts/{id}/positions
   POST /api/accounts/{id}/emergency-close
   
   Monitoring:
   GET /api/accounts/{id}/realtime-metrics
   WebSocket: /ws/accounts/{id}/updates
   ```

3. **Expected Data Models**
   - Account information and status
   - Trading rules and limits
   - Real-time P&L and drawdown metrics
   - Violation alerts and notifications
   - Trading activity and audit trail

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

## Implementation Plan

### Phase 1: Research & Setup (Current)
- [ ] Contact TopStep for API access
- [ ] Obtain API documentation
- [ ] Set up developer credentials
- [ ] Understand authentication flow

### Phase 2: Core Integration
- [ ] Implement authentication
- [ ] Create account metrics polling
- [ ] Build rule enforcement engine
- [ ] Add violation detection

### Phase 3: Real-time Features
- [ ] WebSocket connectivity
- [ ] Real-time rule monitoring
- [ ] Emergency position management
- [ ] Alert notifications

## Current Implementation Status

**Stub Implementation**: Basic models and placeholder connector created for development.
The current implementation provides mock data for testing until actual API access is obtained.

### Mock Rules (For Testing)
```python
mock_rules = FundedAccountRules(
    max_daily_loss=1000,
    max_contracts=3, 
    trailing_drawdown=2000,
    profit_target=3000,
    current_daily_pnl=-250,
    current_drawdown=500
)
```

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

## Next Steps

1. **Immediate**: Contact TopStep support for API access
2. **Week 1**: Implement core rule enforcement with mock data
3. **Week 2**: Integrate real API once documentation is received
4. **Week 3**: Add advanced monitoring and violation handling

## Notes

- TopstepX is critical for funded account trading
- Rule violations can result in account termination
- Real-time monitoring is essential for compliance
- Emergency position flattening must be reliable