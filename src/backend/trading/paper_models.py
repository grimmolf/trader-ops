"""
Paper Trading Models for TraderTerminal

Defines the data models and types used for paper trading simulation,
including accounts, orders, fills, and performance tracking.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class PaperTradingMode(str, Enum):
    """Paper trading execution modes"""
    SANDBOX = "sandbox"      # Use broker sandbox (real API, fake money)
    SIMULATOR = "simulator"  # Internal simulation with market data
    HYBRID = "hybrid"       # Sandbox for execution, simulator for fills


class OrderType(str, Enum):
    """Order types for paper trading"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderAction(str, Enum):
    """Order actions"""
    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_OPEN = "sell_to_open"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_CLOSE = "sell_to_close"


class OrderStatus(str, Enum):
    """Order status values"""
    PENDING = "pending"
    WORKING = "working"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AssetType(str, Enum):
    """Asset types for paper trading"""
    STOCK = "stock"
    OPTION = "option"
    FUTURE = "future"
    CRYPTO = "crypto"
    FOREX = "forex"


class PaperTradingAccount(BaseModel):
    """Paper trading account model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    broker: str  # "tastytrade_sandbox", "tradovate_demo", "simulator", etc.
    mode: PaperTradingMode
    initial_balance: Decimal = Field(default=Decimal("100000"))
    current_balance: Decimal = Field(default=Decimal("100000"))
    day_pnl: Decimal = Field(default=Decimal("0"))
    total_pnl: Decimal = Field(default=Decimal("0"))
    buying_power: Decimal = Field(default=Decimal("100000"))
    positions: Dict[str, "Position"] = Field(default_factory=dict)
    settings: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    def update_balance(self, amount: Decimal) -> None:
        """Update account balance"""
        self.current_balance += amount
        self.last_updated = datetime.now(timezone.utc)
    
    def update_pnl(self, pnl: Decimal, is_day_pnl: bool = True) -> None:
        """Update P&L metrics"""
        if is_day_pnl:
            self.day_pnl += pnl
        self.total_pnl += pnl
        self.last_updated = datetime.now(timezone.utc)


class Position(BaseModel):
    """Trading position model"""
    symbol: str
    asset_type: AssetType
    quantity: Decimal
    avg_price: Decimal
    market_price: Decimal = Field(default=Decimal("0"))
    unrealized_pnl: Decimal = Field(default=Decimal("0"))
    realized_pnl: Decimal = Field(default=Decimal("0"))
    day_pnl: Decimal = Field(default=Decimal("0"))
    cost_basis: Decimal = Field(default=Decimal("0"))
    multiplier: Decimal = Field(default=Decimal("1"))  # Contract multiplier
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    def update_market_price(self, price: Decimal) -> None:
        """Update position with new market price"""
        self.market_price = price
        
        # Calculate unrealized P&L
        if self.quantity != 0:
            price_diff = price - self.avg_price
            self.unrealized_pnl = price_diff * self.quantity * self.multiplier
        
        self.last_updated = datetime.now(timezone.utc)
    
    def close_position(self, close_price: Decimal) -> Decimal:
        """Close position and return realized P&L"""
        if self.quantity == 0:
            return Decimal("0")
        
        price_diff = close_price - self.avg_price
        realized = price_diff * self.quantity * self.multiplier
        
        self.realized_pnl += realized
        self.quantity = Decimal("0")
        self.unrealized_pnl = Decimal("0")
        self.last_updated = datetime.now(timezone.utc)
        
        return realized


class PaperOrder(BaseModel):
    """Paper trading order model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    symbol: str
    asset_type: AssetType
    action: OrderAction
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None  # For limit orders
    stop_price: Optional[Decimal] = None  # For stop orders
    filled_quantity: Decimal = Field(default=Decimal("0"))
    remaining_quantity: Decimal = Field(default=Decimal("0"))
    avg_fill_price: Decimal = Field(default=Decimal("0"))
    status: OrderStatus = OrderStatus.PENDING
    broker: str = "simulator"
    strategy: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filled_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    def __post_init__(self):
        """Initialize remaining quantity"""
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.quantity
    
    def is_buy_order(self) -> bool:
        """Check if this is a buy order"""
        return self.action in [OrderAction.BUY, OrderAction.BUY_TO_OPEN, OrderAction.BUY_TO_CLOSE]
    
    def is_sell_order(self) -> bool:
        """Check if this is a sell order"""
        return self.action in [OrderAction.SELL, OrderAction.SELL_TO_OPEN, OrderAction.SELL_TO_CLOSE]


class Fill(BaseModel):
    """Order fill model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    account_id: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    price: Decimal
    commission: Decimal = Field(default=Decimal("0"))
    fees: Decimal = Field(default=Decimal("0"))
    slippage: Decimal = Field(default=Decimal("0"))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    broker: str = "simulator"
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @property
    def total_cost(self) -> Decimal:
        """Total cost including commission and fees"""
        return (self.price * self.quantity) + self.commission + self.fees


class PaperTradingMetrics(BaseModel):
    """Performance metrics for paper trading"""
    account_id: str
    period_start: datetime
    period_end: datetime
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: Decimal = Field(default=Decimal("0"))
    avg_win: Decimal = Field(default=Decimal("0"))
    avg_loss: Decimal = Field(default=Decimal("0"))
    largest_win: Decimal = Field(default=Decimal("0"))
    largest_loss: Decimal = Field(default=Decimal("0"))
    total_pnl: Decimal = Field(default=Decimal("0"))
    gross_profit: Decimal = Field(default=Decimal("0"))
    gross_loss: Decimal = Field(default=Decimal("0"))
    profit_factor: Decimal = Field(default=Decimal("0"))
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal = Field(default=Decimal("0"))
    total_commissions: Decimal = Field(default=Decimal("0"))
    total_volume: Decimal = Field(default=Decimal("0"))
    avg_trade_duration: Optional[str] = None  # ISO 8601 duration
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }


class MarketDataSnapshot(BaseModel):
    """Market data snapshot for paper trading"""
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @property
    def mid_price(self) -> Decimal:
        """Calculate mid price between bid and ask"""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / Decimal("2")
        return self.last
    
    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread"""
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid
        return Decimal("0")


class PaperTradingAlert(BaseModel):
    """Paper trading alert from TradingView"""
    symbol: str
    action: OrderAction
    quantity: Decimal
    order_type: OrderType = OrderType.MARKET
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    account_group: str
    strategy: Optional[str] = None
    comment: Optional[str] = None
    paper_mode: PaperTradingMode = PaperTradingMode.SIMULATOR
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    def is_paper_trading(self) -> bool:
        """Check if this alert is for paper trading"""
        return (
            self.account_group.startswith("paper_") or
            self.comment == "PAPER" or
            "paper" in (self.comment or "").lower()
        )
    
    def get_paper_broker(self) -> str:
        """Determine which paper broker to use"""
        if "_" in self.account_group:
            parts = self.account_group.split("_", 1)
            if len(parts) > 1:
                preference = parts[1]
                
                # Map preferences to broker keys
                broker_map = {
                    "tastytrade": "tastytrade_sandbox",
                    "tasty": "tastytrade_sandbox",
                    "tradovate": "tradovate_demo",
                    "tradovate_demo": "tradovate_demo",
                    "alpaca": "alpaca_paper",
                    "simulator": "simulator",
                    "sim": "simulator",
                    "auto": "auto"
                }
                
                return broker_map.get(preference, "simulator")
        
        return "auto"