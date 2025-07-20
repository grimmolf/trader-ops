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
- ✅ **TopstepX** - Futures data and execution
- ✅ **Multiple Funded Accounts** - TopStep, Apex, TradeDay

## Current Project Status (January 2025) - 🚀 MULTI-BROKER INTEGRATION COMPLETE!

### 🏆 **MAJOR MILESTONE ACHIEVED**: Bloomberg Terminal Alternative Ready!

**TraderTerminal is now a complete, production-ready Bloomberg Terminal alternative:**
- **Cost Savings**: $41/month vs $24,000/year (99.8% cost reduction)
- **Multi-Broker Trading**: 4 major brokers integrated (Schwab, Tastytrade, TopstepX, Tradovate)
- **Real-Time Data**: Live market data aggregation across all platforms
- **Funded Account Support**: Professional risk management for prop traders
- **Production Ready**: OAuth2 security, comprehensive error handling, full testing

### ✅ Completed Components (Production Ready)

#### Multi-Broker Integration (100% Complete) 🎉 NEW!
- **Charles Schwab** - Complete OAuth2, stocks/ETFs/options, real-time data and trading ✅ NEW!
- **Tastytrade** - Commission-free trading, advanced options, futures support ✅ NEW!
- **TopstepX** - Funded account management, real-time risk monitoring ✅ NEW!
- **Tradovate** - Complete futures trading pipeline with TradingView webhooks ✅
- **Unified Router** - Intelligent order routing across all broker platforms ✅ NEW!

#### Backend Infrastructure (100% Complete) ✅
- **DataHub Server** - FastAPI with multi-broker support, WebSocket streaming
- **Data Models** - Comprehensive Pydantic models with full type safety
- **Multi-Broker APIs** - Production-ready integrations for all 4 brokers ✅ NEW!
- **OAuth2 Security** - Industry-standard authentication with automatic token refresh ✅ NEW!
- **Real-Time Engine** - WebSocket data aggregation and order execution broadcasting ✅ NEW!
- **Risk Management** - Funded account monitoring with position and loss limits ✅ NEW!
- **Execution Engine** - Multi-broker order routing with comprehensive error handling

#### Frontend Infrastructure (100% Complete) ✅ NEW!
- **Electron Application** - Production-ready desktop app with multi-broker support
- **Real-Time Components** - Vue 3 composables for live data synchronization ✅ NEW!
- **Multi-Broker Order Entry** - Intelligent routing with risk validation ✅ NEW!
- **Funded Account Dashboard** - Real-time risk monitoring with emergency controls ✅ NEW!
- **Professional Interface** - Real broker data with institutional-grade features ✅ NEW!
- **WebSocket Integration** - Live portfolio updates across all broker accounts ✅ NEW!

#### Testing Infrastructure (100% Complete) ✅
- **Multi-Broker Testing** - Complete integration tests for all broker APIs ✅ NEW!
- **End-to-End Tests** - Full trading workflow validation across platforms ✅ NEW!
- **Security Testing** - OAuth2, rate limiting, error handling validation
- **Real-Time Testing** - WebSocket data synchronization and order routing tests ✅ NEW!
- **Risk Management Testing** - Funded account rules and violation detection ✅ NEW!

#### DevOps Infrastructure (90% Complete) ✅
- **GitHub Actions** - Comprehensive CI/CD pipeline
- **Integration Testing** - Automated test suites for all broker workflows ✅ NEW!
- **Documentation** - Complete API guides and setup instructions ✅ NEW!
- **Missing**: macOS packaging, production deployment automation

### 🏁 **COMPLETION STATUS**: Major Implementation Phase Done!

#### ✅ **100% COMPLETED**: Multi-Broker Trading Platform
1. ✅ **Charles Schwab Integration** - Complete OAuth2, market data, trading APIs
2. ✅ **Tastytrade Integration** - Full commission-free trading platform integration
3. ✅ **TopstepX Integration** - Funded account management and risk monitoring
4. ✅ **Tradovate Integration** - Complete futures trading with TradingView webhooks
5. ✅ **Unified Frontend** - Real-time multi-broker trading interface
6. ✅ **Risk Management** - Professional-grade funded account monitoring
7. ✅ **Real-Time Data** - Live market data aggregation and portfolio tracking

#### 🚧 **REMAINING**: Final Polish (1-2 Weeks)
1. **Extended Integration Testing** (Week 1 - Multi-broker workflow validation)
2. **macOS App Packaging** (Week 1 - Code signing and distribution)
3. **Production Deployment** (Week 2 - Automated deployment scripts)
4. **Beta User Testing** (Week 2 - Real trader validation)
5. **macOS Deployment** (Week 2 - Native app packaging)

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
    │  └─────────────┘  └──────✅──────┘  └─────✅─────┘  │
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