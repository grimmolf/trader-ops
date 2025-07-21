# GitHub Security Setup Guide

This guide explains how to configure GitHub security features to prevent secrets from being merged into your repository.

## 🔒 Branch Protection Rules

To ensure no secrets can be merged, configure these branch protection rules:

### 1. Navigate to Repository Settings
1. Go to your repository on GitHub
2. Click **Settings** → **Branches**
3. Click **Add rule** or edit existing rules for `main` and `develop`

### 2. Required Status Checks
Enable these required status checks:
- ✅ `Enhanced Security Scanning / Secrets and API Key Detection`
- ✅ `Enhanced Security Scanning / Gitleaks Secret Scan` 
- ✅ `CI / lint-and-format`
- ✅ `CI / test-python`

### 3. Additional Protection Settings
- ✅ **Require a pull request before merging**
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**
- ✅ **Include administrators** (prevents bypassing)
- ✅ **Restrict who can dismiss pull request reviews**

## 🚨 Security Workflows

### Automated Secret Scanning
The repository includes multiple layers of secret detection:

1. **Gitleaks** - Scans for secrets using regex patterns
2. **TruffleHog** - Verifies secrets against actual services
3. **Custom Patterns** - Specific to trader-ops credentials
4. **File Detection** - Prevents `.mcp.json` commits

### When Secrets Are Detected

If the security scan detects secrets:
1. The PR will be blocked from merging
2. A comment will be added with remediation steps
3. For pushes to main, an urgent issue will be created

## 📋 Developer Workflow

### Before Committing
1. Run pre-commit hooks locally:
   ```bash
   git add .
   git commit -m "your message"
   # Pre-commit hooks will run automatically
   ```

2. If hooks fail:
   ```bash
   # View what was detected
   cat .git/hooks/pre-commit.log
   
   # Fix the issues and try again
   ```

### Creating Pull Requests
1. Use the PR template checklist
2. Verify all security items are checked
3. Wait for automated scans to complete
4. Address any security findings before merge

## 🛠️ Local Setup

### Install Pre-commit Hooks
```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

### Test Secret Detection Locally
```bash
# Run gitleaks locally
docker run --rm -v $(pwd):/code zricethezav/gitleaks:latest detect --source /code

# Run custom pattern checks
./scripts/check-api-keys.sh
./scripts/check-mcp-files.sh
```

## 🔍 GitHub Secret Scanning

### Enable Native GitHub Features
1. Go to **Settings** → **Security & analysis**
2. Enable:
   - ✅ Dependency graph
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates
   - ✅ Secret scanning
   - ✅ Secret scanning push protection

### Custom Secret Patterns
Add custom patterns for your specific secrets:
1. Go to **Settings** → **Security & analysis** → **Secret scanning**
2. Click **New pattern**
3. Add patterns like:
   - Pattern: `traderterminal_[a-z]+_[0-9]{3}`
   - Pattern: `[a-fA-F0-9]{64}` (for hex API keys)

## 📊 Monitoring

### Security Alerts
- Check **Security** tab regularly
- Subscribe to security alert emails
- Review Dependabot alerts weekly

### Audit Log
- Review push protection bypasses
- Monitor failed security scans
- Track secret scanning alerts

## 🚀 Best Practices

1. **Never commit real credentials** - Always use placeholders
2. **Use environment variables** - Store secrets securely
3. **Rotate regularly** - Change credentials every 90 days
4. **Review PR carefully** - Check for accidental secrets
5. **Enable 2FA** - Protect your GitHub account
6. **Least privilege** - Limit repository access

## 📞 Incident Response

If a secret is exposed:
1. **Immediately revoke** the compromised credential
2. **Run git filter-repo** to clean history
3. **Force push** the cleaned history
4. **Document** in security incident log
5. **Review** how it bypassed protections

## 🔗 Resources

- [GitHub Secret Scanning Docs](https://docs.github.com/en/code-security/secret-scanning)
- [Gitleaks Documentation](https://github.com/gitleaks/gitleaks)
- [TruffleHog Documentation](https://github.com/trufflesecurity/trufflehog)
- [Pre-commit Framework](https://pre-commit.com/) 