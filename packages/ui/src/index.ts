// Main entry point for @trader-terminal/ui shared component library

// Core Components (available now)
export { default as RiskMeter } from './components/RiskMeter.vue'
export { default as AccountSelector } from './components/AccountSelector.vue'
export { default as FundedAccountPanel } from './components/FundedAccountPanel.vue'

// Types
export * from './types'

// Composables (placeholder)
export * from './composables'

// Stores (placeholder)
export * from './stores'

// TODO: Additional components will be added as they are extracted:
// - OrderEntry, MultiBrokerOrderEntry, TradingDashboard
// - Positions, OrderHistory, AccountInfo
// - Watchlist, SymbolSearch, NewsFeed, AlertPanel  
// - BacktestPanel, PaperTradingPanel, StrategyPerformancePanel
// - TradeNotePanel, TradeNoteCalendar, TradeNoteAnalytics
// - TradingViewChart