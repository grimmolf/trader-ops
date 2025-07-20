"""
Paper Trading Router for TraderTerminal

Routes paper trading orders to appropriate execution engines:
- Broker sandbox environments (real APIs with fake money)
- Internal simulator (full simulation with market data)
- Hybrid mode (sandbox execution with simulated fills)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime

from .paper_models import (
    PaperTradingAccount, PaperOrder, Fill, PaperTradingMode, 
    PaperTradingAlert, OrderStatus, AssetType, MarketDataSnapshot
)

if TYPE_CHECKING:
    from .paper_engine import InternalPaperTradingEngine
    from ..feeds.tastytrade.manager import TastytradeManager
    from ..feeds.tradovate.manager import TradovateManager

logger = logging.getLogger(__name__)


class PaperTradingRouter:
    """
    Route paper trading orders to appropriate execution engines
    
    Supports multiple execution modes:
    - SANDBOX: Use real broker sandbox APIs
    - SIMULATOR: Internal simulation engine
    - HYBRID: Sandbox for order management, simulator for fills
    """
    
    def __init__(self):
        self.accounts: Dict[str, PaperTradingAccount] = {}
        self.execution_engines: Dict[str, Any] = {}
        self.active_orders: Dict[str, PaperOrder] = {}
        self.fills: List[Fill] = []
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize paper trading router and execution engines"""
        if self._initialized:
            return
            
        try:
            # Initialize execution engines
            await self._setup_execution_engines()
            
            # Load or create default paper trading accounts
            await self._setup_default_accounts()
            
            self._initialized = True
            logger.info("Paper trading router initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize paper trading router: {e}")
            raise
    
    async def _setup_execution_engines(self) -> None:
        """Setup all available execution engines"""
        try:
            # Import here to avoid circular imports
            from .paper_engine import InternalPaperTradingEngine
            
            # Initialize internal simulator
            self.execution_engines["simulator"] = InternalPaperTradingEngine()
            await self.execution_engines["simulator"].initialize()
            
            # Try to initialize broker sandbox engines
            await self._setup_sandbox_engines()
            
        except Exception as e:
            logger.warning(f"Some execution engines failed to initialize: {e}")
            # Continue with at least the simulator
            if "simulator" not in self.execution_engines:
                from .paper_engine import InternalPaperTradingEngine
                self.execution_engines["simulator"] = InternalPaperTradingEngine()
                await self.execution_engines["simulator"].initialize()
    
    async def _setup_sandbox_engines(self) -> None:
        """Setup broker sandbox engines if credentials available"""
        try:
            # Try Tastytrade sandbox
            try:
                from ..feeds.tastytrade.manager import TastytradeManager
                from ..security.credential_loader import load_tastytrade_credentials
                
                creds = await load_tastytrade_credentials()
                if creds and creds.sandbox:
                    tastytrade_manager = TastytradeManager(creds)
                    self.execution_engines["tastytrade_sandbox"] = tastytrade_manager
                    logger.info("Tastytrade sandbox engine initialized")
            except Exception as e:
                logger.debug(f"Tastytrade sandbox not available: {e}")
            
            # Try Tradovate demo
            try:
                from ..feeds.tradovate.manager import TradovateManager
                from ..security.credential_loader import load_tradovate_credentials
                
                creds = await load_tradovate_credentials()
                if creds and creds.demo:
                    tradovate_manager = TradovateManager(creds)
                    self.execution_engines["tradovate_demo"] = tradovate_manager
                    logger.info("Tradovate demo engine initialized")
            except Exception as e:
                logger.debug(f"Tradovate demo not available: {e}")
            
            # Try Alpaca paper (free tier)
            try:
                # TODO: Implement Alpaca paper trading when credentials available
                pass
            except Exception as e:
                logger.debug(f"Alpaca paper not available: {e}")
                
        except Exception as e:
            logger.warning(f"Failed to setup sandbox engines: {e}")
    
    async def _setup_default_accounts(self) -> None:
        """Setup default paper trading accounts"""
        default_accounts = [
            {
                "id": "paper_simulator",
                "name": "Internal Simulator",
                "broker": "simulator",
                "mode": PaperTradingMode.SIMULATOR,
                "initial_balance": Decimal("100000")
            },
            {
                "id": "paper_tastytrade", 
                "name": "Tastytrade Sandbox",
                "broker": "tastytrade_sandbox",
                "mode": PaperTradingMode.SANDBOX,
                "initial_balance": Decimal("100000")
            },
            {
                "id": "paper_tradovate",
                "name": "Tradovate Demo", 
                "broker": "tradovate_demo",
                "mode": PaperTradingMode.SANDBOX,
                "initial_balance": Decimal("50000")
            },
            {
                "id": "paper_hybrid",
                "name": "Hybrid Mode",
                "broker": "simulator",
                "mode": PaperTradingMode.HYBRID,
                "initial_balance": Decimal("100000")
            }
        ]
        
        for account_config in default_accounts:
            # Only create account if the execution engine is available
            broker = account_config["broker"]
            if broker in self.execution_engines or broker == "simulator":
                account = PaperTradingAccount(**account_config)
                self.accounts[account.id] = account
                logger.info(f"Created paper trading account: {account.name}")
    
    async def route_alert(self, alert: PaperTradingAlert) -> Dict[str, Any]:
        """Route a paper trading alert to appropriate execution engine"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Determine target account and execution engine
            account_id, engine_key = self._determine_routing(alert)
            
            if account_id not in self.accounts:
                return {
                    "status": "error",
                    "message": f"Paper trading account not found: {account_id}",
                    "alert": alert.dict()
                }
            
            if engine_key not in self.execution_engines:
                # Fallback to simulator
                engine_key = "simulator"
                logger.warning(f"Execution engine not available, falling back to simulator")
            
            account = self.accounts[account_id]
            engine = self.execution_engines[engine_key]
            
            # Create paper order
            order = PaperOrder(
                account_id=account_id,
                symbol=alert.symbol,
                asset_type=self._determine_asset_type(alert.symbol),
                action=alert.action,
                order_type=alert.order_type,
                quantity=alert.quantity,
                price=alert.price,
                stop_price=alert.stop_price,
                broker=engine_key,
                strategy=alert.strategy,
                comment=alert.comment
            )
            
            # Store order
            self.active_orders[order.id] = order
            
            # Execute order
            result = await self._execute_order(order, engine, account)
            
            # Update order status
            order.status = OrderStatus.FILLED if result["status"] == "success" else OrderStatus.REJECTED
            order.updated_at = datetime.now()
            
            if result["status"] == "success" and "fill" in result:
                order.filled_at = datetime.now()
                order.filled_quantity = order.quantity
                order.avg_fill_price = Decimal(str(result["fill"]["price"]))
            
            return {
                "status": result["status"],
                "order_id": order.id,
                "account_id": account_id,
                "execution_engine": engine_key,
                "order": order.dict(),
                "result": result,
                "is_paper": True
            }
            
        except Exception as e:
            logger.error(f"Failed to route paper trading alert: {e}")
            return {
                "status": "error",
                "message": str(e),
                "alert": alert.dict()
            }
    
    def _determine_routing(self, alert: PaperTradingAlert) -> tuple[str, str]:
        """Determine which account and execution engine to use"""
        
        # Extract broker preference from account_group
        broker_preference = alert.get_paper_broker()
        
        # Map to account ID and execution engine
        if broker_preference == "auto":
            # Auto-select based on symbol type
            if alert.symbol in ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL"]:  # Futures
                if "tradovate_demo" in self.execution_engines:
                    return "paper_tradovate", "tradovate_demo"
                else:
                    return "paper_simulator", "simulator"
            elif "/" in alert.symbol or "C" in alert.symbol or "P" in alert.symbol:  # Options
                if "tastytrade_sandbox" in self.execution_engines:
                    return "paper_tastytrade", "tastytrade_sandbox"
                else:
                    return "paper_simulator", "simulator"
            else:  # Stocks
                if "tastytrade_sandbox" in self.execution_engines:
                    return "paper_tastytrade", "tastytrade_sandbox"
                else:
                    return "paper_simulator", "simulator"
        else:
            # Use specific broker preference
            broker_map = {
                "tastytrade_sandbox": ("paper_tastytrade", "tastytrade_sandbox"),
                "tradovate_demo": ("paper_tradovate", "tradovate_demo"),
                "alpaca_paper": ("paper_alpaca", "alpaca_paper"),
                "simulator": ("paper_simulator", "simulator")
            }
            
            return broker_map.get(broker_preference, ("paper_simulator", "simulator"))
    
    def _determine_asset_type(self, symbol: str) -> AssetType:
        """Determine asset type from symbol"""
        if symbol in ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL", "NG", "ZB", "ZN", "ZC", "ZS", "ZW"]:
            return AssetType.FUTURE
        elif "/" in symbol or symbol.endswith("C") or symbol.endswith("P"):
            return AssetType.OPTION
        elif symbol in ["BTC", "ETH", "BTC-USD", "ETH-USD"]:
            return AssetType.CRYPTO
        else:
            return AssetType.STOCK
    
    async def _execute_order(self, order: PaperOrder, engine: Any, account: PaperTradingAccount) -> Dict[str, Any]:
        """Execute order using the specified engine"""
        try:
            # Convert order to engine-specific format
            if hasattr(engine, 'execute_paper_order'):
                # Use paper trading specific method if available
                result = await engine.execute_paper_order(order, account)
            elif hasattr(engine, 'execute_alert'):
                # Convert to alert format for engine
                alert_dict = {
                    "symbol": order.symbol,
                    "action": order.action.value,
                    "quantity": float(order.quantity),
                    "order_type": order.order_type.value,
                    "price": float(order.price) if order.price else None,
                    "strategy": order.strategy,
                    "comment": order.comment
                }
                
                # Create mock alert object
                from ..webhooks.models import TradingViewAlert
                mock_alert = TradingViewAlert(**alert_dict)
                result = await engine.execute_alert(mock_alert)
            else:
                # Use internal simulator as fallback
                simulator = self.execution_engines["simulator"]
                result = await simulator.execute_paper_order(order, account)
            
            # Process fill if successful
            if result.get("status") == "success" and "fill" in result:
                fill = Fill(
                    order_id=order.id,
                    account_id=account.id,
                    symbol=order.symbol,
                    side="buy" if order.is_buy_order() else "sell",
                    quantity=order.quantity,
                    price=Decimal(str(result["fill"]["price"])),
                    commission=Decimal(str(result["fill"].get("commission", 0))),
                    slippage=Decimal(str(result["fill"].get("slippage", 0))),
                    broker=order.broker
                )
                
                self.fills.append(fill)
                
                # Update account
                await self._update_account_from_fill(account, fill, order)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute order {order.id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _update_account_from_fill(self, account: PaperTradingAccount, fill: Fill, order: PaperOrder) -> None:
        """Update account balance and positions from fill"""
        try:
            # Update position
            if fill.symbol not in account.positions:
                from .paper_models import Position
                account.positions[fill.symbol] = Position(
                    symbol=fill.symbol,
                    asset_type=order.asset_type,
                    quantity=Decimal("0"),
                    avg_price=Decimal("0"),
                    multiplier=self._get_multiplier(fill.symbol)
                )
            
            position = account.positions[fill.symbol]
            
            # Calculate new position
            if fill.side == "buy":
                new_quantity = position.quantity + fill.quantity
                if new_quantity != 0:
                    # Calculate new average price
                    total_cost = (position.quantity * position.avg_price) + (fill.quantity * fill.price)
                    position.avg_price = total_cost / new_quantity
                position.quantity = new_quantity
            else:  # sell
                position.quantity -= fill.quantity
                if position.quantity == 0:
                    # Position closed, realize P&L
                    realized_pnl = (fill.price - position.avg_price) * fill.quantity * position.multiplier
                    account.update_pnl(realized_pnl)
            
            # Update account balance (subtract commission and fees)
            total_cost = fill.total_cost
            if fill.side == "sell":
                account.update_balance(total_cost)
            else:
                account.update_balance(-total_cost)
            
            logger.info(f"Updated account {account.id} from fill: {fill.symbol} {fill.side} {fill.quantity}@{fill.price}")
            
        except Exception as e:
            logger.error(f"Failed to update account from fill: {e}")
    
    def _get_multiplier(self, symbol: str) -> Decimal:
        """Get contract multiplier for symbol"""
        multipliers = {
            "ES": Decimal("50"),     # E-mini S&P 500
            "NQ": Decimal("20"),     # E-mini Nasdaq
            "YM": Decimal("5"),      # E-mini Dow
            "RTY": Decimal("50"),    # E-mini Russell
            "GC": Decimal("100"),    # Gold
            "SI": Decimal("5000"),   # Silver
            "CL": Decimal("1000"),   # Crude Oil
            "NG": Decimal("10000"),  # Natural Gas
        }
        
        return multipliers.get(symbol, Decimal("1"))
    
    async def get_account(self, account_id: str) -> Optional[PaperTradingAccount]:
        """Get paper trading account by ID"""
        return self.accounts.get(account_id)
    
    async def get_all_accounts(self) -> List[PaperTradingAccount]:
        """Get all paper trading accounts"""
        return list(self.accounts.values())
    
    async def get_account_orders(self, account_id: str, limit: int = 100) -> List[PaperOrder]:
        """Get orders for a specific account"""
        orders = [order for order in self.active_orders.values() if order.account_id == account_id]
        orders.sort(key=lambda x: x.created_at, reverse=True)
        return orders[:limit]
    
    async def get_account_fills(self, account_id: str, limit: int = 100) -> List[Fill]:
        """Get fills for a specific account"""
        fills = [fill for fill in self.fills if fill.account_id == account_id]
        fills.sort(key=lambda x: x.timestamp, reverse=True)
        return fills[:limit]
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a paper trading order"""
        if order_id not in self.active_orders:
            return {"status": "error", "message": "Order not found"}
        
        order = self.active_orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return {"status": "error", "message": f"Cannot cancel order with status: {order.status}"}
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        
        return {"status": "success", "order_id": order_id}
    
    async def flatten_account_positions(self, account_id: str) -> Dict[str, Any]:
        """Flatten all positions in an account"""
        if account_id not in self.accounts:
            return {"status": "error", "message": "Account not found"}
        
        account = self.accounts[account_id]
        results = []
        
        for symbol, position in account.positions.items():
            if position.quantity != 0:
                # Create close order
                close_alert = PaperTradingAlert(
                    symbol=symbol,
                    action="sell" if position.quantity > 0 else "buy",
                    quantity=abs(position.quantity),
                    account_group=f"paper_{account.broker}",
                    comment="FLATTEN_ALL"
                )
                
                result = await self.route_alert(close_alert)
                results.append(result)
        
        return {
            "status": "success",
            "account_id": account_id,
            "positions_closed": len(results),
            "results": results
        }
    
    async def execute_alert(self, execution_request: Any) -> Dict[str, Any]:
        """
        Execute alert compatible with webhook processor interface.
        
        This method provides compatibility with the webhook receiver that expects
        an execute_alert method from broker connectors.
        """
        try:
            # Convert execution request to paper trading alert
            # Assuming execution_request has similar structure to TradingViewAlert
            alert = PaperTradingAlert(
                symbol=execution_request.symbol,
                action=execution_request.action,
                quantity=execution_request.quantity,
                order_type=getattr(execution_request, 'order_type', 'market'),
                price=getattr(execution_request, 'price', None),
                stop_price=getattr(execution_request, 'stop_price', None),
                account_group=getattr(execution_request, 'account_group', 'paper_simulator'),
                strategy=getattr(execution_request, 'strategy', None),
                comment=getattr(execution_request, 'comment', 'Webhook alert')
            )
            
            # Route alert through paper trading system
            result = await self.route_alert(alert)
            
            # Convert result to format expected by webhook processor
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "order": {
                        "id": result.get("order_id"),
                        "status": "filled" if result.get("result", {}).get("status") == "success" else "pending"
                    },
                    "execution": result.get("result", {}),
                    "message": f"Paper trading order executed: {alert.symbol} {alert.action} {alert.quantity}"
                }
            else:
                return {
                    "status": "error",
                    "reason": result.get("message", "Paper trading execution failed"),
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"Failed to execute paper trading alert: {e}")
            return {
                "status": "error",
                "reason": f"Paper trading execution error: {str(e)}"
            }


# Global paper trading router instance
_paper_router: Optional[PaperTradingRouter] = None


def get_paper_trading_router() -> PaperTradingRouter:
    """Get the global paper trading router instance"""
    global _paper_router
    if _paper_router is None:
        _paper_router = PaperTradingRouter()
    return _paper_router