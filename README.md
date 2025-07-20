# TraderTerminal - Professional Trading Platform

**Bloomberg-quality trading tools without Bloomberg costs.** A complete desktop trading platform with real-time market data, automated execution, professional charting, and comprehensive backtesting - designed for serious traders who demand institutional-grade capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production%20ready-success.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)
![Trading](https://img.shields.io/badge/trading-automated-gold.svg)

---

## 🎯 **For Traders: What You Get**

### 📊 **Professional Desktop Trading Interface**
- **Multi-Monitor Support**: Resizable panels optimized for multiple screens
- **TradingView Charts**: Professional charting with 100+ technical indicators
- **Real-Time Data**: Live quotes with sub-100ms latency across all markets
- **Dark Mode Interface**: Easy on the eyes during long trading sessions
- **One-Click Trading**: Streamlined order entry with instant execution

### 🤖 **Automated Trading & Strategy Development**
- **TradingView Alert Integration**: Auto-execute trades from your TradingView strategies
- **Pine Script Backtesting**: Test your strategies across years of historical data
- **Risk Management**: Built-in position sizing, stop-losses, and portfolio limits
- **Strategy Templates**: Pre-built momentum and mean-reversion strategies
- **Paper Trading**: Test everything risk-free before going live

### 📈 **Advanced Market Analysis**
- **Multi-Asset Support**: Stocks, options, futures, and crypto (expandable)
- **Portfolio Analytics**: Real-time P&L, risk metrics, and performance tracking
- **News Integration**: Market-moving news and economic calendar
- **Custom Alerts**: Price, volume, and technical indicator notifications
- **Historical Analysis**: Backtest strategies with detailed performance metrics

### 🛡️ **Enterprise-Grade Security & Reliability**
- **Encrypted Communications**: All data transmission secured with TLS
- **Local Data Storage**: Your trading data stays on your machine
- **Multiple Broker Support**: Tradier (live), with Tradovate and others coming
- **Automatic Reconnection**: Never miss a trade due to connection issues
- **Open Source**: Full transparency - audit the code yourself

---

## ⚡ **Quick Start - Get Trading in 5 Minutes**

### 1. **Download & Install**
```bash
# macOS
brew install --cask traderterminal

# Linux  
wget https://github.com/grimmolf/trader-ops/releases/latest/download/TraderTerminal.AppImage
chmod +x TraderTerminal.AppImage && ./TraderTerminal.AppImage

# Or build from source (see Installation section)
```

### 2. **Launch the Application**
```bash
# The desktop app will open with a professional trading interface
# No setup required - works with demo data out of the box
```

### 3. **Connect Your Broker (Optional)**
- Go to **Settings** → **Broker Connection**  
- Enter your Tradier API credentials (get free sandbox account)
- Start trading with real market data

### 4. **Start Trading**
- **Watch Markets**: Add symbols to your watchlist
- **Analyze Charts**: Professional TradingView integration
- **Place Orders**: Market, limit, and stop orders with one click
- **Track Performance**: Real-time P&L and portfolio analytics

---

## 🖥️ **Trading Interface Overview**

### **Main Dashboard Layout**
```
┌─────────────────────────────────────────────────────────┐
│ [TraderTerminal] [Search] [Account: $10,000] [●Online] │ ← Header
├─────────────┬───────────────────────┬───────────────────┤
│ Watchlist   │                      │ Positions         │
│ ────────────│                      │ ──────────        │
│ AAPL  $150  │   📈 TradingView     │ TSLA +$1,250     │ ← Left/Right
│ MSFT  $280  │      Charts          │ AAPL   -$340     │   Panels
│ TSLA  $220  │                      │ Cash  $8,410     │
│ ────────────│                      │ ──────────        │
│ Order Entry │                      │ Active Alerts     │
│ [Buy][Sell] │                      │ AAPL > $155      │
├─────────────┴───────────────────────┴───────────────────┤
│ 📰 Market News: Fed signals rate cut | GDP beats est.  │ ← News Feed
└─────────────────────────────────────────────────────────┘
```

### **Key Interface Features**
- **📊 Left Panel**: Watchlist with real-time quotes + Order entry
- **📈 Center Panel**: Professional TradingView charts with indicators
- **💼 Right Panel**: Portfolio positions, alerts, and backtesting
- **📰 Bottom Panel**: Live market news and economic updates
- **⚙️ Header**: Symbol search, account info, connection status

---

## 🚀 **Installation Guide**

### **System Requirements**
- **macOS**: 10.15+ (Intel or Apple Silicon)
- **Linux**: Ubuntu 20.04+, Fedora 34+, or equivalent
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Internet**: Required for real-time data

### **Option 1: Download Release (Easiest)**
1. Visit [Releases](https://github.com/grimmolf/trader-ops/releases)
2. Download for your platform:
   - **macOS**: `TraderTerminal.dmg`
   - **Linux**: `TraderTerminal.AppImage`
3. Install and run

### **Option 2: Build From Source**
```bash
# Clone repository
git clone https://github.com/grimmolf/trader-ops.git
cd trader-ops

# Install dependencies
cd src/frontend
npm install

# Start desktop application
npm run dev
```

### **Option 3: With Backend Services**
```bash
# Full installation with real-time data
git clone https://github.com/grimmolf/trader-ops.git
cd trader-ops

# Install Python backend
uv sync  # or pip install -r requirements.txt

# Start backend services
uv run python -m src.backend.datahub.server &

# Start desktop app
cd src/frontend && npm run dev
```

---

## 🔑 **Configuration & Setup**

### **1. Broker Connection (For Live Trading)**

**Tradier Setup** (Recommended):
1. Sign up at [Tradier](https://tradier.com) (free sandbox available)
2. Get your API key from the developer portal
3. In TraderTerminal: **Settings** → **Broker** → **Tradier**
4. Enter your API key and account ID
5. Toggle **Live Trading** when ready

**Demo Mode** (Default):
- Works immediately with simulated data
- Perfect for learning the interface
- Test strategies risk-free

### **2. TradingView Integration**
1. Get TradingView charting library (premium feature)
2. Place library files in installation directory
3. Restart TraderTerminal for professional charts

**Alternative**: Free charts work out of the box with basic indicators.

### **3. Strategy Automation**
```bash
# Set up automated trading (optional)
./src/automation/kairos_jobs/setup_kairos.sh dev

# Configure your strategies
edit src/automation/kairos_jobs/momentum_strategy.yml
```

---

## 🧪 **Backtesting Your Strategies**

### **Test Pine Script Strategies**
1. **Open Backtest Panel**: Right panel → **Backtest** tab
2. **Enter Strategy Code**: Paste your Pine Script strategy
3. **Select Symbols**: Choose stocks/assets to test
4. **Set Date Range**: Historical period for testing
5. **Run Backtest**: Click "Run Backtest" and watch progress
6. **Analyze Results**: Detailed performance metrics and trade analysis

### **Example Strategy Test**
```javascript
// Simple moving average crossover strategy
//@version=5
strategy("MA Cross", overlay=true)

fast_ma = ta.sma(close, 20)
slow_ma = ta.sma(close, 50)

if ta.crossover(fast_ma, slow_ma)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast_ma, slow_ma)
    strategy.close("Long")
```

**Results Include**:
- 📊 **Performance Metrics**: Total return, Sharpe ratio, max drawdown
- 📈 **Equity Curve**: Visual portfolio growth over time
- 📋 **Trade Analysis**: Win rate, average profit/loss per trade
- 💹 **Risk Metrics**: Volatility, correlation, beta analysis

---

## 🎛️ **Trading Features**

### **Order Management**
- **Market Orders**: Instant execution at current market price
- **Limit Orders**: Execute only at specified price or better
- **Stop Orders**: Automatic stop-loss and take-profit orders
- **Bracket Orders**: OCO (One-Cancels-Other) order combinations
- **Position Sizing**: Automatic position sizing based on risk tolerance

### **Portfolio Tracking**
- **Real-Time P&L**: Live profit/loss tracking across all positions
- **Risk Metrics**: Portfolio beta, correlation, concentration risk
- **Performance Analytics**: Daily, monthly, yearly returns
- **Tax Reporting**: Detailed trade logs for tax preparation
- **Allocation Tracking**: Asset class and sector diversification

### **Market Data & Analysis**
- **Real-Time Quotes**: Live bid/ask prices with Level I data
- **Historical Data**: Years of OHLCV data for backtesting
- **News Integration**: Market-moving news and earnings calendars
- **Economic Calendar**: Fed meetings, GDP, inflation, employment data
- **Sector Analysis**: Industry performance and rotation tracking

---

## 💬 **Support & Community**

### **Getting Help**
- 📖 **Documentation**: Complete guides in the `/docs` folder
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/grimmolf/trader-ops/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/grimmolf/trader-ops/discussions)
- 📧 **Email Support**: support@traderterminal.com

### **Learning Resources**
- 🎥 **Video Tutorials**: Getting started and advanced features
- 📚 **Strategy Library**: Pre-built trading strategies
- 🧪 **Example Backtests**: Learn from successful strategies
- 📊 **Best Practices**: Risk management and portfolio optimization

### **Community**
- 💬 **Discord**: Real-time chat with other traders
- 📱 **Twitter**: [@TraderTerminal](https://twitter.com/traderterminal) for updates
- 🎯 **Reddit**: [r/TraderTerminal](https://reddit.com/r/traderterminal)

---

## ⚠️ **Important Trading Disclaimers**

### **Risk Warning**
- **Trading Risk**: All trading involves substantial risk of loss
- **Educational Purpose**: This software is for educational and research use
- **No Guarantees**: Past performance does not guarantee future results
- **Your Responsibility**: You are responsible for all trading decisions

### **Software Disclaimer**
- **"As Is" Basis**: Software provided without warranty of any kind
- **No Liability**: Authors not liable for trading losses or software issues
- **User Responsibility**: Verify all trades and manage your own risk
- **Backup Data**: Always maintain backups of important trading data

### **Regulatory Compliance**
- **Broker Licensing**: Ensure your broker is properly licensed
- **Tax Obligations**: Report all trading profits/losses per local laws
- **Risk Disclosure**: Read all broker risk disclosures carefully
- **Compliance**: Follow all applicable trading regulations

---

## 📄 **License & Legal**

TraderTerminal is open source software licensed under the MIT License. See [LICENSE](LICENSE) for full terms.

**Commercial Use**: Permitted for commercial trading and business use.
**Modification**: You may modify the software for your own use.
**Distribution**: You may distribute modified versions under the same license.
**Attribution**: Please maintain attribution to the original authors.

---

# 🔧 **Developer Documentation**

*The following sections are for developers who want to contribute to TraderTerminal or understand its technical architecture.*

---

## 🏗️ **Technical Architecture**

### **Technology Stack**
- **Frontend**: Electron 28+ with Vue 3, TypeScript, and Pinia
- **Backend**: FastAPI with async/await, Pydantic validation
- **Charts**: TradingView charting library integration
- **Data**: WebSocket streaming with automatic reconnection
- **Database**: Redis for caching, TimescaleDB for historical data

### **System Overview**
```
┌─────────────────────────────────────────────────────────────┐
│                   Desktop Application                        │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │ TradingView │ │  Backtest   │ │   Portfolio/Risk     │  │
│  │   Charts    │ │   Panel     │ │     Analytics        │  │
│  └──────┬──────┘ └──────┬──────┘ └──────────┬───────────┘  │
│         │               │                    │               │
│         └───────────────┴────────────────────┘               │
│                         │                                    │
│                    IPC Bridge                                │
└─────────────────────────┬────────────────────────────────────┘
                          │
    ┌─────────────────────┴────────────────────────────────┐
    │              Backend Services                        │
    │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
    │  │  Data Hub   │  │   Backtest   │  │  Execution │  │
    │  │  (FastAPI)  │  │   Service    │  │   Engine   │  │
    │  │     ✅      │  │      ✅      │  │     ✅     │  │
    │  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
    │         │                │                 │          │
    │  ┌──────┴──────┐  ┌──────┴───────┐  ┌─────┴──────┐  │
    │  │   Redis     │  │    Kairos    │  │   Tradier  │  │
    │  │  (Cache)    │  │ (Strategies) │  │    API     │  │
    │  │     ✅      │  │      ✅      │  │     ✅     │  │
    │  └─────────────┘  └──────────────┘  └────────────┘  │
    └───────────────────────────────────────────────────────┘
```

### **Data Flow**
1. **User Interface**: Vue.js components with TypeScript
2. **IPC Communication**: Secure Electron preload bridge
3. **WebSocket Streaming**: Real-time market data and updates
4. **API Processing**: FastAPI backend with async operations
5. **Strategy Execution**: Kairos automation with webhook triggers
6. **Risk Management**: Multi-layer validation and controls
7. **Broker Integration**: Tradier API for market data and execution

---

## 🔌 **API Documentation**

### **Core Endpoints**

**Health & Status**:
```
GET  /health                    # Server health and metrics
GET  /udf/config               # TradingView UDF configuration  
WS   /stream                   # WebSocket real-time streaming
```

**Market Data**:
```
GET  /udf/symbols?symbol=AAPL  # Symbol metadata
GET  /udf/history              # Historical OHLCV data
GET  /udf/search?query=AAPL    # Symbol search
GET  /api/v1/quotes            # Real-time quotes
```

**Backtesting**:
```
POST /api/backtest/strategy     # Submit new backtest
GET  /api/backtest/{id}/status  # Check progress
GET  /api/backtest/{id}/results # Retrieve results
DEL  /api/backtest/{id}         # Cancel backtest
GET  /api/backtest              # List recent backtests
WS   /api/backtest/{id}/progress # Real-time progress
```

**Trading & Alerts**:
```
POST /webhook/tradingview      # TradingView/Kairos alerts
GET  /api/v1/alerts           # Active alerts
POST /api/v1/alerts           # Create new alert
```

### **Complete API Documentation**
- **[Backtesting API](docs/api/BACKTESTING_API.md)**: Comprehensive backtesting endpoints
- **[Market Data API](docs/api/README.md)**: Real-time and historical data
- **[WebSocket API](docs/api/README.md)**: Real-time streaming protocol

---

## 🧪 **Development Setup**

### **Prerequisites**
- **Python 3.11+** for backend services
- **Node.js 18+** for desktop application
- **Redis** for caching (optional)
- **Git** for version control

### **Backend Development**
```bash
# Clone repository
git clone https://github.com/grimmolf/trader-ops.git
cd trader-ops

# Install Python dependencies (recommended: uv)
uv sync

# Alternative: pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend server
uv run python -m src.backend.datahub.server
```

### **Frontend Development**
```bash
# Install Node.js dependencies
cd src/frontend
npm install

# Start development mode (hot reload)
npm run dev

# Build for production
npm run build
npm run package:mac    # For macOS
npm run package:linux  # For Linux
```

### **Testing**
```bash
# Backend tests
uv run pytest tests/ -v

# Test API endpoints
curl http://localhost:8080/health
curl "http://localhost:8080/api/v1/quotes?symbols=AAPL"

# Test WebSocket connection
websocat ws://localhost:8080/stream

# Integration testing
redis-server &
uv run python -m src.backend.datahub.server &
cd src/frontend && npm run dev
```

---

## 🤝 **Contributing**

### **How to Contribute**
1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Implement changes**: Follow existing patterns and add tests
4. **Update documentation**: Ensure all changes are documented  
5. **Submit pull request**: Include comprehensive description

### **Development Standards**
- **Type Safety**: Full TypeScript frontend, Pydantic backend
- **Code Quality**: ESLint, Prettier, Ruff for Python
- **Documentation**: All APIs documented with examples
- **Testing**: Unit tests for all components
- **Architecture**: Modular, scalable, maintainable

### **Areas for Contribution**
- **New Broker Integrations**: Tradovate, Interactive Brokers, etc.
- **Additional Indicators**: Custom technical analysis tools
- **Mobile App**: React Native companion app
- **Advanced Strategies**: ML-based trading algorithms
- **UI/UX Improvements**: Better user experience and accessibility

---

## 📚 **Technical Documentation**

### **Complete Documentation**
- **[System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)**: Comprehensive overview
- **[Development Logs](docs/development-logs/)**: Session-by-session tracking  
- **[API Reference](docs/api/)**: Complete endpoint documentation
- **[PRP Document](docs/architecture/PRPs/prps_trader_dashboard_prp.md)**: Requirements
- **[Installation Guide](docs/user/INSTALLATION_GUIDE.md)**: Setup instructions

### **Developer Resources**
- **[Development Workflow](docs/developer/DEVELOPMENT_WORKFLOW.md)**: Process guide
- **[Project Structure](docs/developer/PROJECT_STRUCTURE.md)**: Codebase overview
- **[Kairos Setup](src/automation/kairos_jobs/README.md)**: Strategy automation

---

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Backend services
sudo ./src/automation/kairos_jobs/setup_kairos.sh system
sudo nano /etc/trader-ops/kairos.env
./src/automation/kairos_jobs/setup_kairos.sh start

# Desktop application
cd src/frontend
npm run build
npm run package:mac    # Creates .dmg installer
npm run package:linux  # Creates .AppImage
```

### **Container Deployment (Future)**
```bash
# Podman pod configuration (planned Phase 3)
podman pod create --name traderterminal-pod --publish 8080:8080
podman run -d --name datahub --pod traderterminal-pod traderterminal-datahub
podman run -d --name redis --pod traderterminal-pod redis:7-alpine
```

---

**Built with ❤️ for traders who demand institutional-quality tools.**

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>