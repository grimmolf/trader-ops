"""
TradeNote Integration Example for TraderTerminal

Example showing how to integrate TradeNote trade logging
with live and paper trading execution engines.
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from .hooks import TradeNoteIntegration, load_tradenote_config_from_env
from .models import TradeNoteConfig
from ..trading.execution_engine import ExecutionEngine, Order, Execution
from ..trading.paper_engine import PaperTradingEngine
from ..feeds.tradier import TradierConnector

logger = logging.getLogger(__name__)


async def setup_tradenote_integration_example():
    """
    Example setup for TradeNote integration with TraderTerminal.
    
    This function demonstrates how to:
    1. Initialize TradeNote integration
    2. Hook into live execution engine
    3. Hook into paper trading engine
    4. Handle execution logging
    """
    
    # Load TradeNote configuration from environment
    # Set these environment variables:
    # TRADENOTE_BASE_URL=http://localhost:8082
    # TRADENOTE_APP_ID=your_app_id
    # TRADENOTE_MASTER_KEY=your_master_key
    # TRADENOTE_ENABLED=true
    tradenote_config = load_tradenote_config_from_env()
    
    # Alternative: Manual configuration
    # tradenote_config = TradeNoteConfig(
    #     base_url="http://localhost:8082",
    #     app_id="<YOUR_APP_ID>",
    #     master_key="<YOUR_MASTER_KEY>",
    #     broker_name="TraderTerminal",
    #     enabled=True
    # )
    
    # Initialize TradeNote integration
    tradenote = TradeNoteIntegration(tradenote_config)
    await tradenote.initialize()
    
    try:
        # Example 1: Live Trading Integration
        await setup_live_trading_with_tradenote(tradenote)
        
        # Example 2: Paper Trading Integration
        await setup_paper_trading_with_tradenote(tradenote)
        
        # Example 3: Manual Trade Logging
        await manual_trade_logging_example(tradenote)
        
        logger.info("TradeNote integration examples completed successfully")
        
    finally:
        # Always shutdown cleanly
        await tradenote.shutdown()


async def setup_live_trading_with_tradenote(tradenote: TradeNoteIntegration):
    """Example: Integrate TradeNote with live execution engine"""
    
    # Initialize Tradier connector (example)
    tradier = TradierConnector(
        api_key="your_tradier_api_key",
        account_id="your_account_id",
        sandbox=True  # Use sandbox for testing
    )
    
    # Create execution engine
    execution_engine = ExecutionEngine(tradier)
    await execution_engine.initialize()
    
    try:
        # Hook TradeNote into the execution engine
        tradenote.hook_live_execution_engine(
            engine=execution_engine,
            account_name="Main Trading Account",
            default_strategy="TradingView Alerts"
        )
        
        # Alternative: Create custom order fill hook
        async def custom_tradenote_hook(execution: Execution, order: Order, status_data: Dict[str, Any]):
            """Custom hook for TradeNote logging with additional context"""
            
            # Extract strategy from order alert_id if available
            strategy_name = "Unknown Strategy"
            notes = None
            
            if hasattr(order, 'alert_id') and order.alert_id:
                strategy_name = f"Alert {order.alert_id}"
                notes = f"Original order: {order.id}"
            
            # Log to TradeNote
            success = await tradenote.log_execution_fill(
                execution=execution,
                account_name="Live Account",
                strategy_name=strategy_name,
                notes=notes
            )
            
            if success:
                logger.info(f"Logged live execution to TradeNote: {execution.symbol}")
            else:
                logger.warning(f"Failed to log execution to TradeNote: {execution.symbol}")
        
        # Register the custom hook
        execution_engine.add_order_fill_hook(custom_tradenote_hook)
        
        logger.info("Live trading TradeNote integration setup complete")
        
        # Note: In practice, the execution engine would be running
        # and processing actual webhook alerts here
        
    finally:
        await execution_engine.close()


async def setup_paper_trading_with_tradenote(tradenote: TradeNoteIntegration):
    """Example: Integrate TradeNote with paper trading engine"""
    
    # Create paper trading engine
    paper_engine = PaperTradingEngine()
    await paper_engine.initialize()
    
    try:
        # Hook TradeNote into paper trading
        tradenote.hook_paper_trading_engine(
            engine=paper_engine,
            account_name="Paper Trading Account",
            default_strategy="Strategy Testing"
        )
        
        logger.info("Paper trading TradeNote integration setup complete")
        
        # Example: Execute a paper trade (this would be logged to TradeNote)
        # from ..trading.paper_models import PaperOrder, PaperTradingAccount
        # 
        # account = PaperTradingAccount(
        #     id="paper_001",
        #     name="Test Account",
        #     initial_balance=10000
        # )
        # 
        # order = PaperOrder(
        #     symbol="AAPL",
        #     quantity=100,
        #     order_type="market",
        #     side="buy"
        # )
        # 
        # result = await paper_engine.execute_paper_order(order, account)
        # logger.info(f"Paper trade result: {result}")
        
    finally:
        # Note: Paper engine might not have a close method
        pass


async def manual_trade_logging_example(tradenote: TradeNoteIntegration):
    """Example: Manually log trades to TradeNote"""
    
    # Example: Log a historical trade manually
    from ..models.execution import Execution, OrderSide
    from datetime import datetime, timezone
    
    # Create example execution
    historical_execution = Execution(
        id="hist_001",
        order_id="order_001",
        broker="Example Broker",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=100,
        price=150.00,
        commission=1.00,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Log to TradeNote
    success = await tradenote.log_execution_fill(
        execution=historical_execution,
        account_name="Historical Data",
        strategy_name="Manual Entry",
        notes="Historical trade import"
    )
    
    if success:
        logger.info("Successfully logged historical trade to TradeNote")
    else:
        logger.warning("Failed to log historical trade to TradeNote")
    
    # Example: Sync multiple historical trades
    historical_trades = [
        # Add more Execution objects here
        historical_execution
    ]
    
    sync_success = await tradenote.sync_historical_trades(
        account_name="Historical Data",
        executions=historical_trades,
        is_paper=False
    )
    
    if sync_success:
        logger.info("Successfully synced historical trades to TradeNote")
    else:
        logger.warning("Failed to sync historical trades to TradeNote")


# Configuration validation helper
def validate_tradenote_config(config: TradeNoteConfig) -> bool:
    """Validate TradeNote configuration"""
    
    if not config.enabled:
        logger.info("TradeNote integration is disabled")
        return False
    
    if not config.app_id or not config.master_key:
        logger.error("TradeNote app_id and master_key are required")
        return False
    
    if not config.base_url:
        logger.error("TradeNote base_url is required")
        return False
    
    logger.info("TradeNote configuration is valid")
    return True


# Startup helper for main application
async def initialize_tradenote_for_application(
    execution_engine: Optional[ExecutionEngine] = None,
    paper_engine: Optional[PaperTradingEngine] = None,
    config: Optional[TradeNoteConfig] = None
) -> Optional[TradeNoteIntegration]:
    """
    Initialize TradeNote integration for the main TraderTerminal application.
    
    Args:
        execution_engine: Live execution engine (optional)
        paper_engine: Paper trading engine (optional)
        config: TradeNote configuration (will load from env if not provided)
    
    Returns:
        TradeNote integration instance or None if disabled/failed
    """
    
    # Load configuration
    if not config:
        config = load_tradenote_config_from_env()
    
    # Validate configuration
    if not validate_tradenote_config(config):
        return None
    
    try:
        # Initialize TradeNote integration
        tradenote = TradeNoteIntegration(config)
        await tradenote.initialize()
        
        # Hook into execution engines if provided
        if execution_engine:
            tradenote.hook_live_execution_engine(
                engine=execution_engine,
                account_name="Live Trading",
                default_strategy="TradingView"
            )
            logger.info("TradeNote hooked into live execution engine")
        
        if paper_engine:
            tradenote.hook_paper_trading_engine(
                engine=paper_engine,
                account_name="Paper Trading",
                default_strategy="Strategy Testing"
            )
            logger.info("TradeNote hooked into paper trading engine")
        
        logger.info("TradeNote integration initialized successfully")
        return tradenote
        
    except Exception as e:
        logger.error(f"Failed to initialize TradeNote integration: {e}")
        return None


if __name__ == "__main__":
    # Run the example
    logging.basicConfig(level=logging.INFO)
    asyncio.run(setup_tradenote_integration_example())