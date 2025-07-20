"""
Tastytrade Unified Manager

Provides a high-level interface that combines all Tastytrade API capabilities
into a single, easy-to-use manager class for the TraderTerminal platform.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal

from .auth import TastytradeAuth, TastytradeCredentials
from .market_data import TastytradeMarketData, TastytradeQuote
from .orders import TastytradeOrders, TastytradeOrder, OrderType, OrderAction, OrderTimeInForce
from .account import TastytradeAccount, TastytradeAccountInfo, TastytradePosition, TastytradeBalance

logger = logging.getLogger(__name__)


class TastytradeManager:
    """
    Unified Tastytrade API manager.
    
    This class provides a high-level interface to all Tastytrade API functionality
    including authentication, market data, trading, and account management.
    
    Example Usage:
        # Initialize
        credentials = TastytradeCredentials(
            client_id="your_client_id",
            client_secret="your_client_secret"
        )
        manager = TastytradeManager(credentials)
        
        # Authenticate
        auth_url = manager.get_authorization_url()
        # User visits auth_url and gets callback
        await manager.complete_authentication(callback_url)
        
        # Get market data
        quote = await manager.get_quote("AAPL")
        quotes = await manager.get_quotes(["AAPL", "MSFT", "TSLA"])
        
        # Get account info
        accounts = await manager.get_accounts()
        account = await manager.get_account(account_number)
        
        # Place trades
        order = TastytradeOrder.create_equity_order(
            symbol="AAPL",
            action=OrderAction.BUY_TO_OPEN,
            quantity=100,
            order_type=OrderType.MARKET
        )
        result = await manager.place_order(account_number, order)
    """
    
    def __init__(self, credentials: TastytradeCredentials):
        self.credentials = credentials
        self.auth = TastytradeAuth(credentials)
        self.market_data = TastytradeMarketData(self.auth)
        self.orders = TastytradeOrders(self.auth)
        self.account = TastytradeAccount(self.auth)
        self._cached_accounts: Optional[List[Dict[str, Any]]] = None
        self._accounts_cache_time: Optional[datetime] = None
        
        logger.info(f"Initialized Tastytrade manager for {'sandbox' if credentials.sandbox else 'production'} environment")
    
    # Authentication Methods
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL for user consent"""
        return self.auth.generate_authorization_url(state)
    
    async def complete_authentication(self, callback_url: str) -> Dict[str, Any]:
        """
        Complete OAuth2 authentication flow from callback URL.
        
        Args:
            callback_url: Full callback URL received after user authorization
            
        Returns:
            Dict[str, Any]: Authentication status and token information
        """
        try:
            # Extract authorization code
            auth_code = self.auth.extract_code_from_callback_url(callback_url)
            
            # Exchange for tokens
            tokens = await self.auth.exchange_code_for_tokens(auth_code)
            
            # Test connection
            test_result = await self.auth.test_connection()
            
            logger.info("Tastytrade authentication completed successfully")
            
            return {
                "status": "success",
                "message": "Authentication completed successfully",
                "token_expires_in": tokens.expires_in_seconds,
                "environment": "sandbox" if self.credentials.sandbox else "production",
                "connection_test": test_result
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "environment": "sandbox" if self.credentials.sandbox else "production"
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection with current authentication"""
        return await self.auth.test_connection()
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return self.auth.get_status()
    
    # Market Data Methods
    
    async def get_quote(self, symbol: str) -> TastytradeQuote:
        """Get real-time quote for a single symbol"""
        return await self.market_data.get_quote(symbol)
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, TastytradeQuote]:
        """Get real-time quotes for multiple symbols"""
        return await self.market_data.get_quotes(symbols)
    
    async def get_option_chain(
        self,
        symbol: str,
        expiration_date: Optional[str] = None,
        strike_price: Optional[float] = None,
        option_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get options chain for underlying symbol"""
        return await self.market_data.get_option_chain(
            symbol, expiration_date, strike_price, option_type
        )
    
    async def search_symbols(
        self, 
        query: str, 
        instrument_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for symbols by name or ticker"""
        return await self.market_data.search_symbols(query, instrument_types)
    
    async def get_market_hours(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get market hours for specified date"""
        return await self.market_data.get_market_hours(date)
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get historical OHLCV data for symbol"""
        return await self.market_data.get_historical_data(
            symbol, timeframe, start_time, end_time
        )
    
    # Account Management Methods
    
    async def get_customer_info(self) -> Dict[str, Any]:
        """Get customer information for authenticated user"""
        return await self.account.get_customer_info()
    
    async def get_accounts(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get all accounts for authenticated user.
        
        Args:
            use_cache: Whether to use cached results (valid for 5 minutes)
            
        Returns:
            List[Dict[str, Any]]: Account information list
        """
        # Check cache validity
        if (use_cache and self._cached_accounts and self._accounts_cache_time and 
            datetime.utcnow() - self._accounts_cache_time < timedelta(minutes=5)):
            return self._cached_accounts
        
        # Fetch fresh data
        accounts = await self.account.get_accounts()
        
        # Update cache
        self._cached_accounts = accounts
        self._accounts_cache_time = datetime.utcnow()
        
        return accounts
    
    async def get_account(self, account_number: str) -> TastytradeAccountInfo:
        """Get detailed account information including positions and balance"""
        return await self.account.get_account(account_number)
    
    async def get_account_balance(self, account_number: str) -> TastytradeBalance:
        """Get account balance information"""
        return await self.account.get_account_balance(account_number)
    
    async def get_positions(self, account_number: str) -> List[TastytradePosition]:
        """Get all positions for an account"""
        return await self.account.get_positions(account_number)
    
    async def get_transactions(
        self,
        account_number: str,
        page_offset: Optional[int] = None,
        per_page: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Get transaction history for an account"""
        return await self.account.get_transactions(
            account_number, page_offset, per_page, start_date, end_date
        )
    
    # Trading Methods
    
    async def place_order(self, account_number: str, order: TastytradeOrder) -> Dict[str, Any]:
        """Place a new order"""
        return await self.orders.place_order(account_number, order)
    
    async def cancel_order(self, account_number: str, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        return await self.orders.cancel_order(account_number, order_id)
    
    async def get_order(self, account_number: str, order_id: str) -> TastytradeOrder:
        """Get details for a specific order"""
        return await self.orders.get_order(account_number, order_id)
    
    async def get_orders(
        self,
        account_number: str,
        page_offset: Optional[int] = None,
        per_page: Optional[int] = None,
        sort: Optional[str] = None
    ) -> List[TastytradeOrder]:
        """Get orders for an account"""
        return await self.orders.get_orders(account_number, page_offset, per_page, sort)
    
    async def replace_order(self, account_number: str, order_id: str, new_order: TastytradeOrder) -> Dict[str, Any]:
        """Replace an existing order with a new one"""
        return await self.orders.replace_order(account_number, order_id, new_order)
    
    # Convenience Methods
    
    async def buy_stock(
        self,
        account_number: str,
        symbol: str,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY
    ) -> Dict[str, Any]:
        """
        Convenience method to buy stock.
        
        Args:
            account_number: Account to trade in
            symbol: Stock symbol
            quantity: Number of shares
            order_type: Market, limit, etc.
            price: Limit price (required for limit orders)
            time_in_force: Order duration
            
        Returns:
            Dict[str, Any]: Order placement result
        """
        order = TastytradeOrder.create_equity_order(
            symbol=symbol,
            action=OrderAction.BUY_TO_OPEN,
            quantity=quantity,
            order_type=order_type,
            price=price,
            time_in_force=time_in_force
        )
        
        return await self.place_order(account_number, order)
    
    async def sell_stock(
        self,
        account_number: str,
        symbol: str,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY
    ) -> Dict[str, Any]:
        """
        Convenience method to sell stock.
        
        Args:
            account_number: Account to trade in
            symbol: Stock symbol
            quantity: Number of shares
            order_type: Market, limit, etc.
            price: Limit price (required for limit orders)
            time_in_force: Order duration
            
        Returns:
            Dict[str, Any]: Order placement result
        """
        order = TastytradeOrder.create_equity_order(
            symbol=symbol,
            action=OrderAction.SELL_TO_CLOSE,
            quantity=quantity,
            order_type=order_type,
            price=price,
            time_in_force=time_in_force
        )
        
        return await self.place_order(account_number, order)
    
    async def get_portfolio_summary(self, account_number: str) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary including positions, balance, and P&L.
        
        Args:
            account_number: Account number
            
        Returns:
            Dict[str, Any]: Portfolio summary
        """
        try:
            # Get account info (includes positions and balance)
            account_info = await self.get_account(account_number)
            
            # Calculate summary metrics
            total_positions = len(account_info.positions)
            active_positions = len(account_info.active_positions)
            equity_positions = len(account_info.equity_positions)
            option_positions = len(account_info.option_positions)
            futures_positions = len(account_info.futures_positions)
            
            # Calculate total P&L
            total_unrealized_pnl = Decimal("0")
            total_realized_pnl = Decimal("0")
            
            for position in account_info.positions:
                if position.unrealized_day_gain:
                    total_unrealized_pnl += position.unrealized_day_gain
                if position.realized_day_gain:
                    total_realized_pnl += position.realized_day_gain
            
            summary = {
                "account_number": account_number,
                "account_type": account_info.account_type,
                "day_trader_status": account_info.day_trader_status,
                "timestamp": datetime.utcnow().isoformat(),
                
                # Balance information
                "balance": {
                    "account_value": account_info.balance.account_value if account_info.balance else None,
                    "cash_balance": account_info.balance.cash_balance if account_info.balance else None,
                    "buying_power": account_info.balance.buying_power if account_info.balance else None,
                    "net_liquidating_value": account_info.balance.net_liquidating_value if account_info.balance else None,
                    "day_trading_buying_power": account_info.balance.day_trading_buying_power if account_info.balance else None
                },
                
                # Position summary
                "positions": {
                    "total_positions": total_positions,
                    "active_positions": active_positions,
                    "equity_positions": equity_positions,
                    "option_positions": option_positions,
                    "futures_positions": futures_positions,
                    "total_market_value": account_info.total_market_value
                },
                
                # P&L summary
                "pnl": {
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "total_realized_pnl": total_realized_pnl,
                    "total_day_pnl": total_unrealized_pnl + total_realized_pnl
                }
            }
            
            logger.info(f"Generated portfolio summary for account {account_number}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating portfolio summary: {e}")
            raise
    
    async def close(self):
        """Close HTTP connections and cleanup resources"""
        await self.auth.close()
        logger.info("Tastytrade manager closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def execute_alert(self, alert: Any) -> Dict[str, Any]:
        """
        Execute a TradingView alert for paper trading integration.
        
        This method provides compatibility with the paper trading router
        by accepting TradingView alert objects and executing them as orders.
        
        Args:
            alert: TradingViewAlert object with order details
            
        Returns:
            Dict[str, Any]: Execution result with status and order details
        """
        try:
            # Get available accounts for order placement
            accounts = await self.get_accounts()
            if not accounts:
                return {
                    "status": "error",
                    "reason": "No Tastytrade accounts available",
                    "details": {}
                }
            
            # Use first available account (sandbox should have test accounts)
            account_number = accounts[0].get("account-number", accounts[0].get("id", ""))
            if not account_number:
                return {
                    "status": "error", 
                    "reason": "Invalid account information",
                    "details": {}
                }
            
            # Convert alert to order parameters
            symbol = alert.symbol
            action = alert.action.lower()
            quantity = int(alert.quantity)
            order_type = getattr(alert, 'order_type', 'market')
            price = getattr(alert, 'price', None)
            
            # Determine order action
            if action in ["buy", "long"]:
                if order_type.lower() == "market":
                    result = await self.buy_stock(
                        account_number=account_number,
                        symbol=symbol,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    )
                else:  # limit order
                    if price is None:
                        return {
                            "status": "error",
                            "reason": "Limit price required for limit orders",
                            "details": {}
                        }
                    result = await self.buy_stock(
                        account_number=account_number,
                        symbol=symbol,
                        quantity=quantity,
                        order_type=OrderType.LIMIT,
                        price=Decimal(str(price))
                    )
            elif action in ["sell", "short"]:
                if order_type.lower() == "market":
                    result = await self.sell_stock(
                        account_number=account_number,
                        symbol=symbol,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    )
                else:  # limit order
                    if price is None:
                        return {
                            "status": "error",
                            "reason": "Limit price required for limit orders",
                            "details": {}
                        }
                    result = await self.sell_stock(
                        account_number=account_number,
                        symbol=symbol,
                        quantity=quantity,
                        order_type=OrderType.LIMIT,
                        price=Decimal(str(price))
                    )
            else:
                return {
                    "status": "error",
                    "reason": f"Unsupported action: {action}",
                    "details": {}
                }
            
            # Parse Tastytrade response
            if result and "order" in result:
                order_info = result["order"]
                order_status = order_info.get("status", "unknown")
                
                # For sandbox, assume immediate fill for market orders
                if order_type.lower() == "market" and order_status in ["received", "routed"]:
                    fill_price = price if price else await self._get_market_price(symbol)
                    
                    return {
                        "status": "success",
                        "order": {
                            "id": order_info.get("id", ""),
                            "status": "filled"
                        },
                        "fill": {
                            "price": float(fill_price) if fill_price else 0.0,
                            "quantity": quantity,
                            "commission": 0.0,  # Sandbox typically has no commissions
                            "slippage": 0.001   # Minimal slippage in sandbox
                        },
                        "execution": {
                            "account": account_number,
                            "broker": "tastytrade_sandbox",
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "message": f"Tastytrade sandbox order executed: {symbol} {action} {quantity}"
                    }
                else:
                    return {
                        "status": "success",
                        "order": {
                            "id": order_info.get("id", ""),
                            "status": order_status
                        },
                        "execution": {
                            "account": account_number,
                            "broker": "tastytrade_sandbox",
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "message": f"Tastytrade sandbox order placed: {symbol} {action} {quantity}"
                    }
            else:
                return {
                    "status": "error",
                    "reason": "Order placement failed",
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"Failed to execute Tastytrade alert: {e}")
            return {
                "status": "error",
                "reason": f"Execution error: {str(e)}",
                "details": {}
            }
    
    async def _get_market_price(self, symbol: str) -> Optional[Decimal]:
        """Get current market price for a symbol"""
        try:
            quote = await self.get_quote(symbol)
            if quote and hasattr(quote, 'last_price') and quote.last_price:
                return Decimal(str(quote.last_price))
            elif quote and hasattr(quote, 'bid') and hasattr(quote, 'ask'):
                # Use mid-price if no last price available
                if quote.bid and quote.ask:
                    return (Decimal(str(quote.bid)) + Decimal(str(quote.ask))) / 2
        except Exception as e:
            logger.warning(f"Could not get market price for {symbol}: {e}")
        
        # Return None if unable to get price
        return None