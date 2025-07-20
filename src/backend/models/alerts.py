"""
Alert system models for Kairos/Chronos integration.
Supports conditional alerts and automated execution triggers.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class AlertStatus(str, Enum):
    """Alert status states"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AlertCondition(str, Enum):
    """Alert condition types"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CROSS_ABOVE = "price_cross_above"
    PRICE_CROSS_BELOW = "price_cross_below"
    VOLUME_ABOVE = "volume_above"
    VOLUME_BELOW = "volume_below"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_SIGNAL = "macd_signal"
    BOLLINGER_BREAK = "bollinger_break"
    CUSTOM = "custom"


class Alert(BaseModel):
    """
    Alert definition for Kairos YAML jobs.
    Compatible with TradingView alerts and Chronos execution.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique alert ID")
    symbol: str = Field(..., description="Trading symbol")
    condition: AlertCondition = Field(..., description="Alert condition type")
    condition_value: float = Field(..., description="Trigger value")
    created_at: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Creation timestamp"
    )
    expires_at: Optional[int] = Field(None, description="Expiration timestamp")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Current status")
    
    # Alert configuration
    message: str = Field(..., description="Alert message template")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    
    # Trading execution (optional)
    auto_execute: bool = Field(default=False, description="Auto-execute trade on trigger")
    order_type: Optional[str] = Field(None, description="Order type: market, limit, stop")
    order_side: Optional[str] = Field(None, description="Order side: buy, sell")
    order_quantity: Optional[float] = Field(None, description="Order quantity", gt=0)
    order_price: Optional[float] = Field(None, description="Order price for limit orders", gt=0)
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Alert tags")
    kairos_job_id: Optional[str] = Field(None, description="Associated Kairos job ID")
    
    @validator('expires_at')
    def expires_after_creation(cls, v, values):
        """Validate expiration is after creation"""
        if v is not None and 'created_at' in values and v <= values['created_at']:
            raise ValueError('expires_at must be after created_at')
        return v
    
    @validator('order_quantity')
    def quantity_required_for_auto_execute(cls, v, values):
        """Validate quantity is provided when auto_execute is True"""
        if values.get('auto_execute') and v is None:
            raise ValueError('order_quantity required when auto_execute is True')
        return v
    
    @validator('order_side')
    def side_required_for_auto_execute(cls, v, values):
        """Validate order side is provided when auto_execute is True"""
        if values.get('auto_execute') and v is None:
            raise ValueError('order_side required when auto_execute is True')
        return v
    
    def to_kairos_yaml(self) -> Dict[str, Any]:
        """Convert to Kairos YAML job format"""
        job = {
            "name": f"alert_{self.symbol}_{self.condition}_{self.id[:8]}",
            "screenshot": True,
            "sound": True,
            "log-level": "info",
            "signals": [
                {
                    "name": f"{self.symbol}_signal",
                    "symbol": self.symbol,
                    "condition": self._condition_to_kairos_format(),
                    "webhook": {
                        "url": self.webhook_url or "http://localhost:5000/webhook",
                        "data": {
                            "alert_id": self.id,
                            "symbol": self.symbol,
                            "condition": self.condition,
                            "value": self.condition_value,
                            "message": self.message,
                            "auto_execute": self.auto_execute,
                            "order_type": self.order_type,
                            "order_side": self.order_side,
                            "order_quantity": self.order_quantity,
                            "order_price": self.order_price
                        }
                    }
                }
            ]
        }
        return job
    
    def _condition_to_kairos_format(self) -> str:
        """Convert alert condition to Kairos Pine script format"""
        condition_map = {
            AlertCondition.PRICE_ABOVE: f"close > {self.condition_value}",
            AlertCondition.PRICE_BELOW: f"close < {self.condition_value}",
            AlertCondition.PRICE_CROSS_ABOVE: f"ta.crossover(close, {self.condition_value})",
            AlertCondition.PRICE_CROSS_BELOW: f"ta.crossunder(close, {self.condition_value})",
            AlertCondition.VOLUME_ABOVE: f"volume > {self.condition_value}",
            AlertCondition.VOLUME_BELOW: f"volume < {self.condition_value}",
            AlertCondition.RSI_OVERBOUGHT: f"ta.rsi(close, 14) > {self.condition_value}",
            AlertCondition.RSI_OVERSOLD: f"ta.rsi(close, 14) < {self.condition_value}",
        }
        return condition_map.get(self.condition, f"close > {self.condition_value}")
    
    def check_condition(self, current_price: float, current_volume: float = 0) -> bool:
        """Check if alert condition is met"""
        if self.status != AlertStatus.ACTIVE:
            return False
            
        # Check expiration
        if self.expires_at and int(datetime.now(timezone.utc).timestamp()) > self.expires_at:
            return False
        
        # Check condition
        if self.condition == AlertCondition.PRICE_ABOVE:
            return current_price > self.condition_value
        elif self.condition == AlertCondition.PRICE_BELOW:
            return current_price < self.condition_value
        elif self.condition == AlertCondition.VOLUME_ABOVE:
            return current_volume > self.condition_value
        elif self.condition == AlertCondition.VOLUME_BELOW:
            return current_volume < self.condition_value
        
        return False
    
    def trigger(self) -> None:
        """Mark alert as triggered"""
        self.status = AlertStatus.TRIGGERED
    
    def cancel(self) -> None:
        """Cancel the alert"""
        self.status = AlertStatus.CANCELLED


class AlertEvent(BaseModel):
    """Alert trigger event for Chronos"""
    alert_id: str = Field(..., description="Alert ID that triggered")
    symbol: str = Field(..., description="Trading symbol")
    trigger_time: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp()),
        description="Trigger timestamp"
    )
    trigger_price: float = Field(..., description="Price at trigger", gt=0)
    trigger_volume: Optional[float] = Field(None, description="Volume at trigger", ge=0)
    condition: AlertCondition = Field(..., description="Condition that triggered")
    condition_value: float = Field(..., description="Condition threshold value")
    message: str = Field(..., description="Alert message")
    
    # Execution details (if auto-execute)
    auto_execute: bool = Field(default=False, description="Should auto-execute")
    order_type: Optional[str] = Field(None, description="Order type")
    order_side: Optional[str] = Field(None, description="Order side")
    order_quantity: Optional[float] = Field(None, description="Order quantity")
    order_price: Optional[float] = Field(None, description="Order price")
    
    def to_chronos_payload(self) -> Dict[str, Any]:
        """Convert to Chronos webhook payload format"""
        return {
            "type": "alert_triggered",
            "alert_id": self.alert_id,
            "symbol": self.symbol,
            "timestamp": self.trigger_time,
            "price": self.trigger_price,
            "volume": self.trigger_volume,
            "condition": self.condition,
            "condition_value": self.condition_value,
            "message": self.message,
            "execution": {
                "auto_execute": self.auto_execute,
                "order_type": self.order_type,
                "order_side": self.order_side,
                "order_quantity": self.order_quantity,
                "order_price": self.order_price
            } if self.auto_execute else None
        }