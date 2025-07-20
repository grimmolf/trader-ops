"""
Tradovate Market Data Integration

Provides real-time and historical market data from Tradovate including:
- Real-time quotes via WebSocket
- Historical bars and candles
- Symbol information and contract details
- Market status and trading hours
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Union
from datetime import datetime, timedelta
import time

import websockets
from pydantic import BaseModel, Field

from .auth import TradovateAuth

logger = logging.getLogger(__name__)


class TradovateQuote(BaseModel):
    """Real-time quote from Tradovate"""
    
    symbol: str
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    open_price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Tradovate specific fields
    contract_id: Optional[int] = None
    tick_size: Optional[float] = None
    point_value: Optional[float] = None
    
    @classmethod
    def from_tradovate_tick(cls, tick_data: dict) -> "TradovateQuote":
        """Create quote from Tradovate tick data"""
        return cls(
            symbol=tick_data.get("symbol", ""),
            timestamp=datetime.utcnow(),
            bid=tick_data.get("bid"),
            ask=tick_data.get("ask"), 
            last=tick_data.get("last"),
            volume=tick_data.get("volume"),
            contract_id=tick_data.get("contractId")
        )


class TradovateBar(BaseModel):
    """Historical bar from Tradovate"""
    
    timestamp: datetime
    open_price: float = Field(..., alias="o")
    high: float = Field(..., alias="h") 
    low: float = Field(..., alias="l")
    close: float = Field(..., alias="c")
    volume: int = Field(..., alias="v")
    
    # Tradovate specific
    contract_id: Optional[int] = None
    symbol: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True


class ContractInfo(BaseModel):
    """Futures contract information"""
    
    id: int
    symbol: str
    name: str
    tick_size: float
    point_value: float
    exchange: str
    expiration_date: Optional[datetime] = None
    is_active: bool = True
    
    # Trading specifications
    initial_margin: Optional[float] = None
    maintenance_margin: Optional[float] = None
    min_price_increment: Optional[float] = None
    
    @classmethod
    def from_tradovate_contract(cls, contract_data: dict) -> "ContractInfo":
        """Create from Tradovate contract response"""
        return cls(
            id=contract_data.get("id"),
            symbol=contract_data.get("name", ""),
            name=contract_data.get("fullName", ""),
            tick_size=contract_data.get("tickSize", 0.01),
            point_value=contract_data.get("pointValue", 1.0),
            exchange=contract_data.get("exchange", ""),
            initial_margin=contract_data.get("initialMargin"),
            maintenance_margin=contract_data.get("maintenanceMargin")
        )


class TradovateMarketData:
    """
    Tradovate market data client.
    
    Provides access to real-time and historical market data including:
    - WebSocket streaming quotes
    - Historical bars and charts  
    - Contract specifications
    - Market hours and status
    """
    
    def __init__(self, auth: TradovateAuth):
        self.auth = auth
        self._ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self._subscriptions: Dict[str, bool] = {}
        self._quote_callbacks: List[callable] = []
        self._running = False
        
        logger.info("Initialized Tradovate market data client")
    
    async def get_contract_info(self, symbol: str) -> Optional[ContractInfo]:
        """
        Get contract information for a symbol.
        
        Args:
            symbol: Symbol to lookup (e.g., "ES", "NQ")
            
        Returns:
            ContractInfo: Contract details or None if not found
        """
        try:
            # Search for active contract by symbol
            response = await self.auth.make_authenticated_request(
                "GET",
                "/contract/find",
                params={"name": symbol}
            )
            
            if response.status_code == 200:
                contracts = response.json()
                if contracts:
                    # Return the first active contract
                    contract_data = contracts[0]
                    return ContractInfo.from_tradovate_contract(contract_data)
            
            logger.warning(f"Contract not found for symbol: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting contract info for {symbol}: {e}")
            return None
    
    async def get_quote(self, symbol: str) -> Optional[TradovateQuote]:
        """
        Get current quote for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            TradovateQuote: Current quote or None if unavailable
        """
        try:
            # First get contract ID
            contract = await self.get_contract_info(symbol)
            if not contract:
                return None
            
            # Get current quote
            response = await self.auth.make_authenticated_request(
                "GET",
                "/md/getQuote",
                params={"contractId": contract.id}
            )
            
            if response.status_code == 200:
                quote_data = response.json()
                return TradovateQuote(
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    bid=quote_data.get("bid"),
                    ask=quote_data.get("ask"),
                    last=quote_data.get("last"),
                    volume=quote_data.get("volume"),
                    contract_id=contract.id,
                    tick_size=contract.tick_size,
                    point_value=contract.point_value
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    async def get_quotes(self, symbols: List[str]) -> List[TradovateQuote]:
        """
        Get quotes for multiple symbols.
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            List[TradovateQuote]: List of quotes
        """
        quotes = []
        
        # Get quotes concurrently
        tasks = [self.get_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, TradovateQuote):
                quotes.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error in batch quote request: {result}")
        
        return quotes
    
    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1m",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        count: int = 100
    ) -> List[TradovateBar]:
        """
        Get historical bars for a symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: Bar timeframe (1m, 5m, 15m, 1h, 1d)
            start_date: Start date for historical data
            end_date: End date for historical data  
            count: Number of bars to retrieve
            
        Returns:
            List[TradovateBar]: Historical bars
        """
        try:
            # Get contract info
            contract = await self.get_contract_info(symbol)
            if not contract:
                return []
            
            # Build parameters
            params = {
                "contractId": contract.id,
                "unit": self._convert_timeframe(timeframe),
                "count": count
            }
            
            if start_date:
                params["startTime"] = int(start_date.timestamp() * 1000)
            if end_date:
                params["endTime"] = int(end_date.timestamp() * 1000)
            
            # Make request
            response = await self.auth.make_authenticated_request(
                "GET",
                "/md/getbars",
                params=params
            )
            
            if response.status_code == 200:
                bars_data = response.json()
                bars = []
                
                for bar_data in bars_data.get("bars", []):
                    bar = TradovateBar(
                        timestamp=datetime.fromtimestamp(bar_data["timestamp"] / 1000),
                        o=bar_data["open"],
                        h=bar_data["high"],
                        l=bar_data["low"],
                        c=bar_data["close"],
                        v=bar_data["volume"],
                        contract_id=contract.id,
                        symbol=symbol
                    )
                    bars.append(bar)
                
                return bars
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting historical bars for {symbol}: {e}")
            return []
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to Tradovate format"""
        timeframe_map = {
            "1m": "Minute",
            "5m": "5Min", 
            "15m": "15Min",
            "30m": "30Min",
            "1h": "Hour",
            "4h": "4Hour",
            "1d": "Daily",
            "1w": "Weekly"
        }
        return timeframe_map.get(timeframe, "Minute")
    
    async def start_websocket_stream(self) -> None:
        """Start WebSocket connection for real-time data"""
        if self._running:
            logger.warning("WebSocket stream already running")
            return
        
        self._running = True
        logger.info("Starting Tradovate WebSocket stream...")
        
        try:
            token = await self.auth.get_access_token()
            ws_url = f"{self.auth.ws_url}?token={token}"
            
            async with websockets.connect(ws_url) as websocket:
                self._ws_connection = websocket
                logger.info("WebSocket connected to Tradovate")
                
                # Start message handler
                await self._handle_websocket_messages()
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            self._running = False
            self._ws_connection = None
            logger.info("WebSocket disconnected")
    
    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages"""
        if not self._ws_connection:
            return
        
        try:
            async for message in self._ws_connection:
                try:
                    data = json.loads(message)
                    await self._process_websocket_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in WebSocket message: {message}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket message handler error: {e}")
    
    async def _process_websocket_message(self, data: dict):
        """Process individual WebSocket message"""
        msg_type = data.get("e")  # Event type
        
        if msg_type == "md":  # Market data
            # Process market data update
            tick_data = data.get("d", {})
            if tick_data:
                quote = TradovateQuote.from_tradovate_tick(tick_data)
                
                # Notify callbacks
                for callback in self._quote_callbacks:
                    try:
                        await callback(quote)
                    except Exception as e:
                        logger.error(f"Error in quote callback: {e}")
        
        elif msg_type == "heartbeat":
            # Respond to heartbeat
            if self._ws_connection:
                await self._ws_connection.send(json.dumps({"e": "heartbeat"}))
        
        else:
            logger.debug(f"Received WebSocket message: {data}")
    
    async def subscribe_quotes(self, symbols: List[str]) -> None:
        """
        Subscribe to real-time quotes for symbols.
        
        Args:
            symbols: List of symbols to subscribe to
        """
        if not self._ws_connection:
            logger.error("WebSocket not connected")
            return
        
        try:
            # Get contract IDs for symbols
            contract_ids = []
            for symbol in symbols:
                contract = await self.get_contract_info(symbol)
                if contract:
                    contract_ids.append(contract.id)
                    self._subscriptions[symbol] = True
            
            if contract_ids:
                # Send subscription message
                subscribe_msg = {
                    "op": "subscribe",
                    "args": ["md/subscribeQuote", {"contractIds": contract_ids}]
                }
                
                await self._ws_connection.send(json.dumps(subscribe_msg))
                logger.info(f"Subscribed to quotes for: {symbols}")
                
        except Exception as e:
            logger.error(f"Error subscribing to quotes: {e}")
    
    async def unsubscribe_quotes(self, symbols: List[str]) -> None:
        """Unsubscribe from real-time quotes"""
        if not self._ws_connection:
            return
        
        try:
            contract_ids = []
            for symbol in symbols:
                contract = await self.get_contract_info(symbol)
                if contract:
                    contract_ids.append(contract.id)
                    self._subscriptions.pop(symbol, None)
            
            if contract_ids:
                unsubscribe_msg = {
                    "op": "unsubscribe", 
                    "args": ["md/subscribeQuote", {"contractIds": contract_ids}]
                }
                
                await self._ws_connection.send(json.dumps(unsubscribe_msg))
                logger.info(f"Unsubscribed from quotes for: {symbols}")
                
        except Exception as e:
            logger.error(f"Error unsubscribing from quotes: {e}")
    
    def add_quote_callback(self, callback: callable):
        """Add callback for quote updates"""
        self._quote_callbacks.append(callback)
    
    def remove_quote_callback(self, callback: callable):
        """Remove quote callback"""
        if callback in self._quote_callbacks:
            self._quote_callbacks.remove(callback)
    
    async def stop_websocket_stream(self):
        """Stop WebSocket stream"""
        self._running = False
        if self._ws_connection:
            await self._ws_connection.close()
            self._ws_connection = None
        logger.info("WebSocket stream stopped")
    
    async def close(self):
        """Close market data client"""
        await self.stop_websocket_stream()
        logger.info("Market data client closed")