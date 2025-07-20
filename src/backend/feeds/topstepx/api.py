"""
TopstepX API Router

REST API endpoints for TopstepX funded account monitoring and management.
Provides comprehensive endpoints for account status, rule monitoring, and violation tracking.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from .manager import TopstepXManager
from .models import TopstepAccount, AccountStatus, TradingPhase

logger = logging.getLogger(__name__)

# Router for TopstepX API endpoints
router = APIRouter(prefix="/api/topstepx", tags=["topstepx"])

# Global TopstepX manager instance - will be set during server startup
_topstepx_manager: Optional[TopstepXManager] = None


def set_topstepx_manager(manager: TopstepXManager):
    """Set the global TopstepX manager instance"""
    global _topstepx_manager
    _topstepx_manager = manager


def get_topstepx_manager() -> TopstepXManager:
    """Dependency to get TopstepX manager"""
    if not _topstepx_manager:
        raise HTTPException(
            status_code=503, 
            detail="TopstepX manager not available. Check configuration and credentials."
        )
    return _topstepx_manager


# Response models
class TopstepXStatusResponse(BaseModel):
    """TopstepX connection status response"""
    status: str
    initialized: bool
    environment: str
    account_count: int
    active_accounts: int
    monitoring_active: bool
    message: Optional[str] = None


class AccountSummaryResponse(BaseModel):
    """Individual account summary response"""
    account_info: Dict[str, Any]
    current_metrics: Dict[str, Any]
    rules: Dict[str, Any]
    violations: List[Dict[str, Any]]
    timestamp: str


class AllAccountsResponse(BaseModel):
    """All accounts summary response"""
    account_count: int
    active_accounts: int
    total_violations: int
    accounts: List[Dict[str, Any]]
    monitoring_active: bool
    timestamp: str


# API Endpoints

@router.get("/status", response_model=TopstepXStatusResponse)
async def get_topstepx_status(manager: TopstepXManager = Depends(get_topstepx_manager)):
    """
    Get TopstepX connection and manager status.
    
    Returns:
        TopstepXStatusResponse: Current status and configuration
    """
    try:
        status = manager.get_status()
        
        return TopstepXStatusResponse(
            status="operational" if status["initialized"] else "not_initialized",
            initialized=status["initialized"],
            environment=status["environment"],
            account_count=status["account_count"],
            active_accounts=status.get("active_accounts", 0),
            monitoring_active=status["monitoring_active"],
            message="TopstepX integration operational" if status["initialized"] else "TopstepX manager not initialized"
        )
        
    except Exception as e:
        logger.error(f"Error getting TopstepX status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/accounts", response_model=AllAccountsResponse)
async def get_all_accounts(manager: TopstepXManager = Depends(get_topstepx_manager)):
    """
    Get summary of all TopstepX funded accounts.
    
    Returns:
        AllAccountsResponse: Summary of all accounts and their status
    """
    try:
        summary = await manager.get_all_accounts_summary()
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return AllAccountsResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all TopstepX accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get accounts: {str(e)}")


@router.get("/accounts/{account_id}", response_model=AccountSummaryResponse)
async def get_account_summary(
    account_id: str,
    manager: TopstepXManager = Depends(get_topstepx_manager)
):
    """
    Get detailed summary for a specific TopstepX account.
    
    Args:
        account_id: TopstepX account ID
        
    Returns:
        AccountSummaryResponse: Detailed account information
    """
    try:
        summary = await manager.get_account_summary(account_id)
        
        if "error" in summary:
            if "not found" in summary["error"].lower():
                raise HTTPException(status_code=404, detail=summary["error"])
            else:
                raise HTTPException(status_code=500, detail=summary["error"])
        
        return AccountSummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting TopstepX account summary for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account summary: {str(e)}")


@router.get("/accounts/{account_id}/rules")
async def get_account_rules(
    account_id: str,
    manager: TopstepXManager = Depends(get_topstepx_manager)
):
    """
    Get current trading rules and limits for a TopstepX account.
    
    Args:
        account_id: TopstepX account ID
        
    Returns:
        Dict: Account rules, limits, and current metrics
    """
    try:
        summary = await manager.get_account_summary(account_id)
        
        if "error" in summary:
            if "not found" in summary["error"].lower():
                raise HTTPException(status_code=404, detail=summary["error"])
            else:
                raise HTTPException(status_code=500, detail=summary["error"])
        
        return {
            "account_id": account_id,
            "rules": summary["rules"],
            "current_metrics": summary["current_metrics"],
            "violations": summary["violations"],
            "trading_allowed": len(summary["violations"]) == 0,
            "timestamp": summary["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account rules for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account rules: {str(e)}")


@router.get("/accounts/{account_id}/violations")
async def get_account_violations(
    account_id: str,
    manager: TopstepXManager = Depends(get_topstepx_manager)
):
    """
    Get current and historical rule violations for a TopstepX account.
    
    Args:
        account_id: TopstepX account ID
        
    Returns:
        Dict: Current violations and violation history
    """
    try:
        summary = await manager.get_account_summary(account_id)
        
        if "error" in summary:
            if "not found" in summary["error"].lower():
                raise HTTPException(status_code=404, detail=summary["error"])
            else:
                raise HTTPException(status_code=500, detail=summary["error"])
        
        violations = summary["violations"]
        active_violations = [v for v in violations if not v.get("resolved", False)]
        
        return {
            "account_id": account_id,
            "active_violations": active_violations,
            "violation_history": violations,
            "total_violations": len(violations),
            "active_violation_count": len(active_violations),
            "account_suspended": len(active_violations) > 0,
            "timestamp": summary["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violations for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get violations: {str(e)}")


@router.post("/accounts/{account_id}/validate-trade")
async def validate_trade(
    account_id: str,
    symbol: str,
    action: str,
    quantity: int,
    manager: TopstepXManager = Depends(get_topstepx_manager)
):
    """
    Validate if a proposed trade complies with TopstepX account rules.
    
    Args:
        account_id: TopstepX account ID
        symbol: Trading symbol
        action: Trade action (buy/sell)
        quantity: Number of contracts
        
    Returns:
        Dict: Validation result and details
    """
    try:
        # Create mock alert data for validation
        mock_alert = {
            "symbol": symbol.upper(),
            "action": action.lower(),
            "quantity": quantity,
            "account_group": "topstep"  # Will find account by ID
        }
        
        validation_result = await manager.execute_alert(mock_alert)
        
        return {
            "account_id": account_id,
            "trade_details": {
                "symbol": symbol,
                "action": action,
                "quantity": quantity
            },
            "validation_result": validation_result,
            "trade_allowed": validation_result.get("status") == "rules_validated",
            "timestamp": summary.get("timestamp", "")
        }
        
    except Exception as e:
        logger.error(f"Error validating trade for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Trade validation failed: {str(e)}")


@router.post("/initialize")
async def initialize_topstepx(manager: TopstepXManager = Depends(get_topstepx_manager)):
    """
    Initialize or reinitialize TopstepX connection.
    
    Returns:
        Dict: Initialization result
    """
    try:
        result = await manager.initialize()
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": "TopstepX initialized successfully",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Initialization failed: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing TopstepX: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.get("/test-connection")
async def test_topstepx_connection(manager: TopstepXManager = Depends(get_topstepx_manager)):
    """
    Test TopstepX API connection and authentication.
    
    Returns:
        Dict: Connection test result
    """
    try:
        # Test connection through the connector
        result = await manager.connector.test_connection()
        
        return {
            "connection_test": result,
            "manager_status": manager.get_status(),
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        logger.error(f"Error testing TopstepX connection: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.get("/health")
async def topstepx_health_check():
    """
    Health check endpoint for TopstepX integration.
    
    Returns:
        Dict: Health status
    """
    try:
        if not _topstepx_manager:
            return {
                "status": "unavailable",
                "message": "TopstepX manager not configured",
                "healthy": False
            }
        
        status = _topstepx_manager.get_status()
        
        return {
            "status": "healthy" if status["initialized"] else "not_ready",
            "environment": status["environment"],
            "initialized": status["initialized"],
            "account_count": status["account_count"],
            "monitoring_active": status["monitoring_active"],
            "healthy": status["initialized"]
        }
        
    except Exception as e:
        logger.error(f"TopstepX health check error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "healthy": False
        }