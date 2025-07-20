# Trader Ops Dashboard

A comprehensive cross-platform trading dashboard built with Electron, Vue.js, and FastAPI. Features real-time market data integration, TradingView Advanced Charts, and professional trading tools.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-18%2B-green.svg)
![Electron](https://img.shields.io/badge/electron-latest-lightgrey.svg)

## 🚀 Features

### 📊 Advanced Charting
- **TradingView Integration**: Full TradingView Advanced Charts widget with professional indicators
- **Dual Authentication**: Local data mode + Personal TradingView account integration
- **Real-time Data**: Live market data streaming via WebSocket connections
- **Multiple Timeframes**: Support for all standard trading timeframes

### 📈 Market Data Integration
- **Tradier API**: Real-time equity and options data with WebSocket streaming
- **UDF Protocol**: TradingView Universal Data Feed implementation
- **Historical Data**: Complete OHLCV historical data support
- **Symbol Search**: Advanced symbol lookup and market search

### 🖥️ Cross-Platform Desktop App
- **Electron Framework**: Native desktop experience on macOS, Windows, and Linux
- **Vue.js Frontend**: Reactive UI with modern component architecture
- **IPC Communication**: Seamless data flow between main and renderer processes
- **Responsive Design**: Optimized for various screen sizes and resolutions

### ⚡ Real-time Performance
- **WebSocket Streaming**: Sub-second market data updates
- **Efficient Data Flow**: Optimized data pipeline for minimal latency
- **Memory Management**: Smart caching and data retention strategies
- **Background Processing**: Non-blocking data operations

### 🔧 Development Tools
- **Automated Logging**: Comprehensive development session tracking
- **Git Integration**: Smart hooks for development workflow
- **Type Safety**: Full TypeScript and Python type checking
- **Testing Suite**: Unit, integration, and E2E test coverage

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## ⚡ Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/trader-ops.git
cd trader-ops

# Install dependencies
./scripts/start_dev.sh

# Run development servers
npm run dev          # Frontend (Electron)
python -m uvicorn src.backend.server:app --reload  # Backend API
```

Open the Electron app and start trading with real-time market data!

## 🔧 Installation

### Prerequisites

- **Python 3.11+** with Poetry
- **Node.js 18+** with npm
- **Git** for version control
- **Tradier Account** (optional, for live data)

### System Setup

```bash
# macOS
brew install python node poetry

# Ubuntu/Debian
sudo apt install python3.11 nodejs npm
curl -sSL https://install.python-poetry.org | python3 -

# Windows
# Install Python from python.org
# Install Node.js from nodejs.org
# Install Poetry from python-poetry.org
```

### Project Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/trader-ops.git
cd trader-ops

# 2. Install Python dependencies
poetry install

# 3. Install Node.js dependencies
npm install

# 4. Set up environment configuration
cp .env.example .env
# Edit .env with your API keys and configuration

# 5. Set up development logging (optional)
./scripts/dev-logging/setup-hooks.sh
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Tradier API Configuration
TRADIER_API_KEY=your_tradier_api_key_here
TRADIER_ACCOUNT_ID=your_account_id_here
TRADIER_BASE_URL=https://api.tradier.com
TRADIER_WS_URL=wss://ws.tradier.com

# Development Settings
PYTHON_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:5173"]

# TradingView Configuration
TRADINGVIEW_MODE=local  # or 'authenticated'
TRADINGVIEW_WIDGET_LOCALE=en
TRADINGVIEW_THEME=dark

# Database (Future Enhancement)
# DATABASE_URL=postgresql://user:pass@localhost/traderops
```

### Tradier API Setup

1. **Create Account**: Sign up at [Tradier Developer](https://developer.tradier.com/)
2. **Get API Keys**: Generate sandbox and production API keys
3. **Set Permissions**: Ensure read/write access for market data and trading
4. **Configure Webhook**: Set up paper trading environment

### TradingView Integration

```bash
# Local Data Mode (Default)
TRADINGVIEW_MODE=local

# Personal Account Mode
TRADINGVIEW_MODE=authenticated
# Requires TradingView Pro/Premium subscription
```

## 🎯 Usage

### Starting the Application

```bash
# Option 1: Development mode (recommended)
npm run dev

# Option 2: Manual startup
# Terminal 1: Start backend
poetry run python -m uvicorn src.backend.server:app --reload --port 8000

# Terminal 2: Start frontend
npm run electron:dev
```

### Basic Operations

1. **Launch Application**: Run `npm run dev` and wait for Electron window
2. **Select Symbol**: Use search bar to find stocks/ETFs (e.g., "AAPL", "SPY")
3. **Configure Chart**: Choose timeframe, indicators, and drawing tools
4. **Switch Modes**: Toggle between local data and TradingView account mode
5. **Real-time Data**: Watch live price updates and volume data

### Advanced Features

#### TradingView Account Integration
1. Click "Switch to TradingView Account" in the top-right
2. Complete OAuth authentication in popup window
3. Access your personal watchlists, indicators, and saved layouts
4. Seamlessly switch back to local mode anytime

#### Symbol Management
```javascript
// Search for symbols
const symbols = await searchSymbols("AAPL");

// Subscribe to real-time data
const stream = subscribeToSymbol("AAPL");
stream.onData(data => console.log(data));
```

#### Market Data API
```python
# Python backend usage
from src.backend.feeds.tradier import TradierConnector

connector = TradierConnector()
quotes = await connector.get_quotes(["AAPL", "GOOGL"])
stream = connector.websocket_stream(["AAPL"])
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Electron      │    │   FastAPI       │    │   External      │
│   Frontend      │◄──►│   Backend       │◄──►│   APIs          │
│                 │    │                 │    │                 │
│ ├─ Vue.js       │    │ ├─ WebSocket    │    │ ├─ Tradier      │
│ ├─ TradingView  │    │ ├─ UDF Protocol │    │ ├─ TradingView  │
│ ├─ TypeScript   │    │ ├─ REST API     │    │ └─ Future APIs  │
│ └─ IPC          │    │ └─ Data Models  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

#### Frontend (Electron + Vue.js)
- **Main Process**: Application lifecycle, window management, IPC handling
- **Renderer Process**: Vue.js app with TradingView widget integration
- **Preload Script**: Secure IPC bridge between main and renderer
- **Component Structure**: Modular Vue components for different features

#### Backend (FastAPI)
- **API Server**: RESTful endpoints and WebSocket connections
- **UDF Implementation**: TradingView Universal Data Feed protocol
- **Data Connectors**: Pluggable architecture for multiple data sources
- **Real-time Engine**: WebSocket streaming and data distribution

#### Data Flow
1. **Symbol Selection**: Frontend → IPC → Backend → Data Source
2. **Historical Data**: Backend → UDF Protocol → TradingView Widget
3. **Real-time Updates**: WebSocket → Backend → IPC → Frontend
4. **Authentication**: Frontend ↔ Backend ↔ External OAuth

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Desktop | Electron 26+ | Cross-platform native app |
| Frontend | Vue.js 3 + TypeScript | Reactive UI framework |
| Charting | TradingView Advanced Charts | Professional trading charts |
| Backend | FastAPI + Python 3.11 | High-performance API server |
| Data | Pydantic + WebSockets | Type-safe data modeling |
| Build | Vite + Poetry | Modern build tools |
| Testing | Vitest + Pytest | Comprehensive test coverage |

## 📚 API Documentation

### REST Endpoints

#### Market Data
```http
GET /api/v1/quotes?symbols=AAPL,GOOGL
GET /api/v1/history/{symbol}?interval=daily&from=2024-01-01&to=2024-12-31
GET /api/v1/search?query=apple&limit=10
```

#### TradingView UDF Protocol
```http
GET /udf/config
GET /udf/symbols?symbol=AAPL
GET /udf/history?symbol=AAPL&resolution=D&from=1609459200&to=1640995200
```

#### WebSocket Streams
```javascript
// Connect to real-time data stream
const ws = new WebSocket('ws://localhost:8000/stream');

// Subscribe to symbols
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['AAPL', 'GOOGL']
}));

// Handle real-time data
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time quote:', data);
};
```

### Data Models

#### Quote Model
```typescript
interface Quote {
  symbol: string;
  timestamp: number;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  change: number;
  changePercent: number;
}
```

#### Candle Model
```typescript
interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
```

For complete API documentation, visit `/docs` when running the development server.

## 🛠️ Development

### Development Environment

```bash
# Set up development environment
poetry shell                    # Activate Python virtual environment
npm run dev                     # Start development servers
npm run test                    # Run all tests
npm run lint                    # Check code quality
```

### Project Structure

```
trader-ops/
├── src/
│   ├── backend/               # Python FastAPI backend
│   │   ├── server.py         # Main API server
│   │   ├── models.py         # Pydantic data models
│   │   ├── feeds/            # Data connector implementations
│   │   │   └── tradier.py    # Tradier API integration
│   │   └── config.py         # Configuration management
│   └── frontend/             # Electron + Vue.js frontend
│       ├── main.ts           # Electron main process
│       ├── preload.ts        # IPC preload script
│       └── renderer/         # Vue.js renderer process
│           ├── App.vue       # Main application component
│           ├── components/   # Vue components
│           └── assets/       # Static assets
├── config/                   # Build and TypeScript configuration
├── docs/                     # Comprehensive documentation
├── scripts/                  # Development and deployment scripts
│   └── dev-logging/         # Automated development logging
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   └── e2e/                 # End-to-end tests
├── package.json             # Node.js dependencies and scripts
├── pyproject.toml           # Python dependencies and configuration
└── README.md                # This file
```

### Development Logging

The project includes an automated development logging system:

```bash
# Set up logging hooks
./scripts/dev-logging/setup-hooks.sh

# Manual logging
python scripts/dev-logging/log-prompt.py

# Manage logs
python scripts/dev-logging/manage-logs.py list
python scripts/dev-logging/manage-logs.py search "feature"
python scripts/dev-logging/manage-logs.py stats
```

### Code Quality

```bash
# Python
poetry run ruff check src/          # Linting
poetry run mypy src/                # Type checking
poetry run black src/               # Code formatting

# JavaScript/TypeScript
npm run lint                        # ESLint
npm run type-check                  # TypeScript validation
npm run format                      # Prettier formatting
```

### Git Workflow

```bash
# Standard development workflow
git checkout -b feature/new-feature
# Make changes...
git add .
git commit -m "Add new feature"     # Triggers development logging
git push origin feature/new-feature
# Create pull request
```

## 🧪 Testing

### Test Suite Overview

- **Unit Tests**: Individual component and function testing
- **Integration Tests**: API endpoint and data flow testing
- **E2E Tests**: Full application workflow testing
- **Performance Tests**: WebSocket and data streaming validation

### Running Tests

```bash
# All tests
npm test

# Python backend tests
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v

# Frontend tests
npm run test:unit
npm run test:e2e

# Coverage reports
npm run coverage
poetry run pytest --cov=src tests/
```

### Test Structure

```bash
tests/
├── unit/
│   ├── test_models.py           # Pydantic model validation
│   ├── test_datahub.py          # API endpoint testing
│   └── test_tradier.py          # Tradier connector testing
├── integration/
│   ├── test_websocket.py        # WebSocket functionality
│   └── test_udf_protocol.py     # TradingView UDF testing
└── e2e/
    ├── test_app_launch.py       # Application startup
    ├── test_symbol_search.py    # Symbol search workflow
    └── test_data_streaming.py   # Real-time data flow
```

### Mocking and Test Data

```python
# Example test with mocked data
@pytest.fixture
def mock_tradier_response():
    return {
        "quotes": {
            "quote": {
                "symbol": "AAPL",
                "last": 150.00,
                "volume": 1000000
            }
        }
    }

def test_quote_parsing(mock_tradier_response):
    connector = TradierConnector()
    quotes = connector.parse_quotes(mock_tradier_response)
    assert quotes[0].symbol == "AAPL"
    assert quotes[0].last == 150.00
```

## 🚀 Deployment

### Build Production App

```bash
# Build backend
poetry build

# Build frontend
npm run build

# Package Electron app
npm run electron:build

# Generated files:
# ├── dist/electron/           # Electron distributables
# ├── dist/web/               # Web build (if needed)
# └── dist/python/            # Python package
```

### Distribution

```bash
# macOS
npm run electron:build:mac

# Windows
npm run electron:build:win

# Linux
npm run electron:build:linux

# All platforms
npm run electron:build:all
```

### Environment Configuration

```bash
# Production environment variables
PYTHON_ENV=production
TRADIER_BASE_URL=https://api.tradier.com  # Production API
LOG_LEVEL=WARNING
CORS_ORIGINS=[]
```

### Docker Deployment (Optional)

```dockerfile
# Backend container
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN poetry install --only=main
CMD ["uvicorn", "src.backend.server:app", "--host", "0.0.0.0"]
```

## 🤝 Contributing

### Getting Started

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Follow development setup in [Development](#-development) section
4. Make changes with comprehensive testing
5. Commit with descriptive messages (triggers development logging)
6. Push to your fork: `git push origin feature/amazing-feature`
7. Create a Pull Request with detailed description

### Development Standards

- **Code Style**: Follow ESLint and Ruff configurations
- **Testing**: Maintain >90% test coverage for new code
- **Documentation**: Update docs for any API or feature changes
- **Commits**: Use conventional commit messages
- **Logging**: Use development logging system for complex changes

### Pull Request Guidelines

- Clear, descriptive title and description
- Reference any related issues
- Include test coverage for new features
- Update documentation as needed
- Ensure all CI checks pass

### Issue Reporting

When reporting issues, include:
- Operating system and version
- Python and Node.js versions
- Steps to reproduce
- Expected vs actual behavior
- Relevant log files

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions
- **Development Logs**: Review `/docs/development-logs` for implementation history

## 🎯 Roadmap

### Current Version (v1.0)
- ✅ TradingView Advanced Charts integration
- ✅ Real-time Tradier data streaming
- ✅ Cross-platform Electron desktop app
- ✅ Development logging system

### Next Release (v1.1)
- 🔄 Tradovate futures data integration
- 🔄 CCXT cryptocurrency exchange support
- 🔄 Kairos alert management system
- 🔄 Chronos execution tracking

### Future Releases
- 📅 LEAN backtesting integration
- 📅 Portfolio tracking and analytics
- 📅 Multi-account management
- 📅 Advanced order types and automation

---

**Built with ❤️ for traders who demand professional tools and reliable data.**