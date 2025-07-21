"""
Strategy Performance Tracker

Real-time strategy performance tracking with auto-rotation logic.
Monitors strategy performance, enforces risk rules, and automatically
disables underperforming strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from .strategy_models import (
    StrategyPerformance, TradeRecord, StrategyConfiguration,
    StrategyRotationRule, StrategyPortfolio, StrategyStatus,
    TradingMode, PerformanceMetric
)

logger = logging.getLogger(__name__)


class StrategyPerformanceTracker:
    """
    Real-time strategy performance tracking and auto-rotation system.
    
    Features:
    - Real-time performance metric calculation
    - Automatic strategy rotation based on performance
    - Risk management and position sizing
    - Portfolio-level risk monitoring
    - Integration with trading systems
    """
    
    def __init__(self):
        self.strategies: Dict[str, StrategyPerformance] = {}
        self.configurations: Dict[str, StrategyConfiguration] = {}
        self.portfolios: Dict[str, StrategyPortfolio] = {}
        self.trade_records: Dict[str, TradeRecord] = {}
        
        # Monitoring settings
        self.monitoring_enabled = True
        self.check_interval = timedelta(minutes=5)
        self.last_check = datetime.utcnow()
        
        # Performance thresholds
        self.default_auto_disable_rules = {
            "max_drawdown": 1000.0,        # $1000 max drawdown
            "max_consecutive_losses": 5,    # 5 consecutive losses
            "min_win_rate": 0.25,          # 25% minimum win rate
            "min_profit_factor": 0.8       # 0.8 minimum profit factor
        }
        
        self._initialized = False
        
    async def initialize(self):
        """Initialize the strategy tracker"""
        if self._initialized:
            return
        
        try:
            # Create default portfolio
            default_portfolio = StrategyPortfolio(
                portfolio_name="default",
                portfolio_max_drawdown=Decimal("10000"),
                max_concurrent_strategies=10
            )
            self.portfolios["default"] = default_portfolio
            
            # Start monitoring task
            if self.monitoring_enabled:
                asyncio.create_task(self._monitoring_loop())
            
            self._initialized = True
            logger.info("Strategy performance tracker initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy tracker: {e}")
            raise
    
    async def register_strategy(
        self,
        strategy_name: str,
        configuration: Optional[StrategyConfiguration] = None,
        portfolio_name: str = "default"
    ) -> StrategyPerformance:
        """
        Register a new strategy for tracking.
        
        Args:
            strategy_name: Unique strategy identifier
            configuration: Strategy configuration (optional)
            portfolio_name: Portfolio to add strategy to
            
        Returns:
            StrategyPerformance: Initialized strategy performance object
        """
        if strategy_name in self.strategies:
            logger.warning(f"Strategy {strategy_name} already registered")
            return self.strategies[strategy_name]
        
        # Create configuration if not provided
        if not configuration:
            configuration = StrategyConfiguration(
                strategy_name=strategy_name,
                trading_mode=TradingMode.PAPER,
                auto_rotation_enabled=True
            )
        
        # Create performance tracker
        performance = StrategyPerformance.create_with_default_rules(
            strategy_name=strategy_name,
            trading_mode=configuration.trading_mode
        )
        
        # Apply custom auto-disable rules if provided
        if hasattr(configuration, 'auto_disable_rules'):
            performance.auto_disable_rules.update(configuration.auto_disable_rules)
        else:
            performance.auto_disable_rules = self.default_auto_disable_rules.copy()
        
        # Store strategy
        self.strategies[strategy_name] = performance
        self.configurations[strategy_name] = configuration
        
        # Add to portfolio
        if portfolio_name in self.portfolios:
            self.portfolios[portfolio_name].add_strategy(performance)
        
        logger.info(f"Registered strategy: {strategy_name} in portfolio {portfolio_name}")
        return performance
    
    async def record_trade_execution(
        self,
        strategy_name: str,
        symbol: str,
        side: str,
        quantity: int,
        pnl: float,
        entry_price: float = None,
        exit_price: float = None,
        commission: float = 0.0,
        fees: float = 0.0,
        trading_mode: TradingMode = TradingMode.PAPER,
        account_id: Optional[str] = None,
        broker: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Record a completed trade execution for strategy tracking.
        
        Args:
            strategy_name: Strategy that generated the trade
            symbol: Trading symbol
            side: buy or sell
            quantity: Quantity traded
            pnl: Realized P&L from trade
            entry_price: Entry price (if known)
            exit_price: Exit price (if known)
            commission: Commission paid
            fees: Other fees
            trading_mode: Live, paper, or simulation
            account_id: Account used
            broker: Broker used
            notes: Additional notes
            
        Returns:
            str: Trade record ID
        """
        # Auto-register strategy if not exists
        if strategy_name not in self.strategies:
            await self.register_strategy(strategy_name)
        
        # Create trade record
        trade_id = f"{strategy_name}_{uuid.uuid4().hex[:8]}"
        
        trade_record = TradeRecord(
            trade_id=trade_id,
            strategy_name=strategy_name,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=Decimal(str(entry_price or 0)),
            exit_price=Decimal(str(exit_price or 0)),
            entry_time=datetime.utcnow(),
            exit_time=datetime.utcnow(),  # Assume completed trade
            realized_pnl=Decimal(str(pnl)),
            commission=Decimal(str(commission)),
            fees=Decimal(str(fees)),
            trading_mode=trading_mode,
            account_id=account_id,
            broker=broker,
            notes=notes
        )
        
        # Store trade record
        self.trade_records[trade_id] = trade_record
        
        # Update strategy performance
        performance = self.strategies[strategy_name]
        performance.update_from_trade(trade_record)
        
        logger.info(f"Recorded trade for {strategy_name}: {symbol} {side} {quantity} P&L=${pnl}")
        
        # Check if strategy should be auto-disabled
        if performance.current_status == StrategyStatus.AUTO_DISABLED:
            await self._handle_strategy_auto_disable(strategy_name, performance)
        
        return trade_id
    
    async def get_strategy_performance(self, strategy_name: str) -> Optional[StrategyPerformance]:
        """Get current performance metrics for a strategy"""
        return self.strategies.get(strategy_name)
    
    async def get_all_strategies(self) -> Dict[str, StrategyPerformance]:
        """Get all strategy performance data"""
        return self.strategies.copy()
    
    async def get_active_strategies(self) -> Dict[str, StrategyPerformance]:
        """Get all active strategies"""
        return {
            name: perf for name, perf in self.strategies.items()
            if perf.current_status == StrategyStatus.ACTIVE
        }
    
    async def disable_strategy(self, strategy_name: str, reason: str = "Manual disable") -> bool:
        """
        Manually disable a strategy.
        
        Args:
            strategy_name: Strategy to disable
            reason: Reason for disabling
            
        Returns:
            bool: Success status
        """
        if strategy_name not in self.strategies:
            return False
        
        performance = self.strategies[strategy_name]
        performance.current_status = StrategyStatus.STOPPED
        
        logger.warning(f"Strategy {strategy_name} disabled: {reason}")
        return True
    
    async def enable_strategy(self, strategy_name: str) -> bool:
        """
        Re-enable a disabled strategy.
        
        Args:
            strategy_name: Strategy to enable
            
        Returns:
            bool: Success status
        """
        if strategy_name not in self.strategies:
            return False
        
        performance = self.strategies[strategy_name]
        
        # Check if strategy meets criteria for re-enabling
        if await self._can_enable_strategy(performance):
            performance.current_status = StrategyStatus.ACTIVE
            logger.info(f"Strategy {strategy_name} re-enabled")
            return True
        else:
            logger.warning(f"Strategy {strategy_name} cannot be re-enabled - performance criteria not met")
            return False
    
    async def get_portfolio_summary(self, portfolio_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get portfolio-level performance summary.
        
        Args:
            portfolio_name: Portfolio to summarize
            
        Returns:
            Dict[str, Any]: Portfolio summary
        """
        if portfolio_name not in self.portfolios:
            return None
        
        portfolio = self.portfolios[portfolio_name]
        active_strategies = portfolio.get_active_strategies()
        
        return {
            "portfolio_name": portfolio_name,
            "total_strategies": len(portfolio.strategies),
            "active_strategies": len(active_strategies),
            "total_pnl": float(portfolio.total_portfolio_pnl),
            "portfolio_drawdown": float(portfolio.portfolio_drawdown),
            "strategies": {
                name: {
                    "status": strategy.current_status.value,
                    "total_pnl": float(strategy.total_pnl),
                    "win_rate": strategy.win_rate,
                    "total_trades": strategy.total_trades,
                    "current_drawdown": float(strategy.current_drawdown)
                }
                for name, strategy in portfolio.strategies.items()
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def check_rotation_rules(self, portfolio_name: str = "default") -> List[Dict[str, Any]]:
        """
        Check portfolio rotation rules and return suggested actions.
        
        Args:
            portfolio_name: Portfolio to check
            
        Returns:
            List[Dict[str, Any]]: List of suggested rotation actions
        """
        if portfolio_name not in self.portfolios:
            return []
        
        portfolio = self.portfolios[portfolio_name]
        return portfolio.check_rotation_rules()
    
    async def get_strategy_metrics(self, strategy_name: str) -> Optional[Dict[str, PerformanceMetric]]:
        """
        Get detailed performance metrics for a strategy.
        
        Args:
            strategy_name: Strategy to get metrics for
            
        Returns:
            Dict[str, PerformanceMetric]: Performance metrics
        """
        if strategy_name not in self.strategies:
            return None
        
        return self.strategies[strategy_name].get_current_metrics()
    
    async def get_trade_history(
        self,
        strategy_name: Optional[str] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TradeRecord]:
        """
        Get trade history with optional filtering.
        
        Args:
            strategy_name: Filter by strategy (optional)
            limit: Maximum number of trades to return
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            List[TradeRecord]: Filtered trade records
        """
        trades = list(self.trade_records.values())
        
        # Apply filters
        if strategy_name:
            trades = [t for t in trades if t.strategy_name == strategy_name]
        
        if start_date:
            trades = [t for t in trades if t.entry_time >= start_date]
        
        if end_date:
            trades = [t for t in trades if t.entry_time <= end_date]
        
        # Sort by entry time (newest first)
        trades.sort(key=lambda t: t.entry_time, reverse=True)
        
        return trades[:limit]
    
    async def _monitoring_loop(self):
        """Background monitoring loop for strategy performance"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(self.check_interval.total_seconds())
                await self._perform_monitoring_check()
            except Exception as e:
                logger.error(f"Error in strategy monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_monitoring_check(self):
        """Perform periodic monitoring checks"""
        current_time = datetime.utcnow()
        
        # Check each portfolio
        for portfolio_name, portfolio in self.portfolios.items():
            # Check rotation rules
            actions = await self.check_rotation_rules(portfolio_name)
            
            for action in actions:
                await self._execute_rotation_action(action)
        
        self.last_check = current_time
        logger.debug(f"Completed monitoring check for {len(self.strategies)} strategies")
    
    async def _execute_rotation_action(self, action: Dict[str, Any]):
        """Execute a rotation action"""
        strategy_name = action["strategy_name"]
        action_type = action["action"]
        
        if action_type == "disable":
            await self.disable_strategy(strategy_name, f"Auto-rotation: {action['rule_name']}")
        elif action_type == "pause":
            if strategy_name in self.strategies:
                self.strategies[strategy_name].current_status = StrategyStatus.PAUSED
        elif action_type == "reduce_size":
            # Reduce position size (would integrate with position sizing logic)
            logger.info(f"Reducing position size for {strategy_name}")
        
        logger.info(f"Executed rotation action: {action_type} for {strategy_name}")
    
    async def _handle_strategy_auto_disable(self, strategy_name: str, performance: StrategyPerformance):
        """Handle strategy auto-disable event"""
        # Log the auto-disable
        logger.warning(f"Strategy {strategy_name} auto-disabled due to performance rules")
        
        # Could trigger notifications, close positions, etc.
        # For now, just log the event
        
        # Update configuration to prevent immediate re-enabling
        if strategy_name in self.configurations:
            config = self.configurations[strategy_name]
            config.enabled = False
    
    async def _can_enable_strategy(self, performance: StrategyPerformance) -> bool:
        """Check if a strategy meets criteria for re-enabling"""
        # For now, use simple criteria
        # In practice, might require manual review or cooling-off period
        
        if performance.total_trades < 5:
            return True  # Allow new strategies
        
        # Check if performance has improved
        metrics = performance.get_current_metrics()
        
        win_rate_ok = metrics["win_rate"].value >= 0.4  # Higher threshold for re-enabling
        drawdown_ok = metrics["current_drawdown"].value < 500  # Lower drawdown required
        
        return win_rate_ok and drawdown_ok
    
    async def close(self):
        """Close the strategy tracker"""
        self.monitoring_enabled = False
        logger.info("Strategy performance tracker closed")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get overall summary statistics"""
        total_strategies = len(self.strategies)
        active_strategies = len([s for s in self.strategies.values() if s.current_status == StrategyStatus.ACTIVE])
        total_trades = sum(s.total_trades for s in self.strategies.values())
        total_pnl = sum(s.total_pnl for s in self.strategies.values())
        
        return {
            "total_strategies": total_strategies,
            "active_strategies": active_strategies,
            "disabled_strategies": total_strategies - active_strategies,
            "total_trades": total_trades,
            "total_pnl": float(total_pnl),
            "avg_pnl_per_strategy": float(total_pnl / total_strategies) if total_strategies > 0 else 0,
            "last_monitoring_check": self.last_check.isoformat(),
            "monitoring_enabled": self.monitoring_enabled
        }