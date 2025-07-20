# TradeNote Integration Setup Guide

Complete installation and configuration guide for TradeNote trade journaling in TraderTerminal.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Frontend Setup](#frontend-setup)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## 🔍 Overview

TradeNote integration provides automated trade journaling with professional analytics for all trading activities in TraderTerminal. It automatically captures and logs trades from:

- **Live Trading**: Real-time execution logging from all broker integrations
- **Paper Trading**: Complete simulation trade capture with performance tracking
- **Strategy Execution**: Automated strategy performance logging with detailed metrics

### Key Benefits
- **Zero-Effort Logging**: Automatic trade capture across all execution pipelines
- **Professional Analytics**: 20+ performance metrics with visual dashboards
- **Calendar Heat-Map**: Daily P&L visualization with interactive analysis
- **Multi-Account Support**: Separate journaling for live, paper, and funded accounts
- **Export Capabilities**: Tax reporting and compliance-ready data exports

## ✅ Prerequisites

### System Requirements
- **Docker/Podman**: Container runtime for TradeNote services
- **TraderTerminal**: Main trading platform (must be installed first)
- **MongoDB**: Database for trade journal storage (automated via containers)
- **Disk Space**: 2GB minimum for containers and data storage

### Supported Platforms
- **macOS**: Primary development platform
- **Linux**: Fedora/RHEL, Ubuntu/Debian
- **Windows**: WSL2 with Docker Desktop

### Verify Prerequisites
```bash
# Check Docker/Podman installation
docker --version
# OR
podman --version

# Verify TraderTerminal installation
cd /path/to/trader-ops
ls -la deployment/scripts/tradenote-setup.sh
```

## ⚡ Quick Start

### One-Command Development Setup

```bash
# Navigate to TraderTerminal directory
cd /path/to/trader-ops

# Start TradeNote services for development
./deployment/scripts/tradenote-setup.sh development setup
```

**Services Started:**
- **TradeNote**: http://localhost:8082
- **MongoDB**: localhost:27017
- **Automatic Integration**: TraderTerminal ↔ TradeNote

**Development Credentials:**
```
MongoDB User: tradenote
MongoDB Password: tradenote123
App ID: traderterminal_dev_123
Master Key: traderterminal_master_dev_456
```

### Verify Installation
```bash
# Check service status
./deployment/scripts/tradenote-setup.sh development status

# View logs
./deployment/scripts/tradenote-setup.sh development logs
```

### Quick Test
1. **Open TraderTerminal**: Launch the main trading platform
2. **Navigate to TradeNote Panel**: Look for the "Trade Journal" section
3. **Check Connection**: Green status indicator shows successful integration
4. **Test Trade**: Execute a paper trade and verify it appears in TradeNote

## 🛠️ Development Setup

### Step-by-Step Development Installation

#### 1. Prepare Environment
```bash
# Navigate to project root
cd /path/to/trader-ops

# Ensure Docker/Podman is running
docker info
# OR
podman info
```

#### 2. Start TradeNote Services
```bash
# Start all TradeNote services
./deployment/scripts/tradenote-setup.sh development setup

# Expected output:
# [INFO] Setting up TradeNote for development environment
# [INFO] Starting TradeNote services...
# [INFO] Waiting for TradeNote services to be ready...
# [SUCCESS] TradeNote development setup complete!
```

#### 3. Verify Service Health
```bash
# Check all services are running
docker compose -f deployment/compose/docker-compose.dev.yml ps

# Expected output:
# NAME                               COMMAND                  SERVICE          STATUS              PORTS
# traderterminal-tradenote-dev       "docker-entrypoint.s…"   tradenote        running (healthy)   0.0.0.0:8082->8080/tcp
# traderterminal-tradenote-mongo-dev "docker-entrypoint.s…"   tradenote-mongo  running (healthy)   0.0.0.0:27017->27017/tcp
```

#### 4. Configure TraderTerminal Integration
```bash
# Start TraderTerminal backend (if not already running)
cd src/backend
uv run uvicorn datahub.server:app --reload --port 8080

# Start TraderTerminal frontend (if not already running)
cd src/frontend
npm run dev
```

#### 5. Test Integration
1. **Open TraderTerminal**: http://localhost:5173
2. **Navigate to TradeNote Panel**: Find "Trade Journal" in the interface
3. **Test Connection**: Click "Test Connection" in settings
4. **Execute Test Trade**: Run a paper trade to verify logging

### Development Features
- **Hot Reload**: TradeNote service updates automatically
- **Debug Logging**: Detailed logs for troubleshooting
- **Plain Text Credentials**: Easy development setup
- **Reset Capability**: Easy data reset for testing

## 🚀 Production Deployment

### Production Setup with Secure Secrets

#### 1. Production Installation
```bash
# Run production setup (requires sudo for secret management)
sudo ./deployment/scripts/tradenote-setup.sh production setup
```

#### 2. Secure Secret Generation
The production setup automatically generates and stores secure credentials:

```bash
# Production secrets stored in:
/etc/traderterminal/secrets/tradenote_mongo_user.txt
/etc/traderterminal/secrets/tradenote_mongo_password.txt
/etc/traderterminal/secrets/tradenote_mongo_uri.txt
/etc/traderterminal/secrets/tradenote_app_id.txt
/etc/traderterminal/secrets/tradenote_master_key.txt

# Permissions: 600 (owner read/write only)
# Owner: 1001:1001 (container user)
```

#### 3. Production Configuration
```bash
# View production services
docker compose -f deployment/compose/docker-compose.prod.yml ps

# Monitor production logs
docker compose -f deployment/compose/docker-compose.prod.yml logs -f tradenote tradenote-mongo
```

#### 4. Production Security Features
- **Encrypted Credentials**: All secrets stored in secure files
- **Network Isolation**: Services communicate via internal Docker network
- **Access Control**: MongoDB authentication with unique credentials
- **Container Security**: Non-root user execution
- **Port Binding**: Services accessible only from localhost

### Production Management Commands
```bash
# Start production services
sudo ./deployment/scripts/tradenote-setup.sh production setup

# Stop production services
sudo ./deployment/scripts/tradenote-setup.sh production stop

# View production status
sudo ./deployment/scripts/tradenote-setup.sh production status

# View production logs
sudo ./deployment/scripts/tradenote-setup.sh production logs
```

## ⚙️ Configuration

### Backend Configuration

#### Environment Variables
```bash
# Development (.env or environment)
TRADENOTE_BASE_URL=http://localhost:8082
TRADENOTE_APP_ID=traderterminal_dev_123
TRADENOTE_MASTER_KEY=traderterminal_master_dev_456
TRADENOTE_ENABLED=true
TRADENOTE_AUTO_SYNC=true

# Production (use secure file paths)
TRADENOTE_BASE_URL=http://localhost:8082
TRADENOTE_APP_ID_FILE=/etc/traderterminal/secrets/tradenote_app_id.txt
TRADENOTE_MASTER_KEY_FILE=/etc/traderterminal/secrets/tradenote_master_key.txt
TRADENOTE_ENABLED=true
```

#### Python Configuration
```python
# src/backend/integrations/tradenote/config.py
from src.backend.integrations.tradenote.models import TradeNoteConfig

# Development configuration
config = TradeNoteConfig(
    base_url="http://localhost:8082",
    app_id="traderterminal_dev_123",
    master_key="traderterminal_master_dev_456",
    enabled=True,
    auto_sync=True,
    timeout_seconds=30,
    retry_attempts=3,
    broker_name="TraderTerminal"
)

# Initialize service
from src.backend.integrations.tradenote.service import TradeNoteService
tradenote_service = TradeNoteService(config)
await tradenote_service.initialize()
```

### Container Configuration

#### Development Override
```yaml
# deployment/compose/docker-compose.dev.yml (excerpt)
services:
  tradenote:
    image: eleventrading/tradenote:latest
    ports:
      - "8082:8080"
    environment:
      - MONGO_URI=mongodb://tradenote:tradenote123@tradenote-mongo:27017/tradenote?authSource=admin
      - APP_ID=traderterminal_dev_123
      - MASTER_KEY=traderterminal_master_dev_456
      - NODE_ENV=development
```

#### Production Override
```yaml
# deployment/compose/docker-compose.prod.yml (excerpt)
services:
  tradenote:
    image: eleventrading/tradenote:latest
    ports:
      - "127.0.0.1:8082:8080"  # Localhost only
    environment:
      - MONGO_URI_FILE=/run/secrets/tradenote_mongo_uri
      - APP_ID_FILE=/run/secrets/tradenote_app_id
      - MASTER_KEY_FILE=/run/secrets/tradenote_master_key
    secrets:
      - tradenote_mongo_uri
      - tradenote_app_id
      - tradenote_master_key
```

## 🎨 Frontend Setup

### TradeNote Panel Configuration

#### 1. Access TradeNote Settings
1. **Open TraderTerminal**: Launch the main application
2. **Navigate to TradeNote Panel**: Find "Trade Journal" section
3. **Click Settings**: Gear icon in the panel header
4. **Configure Connection**: Enter TradeNote details

#### 2. Basic Configuration
```typescript
// Frontend configuration interface
interface TradeNoteConfig {
  base_url: string           // "http://localhost:8082"
  app_id: string            // "traderterminal_dev_123"
  master_key: string        // "traderterminal_master_dev_456"
  enabled: boolean          // true
  auto_sync: boolean        // true (sync every 5 minutes)
}
```

#### 3. Test Connection
1. **Enter Configuration**: Fill in the settings form
2. **Test Connection**: Click "Test Connection" button
3. **Verify Success**: Look for green success message
4. **Save Settings**: Click "Save Settings" to persist

#### 4. Enable Auto-Sync
- **Auto-sync**: Automatically sync new trades every 5 minutes
- **Manual Sync**: Use the sync button for immediate updates
- **Connection Status**: Real-time connection monitoring

### Frontend Features

#### Calendar View
- **Heat-Map Display**: Daily P&L color-coded visualization
- **Interactive Tooltips**: Hover for trade details
- **Period Selection**: 1 month, 3 months, 6 months, 1 year
- **Click-through**: Direct links to detailed TradeNote analysis

#### Analytics View
- **Performance Metrics**: 20+ key indicators
- **Risk Analysis**: Sharpe ratio, max drawdown, recovery factor
- **Trading Activity**: Win rate, profit factor, consecutive wins/losses
- **Cost Analysis**: Commission tracking and percentage analysis

#### Combined View
- **Dual Panel**: Calendar and analytics side-by-side
- **Responsive Design**: Adapts to screen size
- **Real-time Updates**: Live sync with trade execution

## 🐛 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check Docker/Podman status
docker info
systemctl status docker

# Check port conflicts
netstat -tuln | grep 8082
netstat -tuln | grep 27017

# Restart services
./deployment/scripts/tradenote-setup.sh development stop
./deployment/scripts/tradenote-setup.sh development setup
```

#### 2. Connection Failed
```bash
# Check service health
curl http://localhost:8082/health

# View service logs
docker compose -f deployment/compose/docker-compose.dev.yml logs tradenote

# Verify network connectivity
docker network ls
docker network inspect deployment_traderterminal
```

#### 3. Authentication Errors
```bash
# Verify credentials in development
echo "App ID: traderterminal_dev_123"
echo "Master Key: traderterminal_master_dev_456"

# Check production secrets
sudo cat /etc/traderterminal/secrets/tradenote_app_id.txt
sudo cat /etc/traderterminal/secrets/tradenote_master_key.txt
```

#### 4. Frontend Connection Issues
1. **Check URL**: Verify TradeNote URL in settings (http://localhost:8082)
2. **Test API**: Use browser to visit http://localhost:8082
3. **Clear Cache**: Clear TradeNote store cache in frontend
4. **Restart**: Restart TraderTerminal frontend

### Advanced Troubleshooting

#### Service Health Diagnostics
```bash
# Full service health check
docker compose -f deployment/compose/docker-compose.dev.yml ps
docker compose -f deployment/compose/docker-compose.dev.yml exec tradenote curl http://localhost:8080/health
docker compose -f deployment/compose/docker-compose.dev.yml exec tradenote-mongo mongosh --eval "db.adminCommand('ping')"
```

#### MongoDB Connection Test
```bash
# Test MongoDB connection
docker compose -f deployment/compose/docker-compose.dev.yml exec tradenote-mongo mongosh "mongodb://tradenote:tradenote123@localhost:27017/tradenote?authSource=admin" --eval "db.stats()"
```

#### Network Debugging
```bash
# Check container networking
docker compose -f deployment/compose/docker-compose.dev.yml exec tradenote ping tradenote-mongo
docker compose -f deployment/compose/docker-compose.dev.yml exec tradenote nslookup tradenote-mongo
```

#### Log Analysis
```bash
# Detailed logging
docker compose -f deployment/compose/docker-compose.dev.yml logs --follow --tail=100 tradenote
docker compose -f deployment/compose/docker-compose.dev.yml logs --follow --tail=100 tradenote-mongo

# Search for specific errors
docker compose -f deployment/compose/docker-compose.dev.yml logs tradenote | grep -i error
docker compose -f deployment/compose/docker-compose.dev.yml logs tradenote | grep -i "connection"
```

## 🔧 Advanced Configuration

### Custom TradeNote Instance

#### Using External TradeNote
```bash
# Update configuration for external instance
# Edit deployment/compose/docker-compose.dev.yml
services:
  tradenote:
    image: eleventrading/tradenote:latest
    ports:
      - "8082:8080"
    environment:
      - MONGO_URI=mongodb://user:password@external-mongo:27017/tradenote
      - APP_ID=your_custom_app_id
      - MASTER_KEY=your_custom_master_key
```

#### SSL/TLS Configuration
```yaml
# For HTTPS TradeNote instances
services:
  tradenote:
    environment:
      - SSL_ENABLED=true
      - SSL_CERT_PATH=/certs/cert.pem
      - SSL_KEY_PATH=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

### Performance Tuning

#### MongoDB Optimization
```yaml
# deployment/compose/docker-compose.prod.yml
services:
  tradenote-mongo:
    image: mongo:6.0
    command: >
      mongod --wiredTigerCacheSizeGB 1
             --wiredTigerCollectionBlockCompressor snappy
             --wiredTigerIndexPrefixCompression true
```

#### TradeNote Service Optimization
```yaml
services:
  tradenote:
    environment:
      - NODE_ENV=production
      - NODE_OPTIONS=--max-old-space-size=1024
      - WORKERS=2
    deploy:
      resources:
        limits:
          memory: 1GB
          cpus: '1.0'
```

### Multi-Environment Setup

#### Development + Staging + Production
```bash
# Development environment
./deployment/scripts/tradenote-setup.sh development setup

# Production environment (different ports)
# Edit docker-compose.prod.yml to use different ports
# Then run:
./deployment/scripts/tradenote-setup.sh production setup
```

### Backup and Restore

#### Database Backup
```bash
# Create backup
docker compose -f deployment/compose/docker-compose.prod.yml exec tradenote-mongo mongodump --uri="mongodb://tradenote:password@localhost:27017/tradenote" --out=/backup

# Restore from backup
docker compose -f deployment/compose/docker-compose.prod.yml exec tradenote-mongo mongorestore --uri="mongodb://tradenote:password@localhost:27017/tradenote" /backup/tradenote
```

#### Configuration Backup
```bash
# Backup production secrets
sudo tar -czf tradenote-secrets-backup-$(date +%Y%m%d).tar.gz /etc/traderterminal/secrets/

# Restore secrets
sudo tar -xzf tradenote-secrets-backup-YYYYMMDD.tar.gz -C /
```

### Monitoring and Alerting

#### Health Check Automation
```bash
#!/bin/bash
# health-check.sh - Monitor TradeNote services

TRADENOTE_URL="http://localhost:8082"
MONGO_URI="mongodb://tradenote:password@localhost:27017/tradenote"

# Check TradeNote API
if ! curl -f "$TRADENOTE_URL/health" > /dev/null 2>&1; then
    echo "ERROR: TradeNote API not responding"
    exit 1
fi

# Check MongoDB
if ! docker compose -f deployment/compose/docker-compose.prod.yml exec tradenote-mongo mongosh "$MONGO_URI" --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "ERROR: MongoDB not responding"
    exit 1
fi

echo "All services healthy"
```

#### Log Rotation
```bash
# Setup log rotation for Docker containers
sudo tee /etc/logrotate.d/docker-compose <<EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    missingok
    notifempty
    compress
    copytruncate
}
EOF
```

## 📚 Additional Resources

### Documentation Links
- **TradeNote Documentation**: https://github.com/ElevenTradingLtd/tradenote
- **MongoDB Documentation**: https://docs.mongodb.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/

### Support and Community
- **TraderTerminal Issues**: https://github.com/grimmolf/trader-ops/issues
- **TradeNote Issues**: https://github.com/ElevenTradingLtd/tradenote/issues
- **Development Discussions**: Project discussion forums

### Migration and Upgrades
- **TradeNote Updates**: Pull latest container images
- **Data Migration**: Export/import procedures
- **Configuration Updates**: Version-specific changes

---

This comprehensive setup guide provides everything needed to successfully integrate TradeNote trade journaling into TraderTerminal, from quick development setup to production deployment with enterprise-grade security.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>