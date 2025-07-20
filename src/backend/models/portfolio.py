"""
Portfolio management and performance analytics models.
Integrates with PyPortfolioOpt and QuantStats for advanced analytics.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, validator
from .execution import Position


class PortfolioType(str, Enum):
    """Portfolio types"""
    EQUITY = "equity"
    OPTIONS = "options"
    FUTURES = "futures"
    MIXED = "mixed"
    CRYPTO = "crypto"


class RiskLevel(str, Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    SPECULATIVE = "speculative"


class PortfolioPosition(BaseModel):
    """Enhanced position with portfolio context"""
    symbol: str = Field(..., description="Trading symbol")
    quantity: float = Field(..., description="Position quantity")
    avg_price: float = Field(..., description="Average cost basis", gt=0)
    current_price: Optional[float] = Field(None, description="Current market price", gt=0)
    
    # Portfolio allocation
    weight: float = Field(..., description="Portfolio weight (0-1)", ge=0, le=1)
    target_weight: Optional[float] = Field(None, description="Target allocation weight", ge=0, le=1)
    
    # Risk metrics
    beta: Optional[float] = Field(None, description="Beta vs benchmark")
    volatility: Optional[float] = Field(None, description="Historical volatility", ge=0)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    
    # P&L metrics
    unrealized_pnl: Optional[float] = Field(None, description="Unrealized P&L")
    realized_pnl: float = Field(default=0, description="Realized P&L")
    day_pnl: Optional[float] = Field(None, description="Day P&L")
    
    @property
    def market_value(self) -> float:
        """Calculate current market value"""
        if self.current_price is None:
            return abs(self.quantity) * self.avg_price
        return abs(self.quantity) * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Calculate total cost basis"""
        return abs(self.quantity) * self.avg_price
    
    @property
    def total_pnl(self) -> float:
        """Calculate total P&L (realized + unrealized)"""
        unrealized = self.unrealized_pnl or 0
        return self.realized_pnl + unrealized
    
    def update_price(self, new_price: float) -> None:
        """Update position with new market price"""
        self.current_price = new_price
        if self.quantity != 0:
            self.unrealized_pnl = (new_price - self.avg_price) * self.quantity
            self.weight = self.market_value  # Will be normalized at portfolio level


class Portfolio(BaseModel):
    """Portfolio management and analytics"""
    id: str = Field(..., description="Portfolio identifier")
    name: str = Field(..., description="Portfolio name")
    account_id: str = Field(..., description="Associated account ID")
    portfolio_type: PortfolioType = Field(..., description="Portfolio type")
    
    # Configuration
    benchmark_symbol: str = Field(default="SPY", description="Benchmark for comparisons")
    risk_level: RiskLevel = Field(default=RiskLevel.MODERATE, description="Risk tolerance")
    target_return: Optional[float] = Field(None, description="Target annual return", gt=0)
    max_position_size: float = Field(default=0.1, description="Max position size (0-1)", gt=0, le=1)
    
    # Portfolio composition
    positions: List[PortfolioPosition] = Field(default_factory=list, description="Portfolio positions")
    cash_balance: float = Field(..., description="Cash balance", ge=0)
    
    # Performance metrics
    total_value: float = Field(default=0, description="Total portfolio value", ge=0)
    day_pnl: float = Field(default=0, description="Day P&L")
    total_pnl: float = Field(default=0, description="Total P&L")
    inception_date: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Portfolio inception date"
    )
    
    # Risk metrics (updated by analytics)
    volatility: Optional[float] = Field(None, description="Portfolio volatility", ge=0)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    beta: Optional[float] = Field(None, description="Beta vs benchmark")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown", le=0)
    var_95: Optional[float] = Field(None, description="95% Value at Risk", le=0)
    
    # Timestamps
    last_updated: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Last update timestamp"
    )
    
    @validator('positions')
    def no_duplicate_symbols(cls, v):
        """Ensure no duplicate symbols in positions"""
        symbols = [pos.symbol for pos in v]
        if len(symbols) != len(set(symbols)):
            raise ValueError('Duplicate symbols not allowed in portfolio')
        return v
    
    def update_values(self) -> None:
        """Update portfolio values and weights"""
        # Calculate total market value
        position_value = sum(pos.market_value for pos in self.positions)
        self.total_value = position_value + self.cash_balance
        
        # Update position weights
        if self.total_value > 0:
            for position in self.positions:
                position.weight = position.market_value / self.total_value
        
        # Update P&L
        self.day_pnl = sum(pos.day_pnl or 0 for pos in self.positions)
        self.total_pnl = sum(pos.total_pnl for pos in self.positions)
        
        self.last_updated = int(datetime.now(timezone.utc).timestamp())
    
    def add_position(self, position: PortfolioPosition) -> None:
        """Add position to portfolio"""
        # Check if position already exists
        existing = next((p for p in self.positions if p.symbol == position.symbol), None)
        if existing:
            # Merge positions (weighted average cost basis)
            total_quantity = existing.quantity + position.quantity
            if total_quantity != 0:
                total_cost = (existing.quantity * existing.avg_price + 
                            position.quantity * position.avg_price)
                existing.avg_price = total_cost / total_quantity
                existing.quantity = total_quantity
            else:
                # Position closed
                self.positions.remove(existing)
        else:
            self.positions.append(position)
        
        self.update_values()
    
    def get_position(self, symbol: str) -> Optional[PortfolioPosition]:
        """Get position by symbol"""
        return next((p for p in self.positions if p.symbol == symbol), None)
    
    def remove_position(self, symbol: str) -> None:
        """Remove position from portfolio"""
        self.positions = [p for p in self.positions if p.symbol != symbol]
        self.update_values()
    
    @property
    def equity_exposure(self) -> float:
        """Calculate equity exposure (non-cash allocation)"""
        if self.total_value == 0:
            return 0
        return (self.total_value - self.cash_balance) / self.total_value
    
    @property
    def concentration_risk(self) -> float:
        """Calculate concentration risk (largest position weight)"""
        if not self.positions:
            return 0
        return max(pos.weight for pos in self.positions)
    
    def get_allocation_summary(self) -> Dict[str, float]:
        """Get portfolio allocation summary"""
        allocation = {"CASH": self.cash_balance / self.total_value if self.total_value > 0 else 1}
        for position in self.positions:
            allocation[position.symbol] = position.weight
        return allocation
    
    def rebalance_targets(self) -> Dict[str, float]:
        """Calculate rebalancing requirements"""
        rebalance = {}
        for position in self.positions:
            if position.target_weight is not None:
                target_value = position.target_weight * self.total_value
                current_value = position.market_value
                difference = target_value - current_value
                if abs(difference) > self.total_value * 0.01:  # 1% threshold
                    rebalance[position.symbol] = difference
        return rebalance


class Performance(BaseModel):
    """Portfolio performance analytics"""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    period_start: int = Field(..., description="Performance period start timestamp")
    period_end: int = Field(..., description="Performance period end timestamp")
    
    # Return metrics
    total_return: float = Field(..., description="Total period return")
    annualized_return: Optional[float] = Field(None, description="Annualized return")
    benchmark_return: Optional[float] = Field(None, description="Benchmark return")
    excess_return: Optional[float] = Field(None, description="Excess return vs benchmark")
    
    # Risk metrics
    volatility: float = Field(..., description="Period volatility", ge=0)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
    
    # Drawdown metrics
    max_drawdown: float = Field(..., description="Maximum drawdown", le=0)
    avg_drawdown: Optional[float] = Field(None, description="Average drawdown", le=0)
    recovery_time: Optional[int] = Field(None, description="Drawdown recovery time (days)", ge=0)
    
    # Trade statistics
    total_trades: int = Field(default=0, description="Total number of trades", ge=0)
    winning_trades: int = Field(default=0, description="Number of winning trades", ge=0)
    win_rate: Optional[float] = Field(None, description="Win rate (0-1)", ge=0, le=1)
    avg_win: Optional[float] = Field(None, description="Average winning trade", gt=0)
    avg_loss: Optional[float] = Field(None, description="Average losing trade", lt=0)
    profit_factor: Optional[float] = Field(None, description="Profit factor", gt=0)
    
    # Risk measures
    var_95: Optional[float] = Field(None, description="95% Value at Risk", le=0)
    cvar_95: Optional[float] = Field(None, description="95% Conditional VaR", le=0)
    beta: Optional[float] = Field(None, description="Beta vs benchmark")
    alpha: Optional[float] = Field(None, description="Alpha vs benchmark")
    
    @validator('period_end')
    def end_after_start(cls, v, values):
        """Validate end timestamp is after start"""
        if 'period_start' in values and v <= values['period_start']:
            raise ValueError('period_end must be after period_start')
        return v
    
    @validator('win_rate')
    def calculate_win_rate(cls, v, values):
        """Calculate win rate from trade statistics"""
        if v is None and 'total_trades' in values and 'winning_trades' in values:
            total = values['total_trades']
            if total > 0:
                return values['winning_trades'] / total
        return v
    
    @property
    def losing_trades(self) -> int:
        """Calculate number of losing trades"""
        return self.total_trades - self.winning_trades
    
    @property
    def information_ratio(self) -> Optional[float]:
        """Calculate information ratio"""
        if self.excess_return is not None and self.volatility > 0:
            return self.excess_return / self.volatility
        return None
    
    def to_quantstats_format(self) -> Dict[str, Any]:
        """Convert to format compatible with QuantStats"""
        return {
            "total_return": self.total_return,
            "annual_return": self.annualized_return,
            "volatility": self.volatility,
            "sharpe": self.sharpe_ratio,
            "sortino": self.sortino_ratio,
            "calmar": self.calmar_ratio,
            "max_drawdown": self.max_drawdown,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "beta": self.beta,
            "alpha": self.alpha,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor
        }