# PRP: Unified TraderTerminal Dashboard with Backtesting & Containerization

## Metadata
- **Feature Name**: TraderTerminal Desktop Dashboard with Integrated Backtesting
- **Date**: January 2025
- **Confidence Score**: 9/10
- **Estimated Implementation Time**: 6-8 weeks (Dashboard: 3-4 weeks, Backtesting: 1-2 weeks, Containerization: 2-3 weeks)
- **Primary Technologies**: Electron/Tauri, FastAPI, TradingView Widgets, Podman, TimescaleDB
- **Target Platforms**: macOS (Apple Silicon), Fedora 40+ Trading Terminal Spin

## Executive Summary

This PRP unifies three major components of the TraderTerminal ecosystem:
1. **Desktop Trading Dashboard** - A Bloomberg-like multi-pane application for macOS/Fedora
2. **TradingView Backtesting Service** - Automated Pine Script strategy testing via grimm-kairos
3. **Containerized Architecture** - Podman-based deployment for the Fedora Trading Terminal spin

The solution creates a professional-grade trading platform that runs natively on macOS and deploys seamlessly to Fedora via containerization, with integrated backtesting capabilities and real-time market data feeds.

## Current State (as of January 2025)

Based on development logs, significant progress has been made:

### ✅ Completed Components

#### Backend Infrastructure (July 19, 2025)
- **DataHub Server** (`src/backend/datahub/server.py`)
  - FastAPI with TradingView UDF protocol
  - WebSocket real-time streaming
  - Mock data generation for development
  - Webhook endpoints for Kairos/TradingView alerts
  
- **Data Models** (`src/backend/models/`)
  - Comprehensive Pydantic models (market_data, alerts, execution, portfolio)
  - TradingView UDF compatibility
  - Full type safety and validation

- **Tradier Integration** (`src/backend/feeds/tradier.py`)
  - Complete API wrapper with WebSocket support
  - Rate limiting and error handling
  - Data normalization for TradingView

- **Execution Engine** (`src/backend/trading/execution_engine.py`)
  - Multi-layer risk management
  - Webhook-driven alert processing
  - Position sizing optimization
  - Redis integration for state management

- **Kairos Automation** (`src/automation/kairos_jobs/`)
  - Momentum strategy (RSI + volume breakout)
  - Mean reversion strategy (Bollinger Bands)
  - Portfolio rebalancing
  - SystemD service configurations

#### DevOps Infrastructure (July 19, 2025)
- **GitHub Actions Workflows**
  - Comprehensive CI/CD pipeline
  - Multi-platform testing
  - Security scanning
  - Performance monitoring
  - Market-aware deployment
  - Release automation

- **Development Tooling** (January 20, 2025)
  - Three-layer git hook system for development logging
  - Automated documentation generation
  - Professional issue templates

### 🚧 In Progress / Remaining Work

#### Desktop Application (Not Started)
- Electron/Tauri framework setup
- TradingView widget integration
- IPC bridge implementation
- UI components (watchlist, order entry, alerts panel)
- Desktop packaging for macOS and Linux

#### Backtesting Service Enhancement (Partially Complete)
- Kairos integration exists but needs:
  - Web API for backtest submission
  - Progress tracking via WebSocket
  - Results visualization component
  - Historical backtest browser

#### Containerization (Not Started)
- Podman pod configuration
- Container definitions for all services
- Volume strategy implementation
- SystemD and launchd integration
- Development compose files

#### Additional Data Feeds (Not Started)
- Tradovate futures integration
- CCXT crypto exchange connectors
- News API integration
- FRED macro data feeds

## LLM Orchestration Directives

You are **Claude**, acting as an orchestrator.

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

## Context & Architecture Overview

### Current Ecosystem
```
trader-ops/ (This Project)
├── src/backend/           ✅ Complete
│   ├── datahub/          ✅ FastAPI server with UDF
│   ├── models/           ✅ Pydantic models
│   ├── feeds/            ✅ Tradier integration
│   └── trading/          ✅ Execution engine
├── src/automation/        ✅ Complete
│   └── kairos_jobs/      ✅ Strategy configs
├── src/frontend/          🚧 Not Started
│   ├── electron/         ❌ Desktop app
│   └── components/       ❌ UI components
└── deployment/            🚧 Not Started
    └── containers/       ❌ Podman configs

grimm-kairos/ (Fork of timelyart/Kairos)
├── TradingView automation via Selenium
├── Strategy backtesting capabilities
└── Alert generation

grimm-chronos/ (Fork of timelyart/chronos)
├── Webhook receiver
├── Trade execution engine
└── Broker API integrations

trading-setups/ (Strategy Repository)
├── Pine Script strategies
├── Configuration templates
└── Backtest results
```

### Unified Architecture
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
    │              Backend Services (Currently Local)        │
    │                                                       │
    │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
    │  │  Data Hub   │  │   Backtest   │  │  Chronos   │  │
    │  │  (FastAPI)  │  │   Service    │  │ (Executor) │  │
    │  │     ✅      │  │      🟡      │  │     ❌     │  │
    │  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
    │         │                │                 │          │
    │  ┌──────┴──────┐  ┌──────┴───────┐  ┌─────┴──────┐  │
    │  │   Redis     │  │    Kairos    │  │   Armory   │  │
    │  │  (State)    │  │  (Headless)  │  │   (Risk)   │  │
    │  │     ❌      │  │      ✅      │  │     ❌     │  │
    │  └─────────────┘  └──────────────┘  └────────────┘  │
    └───────────────────────────────────────────────────────┘
```

## Requirements

### Desktop Dashboard Requirements

#### Core Features
1. **Multi-Pane Layout**
   - TradingView Advanced Charts widget
   - Watchlist with real-time quotes
   - Order entry panel
   - Alert management (Kairos YAML)
   - News & macro data ribbon
   - Portfolio analytics

2. **Data Integration**
   - Real-time feeds: Tradier (equities/options), Tradovate (futures), CCXT (crypto)
   - Sub-100ms latency for price updates
   - UDF protocol for TradingView widget
   - WebSocket streaming with auto-reconnect

3. **Platform Support**
   - Native performance on macOS (Apple Silicon)
   - Electron or Tauri framework
   - Config-driven with .env for secrets
   - Auto-update mechanism

### Backtesting Service Requirements

#### Functional Requirements
1. **API Interface**
   - `POST /api/backtest/strategy` - Submit Pine Script for testing
   - `GET /api/backtest/{id}/status` - Check progress
   - `GET /api/backtest/{id}/results` - Retrieve results
   - WebSocket progress updates

2. **Execution Engine**
   - Headless Kairos automation
   - Parallel execution (up to 5 concurrent)
   - Multi-symbol, multi-timeframe support
   - Results extraction and parsing

3. **Results Management**
   - PostgreSQL storage with TimescaleDB
   - Performance metrics calculation
   - Trade-by-trade analysis
   - Equity curve generation

### Containerization Requirements

#### Infrastructure
1. **Podman Pod Architecture**
   - Single pod with shared network namespace
   - Rootless containers for security
   - Resource limits per service
   - Volume strategy for persistence

2. **Service Containers**
   - `datahub`: FastAPI data aggregation (port 8080)
   - `chronos-db`: TimescaleDB storage (port 5432)
   - `kairos`: Backtest automation (port 8081)
   - `chronos-exec`: Trade execution (port 8083)
   - `armory`: Risk analytics (port 8082)
   - `ops`: Prometheus monitoring (port 9090)

3. **Deployment Targets**
   - Fedora 40+ with SystemD integration
   - macOS with launchd agents
   - Development mode with hot-reload

## Revised Implementation Plan

Given the current state, here's the updated implementation timeline:

### Phase 1: Desktop Application Foundation (Week 1-2) 🔴 Priority

Since the backend is largely complete, we can focus on the desktop application:

#### Step 1.1: Project Setup
```bash
# Initialize Electron app structure
mkdir -p src/frontend/{electron,renderer,components,lib}
cd src/frontend

# Initialize package.json
npm init -y
npm install electron electron-builder @electron/remote
npm install -D @types/node typescript webpack vite @vitejs/plugin-vue
npm install vue@3 pinia vue-router

# TypeScript configuration
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022", "DOM"],
    "jsx": "preserve",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
EOF
```

#### Step 1.2: Electron Main Process
```typescript
// src/frontend/electron/main.ts
import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1920,
        height: 1080,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        titleBarStyle: 'hiddenInset',
        frame: process.platform !== 'darwin'
    });

    // Load the frontend
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:5173'); // Vite dev server
    } else {
        mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
    }
}

// IPC handlers to connect to existing backend
ipcMain.handle('api:request', async (event, endpoint, options) => {
    const response = await fetch(`http://localhost:8080${endpoint}`, options);
    return response.json();
});

ipcMain.handle('websocket:connect', async (event, url) => {
    // WebSocket proxy implementation
});

app.whenReady().then(createWindow);
```

#### Step 1.3: Frontend Components with TradingView
```vue
<!-- src/frontend/renderer/components/TradingDashboard.vue -->
<template>
  <div class="trading-dashboard">
    <!-- Header Bar -->
    <div class="header-bar">
      <SymbolSearch @symbol-selected="onSymbolSelected" />
      <AccountInfo :account="account" />
    </div>
    
    <!-- Main Layout -->
    <div class="main-layout">
      <!-- Left Panel -->
      <div class="left-panel">
        <Watchlist 
          :symbols="watchlistSymbols" 
          @symbol-clicked="onSymbolSelected"
        />
        <OrderEntry 
          :symbol="activeSymbol" 
          :account="account"
          @order-submitted="onOrderSubmitted"
        />
      </div>
      
      <!-- Center Panel -->
      <div class="center-panel">
        <TradingViewChart 
          :symbol="activeSymbol"
          :datafeed-url="datafeedUrl"
          @alert-created="onAlertCreated"
        />
      </div>
      
      <!-- Right Panel -->
      <div class="right-panel">
        <ActiveAlerts :alerts="activeAlerts" />
        <Positions :positions="positions" />
        <OrderHistory :orders="recentOrders" />
      </div>
    </div>
    
    <!-- Bottom Panel -->
    <div class="bottom-panel">
      <NewsFeed :symbol="activeSymbol" />
      <BacktestPanel v-if="showBacktest" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useWebSocket } from '@/composables/useWebSocket';
import { useTradingAPI } from '@/composables/useTradingAPI';
import TradingViewChart from '@/components/TradingViewChart.vue';
// ... other imports

const { subscribe, unsubscribe } = useWebSocket('ws://localhost:8080/stream');
const { getAccount, getPositions, submitOrder } = useTradingAPI();

const activeSymbol = ref('MNQ1!');
const datafeedUrl = 'http://localhost:8080/udf';

onMounted(async () => {
  // Load initial data
  account.value = await getAccount();
  positions.value = await getPositions();
  
  // Subscribe to real-time updates
  subscribe('account', (data) => {
    account.value = data;
  });
  
  subscribe('positions', (data) => {
    positions.value = data;
  });
});
</script>
```

#### Step 1.4: TradingView Integration Component
```typescript
// src/frontend/renderer/components/TradingViewChart.vue
<template>
  <div ref="chartContainer" class="tradingview-chart"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { widget } from '@/lib/charting_library';

const props = defineProps<{
  symbol: string;
  datafeedUrl: string;
}>();

const chartContainer = ref<HTMLDivElement>();
let tvWidget: any = null;

onMounted(() => {
  const widgetOptions = {
    symbol: props.symbol,
    datafeed: new UDFDatafeed(props.datafeedUrl),
    interval: '5',
    container: chartContainer.value,
    library_path: '/charting_library/',
    locale: 'en',
    disabled_features: ['use_localstorage_for_settings'],
    enabled_features: ['study_templates'],
    charts_storage_url: 'http://localhost:8080/api/v1/charts',
    charts_storage_api_version: '1.1',
    client_id: 'traderterminal',
    user_id: 'public_user',
    fullscreen: false,
    autosize: true,
    studies_overrides: {},
    theme: 'dark',
    overrides: {
      'mainSeriesProperties.style': 1, // Candles
    },
  };

  tvWidget = new widget(widgetOptions);
  
  tvWidget.onChartReady(() => {
    // Add custom indicators
    tvWidget.chart().createStudy('Moving Average', false, false, [20]);
    tvWidget.chart().createStudy('RSI', false, false, [14]);
  });
});

// Update symbol when prop changes
watch(() => props.symbol, (newSymbol) => {
  if (tvWidget) {
    tvWidget.chart().setSymbol(newSymbol);
  }
});
</script>
```

### Phase 2: Backtesting Service Enhancement (Week 3) 🟡 In Progress

The backend Kairos integration exists, we need to add the web API layer:

#### Step 2.1: Enhance Existing Backend with Backtest API
```python
# Add to src/backend/datahub/server.py
from src.backend.services.backtest_service import BacktestService

# Initialize backtest service
backtest_service = BacktestService(
    kairos_path=Path(os.getenv("KAIROS_PATH", "/opt/grimm-kairos")),
    db_connection=None  # TODO: Add TimescaleDB connection
)

# Add backtest endpoints
@app.post("/api/backtest/strategy")
async def submit_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """Submit a new strategy backtest"""
    backtest_id = await backtest_service.submit_backtest(
        pine_script=request.pine_script,
        symbols=request.symbols,
        timeframes=request.timeframes,
        date_range={
            "start": request.start_date,
            "end": request.end_date
        },
        background_tasks=background_tasks
    )
    
    return {
        "backtest_id": backtest_id,
        "status": "queued",
        "message": "Backtest submitted successfully"
    }
```

### Phase 3: Containerization (Week 4-5)

#### Step 3.1: Container Definitions
```dockerfile
# deployment/containers/Containerfile.datahub
FROM registry.fedoraproject.org/fedora-minimal:40
RUN microdnf install -y python3 python3-pip && microdnf clean all
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip3 install poetry && poetry install --no-dev
COPY src/backend/ ./src/backend/
EXPOSE 8080
CMD ["poetry", "run", "uvicorn", "src.backend.datahub.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Step 3.2: Pod Configuration
```yaml
# deployment/podman/traderterminal-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: traderterminal-pod
spec:
  containers:
  - name: datahub
    image: ghcr.io/yourorg/traderterminal-datahub:latest
    ports:
    - containerPort: 8080
    resources:
      limits:
        memory: "2Gi"
        cpu: "2"
    volumeMounts:
    - name: config
      mountPath: /etc/traderterminal
      readOnly: true
      
  - name: redis
    image: docker.io/redis:7-alpine
    ports:
    - containerPort: 6379
    command: ["redis-server", "--appendonly", "yes"]
    volumeMounts:
    - name: redis-data
      mountPath: /data
      
  - name: kairos
    image: ghcr.io/yourorg/grimm-kairos:latest
    ports:
    - containerPort: 8081
    volumeMounts:
    - name: config
      mountPath: /etc/traderterminal
      readOnly: true
      
  volumes:
  - name: config
    configMap:
      name: traderterminal-config
  - name: redis-data
    persistentVolumeClaim:
      claimName: traderterminal-redis
```

#### Step 3.3: SystemD Integration
```bash
#!/bin/bash
# deployment/scripts/install-fedora.sh

# Create pod
podman pod create \
  --name traderterminal-pod \
  --publish 8080:8080 \
  --publish 9090:9090

# Start containers
podman run -d --name datahub --pod traderterminal-pod \
  -v tt_config:/etc/traderterminal:ro,z \
  ghcr.io/yourorg/traderterminal-datahub:latest

podman run -d --name redis --pod traderterminal-pod \
  -v tt_redis:/data:z \
  docker.io/redis:7-alpine

# Generate systemd units
podman generate systemd \
  --name traderterminal-pod \
  --files \
  --new

# Install and enable
mkdir -p ~/.config/systemd/user
cp *.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now traderterminal-pod.service
```

### Phase 4: Integration & Polish (Week 6)

#### Step 4.1: Unified Configuration
```yaml
# config/traderterminal.yaml
dashboard:
  theme: dark
  default_layout: "trading"
  auto_save_interval: 60

datahub:
  providers:
    tradier:
      enabled: true
      api_key: ${TRADIER_API_KEY}
      sandbox: false
    tradovate:
      enabled: true
      username: ${TRADOVATE_USER}
      password: ${TRADOVATE_PASS}
    crypto:
      exchanges: ["binance", "coinbase"]
      
backtesting:
  max_concurrent: 5
  timeout_seconds: 300
  kairos_path: /opt/grimm-kairos
  
execution:
  chronos_url: http://localhost:8083
  default_broker: "tradier"
  risk_checks: true
```

#### Step 4.2: Desktop Packaging
```json
// package.json
{
  "name": "traderterminal",
  "version": "1.0.0",
  "main": "app/main.js",
  "scripts": {
    "start": "electron .",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux"
  },
  "build": {
    "appId": "com.traderterminal.desktop",
    "productName": "TraderTerminal",
    "mac": {
      "category": "public.app-category.finance",
      "target": ["dmg", "zip"],
      "arch": ["arm64", "x64"]
    },
    "linux": {
      "target": ["AppImage", "rpm"],
      "category": "Finance"
    }
  }
}
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_datahub.py
import pytest
from src.backend.datahub.server import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_udf_config():
    response = client.get("/udf/config")
    assert response.status_code == 200
    assert "supported_resolutions" in response.json()

@pytest.mark.asyncio
async def test_backtest_submission():
    response = client.post("/api/backtest/strategy", json={
        "pine_script": "test_script",
        "symbols": ["AAPL"],
        "timeframes": ["1h"]
    })
    assert response.status_code == 200
    assert "backtest_id" in response.json()
```

### End-to-End Tests
```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('complete trading flow', async ({ page }) => {
  // Launch app
  await page.goto('http://localhost:3000');
  
  // Select symbol
  await page.click('[data-testid="symbol-search"]');
  await page.fill('[data-testid="symbol-input"]', 'AAPL');
  await page.click('[data-testid="symbol-AAPL"]');
  
  // Verify chart loads
  await expect(page.locator('.tv-chart-container')).toBeVisible();
  
  // Submit backtest
  await page.click('[data-testid="backtest-tab"]');
  await page.click('[data-testid="run-backtest"]');
  
  // Wait for results
  await expect(page.locator('[data-testid="backtest-results"]')).toBeVisible({
    timeout: 30000
  });
});
```

## Immediate Next Steps

Based on the current state, here are the prioritized next steps:

### 1. Desktop Application Setup (Priority 1)
```bash
# Create frontend structure
mkdir -p src/frontend/{electron,renderer,components,lib,composables}

# Initialize Electron project
cd src/frontend
npm init -y
npm install electron electron-builder vue@3 pinia

# Copy TradingView charting library
# NOTE: You must obtain the library from TradingView
cp -r /path/to/charting_library src/frontend/renderer/public/
```

### 2. Connect Frontend to Existing Backend
- The backend is already running on port 8080
- UDF endpoints are ready at `/udf/*`
- WebSocket streaming available at `ws://localhost:8080/stream`
- Just need to create the frontend UI

### 3. Enhance Backtesting API
- Add the missing API endpoints to existing backend
- Connect to Kairos for execution
- Add progress tracking

### 4. Begin Containerization
- Start with DataHub container
- Add Redis for state management
- Create development compose file

## Success Criteria

### Functional Success
- [x] Backend data hub with real-time feeds
- [x] Kairos strategy automation
- [x] Risk management system
- [ ] Desktop app launches in <3 seconds on M3 Mac
- [ ] TradingView charts display real-time data
- [ ] Backtests complete within 5 minutes per symbol
- [ ] All containers start successfully via SystemD
- [ ] Seamless integration between all components

### Performance Benchmarks
- [x] Data Hub handles WebSocket connections
- [x] Execution engine processes webhooks
- [ ] Desktop app uses <500MB RAM idle
- [ ] Container overhead <2% vs native
- [ ] UI responds to user input <50ms

### Quality Metrics
- [x] Type safety with Pydantic models
- [x] Comprehensive GitHub Actions CI/CD
- [ ] 90% test coverage across all services
- [ ] All endpoints documented with OpenAPI
- [ ] User documentation and video tutorials

## Risks & Mitigations

### Technical Risks
1. **TradingView Widget Integration**
   - Risk: License requirements and technical complexity
   - Mitigation: Start with free widget, upgrade if needed
   - Alternative: Use lightweight-charts as fallback

2. **Electron Performance on M3 Mac**
   - Risk: Memory usage and native performance
   - Mitigation: Consider Tauri as alternative
   - Monitoring: Profile memory usage early

3. **WebSocket Connection Management**
   - Risk: Connection drops and reconnection logic
   - Mitigation: Implement robust reconnection
   - Already addressed in backend

### Business Risks
1. **TradingView Licensing**
   - Risk: Cost and usage restrictions
   - Mitigation: Start with free tier
   - Alternative: Build custom charting

2. **Data Provider Limits**
   - Risk: Rate limits on Tradier API
   - Mitigation: Implement caching (Redis)
   - Already handled in backend

## References & Documentation

### Core Documentation
- [TradingView Charting Library](https://www.tradingview.com/HTML5-stock-forex-bitcoin-charting-library/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [Podman Documentation](https://docs.podman.io/)
- [Context Engineering Intro](https://github.com/coleam00/context-engineering-intro)

### API References
- [Tradier API](https://developer.tradier.com/) - Already integrated
- [Tradovate API](https://api.tradovate.com/) - Future integration
- [CCXT Documentation](https://docs.ccxt.com/) - Future integration

### Internal Projects
- grimm-kairos: Already integrated in `src/automation/kairos_jobs/`
- grimm-chronos: Needs integration for execution
- trading-setups: Strategy repository

---

**END OF UNIFIED PRP**

## Validation Checklist

- [x] Current state accurately reflected
- [x] Completed work properly credited
- [x] Remaining work clearly identified
- [x] Implementation phases updated for current state
- [x] Dependencies between components clear
- [x] Testing strategy comprehensive
- [x] Deployment guides updated
- [x] Security and monitoring included
- [x] Success criteria updated
- [x] Risks reassessed based on progress

*Confidence: 9/10 - Comprehensive unified plan with clear understanding of current state. The backend infrastructure is largely complete, making the desktop application the critical next step.*

