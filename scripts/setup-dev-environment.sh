#!/bin/bash
# Developer Environment Setup Script
# Ensures consistent development environment for all contributors

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 TraderTerminal Developer Environment Setup"
echo "=========================================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check Python version
REQUIRED_PYTHON="3.11"
echo -e "\n${YELLOW}📦 Checking Python version...${NC}"

# Install required Python version if not present
uv python install $REQUIRED_PYTHON

# Get actual Python version
PYTHON_VERSION=$(uv run python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)

if [[ "$PYTHON_VERSION" != "$REQUIRED_PYTHON" ]]; then
    echo -e "${RED}❌ Python $REQUIRED_PYTHON required, found $PYTHON_VERSION${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python $PYTHON_VERSION OK${NC}"
fi

# Install dependencies
echo -e "\n${YELLOW}📦 Installing Python dependencies...${NC}"
uv sync --dev

echo -e "\n${YELLOW}📦 Installing Node.js dependencies...${NC}"
npm install

# Install pre-commit hooks
echo -e "\n${YELLOW}🔧 Installing pre-commit hooks...${NC}"
if ! command -v pre-commit &> /dev/null; then
    uv pip install pre-commit
fi

pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push

# Run initial validation
echo -e "\n${YELLOW}🧪 Running initial validation...${NC}"

# Check for common issues
echo "Checking for Pydantic v1 syntax..."
if grep -r "@validator\|class Config:" src/ --include="*.py" 2>/dev/null | head -5; then
    echo -e "${YELLOW}⚠️  Found Pydantic v1 syntax - run './scripts/fix-ci-issues.sh' to fix${NC}"
fi

echo "Checking for old pytest-asyncio syntax..."
if grep -r "@pytest_asyncio\.async_test" tests/ --include="*.py" 2>/dev/null | head -5; then
    echo -e "${YELLOW}⚠️  Found old pytest-asyncio syntax - run './scripts/fix-ci-issues.sh' to fix${NC}"
fi

# Run compatibility check
echo -e "\n${YELLOW}🔍 Running compatibility check...${NC}"
if [ -f "scripts/check-compatibility.py" ]; then
    uv run python scripts/check-compatibility.py || true
fi

# Create local development configuration if needed
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo -e "\n${YELLOW}📝 Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file - please update with your API keys${NC}"
fi

# Run pre-commit on all files (optional, can be slow)
read -p "Run pre-commit checks on all files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}🧹 Running pre-commit on all files...${NC}"
    pre-commit run --all-files || true
fi

# Final instructions
echo -e "\n${GREEN}✅ Development environment setup complete!${NC}"
echo -e "\n📋 Next steps:"
echo "1. Update .env with your API credentials"
echo "2. Run 'npm run dev' to start development"
echo "3. Run 'npm test' to verify everything works"
echo -e "\n💡 Tips:"
echo "- Pre-commit hooks will run automatically on git commit"
echo "- Run 'pre-commit run --all-files' to check all files"
echo "- Run './scripts/fix-ci-issues.sh' if you encounter CI/CD errors"
echo "- Python version is locked to $REQUIRED_PYTHON" 