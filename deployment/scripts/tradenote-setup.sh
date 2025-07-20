#!/bin/bash
# TradeNote Integration Setup Script for TraderTerminal
# Sets up TradeNote containerized trade journal with MongoDB

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_DIR="$PROJECT_ROOT/deployment/compose"
SECRETS_DIR="/etc/traderterminal/secrets"

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for production setup
check_root() {
    if [[ $EUID -eq 0 && "$ENVIRONMENT" == "production" ]]; then
        print_info "Running as root for production setup"
    elif [[ $EUID -eq 0 && "$ENVIRONMENT" == "development" ]]; then
        print_warning "Running as root for development setup (not recommended)"
    fi
}

# Generate secure random strings
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Setup development environment
setup_development() {
    print_info "Setting up TradeNote for development environment"
    
    cd "$COMPOSE_DIR"
    
    # Start TradeNote services
    print_info "Starting TradeNote services..."
    docker compose -f docker-compose.dev.yml up -d tradenote-mongo tradenote
    
    # Wait for services to be ready
    print_info "Waiting for TradeNote services to be ready..."
    sleep 30
    
    # Check service health
    print_info "Checking service health..."
    docker compose -f docker-compose.dev.yml ps
    
    # Display access information
    print_success "TradeNote development setup complete!"
    echo ""
    echo "Services running:"
    echo "  • MongoDB: http://localhost:27017"
    echo "  • TradeNote: http://localhost:8082"
    echo ""
    echo "Development credentials:"
    echo "  • MongoDB User: tradenote"
    echo "  • MongoDB Password: tradenote123"
    echo "  • App ID: traderterminal_dev_123"
    echo "  • Master Key: traderterminal_master_dev_456"
    echo ""
    echo "To stop services: docker compose -f docker-compose.dev.yml down"
}

# Setup production environment
setup_production() {
    print_info "Setting up TradeNote for production environment"
    
    # Create secrets directory
    if [[ ! -d "$SECRETS_DIR" ]]; then
        print_info "Creating secrets directory: $SECRETS_DIR"
        sudo mkdir -p "$SECRETS_DIR"
        sudo chmod 700 "$SECRETS_DIR"
    fi
    
    # Generate and store secrets
    print_info "Generating secure credentials..."
    
    MONGO_USER="tradenote"
    MONGO_PASSWORD=$(generate_secret)
    APP_ID="traderterminal_$(generate_secret | cut -c1-12)"
    MASTER_KEY=$(generate_secret)
    MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@tradenote-mongo:27017/tradenote?authSource=admin"
    
    # Write secrets to files
    echo "$MONGO_USER" | sudo tee "$SECRETS_DIR/tradenote_mongo_user.txt" > /dev/null
    echo "$MONGO_PASSWORD" | sudo tee "$SECRETS_DIR/tradenote_mongo_password.txt" > /dev/null
    echo "$MONGO_URI" | sudo tee "$SECRETS_DIR/tradenote_mongo_uri.txt" > /dev/null
    echo "$APP_ID" | sudo tee "$SECRETS_DIR/tradenote_app_id.txt" > /dev/null
    echo "$MASTER_KEY" | sudo tee "$SECRETS_DIR/tradenote_master_key.txt" > /dev/null
    
    # Set proper permissions
    sudo chmod 600 "$SECRETS_DIR"/tradenote_*.txt
    sudo chown 1001:1001 "$SECRETS_DIR"/tradenote_*.txt
    
    cd "$COMPOSE_DIR"
    
    # Start TradeNote services
    print_info "Starting TradeNote services..."
    docker compose -f docker-compose.prod.yml up -d tradenote-mongo tradenote
    
    # Wait for services to be ready
    print_info "Waiting for TradeNote services to be ready..."
    sleep 60
    
    # Check service health
    print_info "Checking service health..."
    docker compose -f docker-compose.prod.yml ps
    
    # Display access information
    print_success "TradeNote production setup complete!"
    echo ""
    echo "Services running:"
    echo "  • MongoDB: localhost:27017 (localhost only)"
    echo "  • TradeNote: http://localhost:8082 (localhost only)"
    echo ""
    echo "Production credentials stored in: $SECRETS_DIR"
    echo "  • tradenote_mongo_user.txt"
    echo "  • tradenote_mongo_password.txt"
    echo "  • tradenote_mongo_uri.txt"
    echo "  • tradenote_app_id.txt"
    echo "  • tradenote_master_key.txt"
    echo ""
    echo "To stop services: docker compose -f docker-compose.prod.yml down"
}

# Stop services
stop_services() {
    print_info "Stopping TradeNote services..."
    
    cd "$COMPOSE_DIR"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        docker compose -f docker-compose.dev.yml down
    else
        docker compose -f docker-compose.prod.yml down
    fi
    
    print_success "TradeNote services stopped"
}

# View logs
view_logs() {
    cd "$COMPOSE_DIR"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        docker compose -f docker-compose.dev.yml logs -f tradenote tradenote-mongo
    else
        docker compose -f docker-compose.prod.yml logs -f tradenote tradenote-mongo
    fi
}

# Show status
show_status() {
    cd "$COMPOSE_DIR"
    
    print_info "TradeNote service status:"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        docker compose -f docker-compose.dev.yml ps
    else
        docker compose -f docker-compose.prod.yml ps
    fi
}

# Show usage
show_usage() {
    echo "TradeNote Integration Setup Script"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [COMMAND]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  development  Setup for development with plain text credentials"
    echo "  production   Setup for production with secure secrets"
    echo ""
    echo "COMMANDS:"
    echo "  setup        Setup and start TradeNote services"
    echo "  stop         Stop TradeNote services"
    echo "  logs         View service logs"
    echo "  status       Show service status"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 development setup"
    echo "  $0 production setup"
    echo "  $0 development stop"
    echo "  $0 production logs"
}

# Main script
main() {
    if [[ $# -lt 2 ]]; then
        show_usage
        exit 1
    fi
    
    ENVIRONMENT="$1"
    COMMAND="$2"
    
    # Validate environment
    if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
        print_error "Invalid environment: $ENVIRONMENT"
        show_usage
        exit 1
    fi
    
    # Check prerequisites
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is required but not available"
        exit 1
    fi
    
    check_root
    
    # Execute command
    case "$COMMAND" in
        setup)
            if [[ "$ENVIRONMENT" == "development" ]]; then
                setup_development
            else
                setup_production
            fi
            ;;
        stop)
            stop_services
            ;;
        logs)
            view_logs
            ;;
        status)
            show_status
            ;;
        help)
            show_usage
            ;;
        *)
            print_error "Invalid command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"