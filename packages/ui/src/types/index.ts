// Core Trading Types for TraderTerminal UI Components

export interface TradingAccount {
  id: string
  accountNumber: string
  name: string
  platform: string
  accountType: string
  phase: 'evaluation' | 'funded' | 'scaling'
  status: 'active' | 'suspended' | 'passed' | 'failed'
  size: number
  currentBalance: number
  isConnected: boolean
  createdAt: string
  lastUpdated: string
  lastTradeDate?: string
  evaluationEndDate?: string
  
  metrics: AccountMetrics
  rules: AccountRules
  violations: RuleViolation[]
}

export interface AccountMetrics {
  dailyPnL: number
  totalPnL: number
  currentDrawdown: number
  totalContracts: number
  openPositions: number
  totalTrades: number
  winRate: number
  profitFactor: number
  tradingDays: number
}

export interface AccountRules {
  maxDailyLoss: number
  trailingDrawdown: number
  maxContracts: number
  profitTarget: number
  minTradingDays: number
  allowOvernightPositions: boolean
  allowNewsTrading: boolean
  restrictedSymbols: string[]
}

export interface RuleViolation {
  id: string
  type: string
  message: string
  triggeredAt: string
  ruleLimit: number
  actualValue: number
  resolved: boolean
}

export interface GroupedAccounts {
  name: string
  accounts: TradingAccount[]
}

export interface Position {
  id: string
  symbol: string
  accountNumber: string
  feed: string
  quantity: number
  averagePrice: number
  marketValue: number
  unrealizedPnL: number
  side: 'long' | 'short'
  entryTime: string
}

export interface Order {
  id: string
  symbol: string
  accountNumber: string
  feed: string
  side: 'buy' | 'sell'
  quantity: number
  orderType: 'market' | 'limit' | 'stop' | 'stopLimit'
  price?: number
  stopPrice?: number
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  timeInForce: 'day' | 'gtc' | 'ioc' | 'fok'
  createdAt: string
  updatedAt: string
}

// Risk Management Types
export interface RiskMetrics {
  label: string
  current: number
  limit: number
  inverse?: boolean
  showThreshold?: boolean
  thresholdValue?: number
  thresholdLabel?: string
  showRemaining?: boolean
  showDetails?: boolean
  timeToLimit?: number
  format?: 'currency' | 'percentage' | 'number'
}

// UI Component Props Types
export interface RiskMeterProps extends RiskMetrics {}

export interface AccountSelectorProps {
  accounts?: TradingAccount[]
  activeAccount?: TradingAccount
  loading?: boolean
  groupedAccounts?: GroupedAccounts[]
  selectedAccountId?: string
}

export interface FundedAccountPanelProps {
  accounts?: TradingAccount[]
  activeAccount?: TradingAccount
  loading?: boolean
  refreshing?: boolean
  realtimeEnabled?: boolean
  groupedAccounts?: GroupedAccounts[]
  selectedAccountId?: string
  activeViolations?: RuleViolation[]
}

// Event Types
export interface AccountChangedEvent {
  accountId: string
}

export interface EmergencyFlattenEvent {
  accountId: string
  timestamp: string
}

// Common utility types
export type SeverityLevel = 'safe' | 'caution' | 'warning' | 'danger' | 'critical'
export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error'
export type DataFeed = 'tradovate' | 'tastytrade' | 'schwab' | 'topstepx'

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
}

export interface FundedAccountsResponse extends ApiResponse {
  data: TradingAccount[]
}

export interface PositionsResponse extends ApiResponse {
  data: Position[]
}

export interface OrdersResponse extends ApiResponse {
  data: Order[]
}

// WebSocket Event Types
export interface WebSocketEvent {
  type: string
  data: any
  timestamp: string
}

export interface AccountUpdateEvent extends WebSocketEvent {
  type: 'account_update'
  data: TradingAccount
}

export interface PositionUpdateEvent extends WebSocketEvent {
  type: 'position_update'
  data: Position
}

export interface RiskAlertEvent extends WebSocketEvent {
  type: 'risk_alert'
  data: RuleViolation
}

// Export all types for consumption
export * from './vue-components'