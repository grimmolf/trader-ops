# Installation Guide

Complete guide for installing and setting up the Trader Ops trading dashboard on your system.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [First Launch](#first-launch)
- [Troubleshooting](#troubleshooting)

## 💻 System Requirements

### Minimum Requirements
- **Operating System**: macOS 11+, Windows 10+, or Ubuntu 20.04+
- **Memory**: 4 GB RAM
- **Storage**: 2 GB available space
- **Network**: Internet connection for market data

### Recommended Requirements
- **Operating System**: Latest macOS, Windows 11, or Ubuntu 22.04
- **Memory**: 8 GB+ RAM
- **Storage**: 5 GB+ available space
- **Network**: Broadband internet for real-time data
- **Display**: 1920x1080 or higher resolution

### Prerequisites
- **Python 3.11+** with UV (replaces pip/Poetry)
- **Node.js 18+** with npm
- **Git** for development setup

## ⚡ Quick Installation

### Option 1: Pre-built Releases (Recommended)
```bash
# Download the latest release for your platform
# macOS
curl -L -o trader-ops.dmg https://github.com/your-org/trader-ops/releases/latest/download/trader-ops-mac.dmg

# Windows
curl -L -o trader-ops-setup.exe https://github.com/your-org/trader-ops/releases/latest/download/trader-ops-setup.exe

# Linux
curl -L -o trader-ops.AppImage https://github.com/your-org/trader-ops/releases/latest/download/trader-ops.AppImage
```

### Option 2: Development Setup
```bash
# Clone and run
git clone https://github.com/your-org/trader-ops.git
cd trader-ops
./scripts/start_dev.sh
```

## 🔧 Detailed Setup

### Step 1: Install System Dependencies

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 node@18 git

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows
```powershell
# Install using Chocolatey (recommended)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required tools
choco install python nodejs git

# Install UV
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install required tools
sudo apt install python3.11 python3-pip nodejs npm git curl

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Clone Repository
```bash
# Clone the project
git clone https://github.com/your-org/trader-ops.git
cd trader-ops

# Verify you're in the right directory
ls -la  # Should see package.json, pyproject.toml, etc.
```

### Step 3: Install Project Dependencies
```bash
# Install Python dependencies with UV
uv sync --dev

# Install Node.js dependencies  
npm install

# Verify installations
uv run python --version      # Should show Python 3.11+
npm --version                 # Should show npm 9+
```

### Step 4: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration section below)
nano .env  # or your preferred editor
```

### Step 5: Optional Development Setup
```bash
# Set up development logging (optional but recommended)
./scripts/dev-logging/setup-hooks.sh

# Install VS Code extensions (if using VS Code)
code --install-extension ms-python.python
code --install-extension vue.volar
```

## ⚙️ Configuration

### Environment Variables
Edit your `.env` file with the following configuration:

```bash
# Application Settings
PYTHON_ENV=production                    # or 'development'
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR

# Tradier API Configuration (Optional)
TRADIER_API_KEY=your_api_key_here       # Get from https://developer.tradier.com
TRADIER_ACCOUNT_ID=your_account_id      # Your Tradier account ID
TRADIER_BASE_URL=https://api.tradier.com # Production URL
TRADIER_WS_URL=wss://ws.tradier.com     # WebSocket URL

# TradingView Settings
TRADINGVIEW_MODE=local                   # 'local' or 'authenticated'
TRADINGVIEW_THEME=dark                   # 'dark' or 'light'
TRADINGVIEW_LOCALE=en                    # Language locale

# CORS Settings (for development)
CORS_ORIGINS=["http://localhost:5173"]   # Frontend URL

# Optional: Performance Tuning
MAX_WEBSOCKET_CONNECTIONS=100            # Concurrent connections limit
QUOTE_CACHE_SIZE=1000                   # Number of quotes to cache
DATA_RETENTION_HOURS=24                 # How long to keep data
```

### Tradier API Setup (Optional)
1. **Create Account**: Go to [Tradier Developer](https://developer.tradier.com/)
2. **Get API Key**: 
   - Login to your account
   - Navigate to "API Access"
   - Generate a new API key
   - Copy the key to your `.env` file
3. **Account ID**: Find your account ID in the Tradier dashboard
4. **Sandbox vs Production**: Use sandbox for testing, production for live data

### TradingView Configuration
- **Local Mode**: Uses built-in data feeds (Tradier)
- **Authenticated Mode**: Requires TradingView Pro/Premium account
- **Theme**: Choose 'dark' or 'light' to match your preference
- **Locale**: Set language/region for TradingView widget

## 🚀 First Launch

### Start the Application
```bash
# Option 1: Integrated start (recommended)
npm run dev

# Option 2: Manual start
# Terminal 1: Backend
poetry run uvicorn src.backend.server:app --reload --port 8000

# Terminal 2: Frontend  
npm run electron:dev
```

### What to Expect
1. **Backend Server**: Starts on `http://localhost:8000`
2. **Electron Window**: Desktop application opens
3. **Initial UI**: Chart interface with symbol search
4. **Console Output**: Startup logs and connection status

### First Steps
1. **Symbol Search**: Try searching for "AAPL" or "SPY"
2. **Chart Display**: Verify charts load with mock or live data
3. **Real-time Data**: Check if quotes update (if Tradier configured)
4. **Mode Toggle**: Try switching between Local and TradingView modes

### Verify Installation
```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-01-20T15:30:00Z"}

# Check available symbols
curl http://localhost:8000/symbols

# Should return list of symbols
```

## 🔧 Troubleshooting

### Common Installation Issues

#### Python/Poetry Issues
```bash
# Poetry not found
export PATH="$HOME/.local/bin:$PATH"

# Python version conflicts
poetry env use python3.11

# Dependency conflicts
poetry lock --no-update
poetry install --no-cache
```

#### Node.js/npm Issues
```bash
# Clear npm cache
npm cache clean --force

# Remove and reinstall node_modules
rm -rf node_modules package-lock.json
npm install

# Node version issues (use nvm)
nvm install 18
nvm use 18
```

#### Electron Issues
```bash
# Rebuild native modules
npm run electron:rebuild

# Clear Electron cache
npm run electron:clean

# Permission issues (Linux)
chmod +x node_modules/.bin/electron
```

### Runtime Issues

#### Backend Won't Start
```bash
# Check Python path
poetry run which python

# Check port availability
lsof -i :8000  # Should be empty

# Verbose startup
poetry run uvicorn src.backend.server:app --reload --log-level debug
```

#### Frontend Won't Connect
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check network settings
netstat -an | grep 8000

# Try different port
BACKEND_PORT=8001 npm run dev
```

#### TradingView Integration Issues
```bash
# Clear browser cache (for Electron)
rm -rf ~/.config/trader-ops/  # Linux
rm -rf ~/Library/Application\ Support/trader-ops/  # macOS

# Check CORS settings
curl -H "Origin: http://localhost:5173" http://localhost:8000/health
```

### API Connection Issues
```bash
# Test Tradier connection
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.tradier.com/v1/markets/quotes?symbols=AAPL

# Check network connectivity
ping api.tradier.com
ping www.tradingview.com
```

### Performance Issues
```bash
# Monitor resource usage
# macOS/Linux
top -p $(pgrep -f "trader-ops")

# Windows
tasklist | findstr "trader-ops"

# Reduce memory usage
# Edit .env file:
QUOTE_CACHE_SIZE=500
MAX_WEBSOCKET_CONNECTIONS=50
```

### Getting Help
- **Logs**: Check console output and `logs/` directory
- **Issues**: Report bugs at [GitHub Issues](https://github.com/your-org/trader-ops/issues)
- **Documentation**: Review [API docs](../api/README.md) and [architecture](../architecture/SYSTEM_ARCHITECTURE.md)
- **Community**: Join discussions at [GitHub Discussions](https://github.com/your-org/trader-ops/discussions)

### Log Files
```bash
# Application logs
tail -f logs/trader-ops.log

# Development logs (if enabled)
ls docs/development-logs/

# System logs
# macOS: Console.app
# Windows: Event Viewer
# Linux: journalctl -f
```

---

**Next Steps**: After successful installation, check out the [TradingView Integration Guide](TRADINGVIEW_INTEGRATION.md) to set up advanced charting features!