#!/bin/bash

# Trader Ops UV Setup Script
# This script sets up the development environment using UV

echo "🚀 Setting up Trader Ops with UV..."
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Check if installation was successful
    if ! command -v uv &> /dev/null; then
        echo "❌ UV installation failed. Please install manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   Or: pip install uv"
        exit 1
    fi
    
    echo "✅ UV installed successfully!"
else
    echo "✅ UV already installed ($(uv --version))"
fi

echo ""
echo "🐍 Setting up Python environment..."

# Create and sync the UV environment
uv sync --dev

echo ""
echo "📦 Installing Node.js dependencies..."
npm install

echo ""
echo "🔧 Setting up development logging..."
./scripts/dev-logging/setup-hooks.sh

echo ""
echo "✅ Setup complete! You can now:"
echo "   • Run development server: ./scripts/start_dev.sh"
echo "   • Run tests: uv run pytest"
echo "   • Run linting: uv run ruff check src/"
echo "   • Run type checking: uv run mypy src/"
echo ""
echo "📚 UV Commands Reference:"
echo "   • Install package: uv add <package>"
echo "   • Install dev package: uv add --dev <package>"
echo "   • Remove package: uv remove <package>"
echo "   • Run script: uv run <command>"
echo "   • Sync dependencies: uv sync"
echo "   • Show environment: uv pip list"
echo ""