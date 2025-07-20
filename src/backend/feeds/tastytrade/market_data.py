"""
Tastytrade Market Data API

Provides real-time quotes, historical data, and market information
for stocks, options, and futures.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from decimal import Decimal

import httpx
from pydantic import BaseModel, Field

from .auth import TastytradeAuth

logger = logging.getLogger(__name__)


class InstrumentType(Enum):
    """Instrument types supported by Tastytrade"""
    EQUITY = "Equity"
    OPTION = "Equity Option"
    FUTURE = "Future"
    FUTURE_OPTION = "Future Option"
    CRYPTO = "Cryptocurrency"


class TastytradeQuote(BaseModel):
    """Market quote from Tastytrade API"""
    
    symbol: str
    instrument_type: InstrumentType
    
    # Price data
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Optional[Decimal] = None
    mark: Optional[Decimal] = None  # Mid-market price
    
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
    
    # Volume and interest
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    
    # Greeks (for options)
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    rho: Optional[Decimal] = None
    implied_volatility: Optional[Decimal] = None
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quote_time: Optional[datetime] = None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid price from bid/ask"""
        if self.mark:
            return self.mark
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
    def from_tastytrade_data(cls, data: Dict[str, Any]) -> "TastytradeQuote":
        """Create quote from Tastytrade API response"""
        return cls(
            symbol=data.get("symbol", ""),
            instrument_type=InstrumentType(data.get("instrument-type", "Equity")),
            bid=Decimal(str(data["bid"])) if data.get("bid") else None,
            ask=Decimal(str(data["ask"])) if data.get("ask") else None,
            last=Decimal(str(data["last"])) if data.get("last") else None,
            mark=Decimal(str(data["mark"])) if data.get("mark") else None,
            bid_size=data.get("bid-size"),
            ask_size=data.get("ask-size"),
            last_size=data.get("last-size"),
            high=Decimal(str(data["high"])) if data.get("high") else None,
            low=Decimal(str(data["low"])) if data.get("low") else None,
            open_price=Decimal(str(data["open"])) if data.get("open") else None,
            close_price=Decimal(str(data["close"])) if data.get("close") else None,
            change=Decimal(str(data["change"])) if data.get("change") else None,
            change_percent=Decimal(str(data["change-percent"])) if data.get("change-percent") else None,
            volume=data.get("volume"),
            open_interest=data.get("open-interest"),
            delta=Decimal(str(data["delta"])) if data.get("delta") else None,
            gamma=Decimal(str(data["gamma"])) if data.get("gamma") else None,
            theta=Decimal(str(data["theta"])) if data.get("theta") else None,
            vega=Decimal(str(data["vega"])) if data.get("vega") else None,
            rho=Decimal(str(data["rho"])) if data.get("rho") else None,
            implied_volatility=Decimal(str(data["implied-volatility"])) if data.get("implied-volatility") else None,
            quote_time=datetime.fromisoformat(data["quote-time"]) if data.get("quote-time") else None
        )


class TastytradeMarketData:
    """
    Tastytrade market data API client.
    
    Provides access to:
    - Real-time quotes for stocks, options, futures
    - Historical price data
    - Options chains
    - Market hours information
    """
    
    def __init__(self, auth: TastytradeAuth):
        self.auth = auth
        self.base_url = auth.api_base_url
        
    async def get_quote(self, symbol: str) -> TastytradeQuote:
        """
        Get quote for a single symbol.
        
        Args:
            symbol: Symbol (e.g., 'AAPL', 'AAPL  240119C00150000')
            
        Returns:
            TastytradeQuote: Quote data
        """
        quotes = await self.get_quotes([symbol])
        if symbol in quotes:
            return quotes[symbol]
        else:
            raise Exception(f"No quote data received for symbol: {symbol}")
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, TastytradeQuote]:
        """
        Get quotes for multiple symbols.
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dict[str, TastytradeQuote]: Symbol to quote mapping
        """
        if not symbols:
            return {}
        
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Tastytrade API uses comma-separated symbols
            symbols_param = ",".join(symbols)
            
            response = await client.get(
                f"{self.base_url}/market-data/quotes",
                headers=headers,
                params={"symbols": symbols_param}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse quotes
            quotes = {}
            if "data" in data and "items" in data["data"]:
                for quote_data in data["data"]["items"]:
                    try:
                        quote = TastytradeQuote.from_tastytrade_data(quote_data)
                        quotes[quote.symbol] = quote
                    except Exception as e:
                        logger.warning(f"Failed to parse quote for {quote_data.get('symbol', 'unknown')}: {e}")
            
            logger.info(f"Retrieved quotes for {len(quotes)}/{len(symbols)} symbols")
            return quotes
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting quotes: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get quotes: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting quotes: {e}")
            raise
    
    async def get_option_chain(
        self,
        symbol: str,
        expiration_date: Optional[str] = None,
        strike_price: Optional[float] = None,
        option_type: Optional[str] = None  # "C" for calls, "P" for puts
    ) -> List[Dict[str, Any]]:
        """
        Get options chain for a symbol.
        
        Args:
            symbol: Underlying symbol (e.g., 'AAPL')
            expiration_date: Specific expiration date (YYYY-MM-DD)
            strike_price: Specific strike price
            option_type: Filter by option type ('C' or 'P')
            
        Returns:
            List[Dict[str, Any]]: Options chain data
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if expiration_date:
                params["expiration-date"] = expiration_date
            if strike_price:
                params["strike-price"] = strike_price
            if option_type:
                params["option-type"] = option_type
            
            response = await client.get(
                f"{self.base_url}/instruments/equity-options",
                headers=headers,
                params={"underlying-symbol": symbol, **params}
            )
            response.raise_for_status()
            
            data = response.json()
            
            options = []
            if "data" in data and "items" in data["data"]:
                options = data["data"]["items"]
            
            logger.info(f"Retrieved {len(options)} options for {symbol}")
            return options
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting option chain: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get option chain: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            raise
    
    async def search_symbols(self, query: str, instrument_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for symbols by name or symbol.
        
        Args:
            query: Search query
            instrument_types: Filter by instrument types
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {"symbol": query}
            if instrument_types:
                params["instrument-type"] = ",".join(instrument_types)
            
            response = await client.get(
                f"{self.base_url}/instruments/equity-options",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            if "data" in data and "items" in data["data"]:
                for item in data["data"]["items"]:
                    results.append({
                        "symbol": item.get("symbol", ""),
                        "description": item.get("description", ""),
                        "instrument_type": item.get("instrument-type", ""),
                        "exchange": item.get("exchange", "")
                    })
            
            logger.info(f"Found {len(results)} symbols for query: {query}")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching symbols: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to search symbols: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            raise
    
    async def get_market_hours(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market hours for specified date.
        
        Args:
            date: Date to check (YYYY-MM-DD, defaults to today)
            
        Returns:
            Dict[str, Any]: Market hours information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if date:
                params["date"] = date
            
            response = await client.get(
                f"{self.base_url}/market-hours",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.info("Retrieved market hours information")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting market hours: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get market hours: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting market hours: {e}")
            raise
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            timeframe: Data timeframe (1Minute, 5Minute, 15Minute, 1Hour, 1Day)
            start_time: Start time for data
            end_time: End time for data
            
        Returns:
            List[Dict[str, Any]]: Historical OHLCV data
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {
                "symbol": symbol,
                "timeframe": timeframe
            }
            
            if start_time:
                params["start-time"] = start_time.isoformat()
            if end_time:
                params["end-time"] = end_time.isoformat()
            
            response = await client.get(
                f"{self.base_url}/market-data/historical",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            candles = []
            if "data" in data and "items" in data["data"]:
                candles = data["data"]["items"]
            
            logger.info(f"Retrieved {len(candles)} historical bars for {symbol}")
            return candles
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting historical data: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get historical data: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            raise