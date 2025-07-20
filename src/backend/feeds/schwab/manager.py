"""
Charles Schwab Unified Manager

Provides a single interface for all Schwab API operations including
authentication, market data, trading, and account management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal

from .auth import SchwabAuth, SchwabCredentials, SchwabTokens
from .market_data import SchwabMarketData, SchwabQuote, QuoteFields
from .trading import SchwabTrading, SchwabOrder, OrderType, OrderAction, OrderDuration
from .account import SchwabAccount, SchwabAccountInfo, SchwabPosition, SchwabTransaction

logger = logging.getLogger(__name__)


class SchwabManager:
    """
    Unified Schwab API manager.
    
    Provides a single interface for all Schwab operations:
    - Authentication and token management
    - Market data retrieval
    - Trading and order management
    - Account and position management
    
    This is the main class that other components should use to interact
    with the Schwab API.
    """
    
    def __init__(self, credentials: SchwabCredentials):
        """
        Initialize Schwab manager with credentials.
        
        Args:
            credentials: Schwab API credentials
        """
        self.credentials = credentials
        self.auth = SchwabAuth(credentials)
        self.market_data = SchwabMarketData(self.auth)
        self.trading = SchwabTrading(self.auth)
        self.account = SchwabAccount(self.auth)
        
        # Cache for account information
        self._account_cache: Dict[str, SchwabAccountInfo] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # 5-minute cache
        
        logger.info("Initialized Schwab Manager")
    
    async def close(self):
        """Close all HTTP connections"""
        await self.auth.close()
    
    # Authentication methods
    def generate_auth_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL"""
        return self.auth.generate_authorization_url(state)
    
    async def complete_auth(self, authorization_code: str) -> SchwabTokens:
        """Complete OAuth flow with authorization code"""
        return await self.auth.exchange_code_for_tokens(authorization_code)
    
    def extract_auth_code(self, callback_url: str) -> str:
        """Extract authorization code from callback URL"""
        return self.auth.extract_code_from_callback_url(callback_url)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        return await self.auth.test_connection()
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return self.auth.get_status()
    
    # Market data methods
    async def get_quote(self, symbol: str, fields: Optional[List[QuoteFields]] = None) -> SchwabQuote:
        """Get quote for a single symbol"""
        return await self.market_data.get_quote(symbol, fields)
    
    async def get_quotes(self, symbols: List[str], fields: Optional[List[QuoteFields]] = None) -> Dict[str, SchwabQuote]:
        """Get quotes for multiple symbols"""
        return await self.market_data.get_quotes(symbols, fields)
    
    async def get_historical_data(
        self,
        symbol: str,
        period_type: str = "month",
        period: int = 1,
        frequency_type: str = "daily",
        frequency: int = 1,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Get historical price data"""
        return await self.market_data.get_historical_data(
            symbol, period_type, period, frequency_type, frequency, start_date, end_date
        )
    
    async def search_symbols(self, query: str, projection: str = "symbol-search") -> List[Dict[str, Any]]:
        """Search for symbols"""
        return await self.market_data.search_symbols(query, projection)
    
    async def get_options_chain(
        self,
        symbol: str,
        strike_count: int = 10,
        include_quotes: bool = True,
        strategy: str = "SINGLE",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get options chain"""
        return await self.market_data.get_options_chain(
            symbol, strike_count, include_quotes, strategy, from_date, to_date
        )
    
    async def get_market_hours(self, markets: List[str], date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get market hours"""
        return await self.market_data.get_market_hours(markets, date)
    
    # Account methods
    async def get_account_numbers(self) -> List[Dict[str, str]]:
        """Get account numbers"""
        return await self.account.get_account_numbers()
    
    async def get_account_info(self, account_hash: str, use_cache: bool = True) -> SchwabAccountInfo:
        """
        Get account information with optional caching.
        
        Args:
            account_hash: Account hash identifier
            use_cache: Whether to use cached data if available
            
        Returns:
            SchwabAccountInfo: Account information
        """
        if use_cache and account_hash in self._account_cache:
            cache_time = self._cache_expiry.get(account_hash, datetime.min)
            if datetime.utcnow() < cache_time:
                logger.debug(f"Using cached account info for {account_hash}")
                return self._account_cache[account_hash]
        
        # Fetch fresh data
        account_info = await self.account.get_account(account_hash, fields="positions")
        
        # Update cache
        self._account_cache[account_hash] = account_info
        self._cache_expiry[account_hash] = datetime.utcnow() + self._cache_ttl
        
        return account_info
    
    async def get_all_accounts(self, use_cache: bool = True) -> List[SchwabAccountInfo]:
        """Get all account information"""
        accounts = await self.account.get_all_accounts(fields="positions")
        
        # Update cache for all accounts
        if use_cache:
            for account_info in accounts:
                self._account_cache[account_info.account_hash] = account_info
                self._cache_expiry[account_info.account_hash] = datetime.utcnow() + self._cache_ttl
        
        return accounts
    
    async def get_positions(self, account_hash: str) -> List[SchwabPosition]:
        """Get positions for an account"""
        account_info = await self.get_account_info(account_hash)
        return account_info.positions
    
    async def get_account_balance(self, account_hash: str):
        """Get account balance information"""
        account_info = await self.get_account_info(account_hash)
        return account_info.balance
    
    async def get_transactions(
        self,
        account_hash: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> List[SchwabTransaction]:
        """Get transaction history"""
        return await self.account.get_transactions(account_hash, start_date, end_date, transaction_type)
    
    # Trading methods
    async def place_order(self, account_hash: str, order: SchwabOrder) -> Dict[str, Any]:
        """Place a new order"""
        return await self.trading.place_order(account_hash, order)
    
    async def cancel_order(self, account_hash: str, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        return await self.trading.cancel_order(account_hash, order_id)
    
    async def get_order(self, account_hash: str, order_id: str) -> SchwabOrder:
        """Get order details"""
        return await self.trading.get_order(account_hash, order_id)
    
    async def get_orders(
        self,
        account_hash: str,
        max_results: int = 3000,
        from_entered_time: Optional[datetime] = None,
        to_entered_time: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[SchwabOrder]:
        """Get orders for an account"""
        return await self.trading.get_orders(
            account_hash, max_results, from_entered_time, to_entered_time, status
        )
    
    async def replace_order(self, account_hash: str, order_id: str, new_order: SchwabOrder) -> Dict[str, Any]:
        """Replace an existing order"""
        return await self.trading.replace_order(account_hash, order_id, new_order)
    
    # Convenience methods for common operations
    async def buy_stock(
        self,
        account_hash: str,
        symbol: str,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        duration: OrderDuration = OrderDuration.DAY
    ) -> Dict[str, Any]:
        """
        Buy stock with simple parameters.
        
        Args:
            account_hash: Account to trade in
            symbol: Stock symbol
            quantity: Number of shares
            order_type: Market, limit, etc.
            price: Limit price (required for limit orders)
            duration: Order duration
            
        Returns:
            Dict[str, Any]: Order placement response
        """
        order = SchwabOrder.create_equity_order(
            symbol=symbol,
            action=OrderAction.BUY,
            quantity=quantity,
            order_type=order_type,
            price=price,
            duration=duration
        )
        
        return await self.place_order(account_hash, order)
    
    async def sell_stock(
        self,
        account_hash: str,
        symbol: str,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        duration: OrderDuration = OrderDuration.DAY
    ) -> Dict[str, Any]:
        """
        Sell stock with simple parameters.
        
        Args:
            account_hash: Account to trade in
            symbol: Stock symbol
            quantity: Number of shares
            order_type: Market, limit, etc.
            price: Limit price (required for limit orders)
            duration: Order duration
            
        Returns:
            Dict[str, Any]: Order placement response
        """
        order = SchwabOrder.create_equity_order(
            symbol=symbol,
            action=OrderAction.SELL,
            quantity=quantity,
            order_type=order_type,
            price=price,
            duration=duration
        )
        
        return await self.place_order(account_hash, order)
    
    async def get_portfolio_summary(self, account_hash: str) -> Dict[str, Any]:
        """
        Get a summary of portfolio information.
        
        Args:
            account_hash: Account hash identifier
            
        Returns:
            Dict[str, Any]: Portfolio summary
        """
        account_info = await self.get_account_info(account_hash)
        
        # Calculate summary statistics
        total_positions = len(account_info.positions)
        active_positions = len(account_info.active_positions)
        equity_positions = len(account_info.equity_positions)
        option_positions = len(account_info.option_positions)
        
        total_market_value = account_info.total_market_value
        
        # Calculate day P&L
        day_pnl = Decimal("0")
        for position in account_info.positions:
            if position.current_day_profit_loss:
                day_pnl += position.current_day_profit_loss
        
        return {
            "account_hash": account_hash,
            "account_type": account_info.account_type,
            "nickname": account_info.nickname,
            "total_positions": total_positions,
            "active_positions": active_positions,
            "equity_positions": equity_positions,
            "option_positions": option_positions,
            "total_market_value": float(total_market_value),
            "day_pnl": float(day_pnl),
            "buying_power": float(account_info.balance.buying_power) if account_info.balance and account_info.balance.buying_power else 0,
            "cash_available": float(account_info.balance.cash_available_for_trading) if account_info.balance and account_info.balance.cash_available_for_trading else 0,
            "is_day_trader": account_info.is_day_trader,
            "last_updated": account_info.last_updated.isoformat()
        }
    
    async def get_watchlist_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for a watchlist of symbols with formatted output.
        
        Args:
            symbols: List of symbols to quote
            
        Returns:
            Dict[str, Dict[str, Any]]: Formatted quote data
        """
        quotes = await self.get_quotes(symbols, [QuoteFields.QUOTE, QuoteFields.FUNDAMENTAL])
        
        formatted_quotes = {}
        for symbol, quote in quotes.items():
            formatted_quotes[symbol] = {
                "symbol": quote.symbol,
                "last": float(quote.last) if quote.last else 0,
                "bid": float(quote.bid) if quote.bid else 0,
                "ask": float(quote.ask) if quote.ask else 0,
                "change": float(quote.change) if quote.change else 0,
                "change_percent": float(quote.change_percent) if quote.change_percent else 0,
                "volume": quote.volume or 0,
                "high": float(quote.high) if quote.high else 0,
                "low": float(quote.low) if quote.low else 0,
                "open": float(quote.open_price) if quote.open_price else 0,
                "close": float(quote.close_price) if quote.close_price else 0,
                "market_cap": float(quote.market_cap) if quote.market_cap else 0,
                "pe_ratio": float(quote.pe_ratio) if quote.pe_ratio else 0,
                "timestamp": quote.timestamp.isoformat()
            }
        
        return formatted_quotes
    
    def clear_cache(self):
        """Clear account information cache"""
        self._account_cache.clear()
        self._cache_expiry.clear()
        logger.info("Cleared account cache")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of all Schwab services.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "services": {}
        }
        
        # Test authentication
        try:
            auth_result = await self.test_connection()
            results["services"]["authentication"] = {
                "status": "healthy" if auth_result["status"] == "success" else "unhealthy",
                "message": auth_result["message"]
            }
        except Exception as e:
            results["services"]["authentication"] = {
                "status": "unhealthy",
                "message": str(e)
            }
        
        # Test market data
        try:
            quote = await self.get_quote("SPY")
            results["services"]["market_data"] = {
                "status": "healthy",
                "message": f"Successfully retrieved quote for SPY: ${quote.last}"
            }
        except Exception as e:
            results["services"]["market_data"] = {
                "status": "unhealthy",
                "message": str(e)
            }
        
        # Test account access
        try:
            accounts = await self.get_account_numbers()
            results["services"]["accounts"] = {
                "status": "healthy",
                "message": f"Successfully retrieved {len(accounts)} accounts"
            }
        except Exception as e:
            results["services"]["accounts"] = {
                "status": "unhealthy",
                "message": str(e)
            }
        
        # Determine overall status
        all_healthy = all(
            service["status"] == "healthy" 
            for service in results["services"].values()
        )
        results["overall_status"] = "healthy" if all_healthy else "unhealthy"
        
        return results