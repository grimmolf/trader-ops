# @trader-terminal/ui

**Shared UI component library for TraderTerminal applications**

Professional trading interface components built with Vue 3, TypeScript, and modern design principles. Used by both the web application and Electron desktop app.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Development build (watch mode)
npm run dev

# Production build
npm run build

# Type checking
npm run type-check
```

## 📦 Installation

```bash
# In your TraderTerminal application
npm install @trader-terminal/ui
```

## 🧩 Components

### Core Trading Components

#### RiskMeter
Advanced risk monitoring component with visual indicators and real-time updates.

```vue
<template>
  <RiskMeter
    label="Daily P&L"
    :current="1250"
    :limit="2000"
    :inverse="false"
    :show-threshold="true"
    :threshold-value="80"
    threshold-label="Warning"
    format="currency"
  />
</template>

<script setup>
import { RiskMeter } from '@trader-terminal/ui'
</script>
```

**Features:**
- Real-time value updates with smooth animations
- Configurable severity levels (safe, caution, warning, danger, critical)
- Multiple formats: currency, percentage, number
- Visual indicators with color-coded status
- Optional threshold lines and remaining capacity display

#### AccountSelector
Multi-broker account management and selection interface.

```vue
<template>
  <AccountSelector
    :accounts="accounts"
    :active-account="activeAccount"
    :loading="loading"
    @account-changed="handleAccountChange"
    @show-violations="showViolations"
    @positions-flattened="handleFlatten"
  />
</template>

<script setup>
import { AccountSelector } from '@trader-terminal/ui'
</script>
```

**Features:**
- Multi-broker account support (Schwab, Tastytrade, TopstepX, Tradovate)
- Real-time account metrics and P&L
- Violation alerts and risk warnings
- Quick account actions (refresh, flatten positions)
- Connection status indicators

#### FundedAccountPanel
Comprehensive funded account dashboard with risk management.

```vue
<template>
  <FundedAccountPanel
    :accounts="fundedAccounts"
    :active-account="selectedAccount"
    :realtime-enabled="realtimeData"
    @account-changed="selectAccount"
    @emergency-flatten="emergencyClose"
    @toggle-realtime="toggleRealtime"
  />
</template>

<script setup>
import { FundedAccountPanel } from '@trader-terminal/ui'
</script>
```

**Features:**
- Complete funded account overview
- Risk metrics with visual meters
- Evaluation progress tracking
- Trading rules and restrictions display
- Performance statistics
- Emergency position controls

## 🎨 Design System

### Color Palette
```css
/* Risk Level Colors */
--risk-safe: #28a745;
--risk-caution: #17a2b8;
--risk-warning: #ffc107;
--risk-danger: #fd7e14;
--risk-critical: #dc3545;

/* UI Colors */
--primary-color: #0d6efd;
--background-primary: #ffffff;
--background-secondary: #f8f9fa;
--text-primary: #212529;
--text-muted: #6c757d;
--border-color: #dee2e6;
```

### Typography
- **Primary Font**: System fonts for optimal performance
- **Font Sizes**: 0.75rem to 1.25rem scale
- **Font Weights**: 400 (normal), 500 (medium), 600 (semibold)

### Spacing
- **Base Unit**: 0.25rem (4px)
- **Scale**: 0.25rem, 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem, 3rem

## 🏗️ Architecture

### Build System
- **Bundler**: Vite with library mode
- **Output**: ES modules with TypeScript declarations
- **Size**: ~36kB optimized build
- **Externals**: Vue, Pinia, VueUse (peer dependencies)

### TypeScript Support
```typescript
// Full type definitions included
import type { 
  RiskMeterProps,
  AccountSelectorProps,
  FundedAccountPanelProps 
} from '@trader-terminal/ui'
```

### Component Architecture
```
packages/ui/src/
├── components/           # Vue components
│   ├── RiskMeter.vue
│   ├── AccountSelector.vue
│   └── FundedAccountPanel.vue
├── types/                # TypeScript definitions
│   ├── index.ts         # Core types
│   └── vue-components.ts # Component props/events
├── composables/          # Reusable composition functions
├── stores/               # Pinia store definitions
└── index.ts              # Main export file
```

## 🔧 Development

### Component Development
```bash
# Watch mode for development
npm run dev

# Build library
npm run build

# Type checking
npm run type-check
```

### Adding New Components
1. **Create component** in `src/components/`
2. **Add TypeScript types** in `src/types/`
3. **Export component** in `src/index.ts`
4. **Build and test** the library

### Testing Components
```vue
<!-- Example usage in consuming application -->
<template>
  <div class="trading-interface">
    <RiskMeter 
      v-for="metric in riskMetrics"
      :key="metric.id"
      v-bind="metric"
    />
  </div>
</template>
```

## 📚 API Reference

### Component Props

#### RiskMeter Props
```typescript
interface RiskMeterProps {
  label: string                    // Display label
  current: number                  // Current value
  limit: number                    // Maximum limit
  inverse?: boolean                // Higher values = worse (for drawdown)
  showThreshold?: boolean          // Show warning threshold line
  thresholdValue?: number          // Threshold percentage (default: 80)
  thresholdLabel?: string          // Threshold label text
  showRemaining?: boolean          // Show remaining capacity
  showDetails?: boolean            // Show additional details
  timeToLimit?: number             // Minutes until limit reached
  format?: 'currency' | 'percentage' | 'number'  // Value format
}
```

#### AccountSelector Props
```typescript
interface AccountSelectorProps {
  accounts?: TradingAccount[]      // Available accounts
  activeAccount?: TradingAccount   // Currently selected account
  loading?: boolean                // Loading state
  groupedAccounts?: GroupedAccounts[]  // Accounts grouped by platform
  selectedAccountId?: string       // Selected account ID
}
```

### Component Events
```typescript
// RiskMeter Events
'threshold-exceeded': { value: number; threshold: number }
'critical-level-reached': { value: number }

// AccountSelector Events  
'account-changed': string        // Account ID
'show-violations': void
'show-details': void
'positions-flattened': void

// FundedAccountPanel Events
'account-changed': string
'toggle-realtime': void
'refresh-all': void
'emergency-flatten': void
```

## 🎯 Usage Examples

### Risk Management Dashboard
```vue
<template>
  <div class="risk-dashboard">
    <RiskMeter
      label="Daily Loss"
      :current="Math.abs(dailyPnL)"
      :limit="maxDailyLoss"
      :inverse="dailyPnL < 0"
      format="currency"
      :show-details="true"
    />
    
    <RiskMeter
      label="Position Size"
      :current="totalContracts"
      :limit="maxContracts"
      format="number"
      :show-remaining="true"
    />
  </div>
</template>
```

### Account Management
```vue
<template>
  <div class="account-management">
    <AccountSelector
      :accounts="allAccounts"
      :active-account="currentAccount"
      @account-changed="switchAccount"
    />
    
    <FundedAccountPanel
      v-if="currentAccount?.type === 'funded'"
      :active-account="currentAccount"
      @emergency-flatten="handleEmergencyClose"
    />
  </div>
</template>
```

## 🚀 Performance

### Bundle Analysis
- **Gzipped Size**: ~8kB
- **Tree Shaking**: Full support for unused component elimination
- **Code Splitting**: Components can be imported individually
- **Dependencies**: Minimal external dependencies

### Optimization Features
- **Lazy Loading**: Components support dynamic imports
- **Virtual Scrolling**: Large data sets handled efficiently
- **Memoization**: Expensive calculations cached appropriately
- **Animation Performance**: CSS transforms and GPU acceleration

## 🔄 Versioning

This library follows semantic versioning:
- **Major**: Breaking changes to component APIs
- **Minor**: New components or non-breaking feature additions
- **Patch**: Bug fixes and performance improvements

## 📚 Related Documentation

- [Web Application](../../apps/web/README.md)
- [Trading Backend](../../src/backend/README.md)
- [Component Design Guidelines](../../docs/developer/COMPONENT_GUIDELINES.md)
- [Development Workflow](../../docs/developer/DEVELOPMENT_WORKFLOW.md)

---

**Part of TraderTerminal**: Professional trading components for the $41/month Bloomberg Terminal alternative