# Security Incident: API Key Exposure in .mcp.json

**Date**: 2025-01-24
**Severity**: HIGH
**Reporter**: Red Hat Information Security
**Repository**: https://github.com/grimmolf/trader-ops.git
**Status**: ✅ RESOLVED

## Incident Details

- **What was exposed**: @21st-dev/magic API key
- **Where**: `.mcp.json` file, line 10
- **Exposed key**: [REDACTED - 64 character hex string]
- **Status**: ~~Key is in public git history~~ **CLEANED FROM HISTORY**

## Remediation Steps

### 1. Immediate Actions
- [ ] Revoke/regenerate the exposed API key at @21st-dev (USER ACTION STILL REQUIRED - No API management found)
- [x] Remove .mcp.json from git tracking
- [x] Add .mcp.json to .gitignore
- [x] Clean git history to remove the exposed key ✅ **COMPLETED 2025-01-24**

### 2. Implement Secure Configuration
- [x] Use environment variables for API keys
- [x] Update .mcp.json to use environment variable references
- [x] Document secure configuration in README
- [x] Create setup script for environment variables

### 3. Prevention
- [x] Review all configuration files for other potential secrets
- [x] Set up pre-commit hooks to detect secrets
- [x] Enable GitHub secret scanning (already enabled by Red Hat InfoSec)
- [x] Create comprehensive secret management documentation

## Actions Completed

1. **Added to .gitignore**:
   - `.mcp.json`
   - `mcp.config.json`
   - `.mcp/`
   - `.env.mcp`
   - `.env.21st`

2. **Removed from git tracking**:
   - Executed `git rm --cached .mcp.json`

3. **Created secure alternatives**:
   - `.mcp.json.example` - Template showing environment variable usage
   - `scripts/setup-mcp-env.sh` - Interactive setup script
   - `docs/security/SECRET_MANAGEMENT.md` - Comprehensive guide

4. **Enhanced pre-commit hooks**:
   - Installed gitleaks for secret detection
   - Added custom MCP file detection
   - Added API key pattern detection
   - Added private key detection

5. **Updated .mcp.json**:
   - Changed from hardcoded key to `${MAGIC_API_KEY:-}`

6. **Cleaned Git History** ✅ **2025-01-24**:
   - Used `git filter-repo` to remove the exposed key from all commits
   - Force pushed cleaned history to GitHub
   - Verified key no longer exists in any commit

## Resolution Summary

The exposed API key has been successfully removed from the git history using `git filter-repo`. The key was replaced with `***REMOVED***` in all historical commits and the cleaned history was force-pushed to GitHub.

### Remaining Action Items:
1. **API Key Status**: Unable to locate @21st-dev/magic API management console to revoke the exposed key. The key may still be active.
2. **Recommendation**: Continue trying to find where to manage @21st-dev/magic API keys or contact their support

## Impact Assessment
- The API key was publicly exposed in commit 2ae20da
- The key has been removed from git history as of 2025-01-24
- The key itself may still be active if not revoked at the service provider

## Lessons Learned
- Configuration files containing secrets should never be committed
- Use environment variables for all sensitive data
- Pre-commit hooks are essential for preventing secret exposure
- Regular security audits should include checking git history
- **Always verify API key management capabilities before using a service** 