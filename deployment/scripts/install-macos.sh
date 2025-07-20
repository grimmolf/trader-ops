#!/bin/bash
# TraderTerminal macOS Installation Script
# Sets up Podman containers and launchd services for production deployment

set -euo pipefail

# Configuration
POD_NAME="traderterminal-pod"
CONTAINER_REGISTRY="ghcr.io/grimmolf"
CONFIG_DIR="$HOME/.config/traderterminal"
DATA_DIR="$HOME/.local/share/traderterminal"
LOG_DIR="$HOME/.local/share/traderterminal/logs"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
    exit 1
}

# Check if running on macOS
check_macos() {
    if [[ "$(uname)" != "Darwin" ]]; then
        error "This script is only for macOS. Use install-fedora.sh for Fedora."
    fi
}

# Install dependencies via Homebrew
install_dependencies() {
    log "Installing system dependencies..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        error "Homebrew is required. Install from https://brew.sh"
    fi
    
    # Install Podman if not present
    if ! command -v podman &> /dev/null; then
        log "Installing Podman..."
        brew install podman
        podman machine init
        podman machine start
    fi
    
    success "Dependencies installed"
}

# Create directories
create_directories() {
    log "Creating user directories..."
    
    mkdir -p "${CONFIG_DIR}" "${DATA_DIR}" "${LOG_DIR}" "${LAUNCHD_DIR}"
    mkdir -p "${DATA_DIR}/redis" "${DATA_DIR}/kairos" "${DATA_DIR}/datahub"
    
    success "Directories created"
}

# Build container images
build_images() {
    log "Building container images..."
    
    local project_root
    project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
    
    # Build DataHub container
    log "Building DataHub container..."
    podman build -f "${project_root}/deployment/containers/Containerfile.datahub" \
                  -t "${CONTAINER_REGISTRY}/traderterminal-datahub:latest" \
                  "${project_root}"
    
    # Build Redis container
    log "Building Redis container..."
    podman build -f "${project_root}/deployment/containers/Containerfile.redis" \
                  -t "${CONTAINER_REGISTRY}/traderterminal-redis:latest" \
                  "${project_root}"
    
    # Build Kairos container
    log "Building Kairos container..."
    podman build -f "${project_root}/deployment/containers/Containerfile.kairos" \
                  -t "${CONTAINER_REGISTRY}/traderterminal-kairos:latest" \
                  "${project_root}"
    
    success "Container images built"
}

# Create pod and containers
create_pod() {
    log "Creating TraderTerminal pod..."
    
    # Remove existing pod if it exists
    if podman pod exists "${POD_NAME}"; then
        warning "Removing existing pod: ${POD_NAME}"
        podman pod stop "${POD_NAME}" || true
        podman pod rm "${POD_NAME}" || true
    fi
    
    # Create new pod with port mappings
    podman pod create \
        --name "${POD_NAME}" \
        --publish 8080:8080 \
        --publish 6379:6379 \
        --publish 8081:8081
    
    success "Pod created: ${POD_NAME}"
}

# Start containers
start_containers() {
    log "Starting containers..."
    
    # Start Redis container
    podman run -d \
        --name traderterminal-redis \
        --pod "${POD_NAME}" \
        --volume "${DATA_DIR}/redis:/data:z" \
        "${CONTAINER_REGISTRY}/traderterminal-redis:latest"
    
    # Start DataHub container
    podman run -d \
        --name traderterminal-datahub \
        --pod "${POD_NAME}" \
        --volume "${CONFIG_DIR}:/etc/traderterminal:ro,z" \
        --volume "${DATA_DIR}/datahub:/app/data:z" \
        --env REDIS_URL="redis://localhost:6379" \
        --env KAIROS_URL="http://localhost:8081" \
        "${CONTAINER_REGISTRY}/traderterminal-datahub:latest"
    
    # Start Kairos container
    podman run -d \
        --name traderterminal-kairos \
        --pod "${POD_NAME}" \
        --volume "${CONFIG_DIR}:/etc/traderterminal:ro,z" \
        --volume "${DATA_DIR}/kairos:/app/data:z" \
        --env DATAHUB_URL="http://localhost:8080" \
        --env REDIS_URL="redis://localhost:6379" \
        --env HEADLESS_MODE="true" \
        "${CONTAINER_REGISTRY}/traderterminal-kairos:latest"
    
    success "Containers started"
}

# Generate launchd service
generate_launchd_service() {
    log "Generating launchd service..."
    
    cat > "${LAUNCHD_DIR}/com.traderterminal.pod.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.traderterminal.pod</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$(which podman)</string>
        <string>pod</string>
        <string>start</string>
        <string>${POD_NAME}</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/traderterminal-error.log</string>
    
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/traderterminal-output.log</string>
    
    <key>WorkingDirectory</key>
    <string>${DATA_DIR}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>
    
    <key>ProcessType</key>
    <string>Background</string>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF
    
    # Load the service
    launchctl load "${LAUNCHD_DIR}/com.traderterminal.pod.plist"
    
    success "launchd service generated and loaded"
}

# Create configuration template
create_config() {
    log "Creating configuration template..."
    
    cat > "${CONFIG_DIR}/traderterminal.yaml" << 'EOF'
# TraderTerminal macOS Configuration
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
  max_concurrent: 3
  timeout_seconds: 300
  kairos_path: /app/src/automation/kairos_jobs
  
execution:
  default_broker: "tradier"
  risk_checks: true
  max_position_size: 10000
  
logging:
  level: INFO
  file: ~/.local/share/traderterminal/logs/app.log
EOF
    
    success "Configuration template created at ${CONFIG_DIR}/traderterminal.yaml"
}

# Main installation function
main() {
    log "Starting TraderTerminal installation for macOS..."
    
    check_macos
    install_dependencies
    create_directories
    build_images
    create_pod
    start_containers
    generate_launchd_service
    create_config
    
    success "TraderTerminal installation completed!"
    echo
    echo "Next steps:"
    echo "1. Edit ${CONFIG_DIR}/traderterminal.yaml with your broker credentials"
    echo "2. Check service status: launchctl list | grep com.traderterminal"
    echo "3. View logs: tail -f ${LOG_DIR}/traderterminal-output.log"
    echo "4. Access the API at: http://localhost:8080"
    echo "5. Desktop app: npm run dev from src/frontend/"
    echo
    warning "The service will start automatically at login"
    warning "To manually control: launchctl start/stop com.traderterminal.pod"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi