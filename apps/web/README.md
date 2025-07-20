# TraderTerminal Web Application

**Professional trading dashboard as a standalone web application**

The web application provides full TraderTerminal functionality through a modern Vue 3 SPA, enabling cloud deployments and browser-based trading.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Development server (with backend proxy)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## 📋 Features

### Trading Interface
- **Multi-Broker Support**: Schwab, Tastytrade, TopstepX, Tradovate
- **Real-Time Data**: Live quotes, positions, and P&L via WebSocket
- **Order Management**: Advanced order entry and execution
- **Risk Management**: Funded account monitoring and controls

### Technical Features
- **Vue 3 + TypeScript**: Modern reactive framework with type safety
- **Component Library**: Shared UI components from `@trader-terminal/ui`
- **Real-Time Updates**: WebSocket integration for live data
- **Responsive Design**: Optimized for desktop and tablet use

## 🏗️ Architecture

### Build Output
- **Bundle Size**: ~93kB optimized production build
- **Vendor Chunking**: Separate chunks for Vue, utilities, and charts
- **Source Maps**: Available for debugging

### API Integration
```typescript
// Development proxy configuration (vite.config.ts)
proxy: {
  '/api': 'http://localhost:8080',      // Backend API
  '/webhook': 'http://localhost:8080',   // TradingView webhooks  
  '/stream': 'ws://localhost:8080'       // WebSocket real-time data
}
```

### Deployment Modes

#### 1. **Integrated Deployment** (Recommended)
FastAPI backend serves the web app directly:
```bash
cd ../../src/backend
uv run python -m datahub.server
# Visit: http://localhost:8080
```

#### 2. **Standalone Deployment**
Serve from any web server:
```bash
npm run build
# Deploy dist/ folder to your web server
```

## 📁 Project Structure

```
apps/web/
├── src/
│   ├── views/              # Trading dashboard pages
│   │   ├── DashboardView.vue    # Main trading interface
│   │   ├── AccountsView.vue     # Account management
│   │   ├── OrdersView.vue       # Order management
│   │   ├── PositionsView.vue    # Position tracking
│   │   ├── BacktestView.vue     # Strategy backtesting
│   │   └── SettingsView.vue     # Configuration
│   ├── router/             # Vue Router configuration
│   ├── stores/             # Pinia state management
│   ├── composables/        # Reusable composition functions
│   └── main.ts             # Application entry point
├── dist/                   # Production build output
└── package.json            # Dependencies and scripts
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend API URL (development)
VITE_API_URL=http://localhost:8080

# WebSocket URL (development)  
VITE_WS_URL=ws://localhost:8080

# Deployment mode detection
VITE_DEPLOYMENT_MODE=web  # web | electron | tauri
```

### Build Configuration
- **Target**: ES2020 for modern browser support
- **Bundler**: Vite with optimized production builds
- **TypeScript**: Strict mode with comprehensive type checking
- **CSS**: Scoped Vue component styles

## 🧪 Development

### Hot Module Replacement
```bash
npm run dev
# Server runs on http://localhost:5173 with HMR
```

### TypeScript Type Checking
```bash
npm run type-check
# Validates TypeScript without emitting files
```

### Production Preview
```bash
npm run build && npm run preview
# Builds and serves production version
```

## 🔗 Integration

### Shared Components
The web app imports trading components from the shared UI library:
```typescript
import { 
  RiskMeter, 
  AccountSelector, 
  FundedAccountPanel 
} from '@trader-terminal/ui'
```

### Backend Communication
- **REST API**: Trading operations, account data, market data
- **WebSocket**: Real-time quotes, position updates, alerts
- **Webhooks**: TradingView strategy alerts and execution

## 🚀 Deployment

### Cloud Deployment
1. **Build the application**: `npm run build`
2. **Deploy dist/ folder** to your cloud provider
3. **Configure API endpoints** via environment variables
4. **Set up SSL/TLS** for secure trading operations

### Container Deployment
```dockerfile
# Example Dockerfile for standalone deployment
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### Integrated with FastAPI
The recommended deployment serves the web app directly from the FastAPI backend:
- **Single Service**: Combined API and web server
- **Simplified Deployment**: One container, one port
- **Development Friendly**: Unified logging and debugging

## 🔒 Security

### Production Considerations
- **HTTPS Only**: All trading operations require secure connections
- **CORS Configuration**: Properly configured for your domain
- **API Authentication**: Secure token-based authentication
- **WebSocket Security**: Authenticated real-time connections

## 📚 Related Documentation

- [Shared UI Library](../../packages/ui/README.md)
- [Backend API Documentation](../../docs/api/README.md)
- [System Architecture](../../docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Development Workflow](../../docs/developer/DEVELOPMENT_WORKFLOW.md)

---

**Part of TraderTerminal**: The $41/month Bloomberg Terminal alternative