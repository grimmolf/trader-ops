"""
TradingView webhook receiver with enhanced security and processing.

Receives TradingView Premium webhook alerts with HMAC verification,
validates payloads, and routes to appropriate execution systems.
"""

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from .models import TradingViewAlert, WebhookResponse, AlertProcessingResult
from .security import (
    verify_webhook_signature, 
    generate_alert_id,
    webhook_rate_limiter,
    validate_webhook_headers
)

logger = logging.getLogger(__name__)

# Global instances - will be set by server initialization
_settings = None
_tradovate_manager = None
_connection_manager = None


def set_global_instances(settings, tradovate_manager, connection_manager):
    """Set global instances from server startup"""
    global _settings, _tradovate_manager, _connection_manager
    _settings = settings
    _tradovate_manager = tradovate_manager
    _connection_manager = connection_manager

# Router for webhook endpoints
router = APIRouter(prefix="/webhook", tags=["webhooks"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers from proxies
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


@router.post("/tradingview")
async def receive_tradingview_alert(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    authorization: Optional[str] = Header(None)
) -> WebhookResponse:
    """
    Receive and validate TradingView webhook alerts.
    
    This endpoint:
    1. Validates request headers and rate limits
    2. Verifies HMAC signature if webhook secret is configured
    3. Parses and validates alert payload
    4. Queues alert for background processing
    5. Returns immediate response to TradingView
    
    Headers:
        X-Webhook-Signature: HMAC-SHA256 signature of request body
        Authorization: Optional Bearer token for additional auth
        Content-Type: application/json
    """
    start_time = time.time()
    client_ip = get_client_ip(request)
    alert_id = generate_alert_id()
    
    logger.info(f"Webhook received from IP {client_ip}, alert_id: {alert_id}")
    
    try:
        # Step 1: Rate limiting
        if not webhook_rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please reduce webhook frequency."
            )
        
        # Step 2: Validate headers
        headers_valid, header_error = validate_webhook_headers(dict(request.headers))
        if not headers_valid:
            logger.warning(f"Invalid headers from {client_ip}: {header_error}")
            raise HTTPException(status_code=400, detail=header_error)
        
        # Step 3: Get raw body for signature verification
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")
        
        # Step 4: Verify signature if secret is configured
        webhook_secret = _get_webhook_secret()
        if webhook_secret and x_webhook_signature:
            if not verify_webhook_signature(body, x_webhook_signature, webhook_secret):
                logger.error(f"Invalid webhook signature from {client_ip}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        elif webhook_secret:
            logger.warning(f"Webhook secret configured but no signature provided from {client_ip}")
            raise HTTPException(status_code=401, detail="Webhook signature required")
        
        # Step 5: Parse and validate alert payload
        try:
            alert_data = json.loads(body.decode('utf-8'))
            alert = TradingViewAlert(**alert_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_ip}: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Invalid alert format from {client_ip}: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid alert format: {e}")
        
        # Step 6: Log successful alert receipt
        logger.info(
            f"Valid alert received: {alert.symbol} {alert.action} {alert.quantity} "
            f"(strategy: {alert.strategy}, account: {alert.account_group})"
        )
        
        # Step 7: Queue for background processing
        background_tasks.add_task(
            process_tradingview_alert, 
            alert, 
            alert_id, 
            client_ip
        )
        
        # Step 8: Return immediate response
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Webhook processed in {processing_time:.2f}ms")
        
        return WebhookResponse(
            status="received",
            alert_id=alert_id,
            message=f"Alert queued for processing: {alert.symbol} {alert.action} {alert.quantity}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook from {client_ip}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_tradingview_alert(
    alert: TradingViewAlert, 
    alert_id: str, 
    client_ip: str
) -> AlertProcessingResult:
    """
    Process TradingView alert in background.
    
    This function:
    1. Validates alert against account rules
    2. Routes to appropriate broker connector
    3. Executes trade if conditions are met
    4. Logs execution results
    5. Broadcasts updates to connected clients
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing alert {alert_id}: {alert.symbol} {alert.action} {alert.quantity}")
        
        # Step 1: Determine target broker/account based on account_group
        broker_connector = _get_broker_connector(alert.account_group)
        if not broker_connector:
            error_msg = f"No broker connector configured for account group: {alert.account_group}"
            logger.error(error_msg)
            return AlertProcessingResult(
                alert_id=alert_id,
                status="rejected",
                rejection_reason=error_msg
            )
        
        # Step 2: Validate against funded account rules if applicable
        if _is_funded_account(alert.account_group):
            can_trade, rejection_reason = await _check_funded_account_rules(alert)
            if not can_trade:
                logger.warning(f"Alert {alert_id} rejected: {rejection_reason}")
                return AlertProcessingResult(
                    alert_id=alert_id,
                    status="rejected",
                    rejection_reason=rejection_reason
                )
        
        # Step 3: Convert alert to execution request
        execution_request = alert.to_execution_request()
        
        # Step 4: Execute trade
        execution_result = await broker_connector.execute_alert(execution_request)
        
        # Step 5: Process execution result
        if execution_result.get("status") == "success":
            logger.info(f"Alert {alert_id} executed successfully: {execution_result}")
            
            # Broadcast update to connected clients
            await _broadcast_execution_update(alert, execution_result)
            
            processing_time = (time.time() - start_time) * 1000
            return AlertProcessingResult(
                alert_id=alert_id,
                status="processed",
                execution_result=execution_result,
                processing_time_ms=processing_time,
                broker_order_id=execution_result.get("order", {}).get("id")
            )
        else:
            error_msg = execution_result.get("reason", "Unknown execution error")
            logger.error(f"Alert {alert_id} execution failed: {error_msg}")
            return AlertProcessingResult(
                alert_id=alert_id,
                status="failed",
                error_message=error_msg
            )
            
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error processing alert {alert_id}: {e}")
        return AlertProcessingResult(
            alert_id=alert_id,
            status="failed",
            error_message=str(e),
            processing_time_ms=processing_time
        )


def _get_webhook_secret() -> Optional[str]:
    """Get webhook secret from configuration"""
    if _settings:
        return _settings.tradingview_webhook_secret
    return None


def _get_broker_connector(account_group: str):
    """Get appropriate broker connector for account group"""
    logger.info(f"Broker connector lookup for account group: {account_group}")
    
    # Normalize account group
    group = account_group.lower() if account_group else "main"
    
    # Route to Tradovate for futures and funded accounts
    futures_groups = ["main", "tradovate", "topstep", "apex", "tradeday", "fundedtrader"]
    if group in futures_groups:
        if _tradovate_manager:
            logger.info(f"Routing {account_group} to Tradovate manager")
            return _tradovate_manager
        else:
            logger.warning(f"Tradovate manager not available for {account_group}")
            return None
    
    # TODO: Add routing for other brokers (Schwab for stocks/options)
    logger.warning(f"No broker connector configured for account group: {account_group}")
    return None


def _is_funded_account(account_group: str) -> bool:
    """Check if account group represents a funded trading account"""
    funded_groups = ["topstep", "apex", "tradeday", "fundedtrader"]
    return account_group.lower() in funded_groups


async def _check_funded_account_rules(alert: TradingViewAlert) -> tuple[bool, Optional[str]]:
    """
    Check if alert complies with funded account rules.
    
    Returns:
        tuple: (can_trade, rejection_reason)
    """
    # TODO: Implement funded account rule checking
    # This will connect to TopstepX API when available
    logger.info(f"Checking funded account rules for {alert.account_group}")
    return True, None


async def _broadcast_execution_update(alert: TradingViewAlert, execution_result: dict):
    """Broadcast execution update to connected WebSocket clients"""
    if not _connection_manager:
        logger.warning("Connection manager not available for broadcasting")
        return
    
    try:
        # Create execution update message
        update_message = {
            "type": "execution",
            "data": {
                "symbol": alert.symbol,
                "action": alert.action,
                "quantity": alert.quantity,
                "strategy": alert.strategy,
                "account_group": alert.account_group,
                "execution_result": execution_result,
                "timestamp": time.time()
            }
        }
        
        # Broadcast to all connected clients
        await _connection_manager.broadcast_to_all(update_message)
        logger.info(f"Execution update broadcasted for {alert.symbol} {alert.action}")
        
    except Exception as e:
        logger.error(f"Error broadcasting execution update: {e}")


@router.get("/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook system is working"""
    return {
        "status": "healthy",
        "message": "TradingView webhook endpoint is operational",
        "timestamp": time.time(),
        "rate_limit_status": "operational"
    }