# Security Incident: Hardcoded Credentials in Documentation

**Date**: 2025-01-24
**Severity**: HIGH
**Reporter**: Red Hat Information Security
**Repository**: https://github.com/grimmolf/trader-ops.git
**Status**: ✅ RESOLVED

## Incident Details

- **What was exposed**: MongoDB credentials and application keys in documentation
- **Where**: Multiple files containing example configurations
- **Exposed credentials**:
  - MongoDB: `tradenote:[REDACTED]`
  - App ID: `traderterminal_dev_[REDACTED]`
  - Master Key: `traderterminal_master_dev_[REDACTED]`

## Affected Files

1. **docs/user/TRADENOTE_SETUP_GUIDE.md** - Multiple instances
2. **docs/api/TRADENOTE_API.md** - Environment variable examples
3. **src/backend/integrations/tradenote/integration_example.py** - Commented examples
4. **deployment/compose/env.example** - Already using "example" placeholders (acceptable)

## Remediation Actions

### Completed ✅
1. **Replaced all hardcoded credentials with placeholders**:
   - MongoDB credentials → `<DB_USER>:<DB_PASSWORD>`
   - App ID → `<YOUR_APP_ID>`
   - Master Key → `<YOUR_MASTER_KEY>`

2. **Added security warning** in documentation:
   - Added prominent warning about not committing real credentials
   - Emphasized use of environment variables or secure secret management

3. **Verified no remaining exposure**:
   - Searched entire codebase for specific credential patterns
   - Confirmed all instances have been replaced

## Impact Assessment
- These were example/development credentials in documentation
- Risk level: Medium (could be mistaken for real credentials)
- No indication these were actual production credentials

## Lessons Learned
1. **Always use clear placeholders** in documentation (e.g., `<PLACEHOLDER>`)
2. **Avoid realistic-looking credentials** even in examples
3. **Add security warnings** when showing configuration examples
4. **Review all documentation** for potential credential exposure

## Prevention Measures
- Pre-commit hooks already in place from previous incident
- Will catch future attempts to commit similar patterns
- Regular security audits should include documentation review 