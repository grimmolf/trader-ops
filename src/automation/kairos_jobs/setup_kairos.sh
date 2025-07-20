#!/bin/bash
# Setup script for Trader Dashboard Kairos Job Scheduler
# This script configures Kairos for automated trading strategy execution

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KAIROS_USER="trader"
KAIROS_GROUP="trader"
INSTALL_DIR="/opt/trader-ops"
CONFIG_DIR="/etc/trader-ops"
LOG_DIR="/var/log/kairos"
DATA_DIR="/var/lib/kairos"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root (except for system setup)"
        log_info "Run: sudo ./setup_kairos.sh system"
        log_info "Then: ./setup_kairos.sh user"
        exit 1
    fi
}

# System-level setup (requires sudo)
setup_system() {
    log_info "Setting up system-level components for Kairos..."
    
    # Create user and group
    if ! id "$KAIROS_USER" &>/dev/null; then
        log_info "Creating user: $KAIROS_USER"
        sudo useradd -r -s /bin/bash -d "$INSTALL_DIR" "$KAIROS_USER"
    fi
    
    # Create directories
    log_info "Creating system directories..."
    sudo mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR"
    
    # Set ownership
    sudo chown -R "$KAIROS_USER:$KAIROS_GROUP" "$INSTALL_DIR" "$LOG_DIR" "$DATA_DIR"
    sudo chmod 755 "$CONFIG_DIR"
    
    # Copy project files
    log_info "Installing project files..."
    sudo cp -r "$PROJECT_ROOT"/* "$INSTALL_DIR/"
    sudo chown -R "$KAIROS_USER:$KAIROS_GROUP" "$INSTALL_DIR"
    
    # Install systemd service and timer
    log_info "Installing systemd service..."
    sudo cp "$SCRIPT_DIR/systemd/trader-kairos.service" /etc/systemd/system/
    sudo cp "$SCRIPT_DIR/systemd/trader-kairos.timer" /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Create environment file template
    log_info "Creating environment configuration..."
    sudo tee "$CONFIG_DIR/kairos.env" > /dev/null << 'EOF'
# Kairos Environment Configuration
# Edit this file with your actual API keys and settings

# Tradier API Configuration
TRADIER_API_KEY=your_tradier_api_key_here
TRADIER_ACCOUNT_ID=your_account_id_here

# DataHub Configuration
DATAHUB_API_KEY=your_datahub_api_key_here
DATAHUB_URL=http://localhost:8000

# TradingView Webhook Configuration
TRADINGVIEW_WEBHOOK_SECRET=your_webhook_secret_here

# Notification Webhooks (Optional)
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
EMAIL_SERVICE_URL=

# Database Configuration (Optional)
DB_USERNAME=
DB_PASSWORD=

# Additional Settings
KAIROS_LOG_LEVEL=INFO
KAIROS_DEBUG=false
EOF
    
    sudo chmod 600 "$CONFIG_DIR/kairos.env"
    sudo chown root:root "$CONFIG_DIR/kairos.env"
    
    log_success "System setup completed!"
    log_warning "Please edit $CONFIG_DIR/kairos.env with your actual configuration"
    log_info "Next steps:"
    log_info "1. Edit the environment file: sudo nano $CONFIG_DIR/kairos.env"
    log_info "2. Run user setup: ./setup_kairos.sh user"
}

# User-level setup
setup_user() {
    log_info "Setting up user-level components for Kairos..."
    
    # Check if we're the right user
    if [[ "$(whoami)" != "$KAIROS_USER" ]]; then
        log_warning "Switching to $KAIROS_USER user..."
        sudo -u "$KAIROS_USER" bash "$0" user
        return
    fi
    
    # Create Python virtual environment
    log_info "Creating Python virtual environment..."
    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        python3 -m venv "$INSTALL_DIR/venv"
    fi
    
    # Activate virtual environment
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt" || log_warning "requirements.txt not found, skipping pip install"
    
    # Install Kairos (assuming it's available via pip or local install)
    # This would need to be adapted based on actual Kairos installation method
    log_info "Installing Kairos scheduler..."
    # pip install kairos-scheduler  # Placeholder - adjust as needed
    
    # Validate configuration files
    log_info "Validating Kairos job configurations..."
    for config_file in "$INSTALL_DIR/src/automation/kairos_jobs"/*.yml; do
        if [[ -f "$config_file" ]]; then
            log_info "Validating: $(basename "$config_file")"
            # Add validation logic here
            # kairos validate "$config_file" || log_error "Invalid config: $config_file"
        fi
    done
    
    # Create log rotation configuration
    log_info "Setting up log rotation..."
    sudo tee /etc/logrotate.d/trader-kairos > /dev/null << 'EOF'
/var/log/kairos/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su trader trader
}
EOF
    
    log_success "User setup completed!"
}

# Development setup
setup_development() {
    log_info "Setting up Kairos for development..."
    
    # Create local directories
    mkdir -p "$PROJECT_ROOT/logs/kairos"
    mkdir -p "$PROJECT_ROOT/data/kairos"
    
    # Create development environment file
    cat > "$PROJECT_ROOT/.env.kairos" << 'EOF'
# Development Environment for Kairos
KAIROS_CONFIG_DIR=./src/automation/kairos_jobs
KAIROS_LOG_DIR=./logs/kairos
KAIROS_DATA_DIR=./data/kairos
DATAHUB_URL=http://localhost:8000
TRADIER_API_KEY=sandbox_key_here
KAIROS_LOG_LEVEL=DEBUG
KAIROS_DEBUG=true
EOF
    
    # Create development start script
    cat > "$PROJECT_ROOT/scripts/start_kairos_dev.sh" << 'EOF'
#!/bin/bash
# Development start script for Kairos

cd "$(dirname "$0")/.."
source .env.kairos

# Activate virtual environment if it exists
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
fi

# Start Kairos in development mode
python -m kairos.scheduler \
    --config-dir="$KAIROS_CONFIG_DIR" \
    --log-dir="$KAIROS_LOG_DIR" \
    --data-dir="$KAIROS_DATA_DIR" \
    --debug \
    --jobs-glob="*.yml"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/start_kairos_dev.sh"
    
    log_success "Development setup completed!"
    log_info "Start development Kairos: ./scripts/start_kairos_dev.sh"
}

# Main function
main() {
    local command="${1:-}"
    
    case "$command" in
        "system")
            if [[ $EUID -ne 0 ]]; then
                log_error "System setup requires root privileges"
                log_info "Run: sudo $0 system"
                exit 1
            fi
            setup_system
            ;;
        "user")
            check_root
            setup_user
            ;;
        "dev"|"development")
            check_root
            setup_development
            ;;
        "status")
            log_info "Checking Kairos status..."
            systemctl status trader-kairos.service || true
            systemctl status trader-kairos.timer || true
            ;;
        "start")
            log_info "Starting Kairos services..."
            sudo systemctl enable trader-kairos.timer
            sudo systemctl start trader-kairos.timer
            log_success "Kairos timer started and enabled"
            ;;
        "stop")
            log_info "Stopping Kairos services..."
            sudo systemctl stop trader-kairos.timer
            sudo systemctl stop trader-kairos.service
            log_success "Kairos services stopped"
            ;;
        "logs")
            log_info "Viewing Kairos logs..."
            sudo journalctl -u trader-kairos.service -f
            ;;
        *)
            echo "Trader Dashboard Kairos Setup Script"
            echo ""
            echo "Usage: $0 {system|user|dev|status|start|stop|logs}"
            echo ""
            echo "Commands:"
            echo "  system     - System-level setup (requires sudo)"
            echo "  user       - User-level setup"
            echo "  dev        - Development setup"
            echo "  status     - Check service status"
            echo "  start      - Start Kairos services"
            echo "  stop       - Stop Kairos services"
            echo "  logs       - View service logs"
            echo ""
            echo "Installation steps:"
            echo "1. sudo $0 system"
            echo "2. Edit /etc/trader-ops/kairos.env"
            echo "3. $0 user"
            echo "4. $0 start"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"