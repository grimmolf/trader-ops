"""
Order execution and position management models.
Supports Tradier API integration and trading operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    BRACKET = "bracket"
    OCO = "oco"  # One-Cancels-Other


class OrderSide(str, Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_OPEN = "sell_to_open"
    SELL_TO_CLOSE = "sell_to_close"


class OrderStatus(str, Enum):
    """Order status states"""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    """Time in force options"""
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill


class Order(BaseModel):
    """Order model for trade execution"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal order ID")
    broker_order_id: Optional[str] = Field(None, description="Broker-assigned order ID")
    symbol: str = Field(..., description="Trading symbol")
    
    # Order details
    order_type: OrderType = Field(..., description="Order type")
    side: OrderSide = Field(..., description="Order side")
    quantity: float = Field(..., description="Order quantity", gt=0)
    price: Optional[float] = Field(None, description="Limit price", gt=0)
    stop_price: Optional[float] = Field(None, description="Stop price", gt=0)
    
    # Order configuration
    time_in_force: TimeInForce = Field(default=TimeInForce.DAY, description="Time in force")
    extended_hours: bool = Field(default=False, description="Allow extended hours trading")
    
    # Status and timestamps
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    created_at: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Order creation timestamp"
    )
    submitted_at: Optional[int] = Field(None, description="Broker submission timestamp")
    filled_at: Optional[int] = Field(None, description="Fill completion timestamp")
    
    # Execution details
    filled_quantity: float = Field(default=0, description="Filled quantity", ge=0)
    avg_fill_price: Optional[float] = Field(None, description="Average fill price", gt=0)
    fees: float = Field(default=0, description="Total fees", ge=0)
    
    # Additional fields
    account_id: Optional[str] = Field(None, description="Trading account ID")
    strategy_id: Optional[str] = Field(None, description="Associated strategy ID")
    alert_id: Optional[str] = Field(None, description="Triggering alert ID")
    
    @validator('price')
    def price_required_for_limit_orders(cls, v, values):
        """Validate price is provided for limit orders"""
        order_type = values.get('order_type')
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError(f'price required for {order_type} orders')
        return v
    
    @validator('stop_price')
    def stop_price_required_for_stop_orders(cls, v, values):
        """Validate stop price is provided for stop orders"""
        order_type = values.get('order_type')
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError(f'stop_price required for {order_type} orders')
        return v
    
    @validator('filled_quantity')
    def filled_quantity_not_exceed_total(cls, v, values):
        """Validate filled quantity doesn't exceed total quantity"""
        if 'quantity' in values and v > values['quantity']:
            raise ValueError('filled_quantity cannot exceed total quantity')
        return v
    
    @property
    def is_complete(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def remaining_quantity(self) -> float:
        """Calculate remaining unfilled quantity"""
        return self.quantity - self.filled_quantity
    
    def to_tradier_format(self) -> Dict[str, Any]:
        """Convert to Tradier API order format"""
        order_data = {
            "class": "equity",  # Simplified for now
            "symbol": self.symbol,
            "side": self._convert_side_to_tradier(),
            "quantity": int(self.quantity),
            "type": self._convert_type_to_tradier(),
            "duration": self._convert_tif_to_tradier(),
        }
        
        if self.price:
            order_data["price"] = self.price
        if self.stop_price:
            order_data["stop"] = self.stop_price
            
        return order_data
    
    def _convert_side_to_tradier(self) -> str:
        """Convert order side to Tradier format"""
        side_map = {
            OrderSide.BUY: "buy",
            OrderSide.SELL: "sell",
            OrderSide.BUY_TO_OPEN: "buy_to_open",
            OrderSide.BUY_TO_CLOSE: "buy_to_close",
            OrderSide.SELL_TO_OPEN: "sell_to_open",
            OrderSide.SELL_TO_CLOSE: "sell_to_close"
        }
        return side_map.get(self.side, "buy")
    
    def _convert_type_to_tradier(self) -> str:
        """Convert order type to Tradier format"""
        type_map = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP: "stop",
            OrderType.STOP_LIMIT: "stop_limit"
        }
        return type_map.get(self.order_type, "market")
    
    def _convert_tif_to_tradier(self) -> str:
        """Convert time in force to Tradier format"""
        tif_map = {
            TimeInForce.DAY: "day",
            TimeInForce.GTC: "gtc",
            TimeInForce.IOC: "ioc",
            TimeInForce.FOK: "fok"
        }
        return tif_map.get(self.time_in_force, "day")


class Execution(BaseModel):
    """Trade execution record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Execution ID")
    order_id: str = Field(..., description="Parent order ID")
    broker: str = Field(..., description="Executing broker")
    broker_execution_id: Optional[str] = Field(None, description="Broker execution ID")
    
    # Execution details
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Execution side")
    quantity: float = Field(..., description="Executed quantity", gt=0)
    price: float = Field(..., description="Execution price", gt=0)
    timestamp: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Execution timestamp"
    )
    
    # Fees and costs
    commission: float = Field(default=0, description="Commission fee", ge=0)
    sec_fee: float = Field(default=0, description="SEC fee", ge=0)
    taf_fee: float = Field(default=0, description="TAF fee", ge=0)
    other_fees: float = Field(default=0, description="Other fees", ge=0)
    
    @property
    def total_fees(self) -> float:
        """Calculate total execution fees"""
        return self.commission + self.sec_fee + self.taf_fee + self.other_fees
    
    @property
    def gross_value(self) -> float:
        """Calculate gross execution value"""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Calculate net execution value (including fees)"""
        fees = self.total_fees
        if self.side in [OrderSide.BUY, OrderSide.BUY_TO_OPEN, OrderSide.BUY_TO_CLOSE]:
            return self.gross_value + fees  # Add fees for buys
        else:
            return self.gross_value - fees  # Subtract fees for sells


class Position(BaseModel):
    """Position tracking model"""
    symbol: str = Field(..., description="Trading symbol")
    account_id: str = Field(..., description="Account ID")
    
    # Position details
    quantity: float = Field(..., description="Position quantity (+ long, - short)")
    avg_price: float = Field(..., description="Average cost basis", gt=0)
    market_value: Optional[float] = Field(None, description="Current market value")
    day_pnl: Optional[float] = Field(None, description="Day P&L")
    total_pnl: Optional[float] = Field(None, description="Total P&L")
    
    # Timestamps
    opened_at: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Position open timestamp"
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Last update timestamp"
    )
    
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
        """Check if position is flat (zero quantity)"""
        return abs(self.quantity) < 1e-8
    
    def update_market_value(self, current_price: float) -> None:
        """Update market value and P&L based on current price"""
        if self.quantity != 0:
            self.market_value = abs(self.quantity) * current_price
            self.total_pnl = (current_price - self.avg_price) * self.quantity
        else:
            self.market_value = 0
            self.total_pnl = 0
        
        self.updated_at = int(datetime.now(timezone.utc).timestamp())


class Account(BaseModel):
    """Trading account information"""
    account_id: str = Field(..., description="Account identifier")
    broker: str = Field(..., description="Broker name")
    account_type: str = Field(..., description="Account type: cash, margin, etc.")
    
    # Account balances
    total_equity: float = Field(..., description="Total account equity", ge=0)
    cash_balance: float = Field(..., description="Available cash", ge=0)
    buying_power: float = Field(..., description="Available buying power", ge=0)
    day_trade_buying_power: Optional[float] = Field(None, description="Day trade buying power", ge=0)
    
    # P&L tracking
    day_pnl: float = Field(default=0, description="Day P&L")
    total_pnl: float = Field(default=0, description="Total P&L")
    
    # Account status
    is_active: bool = Field(default=True, description="Account is active")
    pattern_day_trader: bool = Field(default=False, description="Pattern day trader status")
    
    # Timestamps
    last_updated: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Last update timestamp"
    )