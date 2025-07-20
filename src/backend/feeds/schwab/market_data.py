"""
Charles Schwab Market Data API

Provides real-time quotes, historical data, and market information
for stocks, options, and other securities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from .auth import SchwabAuth

logger = logging.getLogger(__name__)


class QuoteFields(Enum):
    """Available quote fields from Schwab API"""
    QUOTE = "quote"
    FUNDAMENTAL = "fundamental"
    EXTENDED = "extended"
    REFERENCE = "reference"
    REGULAR = "regular"


class SchwabQuote(BaseModel):
    """Market quote from Schwab API"""
    
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    close_price: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Extended fields
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    
    @classmethod
    def from_schwab_data(cls, symbol: str, data: Dict[str, Any]) -> "SchwabQuote":
        """Create quote from Schwab API response"""
        quote_data = data.get("quote", {})
        fundamental_data = data.get("fundamental", {})
        
        return cls(
            symbol=symbol,
            bid=quote_data.get("bidPrice"),
            ask=quote_data.get("askPrice"),
            last=quote_data.get("lastPrice"),
            volume=quote_data.get("totalVolume"),
            bid_size=quote_data.get("bidSize"),
            ask_size=quote_data.get("askSize"),
            change=quote_data.get("netChange"),
            change_percent=quote_data.get("netPercentChangeInDouble"),
            high=quote_data.get("highPrice"),
            low=quote_data.get("lowPrice"),
            open_price=quote_data.get("openPrice"),
            close_price=quote_data.get("closePrice"),
            market_cap=fundamental_data.get("marketCap"),
            pe_ratio=fundamental_data.get("peRatio"),
            dividend_yield=fundamental_data.get("divYield"),
            beta=fundamental_data.get("beta")
        )


class HistoricalData(BaseModel):
    """Historical price data"""
    
    symbol: str
    candles: List[Dict[str, Any]]
    period_type: str
    period: int
    frequency_type: str
    frequency: int
    
    @classmethod
    def from_schwab_data(cls, symbol: str, data: Dict[str, Any]) -> "HistoricalData":
        """Create historical data from Schwab API response"""
        return cls(
            symbol=symbol,
            candles=data.get("candles", []),
            period_type=data.get("periodType", ""),
            period=data.get("period", 0),
            frequency_type=data.get("frequencyType", ""),
            frequency=data.get("frequency", 0)
        )


class SchwabMarketData:
    """
    Schwab market data API client.
    
    Provides access to:
    - Real-time quotes
    - Historical price data
    - Options chains
    - Market hours information
    """
    
    def __init__(self, auth: SchwabAuth):
        self.auth = auth
        self.base_url = "https://api.schwabapi.com/trader/v1"
        
    async def get_quote(self, symbol: str, fields: Optional[List[QuoteFields]] = None) -> SchwabQuote:
        """
        Get quote for a single symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            fields: Optional list of quote fields to include
            
        Returns:
            SchwabQuote: Quote data
        """
        quotes = await self.get_quotes([symbol], fields)
        if symbol in quotes:
            return quotes[symbol]
        else:
            raise Exception(f"No quote data received for symbol: {symbol}")
    
    async def get_quotes(self, symbols: List[str], fields: Optional[List[QuoteFields]] = None) -> Dict[str, SchwabQuote]:
        """
        Get quotes for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            fields: Optional list of quote fields to include
            
        Returns:
            Dict[str, SchwabQuote]: Symbol to quote mapping
        """
        if not symbols:
            return {}
        
        # Default fields if none specified
        if fields is None:
            fields = [QuoteFields.QUOTE, QuoteFields.FUNDAMENTAL]
        
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Prepare parameters
            params = {
                "symbols": ",".join(symbols),
                "fields": ",".join([field.value for field in fields])
            }
            
            response = await client.get(
                f"{self.base_url}/marketdata/quotes",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse quotes
            quotes = {}
            for symbol, symbol_data in data.items():
                try:
                    quotes[symbol] = SchwabQuote.from_schwab_data(symbol, symbol_data)
                except Exception as e:
                    logger.warning(f"Failed to parse quote for {symbol}: {e}")
            
            logger.info(f"Retrieved quotes for {len(quotes)}/{len(symbols)} symbols")
            return quotes
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting quotes: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get quotes: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting quotes: {e}")
            raise
    
    async def get_historical_data(
        self,
        symbol: str,
        period_type: str = "month",
        period: int = 1,
        frequency_type: str = "daily",
        frequency: int = 1,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> HistoricalData:
        """
        Get historical price data for a symbol.
        
        Args:
            symbol: Stock symbol
            period_type: Type of period (day, month, year, ytd)
            period: Number of periods
            frequency_type: Type of frequency (minute, daily, weekly, monthly)
            frequency: Frequency value
            start_date: Optional start date for date range
            end_date: Optional end date for date range
            
        Returns:
            HistoricalData: Historical price data
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Prepare parameters
            params = {
                "periodType": period_type,
                "period": period,
                "frequencyType": frequency_type,
                "frequency": frequency
            }
            
            # Add date range if specified
            if start_date:
                params["startDate"] = int(start_date.timestamp() * 1000)
            if end_date:
                params["endDate"] = int(end_date.timestamp() * 1000)
            
            response = await client.get(
                f"{self.base_url}/marketdata/{symbol}/pricehistory",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            historical_data = HistoricalData.from_schwab_data(symbol, data)
            logger.info(f"Retrieved {len(historical_data.candles)} historical candles for {symbol}")
            
            return historical_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting historical data: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get historical data: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            raise
    
    async def search_symbols(self, query: str, projection: str = "symbol-search") -> List[Dict[str, Any]]:
        """
        Search for symbols by name or symbol.
        
        Args:
            query: Search query
            projection: Search projection type
            
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
            
            params = {
                "symbol": query,
                "projection": projection
            }
            
            response = await client.get(
                f"{self.base_url}/marketdata/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract search results
            results = []
            for symbol, symbol_data in data.items():
                results.append({
                    "symbol": symbol,
                    "description": symbol_data.get("description", ""),
                    "exchange": symbol_data.get("exchange", ""),
                    "assetType": symbol_data.get("assetType", "")
                })
            
            logger.info(f"Found {len(results)} symbols for query: {query}")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching symbols: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to search symbols: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            raise
    
    async def get_market_hours(self, markets: List[str], date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get market hours for specified markets.
        
        Args:
            markets: List of market names (EQUITY, OPTION, BOND, etc.)
            date: Date to check (defaults to today)
            
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
            
            # Format date if provided
            date_str = date.strftime("%Y-%m-%d") if date else datetime.now().strftime("%Y-%m-%d")
            
            params = {
                "markets": ",".join(markets),
                "date": date_str
            }
            
            response = await client.get(
                f"{self.base_url}/marketdata/markets",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Retrieved market hours for {len(markets)} markets")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting market hours: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get market hours: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting market hours: {e}")
            raise
    
    async def get_options_chain(
        self,
        symbol: str,
        strike_count: int = 10,
        include_quotes: bool = True,
        strategy: str = "SINGLE",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get options chain for a symbol.
        
        Args:
            symbol: Underlying symbol
            strike_count: Number of strikes to include
            include_quotes: Include underlying quotes
            strategy: Options strategy (SINGLE, ANALYTICAL, COVERED, VERTICAL, etc.)
            from_date: Start date for expiration range
            to_date: End date for expiration range
            
        Returns:
            Dict[str, Any]: Options chain data
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
                "strikeCount": strike_count,
                "includeQuotes": str(include_quotes).lower(),
                "strategy": strategy
            }
            
            # Add date range if specified
            if from_date:
                params["fromDate"] = from_date.strftime("%Y-%m-%d")
            if to_date:
                params["toDate"] = to_date.strftime("%Y-%m-%d")
            
            response = await client.get(
                f"{self.base_url}/marketdata/chains",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Retrieved options chain for {symbol}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting options chain: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get options chain: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            raise