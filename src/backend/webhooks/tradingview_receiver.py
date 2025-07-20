"""
TradingView webhook receiver with enhanced security and processing.

Receives TradingView Premium webhook alerts with HMAC verification,
validates payloads, and routes to appropriate execution systems.
"""

import json
import logging
import random
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
from ..strategies.performance_tracker import get_strategy_tracker
from ..strategies.models import TradingMode
from decimal import Decimal

logger = logging.getLogger(__name__)

# Global instances - will be set by server initialization
_settings = None
_tradovate_manager = None
_topstepx_manager = None
_connection_manager = None


def set_global_instances(settings, tradovate_manager, connection_manager, topstepx_manager=None):
    """Set global instances from server startup"""
    global _settings, _tradovate_manager, _topstepx_manager, _connection_manager
    _settings = settings
    _tradovate_manager = tradovate_manager
    _topstepx_manager = topstepx_manager
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
        
        # Step 1: Check strategy performance and override account routing if needed
        original_account_group = alert.account_group
        strategy_override_applied = False
        
        if alert.strategy:
            strategy_tracker = get_strategy_tracker()
            strategy = await strategy_tracker.get_strategy(alert.strategy)
            
            if strategy:
                logger.info(f"Strategy '{alert.strategy}' status: mode={strategy.current_mode}, at_risk={strategy.is_at_risk}")
                
                # If strategy is at risk in live mode, route to paper trading
                if strategy.current_mode == TradingMode.LIVE and strategy.is_at_risk:
                    paper_account_group = f"paper_{original_account_group}"
                    alert.account_group = paper_account_group
                    strategy_override_applied = True
                    
                    logger.warning(
                        f"Strategy '{alert.strategy}' is at risk - routing alert to paper trading "
                        f"(changed from '{original_account_group}' to '{paper_account_group}')"
                    )
                
                # If strategy is in paper mode, ensure it routes to paper
                elif strategy.current_mode == TradingMode.PAPER:
                    if not alert.account_group.startswith("paper_"):
                        paper_account_group = f"paper_{original_account_group}"
                        alert.account_group = paper_account_group
                        strategy_override_applied = True
                        
                        logger.info(
                            f"Strategy '{alert.strategy}' is in paper mode - routing to paper trading "
                            f"(changed from '{original_account_group}' to '{paper_account_group}')"
                        )
                
                # If strategy is suspended, reject the alert
                elif strategy.current_mode == TradingMode.SUSPENDED:
                    error_msg = f"Strategy '{alert.strategy}' is suspended - rejecting alert"
                    logger.warning(error_msg)
                    return AlertProcessingResult(
                        alert_id=alert_id,
                        status="rejected",
                        rejection_reason=error_msg
                    )
            else:
                # Strategy not registered - log warning but continue with original routing
                logger.warning(f"Strategy '{alert.strategy}' not registered in performance tracker")
        
        # Step 2: Determine target broker/account based on (potentially modified) account_group
        broker_connector = _get_broker_connector(alert.account_group)
        if not broker_connector:
            error_msg = f"No broker connector configured for account group: {alert.account_group}"
            logger.error(error_msg)
            return AlertProcessingResult(
                alert_id=alert_id,
                status="rejected",
                rejection_reason=error_msg
            )
        
        # Step 3: Validate against funded account rules if applicable
        if _is_funded_account(alert.account_group):
            can_trade, rejection_reason = await _check_funded_account_rules(alert)
            if not can_trade:
                logger.warning(f"Alert {alert_id} rejected: {rejection_reason}")
                return AlertProcessingResult(
                    alert_id=alert_id,
                    status="rejected",
                    rejection_reason=rejection_reason
                )
        
        # Step 4: Convert alert to execution request
        execution_request = alert.to_execution_request()
        
        # Step 5: Execute trade
        execution_result = await broker_connector.execute_alert(execution_request)
        
        # Step 6: Process execution result
        if execution_result.get("status") == "success":
            logger.info(f"Alert {alert_id} executed successfully: {execution_result}")
            
            # Record trade result for strategy performance tracking
            if alert.strategy:
                await _record_strategy_trade_result(alert, execution_result, strategy_override_applied)
            
            # Report trade execution to TopstepX if this is a funded account
            if _is_funded_account(original_account_group) and _topstepx_manager:
                await _report_trade_to_topstepx(original_account_group, alert, execution_result)
            
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
    
    # Check for paper trading groups first
    if group.startswith("paper_"):
        from ..trading.paper_router import get_paper_trading_router
        logger.info(f"Routing {account_group} to paper trading system")
        return get_paper_trading_router()
    
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
    logger.info(f"Checking funded account rules for {alert.account_group}")
    
    # Check if TopstepX manager is available and this is a TopstepX account
    if _topstepx_manager and alert.account_group.lower() in ["topstep", "topstepx"]:
        try:
            # Use TopstepX manager to validate the alert
            validation_result = await _topstepx_manager.execute_alert(alert)
            
            if validation_result.get("status") == "rules_validated":
                logger.info(f"TopstepX rules validated for {alert.account_group}: {validation_result.get('message')}")
                return True, None
            elif validation_result.get("status") == "rejected":
                reason = validation_result.get("message", "TopstepX rules validation failed")
                logger.warning(f"TopstepX rules rejected alert: {reason}")
                return False, reason
            else:
                # Error or unexpected status
                reason = validation_result.get("message", "TopstepX validation error")
                logger.error(f"TopstepX validation error: {reason}")
                return False, reason
                
        except Exception as e:
            logger.error(f"Error checking TopstepX rules: {e}")
            return False, f"TopstepX rule check failed: {str(e)}"
    
    # For other funded accounts or when TopstepX is not available
    # Implement basic funded account checks
    if alert.account_group.lower() in ["apex", "tradeday", "fundedtrader"]:
        logger.info(f"Using basic funded account rules for {alert.account_group}")
        
        # Basic checks - these would ideally connect to respective provider APIs
        if alert.quantity > 5:  # Example: max 5 contracts
            return False, f"Contract limit exceeded: {alert.quantity} > 5"
        
        # TODO: Implement provider-specific rule checking for Apex, TradeDay, etc.
        logger.warning(f"Basic funded account validation for {alert.account_group} - full rules not implemented")
        return True, None
    
    # Default: allow non-funded accounts
    return True, None


async def _report_trade_to_topstepx(
    account_group: str,
    alert: TradingViewAlert,
    execution_result: Dict[str, Any]
):
    """
    Report completed trade execution to TopstepX for monitoring.
    
    Args:
        account_group: Original account group before any routing changes
        alert: The original TradingView alert
        execution_result: Result from broker execution
    """
    try:
        # Only report for TopstepX accounts
        if account_group.lower() not in ["topstep", "topstepx"]:
            return
        
        # Extract execution details
        fill_data = execution_result.get("fill", {})
        execution_price = fill_data.get("price", 0)
        
        if execution_price <= 0:
            logger.warning("No valid execution price found for TopstepX reporting")
            return
        
        # Report to TopstepX
        success = await _topstepx_manager.report_trade_execution(
            account_group,
            alert.symbol,
            alert.action,
            alert.quantity,
            float(execution_price),
            execution_result
        )
        
        if success:
            logger.info(f"Trade reported to TopstepX: {alert.symbol} {alert.action} {alert.quantity} @ ${execution_price}")
        else:
            logger.warning(f"Failed to report trade to TopstepX: {alert.symbol} {alert.action}")
            
    except Exception as e:
        logger.error(f"Error reporting trade to TopstepX: {e}")


async def _record_strategy_trade_result(
    alert: TradingViewAlert, 
    execution_result: dict, 
    strategy_override_applied: bool
):
    """
    Record completed trade result in strategy performance tracker.
    
    This function extracts trade details from execution result and records them
    for strategy performance monitoring and auto-rotation logic.
    """
    try:
        strategy_tracker = get_strategy_tracker()
        
        # Extract trade details from execution result
        fill_data = execution_result.get("fill", {})
        entry_price = Decimal(str(fill_data.get("price", 0)))
        
        # TODO: This is a simplified implementation for demonstration
        # In production, this would need proper position tracking to match
        # entry/exit trades and calculate actual realized P&L
        
        if entry_price > 0:
            # TODO: Replace with actual exit price from position tracking
            # For now, simulate a basic trade outcome for testing
            price_movement = Decimal(str(random.uniform(-0.01, 0.01))) * entry_price
            exit_price = entry_price + price_movement
            
            # Calculate basic P&L
            side = "long" if alert.action.lower() in ["buy", "long"] else "short"
            commission = Decimal(str(fill_data.get("commission", 2.5)))  # Typical futures commission
            
            logger.info(
                f"Recording trade for strategy '{alert.strategy}': "
                f"{alert.symbol} {side} {alert.quantity} @ {entry_price}->{exit_price}"
                f"{' (OVERRIDE APPLIED)' if strategy_override_applied else ''}"
            )
            
            # Record the trade
            mode_transition = await strategy_tracker.record_trade(
                strategy_id=alert.strategy,
                symbol=alert.symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=alert.quantity,
                side=side,
                commission=commission,
                trade_id=execution_result.get("order", {}).get("id")
            )
            
            # If a mode transition occurred, log it
            if mode_transition:
                logger.warning(
                    f"Strategy '{alert.strategy}' mode transition: "
                    f"{mode_transition.from_mode} -> {mode_transition.to_mode} "
                    f"Reason: {mode_transition.reason}"
                )
                
                # Broadcast mode transition to connected clients
                if _connection_manager:
                    await _connection_manager.broadcast_to_all({
                        "type": "strategy_mode_change",
                        "data": {
                            "strategy_id": alert.strategy,
                            "from_mode": mode_transition.from_mode,
                            "to_mode": mode_transition.to_mode,
                            "reason": mode_transition.reason,
                            "timestamp": time.time()
                        }
                    })
        
    except Exception as e:
        logger.error(f"Error recording strategy trade result for '{alert.strategy}': {e}")


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