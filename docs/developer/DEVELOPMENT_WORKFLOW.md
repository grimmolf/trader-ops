# Development Workflow Guide

Complete guide for developing, testing, and maintaining the Trader Ops project, including the automated development logging system.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Git Workflow](#git-workflow)
- [Development Logging System](#development-logging-system)
- [Code Quality](#code-quality)
- [Testing Strategy](#testing-strategy)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

## ⚡ Quick Start

### Initial Setup
```bash
# 1. Clone and setup project
git clone https://github.com/your-org/trader-ops.git
cd trader-ops

# 2. Install dependencies
poetry install                # Python dependencies
npm install                   # Node.js dependencies

# 3. Set up development logging
./scripts/dev-logging/setup-hooks.sh

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start development servers
npm run dev                   # Starts both frontend and backend
```

### Daily Development
```bash
# Start development session
npm run dev

# Run tests before committing
npm test
poetry run pytest

# Commit with automatic logging
git add .
git commit -m "Your descriptive commit message"
# Development logging prompt will appear

# Push changes
git push origin feature-branch
```

## 🛠️ Development Environment

### Required Tools
- **Python 3.11+** with Poetry for dependency management
- **Node.js 18+** with npm for frontend tooling
- **Git** with development hooks enabled
- **VS Code** (recommended) with recommended extensions

### VS Code Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "vue.volar",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

### Environment Configuration
```bash
# Development environment variables (.env)
PYTHON_ENV=development
LOG_LEVEL=DEBUG
TRADIER_API_KEY=your_sandbox_key
TRADINGVIEW_MODE=local

# Development logging configuration
DEV_LOGGING_ENABLED=true
DEV_LOGGING_MODE=pre-commit
DEV_LOGGING_SKIP_PROMPT=false
```

### Development Servers
```bash
# Option 1: Integrated development (recommended)
npm run dev                    # Starts both servers in parallel

# Option 2: Manual startup
# Terminal 1: Backend
poetry run uvicorn src.backend.server:app --reload --port 8000

# Terminal 2: Frontend
npm run electron:dev

# Terminal 3: Type checking (optional)
npm run type-check --watch
```

## 🔀 Git Workflow

### Branch Strategy
```
main
├── feature/tradingview-integration
├── feature/portfolio-tracking
├── bugfix/websocket-connection
└── release/v1.1.0
```

### Branch Naming Convention
- **Features**: `feature/short-description`
- **Bug Fixes**: `bugfix/issue-description`
- **Releases**: `release/v1.x.x`
- **Hotfixes**: `hotfix/critical-issue`

### Standard Workflow
```bash
# 1. Create feature branch
git checkout main
git pull origin main
git checkout -b feature/new-feature

# 2. Make changes with regular commits
git add .
git commit -m "Add initial feature structure"
# Development logging prompt appears

# 3. Push and create PR
git push -u origin feature/new-feature
gh pr create --title "Add new feature" --body "Description"

# 4. After PR approval
git checkout main
git pull origin main
git branch -d feature/new-feature
```

### Commit Message Convention
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/updates
- `chore`: Maintenance tasks

**Examples**:
```bash
feat(api): add real-time quote WebSocket endpoint
fix(frontend): resolve TradingView widget authentication issue
docs(readme): update installation instructions
```

## 📝 Development Logging System

### Overview
The automated development logging system captures comprehensive context for every development session, enabling perfect reproducibility and knowledge sharing.

### System Components
```
scripts/dev-logging/
├── setup-hooks.sh           # Initial setup script
├── log-prompt.py            # Interactive logging script
├── manage-logs.py           # Log management utilities
└── templates/               # Structured templates
    ├── feature-template.json
    ├── bugfix-template.json
    └── refactor-template.json
```

### Git Hooks Integration
```bash
# Automatic setup
./scripts/dev-logging/setup-hooks.sh

# Manual hook configuration
git config core.hooksPath .git/hooks
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-commit
```

### Hook Behavior
- **Pre-commit**: Prompts for development log before commit
- **Post-commit**: Optional post-commit logging (configurable)
- **Bypass**: Use `[skip-dev-log]` in commit message to skip
- **Emergency**: Use `git commit --no-verify` to bypass all hooks

### Development Log Structure
Each log captures:

#### Session Context
- Primary objective and goals
- Background and motivation
- Scope and limitations

#### Technical Implementation
- Approach and methodology
- Key technical decisions and rationale
- Challenges encountered and solutions

#### Implementation Details
- Specific files modified
- Dependencies added/removed
- Configuration changes
- Testing approach and validation

#### Quality Assurance
- How implementation was validated
- Performance considerations
- Security implications
- Edge cases considered

#### Reproducibility Information
- Development environment details
- Prerequisites and setup steps
- Exact commands executed
- External resources referenced

### Log Management
```bash
# List recent logs
python scripts/dev-logging/manage-logs.py list --limit 10

# Search logs by content
python scripts/dev-logging/manage-logs.py search "WebSocket"

# Organize logs by date/feature
python scripts/dev-logging/manage-logs.py organize --execute

# Generate searchable index
python scripts/dev-logging/manage-logs.py index

# View statistics
python scripts/dev-logging/manage-logs.py stats
```

### Log Storage Structure
```
docs/development-logs/
├── index.md                    # Chronological index
├── index.json                  # Machine-readable index
├── 2024/                      # Yearly organization
│   ├── 01-january/
│   └── 02-february/
├── by-feature/                # Feature-based organization
│   ├── tradingview-integration/
│   └── real-time-data/
└── by-type/                   # Type-based organization
    ├── features/
    ├── bugfixes/
    └── refactoring/
```

### Configuration Options
```bash
# .dev-logging-config
DEV_LOGGING_ENABLED=true           # Enable/disable logging
DEV_LOGGING_MODE=pre-commit        # pre-commit or post-commit
DEV_LOGGING_SKIP_PROMPT=false      # Auto-accept prompts
DEV_LOGGING_AUTO_ORGANIZE=true     # Auto-organize logs
DEV_LOGGING_CREATE_INDEX=true      # Auto-update index
```

## 🧪 Code Quality

### Python Code Quality
```bash
# Linting with Ruff
poetry run ruff check src/
poetry run ruff check src/ --fix     # Auto-fix issues

# Type checking with mypy
poetry run mypy src/

# Code formatting with Black
poetry run black src/
poetry run black src/ --check       # Check without changes

# Import sorting with isort
poetry run isort src/
poetry run isort src/ --check-only

# Combined quality check
npm run lint:python                 # Runs all Python checks
```

### TypeScript/JavaScript Quality
```bash
# ESLint for linting
npm run lint
npm run lint:fix                    # Auto-fix issues

# TypeScript type checking
npm run type-check
npm run type-check:watch           # Watch mode

# Prettier for formatting
npm run format
npm run format:check               # Check without changes

# Combined quality check
npm run lint:frontend              # Runs all frontend checks
```

### Pre-commit Quality Gates
```bash
# Automatic quality checks before commit
git add .
git commit -m "Your message"
# Automatically runs:
# 1. Python linting (Ruff)
# 2. TypeScript checking
# 3. Test suite
# 4. Development logging prompt
```

### VS Code Integration
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll.eslint": true
  }
}
```

## 🧪 Testing Strategy

### Test Organization
```
tests/
├── unit/                      # Fast, isolated tests
│   ├── test_models.py         # Pydantic model validation
│   ├── test_datahub.py        # API endpoint testing
│   └── test_tradier.py        # External API integration
├── integration/               # Component interaction tests
│   ├── test_websocket.py      # WebSocket functionality
│   └── test_udf_protocol.py   # TradingView UDF
└── e2e/                      # End-to-end application tests
    ├── test_app_launch.py     # Application startup
    ├── test_symbol_search.py  # User workflow testing
    └── test_data_streaming.py # Real-time data flow
```

### Running Tests
```bash
# All tests
npm test                       # Frontend + Backend tests

# Python backend tests
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
poetry run pytest tests/ --cov=src  # With coverage

# Frontend tests
npm run test:unit             # Vue component tests
npm run test:e2e              # Electron app tests

# Specific test categories
npm run test:api              # API endpoint tests
npm run test:websocket        # WebSocket tests
npm run test:tradingview      # TradingView integration
```

### Test Development Guidelines
```python
# Example unit test structure
import pytest
from src.backend.models import Quote

class TestQuote:
    def test_quote_validation(self):
        """Test quote model validation."""
        quote = Quote(
            symbol="AAPL",
            bid=150.00,
            ask=150.02,
            last=150.01,
            volume=1000,
            timestamp=1705751400
        )
        assert quote.symbol == "AAPL"
        assert quote.spread == 0.02

    @pytest.mark.asyncio
    async def test_quote_websocket_broadcast(self):
        """Test WebSocket quote broadcasting."""
        # Test implementation
        pass
```

### Mocking and Test Data
```python
# Fixture for test data
@pytest.fixture
def sample_quote():
    return {
        "symbol": "AAPL",
        "last": 150.00,
        "volume": 1000000,
        "timestamp": 1705751400
    }

# Mock external APIs
@pytest.fixture
def mock_tradier_api(monkeypatch):
    def mock_get_quotes(*args, **kwargs):
        return {"quotes": {"quote": sample_quote()}}
    
    monkeypatch.setattr("src.backend.feeds.tradier.get_quotes", mock_get_quotes)
```

### Continuous Testing
```bash
# Watch mode for development
npm run test:watch            # Frontend tests in watch mode
poetry run pytest-watch      # Backend tests in watch mode

# Performance testing
npm run test:performance      # Load testing
poetry run pytest tests/ --benchmark-only  # Benchmark tests
```

## 🚀 Release Process

### Version Management
```bash
# Update version numbers
poetry version patch          # 1.0.0 → 1.0.1
npm version patch            # Update package.json

# Update version in source code
# Update version in pyproject.toml, package.json, and __init__.py
```

### Pre-release Checklist
- [ ] All tests passing (`npm test`)
- [ ] Code quality checks pass (`npm run lint`)
- [ ] Documentation updated
- [ ] Version numbers updated
- [ ] CHANGELOG.md updated
- [ ] Development logs complete

### Build Process
```bash
# Build backend package
poetry build                 # Creates dist/ with wheel and source

# Build frontend application
npm run build               # Web build
npm run electron:build     # Desktop app build

# Build for specific platforms
npm run electron:build:mac  # macOS
npm run electron:build:win  # Windows
npm run electron:build:linux # Linux
```

### Release Workflow
```bash
# 1. Create release branch
git checkout -b release/v1.1.0

# 2. Update version and documentation
poetry version minor
npm version minor
# Update CHANGELOG.md

# 3. Final testing
npm test
npm run build

# 4. Commit and tag
git commit -m "chore: prepare v1.1.0 release"
git tag v1.1.0

# 5. Push and create release
git push origin release/v1.1.0
git push origin v1.1.0
gh release create v1.1.0 --title "v1.1.0" --notes-file CHANGELOG.md

# 6. Merge to main
git checkout main
git merge release/v1.1.0
git push origin main
```

### Distribution
```bash
# Automatic distribution via GitHub Actions
# - Creates GitHub Release
# - Uploads built artifacts
# - Publishes to npm registry (if applicable)
# - Updates documentation site
```

## 🔧 Troubleshooting

### Common Development Issues

#### Backend Issues
```bash
# Poetry dependency conflicts
poetry lock --no-update
poetry install

# Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Database connection issues
poetry run python -c "from src.backend.config import settings; print(settings)"
```

#### Frontend Issues
```bash
# Node modules issues
rm -rf node_modules package-lock.json
npm install

# TypeScript compilation errors
npm run type-check
rm -rf build/ && npm run build

# Electron issues
npm run electron:rebuild
```

#### Development Logging Issues
```bash
# Hooks not triggering
./scripts/dev-logging/setup-hooks.sh
chmod +x .git/hooks/pre-commit

# Logging script errors
python scripts/dev-logging/log-prompt.py --skip
```

### Performance Optimization

#### Backend Performance
```python
# Profile API endpoints
poetry run python -m cProfile -o profile.stats src/backend/server.py

# Memory usage monitoring
poetry run python -m memory_profiler src/backend/server.py
```

#### Frontend Performance
```bash
# Bundle analysis
npm run analyze
npm run build -- --analyze

# Memory leaks
npm run electron:dev -- --inspect
# Use Chrome DevTools for memory profiling
```

### Debugging Tools

#### Python Debugging
```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Debug with VS Code
# Add launch configuration for FastAPI server
```

#### JavaScript Debugging
```javascript
// Electron main process debugging
console.log('Debug info:', data);

// Renderer process debugging (Vue DevTools available)
debugger;
```

#### Network Debugging
```bash
# Monitor WebSocket connections
npm run dev:debug           # Enables debug mode with detailed logging

# API request debugging
curl -X GET "http://localhost:8000/quotes/AAPL" -H "accept: application/json"
```

## 📚 Additional Resources

### Documentation
- [API Reference](../api/README.md) - Complete API documentation
- [TradingView Integration](../user/TRADINGVIEW_INTEGRATION.md) - Integration guide
- [Project Structure](./PROJECT_STRUCTURE.md) - Codebase organization

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [Vue.js Guide](https://vuejs.org/guide/)
- [TradingView Charting Library](https://www.tradingview.com/charting-library-docs/)

### Community
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and ideas
- Development logs for implementation context

---

**Remember**: The development logging system is designed to capture the context that would help any team member understand and reproduce your work months or years later. Be thorough in your documentation!