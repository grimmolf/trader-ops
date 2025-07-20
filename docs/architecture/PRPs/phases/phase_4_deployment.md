### Phase 4: Deployment Preparation (Week 3)

##### Task 4.1: macOS Code Signing Preparation
```javascript
// Update electron-builder.yml
appId: com.grimmolf.traderterminal
productName: TraderTerminal
directories:
  output: dist
  buildResources: build

mac:
  category: public.app-category.finance
  icon: assets/icon.icns
  hardenedRuntime: true
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist
  gatekeeperAssess: false
  notarize:
    teamId: "YOUR_TEAM_ID"

dmg:
  contents:
    - x: 130
      y: 220
    - x: 410
      y: 220
      type: link
      path: /Applications
```

##### Task 4.2: Create Installation Scripts
```bash
# Create scripts/package_macos.sh
#!/bin/bash

echo "Building TraderTerminal for macOS"
echo "================================="

# Clean previous builds
rm -rf dist/

# Build backend
cd src/backend
uv build --wheel
cd ../..

# Build frontend
cd src/frontend
npm run build
cd ../..

# Package with Electron
cd src/frontend
npm run dist:mac

echo "Build complete! Check dist/ directory for .dmg file"
```

