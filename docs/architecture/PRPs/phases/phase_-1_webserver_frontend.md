# Phase -1: Webserver-First Frontend Refactor

**Duration**: 3-4 days (Pre-Work)  
**Priority**: Foundational - Must complete before Phase 0

## Objective

Serve the TraderTerminal UI from FastAPI so it can run head-less in Kubernetes while the Electron/Tauri binary remains a thin wrapper.

This refactoring enables:
1. Cloud deployment capabilities
2. Multi-user access via web browsers
3. Separation of concerns between UI and desktop wrapper
4. Easier testing and development

## Deliverables

- `apps/web` SPA that re-uses existing Vue 3 components
- FastAPI `StaticFiles` mount at `/app`
- Dockerfile updated to copy compiled assets into backend image
- Kubernetes manifests in `deploy/k8s/` for backend + front-end service
- Electron main process loads `http://localhost:8000/app` (configurable via `UI_URL` env)
- CI job `build_web` that runs `npm run build --workspace apps/web`

## Exit Criteria

- Navigating to `http://localhost:8000/app` renders the dashboard
- Backend image < 400 MB and passes CI
- Electron app loads the same UI without code changes

## Implementation Steps

### Step -1.1: Create Web Frontend Skeleton (Day 0)

#### Task -1.1.1: Scaffold project
```bash
# At repo root
npm create vue@latest apps/web -- --template vue-ts
```

#### Task -1.1.2: Configure workspace structure
```json
// Update root package.json to include workspace
{
  "workspaces": [
    "apps/*",
    "packages/*",
    "src/frontend"
  ]
}
```

#### Task -1.1.3: Create shared UI package
```bash
# Create packages/ui directory structure
mkdir -p packages/ui/src/components
mkdir -p packages/ui/src/composables
mkdir -p packages/ui/src/styles

# Create packages/ui/package.json
```
```json
{
  "name": "@traderterminal/ui",
  "version": "1.0.0",
  "main": "src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./styles": "./src/styles/index.css"
  }
}
```

#### Task -1.1.4: Move existing components
```bash
# Move components from Electron renderer to shared package
mv src/frontend/renderer/components/* packages/ui/src/components/
mv src/frontend/renderer/composables/* packages/ui/src/composables/
mv src/frontend/renderer/styles/shared.css packages/ui/src/styles/
```

#### Task -1.1.5: Create UI package exports
```typescript
// packages/ui/src/index.ts
export * from './components/TradingDashboard.vue'
export * from './components/Watchlist.vue'
export * from './components/OrderEntry.vue'
export * from './components/FundedAccountPanel.vue'
export * from './components/RiskMeter.vue'
// ... export all components
```

#### Task -1.1.6: Update import paths in Electron renderer
```typescript
// src/frontend/renderer/App.vue
// Before: import TradingDashboard from './components/TradingDashboard.vue'
// After:
import { TradingDashboard } from '@traderterminal/ui'
```

#### Task -1.1.7: Configure Vite for web app
```typescript
// apps/web/vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@traderterminal/ui': path.resolve(__dirname, '../../packages/ui/src')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
```

### Step -1.2: Serve Static Assets from FastAPI (Day 0-1)

#### Task -1.2.1: Create static file server module
```python
# src/backend/web/__init__.py
# Empty file to make it a package

# src/backend/web/static_server.py
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from pathlib import Path

router = APIRouter()

# Determine static directory path
STATIC_DIR = Path(__file__).parent.parent.parent / "static" / "web"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
if STATIC_DIR.exists():
    router.mount("/app", StaticFiles(directory=str(STATIC_DIR), html=True), name="web-ui")
```

#### Task -1.2.2: Add CORS configuration
```python
# src/backend/web/cors.py
from fastapi.middleware.cors import CORSMiddleware
import os

def configure_cors(app):
    """Configure CORS for development and production"""
    origins = [
        "http://localhost:3000",  # Vite dev server
        "http://localhost:5173",  # Vite default port
        "http://localhost:8000",  # FastAPI
        "http://localhost:8080",  # Alternative port
    ]
    
    # Add production origins from environment
    if os.getenv("ALLOWED_ORIGINS"):
        origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

#### Task -1.2.3: Wire static server into main app
```python
# src/backend/datahub/server.py
from src.backend.web import static_server
from src.backend.web.cors import configure_cors
from fastapi.responses import FileResponse

# After app initialization
configure_cors(app)

# Add static file serving
app.include_router(static_server.router, include_in_schema=False)

# Add catch-all route for SPA
@app.get("/app/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for all SPA routes"""
    return FileResponse(STATIC_DIR / "index.html")
```

#### Task -1.2.4: Create multi-stage Dockerfile
```dockerfile
# Dockerfile
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY apps/web/package*.json ./apps/web/
COPY packages/ui/package*.json ./packages/ui/

# Install dependencies
RUN npm ci

# Copy source files
COPY apps/web ./apps/web
COPY packages/ui ./packages/ui

# Build web app
RUN npm run build --workspace=apps/web

# Stage 2: Python backend
FROM python:3.11-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY pyproject.toml ./
COPY src/backend ./src/backend

# Install Python dependencies
RUN pip install -e .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/apps/web/dist ./static/web

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "src.backend.datahub.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Task -1.2.5: Add build optimization
```javascript
// apps/web/vite.config.ts - add build config
export default defineConfig({
  // ... existing config
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'pinia', 'vue-router'],
          'charts': ['chart.js', 'chartjs-adapter-date-fns'],
          'ui': ['@traderterminal/ui']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
})
```

### Step -1.3: Kubernetes Manifests (Day 1)

#### Task -1.3.1: Create namespace and configmap
```yaml
# deploy/k8s/00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: traderterminal

---
# deploy/k8s/01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: traderterminal-config
  namespace: traderterminal
data:
  TRADING_ENV: "production"
  API_BASE_URL: "http://traderterminal-api:8000"
  ENABLE_MOCK_DATA: "false"
```

#### Task -1.3.2: Create deployment manifest
```yaml
# deploy/k8s/02-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traderterminal-api
  namespace: traderterminal
spec:
  replicas: 2
  selector:
    matchLabels:
      app: traderterminal-api
  template:
    metadata:
      labels:
        app: traderterminal-api
    spec:
      containers:
      - name: api
        image: traderterminal:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: traderterminal-config
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: traderterminal-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Task -1.3.3: Create service manifest
```yaml
# deploy/k8s/03-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: traderterminal-api
  namespace: traderterminal
spec:
  selector:
    app: traderterminal-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Task -1.3.4: Create ingress manifest
```yaml
# deploy/k8s/04-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: traderterminal-ingress
  namespace: traderterminal
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/websocket-services: "traderterminal-api"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  ingressClassName: nginx
  rules:
  - host: traderterminal.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: traderterminal-api
            port:
              number: 8000
```

#### Task -1.3.5: Create secrets template
```yaml
# deploy/k8s/05-secrets-template.yaml
apiVersion: v1
kind: Secret
metadata:
  name: traderterminal-secrets
  namespace: traderterminal
type: Opaque
stringData:
  database-url: "postgresql://user:pass@postgres:5432/traderterminal"
  tradovate-api-key: "your-key-here"
  webhook-secret: "your-webhook-secret"
```

#### Task -1.3.6: Create deployment script
```bash
# deploy/k8s/deploy.sh
#!/bin/bash

echo "Deploying TraderTerminal to Kubernetes..."

# Create namespace
kubectl apply -f 00-namespace.yaml

# Apply configs and secrets
kubectl apply -f 01-configmap.yaml
# Note: Create actual secrets from template
# kubectl apply -f 05-secrets.yaml

# Deploy application
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-ingress.yaml

# Wait for deployment
kubectl -n traderterminal rollout status deployment/traderterminal-api

echo "Deployment complete!"
```

### Step -1.4: Electron/Tauri Wrapper Update (Day 1-2)

#### Task -1.4.1: Add environment configuration
```typescript
// src/frontend/main/config.ts
export interface AppConfig {
  uiUrl: string
  apiUrl: string
  wsUrl: string
  headless: boolean
}

export function loadConfig(): AppConfig {
  const isDev = process.env.NODE_ENV === 'development'
  
  return {
    uiUrl: process.env.UI_URL || (isDev ? 'http://localhost:5173' : 'http://localhost:8000/app'),
    apiUrl: process.env.API_URL || 'http://localhost:8000',
    wsUrl: process.env.WS_URL || 'ws://localhost:8000',
    headless: process.argv.includes('--headless')
  }
}
```

#### Task -1.4.2: Update main process
```typescript
// src/frontend/main/index.ts
import { app, BrowserWindow } from 'electron'
import { loadConfig } from './config'
import path from 'path'

const config = loadConfig()

function createWindow() {
  if (config.headless) {
    console.log('Running in headless mode - no window will be created')
    return
  }
  
  const mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  })
  
  mainWindow.loadURL(config.uiUrl)
  
  // Handle navigation for SPA
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(config.uiUrl)) {
      event.preventDefault()
    }
  })
}
```

#### Task -1.4.3: Add health check endpoint
```python
# src/backend/web/health.py
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "traderterminal-api"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check - verify all services are ready"""
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "brokers": await check_broker_connections()
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### Task -1.4.4: Add CLI argument parsing
```typescript
// src/frontend/main/cli.ts
import { program } from 'commander'

export function parseArgs() {
  program
    .option('--headless', 'Run without GUI window')
    .option('--ui-url <url>', 'Override UI URL')
    .option('--api-url <url>', 'Override API URL')
    .option('--config <path>', 'Path to config file')
    .parse()
  
  return program.opts()
}
```

### Step -1.5: Developer Experience Scripts (Day 2)

#### Task -1.5.1: Create development scripts
```json
// package.json - add scripts
{
  "scripts": {
    "dev:web": "npm run dev --workspace=apps/web",
    "dev:backend": "cd src/backend && uvicorn src.backend.datahub.server:app --reload --port 8000",
    "dev:electron": "npm run dev --workspace=src/frontend",
    "dev:full": "concurrently \"npm:dev:backend\" \"npm:dev:web\"",
    "build:web": "npm run build --workspace=apps/web",
    "build:ui": "npm run build --workspace=packages/ui",
    "build:all": "npm run build:ui && npm run build:web",
    "test:unit": "vitest",
    "test:e2e": "playwright test",
    "docker:build": "docker build -t traderterminal:latest .",
    "docker:run": "docker run -p 8000:8000 traderterminal:latest",
    "k8s:deploy": "cd deploy/k8s && ./deploy.sh",
    "k8s:dev": "skaffold dev"
  }
}
```

#### Task -1.5.2: Create development environment file
```bash
# .env.development
# API Configuration
API_URL=http://localhost:8000
WS_URL=ws://localhost:8000

# UI Configuration  
UI_URL=http://localhost:5173
VITE_API_URL=http://localhost:8000

# Feature Flags
ENABLE_MOCK_DATA=true
ENABLE_PAPER_TRADING=true

# Broker Configuration
TRADOVATE_DEMO=true
TASTYTRADE_SANDBOX=true
```

#### Task -1.5.3: Create Docker Compose for development
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    build: 
      context: .
      target: backend
    ports:
      - "8000:8000"
    environment:
      - TRADING_ENV=development
      - DATABASE_URL=postgresql://trader:trader@postgres:5432/traderterminal
    volumes:
      - ./src/backend:/app/src/backend
      - ./static/web:/app/static/web
    command: uvicorn src.backend.datahub.server:app --reload --host 0.0.0.0
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=trader
      - POSTGRES_PASSWORD=trader
      - POSTGRES_DB=traderterminal
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

#### Task -1.5.4: Add hot-reload configuration
```typescript
// apps/web/src/main.ts - add HMR
if (import.meta.hot) {
  import.meta.hot.accept()
}

// Configure WebSocket connection for hot reload
if (import.meta.env.DEV) {
  // Ensure WebSocket connections work in development
  window.__VUE_HMR_RUNTIME__ = {
    createRecord: () => {},
    rerender: () => {},
    reload: () => window.location.reload()
  }
}
```

#### Task -1.5.5: Create development proxy configuration
```javascript
// apps/web/proxy.config.js
module.exports = {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    configure: (proxy) => {
      proxy.on('error', (err) => {
        console.log('proxy error', err)
      })
    }
  },
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true,
    changeOrigin: true
  },
  '/webhook': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

#### Task -1.5.6: Add TypeScript path mappings
```json
// tsconfig.json - add path mappings
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@traderterminal/ui": ["./packages/ui/src"],
      "@traderterminal/ui/*": ["./packages/ui/src/*"]
    }
  }
}
```

## Testing & Validation

### 🎯 **Playwright GUI Testing Integration**

This phase incorporates **automated Playwright GUI testing** for comprehensive validation:

📄 **Framework Reference**: [`../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md`](../../PLAYWRIGHT_GUI_TESTING_FRAMEWORK.md)

**Phase-Specific Testing:**
- **Static File Serving**: Automated validation of webserver-first architecture
- **Hot-Reload Functionality**: Development mode testing and HMR validation  
- **Cross-Browser Compatibility**: Multi-browser static file serving validation
- **Performance Benchmarking**: Page load times and asset delivery metrics
- **Visual Regression**: Layout consistency across different deployment modes

#### Task -1.7.1: Phase-Specific Playwright Tests
```typescript
// tests/playwright/phase-specific/webserver-frontend-tests.spec.ts
import { test, expect } from '../core/base-test'
import { BrowserCompatibilityTest } from '../test-suites/cross-browser/browser-compatibility-test'

test.describe('Phase -1: Webserver-First Frontend', () => {
  test('Static file serving validation', async ({ traderTerminalPage, performanceTracker }) => {
    await traderTerminalPage.initialize()
    
    // Measure static file performance
    const loadMetrics = await performanceTracker.measurePageLoad()
    expect(loadMetrics.loadTime).toBeLessThan(3000)
    
    // Validate all assets load correctly
    await traderTerminalPage.verifyAllBrokerConnections()
  })
  
  test('WebServer vs Electron mode comparison', async ({ page }) => {
    // Test webserver mode
    await page.goto('http://localhost:8000/app')
    await page.waitForSelector('[data-testid="trading-dashboard"]')
    await page.screenshot({ path: 'tests/screenshots/webserver-mode.png' })
    
    // Validate identical functionality
    const webserverFeatures = await page.evaluate(() => {
      return {
        hasWebSocket: typeof WebSocket !== 'undefined',
        hasLocalStorage: typeof localStorage !== 'undefined',
        hasFetch: typeof fetch !== 'undefined'
      }
    })
    
    expect(webserverFeatures.hasWebSocket).toBe(true)
    expect(webserverFeatures.hasLocalStorage).toBe(true)
    expect(webserverFeatures.hasFetch).toBe(true)
  })
})

// Cross-browser webserver testing
BrowserCompatibilityTest.createCrossBrowserTest('Webserver Frontend', async (page, browserName) => {
  await page.goto('http://localhost:8000/app')
  await expect(page.locator('[data-testid="trading-dashboard"]')).toBeVisible()
  
  // Browser-specific validation
  console.log(`✅ Webserver frontend working in ${browserName}`)
})
```

#### Task -1.7.2: Kubernetes Deployment Validation
```typescript
// tests/playwright/phase-specific/kubernetes-deployment-tests.spec.ts
import { test, expect } from '../core/base-test'

test.describe('Kubernetes Deployment Validation', () => {
  test('Production deployment accessibility', async ({ page }) => {
    // Test ingress accessibility
    await page.goto('http://traderterminal.local')
    await page.waitForSelector('[data-testid="trading-dashboard"]')
    
    // Verify production optimizations
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime
      }
    })
    
    expect(performanceMetrics.loadTime).toBeLessThan(5000) // Production load time
    expect(performanceMetrics.firstContentfulPaint).toBeLessThan(2000)
  })
  
  test('Container health and readiness', async ({ page }) => {
    // Test health endpoints
    const healthCheck = await page.evaluate(async () => {
      const response = await fetch('/health')
      return await response.json()
    })
    
    expect(healthCheck.status).toBe('healthy')
    
    // Test readiness endpoint
    const readinessCheck = await page.evaluate(async () => {
      const response = await fetch('/ready')
      return await response.json()
    })
    
    expect(readinessCheck.ready).toBe(true)
  })
})
```

**Success Criteria:**
- ✅ All phase-specific Playwright tests pass
- ✅ Webserver and Electron modes function identically
- ✅ Kubernetes deployment accessibility confirmed
- ✅ Cross-browser compatibility validated
```

### Traditional Smoke Tests (Enhanced)
1. **Backend serves static files**: `curl http://localhost:8000/app`
   - ✅ **Playwright Enhancement**: Automated visual validation of served content
2. **WebSocket connection works**: Test with wscat
   - ✅ **Playwright Enhancement**: Real-time WebSocket message flow validation
3. **API endpoints accessible**: `curl http://localhost:8000/health`
   - ✅ **Playwright Enhancement**: API response validation through browser context
4. **Electron loads web UI**: `npm run dev:electron`
   - ✅ **Playwright Enhancement**: Desktop app integration and IPC testing

### Enhanced Integration Tests
1. **Build Docker image and verify size < 400MB**
   - ✅ **Playwright Enhancement**: Container UI validation and performance testing
2. **Deploy to local Kubernetes and verify all pods healthy**
   - ✅ **Playwright Enhancement**: Kubernetes-deployed UI accessibility testing
3. **Access UI through ingress at http://traderterminal.local**
   - ✅ **Playwright Enhancement**: Production-like environment GUI validation
4. **Verify hot-reload works in development mode**
   - ✅ **Playwright Enhancement**: Automated HMR testing and component reload validation

## Rollback Plan

If issues arise:
1. Electron can temporarily embed the UI directly (existing setup)
2. Revert to serving UI from Electron's file:// protocol
3. All changes are additive - original code remains functional

## Success Criteria Met When

- [ ] `npm run dev:full` starts both backend and web UI
  - [ ] **Playwright Test**: Automated startup validation and component readiness
- [ ] http://localhost:8000/app shows trading dashboard
  - [ ] **Playwright Test**: Full dashboard visual and functional validation
  - [ ] **Playwright Test**: Cross-browser compatibility verification
- [ ] Electron app loads from web server URL
  - [ ] **Playwright Test**: Desktop app launcher and window management testing
  - [ ] **Playwright Test**: IPC bridge functionality validation
- [ ] Docker image builds successfully
  - [ ] **Playwright Test**: Containerized UI performance and functionality testing
- [ ] Kubernetes deployment succeeds
  - [ ] **Playwright Test**: Production environment GUI validation
- [ ] All existing functionality preserved
  - [ ] **Playwright Test Suite**: Comprehensive regression testing
    - [ ] Webserver-first architecture validation
    - [ ] Static file serving performance testing  
    - [ ] Hot-reload and development mode testing
    - [ ] Cross-browser compatibility validation
    - [ ] Kubernetes deployment accessibility testing 