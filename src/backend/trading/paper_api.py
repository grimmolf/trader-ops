"""
Paper Trading API Routes for TraderTerminal

Provides REST endpoints for paper trading functionality:
- Account management (/api/paper-trading/accounts/*)
- Order submission (/api/paper-trading/alerts)
- Position management (/api/paper-trading/accounts/{id}/*)
- Performance metrics (/api/paper-trading/accounts/{id}/metrics)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, ValidationError

from .paper_models import (
    PaperTradingAccount, PaperOrder, Fill, PaperTradingAlert, 
    PaperTradingMetrics, OrderAction, OrderType
)
from .paper_router import get_paper_trading_router

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/paper-trading", tags=["paper-trading"])

# Request/Response models
class PaperOrderRequest(BaseModel):
    symbol: str
    action: str
    quantity: float
    orderType: str = "market"
    price: Optional[float] = None
    stopPrice: Optional[float] = None
    strategy: Optional[str] = None
    comment: Optional[str] = None

class AccountResetRequest(BaseModel):
    confirm: bool = False

class TestAlertRequest(BaseModel):
    symbol: str
    action: str
    quantity: float
    orderType: str = "market"
    price: Optional[float] = None
    stopPrice: Optional[float] = None
    accountGroup: str = "paper_simulator"
    strategy: Optional[str] = None
    comment: Optional[str] = None

# Paper trading routes
@router.get("/accounts")
async def get_paper_trading_accounts() -> List[Dict[str, Any]]:
    """Get all paper trading accounts"""
    try:
        paper_router = get_paper_trading_router()
        accounts = await paper_router.get_all_accounts()
        
        return [account.dict() for account in accounts]
        
    except Exception as e:
        logger.error(f"Failed to get paper trading accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}")
async def get_paper_trading_account(account_id: str) -> Dict[str, Any]:
    """Get specific paper trading account"""
    try:
        paper_router = get_paper_trading_router()
        account = await paper_router.get_account(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return account.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get paper trading account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accounts/{account_id}/reset")
async def reset_paper_trading_account(
    account_id: str, 
    request: AccountResetRequest
) -> Dict[str, Any]:
    """Reset paper trading account to initial state"""
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400, 
                detail="Account reset requires confirmation"
            )
        
        paper_router = get_paper_trading_router()
        account = await paper_router.get_account(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Reset account to initial state
        account.current_balance = account.initial_balance
        account.day_pnl = 0
        account.total_pnl = 0
        account.buying_power = account.initial_balance
        account.positions = {}
        account.last_updated = datetime.now(timezone.utc)
        
        # Clear orders and fills
        paper_router.active_orders = {
            order_id: order for order_id, order in paper_router.active_orders.items()
            if order.account_id != account_id
        }
        paper_router.fills = [
            fill for fill in paper_router.fills
            if fill.account_id != account_id
        ]
        
        logger.info(f"Reset paper trading account: {account_id}")
        
        return {
            "status": "success",
            "message": f"Account {account_id} has been reset to initial state",
            "account": account.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset paper trading account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}/orders")
async def get_paper_trading_orders(
    account_id: str, 
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get orders for paper trading account"""
    try:
        paper_router = get_paper_trading_router()
        orders = await paper_router.get_account_orders(account_id, limit)
        
        return [order.dict() for order in orders]
        
    except Exception as e:
        logger.error(f"Failed to get orders for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}/fills")
async def get_paper_trading_fills(
    account_id: str, 
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get fills for paper trading account"""
    try:
        paper_router = get_paper_trading_router()
        fills = await paper_router.get_account_fills(account_id, limit)
        
        return [fill.dict() for fill in fills]
        
    except Exception as e:
        logger.error(f"Failed to get fills for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}/metrics")
async def get_paper_trading_metrics(account_id: str) -> Dict[str, Any]:
    """Get performance metrics for paper trading account"""
    try:
        paper_router = get_paper_trading_router()
        account = await paper_router.get_account(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get orders and fills for this account
        orders = await paper_router.get_account_orders(account_id, 1000)
        fills = await paper_router.get_account_fills(account_id, 1000)
        
        # Calculate metrics
        filled_orders = [order for order in orders if order.status == "filled"]
        
        if not filled_orders:
            # Return empty metrics if no trades
            return PaperTradingMetrics(
                account_id=account_id,
                period_start=account.created_at,
                period_end=datetime.now(timezone.utc)
            ).dict()
        
        # Calculate trading statistics
        total_trades = len(filled_orders)
        winning_trades = 0
        losing_trades = 0
        total_pnl = account.total_pnl
        gross_profit = 0
        gross_loss = 0
        trade_pnls = []
        total_commissions = sum(fill.commission + fill.fees for fill in fills)
        total_volume = sum(fill.quantity for fill in fills)
        
        # Calculate P&L per trade (simplified - would need position tracking for accuracy)
        for fill in fills:
            # This is a simplified calculation - in reality would need to track
            # opening/closing of positions properly
            if fill.side == "sell":
                # Assuming profit on sell (simplified)
                pnl = float(fill.price * fill.quantity - fill.commission - fill.fees)
                trade_pnls.append(pnl)
                if pnl > 0:
                    winning_trades += 1
                    gross_profit += pnl
                else:
                    losing_trades += 1
                    gross_loss += abs(pnl)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Calculate max drawdown (simplified)
        max_drawdown = 0
        running_pnl = 0
        peak = 0
        for pnl in trade_pnls:
            running_pnl += pnl
            if running_pnl > peak:
                peak = running_pnl
            drawdown = peak - running_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        largest_win = max(trade_pnls) if trade_pnls else 0
        largest_loss = min(trade_pnls) if trade_pnls else 0
        
        metrics = PaperTradingMetrics(
            account_id=account_id,
            period_start=account.created_at,
            period_end=datetime.now(timezone.utc),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            total_commissions=total_commissions,
            total_volume=total_volume
        )
        
        return metrics.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accounts/{account_id}/flatten")
async def flatten_paper_trading_positions(account_id: str) -> Dict[str, Any]:
    """Close all positions in paper trading account"""
    try:
        paper_router = get_paper_trading_router()
        result = await paper_router.flatten_account_positions(account_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to flatten positions for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts")
async def submit_paper_trading_alert(alert_request: TestAlertRequest) -> Dict[str, Any]:
    """Submit paper trading alert/order"""
    try:
        # Convert request to PaperTradingAlert
        alert = PaperTradingAlert(
            symbol=alert_request.symbol.upper(),
            action=OrderAction(alert_request.action.lower()),
            quantity=alert_request.quantity,
            order_type=OrderType(alert_request.orderType.lower()),
            price=alert_request.price,
            stop_price=alert_request.stopPrice,
            account_group=alert_request.accountGroup,
            strategy=alert_request.strategy,
            comment=alert_request.comment or "Paper trading order"
        )
        
        # Route alert to paper trading system
        paper_router = get_paper_trading_router()
        result = await paper_router.route_alert(alert)
        
        logger.info(f"Paper trading alert processed: {alert.symbol} {alert.action} {alert.quantity}")
        
        return result
        
    except ValidationError as e:
        logger.error(f"Invalid paper trading alert request: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
    except Exception as e:
        logger.error(f"Failed to process paper trading alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/cancel")
async def cancel_paper_trading_order(order_id: str) -> Dict[str, Any]:
    """Cancel a paper trading order"""
    try:
        paper_router = get_paper_trading_router()
        result = await paper_router.cancel_order(order_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to cancel paper trading order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_paper_trading_status() -> Dict[str, Any]:
    """Get paper trading system status"""
    try:
        paper_router = get_paper_trading_router()
        
        # Get accounts count
        accounts = await paper_router.get_all_accounts()
        total_accounts = len(accounts)
        
        # Get total orders and fills
        total_orders = len(paper_router.active_orders)
        total_fills = len(paper_router.fills)
        
        # Get available execution engines
        available_engines = list(paper_router.execution_engines.keys())
        
        return {
            "status": "active",
            "total_accounts": total_accounts,
            "total_orders": total_orders,
            "total_fills": total_fills,
            "available_engines": available_engines,
            "initialized": paper_router._initialized,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get paper trading status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check for paper trading
@router.get("/health")
async def paper_trading_health() -> Dict[str, Any]:
    """Paper trading health check"""
    try:
        paper_router = get_paper_trading_router()
        
        if not paper_router._initialized:
            return {
                "status": "initializing",
                "message": "Paper trading system is initializing"
            }
        
        # Test basic functionality
        accounts = await paper_router.get_all_accounts()
        
        return {
            "status": "healthy",
            "accounts_available": len(accounts),
            "engines_available": len(paper_router.execution_engines),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Paper trading health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }