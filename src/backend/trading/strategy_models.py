"""
Strategy Performance Models

Pydantic models for tracking strategy performance, auto-rotation logic,
and real-time performance monitoring for algorithmic trading strategies.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy operational status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    MONITORING = "monitoring"
    AUTO_DISABLED = "auto_disabled"


class TradingMode(Enum):
    """Strategy trading mode"""
    LIVE = "live"
    PAPER = "paper"
    SIMULATION = "simulation"
    BACKTEST = "backtest"


class PerformanceMetric(BaseModel):
    """Individual performance metric"""
    
    name: str = Field(description="Metric name")
    value: float = Field(description="Current metric value")
    threshold: Optional[float] = Field(None, description="Threshold for alerts")
    direction: str = Field(default="higher_better", description="higher_better or lower_better")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_breached(self) -> bool:
        """Check if metric has breached threshold"""
        if not self.threshold:
            return False
        
        if self.direction == "higher_better":
            return self.value < self.threshold
        else:
            return self.value > self.threshold


class TradeRecord(BaseModel):
    """Individual trade record for strategy tracking"""
    
    trade_id: str = Field(description="Unique trade identifier")
    strategy_name: str = Field(description="Strategy that generated trade")
    
    # Trade details
    symbol: str = Field(description="Trading symbol")
    side: str = Field(description="buy or sell")
    quantity: int = Field(description="Quantity traded")
    entry_price: Decimal = Field(description="Entry price")
    exit_price: Optional[Decimal] = Field(None, description="Exit price")
    
    # Timing
    entry_time: datetime = Field(description="Trade entry time")
    exit_time: Optional[datetime] = Field(None, description="Trade exit time")
    holding_period: Optional[timedelta] = Field(None, description="Time held")
    
    # P&L
    realized_pnl: Optional[Decimal] = Field(None, description="Realized P&L")
    unrealized_pnl: Optional[Decimal] = Field(None, description="Current unrealized P&L")
    commission: Decimal = Field(default=Decimal("0"), description="Commission paid")
    fees: Decimal = Field(default=Decimal("0"), description="Other fees")
    
    # Context
    trading_mode: TradingMode = Field(description="Live, paper, or simulation")
    account_id: Optional[str] = Field(None, description="Account used for trade")
    broker: Optional[str] = Field(None, description="Broker used")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Trade tags")
    notes: Optional[str] = Field(None, description="Trade notes")
    
    @property
    def is_open(self) -> bool:
        """Check if trade is still open"""
        return self.exit_time is None
    
    @property
    def total_pnl(self) -> Decimal:
        """Get total P&L including costs"""
        base_pnl = self.realized_pnl or self.unrealized_pnl or Decimal("0")
        return base_pnl - self.commission - self.fees
    
    @property
    def is_winner(self) -> bool:
        """Check if trade is profitable"""
        return self.total_pnl > 0
    
    def close_trade(self, exit_price: Decimal, exit_time: datetime = None):
        """Close the trade and calculate final P&L"""
        if self.is_open:
            self.exit_price = exit_price
            self.exit_time = exit_time or datetime.utcnow()
            self.holding_period = self.exit_time - self.entry_time
            
            # Calculate realized P&L
            price_diff = exit_price - self.entry_price
            if self.side.lower() == "sell":
                price_diff = -price_diff
            
            self.realized_pnl = price_diff * self.quantity
            self.unrealized_pnl = None


class StrategyPerformance(BaseModel):
    """Comprehensive strategy performance metrics"""
    
    strategy_name: str = Field(description="Strategy identifier")
    
    # Basic statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L metrics
    total_pnl: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")
    gross_loss: Decimal = Decimal("0")
    max_win: Decimal = Decimal("0")
    max_loss: Decimal = Decimal("0")
    
    # Performance ratios
    win_rate: float = 0.0
    profit_factor: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    
    # Drawdown tracking
    max_drawdown: Decimal = Decimal("0")
    current_drawdown: Decimal = Decimal("0")
    drawdown_duration: Optional[timedelta] = None
    
    # Consistency metrics
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Time-based metrics
    avg_trade_duration: Optional[timedelta] = None
    total_trading_time: timedelta = timedelta()
    first_trade_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None
    
    # Current state
    current_status: StrategyStatus = StrategyStatus.ACTIVE
    current_mode: TradingMode = TradingMode.PAPER
    
    # Performance tracking
    daily_pnl_history: List[Decimal] = Field(default_factory=list)
    equity_curve: List[Decimal] = Field(default_factory=list)
    
    # Auto-rotation triggers
    auto_disable_rules: Dict[str, float] = Field(default_factory=dict)
    last_performance_check: datetime = Field(default_factory=datetime.utcnow)
    
    def update_from_trade(self, trade: TradeRecord):
        """Update performance metrics from a completed trade"""
        if trade.is_open:
            return  # Only process completed trades
        
        self.total_trades += 1
        self.last_trade_time = trade.exit_time
        
        if not self.first_trade_time:
            self.first_trade_time = trade.entry_time
        
        # Update P&L
        trade_pnl = trade.total_pnl
        self.total_pnl += trade_pnl
        
        # Track wins/losses
        if trade.is_winner:
            self.winning_trades += 1
            self.gross_profit += trade_pnl
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.max_consecutive_wins = max(self.max_consecutive_wins, self.consecutive_wins)
            
            if trade_pnl > self.max_win:
                self.max_win = trade_pnl
        else:
            self.losing_trades += 1
            self.gross_loss += abs(trade_pnl)
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)
            
            if trade_pnl < self.max_loss:
                self.max_loss = trade_pnl
        
        # Recalculate metrics
        self._recalculate_metrics()
        
        # Update equity curve
        self.equity_curve.append(self.total_pnl)
        
        # Check auto-disable rules
        self._check_auto_disable_rules()
    
    def _recalculate_metrics(self):
        """Recalculate derived performance metrics"""
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        
        if self.gross_loss > 0:
            self.profit_factor = float(self.gross_profit / self.gross_loss)
        
        # Update drawdown
        if len(self.equity_curve) > 0:
            peak = max(self.equity_curve)
            current = self.equity_curve[-1]
            self.current_drawdown = max(Decimal("0"), peak - current)
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
    
    def _check_auto_disable_rules(self):
        """Check if strategy should be auto-disabled"""
        rules_breached = []
        
        # Check each auto-disable rule
        for rule_name, threshold in self.auto_disable_rules.items():
            if rule_name == "max_drawdown" and float(self.current_drawdown) > threshold:
                rules_breached.append(f"Drawdown {self.current_drawdown} > {threshold}")
            elif rule_name == "max_consecutive_losses" and self.consecutive_losses > threshold:
                rules_breached.append(f"Consecutive losses {self.consecutive_losses} > {threshold}")
            elif rule_name == "min_win_rate" and self.win_rate < threshold:
                rules_breached.append(f"Win rate {self.win_rate:.2%} < {threshold:.2%}")
            elif rule_name == "min_profit_factor" and self.profit_factor and self.profit_factor < threshold:
                rules_breached.append(f"Profit factor {self.profit_factor:.2f} < {threshold}")
        
        if rules_breached and self.current_status == StrategyStatus.ACTIVE:
            self.current_status = StrategyStatus.AUTO_DISABLED
            logger.warning(f"Strategy {self.strategy_name} auto-disabled: {', '.join(rules_breached)}")
    
    def get_current_metrics(self) -> Dict[str, PerformanceMetric]:
        """Get current performance metrics as PerformanceMetric objects"""
        return {
            "win_rate": PerformanceMetric(
                name="win_rate",
                value=self.win_rate,
                threshold=self.auto_disable_rules.get("min_win_rate"),
                direction="higher_better"
            ),
            "profit_factor": PerformanceMetric(
                name="profit_factor",
                value=self.profit_factor or 0.0,
                threshold=self.auto_disable_rules.get("min_profit_factor"),
                direction="higher_better"
            ),
            "current_drawdown": PerformanceMetric(
                name="current_drawdown",
                value=float(self.current_drawdown),
                threshold=self.auto_disable_rules.get("max_drawdown"),
                direction="lower_better"
            ),
            "consecutive_losses": PerformanceMetric(
                name="consecutive_losses",
                value=float(self.consecutive_losses),
                threshold=self.auto_disable_rules.get("max_consecutive_losses"),
                direction="lower_better"
            ),
            "total_pnl": PerformanceMetric(
                name="total_pnl",
                value=float(self.total_pnl),
                direction="higher_better"
            )
        }
    
    @classmethod
    def create_with_default_rules(cls, strategy_name: str, trading_mode: TradingMode = TradingMode.PAPER) -> "StrategyPerformance":
        """Create strategy performance with default auto-disable rules"""
        return cls(
            strategy_name=strategy_name,
            current_mode=trading_mode,
            auto_disable_rules={
                "max_drawdown": 1000.0,        # $1000 max drawdown
                "max_consecutive_losses": 5,    # 5 consecutive losses
                "min_win_rate": 0.30,          # 30% minimum win rate
                "min_profit_factor": 1.0       # 1.0 minimum profit factor
            }
        )


class StrategyConfiguration(BaseModel):
    """Strategy configuration and settings"""
    
    strategy_name: str = Field(description="Strategy identifier")
    
    # Basic settings
    enabled: bool = True
    trading_mode: TradingMode = TradingMode.PAPER
    max_positions: int = Field(default=1, description="Maximum open positions")
    position_size: int = Field(default=1, description="Default position size")
    
    # Risk management
    max_daily_loss: Optional[Decimal] = Field(None, description="Maximum daily loss")
    max_daily_trades: Optional[int] = Field(None, description="Maximum trades per day")
    
    # Auto-rotation settings
    auto_rotation_enabled: bool = True
    performance_check_interval: timedelta = timedelta(hours=1)
    min_trades_before_rotation: int = 10
    
    # Strategy-specific parameters
    parameters: Dict[str, any] = Field(default_factory=dict)
    
    # Scheduling
    trading_hours: Optional[Dict[str, str]] = Field(None, description="Trading time windows")
    blackout_periods: List[Dict[str, str]] = Field(default_factory=list)
    
    # Monitoring
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    
    @validator('position_size')
    def validate_position_size(cls, v):
        if v <= 0:
            raise ValueError('Position size must be positive')
        return v
    
    @validator('max_positions')
    def validate_max_positions(cls, v):
        if v <= 0:
            raise ValueError('Max positions must be positive')
        return v


class StrategyRotationRule(BaseModel):
    """Rules for automatic strategy rotation"""
    
    rule_id: str = Field(description="Unique rule identifier")
    name: str = Field(description="Human-readable rule name")
    
    # Trigger conditions
    performance_metric: str = Field(description="Metric to monitor")
    operator: str = Field(description="Comparison operator: <, >, <=, >=, ==")
    threshold: float = Field(description="Threshold value")
    
    # Action to take
    action: str = Field(description="disable, pause, reduce_size, etc.")
    action_parameters: Dict[str, any] = Field(default_factory=dict)
    
    # Rule settings
    enabled: bool = True
    min_trades_required: int = Field(default=5, description="Minimum trades before rule applies")
    evaluation_period: Optional[timedelta] = Field(None, description="Time window for evaluation")
    
    # Tracking
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def evaluate(self, performance: StrategyPerformance) -> bool:
        """Evaluate if rule should trigger based on current performance"""
        if not self.enabled:
            return False
        
        if performance.total_trades < self.min_trades_required:
            return False
        
        # Get metric value
        metrics = performance.get_current_metrics()
        if self.performance_metric not in metrics:
            return False
        
        metric_value = metrics[self.performance_metric].value
        
        # Evaluate condition
        if self.operator == "<":
            triggered = metric_value < self.threshold
        elif self.operator == ">":
            triggered = metric_value > self.threshold
        elif self.operator == "<=":
            triggered = metric_value <= self.threshold
        elif self.operator == ">=":
            triggered = metric_value >= self.threshold
        elif self.operator == "==":
            triggered = abs(metric_value - self.threshold) < 1e-6
        else:
            return False
        
        if triggered:
            self.last_triggered = datetime.utcnow()
            self.trigger_count += 1
        
        return triggered


class StrategyPortfolio(BaseModel):
    """Portfolio of strategies with collective performance tracking"""
    
    portfolio_name: str = Field(description="Portfolio identifier")
    strategies: Dict[str, StrategyPerformance] = Field(default_factory=dict)
    
    # Portfolio-level metrics
    total_portfolio_pnl: Decimal = Decimal("0")
    portfolio_drawdown: Decimal = Decimal("0")
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    
    # Risk management
    portfolio_max_drawdown: Decimal = Field(default=Decimal("5000"))
    max_concurrent_strategies: int = Field(default=5)
    diversification_rules: List[str] = Field(default_factory=list)
    
    # Auto-rotation
    rotation_rules: List[StrategyRotationRule] = Field(default_factory=list)
    last_rotation_check: datetime = Field(default_factory=datetime.utcnow)
    
    def add_strategy(self, strategy: StrategyPerformance):
        """Add strategy to portfolio"""
        self.strategies[strategy.strategy_name] = strategy
        self._recalculate_portfolio_metrics()
    
    def remove_strategy(self, strategy_name: str):
        """Remove strategy from portfolio"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            self._recalculate_portfolio_metrics()
    
    def _recalculate_portfolio_metrics(self):
        """Recalculate portfolio-level metrics"""
        self.total_portfolio_pnl = sum(
            strategy.total_pnl for strategy in self.strategies.values()
        )
        
        # Calculate portfolio drawdown
        strategy_drawdowns = [strategy.current_drawdown for strategy in self.strategies.values()]
        self.portfolio_drawdown = sum(strategy_drawdowns)
    
    def get_active_strategies(self) -> List[StrategyPerformance]:
        """Get all active strategies in portfolio"""
        return [
            strategy for strategy in self.strategies.values()
            if strategy.current_status == StrategyStatus.ACTIVE
        ]
    
    def check_rotation_rules(self) -> List[Dict[str, any]]:
        """Check all rotation rules and return triggered actions"""
        actions = []
        
        for rule in self.rotation_rules:
            for strategy in self.strategies.values():
                if rule.evaluate(strategy):
                    actions.append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "strategy_name": strategy.strategy_name,
                        "action": rule.action,
                        "action_parameters": rule.action_parameters,
                        "triggered_at": datetime.utcnow()
                    })
        
        self.last_rotation_check = datetime.utcnow()
        return actions