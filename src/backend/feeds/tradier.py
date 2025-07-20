"""
Tradier API connector for market data and order execution.
Handles REST API calls and WebSocket streaming for real-time data.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator, Any
from datetime import datetime, timezone

import aiohttp
import websockets
from pydantic import ValidationError

from ..models.market_data import (
    Candle, Quote, Symbol, HistoryRequest, HistoryResponse, TimeFrame
)
from ..models.execution import Order, Execution, OrderStatus, Account, Position


logger = logging.getLogger(__name__)


class TradierError(Exception):
    """Tradier API specific error"""
    pass


class TradierConnector:
    """
    Tradier API connector for market data and trading operations.
    Supports both sandbox and production environments.
    """
    
    def __init__(
        self,
        api_key: str,
        account_id: Optional[str] = None,
        base_url: str = "https://api.tradier.com",
        ws_url: str = "wss://ws.tradier.com",
        session_timeout: int = 30
    ):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url.rstrip("/")
        self.ws_url = ws_url
        self.session_timeout = session_timeout
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self._ws_session_id: Optional[str] = None
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 10 requests per second max
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "TraderOps/1.0"
            }
            timeout = aiohttp.ClientTimeout(total=self.session_timeout)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self._session
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Tradier API with error handling"""
        await self._rate_limit()
        
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with session.request(method, url, params=params, data=data) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    return response_data
                elif response.status == 401:
                    raise TradierError("Authentication failed - check API key")
                elif response.status == 403:
                    raise TradierError("Access forbidden - check permissions")
                elif response.status == 429:
                    raise TradierError("Rate limit exceeded")
                else:
                    error_msg = response_data.get("fault", {}).get("faultstring", "Unknown error")
                    raise TradierError(f"API error {response.status}: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise TradierError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise TradierError(f"Invalid JSON response: {e}")
    
    # ========================================================================
    # Market Data Methods
    # ========================================================================
    
    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get current quotes for symbols"""
        if not symbols:
            return []
        
        params = {"symbols": ",".join(symbols)}
        
        try:
            response = await self._make_request("GET", "/v1/markets/quotes", params=params)
            quotes_data = response.get("quotes", {}).get("quote", [])
            
            # Handle single quote vs list of quotes
            if isinstance(quotes_data, dict):
                quotes_data = [quotes_data]
            
            quotes = []
            for quote_data in quotes_data:
                try:
                    quote = Quote.from_tradier(quote_data)
                    quotes.append(quote)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse quote for {quote_data.get('symbol', 'unknown')}: {e}")
            
            return quotes
            
        except TradierError:
            raise
        except Exception as e:
            raise TradierError(f"Error getting quotes: {e}")
    
    async def get_history(self, request: HistoryRequest) -> HistoryResponse:
        """Get historical data for symbol"""
        try:
            # Convert resolution to Tradier interval
            interval = self._convert_resolution_to_interval(request.resolution)
            
            # Convert timestamps to dates
            start_date = datetime.fromtimestamp(request.from_ts).strftime("%Y-%m-%d")
            end_date = datetime.fromtimestamp(request.to_ts).strftime("%Y-%m-%d")
            
            params = {
                "symbol": request.symbol,
                "interval": interval,
                "start": start_date,
                "end": end_date
            }
            
            response = await self._make_request("GET", "/v1/markets/history", params=params)
            history_data = response.get("history", {})
            
            if history_data is None:
                return HistoryResponse(
                    symbol=request.symbol,
                    resolution=request.resolution,
                    status="no_data"
                )
            
            # Parse candle data
            day_data = history_data.get("day", [])
            if isinstance(day_data, dict):
                day_data = [day_data]
            
            candles = []
            for candle_data in day_data:
                try:
                    candle = Candle.from_tradier(candle_data)
                    # Filter by timestamp range
                    if request.from_ts <= candle.ts <= request.to_ts:
                        candles.append(candle)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse candle data: {e}")
            
            # Sort by timestamp
            candles.sort(key=lambda c: c.ts)
            
            # Apply countback limit if specified
            if request.countback and len(candles) > request.countback:
                candles = candles[-request.countback:]
            
            return HistoryResponse(
                symbol=request.symbol,
                resolution=request.resolution,
                bars=candles
            )
            
        except TradierError:
            raise
        except Exception as e:
            raise TradierError(f"Error getting history: {e}")
    
    async def search_symbols(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for symbols"""
        try:
            params = {"q": query, "exchanges": "N,Q"}  # NYSE and NASDAQ
            
            response = await self._make_request("GET", "/v1/markets/search", params=params)
            securities = response.get("securities", {}).get("security", [])
            
            if isinstance(securities, dict):
                securities = [securities]
            
            results = []
            for security in securities[:limit]:
                results.append({
                    "symbol": security.get("symbol", ""),
                    "full_name": security.get("description", ""),
                    "description": f"{security.get('description', '')} ({security.get('symbol', '')})",
                    "exchange": security.get("exchange", ""),
                    "type": security.get("type", "stock").lower()
                })
            
            return results
            
        except TradierError:
            raise
        except Exception as e:
            logger.warning(f"Error searching symbols: {e}")
            return []
    
    async def get_symbol_info(self, symbol: str) -> Symbol:
        """Get symbol metadata"""
        try:
            # Get basic quote to verify symbol exists
            quotes = await self.get_quotes([symbol])
            if not quotes:
                raise TradierError(f"Symbol {symbol} not found")
            
            # For now, create basic symbol info
            # In production, you might want to call a separate endpoint for detailed info
            return Symbol.from_tradier_symbol(symbol, f"{symbol} Corp")
            
        except TradierError:
            raise
        except Exception as e:
            raise TradierError(f"Error getting symbol info: {e}")
    
    def _convert_resolution_to_interval(self, resolution: str) -> str:
        """Convert TradingView resolution to Tradier interval"""
        resolution_map = {
            "1": "1min",
            "5": "5min", 
            "15": "15min",
            "30": "30min",
            "60": "1hour",
            "240": "4hour",
            "D": "daily",
            "W": "weekly",
            "M": "monthly"
        }
        return resolution_map.get(resolution, "daily")
    
    # ========================================================================
    # WebSocket Streaming
    # ========================================================================
    
    async def start_websocket_stream(self) -> None:
        """Start WebSocket connection for real-time data"""
        try:
            # First, get session ID
            await self._get_ws_session_id()
            
            # Connect to WebSocket
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self._ws_connection = await websockets.connect(
                f"{self.ws_url}/v1/markets/events",
                extra_headers=headers
            )
            
            logger.info("WebSocket connection established")
            
        except Exception as e:
            raise TradierError(f"Failed to start WebSocket stream: {e}")
    
    async def _get_ws_session_id(self) -> str:
        """Get WebSocket session ID"""
        try:
            response = await self._make_request("POST", "/v1/markets/events/session")
            session_data = response.get("stream", {})
            self._ws_session_id = session_data.get("sessionid")
            
            if not self._ws_session_id:
                raise TradierError("Failed to get WebSocket session ID")
            
            return self._ws_session_id
            
        except Exception as e:
            raise TradierError(f"Error getting WebSocket session: {e}")
    
    async def subscribe_symbols(self, symbols: List[str]) -> None:
        """Subscribe to real-time quotes for symbols"""
        if not self._ws_connection or not self._ws_session_id:
            raise TradierError("WebSocket not connected")
        
        subscribe_message = {
            "symbols": symbols,
            "sessionid": self._ws_session_id,
            "linebreak": True
        }
        
        await self._ws_connection.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to symbols: {symbols}")
    
    async def websocket_stream(self) -> AsyncGenerator[Quote, None]:
        """Stream real-time quotes via WebSocket"""
        if not self._ws_connection:
            raise TradierError("WebSocket not connected")
        
        try:
            async for message in self._ws_connection:
                try:
                    data = json.loads(message)
                    
                    # Parse different message types
                    if data.get("type") == "quote":
                        quote_data = data
                        quote = Quote.from_tradier(quote_data)
                        yield quote
                    elif data.get("type") == "trade":
                        # Convert trade to quote format
                        quote = Quote(
                            symbol=data.get("symbol", ""),
                            timestamp=int(time.time()),
                            last=data.get("price"),
                            volume=data.get("size")
                        )
                        yield quote
                        
                except (json.JSONDecodeError, ValidationError) as e:
                    logger.warning(f"Failed to parse WebSocket message: {e}")
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            raise TradierError("WebSocket connection lost")
        except Exception as e:
            logger.error(f"WebSocket stream error: {e}")
            raise TradierError(f"WebSocket error: {e}")
    
    # ========================================================================
    # Trading Operations
    # ========================================================================
    
    async def place_order(self, order: Order) -> str:
        """Place order with Tradier"""
        if not self.account_id:
            raise TradierError("Account ID required for trading")
        
        try:
            # Convert order to Tradier format
            order_data = order.to_tradier_format()
            
            # Place order
            endpoint = f"/v1/accounts/{self.account_id}/orders"
            response = await self._make_request("POST", endpoint, data=order_data)
            
            # Extract order ID
            order_response = response.get("order", {})
            broker_order_id = order_response.get("id")
            
            if not broker_order_id:
                raise TradierError("Failed to get order ID from response")
            
            # Update order with broker ID
            order.broker_order_id = str(broker_order_id)
            order.status = OrderStatus.OPEN
            order.submitted_at = int(time.time())
            
            logger.info(f"Order placed: {order.id} -> {broker_order_id}")
            return str(broker_order_id)
            
        except TradierError:
            raise
        except Exception as e:
            raise TradierError(f"Error placing order: {e}")
    
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel order by broker ID"""
        if not self.account_id:
            raise TradierError("Account ID required for trading")
        
        try:
            endpoint = f"/v1/accounts/{self.account_id}/orders/{broker_order_id}"
            await self._make_request("DELETE", endpoint)
            
            logger.info(f"Order cancelled: {broker_order_id}")
            return True
            
        except TradierError as e:
            if "not found" in str(e).lower():
                return False
            raise
        except Exception as e:
            raise TradierError(f"Error cancelling order: {e}")
    
    async def get_order_status(self, broker_order_id: str) -> Dict[str, Any]:
        """Get order status by broker ID"""
        if not self.account_id:
            raise TradierError("Account ID required")
        
        try:
            endpoint = f"/v1/accounts/{self.account_id}/orders/{broker_order_id}"
            response = await self._make_request("GET", endpoint)
            
            return response.get("order", {})
            
        except Exception as e:
            raise TradierError(f"Error getting order status: {e}")
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        if not self.account_id:
            raise TradierError("Account ID required")
        
        try:
            endpoint = f"/v1/accounts/{self.account_id}/positions"
            response = await self._make_request("GET", endpoint)
            
            positions_data = response.get("positions", {}).get("position", [])
            if isinstance(positions_data, dict):
                positions_data = [positions_data]
            
            positions = []
            for pos_data in positions_data:
                try:
                    position = Position(
                        symbol=pos_data.get("symbol", ""),
                        account_id=self.account_id,
                        quantity=float(pos_data.get("quantity", 0)),
                        avg_price=float(pos_data.get("cost_basis", 0)) / float(pos_data.get("quantity", 1))
                    )
                    positions.append(position)
                except (KeyError, ValueError, ZeroDivisionError) as e:
                    logger.warning(f"Failed to parse position: {e}")
            
            return positions
            
        except Exception as e:
            raise TradierError(f"Error getting positions: {e}")
    
    async def get_account_info(self) -> Account:
        """Get account information"""
        if not self.account_id:
            raise TradierError("Account ID required")
        
        try:
            endpoint = f"/v1/accounts/{self.account_id}/balances"
            response = await self._make_request("GET", endpoint)
            
            balances = response.get("balances", {})
            
            return Account(
                account_id=self.account_id,
                broker="Tradier",
                account_type=balances.get("account_type", "unknown"),
                total_equity=float(balances.get("total_equity", 0)),
                cash_balance=float(balances.get("cash", {}).get("cash_available", 0)),
                buying_power=float(balances.get("margin", {}).get("buying_power", 0)),
                day_trade_buying_power=balances.get("day_trade_buying_power"),
                day_pnl=float(balances.get("day_change", 0)),
                total_pnl=float(balances.get("total_change", 0))
            )
            
        except Exception as e:
            raise TradierError(f"Error getting account info: {e}")
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    async def close(self) -> None:
        """Close all connections"""
        if self._ws_connection:
            await self._ws_connection.close()
            self._ws_connection = None
        
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        
        logger.info("Tradier connector closed")