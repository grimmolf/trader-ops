"""
TradingView webhook models and data structures.

Defines Pydantic models for validating and processing TradingView webhook alerts.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import uuid


class TradingViewAlert(BaseModel):
    """
    TradingView alert payload model with validation.
    
    This model validates incoming webhook data from TradingView Premium alerts,
    ensuring all required fields are present and valid for execution.
    """
    
    # Core trading fields
    symbol: str = Field(..., description="Trading symbol (e.g., 'ES', 'NQ')")
    action: Literal["buy", "sell", "close"] = Field(..., description="Trading action")
    quantity: int = Field(..., gt=0, description="Number of contracts/shares")
    
    # Optional trading fields
    price: Optional[float] = Field(None, description="Limit price for order")
    stop_price: Optional[float] = Field(None, description="Stop price for stop orders")
    order_type: Optional[Literal["market", "limit", "stop", "stop_limit"]] = Field(
        default="market", description="Order type"
    )
    
    # Strategy and routing
    strategy: Optional[str] = Field(None, description="Strategy name that generated alert")
    account_group: Optional[str] = Field(
        default="main", description="Account group for routing (e.g., 'topstep', 'apex')"
    )
    
    # Alert metadata
    alert_name: Optional[str] = Field(None, description="TradingView alert name")
    comment: Optional[str] = Field(None, description="Additional comment/notes")
    message: Optional[str] = Field(None, description="Full alert message")
    
    # Timing
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Alert timestamp"
    )
    
    # Risk management
    max_position_size: Optional[int] = Field(None, description="Maximum position size override")
    risk_percent: Optional[float] = Field(None, description="Risk percentage of account")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate and normalize symbol"""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()
    
    @validator('account_group')
    def validate_account_group(cls, v):
        """Validate account group"""
        if v:
            return v.strip().lower()
        return "main"
    
    def to_execution_request(self) -> Dict[str, Any]:
        """Convert alert to execution request format"""
        return {
            "symbol": self.symbol,
            "action": self.action,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "price": self.price,
            "stop_price": self.stop_price,
            "account_group": self.account_group,
            "strategy": self.strategy,
            "alert_id": str(uuid.uuid4()),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class WebhookResponse(BaseModel):
    """Standard webhook response format"""
    
    status: Literal["received", "rejected", "error"] = Field(..., description="Processing status")
    alert_id: str = Field(..., description="Unique alert identifier")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error details if status is error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class AlertProcessingResult(BaseModel):
    """Result of alert processing pipeline"""
    
    alert_id: str
    status: Literal["processed", "rejected", "failed"]
    execution_result: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None
    broker_order_id: Optional[str] = None