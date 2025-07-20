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

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Development Logging Pre-Commit Hook
# Prompts for development log before committing

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_SCRIPT="$PROJECT_ROOT/scripts/dev-logging/log-prompt.py"

# Check if dev logging is enabled
if [ -f "$PROJECT_ROOT/.dev-logging-config" ]; then
    source "$PROJECT_ROOT/.dev-logging-config"
fi

# Default configuration
DEV_LOGGING_ENABLED=${DEV_LOGGING_ENABLED:-true}
DEV_LOGGING_MODE=${DEV_LOGGING_MODE:-"pre-commit"}
DEV_LOGGING_SKIP_PROMPT=${DEV_LOGGING_SKIP_PROMPT:-false}

# Skip if disabled
if [ "$DEV_LOGGING_ENABLED" != "true" ]; then
    exit 0
fi

# Skip if not in pre-commit mode
if [ "$DEV_LOGGING_MODE" != "pre-commit" ]; then
    exit 0
fi

# Check if this is a merge commit or other automated commit
if [ -n "$GIT_MERGE_HEAD" ] || [ -n "$GIT_CHERRY_PICK_HEAD" ] || [ -n "$GIT_REVERT_HEAD" ]; then
    echo "⏩ Skipping development log for automated commit"
    exit 0
fi

# Check for bypass flag
if git rev-parse --verify HEAD >/dev/null 2>&1; then
    if git log -1 --pretty=%B | grep -q "\[skip-dev-log\]"; then
        echo "⏩ Skipping development log due to [skip-dev-log] flag"
        exit 0
    fi
fi

# Check if there are any staged changes
if ! git diff --cached --quiet; then
    echo ""
    echo "📝 Development Log Required"
    echo "============================"
    echo "Staged changes detected. Capturing development context..."
    echo ""
    echo "💡 Tips:"
    echo "  - Provide detailed information for reproducibility"
    echo "  - Include reasoning behind technical decisions"
    echo "  - Add [skip-dev-log] to commit message to bypass next time"
    echo "  - Use 'git commit --no-verify' to skip hooks entirely"
    echo ""
    
    if [ "$DEV_LOGGING_SKIP_PROMPT" != "true" ]; then
        read -p "Continue with development log? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo "❌ Commit cancelled. Use 'git commit --no-verify' to bypass."
            exit 1
        fi
    fi
    
    # Run the development logging script
    if [ -f "$LOG_SCRIPT" ]; then
        python3 "$LOG_SCRIPT"
        LOG_EXIT_CODE=$?
        
        if [ $LOG_EXIT_CODE -ne 0 ]; then
            echo "❌ Development logging failed or was cancelled."
            echo "   Use 'git commit --no-verify' to bypass if needed."
            exit 1
        fi
    else
        echo "⚠️  Development logging script not found: $LOG_SCRIPT"
        echo "   Run ./scripts/dev-logging/setup-hooks.sh to set up properly."
    fi
fi

exit 0
EOF

# Create post-commit hook
cat > "$HOOKS_DIR/post-commit" << 'EOF'
#!/bin/bash
# Development Logging Post-Commit Hook
# Prompts for development log after successful commit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_SCRIPT="$PROJECT_ROOT/scripts/dev-logging/log-prompt.py"

# Check if dev logging is enabled
if [ -f "$PROJECT_ROOT/.dev-logging-config" ]; then
    source "$PROJECT_ROOT/.dev-logging-config"
fi

# Default configuration
DEV_LOGGING_ENABLED=${DEV_LOGGING_ENABLED:-true}
DEV_LOGGING_MODE=${DEV_LOGGING_MODE:-"pre-commit"}
DEV_LOGGING_SKIP_PROMPT=${DEV_LOGGING_SKIP_PROMPT:-false}

# Skip if disabled
if [ "$DEV_LOGGING_ENABLED" != "true" ]; then
    exit 0
fi

# Skip if not in post-commit mode
if [ "$DEV_LOGGING_MODE" != "post-commit" ]; then
    exit 0
fi

# Check if this is a merge commit or other automated commit
if [ -n "$GIT_MERGE_HEAD" ] || [ -n "$GIT_CHERRY_PICK_HEAD" ] || [ -n "$GIT_REVERT_HEAD" ]; then
    echo "⏩ Skipping development log for automated commit"
    exit 0
fi

# Check for bypass flag in the commit message
if git log -1 --pretty=%B | grep -q "\[skip-dev-log\]"; then
    echo "⏩ Skipping development log due to [skip-dev-log] flag"
    exit 0
fi

echo ""
echo "📝 Post-Commit Development Log"
echo "==============================="
echo "Commit successful! Capturing development context..."
echo ""

if [ "$DEV_LOGGING_SKIP_PROMPT" != "true" ]; then
    read -p "Create development log for this commit? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "⏩ Development log skipped."
        exit 0
    fi
fi

# Run the development logging script
if [ -f "$LOG_SCRIPT" ]; then
    python3 "$LOG_SCRIPT"
    LOG_EXIT_CODE=$?
    
    if [ $LOG_EXIT_CODE -ne 0 ]; then
        echo "⚠️  Development logging failed or was cancelled."
        echo "   This doesn't affect your commit, which was successful."
    fi
else
    echo "⚠️  Development logging script not found: $LOG_SCRIPT"
    echo "   Run ./scripts/dev-logging/setup-hooks.sh to set up properly."
fi

exit 0
EOF

# Make hooks executable
chmod +x "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/post-commit"

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