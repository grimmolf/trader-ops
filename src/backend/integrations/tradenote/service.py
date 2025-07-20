"""
TradeNote Integration Service for TraderTerminal

Provides automated trade logging service that integrates with:
- Live trading execution engine
- Paper trading simulation engine
- Strategy performance tracking system
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timezone
from decimal import Decimal

from .client import TradeNoteClient, TradeNoteClientError
from .models import TradeNoteConfig, TradeNoteTradeData, TradeNoteResponse
from ..models.execution import Execution, Order, OrderSide
from ..trading.paper_models import Fill, PaperOrder
from ..performance.models import TradeResult

logger = logging.getLogger(__name__)


class TradeNoteService:
    """
    TradeNote integration service for automated trade logging.
    
    Handles conversion of execution data from various sources to TradeNote format
    and manages the upload process with error handling and retry logic.
    """
    
    def __init__(self, config: TradeNoteConfig):
        """
        Initialize TradeNote service with configuration.
        
        Args:
            config: TradeNote configuration
        """
        self.config = config
        self._client: Optional[TradeNoteClient] = None
        self.enabled = config.enabled
        
        # Queue for batch processing
        self._trade_queue: List[TradeNoteTradeData] = []
        self._queue_lock = asyncio.Lock()
        self._batch_size = 10
        self._batch_timeout = 30  # seconds
        
        # Background tasks
        self._batch_processor_task: Optional[asyncio.Task] = None
        
        logger.info(f"TradeNote service initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> None:
        """Initialize the TradeNote service"""
        if not self.enabled:
            logger.info("TradeNote service disabled")
            return
        
        try:
            # Initialize client
            self._client = TradeNoteClient(self.config)
            await self._client.connect()
            
            # Start batch processor
            self._batch_processor_task = asyncio.create_task(self._batch_processor())
            
            logger.info("TradeNote service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TradeNote service: {e}")
            self.enabled = False
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the TradeNote service"""
        # Cancel batch processor
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining trades
        await self._flush_queue()
        
        # Disconnect client
        if self._client:
            await self._client.disconnect()
        
        logger.info("TradeNote service shutdown")
    
    async def log_live_execution(
        self,
        execution: Execution,
        account_name: str,
        strategy_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Log a live trading execution to TradeNote.
        
        Args:
            execution: Live execution data from trading engine
            account_name: Trading account identifier
            strategy_name: Strategy name if available
            notes: Additional notes for the trade
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.enabled:
            return True  # Silently succeed when disabled
        
        try:
            # Convert execution to TradeNote format
            trade_data = self._convert_live_execution(
                execution, account_name, strategy_name, notes
            )
            
            # Add to queue for batch processing
            await self._enqueue_trade(trade_data)
            
            logger.debug(f"Queued live execution for TradeNote: {execution.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log live execution: {e}")
            return False
    
    async def log_paper_execution(
        self,
        fill: Fill,
        order: PaperOrder,
        account_name: str,
        strategy_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Log a paper trading execution to TradeNote.
        
        Args:
            fill: Paper trading fill data
            order: Original paper order
            account_name: Paper trading account identifier
            strategy_name: Strategy name if available
            notes: Additional notes for the trade
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.enabled:
            return True  # Silently succeed when disabled
        
        try:
            # Convert paper execution to TradeNote format
            trade_data = self._convert_paper_execution(
                fill, order, account_name, strategy_name, notes
            )
            
            # Add to queue for batch processing
            await self._enqueue_trade(trade_data)
            
            logger.debug(f"Queued paper execution for TradeNote: {fill.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log paper execution: {e}")
            return False
    
    async def log_strategy_trade(
        self,
        trade_result: TradeResult,
        account_name: str,
        strategy_name: str,
        is_paper: bool = False,
        notes: Optional[str] = None
    ) -> bool:
        """
        Log a completed strategy trade to TradeNote.
        
        Args:
            trade_result: Strategy trade result from performance tracker
            account_name: Trading account identifier
            strategy_name: Strategy name
            is_paper: Whether this is a paper trade
            notes: Additional notes for the trade
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.enabled:
            return True  # Silently succeed when disabled
        
        try:
            # Convert trade result to TradeNote format
            trade_data = TradeNoteTradeData.from_traderterminal_trade(
                trade_result, account_name, strategy_name, is_paper, notes
            )
            
            # Add to queue for batch processing
            await self._enqueue_trade(trade_data)
            
            logger.debug(f"Queued strategy trade for TradeNote: {trade_result.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log strategy trade: {e}")
            return False
    
    async def bulk_upload_trades(
        self,
        trades: List[TradeNoteTradeData]
    ) -> TradeNoteResponse:
        """
        Upload multiple trades directly to TradeNote.
        
        Args:
            trades: List of trade data to upload
            
        Returns:
            Upload response
        """
        if not self.enabled or not self._client:
            return TradeNoteResponse(
                success=True,
                message="TradeNote disabled - upload skipped"
            )
        
        try:
            return await self._client.upload_trades(trades)
        except Exception as e:
            logger.error(f"Bulk upload failed: {e}")
            return TradeNoteResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
    
    async def sync_account_history(
        self,
        account_name: str,
        trades: List[TradeNoteTradeData]
    ) -> TradeNoteResponse:
        """
        Sync historical trades for an account.
        
        Args:
            account_name: Account identifier
            trades: Historical trade data
            
        Returns:
            Sync response
        """
        if not self.enabled or not self._client:
            return TradeNoteResponse(
                success=True,
                message="TradeNote disabled - sync skipped"
            )
        
        try:
            return await self._client.sync_account_trades(account_name, trades)
        except Exception as e:
            logger.error(f"Account sync failed: {e}")
            return TradeNoteResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
    
    def _convert_live_execution(
        self,
        execution: Execution,
        account_name: str,
        strategy_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> TradeNoteTradeData:
        """Convert live execution to TradeNote format"""
        
        # Extract timing information
        exec_dt = execution.timestamp if isinstance(execution.timestamp, datetime) else datetime.now(timezone.utc)
        trade_date = exec_dt.strftime("%m/%d/%Y")
        exec_time = exec_dt.strftime("%H:%M:%S")
        
        # Determine instrument type
        symbol = execution.symbol.upper()
        if symbol in ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL", "NG"] or "/" in symbol:
            instrument_type = "future"
        elif "C" in symbol or "P" in symbol:
            instrument_type = "option"
        else:
            instrument_type = "stock"
        
        # Calculate proceeds
        gross_proceeds = execution.quantity * execution.price
        if execution.side == OrderSide.SELL:
            gross_proceeds = gross_proceeds  # Positive for sales
        else:
            gross_proceeds = -gross_proceeds  # Negative for purchases
        
        net_proceeds = gross_proceeds - execution.commission
        
        # Build notes
        trade_notes = []
        if notes:
            trade_notes.append(notes)
        trade_notes.append(f"Live Execution - Broker: {execution.broker}")
        if execution.broker_execution_id:
            trade_notes.append(f"Broker ID: {execution.broker_execution_id}")
        
        return TradeNoteTradeData(
            account=account_name,
            trade_date=trade_date,
            settlement_date=trade_date,
            currency="USD",
            type=instrument_type,
            side="Buy" if execution.side == OrderSide.BUY else "Sell",
            symbol=symbol,
            quantity=int(execution.quantity),
            price=Decimal(str(execution.price)),
            exec_time=exec_time,
            gross_proceeds=Decimal(str(gross_proceeds)),
            commissions_fees=Decimal(str(execution.commission)),
            net_proceeds=Decimal(str(net_proceeds)),
            strategy=strategy_name,
            notes=" | ".join(trade_notes),
            is_paper_trade=False,
            trade_id=execution.id or execution.order_id
        )
    
    def _convert_paper_execution(
        self,
        fill: Fill,
        order: PaperOrder,
        account_name: str,
        strategy_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> TradeNoteTradeData:
        """Convert paper execution to TradeNote format"""
        
        # Extract timing information
        exec_dt = fill.timestamp
        trade_date = exec_dt.strftime("%m/%d/%Y")
        exec_time = exec_dt.strftime("%H:%M:%S")
        
        # Determine instrument type
        symbol = fill.symbol.upper()
        if hasattr(order, 'asset_type'):
            type_map = {
                "stock": "stock",
                "future": "future",
                "option": "option",
                "crypto": "crypto",
                "forex": "forex"
            }
            instrument_type = type_map.get(order.asset_type.value, "stock")
        else:
            # Fallback to symbol-based detection
            if symbol in ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL", "NG"] or "/" in symbol:
                instrument_type = "future"
            elif "C" in symbol or "P" in symbol:
                instrument_type = "option"
            else:
                instrument_type = "stock"
        
        # Calculate proceeds
        gross_proceeds = fill.quantity * fill.price
        if fill.side == "sell":
            gross_proceeds = gross_proceeds  # Positive for sales
        else:
            gross_proceeds = -gross_proceeds  # Negative for purchases
        
        total_fees = fill.commission + fill.fees
        net_proceeds = gross_proceeds - total_fees
        
        # Build notes
        trade_notes = []
        if notes:
            trade_notes.append(notes)
        trade_notes.append(f"Paper Trading - Slippage: ${fill.slippage:.4f}")
        trade_notes.append(f"Broker: {fill.broker}")
        
        return TradeNoteTradeData(
            account=f"{account_name} (Paper)",
            trade_date=trade_date,
            settlement_date=trade_date,
            currency="USD",
            type=instrument_type,
            side="Buy" if fill.side == "buy" else "Sell",
            symbol=symbol,
            quantity=int(fill.quantity),
            price=Decimal(str(fill.price)),
            exec_time=exec_time,
            gross_proceeds=Decimal(str(gross_proceeds)),
            commissions_fees=Decimal(str(total_fees)),
            net_proceeds=Decimal(str(net_proceeds)),
            strategy=strategy_name,
            notes=" | ".join(trade_notes),
            is_paper_trade=True,
            trade_id=fill.order_id
        )
    
    async def _enqueue_trade(self, trade_data: TradeNoteTradeData) -> None:
        """Add trade to queue for batch processing"""
        async with self._queue_lock:
            self._trade_queue.append(trade_data)
            
            # Trigger immediate upload if queue is full
            if len(self._trade_queue) >= self._batch_size:
                await self._flush_queue()
    
    async def _flush_queue(self) -> None:
        """Flush all queued trades to TradeNote"""
        async with self._queue_lock:
            if not self._trade_queue or not self._client:
                return
            
            trades_to_upload = self._trade_queue.copy()
            self._trade_queue.clear()
        
        try:
            result = await self._client.upload_trades(trades_to_upload)
            if result.success:
                logger.info(f"Successfully uploaded {len(trades_to_upload)} trades to TradeNote")
            else:
                logger.error(f"Failed to upload trades: {result.message}")
                # Re-queue failed trades for retry
                async with self._queue_lock:
                    self._trade_queue.extend(trades_to_upload)
                    
        except Exception as e:
            logger.error(f"Error flushing trade queue: {e}")
            # Re-queue trades for retry
            async with self._queue_lock:
                self._trade_queue.extend(trades_to_upload)
    
    async def _batch_processor(self) -> None:
        """Background task for batch processing queued trades"""
        while True:
            try:
                await asyncio.sleep(self._batch_timeout)
                await self._flush_queue()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(5)  # Wait before retrying


# Factory function for creating TradeNote service
def create_tradenote_service(config: TradeNoteConfig) -> TradeNoteService:
    """Create TradeNote service with configuration"""
    return TradeNoteService(config)


# Hook functions for integration with execution engines
async def live_execution_hook(
    tradenote_service: TradeNoteService,
    execution: Execution,
    account_name: str,
    strategy_name: Optional[str] = None,
    notes: Optional[str] = None
) -> None:
    """Hook function for live execution logging"""
    await tradenote_service.log_live_execution(
        execution, account_name, strategy_name, notes
    )


async def paper_execution_hook(
    tradenote_service: TradeNoteService,
    fill: Fill,
    order: PaperOrder,
    account_name: str,
    strategy_name: Optional[str] = None,
    notes: Optional[str] = None
) -> None:
    """Hook function for paper execution logging"""
    await tradenote_service.log_paper_execution(
        fill, order, account_name, strategy_name, notes
    )


async def strategy_trade_hook(
    tradenote_service: TradeNoteService,
    trade_result: TradeResult,
    account_name: str,
    strategy_name: str,
    is_paper: bool = False,
    notes: Optional[str] = None
) -> None:
    """Hook function for strategy trade logging"""
    await tradenote_service.log_strategy_trade(
        trade_result, account_name, strategy_name, is_paper, notes
    )