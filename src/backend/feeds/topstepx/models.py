"""
TopstepX Data Models and Business Logic

Comprehensive Pydantic models for TopstepX API integration including:
- API request/response models for REST and WebSocket
- Business logic models for funded account management
- Rule enforcement, risk monitoring, and compliance tracking
"""

import logging
from datetime import datetime, timedelta, date
from enum import Enum
from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# =============================================================================
# API-Specific Models (TopstepX REST API)
# =============================================================================

class ContractType(Enum):
    """Contract types supported by TopstepX API"""
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    SPREAD = "SPREAD"
    MICRO = "MICRO"


class OrderType(Enum):
    """Order types for futures trading"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    MIT = "MIT"  # Market If Touched
    LIT = "LIT"  # Limit If Touched


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status types from TopstepX API"""
    PENDING = "PENDING"
    WORKING = "WORKING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    PENDING_CANCEL = "PENDING_CANCEL"


class TimeInForce(Enum):
    """Time in force types"""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill


class TopstepXContract(BaseModel):
    """Futures contract information from TopstepX API"""
    
    contract_id: str
    symbol: str
    description: str
    contract_type: ContractType
    exchange: str
    
    # Contract specifications
    tick_size: Decimal
    tick_value: Decimal
    point_value: Decimal
    minimum_tick: Decimal
    
    # Trading hours
    trading_hours: Optional[Dict[str, Any]] = None
    
    # Expiration for futures
    expiration_date: Optional[datetime] = None
    delivery_month: Optional[str] = None
    
    # Margin requirements
    initial_margin: Optional[Decimal] = None
    maintenance_margin: Optional[Decimal] = None
    
    @classmethod
    def from_topstepx_data(cls, data: Dict[str, Any]) -> "TopstepXContract":
        """Create contract from TopstepX API response"""
        return cls(
            contract_id=data.get("contractId", ""),
            symbol=data.get("symbol", ""),
            description=data.get("description", ""),
            contract_type=ContractType(data.get("contractType", "FUTURE")),
            exchange=data.get("exchange", ""),
            tick_size=Decimal(str(data.get("tickSize", 0.25))),
            tick_value=Decimal(str(data.get("tickValue", 12.50))),
            point_value=Decimal(str(data.get("pointValue", 50))),
            minimum_tick=Decimal(str(data.get("minimumTick", 0.25))),
            trading_hours=data.get("tradingHours"),
            expiration_date=datetime.fromisoformat(data["expirationDate"]) if data.get("expirationDate") else None,
            delivery_month=data.get("deliveryMonth"),
            initial_margin=Decimal(str(data["initialMargin"])) if data.get("initialMargin") else None,
            maintenance_margin=Decimal(str(data["maintenanceMargin"])) if data.get("maintenanceMargin") else None
        )


class TopstepXQuote(BaseModel):
    """Real-time market quote from TopstepX API"""
    
    contract_id: str
    symbol: str
    
    # Price data
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Optional[Decimal] = None
    
    # Size data
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    last_size: Optional[int] = None
    
    # Daily statistics
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    open_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    
    # Volume and open interest
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trade_time: Optional[datetime] = None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid price from bid/ask"""
        if self.bid and self.ask:
            return (self.bid + self.ask) / Decimal("2")
        return None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid/ask spread"""
        if self.bid and self.ask:
            return self.ask - self.bid
        return None
    
    @classmethod
    def from_topstepx_data(cls, data: Dict[str, Any]) -> "TopstepXQuote":
        """Create quote from TopstepX API response"""
        return cls(
            contract_id=data.get("contractId", ""),
            symbol=data.get("symbol", ""),
            bid=Decimal(str(data["bid"])) if data.get("bid") else None,
            ask=Decimal(str(data["ask"])) if data.get("ask") else None,
            last=Decimal(str(data["last"])) if data.get("last") else None,
            bid_size=data.get("bidSize"),
            ask_size=data.get("askSize"),
            last_size=data.get("lastSize"),
            high=Decimal(str(data["high"])) if data.get("high") else None,
            low=Decimal(str(data["low"])) if data.get("low") else None,
            open_price=Decimal(str(data["open"])) if data.get("open") else None,
            close_price=Decimal(str(data["close"])) if data.get("close") else None,
            change=Decimal(str(data["change"])) if data.get("change") else None,
            change_percent=Decimal(str(data["changePercent"])) if data.get("changePercent") else None,
            volume=data.get("volume"),
            open_interest=data.get("openInterest"),
            trade_time=datetime.fromisoformat(data["tradeTime"]) if data.get("tradeTime") else None
        )


class TopstepXOrder(BaseModel):
    """Order information for TopstepX API"""
    
    # Order identifiers
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    account_id: str
    
    # Contract details
    contract_id: str
    symbol: str
    
    # Order specifications
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    
    # Order status
    status: Optional[OrderStatus] = None
    filled_quantity: int = 0
    remaining_quantity: Optional[int] = None
    average_fill_price: Optional[Decimal] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Additional metadata
    text: Optional[str] = None  # Order description/notes
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_working(self) -> bool:
        """Check if order is active/working"""
        return self.status in [OrderStatus.PENDING, OrderStatus.WORKING, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order"""
        return self.side == OrderSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order"""
        return self.side == OrderSide.SELL
    
    def to_topstepx_format(self) -> Dict[str, Any]:
        """Convert to TopstepX API format"""
        order_data = {
            "accountId": self.account_id,
            "contractId": self.contract_id,
            "side": self.side.value,
            "orderType": self.order_type.value,
            "quantity": self.quantity,
            "timeInForce": self.time_in_force.value
        }
        
        if self.price is not None:
            order_data["price"] = float(self.price)
        if self.stop_price is not None:
            order_data["stopPrice"] = float(self.stop_price)
        if self.client_order_id:
            order_data["clientOrderId"] = self.client_order_id
        if self.text:
            order_data["text"] = self.text
        
        return order_data
    
    @classmethod
    def from_topstepx_data(cls, data: Dict[str, Any]) -> "TopstepXOrder":
        """Create order from TopstepX API response"""
        return cls(
            order_id=data.get("orderId"),
            client_order_id=data.get("clientOrderId"),
            account_id=data.get("accountId", ""),
            contract_id=data.get("contractId", ""),
            symbol=data.get("symbol", ""),
            side=OrderSide(data.get("side", "BUY")),
            order_type=OrderType(data.get("orderType", "MARKET")),
            quantity=data.get("quantity", 0),
            price=Decimal(str(data["price"])) if data.get("price") else None,
            stop_price=Decimal(str(data["stopPrice"])) if data.get("stopPrice") else None,
            time_in_force=TimeInForce(data.get("timeInForce", "DAY")),
            status=OrderStatus(data["status"]) if data.get("status") else None,
            filled_quantity=data.get("filledQuantity", 0),
            remaining_quantity=data.get("remainingQuantity"),
            average_fill_price=Decimal(str(data["averageFillPrice"])) if data.get("averageFillPrice") else None,
            created_at=datetime.fromisoformat(data["createdAt"]) if data.get("createdAt") else None,
            updated_at=datetime.fromisoformat(data["updatedAt"]) if data.get("updatedAt") else None,
            filled_at=datetime.fromisoformat(data["filledAt"]) if data.get("filledAt") else None,
            text=data.get("text")
        )


class TopstepXPosition(BaseModel):
    """Position information from TopstepX API"""
    
    # Position identifiers
    account_id: str
    contract_id: str
    symbol: str
    
    # Position details
    quantity: int  # Positive for long, negative for short
    average_price: Decimal
    market_value: Optional[Decimal] = None
    
    # P&L calculations
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    day_pnl: Optional[Decimal] = None
    
    # Position metadata
    opened_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat"""
        return self.quantity == 0
    
    @property
    def absolute_quantity(self) -> int:
        """Get absolute position size"""
        return abs(self.quantity)
    
    @classmethod
    def from_topstepx_data(cls, data: Dict[str, Any]) -> "TopstepXPosition":
        """Create position from TopstepX API response"""
        return cls(
            account_id=data.get("accountId", ""),
            contract_id=data.get("contractId", ""),
            symbol=data.get("symbol", ""),
            quantity=data.get("quantity", 0),
            average_price=Decimal(str(data.get("averagePrice", 0))),
            market_value=Decimal(str(data["marketValue"])) if data.get("marketValue") else None,
            unrealized_pnl=Decimal(str(data["unrealizedPnl"])) if data.get("unrealizedPnl") else None,
            realized_pnl=Decimal(str(data["realizedPnl"])) if data.get("realizedPnl") else None,
            day_pnl=Decimal(str(data["dayPnl"])) if data.get("dayPnl") else None,
            opened_at=datetime.fromisoformat(data["openedAt"]) if data.get("openedAt") else None,
            updated_at=datetime.fromisoformat(data["updatedAt"]) if data.get("updatedAt") else None
        )


# =============================================================================
# Business Logic Models (Funded Account Management)
# =============================================================================


class AccountStatus(Enum):
    """Funded account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PASSED = "passed"
    FAILED = "failed"
    UNDER_REVIEW = "under_review"


class RuleViolationType(Enum):
    """Types of rule violations"""
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    TRAILING_DRAWDOWN = "trailing_drawdown"
    MAX_CONTRACTS = "max_contracts"
    CONSISTENCY_VIOLATION = "consistency_violation"
    OVERNIGHT_POSITION = "overnight_position"
    NEWS_TRADING = "news_trading"


class TradingPhase(Enum):
    """Trading account phase"""
    EVALUATION = "evaluation"
    FUNDED = "funded"
    SCALING = "scaling"


class FundedAccountRules(BaseModel):
    """
    Funded account trading rules and limits.
    
    These rules are enforced in real-time to ensure compliance
    with funded account provider requirements.
    """
    
    # Core loss limits
    max_daily_loss: float = Field(..., description="Maximum daily loss limit ($)")
    trailing_drawdown: float = Field(..., description="Maximum trailing drawdown ($)")
    
    # Position and sizing limits
    max_contracts: int = Field(..., description="Maximum contracts per position")
    max_position_value: Optional[float] = Field(None, description="Maximum position value ($)")
    
    # Profit requirements
    profit_target: float = Field(..., description="Profit target to pass evaluation ($)")
    min_trading_days: int = Field(default=5, description="Minimum required trading days")
    
    # Current metrics (real-time tracking)
    current_daily_pnl: float = Field(default=0.0, description="Current day P&L ($)")
    current_drawdown: float = Field(default=0.0, description="Current trailing drawdown ($)")
    max_peak_equity: float = Field(default=0.0, description="Maximum peak equity reached ($)")
    
    # Trading constraints
    allow_overnight_positions: bool = Field(default=False, description="Allow holding overnight")
    allow_news_trading: bool = Field(default=False, description="Allow trading during news events")
    restricted_symbols: List[str] = Field(default_factory=list, description="Restricted trading symbols")
    
    # Consistency requirements
    max_daily_profit_ratio: Optional[float] = Field(None, description="Max daily profit as % of total target")
    
    def can_trade(self, contracts: int, symbol: str = None) -> tuple[bool, Optional[str]]:
        """
        Check if a trade is allowed based on current rules.
        
        Args:
            contracts: Number of contracts for the trade
            symbol: Trading symbol (optional)
            
        Returns:
            tuple: (is_allowed, rejection_reason)
        """
        # Check daily loss limit
        if self.current_daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit reached: ${abs(self.current_daily_pnl):,.2f}"
        
        # Check contract limit
        if contracts > self.max_contracts:
            return False, f"Contract limit exceeded: {contracts} > {self.max_contracts}"
        
        # Check trailing drawdown
        if self.current_drawdown >= self.trailing_drawdown:
            return False, f"Trailing drawdown limit reached: ${self.current_drawdown:,.2f}"
        
        # Check restricted symbols
        if symbol and symbol.upper() in self.restricted_symbols:
            return False, f"Symbol {symbol} is restricted for trading"
        
        return True, None
    
    def update_daily_pnl(self, new_pnl: float):
        """Update current daily P&L and recalculate drawdown"""
        self.current_daily_pnl = new_pnl
        
        # Update peak equity if we've made new highs
        current_equity = self.max_peak_equity + new_pnl
        if current_equity > self.max_peak_equity:
            self.max_peak_equity = current_equity
            self.current_drawdown = 0.0  # Reset drawdown at new peak
        else:
            # Calculate drawdown from peak
            self.current_drawdown = self.max_peak_equity - current_equity
    
    def check_profit_target_reached(self) -> bool:
        """Check if profit target has been reached"""
        total_profit = self.current_daily_pnl + (self.max_peak_equity - self.profit_target)
        return total_profit >= self.profit_target
    
    def get_remaining_loss_buffer(self) -> float:
        """Get remaining loss buffer before hitting daily limit"""
        return max(0, self.max_daily_loss + self.current_daily_pnl)
    
    def get_remaining_drawdown_buffer(self) -> float:
        """Get remaining drawdown buffer before hitting limit"""
        return max(0, self.trailing_drawdown - self.current_drawdown)


class RuleViolation(BaseModel):
    """Record of a rule violation"""
    
    id: str = Field(..., description="Unique violation ID")
    account_id: str = Field(..., description="Account that violated rule")
    violation_type: RuleViolationType = Field(..., description="Type of violation")
    
    # Violation details
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    rule_limit: float = Field(..., description="The rule limit that was exceeded")
    actual_value: float = Field(..., description="The actual value that triggered violation")
    
    # Context
    symbol: Optional[str] = Field(None, description="Symbol being traded when violation occurred")
    trade_id: Optional[str] = Field(None, description="Trade that triggered violation")
    message: str = Field(..., description="Human-readable violation message")
    
    # Resolution
    resolved: bool = Field(default=False, description="Whether violation has been resolved")
    resolved_at: Optional[datetime] = Field(None, description="When violation was resolved")
    action_taken: Optional[str] = Field(None, description="Action taken to resolve violation")
    
    def resolve_violation(self, action: str):
        """Mark violation as resolved"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.action_taken = action


class AccountMetrics(BaseModel):
    """Real-time account performance metrics"""
    
    account_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # P&L metrics
    daily_pnl: float = Field(description="Current day P&L")
    total_pnl: float = Field(description="Total account P&L")
    gross_pnl: float = Field(description="Gross P&L before commissions")
    net_pnl: float = Field(description="Net P&L after commissions")
    
    # Drawdown tracking
    current_drawdown: float = Field(description="Current trailing drawdown")
    max_drawdown: float = Field(description="Maximum drawdown experienced")
    max_peak_equity: float = Field(description="Highest equity peak reached")
    
    # Position information
    open_positions: int = Field(description="Number of open positions")
    total_contracts: int = Field(description="Total contracts held")
    largest_position: int = Field(description="Largest single position size")
    
    # Performance stats
    win_rate: float = Field(description="Winning trade percentage")
    profit_factor: float = Field(description="Gross profit / gross loss ratio")
    avg_win: float = Field(description="Average winning trade")
    avg_loss: float = Field(description="Average losing trade")
    
    # Risk metrics
    sharpe_ratio: Optional[float] = Field(None, description="Risk-adjusted return ratio")
    max_consecutive_losses: int = Field(description="Maximum consecutive losing trades")
    
    # Trading activity
    total_trades: int = Field(description="Total number of trades")
    trading_days: int = Field(description="Number of active trading days")
    avg_daily_volume: float = Field(description="Average daily trading volume")


class TradingRules(BaseModel):
    """Complete set of trading rules for funded account"""
    
    # Basic rules
    account_rules: FundedAccountRules
    
    # Time-based restrictions
    trading_hours_start: str = Field(default="09:30", description="Trading start time (HH:MM)")
    trading_hours_end: str = Field(default="16:00", description="Trading end time (HH:MM)")
    timezone: str = Field(default="US/Eastern", description="Trading timezone")
    
    # News and event restrictions
    news_blackout_minutes: int = Field(default=2, description="Minutes before/after news events")
    restricted_news_events: List[str] = Field(
        default_factory=lambda: ["FOMC", "NFP", "CPI", "GDP"],
        description="Restricted news events"
    )
    
    # Account progression rules
    consistency_rule_enabled: bool = Field(default=True, description="Enable consistency rule")
    max_daily_profit_percentage: float = Field(default=0.5, description="Max daily profit as % of target")
    
    def is_trading_allowed_now(self) -> tuple[bool, Optional[str]]:
        """Check if trading is allowed at current time"""
        now = datetime.now()
        
        # Check if within trading hours
        # This is a simplified check - real implementation would handle timezones properly
        current_time = now.strftime("%H:%M")
        
        if current_time < self.trading_hours_start:
            return False, f"Trading not allowed before {self.trading_hours_start}"
        
        if current_time > self.trading_hours_end:
            return False, f"Trading not allowed after {self.trading_hours_end}"
        
        # Check if it's a trading day (simplified - weekdays only)
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False, "Trading not allowed on weekends"
        
        return True, None


class TopstepAccount(BaseModel):
    """Complete TopStep funded account information"""
    
    # Account identification
    account_id: str = Field(..., description="TopStep account ID")
    account_name: str = Field(..., description="Account display name")
    trader_id: str = Field(..., description="Trader/user ID")
    
    # Account details
    account_size: float = Field(..., description="Account starting balance ($)")
    current_balance: float = Field(..., description="Current account balance ($)")
    account_type: str = Field(..., description="Account type (Express, Standard, etc.)")
    phase: TradingPhase = Field(..., description="Current trading phase")
    status: AccountStatus = Field(..., description="Account status")
    
    # Rules and metrics
    rules: TradingRules = Field(..., description="Trading rules for this account")
    current_metrics: AccountMetrics = Field(..., description="Current performance metrics")
    
    # Violation tracking
    active_violations: List[RuleViolation] = Field(
        default_factory=list, description="Current active violations"
    )
    violation_history: List[RuleViolation] = Field(
        default_factory=list, description="Historical violations"
    )
    
    # Account lifecycle
    created_at: datetime = Field(..., description="Account creation date")
    last_trade_date: Optional[datetime] = Field(None, description="Last trading activity")
    evaluation_end_date: Optional[datetime] = Field(None, description="Evaluation period end")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def add_violation(self, violation: RuleViolation):
        """Add a new rule violation"""
        self.active_violations.append(violation)
        self.violation_history.append(violation)
        
        # Update account status if severe violation
        if violation.violation_type in [RuleViolationType.DAILY_LOSS_LIMIT, RuleViolationType.TRAILING_DRAWDOWN]:
            self.status = AccountStatus.SUSPENDED
    
    def resolve_violation(self, violation_id: str, action: str) -> bool:
        """Resolve an active violation"""
        for violation in self.active_violations:
            if violation.id == violation_id:
                violation.resolve_violation(action)
                self.active_violations.remove(violation)
                return True
        return False
    
    def is_trading_allowed(self) -> tuple[bool, Optional[str]]:
        """Check if trading is currently allowed"""
        # Check account status
        if self.status != AccountStatus.ACTIVE:
            return False, f"Account status is {self.status.value}"
        
        # Check for active violations
        if self.active_violations:
            violation_types = [v.violation_type.value for v in self.active_violations]
            return False, f"Active violations: {', '.join(violation_types)}"
        
        # Check trading hours
        time_allowed, time_reason = self.rules.is_trading_allowed_now()
        if not time_allowed:
            return False, time_reason
        
        # Check account rules
        return self.rules.account_rules.can_trade(1)  # Check with 1 contract
    
    def update_metrics(self, new_metrics: AccountMetrics):
        """Update account metrics and check for violations"""
        self.current_metrics = new_metrics
        self.last_updated = datetime.utcnow()
        
        # Update rules with new P&L
        self.rules.account_rules.update_daily_pnl(new_metrics.daily_pnl)
        
        # Check for new violations
        self._check_for_violations(new_metrics)
    
    def _check_for_violations(self, metrics: AccountMetrics):
        """Check metrics for rule violations"""
        rules = self.rules.account_rules
        
        # Check daily loss limit
        if metrics.daily_pnl <= -rules.max_daily_loss:
            violation = RuleViolation(
                id=f"daily_loss_{self.account_id}_{int(datetime.utcnow().timestamp())}",
                account_id=self.account_id,
                violation_type=RuleViolationType.DAILY_LOSS_LIMIT,
                rule_limit=rules.max_daily_loss,
                actual_value=abs(metrics.daily_pnl),
                message=f"Daily loss limit exceeded: ${abs(metrics.daily_pnl):,.2f} > ${rules.max_daily_loss:,.2f}"
            )
            self.add_violation(violation)
        
        # Check trailing drawdown
        if metrics.current_drawdown >= rules.trailing_drawdown:
            violation = RuleViolation(
                id=f"drawdown_{self.account_id}_{int(datetime.utcnow().timestamp())}",
                account_id=self.account_id,
                violation_type=RuleViolationType.TRAILING_DRAWDOWN,
                rule_limit=rules.trailing_drawdown,
                actual_value=metrics.current_drawdown,
                message=f"Trailing drawdown limit exceeded: ${metrics.current_drawdown:,.2f} > ${rules.trailing_drawdown:,.2f}"
            )
            self.add_violation(violation)
        
        # Check contract limits
        if metrics.total_contracts > rules.max_contracts:
            violation = RuleViolation(
                id=f"contracts_{self.account_id}_{int(datetime.utcnow().timestamp())}",
                account_id=self.account_id,
                violation_type=RuleViolationType.MAX_CONTRACTS,
                rule_limit=rules.max_contracts,
                actual_value=metrics.total_contracts,
                message=f"Contract limit exceeded: {metrics.total_contracts} > {rules.max_contracts}"
            )
            self.add_violation(violation)
    
    def get_status_summary(self) -> Dict[str, any]:
        """Get comprehensive account status summary"""
        return {
            "account_id": self.account_id,
            "status": self.status.value,
            "phase": self.phase.value,
            "balance": self.current_balance,
            "daily_pnl": self.current_metrics.daily_pnl,
            "drawdown": self.current_metrics.current_drawdown,
            "violations": len(self.active_violations),
            "trading_allowed": self.is_trading_allowed()[0],
            "profit_target_progress": (self.current_metrics.total_pnl / self.rules.account_rules.profit_target) * 100,
            "last_updated": self.last_updated.isoformat()
        }