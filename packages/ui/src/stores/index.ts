// Shared Pinia stores for TraderTerminal UI components

// Trade Journal Store
export { useTradeNoteStore } from './tradenote'

// Paper Trading Store
export { usePaperTradingStore } from './paperTrading'

// Strategy Performance Store
export { useStrategyPerformanceStore } from './strategyPerformance'

// Trading Store
export { useTradingStore } from './trading'

// Export types
export type { Account, Position, Quote, Order, OrderRequest } from './trading'
export type { 
  StrategyMetrics, 
  TradeResult, 
  SetResult, 
  TransitionEvent, 
  StrategyRegistration, 
  StrategyModeChangeRequest, 
  TradingMode 
} from './strategyPerformance'
export type { PaperAccount, PaperTrade, PerformanceMetrics } from './paperTrading'
export type { TradeJournalEntry, CalendarData } from './tradenote'

// Placeholder for additional stores
export const useTraderTerminalStores = () => {
  console.log('TraderTerminal UI stores placeholder')
}