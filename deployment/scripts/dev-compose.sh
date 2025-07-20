#!/bin/bash
# TraderTerminal Development Compose Management Script
# Simplifies container management for development workflows

set -euo pipefail

# Configuration
COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../compose" && pwd)"
PROJECT_ROOT="$(cd "${COMPOSE_DIR}/../.." && pwd)"
PROJECT_NAME="traderterminal"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $1${NC}"
    exit 1
}

# Check if Docker/Podman is available
check_container_runtime() {
    if command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        error "No container runtime found. Install Docker or Podman with compose support."
    fi
    
    log "Using container runtime: ${COMPOSE_CMD}"
}

# Build development images
build() {
    log "Building development images..."
    cd "${COMPOSE_DIR}"
    
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" build --parallel
    
    success "Development images built"
}

# Start development environment
start() {
    log "Starting development environment..."
    cd "${COMPOSE_DIR}"
    
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check service status
    check_status
    
    success "Development environment started"
    echo
    echo "Services available at:"
    echo "  • DataHub API: http://localhost:8080"
    echo "  • Redis: localhost:6379"
    echo "  • Kairos API: http://localhost:8081"
    echo
    echo "Useful commands:"
    echo "  • View logs: $0 logs [service]"
    echo "  • Check status: $0 status"
    echo "  • Stop: $0 stop"
    echo "  • Restart: $0 restart"
}

# Stop development environment
stop() {
    log "Stopping development environment..."
    cd "${COMPOSE_DIR}"
    
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" down
    
    success "Development environment stopped"
}

# Restart development environment
restart() {
    log "Restarting development environment..."
    stop
    start
}

# Show logs
logs() {
    cd "${COMPOSE_DIR}"
    
    if [[ $# -gt 1 ]]; then
        # Show logs for specific service
        local service="$2"
        log "Showing logs for service: ${service}"
        ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" logs -f "${service}"
    else
        # Show all logs
        log "Showing all service logs..."
        ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" logs -f
    fi
}

# Check service status
status() {
    cd "${COMPOSE_DIR}"
    
    echo "=== Container Status ==="
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" ps
    
    echo
    echo "=== Service Health Checks ==="
    
    # Check DataHub
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        success "DataHub API is healthy"
    else
        warning "DataHub API is not responding"
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null && redis-cli -p 6379 ping > /dev/null 2>&1; then
        success "Redis is healthy"
    else
        warning "Redis is not responding (redis-cli needed for check)"
    fi
    
    # Check Kairos
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        success "Kairos API is healthy"
    else
        warning "Kairos API is not responding"
    fi
}

# Clean up development environment
clean() {
    log "Cleaning up development environment..."
    cd "${COMPOSE_DIR}"
    
    # Stop and remove containers
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" down -v --remove-orphans
    
    # Remove images
    log "Removing development images..."
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" down --rmi all || true
    
    success "Development environment cleaned"
}

# Execute command in container
exec_cmd() {
    if [[ $# -lt 3 ]]; then
        error "Usage: $0 exec <service> <command>"
    fi
    
    local service="$2"
    local cmd="${@:3}"
    
    cd "${COMPOSE_DIR}"
    ${COMPOSE_CMD} -f docker-compose.dev.yml -p "${PROJECT_NAME}-dev" exec "${service}" ${cmd}
}

# Show shell access options
shell() {
    echo "Available services for shell access:"
    echo "  • datahub: Main backend service"
    echo "  • redis: Redis cache"
    echo "  • kairos: Automation service"
    echo "  • dev-utils: Utility container"
    echo
    echo "Usage examples:"
    echo "  $0 exec datahub bash"
    echo "  $0 exec redis redis-cli"
    echo "  $0 exec kairos python -c 'import sys; print(sys.path)'"
}

# Show help
help() {
    echo "TraderTerminal Development Compose Management"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  build                 Build development images"
    echo "  start                 Start development environment"
    echo "  stop                  Stop development environment"
    echo "  restart               Restart development environment"
    echo "  status                Show service status and health"
    echo "  logs [service]        Show logs (all or specific service)"
    echo "  exec <service> <cmd>  Execute command in service container"
    echo "  shell                 Show shell access help"
    echo "  clean                 Stop and remove everything"
    echo "  help                  Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start              # Start all services"
    echo "  $0 logs datahub       # Show DataHub logs"
    echo "  $0 exec datahub bash  # Get shell in DataHub container"
    echo "  $0 status             # Check service health"
    echo
}

# Check container runtime availability
check_status() {
    status
}

# Main function
main() {
    check_container_runtime
    
    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs "$@"
            ;;
        status)
            status
            ;;
        exec)
            exec_cmd "$@"
            ;;
        shell)
            shell
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            help
            ;;
        *)
            error "Unknown command: $1. Use '$0 help' for usage information."
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi