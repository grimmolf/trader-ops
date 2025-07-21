"""
Webhook Processor

Main webhook processing logic that routes TradingView alerts to
appropriate trading engines and execution systems.

This module integrates with the paper trading router and live
broker connections to execute trades based on webhook alerts.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .models import TradingViewAlert
from ..trading.paper_router import get_paper_trading_router

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Main webhook processor that routes alerts to trading systems.
    
    Handles routing logic to determine whether alerts should go to:
    - Paper trading simulation
    - Live broker execution (Tradovate, Tastytrade, etc.)
    - Funded account validation (TopstepX)
    """
    
    def __init__(self):
        self.paper_router = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize webhook processor"""
        if self._initialized:
            return
        
        # Initialize paper trading router
        self.paper_router = get_paper_trading_router()
        await self.paper_router.initialize()
        
        self._initialized = True
        logger.info("Webhook processor initialized")
    
    async def process_alert(self, alert: TradingViewAlert) -> Dict[str, Any]:
        """
        Process a TradingView alert and route to appropriate execution system.
        
        Args:
            alert: Validated TradingView alert
            
        Returns:
            Dict[str, Any]: Processing result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Processing alert: {alert.symbol} {alert.action} {alert.quantity}")
            
            # Determine routing based on account_group
            account_group = getattr(alert, 'account_group', 'paper_simulator')
            
            if account_group.startswith('paper_'):
                # Route to paper trading
                result = await self.paper_router.route_alert(alert)
                result["routing"] = "paper_trading"
                return result
            
            elif account_group.startswith('topstep'):
                # Route to TopstepX validation + Tradovate execution
                # This would integrate TopstepX validation with Tradovate execution
                logger.info(f"TopstepX routing not fully implemented for: {account_group}")
                
                # For now, route to paper trading as fallback
                result = await self.paper_router.route_alert(alert)
                result["routing"] = "paper_trading_fallback"
                result["note"] = "TopstepX validation integration pending"
                return result
            
            else:
                # Route to live trading (Tradovate, Tastytrade, etc.)
                logger.info(f"Live trading routing not fully implemented for: {account_group}")
                
                # For now, route to paper trading as fallback
                result = await self.paper_router.route_alert(alert)
                result["routing"] = "paper_trading_fallback"
                result["note"] = "Live trading integration pending"
                return result
        
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            return {
                "status": "error",
                "message": str(e),
                "alert": alert.dict() if hasattr(alert, 'dict') else str(alert)
            }
    
    async def close(self):
        """Close webhook processor"""
        self._initialized = False
        logger.info("Webhook processor closed")


# Global processor instance
_processor: Optional[WebhookProcessor] = None


def get_webhook_processor() -> WebhookProcessor:
    """Get the global webhook processor instance"""
    global _processor
    if _processor is None:
        _processor = WebhookProcessor()
    return _processor