"""
Tradovate Integration Manager

High-level manager that coordinates all Tradovate operations including
authentication, market data, order execution, and account management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .auth import TradovateAuth, TradovateCredentials
from .market_data import TradovateMarketData, TradovateQuote
from .orders import TradovateOrders, OrderType, TradovateOrderResponse
from .account import TradovateAccount, TradovateAccountInfo, CashBalance, Position

logger = logging.getLogger(__name__)


class TradovateManager:
    """
    High-level manager for all Tradovate operations.
    
    Provides a unified interface for:
    - Authentication and connection management
    - Market data subscriptions
    - Order execution with risk management
    - Account monitoring and performance tracking
    - Integration with TradingView alerts
    """
    
    def __init__(self, credentials: TradovateCredentials):
        self.credentials = credentials
        
        # Initialize core components
        self.auth = TradovateAuth(credentials)
        self.market_data = TradovateMarketData(self.auth)
        self.orders = TradovateOrders(self.auth)
        self.account = TradovateAccount(self.auth)
        
        # State management
        self._initialized = False
        self._accounts: List[TradovateAccountInfo] = []
        self._default_account_id: Optional[int] = None
        self._market_data_connected = False
        
        logger.info(f"Initialized Tradovate manager for {'demo' if credentials.demo else 'live'} environment")
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the Tradovate connection and verify setup.
        
        Returns:
            Dict[str, Any]: Initialization results
        """
        if self._initialized:
            logger.warning("Tradovate manager already initialized")
            return {"status": "already_initialized"}
        
        logger.info("Initializing Tradovate connection...")
        
        try:
            # Step 1: Test authentication
            auth_test = await self.auth.test_connection()
            if auth_test.get("status") != "success":
                return {
                    "status": "failed",
                    "step": "authentication",
                    "error": auth_test.get("message", "Authentication failed")
                }
            
            # Step 2: Load accounts
            self._accounts = await self.account.get_accounts()
            if not self._accounts:
                return {
                    "status": "failed",
                    "step": "accounts",
                    "error": "No trading accounts found"
                }
            
            # Step 3: Set default account (first non-archived account)
            for account in self._accounts:
                if not account.archived:
                    self._default_account_id = account.id
                    break
            
            if not self._default_account_id:
                return {
                    "status": "failed",
                    "step": "default_account",
                    "error": "No active accounts available"
                }
            
            # Step 4: Test market data connection
            test_symbols = ["ES", "NQ"]  # Common futures symbols
            quotes = await self.market_data.get_quotes(test_symbols)
            market_data_working = len(quotes) > 0
            
            self._initialized = True
            
            return {
                "status": "success",
                "environment": "demo" if self.credentials.demo else "live",
                "account_count": len(self._accounts),
                "default_account_id": self._default_account_id,
                "market_data_working": market_data_working,
                "accounts": [
                    {
                        "id": acc.id,
                        "name": acc.name,
                        "type": acc.account_type,
                        "archived": acc.archived
                    }
                    for acc in self._accounts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error initializing Tradovate: {e}")
            return {
                "status": "failed",
                "step": "initialization",
                "error": str(e)
            }
    
    async def execute_alert(self, alert: Any) -> Dict[str, Any]:
        """
        Execute a TradingView alert through Tradovate.
        
        This is the main entry point for webhook-driven trading.
        Compatible with paper trading router interface.
        
        Args:
            alert: TradingViewAlert object or dict with alert data
            
        Returns:
            Dict[str, Any]: Execution result
        """
        if not self._initialized:
            return {
                "status": "error",
                "message": "Tradovate manager not initialized"
            }
        
        try:
            logger.info(f"Executing alert: {alert}")
            
            # Handle both TradingViewAlert objects and dictionaries
            if hasattr(alert, 'symbol'):
                # TradingViewAlert object
                symbol = alert.symbol.upper()
                action = alert.action.lower()
                quantity = alert.quantity
                account_group = getattr(alert, 'account_group', 'main')
                alert_data = {
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'account_group': account_group,
                    'order_type': getattr(alert, 'order_type', 'market'),
                    'price': getattr(alert, 'price', None),
                    'strategy': getattr(alert, 'strategy', None),
                    'comment': getattr(alert, 'comment', None)
                }
            else:
                # Dictionary format (for backward compatibility)
                alert_data = alert
                symbol = alert_data.get("symbol", "").upper()
                action = alert_data.get("action", "").lower()
                quantity = alert_data.get("quantity", 1)
                account_group = alert_data.get("account_group", "main")
            
            # Validate parameters
            if not symbol or not action:
                return {
                    "status": "rejected",
                    "message": "Missing required parameters: symbol and action"
                }
            
            if action not in ["buy", "sell", "close"]:
                return {
                    "status": "rejected",
                    "message": f"Invalid action: {action}. Must be buy, sell, or close"
                }
            
            # Determine target account
            target_account_id = await self._get_target_account(account_group)
            if not target_account_id:
                return {
                    "status": "rejected",
                    "message": f"No account found for group: {account_group}"
                }
            
            # Check if this is a funded account (requires special handling)
            if self._is_funded_account(account_group):
                risk_check = await self._check_funded_account_rules(target_account_id, alert_data)
                if not risk_check.get("allowed"):
                    return {
                        "status": "rejected",
                        "message": f"Risk check failed: {risk_check.get('reason')}"
                    }
            
            # Handle different action types
            if action == "close":
                return await self._execute_close_position(target_account_id, symbol)
            else:
                return await self._execute_directional_order(
                    target_account_id, symbol, action, quantity, alert_data
                )
                
        except Exception as e:
            logger.error(f"Error executing alert: {e}")
            return {
                "status": "error",
                "message": f"Execution error: {str(e)}"
            }
    
    async def _get_target_account(self, account_group: str) -> Optional[int]:
        """Determine target account ID based on account group"""
        if account_group == "main" or not account_group:
            return self._default_account_id
        
        # For funded accounts, you would implement mapping logic here
        # For now, use default account
        logger.info(f"Using default account for group: {account_group}")
        return self._default_account_id
    
    def _is_funded_account(self, account_group: str) -> bool:
        """Check if account group represents a funded trading account"""
        funded_groups = ["topstep", "apex", "tradeday", "fundedtrader"]
        return account_group.lower() in funded_groups
    
    async def _check_funded_account_rules(
        self, 
        account_id: int, 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check funded account rules before execution.
        
        This is a placeholder for funded account risk management.
        In production, this would integrate with TopstepX or other
        funded account provider APIs.
        """
        try:
            # Get account performance
            performance = await self.account.get_account_performance(account_id)
            
            # Example rules (these would come from TopstepX API in production)
            MAX_DAILY_LOSS = 1000  # $1000 daily loss limit
            MAX_CONTRACTS = 3      # Max 3 contracts at once
            
            day_pnl = performance.get("day_pnl", 0)
            
            # Check daily loss limit
            if day_pnl <= -MAX_DAILY_LOSS:
                return {
                    "allowed": False,
                    "reason": f"Daily loss limit reached: ${abs(day_pnl):.2f}"
                }
            
            # Check contract limit
            positions = await self.account.get_positions(account_id)
            total_contracts = sum(abs(pos.net_position) for pos in positions)
            
            requested_quantity = alert_data.get("quantity", 1)
            if total_contracts + requested_quantity > MAX_CONTRACTS:
                return {
                    "allowed": False,
                    "reason": f"Contract limit exceeded: {total_contracts} + {requested_quantity} > {MAX_CONTRACTS}"
                }
            
            return {
                "allowed": True,
                "day_pnl": day_pnl,
                "contract_count": total_contracts
            }
            
        except Exception as e:
            logger.error(f"Error checking funded account rules: {e}")
            return {
                "allowed": False,
                "reason": f"Rule check error: {str(e)}"
            }
    
    async def _execute_close_position(self, account_id: int, symbol: str) -> Dict[str, Any]:
        """Execute position close/flatten order"""
        try:
            result = await self.orders.flatten_position(account_id, symbol)
            
            return {
                "status": "success" if result.is_filled or result.is_working else "failed",
                "action": "close",
                "symbol": symbol,
                "order_id": result.order_id,
                "message": result.message,
                "order_status": result.status
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                "status": "error",
                "message": f"Close position error: {str(e)}"
            }
    
    async def _execute_directional_order(
        self,
        account_id: int,
        symbol: str,
        action: str,
        quantity: int,
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute buy/sell order"""
        try:
            # Determine order type and price
            order_type = OrderType.MARKET  # Default to market orders
            price = alert_data.get("price")
            
            if price and alert_data.get("order_type") == "limit":
                order_type = OrderType.LIMIT
            
            # Execute order
            result = await self.orders.place_order(
                account_id=account_id,
                symbol=symbol,
                action=action.capitalize(),
                quantity=quantity,
                order_type=order_type,
                price=price
            )
            
            return {
                "status": "success" if result.is_filled or result.is_working else "failed",
                "action": action,
                "symbol": symbol,
                "quantity": quantity,
                "order_id": result.order_id,
                "message": result.message,
                "order_status": result.status,
                "filled_quantity": result.filled_quantity
            }
            
        except Exception as e:
            logger.error(f"Error executing directional order: {e}")
            return {
                "status": "error",
                "message": f"Order execution error: {str(e)}"
            }
    
    async def get_account_summary(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive account summary.
        
        Args:
            account_id: Account ID (uses default if None)
            
        Returns:
            Dict[str, Any]: Account summary
        """
        if not account_id:
            account_id = self._default_account_id
        
        if not account_id:
            return {"error": "No account ID specified"}
        
        try:
            # Get all account data in parallel
            account_info_task = self.account.get_account_info(account_id)
            balance_task = self.account.get_cash_balance(account_id)
            positions_task = self.account.get_positions(account_id)
            performance_task = self.account.get_account_performance(account_id)
            
            account_info, balance, positions, performance = await asyncio.gather(
                account_info_task, balance_task, positions_task, performance_task
            )
            
            return {
                "account_info": account_info.dict() if account_info else None,
                "balance": balance.dict() if balance else None,
                "positions": [pos.dict() for pos in positions],
                "performance": performance,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {"error": str(e)}
    
    async def start_market_data_stream(self, symbols: List[str]) -> bool:
        """
        Start real-time market data stream.
        
        Args:
            symbols: List of symbols to subscribe to
            
        Returns:
            bool: True if stream started successfully
        """
        try:
            if self._market_data_connected:
                logger.warning("Market data stream already running")
                return True
            
            # Start WebSocket stream in background
            asyncio.create_task(self.market_data.start_websocket_stream())
            
            # Wait a moment for connection
            await asyncio.sleep(1)
            
            # Subscribe to symbols
            await self.market_data.subscribe_quotes(symbols)
            
            self._market_data_connected = True
            logger.info(f"Started market data stream for {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting market data stream: {e}")
            return False
    
    async def stop_market_data_stream(self):
        """Stop real-time market data stream"""
        try:
            await self.market_data.stop_websocket_stream()
            self._market_data_connected = False
            logger.info("Stopped market data stream")
            
        except Exception as e:
            logger.error(f"Error stopping market data stream: {e}")
    
    async def close(self):
        """Close all connections and cleanup"""
        try:
            if self._market_data_connected:
                await self.stop_market_data_stream()
            
            await self.market_data.close()
            await self.auth.close()
            
            logger.info("Tradovate manager closed")
            
        except Exception as e:
            logger.error(f"Error closing Tradovate manager: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of Tradovate manager"""
        return {
            "initialized": self._initialized,
            "environment": "demo" if self.credentials.demo else "live",
            "account_count": len(self._accounts),
            "default_account_id": self._default_account_id,
            "market_data_connected": self._market_data_connected,
            "auth_token_valid": self.auth.tokens and not self.auth.tokens.is_expired if self.auth.tokens else False
        }
    
    def __repr__(self) -> str:
        env = "demo" if self.credentials.demo else "live"
        status = "initialized" if self._initialized else "not_initialized"
        return f"TradovateManager(env={env}, status={status}, accounts={len(self._accounts)})"