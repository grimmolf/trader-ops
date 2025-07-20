"""
Strategy Performance Tracker for TraderTerminal

Implements automated strategy performance tracking and management,
including auto-rotation between live and paper trading based on performance metrics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timezone
from collections import defaultdict
from decimal import Decimal

from .models import (
    StrategyPerformance, StrategySet, TradeResult, TradingMode,
    ModeTransition, StrategyRegistration, StrategyPerformanceSummary
)

logger = logging.getLogger(__name__)


class StrategyPerformanceTracker:
    """Track and evaluate strategy performance across live and paper trading"""
    
    def __init__(self):
        self.strategies: Dict[str, StrategyPerformance] = {}
        self.active_trades: Dict[str, TradeResult] = {}  # trade_id -> TradeResult
        self.mode_change_callbacks: List[Callable] = []
        self._initialized = False
        
        # Performance tracking
        self.performance_alerts: List[Dict[str, Any]] = []
        self.daily_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
    async def initialize(self) -> None:
        """Initialize the strategy performance tracker"""
        if self._initialized:
            return
            
        try:
            # Load existing strategies from storage if available
            # For now, we'll start fresh, but this could be extended to load from database
            logger.info("Strategy performance tracker initialized")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy performance tracker: {e}")
            raise
    
    async def register_strategy(
        self, 
        strategy_id: str, 
        strategy_name: str,
        min_win_rate: Decimal = Decimal("55.0"),
        evaluation_period: int = 20,
        initial_mode: TradingMode = TradingMode.LIVE
    ) -> StrategyPerformance:
        """Register a new strategy for tracking"""
        
        if strategy_id in self.strategies:
            logger.info(f"Strategy {strategy_id} already registered, returning existing")
            return self.strategies[strategy_id]
        
        # Create initial strategy set
        initial_set = StrategySet(
            set_number=1,
            strategy_id=strategy_id,
            mode=initial_mode,
            evaluation_threshold=evaluation_period
        )
        
        # Create strategy performance tracker
        strategy = StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            current_mode=initial_mode,
            current_set=initial_set,
            min_win_rate=min_win_rate,
            evaluation_period=evaluation_period
        )
        
        self.strategies[strategy_id] = strategy
        
        logger.info(
            f"Registered strategy '{strategy_name}' (ID: {strategy_id}) "
            f"with {min_win_rate}% min win rate, {evaluation_period} trade evaluation period"
        )
        
        return strategy
    
    async def record_trade(
        self,
        strategy_id: str,
        symbol: str,
        entry_price: Decimal,
        exit_price: Decimal,
        quantity: int,
        side: str,
        commission: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
        trade_id: Optional[str] = None
    ) -> Optional[ModeTransition]:
        """
        Record a completed trade and evaluate for mode transitions.
        Returns ModeTransition if a mode change occurred.
        """
        
        if strategy_id not in self.strategies:
            logger.warning(f"Trade recorded for unregistered strategy: {strategy_id}")
            return None
        
        strategy = self.strategies[strategy_id]
        
        # Calculate P&L
        if side.lower() in ["long", "buy"]:
            pnl = (exit_price - entry_price) * quantity
        else:  # short/sell
            pnl = (entry_price - exit_price) * quantity
        
        # Determine if trade was a winner
        win = pnl > 0
        
        # Create trade result
        trade = TradeResult(
            strategy_id=strategy_id,
            trade_id=trade_id or f"{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbol=symbol,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            side=side.lower(),
            pnl=pnl,
            win=win,
            mode=strategy.current_mode,
            set_number=strategy.current_set.set_number,
            trade_number_in_set=len(strategy.current_set.trades) + 1,
            commission=commission,
            slippage=slippage
        )
        
        logger.info(
            f"Recording trade for strategy '{strategy.strategy_name}': "
            f"{symbol} {side} {quantity} @ {entry_price}->{exit_price} "
            f"P&L: {pnl} ({'WIN' if win else 'LOSS'})"
        )
        
        # Add trade to strategy
        set_completed = strategy.add_trade(trade)
        
        # Check for mode transitions if set was completed
        mode_transition = None
        if set_completed:
            mode_transition = await self._evaluate_strategy_performance(strategy)
        
        # Store active trade for potential callbacks
        self.active_trades[trade.trade_id] = trade
        
        return mode_transition
    
    async def _evaluate_strategy_performance(self, strategy: StrategyPerformance) -> Optional[ModeTransition]:
        """Evaluate strategy performance and trigger mode changes if needed"""
        
        completed_set = strategy.completed_sets[-1]  # Most recently completed set
        
        logger.info(
            f"Evaluating strategy '{strategy.strategy_name}' set {completed_set.set_number}: "
            f"Win Rate: {completed_set.win_rate}% "
            f"(Threshold: {strategy.min_win_rate}%) "
            f"P&L: {completed_set.total_pnl} "
            f"Mode: {strategy.current_mode}"
        )
        
        # Check for transition from LIVE to PAPER
        if strategy.current_mode == TradingMode.LIVE and strategy.is_at_risk:
            return await self._transition_to_paper(strategy)
        
        # Check for transition from PAPER to LIVE
        elif strategy.current_mode == TradingMode.PAPER and strategy.can_return_to_live:
            return await self._transition_to_live(strategy)
        
        return None
    
    async def _transition_to_paper(self, strategy: StrategyPerformance) -> ModeTransition:
        """Transition strategy to paper trading"""
        
        recent_sets = strategy.completed_sets[-strategy.consecutive_failures_threshold:]
        recent_win_rates = [s.win_rate for s in recent_sets]
        
        reason = (
            f"Performance below threshold. "
            f"Last {len(recent_sets)} sets win rates: {recent_win_rates} "
            f"(Required: {strategy.min_win_rate}%+)"
        )
        
        logger.warning(
            f"Strategy '{strategy.strategy_name}' moving to PAPER trading. "
            f"Reason: {reason}"
        )
        
        # Create transition
        transition = strategy.transition_mode(TradingMode.PAPER, reason)
        
        # Create performance alert
        alert = {
            "type": "strategy_mode_change",
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.strategy_name,
            "from_mode": "live",
            "to_mode": "paper",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc),
            "recent_performance": recent_win_rates
        }
        self.performance_alerts.append(alert)
        
        # Notify callbacks
        await self._notify_mode_change(strategy, TradingMode.PAPER, transition)
        
        return transition
    
    async def _transition_to_live(self, strategy: StrategyPerformance) -> ModeTransition:
        """Transition strategy back to live trading"""
        
        paper_sets = [s for s in strategy.completed_sets if s.mode == TradingMode.PAPER]
        recent_paper_sets = paper_sets[-strategy.consecutive_successes_threshold:]
        recent_win_rates = [s.win_rate for s in recent_paper_sets]
        
        reason = (
            f"Paper trading performance meets threshold. "
            f"Last {len(recent_paper_sets)} paper sets win rates: {recent_win_rates} "
            f"(Required: {strategy.min_win_rate}%+)"
        )
        
        logger.info(
            f"Strategy '{strategy.strategy_name}' returning to LIVE trading! "
            f"Reason: {reason}"
        )
        
        # Create transition
        transition = strategy.transition_mode(TradingMode.LIVE, reason)
        
        # Create performance alert
        alert = {
            "type": "strategy_mode_change",
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.strategy_name,
            "from_mode": "paper",
            "to_mode": "live",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc),
            "recent_performance": recent_win_rates
        }
        self.performance_alerts.append(alert)
        
        # Notify callbacks
        await self._notify_mode_change(strategy, TradingMode.LIVE, transition)
        
        return transition
    
    async def _notify_mode_change(
        self, 
        strategy: StrategyPerformance, 
        new_mode: TradingMode,
        transition: ModeTransition
    ):
        """Notify all callbacks about mode change"""
        for callback in self.mode_change_callbacks:
            try:
                await callback({
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.strategy_name,
                    "old_mode": transition.from_mode,
                    "new_mode": new_mode,
                    "transition": transition.dict(),
                    "strategy": strategy.dict()
                })
            except Exception as e:
                logger.error(f"Error in mode change callback: {e}")
    
    def add_mode_change_callback(self, callback: Callable) -> None:
        """Add a callback to be notified of mode changes"""
        self.mode_change_callbacks.append(callback)
    
    async def get_strategy(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """Get strategy by ID"""
        return self.strategies.get(strategy_id)
    
    async def get_all_strategies(self) -> List[StrategyPerformance]:
        """Get all registered strategies"""
        return list(self.strategies.values())
    
    async def get_strategy_summary(self, strategy_id: str) -> Optional[StrategyPerformanceSummary]:
        """Get strategy performance summary"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        last_trade_time = None
        if strategy.current_set.trades:
            last_trade_time = max(trade.timestamp for trade in strategy.current_set.trades)
        elif strategy.completed_sets:
            last_set = strategy.completed_sets[-1]
            if last_set.trades:
                last_trade_time = max(trade.timestamp for trade in last_set.trades)
        
        return StrategyPerformanceSummary(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name,
            current_mode=strategy.current_mode,
            current_set_progress=len(strategy.current_set.trades),
            current_set_win_rate=strategy.current_set.calculate_win_rate,
            overall_win_rate=strategy.overall_win_rate,
            total_sets_completed=len(strategy.completed_sets),
            recent_performance=strategy.recent_performance,
            is_at_risk=strategy.is_at_risk,
            can_return_to_live=strategy.can_return_to_live,
            lifetime_pnl=strategy.lifetime_pnl,
            lifetime_net_pnl=strategy.lifetime_net_pnl,
            last_trade_time=last_trade_time,
            last_updated=strategy.last_updated
        )
    
    async def get_all_strategy_summaries(self) -> List[StrategyPerformanceSummary]:
        """Get summaries for all strategies"""
        summaries = []
        for strategy_id in self.strategies:
            summary = await self.get_strategy_summary(strategy_id)
            if summary:
                summaries.append(summary)
        return summaries
    
    async def manually_change_mode(
        self, 
        strategy_id: str, 
        new_mode: TradingMode, 
        reason: str = "Manual override"
    ) -> Optional[ModeTransition]:
        """Manually change strategy mode"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        if strategy.current_mode == new_mode:
            logger.info(f"Strategy {strategy_id} already in {new_mode} mode")
            return None
        
        logger.info(
            f"Manually changing strategy '{strategy.strategy_name}' "
            f"from {strategy.current_mode} to {new_mode}. Reason: {reason}"
        )
        
        # Create transition
        transition = strategy.transition_mode(new_mode, reason)
        
        # Notify callbacks
        await self._notify_mode_change(strategy, new_mode, transition)
        
        return transition
    
    async def get_performance_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent performance alerts"""
        # Sort by timestamp descending and limit
        sorted_alerts = sorted(
            self.performance_alerts,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        return sorted_alerts[:limit]
    
    def clear_performance_alerts(self) -> None:
        """Clear all performance alerts"""
        self.performance_alerts.clear()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics"""
        total_strategies = len(self.strategies)
        live_strategies = sum(1 for s in self.strategies.values() if s.current_mode == TradingMode.LIVE)
        paper_strategies = sum(1 for s in self.strategies.values() if s.current_mode == TradingMode.PAPER)
        suspended_strategies = sum(1 for s in self.strategies.values() if s.current_mode == TradingMode.SUSPENDED)
        
        at_risk_strategies = sum(1 for s in self.strategies.values() if s.is_at_risk)
        can_return_strategies = sum(1 for s in self.strategies.values() if s.can_return_to_live)
        
        total_completed_sets = sum(len(s.completed_sets) for s in self.strategies.values())
        total_trades = sum(s.total_trades for s in self.strategies.values())
        
        return {
            "initialized": self._initialized,
            "total_strategies": total_strategies,
            "live_strategies": live_strategies,
            "paper_strategies": paper_strategies,
            "suspended_strategies": suspended_strategies,
            "at_risk_strategies": at_risk_strategies,
            "can_return_strategies": can_return_strategies,
            "total_completed_sets": total_completed_sets,
            "total_trades": total_trades,
            "recent_alerts": len(self.performance_alerts),
            "timestamp": datetime.now(timezone.utc)
        }


# Global strategy performance tracker instance
_strategy_tracker: Optional[StrategyPerformanceTracker] = None


def get_strategy_tracker() -> StrategyPerformanceTracker:
    """Get the global strategy performance tracker instance"""
    global _strategy_tracker
    if _strategy_tracker is None:
        _strategy_tracker = StrategyPerformanceTracker()
    return _strategy_tracker


async def initialize_strategy_tracker() -> StrategyPerformanceTracker:
    """Initialize and return the global strategy tracker"""
    tracker = get_strategy_tracker()
    await tracker.initialize()
    return tracker