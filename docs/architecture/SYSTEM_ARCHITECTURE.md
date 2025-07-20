# System Architecture

Comprehensive architectural overview of the Trader Dashboard, including system design, component interactions, and data flow patterns for automated trading with webhook-driven execution.

## 📋 Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Strategy Automation](#strategy-automation)
- [Risk Management](#risk-management)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)

## 🔍 Overview

The Trader Dashboard is a production-grade automated trading platform that combines real-time market data, TradingView charting, strategy automation via Kairos, and sophisticated risk management. The system follows an event-driven architecture with webhook-based strategy execution and comprehensive risk controls.

### Key Design Principles
- **Event-Driven**: Webhook-based strategy automation with real-time processing
- **Risk-First**: Multi-layer risk management at strategy, portfolio, and account levels  
- **Modularity**: Clear separation between data services, strategy automation, and execution
- **Performance**: Optimized for sub-100ms real-time data processing and execution
- **Security**: Secure API key management and webhook validation
- **Reliability**: Comprehensive error handling with fallback mechanisms

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Trader Dashboard Platform                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │     Kairos      │    │    DataHub      │    │  Execution      │         │
│  │   Strategies    │───►│   Server        │───►│   Engine        │         │
│  │                 │    │                 │    │                 │         │
│  │ ├─ Momentum     │    │ ├─ FastAPI      │    │ ├─ Risk Mgmt    │         │
│  │ ├─ Mean Rev     │    │ ├─ WebSocket    │    │ ├─ Position     │         │
│  │ ├─ Rebalance    │    │ ├─ UDF Protocol │    │ ├─ Portfolio    │         │
│  │ └─ Custom       │    │ ├─ Webhooks     │    │ ├─ Order Mgmt   │         │
│  └─────────────────┘    │ └─ Redis Cache  │    │ └─ Monitoring   │         │
│                         └─────────────────┘    └─────────────────┘         │
│                                  │                       │                 │
│  ┌─────────────────┐             │              ┌────────▼────────┐        │
│  │   Frontend      │◄────────────┤              │    Tradier      │        │
│  │   (Pending)     │             │              │     API         │        │
│  │                 │             │              │                 │        │
│  │ ├─ Electron     │             │              │ ├─ Market Data  │        │
│  │ ├─ TradingView  │             │              │ ├─ Orders       │        │
│  │ ├─ Dashboard    │             │              │ ├─ Positions    │        │
│  │ └─ Monitoring   │             │              │ └─ Account      │        │
│  └─────────────────┘             │              └─────────────────┘        │
│                                   │                                        │
└─────────────────────────────────┼─┼────────────────────────────────────────┘
                                  │ │
                    ┌─────────────┼─┼─────────────┐
                    │             │ │             │
            ┌───────▼──────┐ ┌────▼─▼────┐ ┌─────▼─────┐
            │ TradingView  │ │   Redis    │ │  System   │
            │  Webhooks    │ │  Cache     │ │  Services │
            │              │ │            │ │           │
            │ ├─ Alerts    │ │ ├─ Pub/Sub │ │ ├─ Systemd│
            │ ├─ Signals   │ │ ├─ State   │ │ ├─ Logging│
            │ └─ Custom    │ │ └─ Session │ │ └─ Monitor│
            └──────────────┘ └────────────┘ └───────────┘
```

## 🔧 Component Architecture

### Core Backend Services

#### DataHub Server (`src/backend/datahub/server.py`)
Central data aggregation and distribution service built with FastAPI:

- **TradingView UDF Protocol**: Complete implementation of Universal Data Feed endpoints
- **Real-Time Streaming**: WebSocket connections for live market data distribution  
- **REST API**: RESTful endpoints for quotes, symbols, and market data
- **Webhook Processing**: TradingView alert processing with background task handling
- **CORS Support**: Cross-origin resource sharing for frontend integration

**Key Endpoints**:
```
GET  /udf/config           # TradingView configuration
GET  /udf/symbols          # Symbol metadata  
GET  /udf/history          # Historical OHLCV data
GET  /udf/search           # Symbol search
GET  /api/v1/quotes        # Real-time quotes
POST /webhook/tradingview  # Alert webhooks
WS   /stream               # Real-time data streaming
```

#### Execution Engine (`src/backend/trading/execution_engine.py`)
Advanced trading execution with comprehensive risk management:

- **Webhook-Driven Processing**: Automated execution from Kairos/TradingView alerts
- **Multi-Layer Risk Management**: Account, portfolio, and position-level risk checks
- **Position Sizing**: Dynamic optimization based on portfolio allocation and risk
- **Order Lifecycle Management**: Complete order tracking from placement to fill
- **Performance Monitoring**: Real-time execution metrics and statistics

**Risk Management Layers**:
```python
1. Strategy Level:    stop_loss, position_size, max_positions
2. Portfolio Level:   concentration, correlation, allocation_limits  
3. Account Level:     buying_power, daily_loss, leverage_limits
4. System Level:      emergency_stops, circuit_breakers, volatility_filters
```

#### Tradier Connector (`src/backend/feeds/tradier.py`)
Complete Tradier API integration with real-time capabilities:

- **Market Data**: Real-time quotes, historical data, symbol search
- **Trading Operations**: Order placement, cancellation, position tracking
- **WebSocket Streaming**: Live market data with automatic reconnection
- **Rate Limiting**: Respects API limits with intelligent throttling
- **Error Handling**: Comprehensive error handling with retry logic

### Data Models (`src/backend/models/`)

#### Market Data Models
```python
class Candle(BaseModel):
    ts: int       # Epoch timestamp (TradingView compatible)
    o: float      # Open price
    h: float      # High price  
    l: float      # Low price
    c: float      # Close price
    v: float      # Volume

class Quote(BaseModel):
    symbol: str
    timestamp: int
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    volume: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
```

#### Execution Models
```python
class Order(BaseModel):
    id: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: Optional[float]
    status: OrderStatus
    
class Execution(BaseModel):
    order_id: str
    symbol: str
    quantity: float
    price: float
    timestamp: int
    commission: float
```

#### Portfolio Models  
```python
class Portfolio(BaseModel):
    id: str
    positions: List[PortfolioPosition]
    cash_balance: float
    total_value: float
    risk_metrics: Dict[str, float]
    
class PortfolioPosition(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    weight: float
    unrealized_pnl: float
```

## 🔄 Data Flow

### Real-Time Market Data Flow
```
Tradier WebSocket → DataHub Server → Redis Cache → WebSocket Clients
                 ↘                ↗              ↘
                  UDF Protocol   FastAPI        TradingView Widget
```

### Strategy Execution Flow
```
Kairos Strategy → Webhook Alert → DataHub → Execution Engine → Risk Checks → Tradier API
      ↓              ↓              ↓            ↓              ↓           ↓
   YAML Config   HTTP POST      AlertEvent   Order Creation  Validation   Order Fill
   Cron Timer    JSON Payload   Processing   Position Size   Risk Mgmt    Portfolio Update
```

### Order Lifecycle Flow
```
Alert Event → Risk Validation → Position Sizing → Order Placement → Fill Monitoring
     ↓              ↓                ↓               ↓               ↓
 Webhook Data   Account Check    Portfolio Opt    Broker API      Status Update
 Symbol/Side    Daily Limits     Allocation %     Order Submit    P&L Tracking
```

## 🛠️ Technology Stack

### Backend Services
- **FastAPI**: High-performance async web framework
- **Pydantic**: Data validation and serialization
- **Redis**: Caching, pub/sub messaging, and session storage
- **WebSocket**: Real-time data streaming
- **asyncio**: Asynchronous programming throughout

### Data & Storage
- **JSON**: Configuration and data exchange format
- **Environment Variables**: Secure configuration management
- **File System**: Local storage for logs and state

### External Integrations
- **Tradier API**: Market data and trading operations
- **TradingView**: Charting widgets and webhook alerts
- **Kairos**: Strategy automation and job scheduling

### Development & Operations
- **Python 3.11+**: Primary development language
- **Type Hints**: Comprehensive type safety with mypy
- **Systemd**: Service management and scheduling
- **Git**: Version control with development logging

## ⚙️ Strategy Automation

### Kairos Integration (`src/automation/kairos_jobs/`)

The platform uses Kairos for automated strategy execution with YAML-based job definitions:

#### Strategy Types

1. **Momentum Strategy** (`momentum_strategy.yml`)
   - **Schedule**: Every 5 minutes during market hours
   - **Logic**: RSI oversold + volume breakout  
   - **Symbols**: Large-cap tech stocks (AAPL, GOOGL, MSFT, etc.)
   - **Risk**: 5% position size, 3% stop loss, 6% take profit

2. **Mean Reversion Strategy** (`mean_reversion_strategy.yml`)
   - **Schedule**: Every 15 minutes during market hours
   - **Logic**: Bollinger Bands + RSI extremes
   - **Symbols**: ETFs (SPY, QQQ, IWM, DIA, VTI)
   - **Risk**: 8% position size, 5% stop loss, 4% take profit

3. **Portfolio Rebalancing** (`portfolio_rebalance.yml`)  
   - **Schedule**: Daily at 4:30 PM after market close
   - **Logic**: Target allocation maintenance with drift threshold
   - **Allocation**: 40% SPY, 20% QQQ, 15% VTI, 10% IWM, 15% sectors
   - **Rebalance**: Triggered on >5% allocation deviation

#### Webhook Architecture
```yaml
# Kairos Strategy Configuration
webhooks:
  datahub_alerts:
    url: "http://localhost:8000/webhook/tradingview"
    payload_templates:
      long_entry:
        action: "buy"
        ticker: "{symbol}"
        position_size: "{position_size}"
        price: "{current_price}"
        message: "Strategy signal: {strategy_name}"
```

### Systemd Integration
- **Service**: `trader-kairos.service` for continuous operation
- **Timer**: `trader-kairos.timer` for market hours scheduling  
- **Configuration**: `kairos.conf` for global settings
- **Setup**: `setup_kairos.sh` for automated deployment

## 🛡️ Risk Management

### Multi-Layer Risk Architecture

#### Strategy Level Risk
```python
risk_params = RiskParameters(
    max_position_size=0.1,      # 10% max position
    max_daily_loss=0.02,        # 2% daily loss limit  
    max_concentration=0.25,     # 25% single position limit
    min_account_balance=1000.0  # Minimum account balance
)
```

#### Portfolio Level Risk
```python
portfolio_constraints = {
    "max_positions": 10,
    "correlation_limit": 0.8,
    "sector_concentration": 0.3,
    "leverage_limit": 1.0
}
```

#### Risk Check Implementation
```python
async def comprehensive_risk_check(order: Order) -> RiskCheckResult:
    checks = [
        self._check_account_balance(),
        self._check_position_limits(),  
        self._check_daily_loss_limit(),
        self._check_market_hours(),
        self._check_concentration_risk(),
        self._check_volatility_limits()
    ]
    return aggregate_risk_results(checks)
```

### Emergency Controls
- **Emergency Stop**: Immediate halt of all trading with position liquidation
- **Circuit Breakers**: Automatic suspension on excessive volatility or losses
- **Position Limits**: Hard limits on position size and leverage
- **Market Hours**: Enforcement of trading hour restrictions

## 🚀 Deployment Architecture

### Development Environment
```bash
# Local development setup
python -m uvicorn src.backend.datahub.server:app --reload --port 8000
redis-server --port 6379
./src/automation/kairos_jobs/setup_kairos.sh dev
```

### Production Deployment

#### Systemd Services
```bash
# Kairos strategy automation
systemctl enable trader-kairos.timer
systemctl start trader-kairos.timer

# DataHub server (via custom service)
systemctl enable trader-datahub.service
systemctl start trader-datahub.service

# Redis cache
systemctl enable redis.service
systemctl start redis.service
```

#### Directory Structure
```
/opt/trader-ops/                    # Main installation
├── src/backend/                    # Backend services
├── src/automation/kairos_jobs/     # Strategy configurations
├── venv/                          # Python virtual environment
└── logs/                          # Application logs

/etc/trader-ops/                   # Configuration
├── kairos.env                     # Environment variables
└── datahub.conf                   # DataHub settings

/var/log/kairos/                   # Kairos logs
├── momentum_strategy.log
├── mean_reversion_strategy.log
└── portfolio_rebalance.log

/var/lib/kairos/                   # Strategy state
├── strategy_state/
└── execution_history/
```

#### Resource Requirements
```yaml
Minimum:
  CPU: 2 cores
  RAM: 4GB
  Disk: 20GB SSD
  Network: Broadband (low latency preferred)

Recommended:
  CPU: 4 cores  
  RAM: 8GB
  Disk: 50GB NVMe SSD
  Network: Fiber/dedicated line for trading
```

### Container Deployment (Future)
```dockerfile
# Multi-stage Docker build for production
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
CMD ["uvicorn", "src.backend.datahub.server:app", "--host", "0.0.0.0"]
```

## 🔒 Security Architecture

### API Security
```python
# Environment-based configuration
API_KEYS = {
    "tradier": os.getenv("TRADIER_API_KEY"),
    "tradingview": os.getenv("TRADINGVIEW_WEBHOOK_SECRET"),
    "datahub": os.getenv("DATAHUB_API_KEY")
}

# Header-based authentication
headers = {
    "Authorization": f"Bearer {TRADIER_API_KEY}",
    "X-Webhook-Secret": WEBHOOK_SECRET
}
```

### Webhook Validation
```python
# TradingView webhook signature verification
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### System Security
- **File Permissions**: Restrictive permissions on config files (600)
- **Process Isolation**: Dedicated user account for trading services
- **Network Security**: Firewall rules limiting external access
- **Systemd Security**: NoNewPrivileges, ProtectSystem, PrivateTmp

### Data Protection
- **API Keys**: Environment variables, never hardcoded
- **Logs**: Sanitized to exclude sensitive trading data
- **State Files**: Encrypted storage for strategy state
- **Network**: TLS for all external API communications

## ⚡ Performance Considerations

### Real-Time Requirements
```python
# Performance targets
LATENCY_TARGETS = {
    "websocket_data": "< 50ms",      # Market data delivery
    "api_response": "< 100ms",       # REST API responses  
    "risk_check": "< 25ms",          # Risk validation
    "order_execution": "< 500ms"     # End-to-end execution
}
```

### Optimization Strategies

#### Async Programming
```python
# Non-blocking I/O throughout
async def process_market_data():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_quotes(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
    return results
```

#### Caching Strategy
```python
# Redis caching for frequently accessed data
CACHE_CONFIG = {
    "quotes": {"ttl": 1, "key": "quote:{symbol}"},
    "history": {"ttl": 300, "key": "history:{symbol}:{resolution}"},
    "portfolio": {"ttl": 60, "key": "portfolio:{account_id}"}
}
```

#### Connection Pooling
```python
# Persistent connections for external APIs
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(
        limit=100,           # Max connections
        limit_per_host=20,   # Per-host limit
        keepalive_timeout=300 # Keep-alive duration
    )
)
```

### Monitoring & Metrics
```python
# Performance tracking
METRICS = {
    "execution_times": [],
    "risk_check_times": [],
    "api_latencies": {},
    "websocket_reconnections": 0,
    "failed_requests": 0
}

# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "metrics": get_performance_metrics(),
        "uptime": get_uptime(),
        "version": "1.0.0"
    }
```

### Scalability Considerations
- **Horizontal Scaling**: Redis pub/sub for multi-instance coordination
- **Load Balancing**: Multiple DataHub instances behind load balancer
- **Database Sharding**: Portfolio data partitioned by account
- **Geographic Distribution**: Regional deployments for latency optimization

## 📋 Implementation Status

### ✅ Completed Components
- **Backend Data Models**: Complete Pydantic models with validation
- **DataHub Server**: FastAPI with TradingView UDF protocol
- **Tradier Integration**: Full API wrapper with WebSocket streaming  
- **Execution Engine**: Advanced trading with risk management
- **Strategy Automation**: Kairos configurations with systemd integration
- **Documentation**: Comprehensive architecture and setup guides

### 🚧 In Progress  
- **Frontend Development**: Electron app with TradingView widget (pending)
- **IPC Implementation**: Symbol selection and chart integration (pending)
- **Testing Suite**: Unit and E2E tests with Playwright (pending)

### 📋 Planned Features
- **Chronos Integration**: Flask listener for webhook execution  
- **News Integration**: NewsAPI and FRED data feeds
- **Backtesting**: QuantConnect LEAN integration
- **Portfolio Analytics**: PyPortfolioOpt and QuantStats integration
- **Multi-Broker**: Tradovate and CCXT support

## 🔧 Development Workflow

### Local Development
```bash
# 1. Start Redis cache
redis-server --port 6379

# 2. Start DataHub server  
cd src/backend && python -m uvicorn datahub.server:app --reload

# 3. Start Kairos in development mode
./src/automation/kairos_jobs/setup_kairos.sh dev

# 4. Run tests
pytest tests/ -v

# 5. Code quality checks
ruff check . --fix
mypy src/
```

### Production Deployment
```bash
# 1. System setup
sudo ./src/automation/kairos_jobs/setup_kairos.sh system

# 2. Configure environment
sudo nano /etc/trader-ops/kairos.env

# 3. User setup  
./src/automation/kairos_jobs/setup_kairos.sh user

# 4. Start services
./src/automation/kairos_jobs/setup_kairos.sh start
```

This architecture provides a robust foundation for automated trading with comprehensive risk management, real-time data processing, and scalable deployment options. The modular design enables independent development and testing of components while maintaining system cohesion through well-defined interfaces.
