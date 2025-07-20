# Contributing to Trader Ops

Thank you for your interest in contributing to the Trader Ops trading dashboard! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Contribution Types](#contribution-types)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Development Logging](#development-logging)
- [Community Guidelines](#community-guidelines)

## 🤝 Code of Conduct

### Our Pledge
We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards
**Positive behaviors include:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors include:**
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## 🚀 Getting Started

### Prerequisites
Before contributing, ensure you have:
- **Python 3.11+** with UV
- **Node.js 18+** with npm
- **Git** with proper configuration
- Basic understanding of trading concepts (helpful but not required)
- Familiarity with Electron, Vue.js, or FastAPI (depending on contribution area)

### Setting Up Development Environment
```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/trader-ops.git
cd trader-ops

# 3. Set up development environment (automated)
./scripts/setup_uv.sh                   # Complete UV setup (installs UV, dependencies, logging)

# OR manual setup:
# uv sync --dev                         # Python dependencies
# npm install                           # Node.js dependencies
# ./scripts/dev-logging/setup-hooks.sh  # Development logging system

# 4. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 5. Verify setup
npm test                                # Run all tests
npm run dev                             # Start development servers
```

### First Contribution Setup
```bash
# 1. Create a new branch for your contribution
git checkout -b feature/your-feature-name

# 2. Make a small test change to verify development logging
echo "# Test contribution" >> CONTRIBUTING.md
git add CONTRIBUTING.md
git commit -m "test: verify development environment setup"
# Follow the development logging prompts

# 3. Revert the test change
git reset --hard HEAD~1
```

## 🔄 Development Workflow

### Branch Strategy
- **main**: Production-ready code
- **feature/**: New features (`feature/add-portfolio-tracking`)
- **bugfix/**: Bug fixes (`bugfix/websocket-reconnection`)
- **docs/**: Documentation updates (`docs/api-improvements`)
- **refactor/**: Code improvements (`refactor/optimize-data-flow`)

### Standard Workflow
```bash
# 1. Ensure main branch is up to date
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes with regular commits
# Edit files...
git add .
git commit -m "feat: add initial feature structure"
# Follow development logging prompts

# 4. Keep branch updated
git checkout main
git pull upstream main
git checkout feature/your-feature-name
git rebase main

# 5. Push and create pull request
git push origin feature/your-feature-name
# Create PR via GitHub interface
```

### Commit Message Convention
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

**Examples:**
```bash
feat(api): add real-time portfolio tracking endpoint
fix(frontend): resolve TradingView widget authentication timeout
docs(readme): update installation instructions for macOS
style(backend): format code according to Black standards
refactor(websocket): optimize connection management for better performance
test(integration): add comprehensive WebSocket connection tests
chore(deps): update FastAPI to version 0.104.1
```

## 🎯 Contribution Types

### 🚀 Feature Development
**Areas needing contributions:**
- **Trading Integrations**: Tradovate futures, crypto exchanges (CCXT)
- **Portfolio Analytics**: P&L tracking, performance metrics
- **Alert Systems**: Price alerts, news alerts, technical indicators
- **Backtesting**: Strategy testing and historical analysis (LEAN integration)
- **Mobile Interface**: React Native or web mobile version
- **Performance Optimization**: Further UV workflow enhancements

**Feature contribution process:**
1. **Discuss first**: Open an issue to discuss the feature
2. **Design review**: Share design approach for feedback
3. **Implementation**: Follow coding standards and testing requirements
4. **Documentation**: Update relevant documentation
5. **Testing**: Comprehensive test coverage

### 🐛 Bug Fixes
**Common bug areas:**
- WebSocket connection stability
- TradingView widget integration issues
- Data synchronization problems
- Cross-platform compatibility
- Memory leaks or performance issues

**Bug fix process:**
1. **Reproduce**: Create minimal reproduction case
2. **Root cause**: Document the underlying issue
3. **Fix**: Implement targeted solution
4. **Test**: Verify fix and add regression tests
5. **Document**: Update relevant documentation if needed

### 📚 Documentation
**Documentation needs:**
- API endpoint examples
- Integration guides for new data sources
- Troubleshooting guides
- Video tutorials
- Architecture decision records (ADRs)

### 🧪 Testing
**Testing contribution areas:**
- Unit test coverage improvement
- Integration test scenarios
- End-to-end workflow testing
- Performance and load testing
- Cross-platform testing

## 📥 Pull Request Process

### Before Submitting
- [ ] Code follows project style guidelines
- [ ] All tests pass (`npm test`)
- [ ] UV dependencies are properly specified (if adding packages)
- [ ] Documentation is updated
- [ ] Development log is complete
- [ ] Changes are focused and atomic
- [ ] Commit messages follow convention

### PR Template
When creating a pull request, include:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Cross-platform testing (if applicable)

## Documentation
- [ ] Code comments updated
- [ ] API documentation updated
- [ ] User documentation updated
- [ ] Development log completed

## Screenshots (if applicable)
Add screenshots for UI changes.

## Related Issues
Closes #(issue number)
```

### Review Process
1. **Automated checks**: CI/CD pipeline runs tests and quality checks
2. **Code review**: Maintainers review code for quality and design
3. **Testing**: Manual testing of functionality
4. **Documentation review**: Ensure documentation is complete and accurate
5. **Approval**: At least one maintainer approval required
6. **Merge**: Squash and merge or rebase and merge depending on PR size

### Review Criteria
- **Functionality**: Does it work as intended?
- **Code Quality**: Is it readable, maintainable, and efficient?
- **Testing**: Are there adequate tests?
- **Documentation**: Is it properly documented?
- **Security**: Are there any security implications?
- **Performance**: Does it impact system performance?

## 📏 Code Standards

### Python (Backend)
```python
# Style: Black formatting with line length 88
# Linting: Ruff with project-specific rules (via UV)
# Type hints: Required for all functions and methods

from typing import List, Optional
import asyncio

class DataConnector:
    """Base class for market data connectors."""
    
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
    
    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Fetch real-time quotes for symbols."""
        pass
```

**Standards:**
- Use type hints for all functions and class methods
- Docstrings for all public functions and classes (Google style)
- Maximum line length: 88 characters
- Use async/await for I/O operations
- Error handling with specific exception types
- UV for all Python package management (no Poetry/pip)

### TypeScript/JavaScript (Frontend)
```typescript
// Style: Prettier formatting
// Linting: ESLint with Vue.js rules
// Type safety: Strict TypeScript configuration

interface Quote {
  symbol: string;
  price: number;
  timestamp: number;
}

class QuoteManager {
  private quotes: Map<string, Quote> = new Map();
  
  public updateQuote(quote: Quote): void {
    this.quotes.set(quote.symbol, quote);
  }
  
  public getQuote(symbol: string): Quote | undefined {
    return this.quotes.get(symbol);
  }
}
```

**Standards:**
- Strict TypeScript configuration enabled
- Interface definitions for all data structures
- Proper error handling with try/catch
- Vue.js composition API preferred for new components
- Reactive data management with proper cleanup

### Vue.js Components
```vue
<template>
  <div class="quote-display">
    <h3>{{ symbol }}</h3>
    <span class="price">{{ formatPrice(quote.price) }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import type { Quote } from '@/types/market';

interface Props {
  symbol: string;
}

const props = defineProps<Props>();
const quote = ref<Quote | null>(null);

const formatPrice = (price: number): string => {
  return price.toFixed(2);
};

onMounted(() => {
  // Component initialization
});
</script>

<style scoped>
.quote-display {
  /* Component-specific styles */
}
</style>
```

## 🧪 Testing Requirements

### Test Coverage Targets
- **Unit tests**: >90% coverage for new code
- **Integration tests**: All API endpoints and data flows
- **E2E tests**: Critical user workflows

### Writing Tests
```python
# Python test example
import pytest
from src.backend.models import Quote

class TestQuote:
    def test_quote_validation(self):
        """Test quote model validation with valid data."""
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

    def test_quote_invalid_price(self):
        """Test quote validation with invalid price."""
        with pytest.raises(ValidationError):
            Quote(
                symbol="AAPL",
                bid=-1.0,  # Invalid negative price
                ask=150.02,
                last=150.01,
                volume=1000,
                timestamp=1705751400
            )
```

```typescript
// TypeScript test example
import { describe, it, expect } from 'vitest';
import { QuoteManager } from '@/services/QuoteManager';

describe('QuoteManager', () => {
  it('should update and retrieve quotes correctly', () => {
    const manager = new QuoteManager();
    const quote = {
      symbol: 'AAPL',
      price: 150.00,
      timestamp: Date.now()
    };
    
    manager.updateQuote(quote);
    const retrieved = manager.getQuote('AAPL');
    
    expect(retrieved).toEqual(quote);
  });
});
```

### Running Tests
```bash
# Run all tests
npm test

# Run specific test suites
uv run pytest tests/unit/
uv run pytest tests/integration/
npm run test:unit
npm run test:e2e

# Run with coverage
uv run pytest --cov=src tests/
npm run test:coverage
```

## 📚 Documentation Guidelines

### Code Documentation
- **Python**: Google-style docstrings for all public functions and classes
- **TypeScript**: JSDoc comments for public APIs and complex functions
- **Vue**: Component documentation using @vue/documentation

### API Documentation
- Update OpenAPI specifications for new endpoints
- Include request/response examples
- Document error conditions and responses
- Provide curl examples for testing

### User Documentation
- Clear step-by-step instructions
- Screenshots for UI features
- Troubleshooting sections
- Cross-platform considerations

### Development Documentation
- Architecture decision records (ADRs) for significant design decisions
- Update system architecture diagrams
- Document new integrations and data flows

## 📝 Development Logging

### Automated Logging System
This project uses an automated development logging system that captures comprehensive context for every development session. When you commit changes, you'll be prompted to provide:

- **Session objective** and background
- **Technical approach** and decisions
- **Implementation details** and challenges
- **Testing methodology** and validation
- **Future implications** and follow-up work

### Best Practices for Development Logs
1. **Be specific**: Include exact error messages, file paths, and commands
2. **Explain reasoning**: Don't just describe what you did, explain why
3. **Document failures**: Include failed attempts and lessons learned
4. **Reference resources**: Link to documentation, tutorials, or discussions
5. **Think future you**: Write as if explaining to yourself in 6 months

### Bypassing Development Logging
For small commits or when working in automated environments:
```bash
# Bypass for specific commits
git commit --no-verify -m "Your commit message"

# Bypass with flag in message (affects next commit)
git commit -m "Your commit message [skip-dev-log]"

# Disable temporarily
echo "DEV_LOGGING_ENABLED=false" >> .dev-logging-config
```

## 🌟 Community Guidelines

### Getting Help
- **Documentation**: Check the [docs/](docs/) directory first
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Development Logs**: Review [development logs](docs/development-logs/) for implementation context

### Reporting Issues
When reporting bugs or requesting features:
1. **Search existing issues** first
2. **Use issue templates** provided
3. **Provide minimal reproduction** cases for bugs
4. **Include system information** (OS, Python/Node versions, etc.)
5. **Attach relevant logs** and screenshots

### Communication Standards
- Be respectful and constructive in all interactions
- Use clear, descriptive titles for issues and PRs
- Provide context and background for requests
- Follow up on feedback and suggestions promptly

### Recognition
Contributors are recognized through:
- **Contributors file**: Listing all project contributors
- **Release notes**: Highlighting significant contributions
- **GitHub badges**: Contribution recognition on profiles
- **Mentorship opportunities**: For regular contributors

## 🚀 Advanced Contributions

### Architecture Changes
For significant architectural changes:
1. **RFC process**: Create a Request for Comments document
2. **Community discussion**: Discuss in GitHub Discussions
3. **Prototype**: Create a proof of concept
4. **Documentation**: Update architecture documentation
5. **Migration plan**: Document breaking changes and migration steps

### New Integrations
When adding new trading platforms or data sources:
1. **Abstract interface**: Implement the base connector interface
2. **Configuration**: Add necessary configuration options
3. **Testing**: Comprehensive testing with mock and real data
4. **Documentation**: Integration guide and API reference
5. **Examples**: Working examples and troubleshooting guide

### Performance Optimization
For performance improvements:
1. **Benchmarks**: Establish baseline measurements
2. **Profiling**: Document performance bottlenecks
3. **Testing**: Verify improvements with benchmarks
4. **Monitoring**: Add metrics for ongoing monitoring
5. **Documentation**: Update performance guidelines

## 📞 Support

### Getting Support
- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Comprehensive guides in [docs/](docs/)
- **Development Logs**: Implementation context and examples

### Providing Support
Help other contributors by:
- Answering questions in discussions
- Reviewing pull requests
- Improving documentation
- Sharing your development experiences

---

**Thank you for contributing to Trader Ops!** Your contributions help create better trading tools for the community. Every contribution, whether it's a bug fix, feature addition, or documentation improvement, is valuable and appreciated.

For questions about contributing, please open a discussion or contact the maintainers through GitHub.