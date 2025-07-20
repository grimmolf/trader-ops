#!/bin/bash
# Development Logging Git Hooks Setup
# Installs git hooks for automated development log prompts

set -e

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Setting up Development Logging Git Hooks"
echo "============================================="
echo "Project root: $PROJECT_ROOT"
echo "Hooks directory: $HOOKS_DIR"

# Ensure hooks directory exists
mkdir -p "$HOOKS_DIR"

echo "📝 Installing new pre-commit hook for single-file dev-log"

# Remove old hooks if they exist
rm -f "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/post-commit"

cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/usr/bin/env bash
# New Development Log Pre-commit Hook (single-file version)

LOG_FILE="docs/CLAUDE_DEVELOPMENT_LOG.md"

# Skip on merge / rebase
if [[ -n "$GIT_MERGE_HEAD" || -n "$GIT_REBASE_HEAD" ]]; then
    exit 0
fi

# Skip if commit has [skip-dev-log]
if git log -1 --pretty=%B | grep -q "\[skip-dev-log\]"; then
    exit 0
fi

# Only run if there are staged changes
git diff --cached --quiet && exit 0

# Ensure log file exists
if [[ ! -f "$LOG_FILE" ]]; then
    mkdir -p "$(dirname "$LOG_FILE")"
    cat > "$LOG_FILE" <<'MARK'
# Trader Ops - Claude Code Development Log

### [YYYY-MM-DD HH:MM] - [branch] - [Short summary]
**Context:** _What problem are you solving?_
**Changes:** _Bullet list of key changes._
**Validation:** _How did you test?_

---
MARK
fi

echo "📝 Please update $LOG_FILE before committing. Press ENTER to open editor (CTRL+C to cancel)"
read -r _

${EDITOR:-nano} "$LOG_FILE"

# Stage the log file
git add "$LOG_FILE"

exit 0
EOF

# Make executable
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ New pre-commit hook installed (old hooks removed)"

# Create default configuration file
cat > "$PROJECT_ROOT/.dev-logging-config" << 'EOF'
# Development Logging Configuration
# Edit these settings to customize logging behavior

# Enable/disable development logging
DEV_LOGGING_ENABLED=true

# When to prompt for logs: "pre-commit" or "post-commit"
# pre-commit: Prompts before commit (blocks commit if cancelled)
# post-commit: Prompts after successful commit (non-blocking)
DEV_LOGGING_MODE=pre-commit

# Skip the "Continue with log?" prompt
DEV_LOGGING_SKIP_PROMPT=false

# Additional settings
DEV_LOGGING_AUTO_ADD=true  # Automatically add logs to commit
EOF

# Create .gitignore entry for config file
if [ -f "$PROJECT_ROOT/.gitignore" ]; then
    if ! grep -q ".dev-logging-config" "$PROJECT_ROOT/.gitignore"; then
        echo ".dev-logging-config" >> "$PROJECT_ROOT/.gitignore"
    fi
fi

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "📁 Created files:"
echo "   🪝 .git/hooks/pre-commit"
echo "   🪝 .git/hooks/post-commit"
echo "   ⚙️  .dev-logging-config"
echo ""
echo "🔧 Configuration:"
echo "   Edit .dev-logging-config to customize behavior"
echo "   Current mode: pre-commit (prompts before commit)"
echo ""
echo "💡 Usage tips:"
echo "   • Add [skip-dev-log] to commit message to bypass"
echo "   • Use 'git commit --no-verify' to skip all hooks"
echo "   • Set DEV_LOGGING_MODE=post-commit for non-blocking mode"
echo ""
echo "🧪 Test the setup:"
echo "   1. Make a small change to a file"
echo "   2. git add <file>"
echo "   3. git commit -m 'Test development logging'"
echo ""