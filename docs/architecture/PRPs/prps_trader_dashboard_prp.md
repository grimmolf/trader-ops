# PRP: Unified TraderTerminal Dashboard with Backtesting & Containerization

## Metadata
- **Feature Name**: TraderTerminal Desktop Dashboard with Integrated Backtesting
- **Date**: July 2025
- **Confidence Score**: 9/10
- **Estimated Implementation Time**: 2-3 weeks for MVP (reduced from 3-4 weeks)
- **Primary Technologies**: Electron/Tauri, FastAPI, TradingView Premium Webhooks, Tradovate, Tastytrade, Charles Schwab
- **Target Platforms**: macOS (Apple Silicon) primary, Fedora 40+ secondary

## Executive Summary

This PRP defines the completion of the TraderTerminal ecosystem - an open-source Bloomberg Terminal alternative that provides institutional-grade trading capabilities at minimal cost ($41/month for additional data feeds). The project aims to create a professional desktop trading platform that rivals Bloomberg Terminal functionality while leveraging the user's existing premium services.

### Vision
Create a comprehensive trading workstation that provides:
- **Real-time market data** via existing Tradovate (futures) and Charles Schwab (stocks/options)
- **Professional charting** via TradingView Premium webhooks (user already has)
- **Automated trading** through TradingView alerts → TraderTerminal → Broker execution
- **Funded account management** for TopStep, Apex, and TradeDay accounts
- **News and economic data** aggregation from multiple sources
- **Risk management** with funded account rules and drawdown tracking
- **Quick deployment** on macOS with Fedora as secondary target

### User's Existing Infrastructure
- ✅ **TradingView Premium** - For charting and alert generation
- ✅ **Tradovate Account** - Futures data and execution
- ✅ **Charles Schwab/thinkorswim** - Stocks/options data and execution
- ✅ **NinjaTrader** - Alternative futures platform
- ✅ **Multiple Funded Accounts** - TopStep, Apex, TradeDay

## Current State (as of January 2025)

Based on development logs and code review, the project has made substantial progress:

### ✅ Completed Components

#### Backend Infrastructure (95% Complete)
- **DataHub Server** - FastAPI with TradingView UDF protocol, WebSocket streaming, mock data generation
- **Data Models** - Comprehensive Pydantic models with full type safety
- **Tradier Integration** - Complete API wrapper for equities/options with WebSocket support
- **Execution Engine** - Multi-layer risk management with webhook-driven alert processing
- **Kairos Automation** - Momentum and mean reversion strategies with SystemD integration
- **Backtesting Service** - Complete API with job queue management

#### Frontend Infrastructure (60% Complete)
- **Electron Application** - Main process with IPC bridge and macOS menu integration
- **Vue 3 Components** - TradingDashboard, TradingViewChart, Watchlist, OrderEntry, etc.
- **Missing**: Real data connections, funded account dashboards

#### DevOps Infrastructure (70% Complete)
- **GitHub Actions** - Comprehensive CI/CD pipeline
- **Containerization** - Containerfiles for all services, install scripts for Fedora/macOS
- **Missing**: Chronos container, TimescaleDB integration

### 🚧 Remaining Work (2-3 Weeks)

#### Critical Path Items (Revised for User's Setup)
1. **Webserver-First Frontend Refactor** (Pre-Work – foundational for cross-platform deployment)
2. **TradingView Webhook Integration** (Week 1 – already has Premium)
3. **Tradovate Futures Integration** (Week 1 – CRITICAL for funded accounts)
4. **Tastytrade Integration** (Week 1 – futures & options while waiting on other keys)
5. **Paper Trading Implementation** (Week 1 – test strategies safely)
6. **Strategy Performance Monitoring** (Week 1 – auto-rotation between live/paper)
7. **TopstepX API Integration** (Week 1 – CRITICAL for TopStep execution)
8. **Charles Schwab Integration** (Week 2 – stocks/options)
9. **Funded Account Risk Management** (Week 1 – CRITICAL)
10. **Desktop UI Polish** (Week 2 – connect real feeds, add dashboards)
11. **Deployment & Packaging** (Week 3 – macOS primary)

## LLM Orchestration Directives

You are **Claude**, acting as an orchestrator for the TraderTerminal project.

### Goal
- Spawn **planning-agents** (OpenAI MCP · o3) to break work into milestones.  
- Spawn **file-analysis-agents** (Gemini MCP · 2.5 Pro) to scan code slices and return `{file, findings}` JSON.  
- Merge all agent outputs and continue execution.

### Allowed
✓ Calling both MCPs  
✓ Installing / running external tooling (brew, dnf, go install, podman, etc.)  
✓ Reading & writing repo files
✓ Container orchestration via Podman

### Forbidden
✗ Hallucinating paths or docs—mark `TODO:` if unsure  
✗ Pushing to protected branches without user confirmation
✗ Scraping TradingView sockets  
✗ Hard-coding API keys or credentials

### Warnings
- Double-check OS-specific steps (macOS vs Fedora)
- Label assumptions with `ASSUMPTION:` for auditability
- Respect TradingView license terms (display-only widgets)
- Ensure containers run rootless for security

## Implementation Phases

> **Note**: Detailed implementation for each phase is documented separately to maintain clarity and enable focused development.

### 🎯 **NEW: Playwright GUI Automation Integration**

All phases now incorporate **automated Playwright GUI testing** for comprehensive validation:

📄 **Framework Reference**: [`PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md`](../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md)

**Integrated Testing Capabilities:**
- **Autonomous GUI Testing**: Headless browser automation for all user workflows
- **Visual Regression Detection**: Automated screenshot comparison and UI validation
- **End-to-End Trade Flow Testing**: Complete TradingView → Dashboard → Broker execution validation
- **Performance Monitoring**: Automated network request analysis and timing metrics
- **Cross-Platform Testing**: Multi-browser compatibility verification
- **Automated Debugging**: Self-diagnosing connection issues and error detection

**Key Benefits**:
- ✅ **Zero Manual Testing**: All GUI functions tested automatically
- ✅ **Rapid Issue Detection**: Problems identified within seconds, not minutes
- ✅ **Continuous Validation**: Automated testing on every code change
- ✅ **Documentation Through Testing**: Test scripts serve as living documentation

### Phase -1: Webserver-First Frontend Refactor (Pre-Work, 3-4 days)
**Objective**: Serve the TraderTerminal UI from FastAPI so it can run head-less in Kubernetes while the Electron/Tauri binary remains a thin wrapper.

📄 **See**: [`phase_-1_webserver_frontend.md`](./phases/phase_-1_webserver_frontend.md)

### Phase 0: Critical Path Futures Trading (Week 1) 🔴 URGENT
**Objective**: Implement core futures trading functionality with funded account support.

📄 **See**: [`phase_0_futures_trading.md`](./phases/phase_0_futures_trading.md)

Includes:
- Step 0.1: TradingView Webhook Setup
- Step 0.2: Tradovate Connector Implementation  
- Step 0.25: Tastytrade Connector Implementation
- Step 0.3: TopstepX Integration
- Step 0.4: Funded Account Dashboard Component
- Step 0.5: Paper Trading Implementation
- Step 0.6: Strategy Performance Monitoring & Auto-Rotation
- Step 0.7: Trade Journal Integration with TradeNote

### Phase 1: Broker Integration Sprint (Week 1)
**Objective**: Complete all broker integrations for multi-asset trading.

📄 **See**: [`phase_1_broker_integration.md`](./phases/phase_1_broker_integration.md)

### Phase 2: UI Completion Sprint (Week 2)
**Objective**: Connect real data feeds and polish the desktop interface.

📄 **See**: [`phase_2_ui_completion.md`](./phases/phase_2_ui_completion.md)

### Phase 3: Integration Testing (Week 2, Day 5)
**Objective**: Comprehensive end-to-end testing of all systems with **automated Playwright GUI validation**.

📄 **See**: [`phase_3_integration_testing.md`](./phases/phase_3_integration_testing.md)

**Enhanced with Playwright Automation**:
- **Multi-Browser GUI Testing**: Chrome, Firefox, Safari compatibility validation
- **Visual Regression Testing**: Automated screenshot comparison across builds
- **User Journey Automation**: Complete trading workflows tested automatically
- **Performance Benchmarking**: Network timing and rendering performance metrics

### Phase 4: Deployment Preparation (Week 3)
**Objective**: Package and prepare for production deployment.

📄 **See**: [`phase_4_deployment.md`](./phases/phase_4_deployment.md)

### Additional Support Tasks
**Objective**: Development tools, documentation, and quick start guides.

📄 **See**: [`support_tasks.md`](./phases/support_tasks.md)

## Revised Implementation Timeline

### Week 0: Webserver-First Frontend Refactor
- Day 0-1: Scaffold `apps/web`, share `packages/ui`.
- Day 1-2: FastAPI Static Files wiring & Docker/K8s manifests.
- Day 2-3: Electron wrapper refactor & dev scripts.
- Day 3-4: Smoke-tests & CI job.

### Week 1: Futures Trading MVP
- Day 1: TradingView webhook receiver
- Day 2: Tradovate API integration  
- Day 3: TopstepX connector & Tastytrade integration
- Day 4: Funded account risk management & Paper trading setup
- Day 5: Strategy performance monitoring & End-to-end testing

### Week 2: Full Platform Integration
- Day 1-2: Charles Schwab connector
- Day 3: Multi-broker routing
- Day 4: Complete UI with real data & TradeNote integration
- Day 5: Integration testing

### Week 3: Polish & Deployment
- Day 1-2: macOS packaging and installer
- Day 3: Performance optimization
- Day 4: Documentation
- Day 5: Beta release

### Future Phases (Post-MVP)
- Fedora Spin packaging
- NinjaTrader integration
- Advanced analytics
- Mobile companion app

## Key Advantages of User's Setup

1. **Paper Trading First Philosophy** - Built-in safety with mandatory 100+ paper trades before live
2. **Multiple Sandbox Environments** - Tradovate Demo, Tastytrade, Alpaca all available free
3. **No TradingView Library Needed** - Saves 1-2 days waiting for approval
4. **Existing Data Feeds** - Tradovate + Schwab already paid for
5. **Simplified Architecture** - No complex data aggregation needed
6. **Faster Time to Market** - 2-3 weeks instead of 3-4 weeks
7. **Lower Risk** - Using proven, existing services
8. **Automated Strategy Management** - Auto-rotation to paper when performance drops
9. **Complete Trade Lifecycle** - Backtest → Paper → Live with full tracking

## Success Metrics

### Week 1: Paper Trading Foundation
1. **Day 1-2**: Paper trading operational across all brokers (Tradovate Demo, Tastytrade Sandbox, Alpaca Paper)
   - ✅ **Playwright Validation**: Automated GUI tests confirm all broker connections functional
2. **Day 3-4**: Execute first 50 automated paper trades via TradingView webhooks
   - ✅ **Playwright Validation**: End-to-end trade flow automation confirms execution pipeline
3. **Day 5**: Complete 100+ paper trades with performance tracking active
   - ✅ **Playwright Validation**: Automated dashboard testing confirms real-time updates working

### Week 2: Live Trading Validation
4. **Day 1**: Strategy performance monitoring validates 55%+ win rate in paper
5. **Day 2-3**: Execute first LIVE automated trade via TradingView → Tradovate (minimum position size)
6. **Day 4-5**: Full platform operational with stocks/options via Schwab

### Week 3: Production Deployment
7. **Day 1-2**: Packaged macOS app ready for daily use
8. **Day 3-5**: Complete production deployment with monitoring

### Ongoing Success Criteria
- All new strategies must complete 100+ paper trades before live activation
- Strategies automatically rotate to paper trading if win rate drops below 55%
- Daily P&L tracking via TradeNote integration
- Zero manual intervention required for trade execution

## Final Validation Checklist

### Paper Trading Validation (Must Complete First)
- [ ] Paper trading operational on ALL broker sandboxes:
  - [ ] Tradovate Demo account connected and executing
    - [ ] **Playwright Test**: Automated OAuth flow validation
    - [ ] **Playwright Test**: Connection status dashboard verification
  - [ ] Tastytrade Sandbox authenticated via OAuth2
    - [ ] **Playwright Test**: Multi-step authentication flow automation
    - [ ] **Playwright Test**: Account balance and position display validation
  - [ ] Alpaca Paper account active
    - [ ] **Playwright Test**: API key validation through GUI
- [ ] Minimum 100 paper trades executed successfully
  - [ ] **Playwright Test**: Trade execution workflow automation
  - [ ] **Playwright Test**: Order status updates in real-time dashboard
- [ ] Win rate tracking shows 55%+ across paper trades
  - [ ] **Playwright Test**: Performance metrics dashboard validation
- [ ] All TradingView webhooks tested with paper accounts
  - [ ] **Playwright Test**: Webhook receiver status and processing validation
- [ ] Paper trading performance logged in TradeNote
  - [ ] **Playwright Test**: Trade journal integration and data accuracy

### Live Trading Prerequisites
- [ ] Paper trading validation complete (100+ trades)
- [ ] Funded account risk management tested in paper
- [ ] Real-time P&L tracking verified
- [ ] Emergency stop functionality tested
- [ ] Position size limits enforced

### Technical Validation
- [ ] All API credentials securely stored in environment variables
  - [ ] **Playwright Test**: Credential management interface validation
- [ ] HMAC signature verification on all webhooks
  - [ ] **Playwright Test**: Security status dashboard verification
- [ ] Strategy performance monitoring with auto-rotation active
  - [ ] **Playwright Test**: Auto-rotation notification system validation
  - [ ] **Playwright Test**: Performance threshold alert testing
- [ ] End-to-end tests passing for all critical paths
  - [ ] **Playwright Test Suite**: Complete user journey automation (100+ test scenarios)
  - [ ] **Playwright Test**: Visual regression testing across all components
  - [ ] **Playwright Test**: Cross-browser compatibility validation
- [ ] Desktop app packaged and installable on macOS
  - [ ] **Playwright Test**: Desktop app launcher and window management
  - [ ] **Playwright Test**: Native menu integration and keyboard shortcuts

### Documentation & Operations
- [ ] Paper trading guide documented
- [ ] Strategy migration process (paper → live) documented
- [ ] Emergency procedures documented
- [ ] TradeNote backup procedures in place

## Risk Mitigation

### Primary Protection: Paper Trading First

1. **Mandatory Paper Trading**: All strategies must complete 100+ paper trades before live activation
   - Validates system functionality without financial risk
   - Proves strategy viability in real market conditions
   - Identifies edge cases and error scenarios safely

### Technical Risk Mitigation

2. **Strategy Underperformance**: Automatic rotation to paper trading when win rate < 55%
3. **API Access Delays**: Multiple broker sandboxes available (Tradovate Demo, Tastytrade, Alpaca)
4. **Funded Account Protection**: Rules enforcement tested in paper before risking evaluation accounts
5. **Data Feed Interruptions**: Automatic reconnection with exponential backoff
6. **Performance Issues**: Circuit breakers and rate limiting on all connections

### Operational Risk Mitigation

7. **Position Sizing**: Start with minimum sizes when transitioning from paper to live
8. **Emergency Stops**: Kill switch to halt all trading immediately
9. **Audit Trail**: All trades logged in TradeNote for review and analysis
10. **Gradual Scaling**: Increase position sizes only after proven live performance

## Post-MVP Roadmap

1. **Month 1**: NinjaTrader integration for alternative execution
2. **Month 2**: Advanced analytics dashboard with ML-based insights
3. **Month 3**: Mobile companion app for monitoring
4. **Month 4**: Social trading features for strategy sharing
5. **Month 6**: Cloud deployment option for 24/7 operation

## Document History

- **v1.0** (2025-01-20): Initial PRP creation
- **v1.1** (2025-01-20): Added strategy performance monitoring & auto-rotation
- **v1.2** (2025-01-20): Added TradeNote integration for trade journaling
- **v1.3** (2025-01-20): Restructured into master + phase-specific documents

## Related Documents

- [`IMPLEMENTATION_SUMMARY.md`](../../IMPLEMENTATION_SUMMARY.md) - Current implementation status
- [`docs/QUICK_START.md`](../../QUICK_START.md) - Getting started guide
- [`docs/PAPER_TRADING_GUIDE.md`](../../PAPER_TRADING_GUIDE.md) - Paper trading requirements and best practices
- [`docs/TRADINGVIEW_ALERTS.md`](../../TRADINGVIEW_ALERTS.md) - Webhook configuration
- [`docs/TRADE_JOURNAL.md`](../../TRADE_JOURNAL.md) - TradeNote setup guide


