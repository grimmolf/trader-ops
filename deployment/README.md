# TraderTerminal Deployment Guide

Complete containerization and deployment solutions for the TraderTerminal trading platform, supporting both development and production environments across macOS and Fedora Linux.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Production Deployment](#production-deployment)
- [Container Architecture](#container-architecture)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

This deployment system provides:

- **🐳 Containerized Services**: DataHub API, Redis cache, Kairos automation
- **🔧 Development Tools**: Hot-reload, debugging, easy service management
- **🚀 Production Ready**: Security hardened, resource optimized, auto-restart
- **🖥️ Multi-Platform**: macOS (launchd) and Fedora (SystemD) support
- **📊 Monitoring**: Health checks, logging, optional Prometheus integration

## Quick Start

### Development Environment

**Option 1: Docker/Podman Compose (Recommended)**
```bash
# Start all services with hot reload
./deployment/scripts/dev-compose.sh build
./deployment/scripts/dev-compose.sh start

# Check status
./deployment/scripts/dev-compose.sh status

# View logs
./deployment/scripts/dev-compose.sh logs

# Stop when done
./deployment/scripts/dev-compose.sh stop
```

**Option 2: Native Development**
```bash
# Terminal 1: Backend
PYTHONPATH=$(pwd) uv run uvicorn src.backend.datahub.server:app --host localhost --port 8080 --reload

# Terminal 2: Frontend (in src/frontend/)
npm run dev
```

### Production Deployment

**Fedora (SystemD)**
```bash
# Automated installation
sudo ./deployment/scripts/install-fedora.sh

# Manual control
systemctl --user start pod-traderterminal-pod.service
systemctl --user status pod-traderterminal-pod.service
```

**macOS (launchd)**
```bash
# Automated installation  
./deployment/scripts/install-macos.sh

# Manual control
launchctl start com.traderterminal.pod
launchctl list | grep traderterminal
```

## Development Environment

### Architecture

```
┌─────────────────────────────────────────┐
│           Development Stack              │
├─────────────────────────────────────────┤
│  Frontend (Hot Reload)                  │
│  ├── Electron App (localhost:5173)     │
│  ├── Vue 3 + TypeScript + Vite         │
│  └── TradingView Integration            │
├─────────────────────────────────────────┤
│  Backend Services (Containerized)      │
│  ├── DataHub API (localhost:8080)      │
│  ├── Redis Cache (localhost:6379)      │
│  └── Kairos Automation (localhost:8081)│
└─────────────────────────────────────────┘
```

### Development Workflow

1. **Start Backend Services**:
   ```bash
   cd deployment/scripts
   ./dev-compose.sh start
   ```

2. **Start Frontend Development**:
   ```bash
   cd src/frontend
   npm run dev
   ```

3. **Development Features**:
   - ✅ **Hot Reload**: Backend code changes trigger restart
   - ✅ **Debug Logging**: Full debug output for troubleshooting
   - ✅ **Volume Mounts**: Source code mounted for instant updates
   - ✅ **Health Checks**: Automatic service health monitoring
   - ✅ **Easy Logs**: `./dev-compose.sh logs [service]`

### Development Commands

```bash
# Service management
./dev-compose.sh start          # Start all services
./dev-compose.sh stop           # Stop all services
./dev-compose.sh restart        # Restart all services
./dev-compose.sh status         # Check service health

# Debugging
./dev-compose.sh logs datahub   # View DataHub logs
./dev-compose.sh logs kairos    # View Kairos logs
./dev-compose.sh logs           # View all logs

# Container access
./dev-compose.sh exec datahub bash      # Shell into DataHub
./dev-compose.sh exec redis redis-cli   # Redis CLI

# Cleanup
./dev-compose.sh clean          # Remove all containers and images
```

## Production Deployment

### Fedora Linux (SystemD)

**Automated Installation**:
```bash
# Download and run installer
curl -sSL https://raw.githubusercontent.com/grimmolf/trader-ops/main/deployment/scripts/install-fedora.sh | bash

# Or clone and run locally
git clone https://github.com/grimmolf/trader-ops.git
cd trader-ops
./deployment/scripts/install-fedora.sh
```

**Manual Installation**:
```bash
# 1. Install Podman
sudo dnf install -y podman podman-compose

# 2. Build images
podman build -f deployment/containers/Containerfile.datahub -t traderterminal-datahub .
podman build -f deployment/containers/Containerfile.redis -t traderterminal-redis .
podman build -f deployment/containers/Containerfile.kairos -t traderterminal-kairos .

# 3. Create pod and start services
podman pod create --name traderterminal-pod --publish 8080:8080 --publish 6379:6379
podman run -d --name datahub --pod traderterminal-pod traderterminal-datahub
podman run -d --name redis --pod traderterminal-pod traderterminal-redis
podman run -d --name kairos --pod traderterminal-pod traderterminal-kairos

# 4. Generate and enable SystemD services
podman generate systemd --name traderterminal-pod --files --new
mkdir -p ~/.config/systemd/user
mv *.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now pod-traderterminal-pod.service
```

**SystemD Management**:
```bash
# Service control
systemctl --user start pod-traderterminal-pod.service
systemctl --user stop pod-traderterminal-pod.service
systemctl --user restart pod-traderterminal-pod.service
systemctl --user status pod-traderterminal-pod.service

# View logs
journalctl --user -u pod-traderterminal-pod.service -f

# Enable auto-start
systemctl --user enable pod-traderterminal-pod.service
```

### macOS (launchd)

**Automated Installation**:
```bash
# Install Homebrew (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Run installer
./deployment/scripts/install-macos.sh
```

**Manual Installation**:
```bash
# 1. Install Podman via Homebrew
brew install podman
podman machine init
podman machine start

# 2. Build and run (similar to Fedora)
# ... same container commands as above ...

# 3. Create launchd service
cp deployment/scripts/com.traderterminal.pod.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.traderterminal.pod.plist
```

**launchd Management**:
```bash
# Service control
launchctl start com.traderterminal.pod
launchctl stop com.traderterminal.pod

# Check status
launchctl list | grep traderterminal

# View logs
tail -f ~/.local/share/traderterminal/logs/traderterminal-output.log
```

## Container Architecture

### Services Overview

| Service | Port | Purpose | Resources |
|---------|------|---------|-----------|
| **DataHub** | 8080 | Main API, UDF protocol, WebSocket streaming | 2GB RAM, 2 CPU |
| **Redis** | 6379 | Cache, session state, real-time data | 512MB RAM, 0.5 CPU |
| **Kairos** | 8081 | Strategy automation, backtesting | 1GB RAM, 1 CPU |

### Container Features

- **🔒 Security**: Non-root users, read-only filesystems, resource limits
- **📊 Health Checks**: HTTP and TCP health monitoring
- **🔄 Auto-Restart**: Automatic restart on failure
- **📝 Logging**: Structured logging with log rotation
- **🎯 Isolation**: Separate network namespace for security

### Container Images

```bash
# Base images
ghcr.io/grimmolf/traderterminal-datahub:latest    # FastAPI backend
ghcr.io/grimmolf/traderterminal-redis:latest      # Redis cache
ghcr.io/grimmolf/traderterminal-kairos:latest     # Automation service

# Development images (locally built)
traderterminal-datahub-dev                        # Dev with hot reload
traderterminal-redis-dev                          # Dev Redis
traderterminal-kairos-dev                         # Dev automation
```

## Configuration

### Environment Configuration

**Development** (`deployment/compose/.env.dev`):
```bash
# Backend configuration
LOG_LEVEL=DEBUG
DEVELOPMENT_MODE=true
REDIS_URL=redis://redis:6379

# Broker settings (optional)
TRADIER_API_KEY=your_api_key_here
TRADIER_ACCOUNT_ID=your_account_id
```

**Production** (`/etc/traderterminal/traderterminal.yaml`):
```yaml
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
    mock:
      enabled: true
      
backtesting:
  max_concurrent: 5
  timeout_seconds: 300
  
execution:
  default_broker: "tradier"
  risk_checks: true
  max_position_size: 10000
```

### Volume Mounts

**Development**:
- Source code: `./src -> /app/src` (read-only)
- Configuration: `./config -> /etc/traderterminal` (read-only)
- Data: Named volumes for persistence

**Production**:
- Configuration: `/etc/traderterminal` (system config)
- Data: `/var/lib/traderterminal` (persistent data)
- Logs: `/var/log/traderterminal` (log files)

## Monitoring

### Health Checks

All services include comprehensive health checks:

```bash
# Check service health
curl http://localhost:8080/health      # DataHub API
redis-cli -p 6379 ping               # Redis
curl http://localhost:8081/health     # Kairos (if enabled)
```

### Logging

**Development**:
```bash
# View real-time logs
./dev-compose.sh logs                 # All services
./dev-compose.sh logs datahub         # Specific service
```

**Production**:
```bash
# SystemD logs (Fedora)
journalctl --user -u pod-traderterminal-pod.service -f

# File logs (macOS)
tail -f ~/.local/share/traderterminal/logs/traderterminal-output.log
```

### Prometheus Monitoring (Optional)

Enable monitoring stack:
```bash
# Development
docker-compose -f deployment/compose/docker-compose.dev.yml --profile monitoring up

# Production
docker-compose -f deployment/compose/docker-compose.prod.yml --profile monitoring up
```

Access Prometheus at: http://localhost:9090

## Troubleshooting

### Common Issues

**Container Build Failures**:
```bash
# Clean build cache
podman system prune -a

# Rebuild from scratch
./dev-compose.sh clean
./dev-compose.sh build
```

**Port Conflicts**:
```bash
# Check what's using ports
lsof -i :8080
lsof -i :6379

# Kill conflicting processes
pkill -f "port 8080"
```

**Permission Issues**:
```bash
# Fix data directory permissions
sudo chown -R 1001:1001 /var/lib/traderterminal
```

**Service Won't Start**:
```bash
# Check detailed logs
./dev-compose.sh logs datahub

# Check health status
./dev-compose.sh status

# Restart specific service
docker-compose restart datahub
```

### Debug Mode

Enable debug logging:
```bash
# Development
export LOG_LEVEL=DEBUG
./dev-compose.sh restart

# Production
# Edit /etc/traderterminal/traderterminal.yaml
# Set: logging.level: DEBUG
systemctl --user restart pod-traderterminal-pod.service
```

### Network Issues

**Container Connectivity**:
```bash
# Test inter-service communication
./dev-compose.sh exec datahub curl http://redis:6379
./dev-compose.sh exec kairos curl http://datahub:8080/health
```

**External Access**:
```bash
# Check firewall (Fedora)
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=8080/tcp --permanent

# Check binding (macOS)
netstat -an | grep 8080
```

### Performance Tuning

**Resource Limits**:
```yaml
# Adjust in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G      # Increase if needed
      cpus: '4'       # Increase if needed
```

**Redis Optimization**:
```bash
# Monitor Redis memory
./dev-compose.sh exec redis redis-cli info memory

# Adjust Redis settings in Containerfile.redis
--maxmemory 512mb
--maxmemory-policy allkeys-lru
```

---

## Support

- **Documentation**: [Complete deployment docs](../docs/)
- **Issues**: [GitHub Issues](https://github.com/grimmolf/trader-ops/issues)
- **Community**: [GitHub Discussions](https://github.com/grimmolf/trader-ops/discussions)

---

**Built with ❤️ for professional traders who demand reliable, scalable infrastructure.**

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>