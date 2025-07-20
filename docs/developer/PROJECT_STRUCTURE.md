# Project Structure Guide

## 📁 Directory Organization

The Trader Ops project follows a clean, maintainable structure optimized for long-term development and scalability.

### 🗂️ Top-Level Structure

```
trader-ops/
├── docs/                          # All documentation
├── src/                           # Source code
├── tests/                         # Test suites  
├── scripts/                       # Development tools
├── config/                        # Configuration files
├── build/                         # Build artifacts (generated)
├── node_modules/                  # Node.js dependencies (generated)
├── venv/                          # Python virtual environment (generated)
└── release/                       # Distribution packages (generated)
```

## 📚 Documentation (`docs/`)

Comprehensive documentation organized by audience and purpose:

```
docs/
├── README.md                      # Main project documentation
├── user/                          # End-user documentation
│   ├── TRADINGVIEW_INTEGRATION.md  # TradingView account setup
│   ├── trading-setup.md            # API configuration guide
│   └── dashboard-guide.md          # Interface walkthrough
├── developer/                     # Developer documentation
│   ├── IMPROVEMENT_REPORT.md       # Implementation details
│   ├── VALIDATION_REPORT.md        # Test results and validation
│   ├── PROJECT_STRUCTURE.md        # This file
│   └── api-reference.md            # Backend API documentation
├── api/                           # API documentation
│   ├── fastapi-docs.md             # FastAPI endpoints
│   ├── websocket-protocol.md       # Real-time data protocol
│   └── udf-integration.md          # TradingView UDF protocol
└── architecture/                  # Technical architecture
    ├── PRPs/                      # Product Requirements
    ├── system-design.md           # High-level architecture
    ├── data-flow.md              # Data flow diagrams
    └── security.md               # Security considerations
```

## 💻 Source Code (`src/`)

Clean separation of concerns across different application layers:

```
src/
├── backend/                       # Python FastAPI backend
│   ├── __init__.py               # Package initialization
│   ├── server.py                 # Main FastAPI application
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Pydantic data models
│   └── feeds/                    # Trading data connectors
│       ├── __init__.py
│       ├── tradier.py           # Tradier API integration
│       ├── tradovate.py         # Tradovate futures API
│       └── ccxt.py              # Crypto exchange APIs
├── frontend/                      # Electron + Vue frontend
│   ├── main.ts                  # Electron main process
│   ├── preload.ts               # Electron preload script
│   └── renderer/                # Vue.js renderer process
│       ├── index.html           # HTML entry point
│       ├── main.ts              # Vue application bootstrap
│       ├── App.vue              # Main Vue component
│       ├── style.css            # Global styles
│       ├── components/          # Vue components
│       └── assets/              # Static assets
├── connectors/                    # External API integrations
│   ├── brokers/                 # Broker-specific connectors
│   ├── data-providers/          # Market data providers
│   └── social/                  # Social trading platforms
└── automation/                   # Trading automation
    ├── backtests/               # Backtesting engine
    ├── chronos/                 # Execution system
    └── kairos_jobs/             # Alert configurations
```

## 🧪 Tests (`tests/`)

Comprehensive test coverage across all application layers:

```
tests/
├── __init__.py                   # Test package initialization
├── unit/                         # Unit tests
│   ├── __init__.py
│   ├── test_models.py           # Data model validation
│   ├── test_datahub.py          # Backend API tests
│   ├── test_tradier.py          # Tradier connector tests
│   └── test_frontend.py         # Frontend component tests
├── integration/                  # Integration tests
│   ├── test_api_integration.py  # API integration tests
│   ├── test_websocket.py        # Real-time data tests
│   └── test_electron.py         # Electron app tests
├── e2e/                         # End-to-end tests
│   ├── test_trading_flow.py     # Complete trading workflows
│   ├── test_authentication.py   # TradingView auth tests
│   └── test_performance.py      # Performance benchmarks
└── fixtures/                    # Test data and mocks
    ├── mock_data.py             # Mock market data
    ├── test_configs.py          # Test configurations
    └── sample_responses.json     # API response samples
```

## ⚙️ Scripts (`scripts/`)

Development and deployment automation:

```
scripts/
├── start_dev.sh                 # Development environment startup
├── build.sh                     # Production build script
├── test.sh                      # Test execution script
├── deploy.sh                    # Deployment automation
├── backup.sh                    # Data backup script
└── maintenance/                 # Maintenance utilities
    ├── cleanup.sh               # Cleanup temporary files
    ├── update_deps.sh           # Update dependencies
    └── health_check.sh          # System health verification
```

## 🔧 Configuration (`config/`)

Centralized configuration management:

```
config/
├── .env.example                 # Environment variables template
├── tsconfig.json               # TypeScript compiler configuration
├── tsconfig.main.json          # Electron main process TypeScript config
├── vite.config.ts              # Vite build tool configuration
├── environments/               # Environment-specific configs
│   ├── development.json        # Development environment
│   ├── production.json         # Production environment
│   └── testing.json            # Testing environment
└── docker/                     # Docker configurations
    ├── Dockerfile              # Main Docker image
    ├── docker-compose.yml      # Multi-service deployment
    └── .dockerignore           # Docker build exclusions
```

## 🏗️ Build System Integration

### TypeScript Configuration
- **Main Process**: `config/tsconfig.main.json` - Electron main process compilation
- **Renderer**: `config/tsconfig.json` - Vue.js frontend compilation
- **Build Output**: `build/` directory

### Python Package Structure
- **Backend Module**: `src.backend` - FastAPI application
- **Automation**: `src.automation` - Trading automation components
- **Tests**: Pytest configuration in `pyproject.toml`

### Build Artifacts (`build/`)
```
build/                           # Generated during build process
├── main.js                     # Compiled Electron main process
├── preload.js                  # Compiled Electron preload script
└── renderer/                   # Compiled Vue.js frontend
    ├── index.html
    ├── assets/
    └── *.js, *.css files
```

## 🔄 Development Workflow

### File Organization Principles

1. **Separation of Concerns**: Each directory has a single responsibility
2. **Language Grouping**: Python and TypeScript code separated
3. **Feature Modules**: Related functionality grouped together
4. **Clear Dependencies**: Import paths reflect directory structure

### Import Path Standards

```python
# Backend imports
from src.backend.config import settings
from src.backend.models import Quote, Symbol
from src.backend.feeds.tradier import TradierClient

# Test imports
from src.backend.server import app
from tests.fixtures.mock_data import sample_quote
```

```typescript
// Frontend imports (relative paths)
import { TradingViewMode } from './types'
import QuoteDisplay from '../components/QuoteDisplay.vue'
import { formatPrice } from '../utils/formatting'
```

### Configuration Management

1. **Environment Variables**: `.env` files for sensitive data
2. **Type Safety**: Pydantic models for Python, TypeScript interfaces
3. **Validation**: Configuration validation at startup
4. **Environment Separation**: Different configs per environment

## 📊 Maintenance Guidelines

### File Cleanup Rules

**Temporary Files** (auto-cleaned):
- `build/` - Regenerated on each build
- `node_modules/` - Reinstall with `npm install`
- `venv/` - Recreate virtual environment
- `*.pyc`, `__pycache__/` - Python bytecode cache

**Development Files** (keep):
- Source code in `src/`
- Tests in `tests/`
- Documentation in `docs/`
- Configuration in `config/`

**Generated Files** (version control ignore):
- Build artifacts
- Environment files (`.env`)
- IDE configuration (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)

### Dependency Management

**Python**: `pyproject.toml`
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
# ... other dependencies
```

**Node.js**: `package.json`
```json
{
  "dependencies": {
    "electron": "^27.1.2",
    "vue": "^3.3.8"
  },
  "devDependencies": {
    "typescript": "^5.2.2",
    "@types/node": "^20.9.0"
  }
}
```

## 🎯 Best Practices

### Directory Naming
- **kebab-case** for directories (`config/`, `e2e/`)
- **snake_case** for Python modules (`test_models.py`)
- **camelCase** for TypeScript files (`App.vue`, `main.ts`)

### File Organization
- **Single Responsibility**: One main concern per file
- **Logical Grouping**: Related functionality together
- **Clear Naming**: Descriptive, unambiguous names
- **Consistent Structure**: Same patterns across modules

### Documentation Standards
- **README** in each major directory
- **Inline comments** for complex logic
- **API documentation** for public interfaces
- **Architecture diagrams** for system overview

---

This structure supports **scalable development**, **clear maintenance**, and **easy onboarding** for new team members while maintaining **separation of concerns** and **clean architecture principles**.