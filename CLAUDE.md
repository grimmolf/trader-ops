# TraderTerminal Project Context for Claude

## Project Overview

TraderTerminal (trader-ops) is an **open-source Bloomberg Terminal alternative** that provides institutional-grade trading capabilities at minimal cost ($41/month for additional data feeds). The project leverages the user's existing premium services to create a professional desktop trading platform.

### Vision
Create a comprehensive trading workstation that provides:
- **Real-time market data** via existing Tradovate (futures) and Charles Schwab (stocks/options)
- **Professional charting** via TradingView Premium webhooks (user already has)
- **Automated trading** through TradingView alerts → TraderTerminal → Broker execution
- **Funded account management** for TopStep, Apex, and TradeDay accounts
- **News and economic data** aggregation from multiple sources
- **Risk management** with funded account rules and drawdown tracking
- **Quick deployment** on macOS with Fedora as secondary target

### Target Users
- **Funded account traders** managing multiple prop firm accounts
- **Retail traders** seeking professional tools without Bloomberg's $24k/year cost
- **Algorithmic traders** using TradingView Premium for strategy development
- **macOS power users** wanting native desktop trading tools

### User's Existing Infrastructure
- ✅ **TradingView Premium** - For charting and alert generation
- ✅ **Tradovate Account** - Futures data and execution (no Rithmic needed)
- ✅ **Charles Schwab/thinkorswim** - Stocks/options data and execution
- ✅ **NinjaTrader** - Alternative futures platform
- ✅ **Multiple Funded Accounts** - TopStep, Apex, TradeDay

## Current Project Status (January 2025)

### ✅ Completed Components (What's Already Built)

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

### 🚧 Remaining Work (2-3 Weeks) - REDUCED TIMELINE

1. **TradingView Webhook Integration** (Week 1 - User has Premium, no library needed!)
2. **Tradovate Futures Integration** (Week 1 - CRITICAL for funded accounts)
3. **TopstepX API Integration** (Week 1 - CRITICAL for TopStep execution)
4. **Charles Schwab Integration** (Week 2 - For stocks/options)
5. **Funded Account Risk Management** (Week 1 - CRITICAL)
6. **Desktop UI Polish** (Week 2 - Connect real feeds)
7. **macOS Deployment** (Week 3 - Primary platform)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Desktop Application (Electron + Vue 3)      │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │ TradingView │ │  Funded     │ │   Portfolio/Risk     │  │
│  │  Webhooks   │ │  Accounts   │ │     Analytics        │  │
│  └──────┬──────┘ └──────┬──────┘ └──────────┬───────────┘  │
│         └───────────────┴────────────────────┘               │
│                    IPC Bridge                                │
└─────────────────────────┬────────────────────────────────────┘
                          │
    ┌─────────────────────┴────────────────────────────────┐
    │              Backend Services (FastAPI + WebSocket)    │
    │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
    │  │  DataHub    │  │   Webhook    │  │  Execution │  │
    │  │    ✅       │  │   Receiver   │  │   Engine   │  │
    │  └─────────────┘  └──────🚧──────┘  └─────✅─────┘  │
    └───────────────────────────────────────────────────────┘
              │                │                 │
    ┌─────────┴─────┐ ┌────────┴──────┐ ┌──────┴────────┐
    │ Market Feeds  │ │  TradingView  │ │    Brokers    │
    │ • Tradovate ✅│ │  Premium ✅   │ │ • Tradovate✅ │
    │ • Schwab 🚧   │ │  (Webhooks)   │ │ • TopstepX🚧  │
    │ • News 🚧     │ │               │ │ • Schwab 🚧   │
    └───────────────┘ └───────────────┘ └───────────────┘
```

## Key Technologies

- **Frontend**: Electron, Vue 3, TypeScript, TradingView Premium (webhooks)
- **Backend**: Python 3.11+, FastAPI, Pydantic, asyncio, Redis
- **Data Feeds**: Tradovate (futures), Charles Schwab (stocks/options), TheNewsAPI
- **Automation**: TradingView Premium webhooks (no library needed!)
- **Deployment**: macOS primary, Podman containers, Fedora secondary
- **Testing**: pytest, Playwright, GitHub Actions

## Data Feed Requirements & Costs

Total NEW monthly cost: **$41/month** (user already has main services)

| Service | Monthly Cost | Purpose | Status |
|---------|--------------|---------|--------|
| TradingView Premium | Paid | Charts & webhooks | ✅ User has |
| Tradovate | $12 | Futures data | ✅ User has |
| Charles Schwab | $0 | Stocks/options | ✅ User has |
| Tradier Pro | $10 | Alt equities feed | ⬜ Optional |
| TheNewsAPI Basic | $19 | Real-time news | ⬜ Need |
| Alpha Vantage | Free | Historical data | ⬜ Need |
| **NEW TOTAL** | **$41** | Additional feeds | - |

## Critical Path Priorities (Futures Trading First!)

### Week 1: Futures Trading MVP
1. **Day 1**: TradingView webhook receiver
2. **Day 2**: Tradovate API integration
3. **Day 3**: TopstepX connector for funded accounts
4. **Day 4**: Funded account risk management
5. **Day 5**: End-to-end futures trading test

### Week 2: Full Platform
1. **Days 1-2**: Charles Schwab integration
2. **Day 3**: Multi-broker routing
3. **Day 4**: Complete UI with real data
4. **Day 5**: Integration testing

### Week 3: Polish & Deploy
1. **Days 1-2**: macOS packaging
2. **Day 3**: Performance optimization
3. **Days 4-5**: Documentation & release

## LLM Orchestration Directives

You are **Claude**, acting as an orchestrator for the TraderTerminal project.

### Goal
- Focus on **critical path**: Futures trading through funded accounts
- Leverage user's **existing services** (TradingView Premium, Tradovate, Schwab)
- Target **2-3 week MVP** instead of longer timeline

### Allowed
✓ Calling both MCPs  
✓ Installing / running external tooling (brew, dnf, go install, podman, etc.)  
✓ Reading & writing repo files  
✓ Container orchestration via Podman  
✓ Using TradingView webhooks (user has Premium)

### Forbidden
✗ Implementing TradingView charting library (use webhooks instead)
✗ Building Rithmic data integration (user uses Tradovate/NinjaTrader)
✗ Complex multi-feed aggregation (use direct connections)
✗ Hallucinating paths or docs—mark `TODO:` if unsure  
✗ Hard-coding API keys or credentials  

### Warnings
- User trades futures on funded accounts (TopStep, Apex, TradeDay)
- macOS is primary platform, Fedora is secondary
- Focus on execution and risk management over charting
- Respect funded account rules (drawdown limits, position sizing)

## Development Guidelines

### Code Style
- **Python**: Type hints everywhere, Pydantic for validation, async/await for I/O
- **TypeScript**: Strict mode, Vue 3 Composition API, no any types
- **Documentation**: Docstrings for all public functions, README for each module

### Testing Requirements
- Unit tests for all business logic (pytest)
- Integration tests for API endpoints
- E2E tests for critical user flows (Playwright)
- Minimum 80% code coverage

### Security Practices
- Never commit API keys or secrets
- Use environment variables for all configuration
- Implement rate limiting on all endpoints
- Validate all user inputs with Pydantic
- Run containers as non-root user

### Git Workflow
- Feature branches from `main`
- Conventional commits (feat:, fix:, docs:, etc.)
- PR reviews required for all changes
- CI must pass before merge

## File Structure

```
trader-ops/
├── src/
│   ├── backend/           # FastAPI backend (95% complete)
│   │   ├── datahub/      # Main API server ✅
│   │   ├── models/       # Pydantic models ✅
│   │   ├── feeds/        # Market data connectors
│   │   │   ├── tradier.py ✅
│   │   │   ├── tradovate.py 🚧 CRITICAL PATH
│   │   │   ├── schwab.py 🚧 Week 2
│   │   │   └── topstepx.py 🚧 CRITICAL PATH
│   │   ├── trading/      # Execution engine ✅
│   │   ├── webhooks/     # TradingView receiver 🚧 CRITICAL
│   │   └── services/     # Business logic ✅
│   ├── frontend/         # Electron + Vue 3 (60% complete)
│   │   ├── electron/     # Main process ✅
│   │   ├── renderer/     # Vue application
│   │   └── components/   # UI components
│   │       └── FundedAccountPanel.vue 🚧 CRITICAL
│   └── automation/       # Kairos integration ✅
│       └── kairos_jobs/  # Strategy configurations
├── deployment/           # Container & packaging (70% complete)
│   ├── containers/       # Dockerfiles/Containerfiles
│   ├── compose/          # Docker Compose configs
│   └── scripts/          # Installation scripts
├── docs/                 # Documentation
│   └── architecture/     # PRPs and design docs
│       ├── PRPs/prps_trader_dashboard_prp.md ✅ Updated
│       ├── API_ACCESS_GUIDE.md ✅ Updated
│       └── CRITICAL_PATH_APIS.md ✅ NEW
└── tests/               # Test suites
```

## Quick Start Commands

```bash
# Backend development
cd src/backend
uv sync
uv run uvicorn src.backend.datahub.server:app --reload

# Test with mock data immediately
# Then implement Tradovate connector

# Frontend development
cd src/frontend
npm install
npm run dev

# Critical path testing
# 1. Set up TradingView webhook
# 2. Test Tradovate connection
# 3. Test funded account rules
```

## Related Projects

- **highseat**: User's other futures trading platform with similar goals
- **grimm-kairos**: Fork of timelyart/Kairos (already integrated)
- **grimm-chronos**: Fork of timelyart/chronos (lower priority now)

## Success Metrics (Revised for MVP)

The MVP will be considered successful when:
- [x] Mock data working for immediate frontend testing
- [ ] TradingView webhook → Tradovate execution working
- [ ] TopstepX integration for funded accounts complete
- [ ] Funded account risk rules enforced
- [ ] Charles Schwab integration for stocks/options
- [ ] macOS app packaged and running
- [ ] Total cost remains at $41/month for new services

## Current Priorities (January 2025)

1. **TODAY**: Get Tradovate API credentials from existing account
2. **TODAY**: Contact TopStep for API documentation
3. **Week 1**: Implement critical path (webhooks → futures execution)
4. **Week 2**: Add Charles Schwab and complete UI
5. **Week 3**: Package for macOS and release

## Important Notes

- **NO TradingView Library Needed**: User has Premium, use webhooks
- **NO Rithmic Data**: User uses Tradovate/NinjaTrader
- **Funded Accounts First**: Critical path is futures trading
- **macOS Primary**: Fedora can wait until after MVP

## Contact & Support

- **Project Lead**: @grimmolf
- **Repository**: https://github.com/grimmolf/trader-ops
- **Critical Docs**: 
  - [Updated PRP](docs/architecture/PRPs/prps_trader_dashboard_prp.md)
  - [API Access Guide](docs/architecture/API_ACCESS_GUIDE.md)
  - [Critical Path APIs](docs/architecture/CRITICAL_PATH_APIS.md)

---

*This CLAUDE.md reflects the user's actual trading setup and critical path priorities. Focus on funded account futures trading first, then expand to stocks/options.* 