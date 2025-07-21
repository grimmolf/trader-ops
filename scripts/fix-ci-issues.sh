#!/bin/bash
# Fix CI/CD Issues Script

echo "🔧 Fixing CI/CD Pipeline Issues..."

# 1. Fix pytest-asyncio decorator issue
echo "📝 Fixing pytest-asyncio decorators..."
find tests -name "*.py" -type f -exec sed -i '' 's/@pytest_asyncio\.async_test/@pytest.mark.asyncio/g' {} +
echo "✅ Fixed pytest-asyncio decorators"

# 2. Install correct Python version
echo "🐍 Installing Python 3.11 via UV..."
uv python install 3.11
echo "✅ Python 3.11 installed"

# 3. Fix Pydantic v1 deprecations
echo "📝 Fixing Pydantic deprecations..."

# Fix validator imports
find src -name "*.py" -type f -exec sed -i '' 's/from pydantic import validator/from pydantic import field_validator/g' {} +

# Fix @validator decorators to @field_validator
find src -name "*.py" -type f -exec sed -i '' 's/@validator(/@field_validator(/g' {} +

# Fix class Config to ConfigDict
cat > fix_pydantic_config.py << 'EOF'
import os
import re

def fix_pydantic_config(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace class Config with model_config
    pattern = r'class Config:\s*([^}]+?)(?=\n\s*(?:class|def|@|\Z))'
    
    def replace_config(match):
        config_body = match.group(1)
        # Extract config values
        config_lines = [line.strip() for line in config_body.split('\n') if line.strip()]
        config_dict = {}
        
        for line in config_lines:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle special cases
                if key == 'allow_population_by_field_name':
                    key = 'validate_by_name'
                
                config_dict[key] = value
        
        # Build model_config
        config_str = 'model_config = ConfigDict(\n'
        for key, value in config_dict.items():
            config_str += f'        {key}={value},\n'
        config_str = config_str.rstrip(',\n') + '\n    )'
        
        return config_str
    
    # Replace class Config blocks
    if 'class Config:' in content:
        content = re.sub(pattern, replace_config, content)
        
        # Add ConfigDict import
        if 'from pydantic import' in content and 'ConfigDict' not in content:
            content = re.sub(
                r'(from pydantic import[^)]+)',
                r'\1, ConfigDict',
                content
            )
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Fixed: {filepath}")

# Find all Python files with Pydantic models
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                fix_pydantic_config(filepath)
            except Exception as e:
                print(f"Error fixing {filepath}: {e}")
EOF

uv run python fix_pydantic_config.py
rm fix_pydantic_config.py

echo "✅ Fixed Pydantic deprecations"

# 4. Fix specific Pydantic validator syntax
echo "📝 Updating Pydantic validator syntax..."

# Update validator methods to use mode='before'
find src -name "*.py" -type f -exec sed -i '' 's/@field_validator(\(.*\))/@field_validator(\1, mode="before")/g' {} +

# Fix duplicate mode parameters (common when script is run multiple times)
find src -name "*.py" -type f -exec sed -i '' 's/mode="before", mode="before"/mode="before"/g' {} +

echo "✅ Updated Pydantic validator syntax"

# 5. Sync dependencies with correct Python version
echo "📦 Syncing dependencies..."
uv sync --dev
echo "✅ Dependencies synced"

# 6. Run linting fixes
echo "🧹 Running auto-formatting..."
uv run black src/ tests/
uv run isort src/ tests/
echo "✅ Code formatted"

# 7. Check for missing __init__.py files
echo "📝 Checking for missing __init__.py files..."
find src -type d -exec bash -c 'test -f "$0/__init__.py" || touch "$0/__init__.py"' {} \;
find tests -type d -exec bash -c 'test -f "$0/__init__.py" || touch "$0/__init__.py"' {} \;
echo "✅ Added missing __init__.py files"

echo "🎉 CI/CD fixes complete!"
echo ""
echo "Next steps:"
echo "1. Review the changes: git diff"
echo "2. Run tests locally: npm run test"
echo "3. Commit the fixes: git add -A && git commit -m 'fix: resolve CI/CD pipeline issues'"
echo "4. Push to trigger CI: git push" 