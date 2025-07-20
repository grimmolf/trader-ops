#!/bin/bash
# Development container setup script for Trader Ops

set -e

echo "🚀 Setting up Trader Ops Development Environment..."

# Ensure we're in the workspace directory
cd /workspace

# Update PATH for UV
export PATH="$HOME/.cargo/bin:$PATH"

# Check if UV is available
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install Python dependencies with UV
echo "🐍 Installing Python dependencies with UV..."
if [ -f "pyproject.toml" ]; then
    uv sync --dev
    echo "✅ Python dependencies installed successfully"
else
    echo "⚠️ pyproject.toml not found - skipping Python dependencies"
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    npm ci
    echo "✅ Node.js dependencies installed successfully"
else
    echo "⚠️ package.json not found - skipping Node.js dependencies"
fi

# Set up development logging hooks
echo "📝 Setting up development logging..."
if [ -f "scripts/dev-logging/setup-hooks.sh" ]; then
    chmod +x scripts/dev-logging/setup-hooks.sh
    ./scripts/dev-logging/setup-hooks.sh
    echo "✅ Development logging hooks configured"
else
    echo "⚠️ Development logging setup script not found"
fi

# Install Playwright browsers if not already installed
echo "🎭 Setting up Playwright browsers..."
if command -v npx &> /dev/null; then
    npx playwright install chromium firefox webkit
    echo "✅ Playwright browsers installed"
fi

# Create development environment file if it doesn't exist
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✅ Development .env file created from example"
fi

# Set up development-friendly git configuration
echo "🔧 Configuring Git for development..."
git config --global --add safe.directory /workspace
git config --global init.defaultBranch main
git config --global pull.rebase false

# Create development directories
echo "📁 Creating development directories..."
mkdir -p logs
mkdir -p temp
mkdir -p build
mkdir -p dist

# Set up Redis for development (if needed)
echo "🗄️ Setting up Redis for development..."
if command -v redis-server &> /dev/null; then
    sudo service redis-server start || echo "Redis service not available"
fi

# Verify installation
echo "🔍 Verifying development environment..."

# Check Python setup
if command -v uv &> /dev/null; then
    echo "✅ UV: $(uv --version)"
    if [ -f "pyproject.toml" ]; then
        echo "✅ Python environment: $(uv run python --version 2>/dev/null || echo 'Not configured')"
    fi
else
    echo "❌ UV not found"
fi

# Check Node.js setup
if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
    echo "✅ npm: $(npm --version)"
else
    echo "❌ Node.js not found"
fi

# Check Playwright
if command -v npx &> /dev/null && npx playwright --version &> /dev/null; then
    echo "✅ Playwright: $(npx playwright --version)"
else
    echo "❌ Playwright not configured"
fi

# Display development commands
echo ""
echo "🎯 Development Environment Ready!"
echo ""
echo "📋 Available Commands:"
echo "  npm run dev          - Start development servers (frontend + backend)"
echo "  npm run dev:frontend - Start frontend development server only"
echo "  uv run python -m uvicorn src.backend.server:app --reload --port 8000"
echo "                       - Start backend development server only"
echo "  npm test             - Run all tests"
echo "  npm run test:e2e     - Run end-to-end tests"
echo "  uv run pytest       - Run Python tests"
echo "  npm run lint         - Run linting checks"
echo "  npm run type-check   - Run TypeScript type checking"
echo "  uv run ruff check src/ - Run Python linting"
echo ""
echo "🌐 Development Ports:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs (FastAPI auto-docs)"
echo ""
echo "📝 Development Tips:"
echo "  - Use 'git commit --no-verify' for quick WIP commits"
echo "  - Add '[skip-dev-log]' to commit messages for minor changes"
echo "  - Run './scripts/setup_uv.sh' if you need to reset the environment"
echo "  - Check 'docs/developer/' for development guides"
echo ""
echo "🚀 Happy Trading Platform Development!"
echo ""

# Make sure all scripts are executable
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/dev-logging/*.sh 2>/dev/null || true

# Final verification
if [ -f "pyproject.toml" ] && [ -f "package.json" ]; then
    echo "✅ Development environment setup completed successfully!"
    exit 0
else
    echo "⚠️ Some configuration files are missing - environment may not be fully functional"
    exit 1
fi