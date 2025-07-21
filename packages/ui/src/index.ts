// Main entry point for @trader-terminal/ui shared component library

// Core Trading Components
export { default as TradingDashboard } from './components/TradingDashboard.vue'
export { default as OrderEntry } from './components/OrderEntry.vue'
export { default as MultiBrokerOrderEntry } from './components/MultiBrokerOrderEntry.vue'
export { default as Watchlist } from './components/Watchlist.vue'
export { default as Positions } from './components/Positions.vue'
export { default as OrderHistory } from './components/OrderHistory.vue'
export { default as TradingViewChart } from './components/TradingViewChart.vue'

// Account & Risk Management
export { default as AccountInfo } from './components/AccountInfo.vue'
export { default as AccountSelector } from './components/AccountSelector.vue'
export { default as FundedAccountPanel } from './components/FundedAccountPanel.vue'
export { default as RiskMeter } from './components/RiskMeter.vue'

// Analysis & Strategy
export { default as BacktestPanel } from './components/BacktestPanel.vue'
export { default as PaperTradingPanel } from './components/PaperTradingPanel.vue'
export { default as StrategyPerformancePanel } from './components/StrategyPerformancePanel.vue'

// Trade Journaling (TradeNote Integration)
export { default as TradeNotePanel } from './components/TradeNotePanel.vue'
export { default as TradeNoteCalendar } from './components/TradeNoteCalendar.vue'
export { default as TradeNoteAnalytics } from './components/TradeNoteAnalytics.vue'

// Utilities & UI
export { default as SymbolSearch } from './components/SymbolSearch.vue'
export { default as AlertPanel } from './components/AlertPanel.vue'
export { default as NewsFeed } from './components/NewsFeed.vue'

// Types
export * from './types'

// Composables
export * from './composables'

// Stores
export * from './stores'