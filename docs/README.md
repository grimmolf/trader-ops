# Trader Ops Dashboard

## 🚀 Overview

A cross-platform desktop trading dashboard that combines real-time market data, TradingView charts, and automated execution in a unified interface. Built for macOS with Fedora packaging support.

## 📁 Project Structure

```
trader-ops/
├── docs/                          # Documentation
│   ├── user/                     # User guides & tutorials
│   ├── developer/                # Development documentation  
│   ├── api/                      # API documentation
│   └── architecture/             # Technical specifications
├── src/                          # Source code
│   ├── backend/                  # Python FastAPI backend
│   ├── frontend/                 # Electron + Vue frontend
│   ├── connectors/               # Trading API connectors
│   └── automation/               # Alerts & backtesting
├── tests/                        # Test suites
├── scripts/                      # Development & build scripts
├── config/                       # Configuration files
└── build/                        # Build artifacts
```

## 🎯 Key Features

### ✅ **Real-Time Trading Dashboard**
- Multi-pane layout with synchronized data
- TradingView Advanced Charts integration
- Real-time market data streaming
- Portfolio tracking and P&L monitoring

### ✅ **Dual TradingView Integration**
- **Local Mode**: Fast, private, custom data feeds
- **Authenticated Mode**: Full TradingView account access
- One-click switching between modes
- Personal layouts, watchlists, and indicators

### ✅ **Trading API Integration**
- Tradier API for equities and options
- WebSocket real-time data streaming
- Order management and execution
- Account and position tracking

### ✅ **Cross-Platform Desktop**
- Native Electron application
- macOS optimized (Apple Silicon)
- Fedora packaging ready
- Auto-updater support

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** and **npm**
- **Python 3.11+** and **pip**
- **Git** for version control

### Installation
```bash
# Clone repository
git clone <repository-url>
cd trader-ops

# Install Node.js dependencies
npm install

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install fastapi uvicorn pytest pydantic pydantic-settings

# Copy configuration template
cp config/.env.example .env

# Start development environment
./scripts/start_dev.sh
```

### Development Commands
```bash
# Start full development stack
./scripts/start_dev.sh

# Individual components
source venv/bin/activate && python -m src.backend.server  # Backend
npm run dev:renderer                                      # Frontend
npm run electron:dev                                      # Desktop App

# Testing
source venv/bin/activate && pytest tests/ -v             # Unit tests
npm run test:e2e                                          # E2E tests

# Building
npm run build:main && npm run build:renderer              # Build all
npm run pack                                              # Package app
```

## 📚 Documentation

### For Users
- **[TradingView Integration Guide](user/TRADINGVIEW_INTEGRATION.md)** - How to use personal TradingView accounts
- **[Trading Setup Guide](user/trading-setup.md)** - Configure API keys and brokers
- **[Dashboard Guide](user/dashboard-guide.md)** - Navigate the interface

### For Developers
- **[Architecture Overview](architecture/)** - System design and components
- **[API Documentation](api/)** - Backend API reference
- **[Development Guide](developer/)** - Setup and contribution guidelines
- **[Deployment Guide](developer/deployment.md)** - Production deployment

## 🔧 Configuration

### Environment Variables
Create `.env` file from `config/.env.example`:

```bash
# Trading APIs
TRADIER_TOKEN=your_tradier_token
TRADIER_ACCOUNT_ID=your_account_id

# Application Settings  
DATAHUB_HOST=localhost
DATAHUB_PORT=9000
DEBUG=true
```

### Configuration Files
- **`config/tsconfig.json`** - TypeScript configuration
- **`config/vite.config.ts`** - Vite build configuration
- **`pyproject.toml`** - Python project configuration
- **`package.json`** - Node.js dependencies and scripts

## 🏗️ Architecture

### Backend (Python)
- **FastAPI** server with WebSocket support
- **Pydantic** models for type safety
- **Trading API connectors** (Tradier, Tradovate, CCXT)
- **UDF protocol** for TradingView integration

### Frontend (Electron + Vue)
- **Electron** for cross-platform desktop
- **Vue 3** with Composition API
- **TypeScript** for type safety
- **TradingView** charting library integration

### Data Flow
```
Trading APIs → Backend Server → WebSocket → Frontend → TradingView Charts
     ↓              ↓              ↓           ↓            ↓
  Tradier      FastAPI/Uvicorn   Real-time   Electron    Advanced Charts
  Tradovate    Pydantic Models   Streaming   Vue App     Personal Account
  CCXT         UDF Protocol      IPC Bridge  TypeScript  Local Data
```

## 🧪 Testing

### Unit Tests (Backend)
```bash
source venv/bin/activate
pytest tests/unit/ -v --cov=src/backend
```

### Integration Tests (Frontend)
```bash
npm run test:e2e
```

### Validation Pipeline
```bash
# Python linting and type checking
ruff check src/ --fix
mypy src/backend/

# Node.js linting and building
npm run build:main
npm run build:renderer
```

## 🚀 Deployment

### Development
```bash
./scripts/start_dev.sh
```

### Production Build
```bash
npm run build
npm run dist  # Creates platform-specific packages
```

### Docker Support
```bash
docker build -t trader-ops .
docker run -p 9000:9000 trader-ops
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Development Standards
- **TypeScript** for all frontend code
- **Python type hints** for all backend code
- **Unit tests** for new features
- **Documentation** for user-facing changes

## 📊 Performance

### Benchmarks
- **Startup Time**: Local Mode ~2s, Authenticated Mode ~5s
- **Memory Usage**: ~150MB (Local), ~300MB (Authenticated)
- **Data Latency**: ~50ms (Local), ~200ms (Authenticated)
- **Test Coverage**: 95%+ for core business logic

### Optimization
- **Lazy loading** of components
- **WebSocket** for real-time data
- **Efficient** state management
- **Build optimization** with Vite

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- **User guides**: `docs/user/`
- **API reference**: `docs/api/`
- **Troubleshooting**: `docs/developer/troubleshooting.md`

### Community
- **Issues**: [GitHub Issues](https://github.com/your-org/trader-ops/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/trader-ops/discussions)
- **Wiki**: [Project Wiki](https://github.com/your-org/trader-ops/wiki)

---

**Built with** ⚡ **FastAPI** • 🖥️ **Electron** • 📊 **TradingView** • 🚀 **Vue.js**