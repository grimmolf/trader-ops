"""
TradeNote Integration Hooks for TraderTerminal

Provides integration hooks for connecting TradeNote trade logging
to the live and paper trading execution engines.
"""

import logging
from typing import Optional, Dict, Any
from functools import partial

from .service import TradeNoteService, create_tradenote_service
from .models import TradeNoteConfig
from ..trading.execution_engine import ExecutionEngine, Order, Execution
from ..trading.paper_engine import PaperTradingEngine
from ..trading.paper_models import Fill, PaperOrder

logger = logging.getLogger(__name__)


class TradeNoteIntegration:
    """
    TradeNote integration manager for TraderTerminal.
    
    Manages the setup and configuration of TradeNote hooks
    for both live and paper trading engines.
    """
    
    def __init__(self, config: TradeNoteConfig):
        """
        Initialize TradeNote integration.
        
        Args:
            config: TradeNote configuration
        """
        self.config = config
        self.service: Optional[TradeNoteService] = None
        self._hooked_engines: Dict[str, Any] = {}
        
        logger.info("TradeNote integration initialized")
    
    async def initialize(self) -> None:
        """Initialize TradeNote service and prepare for hooking"""
        if not self.config.enabled:
            logger.info("TradeNote integration disabled")
            return
        
        try:
            # Create and initialize service
            self.service = create_tradenote_service(self.config)
            await self.service.initialize()
            
            logger.info("TradeNote integration ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize TradeNote integration: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown TradeNote integration"""
        if self.service:
            await self.service.shutdown()
        
        # Clear hooked engines
        self._hooked_engines.clear()
        
        logger.info("TradeNote integration shutdown")
    
    def hook_live_execution_engine(
        self,
        engine: ExecutionEngine,
        account_name: str,
        default_strategy: Optional[str] = None
    ) -> None:
        """
        Hook TradeNote logging into live execution engine.
        
        Args:
            engine: Live execution engine to hook
            account_name: Trading account name for logging
            default_strategy: Default strategy name if not provided in alerts
        """
        if not self.service:
            logger.warning("TradeNote service not initialized, skipping live engine hook")
            return
        
        # Create post-execution hook for live trades
        async def live_post_execution_hook(order: Order, context: Optional[Any] = None) -> None:
            """Post-execution hook for live trades"""
            try:
                # Wait for order to be filled and create execution record
                # This hook is called after successful order placement
                # We'll need to monitor for fills separately or integrate with the order monitoring
                
                strategy_name = default_strategy
                notes = None
                
                # Extract strategy and notes from context if available
                if context and hasattr(context, 'strategy_id'):
                    strategy_name = context.strategy_id or default_strategy
                
                if context and hasattr(context, 'notes'):
                    notes = context.notes
                
                # For now, we'll log the order placement
                # In practice, this should be called from _handle_order_fill
                logger.debug(f"Live order placed, will log to TradeNote when filled: {order.id}")
                
            except Exception as e:
                logger.error(f"Error in live post-execution hook: {e}")
        
        # Add hook to engine
        engine.add_post_execution_hook(live_post_execution_hook)
        self._hooked_engines[f"live_{id(engine)}"] = engine
        
        logger.info(f"TradeNote hooked into live execution engine for account: {account_name}")
    
    def hook_paper_trading_engine(
        self,
        engine: PaperTradingEngine,
        account_name: str,
        default_strategy: Optional[str] = None
    ) -> None:
        """
        Hook TradeNote logging into paper trading engine.
        
        Note: Paper trading engine doesn't have hook system like live engine,
        so we'll need to patch the execution method or create a wrapper.
        
        Args:
            engine: Paper trading engine to hook
            account_name: Paper account name for logging
            default_strategy: Default strategy name
        """
        if not self.service:
            logger.warning("TradeNote service not initialized, skipping paper engine hook")
            return
        
        # Store original execution method
        original_execute = engine.execute_paper_order
        
        # Create wrapped execution method
        async def wrapped_execute_paper_order(order: PaperOrder, account) -> Dict[str, Any]:
            """Wrapped paper order execution with TradeNote logging"""
            try:
                # Execute original order
                result = await original_execute(order, account)
                
                # Log to TradeNote if successful
                if result.get("status") == "success" and "fill" in result:
                    fill_data = result["fill"]
                    
                    # Create Fill object for logging
                    fill = Fill(
                        order_id=order.id,
                        account_id=account.id if hasattr(account, 'id') else account_name,
                        symbol=order.symbol,
                        side="buy" if order.is_buy_order() else "sell",
                        quantity=order.quantity,
                        price=fill_data["price"],
                        commission=fill_data["commission"],
                        fees=fill_data["fees"],
                        slippage=fill_data["slippage"],
                        timestamp=order.created_at,
                        broker="simulator"
                    )
                    
                    # Extract strategy name from order context
                    strategy_name = default_strategy
                    notes = f"Paper Trading Simulation"
                    
                    if hasattr(order, 'strategy_name') and order.strategy_name:
                        strategy_name = order.strategy_name
                    
                    if hasattr(order, 'notes') and order.notes:
                        notes = f"{notes} | {order.notes}"
                    
                    # Log to TradeNote
                    await self.service.log_paper_execution(
                        fill, order, account_name, strategy_name, notes
                    )
                    
                    logger.debug(f"Logged paper execution to TradeNote: {order.symbol}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in wrapped paper execution: {e}")
                # Return original result even if logging fails
                return await original_execute(order, account)
        
        # Replace engine's execute method
        engine.execute_paper_order = wrapped_execute_paper_order
        self._hooked_engines[f"paper_{id(engine)}"] = engine
        
        logger.info(f"TradeNote hooked into paper trading engine for account: {account_name}")
    
    async def log_execution_fill(
        self,
        execution: Execution,
        account_name: str,
        strategy_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Manually log an execution fill to TradeNote.
        
        This can be called directly from the order fill handler
        in the live execution engine.
        
        Args:
            execution: Execution data
            account_name: Account name
            strategy_name: Strategy name
            notes: Additional notes
            
        Returns:
            True if logged successfully
        """
        if not self.service:
            return False
        
        return await self.service.log_live_execution(
            execution, account_name, strategy_name, notes
        )
    
    async def sync_historical_trades(
        self,
        account_name: str,
        executions: list,
        is_paper: bool = False
    ) -> bool:
        """
        Sync historical trades to TradeNote.
        
        Args:
            account_name: Account name
            executions: List of historical executions
            is_paper: Whether these are paper trades
            
        Returns:
            True if sync successful
        """
        if not self.service:
            return False
        
        try:
            trades = []
            for execution in executions:
                if is_paper:
                    # Handle paper trade format
                    trade_data = self.service._convert_paper_execution(
                        execution.fill, execution.order, account_name
                    )
                else:
                    # Handle live trade format
                    trade_data = self.service._convert_live_execution(
                        execution, account_name
                    )
                trades.append(trade_data)
            
            result = await self.service.sync_account_history(account_name, trades)
            return result.success
            
        except Exception as e:
            logger.error(f"Error syncing historical trades: {e}")
            return False


# Utility function to create live execution hook for direct integration
def create_live_execution_fill_hook(
    tradenote_integration: TradeNoteIntegration,
    account_name: str,
    default_strategy: Optional[str] = None
):
    """
    Create a hook function that can be called directly from order fill handlers.
    
    Args:
        tradenote_integration: TradeNote integration instance
        account_name: Account name for logging
        default_strategy: Default strategy name
        
    Returns:
        Async hook function
    """
    async def execution_fill_hook(
        execution: Execution,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Hook to log execution fills to TradeNote"""
        try:
            strategy_name = default_strategy
            notes = None
            
            # Extract context information
            if context:
                if 'strategy_name' in context:
                    strategy_name = context['strategy_name'] or default_strategy
                if 'notes' in context:
                    notes = context['notes']
                if 'alert_id' in context:
                    notes = f"Alert: {context['alert_id']}" + (f" | {notes}" if notes else "")
            
            # Log to TradeNote
            await tradenote_integration.log_execution_fill(
                execution, account_name, strategy_name, notes
            )
            
        except Exception as e:
            logger.error(f"Error in execution fill hook: {e}")
    
    return execution_fill_hook


# Configuration helper
def load_tradenote_config_from_env() -> TradeNoteConfig:
    """Load TradeNote configuration from environment variables"""
    import os
    
    return TradeNoteConfig(
        base_url=os.getenv("TRADENOTE_BASE_URL", "http://localhost:8082"),
        app_id=os.getenv("TRADENOTE_APP_ID", ""),
        master_key=os.getenv("TRADENOTE_MASTER_KEY", ""),
        broker_name=os.getenv("TRADENOTE_BROKER_NAME", "TraderTerminal"),
        upload_mfe_prices=os.getenv("TRADENOTE_UPLOAD_MFE", "false").lower() == "true",
        timeout_seconds=int(os.getenv("TRADENOTE_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("TRADENOTE_RETRIES", "3")),
        enabled=os.getenv("TRADENOTE_ENABLED", "true").lower() == "true"
    )