#!/bin/bash
# TraderTerminal Fedora Installation Script
# Sets up Podman containers and SystemD services for production deployment

set -euo pipefail

# Configuration
POD_NAME="traderterminal-pod"
CONTAINER_REGISTRY="ghcr.io/grimmolf"
CONFIG_DIR="/etc/traderterminal"
DATA_DIR="/var/lib/traderterminal"
LOG_DIR="/var/log/traderterminal"

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Run as regular user with sudo access."
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Check if podman is installed
    if ! command -v podman &> /dev/null; then
        sudo dnf install -y podman podman-compose
    fi
    
    # Check if systemctl is available
    if ! command -v systemctl &> /dev/null; then
        error "SystemD is required for this installation"
    fi
    
    success "Dependencies installed"
}

# Create directories
create_directories() {
    log "Creating system directories..."
    
    sudo mkdir -p "${CONFIG_DIR}" "${DATA_DIR}" "${LOG_DIR}"
    sudo mkdir -p "${DATA_DIR}/redis" "${DATA_DIR}/kairos" "${DATA_DIR}/datahub"
    
    # Set permissions for non-root containers
    sudo chown -R 1001:1001 "${DATA_DIR}"
    sudo chown -R $(id -u):$(id -g) "${CONFIG_DIR}"
    
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

# Generate SystemD service files
generate_systemd_services() {
    log "Generating SystemD service files..."
    
    # Generate systemd units for the pod
    podman generate systemd \
        --name "${POD_NAME}" \
        --files \
        --new \
        --restart-policy=always
    
    # Install systemd units
    mkdir -p ~/.config/systemd/user
    mv *.service ~/.config/systemd/user/
    
    # Reload systemd and enable services
    systemctl --user daemon-reload
    systemctl --user enable "pod-${POD_NAME}.service"
    
    success "SystemD services generated and enabled"
}

# Create configuration template
create_config() {
    log "Creating configuration template..."
    
    cat > "${CONFIG_DIR}/traderterminal.yaml" << 'EOF'
# TraderTerminal Production Configuration
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
  kairos_path: /app/src/automation/kairos_jobs
  
execution:
  default_broker: "tradier"
  risk_checks: true
  max_position_size: 10000
  
logging:
  level: INFO
  file: /var/log/traderterminal/app.log
EOF
    
    success "Configuration template created at ${CONFIG_DIR}/traderterminal.yaml"
}

# Main installation function
main() {
    log "Starting TraderTerminal installation for Fedora..."
    
    check_root
    install_dependencies
    create_directories
    build_images
    create_pod
    start_containers
    generate_systemd_services
    create_config
    
    success "TraderTerminal installation completed!"
    echo
    echo "Next steps:"
    echo "1. Edit ${CONFIG_DIR}/traderterminal.yaml with your broker credentials"
    echo "2. Start the service: systemctl --user start pod-${POD_NAME}.service"
    echo "3. Check status: systemctl --user status pod-${POD_NAME}.service"
    echo "4. View logs: journalctl --user -u pod-${POD_NAME}.service -f"
    echo "5. Access the API at: http://localhost:8080"
    echo
    warning "Remember to configure your firewall to allow access to ports 8080, 6379, and 8081"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi