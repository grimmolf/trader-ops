"""
Strategy Performance Management API Routes for TraderTerminal

Provides REST endpoints for strategy performance tracking and auto-rotation:
- Strategy registration (/api/strategies/register)
- Strategy management (/api/strategies/{strategy_id}/*)
- Performance monitoring (/api/strategies/summaries, /api/strategies/status)
- Alert management (/api/strategies/alerts)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, ValidationError

from .models import (
    StrategyPerformance, StrategyPerformanceSummary, StrategyRegistration,
    StrategyModeChangeRequest, ModeTransition, TradingMode
)
from .performance_tracker import get_strategy_tracker, initialize_strategy_tracker

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/strategies", tags=["strategy-performance"])

# Request/Response models
class StrategyRegistrationResponse(BaseModel):
    strategy: StrategyPerformance
    message: str

class ModeChangeResponse(BaseModel):
    transition: Optional[ModeTransition]
    message: str

class SystemStatusResponse(BaseModel):
    status: Dict[str, Any]
    timestamp: str

class PerformanceAlertsResponse(BaseModel):
    alerts: List[Dict[str, Any]]
    count: int

# Strategy Performance API Routes

@router.get("/summaries")
async def get_all_strategy_summaries() -> List[Dict[str, Any]]:
    """Get performance summaries for all registered strategies"""
    try:
        strategy_tracker = get_strategy_tracker()
        summaries = await strategy_tracker.get_all_strategy_summaries()
        
        return [summary.dict() for summary in summaries]
        
    except Exception as e:
        logger.error(f"Failed to get strategy summaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}")
async def get_strategy_details(strategy_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific strategy"""
    try:
        strategy_tracker = get_strategy_tracker()
        strategy = await strategy_tracker.get_strategy(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return strategy.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}/summary")
async def get_strategy_summary(strategy_id: str) -> Dict[str, Any]:
    """Get performance summary for a specific strategy"""
    try:
        strategy_tracker = get_strategy_tracker()
        summary = await strategy_tracker.get_strategy_summary(strategy_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return summary.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy summary {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
async def register_strategy(registration: StrategyRegistration) -> StrategyRegistrationResponse:
    """Register a new strategy for performance tracking"""
    try:
        strategy_tracker = get_strategy_tracker()
        
        # Check if strategy already exists
        existing_strategy = await strategy_tracker.get_strategy(registration.strategy_id)
        if existing_strategy:
            raise HTTPException(
                status_code=409, 
                detail=f"Strategy with ID '{registration.strategy_id}' already exists"
            )
        
        # Register the strategy
        strategy = await strategy_tracker.register_strategy(
            strategy_id=registration.strategy_id,
            strategy_name=registration.strategy_name,
            min_win_rate=registration.min_win_rate,
            evaluation_period=registration.evaluation_period,
            initial_mode=registration.initial_mode
        )
        
        logger.info(f"Strategy '{registration.strategy_name}' registered successfully")
        
        return StrategyRegistrationResponse(
            strategy=strategy,
            message=f"Strategy '{registration.strategy_name}' registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{strategy_id}/mode")
async def change_strategy_mode(
    strategy_id: str, 
    request: StrategyModeChangeRequest
) -> ModeChangeResponse:
    """Manually change strategy trading mode"""
    try:
        strategy_tracker = get_strategy_tracker()
        
        # Check if strategy exists
        strategy = await strategy_tracker.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Validate mode change
        if strategy.current_mode == request.new_mode:
            return ModeChangeResponse(
                transition=None,
                message=f"Strategy is already in {request.new_mode} mode"
            )
        
        # Change mode
        transition = await strategy_tracker.manually_change_mode(
            strategy_id=strategy_id,
            new_mode=request.new_mode,
            reason=request.reason
        )
        
        logger.info(
            f"Strategy '{strategy.strategy_name}' mode changed from "
            f"{strategy.current_mode} to {request.new_mode}"
        )
        
        return ModeChangeResponse(
            transition=transition,
            message=f"Strategy mode changed to {request.new_mode} successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change strategy mode for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_system_status() -> SystemStatusResponse:
    """Get system status and statistics"""
    try:
        strategy_tracker = get_strategy_tracker()
        status = await strategy_tracker.get_system_status()
        
        return SystemStatusResponse(
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_performance_alerts(limit: int = 50) -> PerformanceAlertsResponse:
    """Get recent performance alerts"""
    try:
        strategy_tracker = get_strategy_tracker()
        alerts = await strategy_tracker.get_performance_alerts(limit=limit)
        
        return PerformanceAlertsResponse(
            alerts=alerts,
            count=len(alerts)
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts")
async def clear_performance_alerts() -> Dict[str, str]:
    """Clear all performance alerts"""
    try:
        strategy_tracker = get_strategy_tracker()
        strategy_tracker.clear_performance_alerts()
        
        logger.info("Performance alerts cleared")
        
        return {"message": "Performance alerts cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear performance alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Advanced endpoints for detailed analysis

@router.get("/{strategy_id}/sets")
async def get_strategy_sets(strategy_id: str) -> Dict[str, Any]:
    """Get all completed sets for a strategy"""
    try:
        strategy_tracker = get_strategy_tracker()
        strategy = await strategy_tracker.get_strategy(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.strategy_name,
            "current_set": strategy.current_set.dict(),
            "completed_sets": [s.dict() for s in strategy.completed_sets],
            "total_sets": len(strategy.completed_sets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy sets for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}/transitions")
async def get_strategy_transitions(strategy_id: str) -> Dict[str, Any]:
    """Get mode transition history for a strategy"""
    try:
        strategy_tracker = get_strategy_tracker()
        strategy = await strategy_tracker.get_strategy(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.strategy_name,
            "current_mode": strategy.current_mode,
            "transitions": [t.dict() for t in strategy.mode_transition_history],
            "total_transitions": len(strategy.mode_transition_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy transitions for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{strategy_id}/simulate-trade")
async def simulate_trade_result(
    strategy_id: str,
    trade_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Simulate adding a trade result for testing purposes"""
    try:
        strategy_tracker = get_strategy_tracker()
        strategy = await strategy_tracker.get_strategy(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Extract trade data
        symbol = trade_data.get("symbol", "TEST")
        entry_price = float(trade_data.get("entry_price", 100.0))
        exit_price = float(trade_data.get("exit_price", 101.0))
        quantity = int(trade_data.get("quantity", 1))
        side = trade_data.get("side", "long")
        commission = float(trade_data.get("commission", 2.5))
        
        # Record the simulated trade
        mode_transition = await strategy_tracker.record_trade(
            strategy_id=strategy_id,
            symbol=symbol,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            side=side,
            commission=commission,
            trade_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        result = {
            "message": "Trade simulated successfully",
            "trade": {
                "symbol": symbol,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": quantity,
                "side": side,
                "pnl": (exit_price - entry_price) * quantity if side == "long" else (entry_price - exit_price) * quantity,
                "commission": commission
            }
        }
        
        if mode_transition:
            result["mode_transition"] = mode_transition.dict()
            result["message"] += f" - Mode changed to {mode_transition.to_mode}"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to simulate trade for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for strategy performance system"""
    try:
        strategy_tracker = get_strategy_tracker()
        status = await strategy_tracker.get_system_status()
        
        if status["initialized"]:
            return {"status": "healthy", "message": "Strategy performance system operational"}
        else:
            return {"status": "initializing", "message": "Strategy performance system starting up"}
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "message": str(e)}

# Initialize strategy tracker on startup
async def initialize_strategy_performance_api():
    """Initialize the strategy performance tracker"""
    try:
        await initialize_strategy_tracker()
        logger.info("Strategy performance API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize strategy performance API: {e}")
        raise