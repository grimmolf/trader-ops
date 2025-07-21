"""
Funded Accounts API

FastAPI endpoints for managing funded trading accounts with real-time
risk monitoring, rule enforcement, and violation tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/funded-accounts", tags=["Funded Accounts"])


# Pydantic models for API
class FundedAccountResponse(BaseModel):
    id: str
    name: str
    provider: str = Field(..., description="TopstepX, Apex, TradeDay, etc.")
    type: str = Field(..., description="evaluation, funded, express, swing")
    status: str = Field(..., description="active, paused, violated, suspended, passed")

    # Balance and P&L
    balance: float
    equity: float
    dailyPnL: float
    totalPnL: float
    maxDrawdown: float
    currentDrawdown: float

    # Risk Limits
    rules: Dict[str, Any]

    # Trading Activity
    todayTrades: int
    positions: List[Dict[str, Any]]

    # Metadata
    createdAt: datetime
    lastUpdated: datetime
    connectionStatus: str


class AccountMetricsResponse(BaseModel):
    accountId: str

    # Risk Metrics
    dailyLossPercent: float
    totalLossPercent: float
    drawdownPercent: float

    # Trading Metrics
    tradeCount: int
    positionUtilization: float
    avgWinRate: float
    profitFactor: float

    # Status
    riskLevel: str = Field(..., description="safe, warning, danger, violation")
    canTrade: bool
    violations: List[Dict[str, Any]]

    lastCalculated: datetime


class ViolationResponse(BaseModel):
    id: str
    accountId: str
    type: str = Field(
        ...,
        description="daily_loss, total_loss, drawdown, position_size, trading_hours, max_trades",
    )
    severity: str = Field(..., description="warning, critical, violation")
    message: str
    value: float
    limit: float
    timestamp: datetime
    acknowledged: bool


class AccountCreateRequest(BaseModel):
    name: str = Field(..., description="Account display name")
    provider: str = Field(..., description="TopstepX, Apex, TradeDay, etc.")
    type: str = Field(..., description="evaluation, funded, express, swing")
    balance: float = Field(..., description="Initial account balance")

    # Risk Rules
    maxDailyLoss: float = Field(..., description="Maximum daily loss allowed")
    maxTotalLoss: float = Field(
        ..., description="Maximum total loss (trailing drawdown)"
    )
    maxDrawdownPercent: float = Field(
        default=10.0, description="Maximum drawdown percentage"
    )
    maxPositionSize: float = Field(..., description="Maximum position size")
    maxDailyTrades: int = Field(default=10, description="Maximum trades per day")


class PositionFlattenRequest(BaseModel):
    accountId: str = Field(..., description="Account to flatten positions for")
    reason: str = Field(default="Manual flatten", description="Reason for flattening")


# Mock data store (in production, this would connect to real providers)
_mock_accounts: Dict[str, Dict[str, Any]] = {}
_mock_metrics: Dict[str, Dict[str, Any]] = {}
_mock_violations: List[Dict[str, Any]] = []


# Helper functions
def _generate_mock_account_data(account_id: str) -> Dict[str, Any]:
    """Generate realistic mock data for a funded account"""
    import random

    # Simulate different account providers and types
    providers = ["topstepx", "apex", "tradeday", "ftmo"]
    types = ["evaluation", "funded", "express"]
    statuses = ["active", "paused"]

    provider = random.choice(providers)
    account_type = random.choice(types)

    base_balance = 50000 if account_type == "evaluation" else 100000
    daily_pnl = random.uniform(-500, 800)
    total_pnl = random.uniform(-2000, 5000)

    return {
        "id": account_id,
        "name": f"{provider.title()} {account_type.title()} Account",
        "provider": provider,
        "type": account_type,
        "status": random.choice(statuses),
        "balance": base_balance + total_pnl,
        "equity": base_balance + total_pnl,
        "dailyPnL": daily_pnl,
        "totalPnL": total_pnl,
        "maxDrawdown": (
            base_balance * 0.08 if account_type == "evaluation" else base_balance * 0.05
        ),
        "currentDrawdown": max(0, -total_pnl),
        "rules": {
            "maxDailyLoss": 2000 if account_type == "evaluation" else 3000,
            "maxTotalLoss": 3000 if account_type == "evaluation" else 5000,
            "maxDrawdownPercent": 8.0 if account_type == "evaluation" else 5.0,
            "maxPositionSize": 10,
            "maxDailyTrades": 15,
            "maxConcurrentPositions": 3,
            "tradingHours": [
                {
                    "startTime": "09:30",
                    "endTime": "16:00",
                    "timezone": "America/New_York",
                    "days": [1, 2, 3, 4, 5],
                }
            ],
            "minimumTradingDays": 5,
            "newsTrading": False,
            "weekendTrading": False,
            "consistencyRule": True,
        },
        "todayTrades": random.randint(0, 8),
        "positions": _generate_mock_positions(),
        "createdAt": datetime.utcnow(),
        "lastUpdated": datetime.utcnow(),
        "connectionStatus": "connected",
    }


def _generate_mock_positions() -> List[Dict[str, Any]]:
    """Generate mock position data"""
    import random

    symbols = ["ES", "NQ", "YM", "RTY", "GC", "CL"]
    positions = []

    # Random number of positions (0-3)
    num_positions = random.randint(0, 3)

    for _ in range(num_positions):
        symbol = random.choice(symbols)
        side = random.choice(["long", "short"])
        quantity = random.randint(1, 5)
        entry_price = (
            random.uniform(4000, 5000)
            if symbol == "ES"
            else random.uniform(15000, 17000)
        )
        current_price = entry_price * random.uniform(0.98, 1.02)

        unrealized_pnl = (
            (current_price - entry_price) * quantity * 50
        )  # ES contract size
        if side == "short":
            unrealized_pnl *= -1

        positions.append(
            {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entryPrice": round(entry_price, 2),
                "currentPrice": round(current_price, 2),
                "unrealizedPnL": round(unrealized_pnl, 2),
                "entryTime": datetime.utcnow(),
            }
        )

    return positions


def _generate_mock_metrics(
    account_id: str, account_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate mock metrics for an account"""
    import random

    rules = account_data["rules"]
    daily_loss_percent = (
        abs(min(0, account_data["dailyPnL"])) / rules["maxDailyLoss"] * 100
    )
    total_loss_percent = account_data["currentDrawdown"] / rules["maxTotalLoss"] * 100
    drawdown_percent = account_data["currentDrawdown"] / account_data["balance"] * 100

    win_rate = random.uniform(0.45, 0.75)
    profit_factor = random.uniform(0.8, 2.5)

    # Determine risk level
    max_percent = max(daily_loss_percent, total_loss_percent, drawdown_percent)
    if max_percent >= 100:
        risk_level = "violation"
    elif max_percent >= 80:
        risk_level = "danger"
    elif max_percent >= 60:
        risk_level = "warning"
    else:
        risk_level = "safe"

    return {
        "accountId": account_id,
        "dailyLossPercent": daily_loss_percent,
        "totalLossPercent": total_loss_percent,
        "drawdownPercent": drawdown_percent,
        "tradeCount": account_data["todayTrades"],
        "positionUtilization": len(account_data["positions"])
        / rules["maxConcurrentPositions"]
        * 100,
        "avgWinRate": win_rate,
        "profitFactor": profit_factor,
        "riskLevel": risk_level,
        "canTrade": risk_level != "violation" and account_data["status"] == "active",
        "violations": _generate_mock_violations(account_id, risk_level),
        "lastCalculated": datetime.utcnow(),
    }


def _generate_mock_violations(account_id: str, risk_level: str) -> List[Dict[str, Any]]:
    """Generate mock violations based on risk level"""
    violations = []

    if risk_level in ["danger", "violation"]:
        severity = "critical" if risk_level == "violation" else "warning"
        violations.append(
            {
                "id": f"viol_{account_id}_1",
                "accountId": account_id,
                "type": "daily_loss",
                "severity": severity,
                "message": f"Daily loss approaching limit ({severity} level)",
                "value": 1500.0,
                "limit": 2000.0,
                "timestamp": datetime.utcnow(),
                "acknowledged": False,
            }
        )

    return violations


# Initialize some mock accounts
def _initialize_mock_data():
    """Initialize mock account data"""
    account_ids = ["topstep_001", "apex_001", "tradeday_001"]

    for account_id in account_ids:
        account_data = _generate_mock_account_data(account_id)
        _mock_accounts[account_id] = account_data
        _mock_metrics[account_id] = _generate_mock_metrics(account_id, account_data)


# Initialize mock data
_initialize_mock_data()

# API Endpoints


@router.get("/", response_model=List[FundedAccountResponse])
async def get_funded_accounts():
    """
    Get all funded accounts with current status and metrics.

    Returns a list of all funded accounts being monitored,
    including balance, P&L, and risk status.
    """
    try:
        accounts = []

        for account_data in _mock_accounts.values():
            accounts.append(
                FundedAccountResponse(
                    id=account_data["id"],
                    name=account_data["name"],
                    provider=account_data["provider"],
                    type=account_data["type"],
                    status=account_data["status"],
                    balance=account_data["balance"],
                    equity=account_data["equity"],
                    dailyPnL=account_data["dailyPnL"],
                    totalPnL=account_data["totalPnL"],
                    maxDrawdown=account_data["maxDrawdown"],
                    currentDrawdown=account_data["currentDrawdown"],
                    rules=account_data["rules"],
                    todayTrades=account_data["todayTrades"],
                    positions=account_data["positions"],
                    createdAt=account_data["createdAt"],
                    lastUpdated=account_data["lastUpdated"],
                    connectionStatus=account_data["connectionStatus"],
                )
            )

        logger.info(f"Retrieved {len(accounts)} funded accounts")
        return accounts

    except Exception as e:
        logger.error(f"Failed to get funded accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get accounts: {str(e)}")


@router.get("/{account_id}", response_model=FundedAccountResponse)
async def get_funded_account(account_id: str):
    """
    Get detailed information for a specific funded account.
    """
    try:
        if account_id not in _mock_accounts:
            raise HTTPException(
                status_code=404, detail=f"Account '{account_id}' not found"
            )

        account_data = _mock_accounts[account_id]

        return FundedAccountResponse(
            id=account_data["id"],
            name=account_data["name"],
            provider=account_data["provider"],
            type=account_data["type"],
            status=account_data["status"],
            balance=account_data["balance"],
            equity=account_data["equity"],
            dailyPnL=account_data["dailyPnL"],
            totalPnL=account_data["totalPnL"],
            maxDrawdown=account_data["maxDrawdown"],
            currentDrawdown=account_data["currentDrawdown"],
            rules=account_data["rules"],
            todayTrades=account_data["todayTrades"],
            positions=account_data["positions"],
            createdAt=account_data["createdAt"],
            lastUpdated=account_data["lastUpdated"],
            connectionStatus=account_data["connectionStatus"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account: {str(e)}")


@router.get("/{account_id}/metrics", response_model=AccountMetricsResponse)
async def get_account_metrics(account_id: str):
    """
    Get current risk metrics and trading statistics for an account.
    """
    try:
        if account_id not in _mock_accounts:
            raise HTTPException(
                status_code=404, detail=f"Account '{account_id}' not found"
            )

        # Refresh metrics
        account_data = _mock_accounts[account_id]
        metrics_data = _generate_mock_metrics(account_id, account_data)
        _mock_metrics[account_id] = metrics_data

        return AccountMetricsResponse(
            accountId=metrics_data["accountId"],
            dailyLossPercent=metrics_data["dailyLossPercent"],
            totalLossPercent=metrics_data["totalLossPercent"],
            drawdownPercent=metrics_data["drawdownPercent"],
            tradeCount=metrics_data["tradeCount"],
            positionUtilization=metrics_data["positionUtilization"],
            avgWinRate=metrics_data["avgWinRate"],
            profitFactor=metrics_data["profitFactor"],
            riskLevel=metrics_data["riskLevel"],
            canTrade=metrics_data["canTrade"],
            violations=metrics_data["violations"],
            lastCalculated=metrics_data["lastCalculated"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/{account_id}/flatten-positions")
async def flatten_positions(account_id: str, request: PositionFlattenRequest):
    """
    Close all open positions for an account (emergency risk management).
    """
    try:
        if account_id not in _mock_accounts:
            raise HTTPException(
                status_code=404, detail=f"Account '{account_id}' not found"
            )

        account_data = _mock_accounts[account_id]
        positions_count = len(account_data["positions"])

        # Simulate flattening positions
        account_data["positions"] = []
        account_data["lastUpdated"] = datetime.utcnow()

        logger.warning(
            f"Flattened {positions_count} positions for account {account_id}: {request.reason}"
        )

        return {
            "account_id": account_id,
            "positions_closed": positions_count,
            "reason": request.reason,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to flatten positions for account {account_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to flatten positions: {str(e)}"
        )


@router.post("/{account_id}/pause")
async def pause_trading(account_id: str):
    """
    Pause trading for an account.
    """
    try:
        if account_id not in _mock_accounts:
            raise HTTPException(
                status_code=404, detail=f"Account '{account_id}' not found"
            )

        account_data = _mock_accounts[account_id]
        account_data["status"] = "paused"
        account_data["lastUpdated"] = datetime.utcnow()

        logger.info(f"Paused trading for account {account_id}")

        return {
            "account_id": account_id,
            "status": "paused",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause trading for account {account_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to pause trading: {str(e)}"
        )


@router.post("/{account_id}/resume")
async def resume_trading(account_id: str):
    """
    Resume trading for an account.
    """
    try:
        if account_id not in _mock_accounts:
            raise HTTPException(
                status_code=404, detail=f"Account '{account_id}' not found"
            )

        account_data = _mock_accounts[account_id]
        metrics_data = _mock_metrics.get(account_id, {})

        # Check if account can resume trading
        if metrics_data.get("riskLevel") == "violation":
            raise HTTPException(
                status_code=400,
                detail="Cannot resume trading while account has active violations",
            )

        account_data["status"] = "active"
        account_data["lastUpdated"] = datetime.utcnow()

        logger.info(f"Resumed trading for account {account_id}")

        return {
            "account_id": account_id,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume trading for account {account_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to resume trading: {str(e)}"
        )


@router.get("/violations/", response_model=List[ViolationResponse])
async def get_all_violations(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    severity: Optional[str] = Query(
        None, description="Filter by severity: warning, critical, violation"
    ),
    acknowledged: Optional[bool] = Query(
        None, description="Filter by acknowledgment status"
    ),
):
    """
    Get all risk violations across accounts with optional filtering.
    """
    try:
        violations = []

        for metrics_data in _mock_metrics.values():
            for violation in metrics_data.get("violations", []):
                # Apply filters
                if account_id and violation["accountId"] != account_id:
                    continue
                if severity and violation["severity"] != severity:
                    continue
                if (
                    acknowledged is not None
                    and violation["acknowledged"] != acknowledged
                ):
                    continue

                violations.append(
                    ViolationResponse(
                        id=violation["id"],
                        accountId=violation["accountId"],
                        type=violation["type"],
                        severity=violation["severity"],
                        message=violation["message"],
                        value=violation["value"],
                        limit=violation["limit"],
                        timestamp=violation["timestamp"],
                        acknowledged=violation["acknowledged"],
                    )
                )

        return violations

    except Exception as e:
        logger.error(f"Failed to get violations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get violations: {str(e)}"
        )


@router.post("/violations/{violation_id}/acknowledge")
async def acknowledge_violation(violation_id: str):
    """
    Acknowledge a risk violation.
    """
    try:
        # Find and acknowledge the violation
        violation_found = False

        for metrics_data in _mock_metrics.values():
            for violation in metrics_data.get("violations", []):
                if violation["id"] == violation_id:
                    violation["acknowledged"] = True
                    violation_found = True
                    break
            if violation_found:
                break

        if not violation_found:
            raise HTTPException(
                status_code=404, detail=f"Violation '{violation_id}' not found"
            )

        logger.info(f"Acknowledged violation {violation_id}")

        return {
            "violation_id": violation_id,
            "acknowledged": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge violation {violation_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to acknowledge violation: {str(e)}"
        )
