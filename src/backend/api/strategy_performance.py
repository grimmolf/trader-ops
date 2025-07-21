"""
Strategy Performance API

FastAPI endpoints for managing strategy performance, auto-rotation,
and real-time monitoring of trading strategies.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..trading.strategy_models import (PerformanceMetric,
                                       StrategyConfiguration,
                                       StrategyPerformance, StrategyStatus,
                                       TradeRecord, TradingMode)
from ..trading.strategy_tracker import StrategyPerformanceTracker

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/strategy-performance", tags=["Strategy Performance"])


# Pydantic models for API
class StrategyRegistrationRequest(BaseModel):
    strategy_name: str = Field(..., description="Unique strategy name")
    trading_mode: TradingMode = Field(
        default=TradingMode.PAPER, description="Initial trading mode"
    )
    auto_rotation_enabled: bool = Field(
        default=True, description="Enable automatic live/paper rotation"
    )
    min_win_rate: Optional[float] = Field(
        default=0.55, description="Minimum win rate threshold"
    )
    max_drawdown: Optional[float] = Field(
        default=1000.0, description="Maximum drawdown limit"
    )
    evaluation_period: Optional[int] = Field(
        default=100, description="Number of trades per evaluation set"
    )


class TradeExecutionRequest(BaseModel):
    strategy_name: str = Field(..., description="Strategy that generated the trade")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Buy or sell")
    quantity: int = Field(..., description="Quantity traded")
    pnl: float = Field(..., description="Realized P&L from trade")
    entry_price: Optional[float] = Field(None, description="Entry price")
    exit_price: Optional[float] = Field(None, description="Exit price")
    commission: float = Field(default=0.0, description="Commission paid")
    fees: float = Field(default=0.0, description="Other fees")
    trading_mode: TradingMode = Field(
        default=TradingMode.PAPER, description="Trading mode used"
    )
    account_id: Optional[str] = Field(None, description="Account ID used")
    broker: Optional[str] = Field(None, description="Broker used")
    notes: Optional[str] = Field(None, description="Additional notes")


class StrategyModeChangeRequest(BaseModel):
    strategy_name: str = Field(..., description="Strategy to change mode for")
    new_mode: TradingMode = Field(..., description="New trading mode")
    reason: str = Field(..., description="Reason for mode change")


class StrategyStatusResponse(BaseModel):
    strategy_name: str
    current_status: StrategyStatus
    current_mode: TradingMode
    total_trades: int
    win_rate: float
    total_pnl: float
    current_drawdown: float
    last_updated: datetime


class PerformanceMetricsResponse(BaseModel):
    strategy_name: str
    metrics: Dict[str, PerformanceMetric]
    last_calculated: datetime


class TradeHistoryResponse(BaseModel):
    trades: List[TradeRecord]
    total_count: int
    page: int
    page_size: int


class SystemStatusResponse(BaseModel):
    total_strategies: int
    active_strategies: int
    disabled_strategies: int
    total_trades: int
    total_pnl: float
    avg_pnl_per_strategy: float
    last_monitoring_check: datetime
    monitoring_enabled: bool


# Dependency to get strategy tracker
async def get_strategy_tracker() -> StrategyPerformanceTracker:
    """Get the global strategy performance tracker instance"""
    from ..trading.strategy_tracker import StrategyPerformanceTracker

    tracker = StrategyPerformanceTracker()
    if not tracker._initialized:
        await tracker.initialize()
    return tracker


# API Endpoints


@router.post("/strategies/register", response_model=StrategyStatusResponse)
async def register_strategy(
    request: StrategyRegistrationRequest,
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Register a new strategy for performance tracking.

    Creates a new strategy with specified configuration and begins tracking
    its performance metrics and auto-rotation rules.
    """
    try:
        # Create configuration
        config = StrategyConfiguration(
            strategy_name=request.strategy_name,
            trading_mode=request.trading_mode,
            auto_rotation_enabled=request.auto_rotation_enabled,
            min_win_rate=request.min_win_rate,
            max_drawdown=request.max_drawdown,
            evaluation_period=request.evaluation_period,
        )

        # Register strategy
        performance = await tracker.register_strategy(
            strategy_name=request.strategy_name, configuration=config
        )

        logger.info(f"Registered new strategy: {request.strategy_name}")

        return StrategyStatusResponse(
            strategy_name=performance.strategy_name,
            current_status=performance.current_status,
            current_mode=performance.trading_mode,
            total_trades=performance.total_trades,
            win_rate=performance.win_rate,
            total_pnl=float(performance.total_pnl),
            current_drawdown=float(performance.current_drawdown),
            last_updated=performance.last_updated,
        )

    except Exception as e:
        logger.error(f"Failed to register strategy {request.strategy_name}: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to register strategy: {str(e)}"
        )


@router.post("/trades/record", response_model=Dict[str, Any])
async def record_trade_execution(
    request: TradeExecutionRequest,
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Record a completed trade execution for strategy performance tracking.

    This endpoint should be called after each trade execution to update
    strategy performance metrics and trigger auto-rotation logic if needed.
    """
    try:
        trade_id = await tracker.record_trade_execution(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            pnl=request.pnl,
            entry_price=request.entry_price,
            exit_price=request.exit_price,
            commission=request.commission,
            fees=request.fees,
            trading_mode=request.trading_mode,
            account_id=request.account_id,
            broker=request.broker,
            notes=request.notes,
        )

        # Get updated performance
        performance = await tracker.get_strategy_performance(request.strategy_name)

        logger.info(
            f"Recorded trade for {request.strategy_name}: {request.symbol} {request.side} {request.quantity} P&L=${request.pnl}"
        )

        return {
            "trade_id": trade_id,
            "strategy_name": request.strategy_name,
            "status": performance.current_status.value if performance else "unknown",
            "win_rate": performance.win_rate if performance else 0,
            "total_trades": performance.total_trades if performance else 0,
            "mode_changed": (
                performance.current_status == StrategyStatus.AUTO_DISABLED
                if performance
                else False
            ),
        }

    except Exception as e:
        logger.error(f"Failed to record trade for {request.strategy_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to record trade: {str(e)}")


@router.get("/strategies", response_model=List[StrategyStatusResponse])
async def get_all_strategies(
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Get performance status for all registered strategies.

    Returns current status, metrics, and trading mode for all strategies
    being tracked by the system.
    """
    try:
        strategies = await tracker.get_all_strategies()

        return [
            StrategyStatusResponse(
                strategy_name=name,
                current_status=performance.current_status,
                current_mode=performance.trading_mode,
                total_trades=performance.total_trades,
                win_rate=performance.win_rate,
                total_pnl=float(performance.total_pnl),
                current_drawdown=float(performance.current_drawdown),
                last_updated=performance.last_updated,
            )
            for name, performance in strategies.items()
        ]

    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get strategies: {str(e)}"
        )


@router.get("/strategies/{strategy_name}", response_model=StrategyStatusResponse)
async def get_strategy_performance(
    strategy_name: str,
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Get detailed performance information for a specific strategy.
    """
    try:
        performance = await tracker.get_strategy_performance(strategy_name)

        if not performance:
            raise HTTPException(
                status_code=404, detail=f"Strategy '{strategy_name}' not found"
            )

        return StrategyStatusResponse(
            strategy_name=performance.strategy_name,
            current_status=performance.current_status,
            current_mode=performance.trading_mode,
            total_trades=performance.total_trades,
            win_rate=performance.win_rate,
            total_pnl=float(performance.total_pnl),
            current_drawdown=float(performance.current_drawdown),
            last_updated=performance.last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy: {str(e)}")


@router.get(
    "/strategies/{strategy_name}/metrics", response_model=PerformanceMetricsResponse
)
async def get_strategy_metrics(
    strategy_name: str,
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Get detailed performance metrics for a specific strategy.
    """
    try:
        metrics = await tracker.get_strategy_metrics(strategy_name)

        if metrics is None:
            raise HTTPException(
                status_code=404, detail=f"Strategy '{strategy_name}' not found"
            )

        return PerformanceMetricsResponse(
            strategy_name=strategy_name,
            metrics=metrics,
            last_calculated=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/trades", response_model=TradeHistoryResponse)
async def get_trade_history(
    strategy_name: Optional[str] = Query(None, description="Filter by strategy name"),
    limit: int = Query(100, description="Maximum number of trades to return"),
    offset: int = Query(0, description="Number of trades to skip"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Get trade history with optional filtering.
    """
    try:
        trades = await tracker.get_trade_history(
            strategy_name=strategy_name,
            limit=limit + offset,  # Get extra for pagination
            start_date=start_date,
            end_date=end_date,
        )

        # Apply pagination
        paginated_trades = trades[offset : offset + limit]

        return TradeHistoryResponse(
            trades=paginated_trades,
            total_count=len(trades),
            page=offset // limit + 1,
            page_size=limit,
        )

    except Exception as e:
        logger.error(f"Failed to get trade history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get trade history: {str(e)}"
        )


@router.post("/strategies/{strategy_name}/mode", response_model=Dict[str, Any])
async def change_strategy_mode(
    strategy_name: str,
    request: StrategyModeChangeRequest,
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Manually change the trading mode for a strategy.
    """
    try:
        if request.new_mode == TradingMode.LIVE:
            success = await tracker.enable_strategy(strategy_name)
        else:
            success = await tracker.disable_strategy(strategy_name, request.reason)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to change mode for strategy '{strategy_name}'",
            )

        performance = await tracker.get_strategy_performance(strategy_name)

        logger.info(
            f"Changed mode for {strategy_name} to {request.new_mode.value}: {request.reason}"
        )

        return {
            "strategy_name": strategy_name,
            "old_mode": "unknown",  # Would need to track this
            "new_mode": request.new_mode.value,
            "reason": request.reason,
            "current_status": (
                performance.current_status.value if performance else "unknown"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change mode for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change mode: {str(e)}")


@router.get("/portfolio", response_model=Dict[str, Any])
async def get_portfolio_summary(
    portfolio_name: str = Query("default", description="Portfolio name"),
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Get portfolio-level performance summary.
    """
    try:
        summary = await tracker.get_portfolio_summary(portfolio_name)

        if not summary:
            raise HTTPException(
                status_code=404, detail=f"Portfolio '{portfolio_name}' not found"
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get portfolio summary: {str(e)}"
        )


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Get overall system status and summary statistics.
    """
    try:
        stats = tracker.get_summary_stats()

        return SystemStatusResponse(
            total_strategies=stats["total_strategies"],
            active_strategies=stats["active_strategies"],
            disabled_strategies=stats["disabled_strategies"],
            total_trades=stats["total_trades"],
            total_pnl=stats["total_pnl"],
            avg_pnl_per_strategy=stats["avg_pnl_per_strategy"],
            last_monitoring_check=datetime.fromisoformat(
                stats["last_monitoring_check"]
            ),
            monitoring_enabled=stats["monitoring_enabled"],
        )

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get system status: {str(e)}"
        )


@router.post("/system/rotation-check", response_model=List[Dict[str, Any]])
async def trigger_rotation_check(
    portfolio_name: str = Query("default", description="Portfolio name"),
    tracker: StrategyPerformanceTracker = Depends(get_strategy_tracker),
):
    """
    Manually trigger a rotation rules check for a portfolio.
    """
    try:
        actions = await tracker.check_rotation_rules(portfolio_name)

        # Execute the actions
        for action in actions:
            if action["action"] == "disable":
                await tracker.disable_strategy(
                    action["strategy_name"], f"Auto-rotation: {action['rule_name']}"
                )
            # Add other action types as needed

        logger.info(
            f"Executed {len(actions)} rotation actions for portfolio {portfolio_name}"
        )

        return actions

    except Exception as e:
        logger.error(f"Failed to check rotation rules: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check rotation rules: {str(e)}"
        )
