"""
TradeNote integration data models for TraderTerminal

Defines Pydantic models for TradeNote trade data format and configuration.
Handles conversion between TraderTerminal internal formats and TradeNote API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, timezone
from decimal import Decimal
import uuid


class TradeNoteConfig(BaseModel):
    """Configuration for TradeNote integration"""
    base_url: str = "http://localhost:8082"
    api_key: Optional[str] = None
    app_id: str
    master_key: str
    broker_name: str = "TraderTerminal"
    upload_mfe_prices: bool = False
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enabled: bool = True

    class Config:
        env_prefix = "TRADENOTE_"


class TradeNoteTradeData(BaseModel):
    """
    TradeNote trade data format matching their CSV template structure.
    
    Based on TradeNote's 22-column CSV template for trade imports.
    """
    
    # Core trade identification
    account: str = Field(..., description="Trading account identifier")
    trade_date: str = Field(..., description="Trade date (MM/DD/YYYY)")
    settlement_date: str = Field(..., description="Settlement date (MM/DD/YYYY)")
    currency: str = Field(default="USD", description="Currency code")
    
    # Trade details
    type: Literal["stock", "option", "future", "forex", "crypto"] = Field(..., description="Instrument type")
    side: Literal["Buy", "Sell"] = Field(..., description="Buy or Sell")
    symbol: str = Field(..., description="Trading symbol")
    quantity: int = Field(..., gt=0, description="Number of shares/contracts")
    price: Decimal = Field(..., description="Execution price")
    
    # Timing
    exec_time: str = Field(..., description="Execution time (HH:MM:SS)")
    
    # P&L and fees
    gross_proceeds: Optional[Decimal] = Field(None, description="Gross proceeds")
    commissions_fees: Decimal = Field(default=Decimal("0"), description="Total commissions and fees")
    net_proceeds: Optional[Decimal] = Field(None, description="Net proceeds after fees")
    
    # Additional fields for options/futures
    expiration_date: Optional[str] = Field(None, description="Option/Future expiration")
    strike_price: Optional[Decimal] = Field(None, description="Option strike price")
    
    # Strategy and notes
    strategy: Optional[str] = Field(None, description="Strategy name")
    notes: Optional[str] = Field(None, description="Trade notes/comments")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    
    # Paper trading indicator
    is_paper_trade: bool = Field(default=False, description="Whether this is a paper trade")
    
    # Internal tracking
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal trade ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat()
        }

    @validator('trade_date', 'settlement_date')
    def validate_date_format(cls, v):
        """Ensure dates are in MM/DD/YYYY format"""
        if v and len(v) == 10 and v.count('/') == 2:
            try:
                month, day, year = v.split('/')
                datetime(int(year), int(month), int(day))
                return v
            except ValueError:
                pass
        raise ValueError("Date must be in MM/DD/YYYY format")
    
    @validator('exec_time')
    def validate_time_format(cls, v):
        """Ensure execution time is in HH:MM:SS format"""
        if v and len(v) == 8 and v.count(':') == 2:
            try:
                hour, minute, second = v.split(':')
                if 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59 and 0 <= int(second) <= 59:
                    return v
            except ValueError:
                pass
        raise ValueError("Execution time must be in HH:MM:SS format")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate and normalize symbol"""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()

    def to_tradenote_format(self) -> Dict[str, Any]:
        """Convert to TradeNote API format"""
        return {
            "Account": self.account,
            "T/D": self.trade_date,
            "S/D": self.settlement_date,
            "Currency": self.currency,
            "Type": self.type.title(),
            "Side": self.side,
            "Symbol": self.symbol,
            "Qty": self.quantity,
            "Price": float(self.price),
            "Exec Time": self.exec_time,
            "Gross Proceeds": float(self.gross_proceeds) if self.gross_proceeds else None,
            "Commissions & Fees": float(self.commissions_fees),
            "Net Proceeds": float(self.net_proceeds) if self.net_proceeds else None,
            "Expiration Date": self.expiration_date,
            "Strike": float(self.strike_price) if self.strike_price else None,
            "Strategy": self.strategy,
            "Notes": self.notes,
            "Tags": self.tags,
            "Paper Trade": "Yes" if self.is_paper_trade else "No",
            "Trade ID": self.trade_id
        }

    @classmethod
    def from_traderterminal_trade(
        cls,
        trade_result,
        account_name: str,
        strategy_name: Optional[str] = None,
        is_paper: bool = False,
        notes: Optional[str] = None
    ) -> "TradeNoteTradeData":
        """
        Create TradeNote trade data from TraderTerminal trade result.
        
        Args:
            trade_result: TradeResult from strategy performance tracker
            account_name: Trading account identifier
            strategy_name: Strategy name if available
            is_paper: Whether this is a paper trade
            notes: Additional notes for the trade
        """
        
        # Convert timestamp to date and time components
        trade_dt = trade_result.timestamp if isinstance(trade_result.timestamp, datetime) else datetime.fromisoformat(trade_result.timestamp)
        trade_date = trade_dt.strftime("%m/%d/%Y")
        settlement_date = trade_date  # Same day for most instruments
        exec_time = trade_dt.strftime("%H:%M:%S")
        
        # Determine instrument type
        symbol = trade_result.symbol.upper()
        if symbol in ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL", "NG"]:
            instrument_type = "future"
        elif "/" in symbol or "C" in symbol or "P" in symbol:
            instrument_type = "option"
        else:
            instrument_type = "stock"
        
        # Calculate gross and net proceeds
        gross_proceeds = trade_result.pnl
        net_proceeds = trade_result.net_pnl if hasattr(trade_result, 'net_pnl') else (
            gross_proceeds - trade_result.commission - abs(getattr(trade_result, 'slippage', 0))
        )
        
        # Build notes
        trade_notes = []
        if notes:
            trade_notes.append(notes)
        if hasattr(trade_result, 'mode') and trade_result.mode:
            trade_notes.append(f"Mode: {trade_result.mode}")
        if hasattr(trade_result, 'set_number'):
            trade_notes.append(f"Set #{trade_result.set_number}, Trade #{trade_result.trade_number_in_set}")
        
        return cls(
            account=account_name,
            trade_date=trade_date,
            settlement_date=settlement_date,
            currency="USD",
            type=instrument_type,
            side="Buy" if trade_result.side == "long" else "Sell",
            symbol=symbol,
            quantity=trade_result.quantity,
            price=Decimal(str(trade_result.exit_price)),  # Use exit price for logging
            exec_time=exec_time,
            gross_proceeds=Decimal(str(gross_proceeds)),
            commissions_fees=Decimal(str(trade_result.commission)),
            net_proceeds=Decimal(str(net_proceeds)),
            strategy=strategy_name or trade_result.strategy_id,
            notes=" | ".join(trade_notes) if trade_notes else None,
            tags=f"win,{instrument_type}" if trade_result.win else f"loss,{instrument_type}",
            is_paper_trade=is_paper,
            trade_id=trade_result.trade_id
        )


class TradeNoteExecutionData(BaseModel):
    """Data for a single execution to be sent to TradeNote"""
    data: List[TradeNoteTradeData]
    selected_broker: str
    upload_mfe_prices: bool = False

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to TradeNote API payload format"""
        return {
            "data": [trade.to_tradenote_format() for trade in self.data],
            "selectedBroker": self.selected_broker,
            "uploadMfePrices": self.upload_mfe_prices
        }


class TradeNoteResponse(BaseModel):
    """Response from TradeNote API"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class TradeNoteCalendarData(BaseModel):
    """Calendar heat-map data from TradeNote"""
    date: str
    value: Decimal
    trades_count: int
    win_rate: Optional[Decimal] = None

    class Config:
        json_encoders = {
            Decimal: str
        }