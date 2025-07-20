// Vue Component Type Definitions for TraderTerminal UI

import type { DefineComponent } from 'vue'
import type {
  RiskMeterProps,
  AccountSelectorProps,
  FundedAccountPanelProps
} from './index'

// Component instance types
export type RiskMeterComponent = DefineComponent<RiskMeterProps>
export type AccountSelectorComponent = DefineComponent<AccountSelectorProps>
export type FundedAccountPanelComponent = DefineComponent<FundedAccountPanelProps>

// Event payload types for Vue emit
export interface RiskMeterEvents {
  'threshold-exceeded': { value: number; threshold: number }
  'critical-level-reached': { value: number }
}

export interface AccountSelectorEvents {
  'account-changed': string
  'show-violations': void
  'show-details': void
  'positions-flattened': void
}

export interface FundedAccountPanelEvents {
  'account-changed': string
  'positions-flattened': void
  'toggle-realtime': void
  'refresh-all': void
  'refresh-account': void
  'fetch-accounts': void
  'emergency-flatten': void
}

// Vue component props with default values
export interface ComponentDefaults {
  RiskMeter: {
    inverse: boolean
    showThreshold: boolean
    thresholdValue: number
    thresholdLabel: string
    showRemaining: boolean
    showDetails: boolean
    format: 'currency' | 'percentage' | 'number'
  }
  
  AccountSelector: {
    accounts: any[]
    loading: boolean
    groupedAccounts: any[]
    selectedAccountId: string
  }
  
  FundedAccountPanel: {
    accounts: any[]
    loading: boolean
    refreshing: boolean
    realtimeEnabled: boolean
    groupedAccounts: any[]
    selectedAccountId: string
    activeViolations: any[]
  }
}

// Component slot types
export interface ComponentSlots {
  RiskMeter: {
    default?: any
    threshold?: any
    details?: any
  }
  
  AccountSelector: {
    default?: any
    'no-accounts'?: any
    'account-actions'?: any
  }
  
  FundedAccountPanel: {
    default?: any
    header?: any
    'custom-metrics'?: any
    'custom-actions'?: any
    footer?: any
  }
}