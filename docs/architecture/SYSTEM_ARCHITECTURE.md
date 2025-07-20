# System Architecture

Comprehensive architectural overview of the Trader Ops trading dashboard, including system design, component interactions, and data flow patterns.

## 📋 Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)

## 🔍 Overview

Trader Ops is a cross-platform desktop trading dashboard that combines real-time market data, advanced charting, and trading execution in a unified interface. The system follows a microservices-inspired architecture with clear separation between data services, presentation layers, and external integrations.

### Key Design Principles
- **Modularity**: Clear separation of concerns between components
- **Extensibility**: Plugin architecture for data feeds and trading platforms
- **Performance**: Optimized for real-time data processing and UI responsiveness
- **Security**: Secure handling of authentication and sensitive trading data
- **Reliability**: Robust error handling and graceful degradation

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Trader Ops Desktop App                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Electron      │    │   FastAPI       │                │
│  │   Frontend      │◄──►│   Backend       │                │
│  │                 │    │                 │                │
│  │ ├─ Main Process │    │ ├─ API Server   │                │
│  │ ├─ Renderer     │    │ ├─ WebSocket    │                │
│  │ ├─ Vue.js UI    │    │ ├─ UDF Protocol │                │
│  │ └─ TradingView  │    │ └─ Data Feeds   │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼───────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │   Tradier     │ │ TradingView │ │   Future    │
        │     API       │ │  Services   │ │ Integrations│
        │               │ │             │ │             │
        │ ├─ Market Data│ │ ├─ Auth API │ │ ├─ Tradovate│
        │ ├─ Trading    │ │ ├─ Widget   │ │ ├─ CCXT     │
        │ └─ WebSocket  │ │ └─ Sessions │ │ └─ LEAN     │
        └───────────────┘ └─────────────┘ └─────────────┘
```

### System Boundaries
- **Desktop Application**: Self-contained Electron app with embedded backend
- **External APIs**: Third-party services for data and authentication
- **User Environment**: Local machine with network connectivity

## 🧩 Component Architecture

### Frontend Layer (Electron + Vue.js)

#### Main Process
```typescript
// src/frontend/main.ts
class MainProcess {
  - windowManager: BrowserWindowManager
  - ipcHandler: IPCHandler
  - menuBuilder: MenuBuilder
  - updater: AutoUpdater
  
  + createWindow(): BrowserWindow
  + handleIPC(channel: string, handler: Function): void
  + setupMenus(): void
}
```

**Responsibilities**:
- Application lifecycle management
- Window creation and management
- IPC communication coordination
- Menu and system integration
- Auto-updates and app distribution

#### Renderer Process
```typescript
// src/frontend/renderer/
class RendererProcess {
  - vueApp: VueApplication
  - chartManager: TradingViewManager
  - dataService: DataService
  - stateManager: VuexStore
  
  + initializeApp(): void
  + connectToBackend(): void
  + handleRealTimeData(): void
}
```

**Components**:
- **App.vue**: Root application component
- **ChartContainer.vue**: TradingView widget wrapper
- **SymbolSearch.vue**: Symbol search and selection
- **DataPanel.vue**: Real-time quotes and market data
- **SettingsPanel.vue**: Configuration and preferences

#### TradingView Integration
```typescript
class TradingViewManager {
  - widget: TradingViewWidget
  - datafeed: UDFDatafeed
  - authManager: AuthenticationManager
  - mode: 'local' | 'authenticated'
  
  + createWidget(container: HTMLElement): void
  + switchMode(mode: string): Promise<void>
  + updateSymbol(symbol: string): void
  + setupDatafeed(): UDFCompatibleDatafeed
}
```

### Backend Layer (FastAPI)

#### API Server
```python
# src/backend/server.py
class DataHubServer:
    - app: FastAPI
    - connection_manager: WebSocketManager
    - data_connectors: Dict[str, DataConnector]
    - udf_handler: UDFProtocolHandler
    
    + start_server(): None
    + register_routes(): None
    + setup_middleware(): None
    + handle_websocket(): None
```

**Core Endpoints**:
- `/health` - Health monitoring
- `/symbols` - Available trading symbols
- `/quotes/{symbol}` - Real-time quotes
- `/history` - Historical OHLCV data (UDF)
- `/stream` - WebSocket real-time data
- `/alerts` - Alert management
- `/portfolio/{account}` - Portfolio data

#### Data Models
```python
# src/backend/models.py
@dataclass
class Quote:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: int
    change: float
    change_percent: float

@dataclass  
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int
```

#### WebSocket Manager
```python
class ConnectionManager:
    - active_connections: List[WebSocket]
    - symbol_subscribers: Dict[str, List[WebSocket]]
    - data_streams: Dict[str, DataStream]
    
    + connect(websocket: WebSocket): None
    + subscribe_symbol(ws: WebSocket, symbol: str): None
    + broadcast_quote(symbol: str, quote: Quote): None
    + handle_disconnect(websocket: WebSocket): None
```

### Data Connector Layer

#### Abstract Data Connector
```python
# src/backend/feeds/base.py
class DataConnector(ABC):
    @abstractmethod
    async def get_quotes(symbols: List[str]) -> List[Quote]:
        pass
        
    @abstractmethod  
    async def get_history(symbol: str, interval: str, 
                         start: datetime, end: datetime) -> List[Candle]:
        pass
        
    @abstractmethod
    async def websocket_stream(symbols: List[str]) -> AsyncIterator[Quote]:
        pass
```

#### Tradier Implementation
```python
# src/backend/feeds/tradier.py
class TradierConnector(DataConnector):
    - api_key: str
    - base_url: str
    - session: aiohttp.ClientSession
    - websocket_url: str
    
    + authenticate(): bool
    + get_quotes(symbols: List[str]) -> List[Quote]
    + get_history(symbol: str, **kwargs) -> List[Candle]
    + websocket_stream(symbols: List[str]) -> AsyncIterator[Quote]
    + place_order(order: OrderRequest) -> OrderResponse
```

## 🔄 Data Flow

### Real-time Data Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Market    │    │   Tradier   │    │   Backend   │    │  Frontend   │
│   Data      │───►│   WebSocket │───►│  WebSocket  │───►│    UI       │
│   Sources   │    │   Feed      │    │   Manager   │    │  Components │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

1. Market data updates
2. Tradier WebSocket receives updates  
3. Backend processes and validates data
4. WebSocket manager broadcasts to subscribers
5. Frontend receives and updates UI components
```

### Historical Data Flow (UDF Protocol)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ TradingView │    │   Backend   │    │   Tradier   │    │   Market    │
│   Widget    │───►│ UDF Handler │───►│   REST API  │───►│    Data     │
│             │◄───│             │◄───│             │◄───│   Sources   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

1. TradingView requests historical data
2. Backend UDF handler processes request
3. Tradier API fetches historical candles
4. Backend formats response per UDF specification
5. TradingView widget renders chart data
```

### Authentication Flow (TradingView Mode)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │    │ Auth Window │    │ TradingView │    │  Main App   │
│ Mode Toggle │───►│  (Electron) │───►│   Login     │───►│ Authenticated│
│             │    │             │    │   Server    │    │    Mode     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

1. User clicks mode toggle
2. Electron opens authentication window
3. User logs into TradingView
4. Session cookies captured via IPC
5. Main app switches to authenticated mode
```

### Inter-Process Communication (IPC)
```
┌─────────────────────────────────────┐
│            Main Process             │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ IPC Handler │  │Window Manager│   │
│  └─────────────┘  └─────────────┘   │
└─────────┬───────────────────────────┘
          │ IPC Messages
          ▼
┌─────────────────────────────────────┐
│         Renderer Process            │
│  ┌─────────────┐  ┌─────────────┐   │
│  │  Vue App    │  │ TradingView │   │
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘

IPC Channels:
- symbol-selected: Symbol change notifications
- tradingview-auth: Authentication flow
- data-stream: Real-time market data
- settings-update: Configuration changes
```

## 💻 Technology Stack

### Core Technologies
| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Desktop | Electron | 26+ | Cross-platform desktop framework |
| Frontend | Vue.js | 3.x | Reactive UI framework |
| Backend | FastAPI | 0.104+ | High-performance API framework |
| Language | TypeScript | 5.x | Type-safe frontend development |
| Language | Python | 3.11+ | Backend development |
| Charts | TradingView | Latest | Professional trading charts |

### Supporting Technologies
| Component | Technology | Purpose |
|-----------|-----------|---------|
| HTTP Client | aiohttp | Async HTTP requests |
| WebSocket | websockets | Real-time communication |
| Data Validation | Pydantic | Type-safe data models |
| Process Management | Poetry | Python dependency management |
| Build System | Vite | Fast frontend build tool |
| Package Manager | npm | Node.js dependency management |
| Testing | Pytest + Vitest | Comprehensive test coverage |

### Development Tools
| Tool | Purpose |
|------|---------|
| Ruff | Python linting and formatting |
| Black | Python code formatting |
| ESLint | JavaScript/TypeScript linting |
| Prettier | Code formatting |
| mypy | Python static type checking |
| TypeScript | Frontend type checking |

## 🚀 Deployment Architecture

### Development Environment
```
┌─────────────────────────────────────┐
│        Developer Machine            │
│                                     │
│  ┌─────────────┐  ┌─────────────┐   │
│  │   Backend   │  │  Frontend   │   │
│  │ (Port 8000) │  │ (Electron)  │   │
│  └─────────────┘  └─────────────┘   │
│                                     │
│  ┌─────────────────────────────┐     │
│  │      External APIs          │     │
│  │  - Tradier (Sandbox)       │     │
│  │  - TradingView Auth         │     │
│  └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

### Production Distribution
```
┌─────────────────────────────────────┐
│         User Machine               │
│                                     │
│  ┌─────────────────────────────┐     │
│  │     Packaged Electron App   │     │
│  │                             │     │
│  │  ┌─────────┐ ┌─────────┐    │     │
│  │  │Frontend │ │ Backend │    │     │
│  │  │  (UI)   │ │ (API)   │    │     │
│  │  └─────────┘ └─────────┘    │     │
│  └─────────────────────────────┘     │
│                  │                   │
│         ┌────────┼────────┐          │
│         ▼        ▼        ▼          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │Tradier  │ │Trading  │ │ Future  │ │
│  │   API   │ │View API │ │  APIs   │ │
│  └─────────┘ └─────────┘ └─────────┘ │
└─────────────────────────────────────┘
```

### Build Pipeline
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Source    │    │    Build    │    │ Distribution│
│    Code     │───►│   Process   │───►│  Artifacts  │
│             │    │             │    │             │
│ ├─ Python   │    │ ├─ Poetry   │    │ ├─ .dmg     │
│ ├─ TypeScript│    │ ├─ Vite     │    │ ├─ .exe     │
│ ├─ Vue      │    │ ├─ Electron │    │ ├─ .AppImage│
│ └─ Assets   │    │ └─ Package  │    │ └─ .tar.gz  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔒 Security Architecture

### Authentication & Authorization
```
┌─────────────────────────────────────┐
│           Security Layers           │
│                                     │
│  ┌─────────────────────────────┐     │
│  │      TradingView Auth       │     │
│  │  - OAuth 2.0 Flow          │     │
│  │  - Session Cookie Capture   │     │
│  │  - Secure IPC Transfer      │     │
│  └─────────────────────────────┘     │
│                                     │
│  ┌─────────────────────────────┐     │
│  │       API Security          │     │
│  │  - API Key Management       │     │
│  │  - Request Rate Limiting    │     │
│  │  - Input Validation         │     │
│  └─────────────────────────────┘     │
│                                     │
│  ┌─────────────────────────────┐     │
│  │      Local Security         │     │
│  │  - Secure Credential Store  │     │
│  │  - Memory Protection        │     │
│  │  - Process Isolation        │     │
│  └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

### Data Protection
- **In Transit**: HTTPS/WSS for all external communications
- **At Rest**: Encrypted credential storage using OS keychain
- **In Memory**: Secure memory allocation for sensitive data
- **Logs**: Sanitized logging with no credential exposure

### Security Boundaries
```
┌───────────────────────────────┐
│         Trust Boundary        │
│                               │
│  ┌─────────────────────────┐   │ ┌─────────────────────────┐
│  │     Local Process       │   │ │    External Services    │
│  │                         │◄──┼─┤                         │
│  │ ├─ Electron Main        │   │ │ ├─ Tradier API          │
│  │ ├─ Electron Renderer    │   │ │ ├─ TradingView          │
│  │ ├─ FastAPI Backend      │   │ │ └─ Future Services      │
│  │ └─ Local Data Store     │   │ │                         │
│  └─────────────────────────┘   │ └─────────────────────────┘
└───────────────────────────────┘
```

## ⚡ Performance Considerations

### Real-time Data Optimization
- **WebSocket Connection Pooling**: Efficient connection management
- **Data Compression**: Minimize bandwidth usage
- **Message Batching**: Aggregate multiple updates
- **Smart Throttling**: Rate limiting for UI updates

### Memory Management
```python
# Example: Efficient quote caching
class QuoteCache:
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Quote] = {}
        self._access_times: Dict[str, float] = {}
        self._max_size = max_size
    
    def get(self, symbol: str) -> Optional[Quote]:
        if symbol in self._cache:
            self._access_times[symbol] = time.time()
            return self._cache[symbol]
        return None
    
    def put(self, quote: Quote) -> None:
        if len(self._cache) >= self._max_size:
            self._evict_lru()
        self._cache[quote.symbol] = quote
        self._access_times[quote.symbol] = time.time()
```

### UI Performance
- **Virtual Scrolling**: Handle large datasets efficiently
- **Component Lazy Loading**: Load components on demand
- **State Management**: Optimized Vuex store with normalized data
- **Chart Optimization**: TradingView widget performance tuning

### Backend Performance
- **Async Processing**: Non-blocking I/O operations
- **Connection Pooling**: Reuse HTTP connections
- **Caching Strategy**: Multi-layer caching (memory, disk)
- **Database Optimization**: Efficient queries and indexing (future)

### Monitoring & Metrics
```python
# Example: Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'websocket_connections': 0,
            'api_requests_per_second': 0,
            'memory_usage_mb': 0,
            'response_time_ms': 0
        }
    
    def track_websocket_connection(self):
        self.metrics['websocket_connections'] += 1
    
    def track_api_request(self, response_time: float):
        self.metrics['response_time_ms'] = response_time
```

### Scalability Patterns
- **Horizontal Scaling**: Multiple data connector instances
- **Load Balancing**: Distribute WebSocket connections
- **Caching Strategy**: Redis for shared state (future)
- **Message Queues**: Async processing (future enhancement)

---

This architecture provides a solid foundation for a professional trading application while maintaining flexibility for future enhancements and integrations.