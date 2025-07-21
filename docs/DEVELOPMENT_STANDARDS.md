# TraderTerminal Development Standards

This document defines the mandatory development practices for the TraderTerminal project to ensure code quality and prevent CI/CD failures.

## 🎯 Core Principles

1. **Fail Fast**: Catch issues locally before they reach CI/CD
2. **Consistency**: Same environment for all developers
3. **Automation**: Minimize manual checks through tooling
4. **Prevention**: Systemic fixes over reactive patches

## 🐍 Python Standards

### Version Requirements

- **Python Version**: 3.11.x (strictly enforced)
- **Lock File**: `.python-version` specifies exact version
- **CI/CD**: Tests run on Python 3.11 and 3.12

```bash
# Check your Python version
uv run python --version  # Must show 3.11.x
```

### Pydantic v2 Compliance

All models MUST use Pydantic v2 syntax:

```python
# ❌ WRONG - Pydantic v1
from pydantic import BaseModel, validator

class MyModel(BaseModel):
    name: str
    
    class Config:
        allow_population_by_field_name = True
    
    @validator('name')
    def validate_name(cls, v):
        return v.strip()

# ✅ CORRECT - Pydantic v2
from pydantic import BaseModel, field_validator, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: str
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v):
        return v.strip()
```

### Async Testing

Use modern pytest-asyncio syntax:

```python
# ❌ WRONG
@pytest_asyncio.async_test
async def test_something():
    pass

# ✅ CORRECT
@pytest.mark.asyncio
async def test_something():
    pass
```

## 🛠️ Development Workflow

### 1. Initial Setup (One Time)

```bash
# Clone and enter project
git clone https://github.com/grimmolf/trader-ops.git
cd trader-ops

# Run automated setup
./scripts/setup-dev-environment.sh
```

### 2. Before Every Coding Session

```bash
# Ensure correct Python version
uv run python --version

# Check compatibility
uv run python scripts/check-compatibility.py

# Update dependencies
uv sync --dev
npm install
```

### 3. Before Every Commit

Pre-commit hooks run automatically, but you can test manually:

```bash
# Run all checks
pre-commit run --all-files

# Run specific checks
uv run ruff check src/
uv run black --check src/
uv run mypy src/
uv run pytest tests/unit -x
```

### 4. Before Creating PR

```bash
# Run full test suite
npm test

# Check CI/CD compatibility
uv run python scripts/check-compatibility.py

# Fix any issues
./scripts/fix-ci-issues.sh
```

## 📦 Dependency Management

### Adding Dependencies

```toml
# pyproject.toml
dependencies = [
    "package>=1.0.0,<2.0.0",  # Always pin major version
]

[dependency-groups]
dev = [
    "test-package>=1.0.0",
]
```

After adding:
```bash
uv lock --upgrade-package <package-name>
uv sync --dev
```

### Security Scanning

Dependencies are automatically scanned for vulnerabilities:
- Weekly automated updates via GitHub Actions
- Pre-commit hooks check for security issues
- CI/CD blocks on critical vulnerabilities

## 🧪 Testing Standards

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Tests with external dependencies
├── e2e/            # End-to-end workflow tests
└── conftest.py     # Shared fixtures
```

### Test Requirements

1. **Minimum Coverage**: 80% for new code
2. **Async Tests**: Use `@pytest.mark.asyncio`
3. **Fixtures**: Define in `conftest.py`
4. **Mocking**: Mock all external API calls

### Running Tests

```bash
# Unit tests only (fast)
uv run pytest tests/unit -v

# With coverage
uv run pytest tests/unit --cov=src --cov-report=html

# Specific test file
uv run pytest tests/unit/test_specific.py -v

# Run failed tests only
uv run pytest --lf
```

## 🎨 Code Style

### Python Style

- **Formatter**: Black (line length 88)
- **Import Sorter**: isort (black-compatible)
- **Linter**: Ruff (comprehensive rules)
- **Type Checker**: mypy (strict mode)

### JavaScript/TypeScript Style

- **Formatter**: Prettier
- **Linter**: ESLint with TypeScript plugin
- **Framework**: Vue 3 Composition API

## 🔐 Security Practices

### API Keys and Secrets

1. **Never commit secrets** - Use environment variables
2. **Use `.env` files** - Never commit these
3. **Secrets in CI/CD** - Use GitHub Secrets

### Pre-commit Security Checks

- Gitleaks scans for secrets
- Bandit checks Python security
- Dependencies scanned for vulnerabilities

## 🚀 CI/CD Integration

### Pipeline Stages

1. **Compatibility Check** - Python version, dependencies
2. **Lint & Format** - Code style validation
3. **Type Check** - Static type analysis
4. **Unit Tests** - Fast isolated tests
5. **Integration Tests** - With mocked externals
6. **Security Scan** - Vulnerabilities and secrets
7. **Build** - Package creation
8. **E2E Tests** - Full workflow validation

### Branch Protection

- **main**: Protected, requires PR and passing tests
- **develop**: Integration branch, requires passing tests
- **feature/***: Developer branches, pre-commit hooks enforced

## 📊 Monitoring

### Health Checks

```bash
# Check CI/CD health
uv run python scripts/ci-health-check.py

# View recent failures
gh run list --limit 10

# Debug specific run
gh run view <run-id>
```

### Common Issues

1. **Python Version Mismatch**
   - Solution: `uv python install 3.11`

2. **Pydantic v1 Syntax**
   - Solution: `./scripts/fix-ci-issues.sh`

3. **Import Errors**
   - Solution: Check `__init__.py` files exist

4. **Type Errors**
   - Solution: Add type hints or `# type: ignore` comments

## 🆘 Troubleshooting

### CI/CD Failures

1. Check the specific job that failed
2. Run the same command locally
3. Use compatibility check script
4. Apply automated fixes if available

### Local Development Issues

```bash
# Reset environment
rm -rf .venv
uv sync --dev

# Clear caches
rm -rf .pytest_cache
rm -rf .mypy_cache
rm -rf __pycache__

# Reinstall pre-commit
pre-commit uninstall
pre-commit install
```

## 📚 Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [Pydantic V2 Migration](https://docs.pydantic.dev/latest/migration/)
- [pytest-asyncio Guide](https://pytest-asyncio.readthedocs.io/)
- [Pre-commit Hooks](https://pre-commit.com/)

## ✅ Checklist

Before pushing code, ensure:

- [ ] Python 3.11 is active (`uv run python --version`)
- [ ] All tests pass (`npm test`)
- [ ] No linting errors (`pre-commit run --all-files`)
- [ ] No type errors (`uv run mypy src/`)
- [ ] No security issues (`uv run bandit -r src/`)
- [ ] Dependencies are locked (`uv lock`)
- [ ] Documentation is updated 