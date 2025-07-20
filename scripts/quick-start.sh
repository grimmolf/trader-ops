#!/bin/bash
# Trader Ops Quick Start - One Command Setup & Launch
# This script handles complete environment setup and starts the application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Header
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   🚀 TRADER OPS QUICK START 🚀                ║"
echo "║              One Command Setup & Launch with UV              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "package.json" ]; then
    print_error "Not in Trader Ops project directory. Please run from project root."
    exit 1
fi

# Step 1: UV Installation & Verification
print_step "Checking UV installation..."
if ! command -v uv &> /dev/null; then
    print_warning "UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verify installation
    if ! command -v uv &> /dev/null; then
        print_error "UV installation failed. Please install manually:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  Then restart your terminal and try again."
        exit 1
    fi
    print_success "UV installed successfully!"
else
    print_success "UV already installed ($(uv --version))"
fi

# Step 2: Node.js Verification
print_step "Checking Node.js installation..."
if ! command -v npm &> /dev/null; then
    print_error "Node.js/npm not found. Please install Node.js 18+ first:"
    echo "  macOS: brew install node"
    echo "  Ubuntu: sudo apt install nodejs npm"
    echo "  Windows: Download from nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version $NODE_VERSION detected. Trader Ops requires Node.js 18+."
    exit 1
fi
print_success "Node.js $(node --version) detected"

# Step 3: Environment Configuration
print_step "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created"
    print_warning "Remember to update .env with your API keys before trading!"
else
    print_success ".env file already exists"
fi

# Step 4: Python Environment Setup with UV
print_step "Setting up Python environment with UV (this is FAST!)..."
echo "⚡ UV will resolve dependencies in milliseconds..."

# Sync Python dependencies (development mode)
time uv sync --dev
print_success "Python environment ready in record time!"

# Step 5: Node.js Dependencies
print_step "Installing Node.js dependencies..."
if [ ! -d "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
    npm install
    print_success "Node.js dependencies installed"
else
    print_success "Node.js dependencies already up to date"
fi

# Step 6: Development Logging Setup
print_step "Setting up development logging system..."
if [ -f "scripts/dev-logging/setup-hooks.sh" ]; then
    ./scripts/dev-logging/setup-hooks.sh
    print_success "Development logging configured"
else
    print_warning "Development logging setup script not found (skipping)"
fi

# Step 7: Environment Validation
print_step "Validating environment setup..."

# Check Python packages
if uv run python -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    print_success "Python dependencies validated"
else
    print_error "Python dependencies validation failed"
    exit 1
fi

# Check if build compiles
print_info "Validating TypeScript compilation..."
npm run build:main > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "TypeScript compilation validated"
else
    print_warning "TypeScript compilation issues detected (may still work)"
fi

# Step 8: Launch Application
echo ""
print_step "🚀 Launching Trader Ops Dashboard..."
echo ""

# Function to cleanup processes on exit
cleanup() {
    echo ""
    print_info "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    if [ ! -z "$ELECTRON_PID" ]; then
        kill $ELECTRON_PID 2>/dev/null
    fi
    print_success "All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start Backend (FastAPI with UV)
print_info "Starting FastAPI backend server..."
uv run python -m uvicorn src.backend.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Verify backend is running
if ps -p $BACKEND_PID > /dev/null; then
    print_success "Backend server started (PID: $BACKEND_PID)"
    print_info "  API: http://localhost:8000"
    print_info "  Docs: http://localhost:8000/docs"
    print_info "  WebSocket: ws://localhost:8000/stream"
else
    print_error "Backend server failed to start"
    exit 1
fi

# Start Frontend (Vite dev server)
print_info "Starting Vite development server..."
npm run dev:renderer &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 2

if ps -p $FRONTEND_PID > /dev/null; then
    print_success "Frontend server started (PID: $FRONTEND_PID)"
    print_info "  Frontend: http://localhost:5173"
else
    print_error "Frontend server failed to start"
    cleanup
    exit 1
fi

# Start Electron App
print_info "Starting Electron application..."
npm run electron:dev &
ELECTRON_PID=$!

sleep 2

if ps -p $ELECTRON_PID > /dev/null; then
    print_success "Electron app started (PID: $ELECTRON_PID)"
else
    print_error "Electron app failed to start"
    cleanup
    exit 1
fi

# Success message
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 🎉 TRADER OPS IS READY! 🎉                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_success "All services are running:"
echo "  📊 Frontend:  http://localhost:5173"
echo "  ⚡ Backend:   http://localhost:8000"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo "  🖥️  Desktop:   Electron window should be open"
echo ""
print_info "Development tips:"
echo "  • Edit .env file to configure API keys"
echo "  • Backend auto-reloads on Python changes"
echo "  • Frontend auto-reloads on Vue/TS changes"
echo "  • Logs are automatically tracked with git hooks"
echo ""
print_warning "Press Ctrl+C to stop all services"

# Keep script running and wait for user interrupt
wait