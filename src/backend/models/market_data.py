"""
Market data models for trading platform.
Follows TradingView UDF protocol and trading industry standards.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, validator
import time


class TimeFrame(str, Enum):
    """Standard trading timeframes"""
    TICK = "tick"
    MINUTE_1 = "1"
    MINUTE_5 = "5" 
    MINUTE_15 = "15"
    MINUTE_30 = "30"
    HOUR_1 = "60"
    HOUR_4 = "240"
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


class SymbolType(str, Enum):
    """Symbol asset classes"""
    STOCK = "stock"
    OPTION = "option"
    FUTURE = "future"
    FOREX = "forex"
    CRYPTO = "crypto"
    INDEX = "index"
    ETF = "etf"


class Candle(BaseModel):
    """
    OHLCV candle data model.
    Timestamp in epoch seconds for TradingView compatibility.
    """
    ts: int = Field(..., description="Timestamp in epoch seconds")
    o: float = Field(..., description="Open price", ge=0)
    h: float = Field(..., description="High price", ge=0) 
    l: float = Field(..., description="Low price", ge=0)
    c: float = Field(..., description="Close price", ge=0)
    v: float = Field(..., description="Volume", ge=0)
    
    @validator('h')
    def high_must_be_highest(cls, v, values):
        """Validate high >= open, close, low"""
        if 'o' in values and v < values['o']:
            raise ValueError('High must be >= open')
        if 'l' in values and v < values['l']:
            raise ValueError('High must be >= low')
        return v
    
    @validator('l')
    def low_must_be_lowest(cls, v, values):
        """Validate low <= open, close, high"""
        if 'o' in values and v > values['o']:
            raise ValueError('Low must be <= open')
        return v
    
    @classmethod
    def from_tradier(cls, data: Dict[str, Any]) -> "Candle":
        """Convert Tradier API response to Candle"""
        # Tradier returns ISO8601, convert to epoch seconds
        ts = int(datetime.fromisoformat(data['date'].replace('Z', '+00:00')).timestamp())
        return cls(
            ts=ts,
            o=float(data['open']),
            h=float(data['high']),
            l=float(data['low']),
            c=float(data['close']),
            v=float(data['volume'])
        )
    
    @classmethod
    def from_ccxt(cls, data: List[Any]) -> "Candle":
        """Convert CCXT OHLCV array to Candle"""
        return cls(
            ts=int(data[0] / 1000),  # CCXT uses milliseconds
            o=float(data[1]),
            h=float(data[2]),
            l=float(data[3]),
            c=float(data[4]),
            v=float(data[5])
        )


class Quote(BaseModel):
    """Real-time quote data"""
    symbol: str = Field(..., description="Trading symbol")
    timestamp: int = Field(..., description="Quote timestamp in epoch seconds")
    bid: Optional[float] = Field(None, description="Bid price", ge=0)
    ask: Optional[float] = Field(None, description="Ask price", ge=0)
    bid_size: Optional[float] = Field(None, description="Bid size", ge=0)
    ask_size: Optional[float] = Field(None, description="Ask size", ge=0)
    last: Optional[float] = Field(None, description="Last trade price", ge=0)
    volume: Optional[float] = Field(None, description="Volume", ge=0)
    change: Optional[float] = Field(None, description="Price change")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    
    @classmethod
    def from_tradier(cls, data: Dict[str, Any]) -> "Quote":
        """Convert Tradier quote to Quote model"""
        return cls(
            symbol=data.get('symbol', ''),
            timestamp=int(time.time()),  # Current time if not provided
            bid=data.get('bid'),
            ask=data.get('ask'),
            bid_size=data.get('bidsize'),
            ask_size=data.get('asksize'),
            last=data.get('last'),
            volume=data.get('volume'),
            change=data.get('change'),
            change_percent=data.get('change_percentage')
        )


class Trade(BaseModel):
    """Individual trade execution"""
    symbol: str = Field(..., description="Trading symbol")
    timestamp: int = Field(..., description="Trade timestamp in epoch seconds")
    price: float = Field(..., description="Trade price", gt=0)
    size: float = Field(..., description="Trade size", gt=0)
    side: Optional[str] = Field(None, description="Buy/Sell side")
    trade_id: Optional[str] = Field(None, description="Unique trade ID")


class Symbol(BaseModel):
    """Symbol metadata for TradingView widget"""
    symbol: str = Field(..., description="Primary symbol identifier")
    full_name: str = Field(..., description="Full company/asset name")
    description: str = Field(..., description="Symbol description")
    exchange: str = Field(..., description="Exchange code")
    type: SymbolType = Field(..., description="Asset type")
    session: str = Field(default="0930-1600", description="Trading session hours")
    timezone: str = Field(default="America/New_York", description="Trading timezone")
    minmov: int = Field(default=1, description="Minimum price movement")
    pricescale: int = Field(default=100, description="Price scale factor")
    has_intraday: bool = Field(default=True, description="Supports intraday data")
    has_weekly: bool = Field(default=True, description="Supports weekly data")
    has_daily: bool = Field(default=True, description="Supports daily data")
    supported_resolutions: List[str] = Field(
        default=["1", "5", "15", "30", "60", "240", "D", "W"],
        description="Supported timeframes"
    )
    
    @classmethod
    def from_tradier_symbol(cls, symbol: str, company_name: str = "") -> "Symbol":
        """Create Symbol from Tradier symbol info"""
        return cls(
            symbol=symbol,
            full_name=company_name or symbol,
            description=f"{company_name} ({symbol})" if company_name else symbol,
            exchange="NASDAQ/NYSE",  # Simplified for now
            type=SymbolType.STOCK,  # Default to stock
            session="0930-1600",
            timezone="America/New_York"
        )


class HistoryRequest(BaseModel):
    """Request for historical data"""
    symbol: str = Field(..., description="Trading symbol")
    resolution: str = Field(..., description="Timeframe/resolution")
    from_ts: int = Field(..., description="Start timestamp (epoch seconds)")
    to_ts: int = Field(..., description="End timestamp (epoch seconds)")
    countback: Optional[int] = Field(None, description="Number of bars to return")
    
    @validator('to_ts')
    def to_must_be_after_from(cls, v, values):
        """Validate end time is after start time"""
        if 'from_ts' in values and v <= values['from_ts']:
            raise ValueError('to_ts must be greater than from_ts')
        return v


class HistoryResponse(BaseModel):
    """Response containing historical candle data"""
    symbol: str = Field(..., description="Trading symbol")
    resolution: str = Field(..., description="Timeframe/resolution")
    status: str = Field(default="ok", description="Response status")
    bars: List[Candle] = Field(default_factory=list, description="OHLCV candle data")
    next_time: Optional[int] = Field(None, description="Next available timestamp")
    
    @property
    def times(self) -> List[int]:
        """Extract timestamps for TradingView UDF format"""
        return [bar.ts for bar in self.bars]
    
    @property
    def opens(self) -> List[float]:
        """Extract open prices for TradingView UDF format"""
        return [bar.o for bar in self.bars]
    
    @property
    def highs(self) -> List[float]:
        """Extract high prices for TradingView UDF format"""
        return [bar.h for bar in self.bars]
    
    @property
    def lows(self) -> List[float]:
        """Extract low prices for TradingView UDF format"""
        return [bar.l for bar in self.bars]
    
    @property
    def closes(self) -> List[float]:
        """Extract close prices for TradingView UDF format"""
        return [bar.c for bar in self.bars]
    
    @property
    def volumes(self) -> List[float]:
        """Extract volumes for TradingView UDF format"""
        return [bar.v for bar in self.bars]
    
    def to_udf_format(self) -> Dict[str, Any]:
        """Convert to TradingView UDF history format"""
        if not self.bars:
            return {"s": "no_data"}
        
        return {
            "s": self.status,
            "t": self.times,
            "o": self.opens,
            "h": self.highs,
            "l": self.lows,
            "c": self.closes,
            "v": self.volumes,
            "nextTime": self.next_time
        }