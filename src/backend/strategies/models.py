"""
Strategy Performance Models for TraderTerminal

Defines the data models for tracking strategy performance, auto-rotation logic,
and trade set evaluation for automated strategy management.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal
import uuid


class TradingMode(str, Enum):
    """Trading modes for strategy execution"""
    LIVE = "live"
    PAPER = "paper"
    SUSPENDED = "suspended"


class TradeResult(BaseModel):
    """Individual trade result for strategy performance tracking"""
    strategy_id: str
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    side: Literal["long", "short"]
    pnl: Decimal
    win: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: TradingMode
    set_number: int
    trade_number_in_set: int
    commission: Decimal = Field(default=Decimal("0"))
    slippage: Decimal = Field(default=Decimal("0"))
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @property
    def net_pnl(self) -> Decimal:
        """Net P&L after commission and slippage"""
        return self.pnl - self.commission - abs(self.slippage)


class StrategySet(BaseModel):
    """Represents a set of 20 trades for evaluation"""
    set_number: int
    strategy_id: str
    trades: List[TradeResult] = Field(default_factory=list)
    win_rate: Decimal = Field(default=Decimal("0"))
    total_pnl: Decimal = Field(default=Decimal("0"))
    net_pnl: Decimal = Field(default=Decimal("0"))
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    mode: TradingMode
    evaluation_threshold: int = Field(default=20)
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @property
    def is_complete(self) -> bool:
        """Check if the set has enough trades for evaluation"""
        return len(self.trades) >= self.evaluation_threshold
    
    @property
    def calculate_win_rate(self) -> Decimal:
        """Calculate current win rate for the set"""
        if not self.trades:
            return Decimal("0")
        
        winning_trades = sum(1 for trade in self.trades if trade.win)
        return Decimal(str((winning_trades / len(self.trades)) * 100))
    
    @property
    def calculate_total_pnl(self) -> Decimal:
        """Calculate total P&L for the set"""
        return sum(trade.pnl for trade in self.trades)
    
    @property
    def calculate_net_pnl(self) -> Decimal:
        """Calculate net P&L after commissions and slippage"""
        return sum(trade.net_pnl for trade in self.trades)
    
    @property
    def average_trade_pnl(self) -> Decimal:
        """Calculate average P&L per trade"""
        if not self.trades:
            return Decimal("0")
        return self.calculate_total_pnl / len(self.trades)
    
    @property
    def profit_factor(self) -> Decimal:
        """Calculate profit factor (gross profit / gross loss)"""
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        if not losing_trades:
            return Decimal("999.99")  # No losses, very high profit factor
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        
        if gross_loss == 0:
            return Decimal("999.99")
        
        return gross_profit / gross_loss
    
    def add_trade(self, trade: TradeResult) -> None:
        """Add a trade to the set and update metrics"""
        trade.set_number = self.set_number
        trade.trade_number_in_set = len(self.trades) + 1
        self.trades.append(trade)
        
        # Update calculated metrics
        self.win_rate = self.calculate_win_rate
        self.total_pnl = self.calculate_total_pnl
        self.net_pnl = self.calculate_net_pnl
        
        # Mark set as complete if we reach the threshold
        if self.is_complete and not self.end_date:
            self.end_date = datetime.now(timezone.utc)


class ModeTransition(BaseModel):
    """Record of strategy mode transitions"""
    from_mode: TradingMode
    to_mode: TradingMode
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str
    trigger_set_number: int
    trigger_win_rates: List[Decimal] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }


class StrategyPerformance(BaseModel):
    """Complete strategy performance tracking"""
    strategy_id: str
    strategy_name: str
    current_mode: TradingMode = TradingMode.LIVE
    current_set: StrategySet
    completed_sets: List[StrategySet] = Field(default_factory=list)
    mode_transition_history: List[ModeTransition] = Field(default_factory=list)
    
    # Performance thresholds
    min_win_rate: Decimal = Field(default=Decimal("55.0"))  # Minimum acceptable win rate
    evaluation_period: int = Field(default=20)  # Trades per set
    consecutive_failures_threshold: int = Field(default=2)  # Sets needed to move to paper
    consecutive_successes_threshold: int = Field(default=2)  # Sets needed to move back to live
    
    # Statistics
    total_trades: int = Field(default=0)
    total_winning_trades: int = Field(default=0)
    total_losing_trades: int = Field(default=0)
    lifetime_pnl: Decimal = Field(default=Decimal("0"))
    lifetime_net_pnl: Decimal = Field(default=Decimal("0"))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @property
    def overall_win_rate(self) -> Decimal:
        """Calculate overall win rate across all completed sets"""
        if self.total_trades == 0:
            return Decimal("0")
        return Decimal(str((self.total_winning_trades / self.total_trades) * 100))
    
    @property
    def recent_performance(self) -> List[Decimal]:
        """Get win rates from the last 3 completed sets"""
        recent_sets = self.completed_sets[-3:] if len(self.completed_sets) >= 3 else self.completed_sets
        return [s.win_rate for s in recent_sets]
    
    @property
    def is_at_risk(self) -> bool:
        """Check if strategy is at risk of being moved to paper"""
        if self.current_mode != TradingMode.LIVE:
            return False
        
        # Check if we have recent completed sets
        if len(self.completed_sets) < self.consecutive_failures_threshold:
            return False
        
        # Check last N sets for failure
        recent_sets = self.completed_sets[-self.consecutive_failures_threshold:]
        failed_sets = sum(1 for s in recent_sets if s.win_rate < self.min_win_rate)
        
        return failed_sets >= self.consecutive_failures_threshold
    
    @property
    def can_return_to_live(self) -> bool:
        """Check if paper strategy can return to live trading"""
        if self.current_mode != TradingMode.PAPER:
            return False
        
        # Need enough paper sets to evaluate
        paper_sets = [s for s in self.completed_sets if s.mode == TradingMode.PAPER]
        if len(paper_sets) < self.consecutive_successes_threshold:
            return False
        
        # Check last N paper sets for success
        recent_paper_sets = paper_sets[-self.consecutive_successes_threshold:]
        successful_sets = sum(1 for s in recent_paper_sets if s.win_rate >= self.min_win_rate)
        
        return successful_sets >= self.consecutive_successes_threshold
    
    def add_trade(self, trade: TradeResult) -> bool:
        """
        Add a trade to the current set and check for mode transitions.
        Returns True if set was completed.
        """
        # Add trade to current set
        self.current_set.add_trade(trade)
        
        # Update statistics
        self.total_trades += 1
        if trade.win:
            self.total_winning_trades += 1
        else:
            self.total_losing_trades += 1
        
        self.lifetime_pnl += trade.pnl
        self.lifetime_net_pnl += trade.net_pnl
        self.last_updated = datetime.now(timezone.utc)
        
        # Check if current set is complete
        if self.current_set.is_complete:
            self._complete_current_set()
            return True
        
        return False
    
    def _complete_current_set(self) -> None:
        """Complete the current set and start a new one"""
        # Finalize current set
        self.current_set.end_date = datetime.now(timezone.utc)
        
        # Move to completed sets
        self.completed_sets.append(self.current_set)
        
        # Start new set
        new_set_number = self.current_set.set_number + 1
        self.current_set = StrategySet(
            set_number=new_set_number,
            strategy_id=self.strategy_id,
            mode=self.current_mode,
            evaluation_threshold=self.evaluation_period
        )
    
    def transition_mode(self, new_mode: TradingMode, reason: str) -> ModeTransition:
        """Transition to a new trading mode"""
        old_mode = self.current_mode
        
        # Create transition record
        transition = ModeTransition(
            from_mode=old_mode,
            to_mode=new_mode,
            reason=reason,
            trigger_set_number=self.current_set.set_number,
            trigger_win_rates=self.recent_performance
        )
        
        # Update mode
        self.current_mode = new_mode
        self.current_set.mode = new_mode
        
        # Record transition
        self.mode_transition_history.append(transition)
        self.last_updated = datetime.now(timezone.utc)
        
        return transition


class StrategyRegistration(BaseModel):
    """Strategy registration request model"""
    strategy_id: str
    strategy_name: str
    min_win_rate: Decimal = Field(default=Decimal("55.0"))
    evaluation_period: int = Field(default=20)
    initial_mode: TradingMode = TradingMode.LIVE
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class StrategyModeChangeRequest(BaseModel):
    """Request to manually change strategy mode"""
    new_mode: TradingMode
    reason: str = "Manual override"
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class StrategyPerformanceSummary(BaseModel):
    """Summary view of strategy performance for API responses"""
    strategy_id: str
    strategy_name: str
    current_mode: TradingMode
    current_set_progress: int  # Number of trades in current set
    current_set_win_rate: Decimal
    overall_win_rate: Decimal
    total_sets_completed: int
    recent_performance: List[Decimal]  # Last 3 set win rates
    is_at_risk: bool
    can_return_to_live: bool
    lifetime_pnl: Decimal
    lifetime_net_pnl: Decimal
    last_trade_time: Optional[datetime] = None
    last_updated: datetime
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }