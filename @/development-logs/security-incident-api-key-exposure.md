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

────────────────────────────────────────
Host-agnostic parts (already done)  
• Pre-commit config, security scripts, `.gitleaks.toml`, `.gitignore` additions  
→ Work on every workstation regardless of remote host.  

Host-specific parts (need parallel jobs)  
• GitHub → `.github/workflows/security-scanning.yml` (already created)  
• GitLab → `.gitlab-ci.yml` (to be added)

────────────────────────────────────────
What we should add for GitLab projects

```yaml
<code_block_to_apply_changes_from>
# .gitlab-ci.yml  (minimal version – mirrors the GitHub job names)
stages:
  - security

variables:
  GITLEAKS_CONFIG: ".gitleaks.toml"

security_scanning:
  stage: security
  image: golang:1.22-alpine   # contains bash + curl
  before_script:
    - apk add --no-cache git curl python3
    - go install github.com/gitleaks/gitleaks/v8@latest   # installs gitleaks
    - curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
  script:
    - echo "🔍 Running Gitleaks"
    - gitleaks detect --config $GITLEAKS_CONFIG --redact --no-banner
    - echo "🔍 Running TruffleHog (verified only)"
    - trufflehog git file://. --only-verified --fail
    - echo "🔍 Running custom pattern scan"
    - bash scripts/security/check-api-keys.sh
    - bash scripts/security/check-config-files.sh
  allow_failure: false
```

• Branch protection / “MR approval rules” → configure in the GitLab UI to **require** that `security_scanning` passes before merge, the same way we require the “Security Scanning” status check on GitHub.  
• GitLab has its own *Server-side Secret Detection* feature; enable **“Push Rules → Prevent secrets”** or Secret-Scanning under **Settings → Security & Compliance** for an extra layer.

────────────────────────────────────────
Making the setup script host-aware

Update `global_claude/scripts/setup-project-security.sh`:

1. Detect default remote:  
   ```bash
   remote=$(git remote get-url origin 2>/dev/null || true)
   case "$remote" in
     *github.com*) host=github ;;
     *gitlab*)     host=gitlab ;;
     *)            host=unknown ;;
   esac
   ```
2. Always install the host-agnostic parts.  
3. If `$host == github` → write the `.github/workflows/…` files.  
   If `$host == gitlab` → write `.gitlab-ci.yml`.  
   (If unknown, warn and skip CI config.)

────────────────────────────────────────
Bottom line

• Nothing in the local tooling needs to change—those protections already cover **all** repositories.  
• Add a small `.gitlab-ci.yml` (or include a central template) so GitLab projects get the same CI gate.  
• Enhance the setup script to drop the correct CI file automatically.

Let me know if you’d like me to:

1. generate the ready-to-use `.gitlab-ci.yml`, and/or  
2. patch the setup script to auto-detect the host and copy the right CI template.

(That is a self-contained, reversible change and keeps behaviour consistent across both GitHub and Red Hat GitLab.) 