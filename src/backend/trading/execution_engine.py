"""
Advanced Trading Execution Engine

Implements sophisticated automated trading logic that:
1. Receives webhook alerts from Kairos/TradingView
2. Applies risk management and position sizing
3. Executes trades through multiple brokers
4. Manages order lifecycle and portfolio tracking
5. Provides real-time execution monitoring

Architecture: Kairos/TradingView -> Webhook -> Execution Engine -> Broker APIs
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

import redis.asyncio as redis
from pydantic import BaseModel, Field

from ..models.alerts import Alert, AlertEvent, AlertStatus
from ..models.execution import Order, Execution, OrderStatus, OrderType, OrderSide, Position
from ..models.portfolio import Portfolio, PortfolioPosition
from ..feeds.tradier import TradierConnector, TradierError


logger = logging.getLogger(__name__)


class RiskCheckResult(str, Enum):
    """Risk check results"""
    APPROVED = "approved"
    REJECTED_INSUFFICIENT_FUNDS = "rejected_insufficient_funds"
    REJECTED_POSITION_LIMIT = "rejected_position_limit"
    REJECTED_DAILY_LOSS_LIMIT = "rejected_daily_loss_limit"
    REJECTED_CONCENTRATION = "rejected_concentration"
    REJECTED_MARKET_HOURS = "rejected_market_hours"
    REJECTED_VOLATILITY = "rejected_volatility"
    APPROVED_WITH_REDUCTION = "approved_with_reduction"


class ExecutionResult(BaseModel):
    """Result of trade execution attempt"""
    success: bool
    order_id: Optional[str] = None
    broker_order_id: Optional[str] = None
    error_message: Optional[str] = None
    risk_check: Optional[RiskCheckResult] = None
    original_quantity: Optional[float] = None
    executed_quantity: Optional[float] = None
    execution_price: Optional[float] = None


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float = 0.1  # 10% of portfolio
    max_daily_loss: float = 0.02    # 2% daily loss limit
    max_concentration: float = 0.25  # 25% in single position
    min_account_balance: float = 1000.0
    max_portfolio_leverage: float = 2.0
    
    # Market hours enforcement
    enforce_market_hours: bool = True
    allow_extended_hours: bool = False
    
    # Volatility controls
    max_symbol_volatility: float = 0.5  # 50% annualized
    volatility_lookback_days: int = 30


class TradingSession:
    """Manages trading session state and controls"""
    
    def __init__(self):
        self.is_active: bool = True
        self.daily_pnl: float = 0.0
        self.trades_today: int = 0
        self.last_trade_time: Optional[int] = None
        self.emergency_stop: bool = False
        self.session_start: int = int(time.time())


class ExecutionEngine:
    """
    Advanced trading execution engine with comprehensive risk management.
    
    Features:
    - Multi-broker support
    - Real-time risk management
    - Position size optimization
    - Portfolio-aware execution
    - Alert-driven automation
    - Execution monitoring and reporting
    """
    
    def __init__(
        self,
        tradier_connector: TradierConnector,
        risk_params: Optional[RiskParameters] = None,
        redis_url: str = "redis://localhost:6379"
    ):
        self.tradier = tradier_connector
        self.risk_params = risk_params or RiskParameters()
        
        # State management
        self.session = TradingSession()
        self.active_orders: Dict[str, Order] = {}
        self.executions: List[Execution] = []
        self.portfolio: Optional[Portfolio] = None
        
        # Event handlers
        self.pre_execution_hooks: List[Callable] = []
        self.post_execution_hooks: List[Callable] = []
        self.risk_check_hooks: List[Callable] = []
        self.order_fill_hooks: List[Callable] = []
        
        # Redis for state persistence and pub/sub
        self.redis: Optional[redis.Redis] = None
        self.redis_url = redis_url
        
        # Performance tracking
        self.execution_times: List[float] = []
        self.risk_check_times: List[float] = []
    
    async def initialize(self) -> None:
        """Initialize execution engine"""
        try:
            # Connect to Redis
            self.redis = redis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("Connected to Redis")
            
            # Load portfolio
            await self._load_portfolio()
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_orders())
            asyncio.create_task(self._update_portfolio())
            
            logger.info("Execution engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize execution engine: {e}")
            raise
    
    async def process_alert_event(self, alert_event: AlertEvent) -> ExecutionResult:
        """
        Process alert event and execute trade if conditions are met.
        
        This is the main entry point for webhook-driven trading.
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing alert event: {alert_event.alert_id} for {alert_event.symbol}")
            
            # Check if auto-execution is enabled
            if not alert_event.auto_execute:
                logger.info("Auto-execute disabled for alert")
                return ExecutionResult(
                    success=False,
                    error_message="Auto-execute disabled"
                )
            
            # Create order from alert
            order = await self._create_order_from_alert(alert_event)
            if not order:
                return ExecutionResult(
                    success=False,
                    error_message="Failed to create order from alert"
                )
            
            # Execute trade
            result = await self.execute_trade(order, alert_event)
            
            # Record processing time
            processing_time = time.time() - start_time
            self.execution_times.append(processing_time)
            
            # Publish execution result
            await self._publish_execution_result(alert_event, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing alert event: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )
    
    async def execute_trade(
        self,
        order: Order,
        context: Optional[AlertEvent] = None
    ) -> ExecutionResult:
        """
        Execute trade with comprehensive risk management.
        
        Flow:
        1. Pre-execution hooks
        2. Risk management checks
        3. Position sizing optimization
        4. Order placement
        5. Order monitoring
        6. Post-execution hooks
        """
        try:
            # Run pre-execution hooks
            for hook in self.pre_execution_hooks:
                await hook(order, context)
            
            # Comprehensive risk check
            risk_result = await self._comprehensive_risk_check(order)
            
            if risk_result == RiskCheckResult.REJECTED_INSUFFICIENT_FUNDS:
                return ExecutionResult(
                    success=False,
                    risk_check=risk_result,
                    error_message="Insufficient funds"
                )
            elif risk_result == RiskCheckResult.REJECTED_POSITION_LIMIT:
                return ExecutionResult(
                    success=False,
                    risk_check=risk_result,
                    error_message="Position size exceeds limit"
                )
            elif risk_result == RiskCheckResult.REJECTED_DAILY_LOSS_LIMIT:
                return ExecutionResult(
                    success=False,
                    risk_check=risk_result,
                    error_message="Daily loss limit reached"
                )
            elif risk_result == RiskCheckResult.REJECTED_MARKET_HOURS:
                return ExecutionResult(
                    success=False,
                    risk_check=risk_result,
                    error_message="Outside market hours"
                )
            
            # Apply position sizing optimization
            original_quantity = order.quantity
            if risk_result == RiskCheckResult.APPROVED_WITH_REDUCTION:
                order.quantity = await self._optimize_position_size(order)
                logger.info(f"Reduced position size from {original_quantity} to {order.quantity}")
            
            # Place order with broker
            try:
                broker_order_id = await self.tradier.place_order(order)
                order.broker_order_id = broker_order_id
                order.status = OrderStatus.OPEN
                
                # Track active order
                self.active_orders[order.id] = order
                
                # Update session stats
                self.session.trades_today += 1
                self.session.last_trade_time = int(time.time())
                
                logger.info(f"Order placed successfully: {order.id} -> {broker_order_id}")
                
                # Run post-execution hooks
                for hook in self.post_execution_hooks:
                    await hook(order, context)
                
                return ExecutionResult(
                    success=True,
                    order_id=order.id,
                    broker_order_id=broker_order_id,
                    risk_check=risk_result,
                    original_quantity=original_quantity,
                    executed_quantity=order.quantity
                )
                
            except TradierError as e:
                logger.error(f"Broker error placing order: {e}")
                return ExecutionResult(
                    success=False,
                    error_message=f"Broker error: {e}",
                    risk_check=risk_result
                )
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _comprehensive_risk_check(self, order: Order) -> RiskCheckResult:
        """Comprehensive risk management check"""
        start_time = time.time()
        
        try:
            # Check session state
            if self.session.emergency_stop:
                return RiskCheckResult.REJECTED_DAILY_LOSS_LIMIT
            
            if not self.session.is_active:
                return RiskCheckResult.REJECTED_MARKET_HOURS
            
            # Check daily loss limit
            if self.session.daily_pnl <= -self.risk_params.max_daily_loss:
                logger.warning(f"Daily loss limit reached: {self.session.daily_pnl}")
                return RiskCheckResult.REJECTED_DAILY_LOSS_LIMIT
            
            # Check market hours
            if self.risk_params.enforce_market_hours:
                if not await self._is_market_open():
                    return RiskCheckResult.REJECTED_MARKET_HOURS
            
            # Get account info
            account = await self.tradier.get_account_info()
            
            # Check account balance
            if account.cash_balance < self.risk_params.min_account_balance:
                return RiskCheckResult.REJECTED_INSUFFICIENT_FUNDS
            
            # Calculate position value
            position_value = order.quantity * (order.price or 100.0)  # Estimate if no price
            
            # Check buying power
            if position_value > account.buying_power:
                if position_value > account.cash_balance:
                    return RiskCheckResult.REJECTED_INSUFFICIENT_FUNDS
                else:
                    # Can execute with reduced size
                    return RiskCheckResult.APPROVED_WITH_REDUCTION
            
            # Check position size limits
            if self.portfolio:
                portfolio_value = self.portfolio.total_value
                if portfolio_value > 0:
                    position_weight = position_value / portfolio_value
                    if position_weight > self.risk_params.max_position_size:
                        return RiskCheckResult.APPROVED_WITH_REDUCTION
                    
                    # Check concentration risk
                    existing_position = self.portfolio.get_position(order.symbol)
                    if existing_position:
                        total_weight = existing_position.weight + position_weight
                        if total_weight > self.risk_params.max_concentration:
                            return RiskCheckResult.REJECTED_CONCENTRATION
            
            # Run custom risk check hooks
            for hook in self.risk_check_hooks:
                hook_result = await hook(order, account, self.portfolio)
                if hook_result != RiskCheckResult.APPROVED:
                    return hook_result
            
            # Record risk check time
            check_time = time.time() - start_time
            self.risk_check_times.append(check_time)
            
            return RiskCheckResult.APPROVED
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            return RiskCheckResult.REJECTED_INSUFFICIENT_FUNDS  # Fail safe
    
    async def _optimize_position_size(self, order: Order) -> float:
        """Optimize position size based on risk parameters"""
        try:
            # Get account info
            account = await self.tradier.get_account_info()
            
            # Calculate maximum position size based on buying power
            estimated_price = order.price or 100.0
            max_shares_by_capital = account.buying_power / estimated_price
            
            # Calculate maximum position size based on portfolio weight
            max_shares_by_weight = order.quantity
            if self.portfolio and self.portfolio.total_value > 0:
                max_position_value = self.portfolio.total_value * self.risk_params.max_position_size
                max_shares_by_weight = max_position_value / estimated_price
            
            # Take the minimum
            optimized_quantity = min(
                order.quantity,
                max_shares_by_capital,
                max_shares_by_weight
            )
            
            # Ensure minimum viable position
            min_quantity = 1.0
            return max(optimized_quantity, min_quantity)
            
        except Exception as e:
            logger.error(f"Error optimizing position size: {e}")
            return order.quantity  # Return original if optimization fails
    
    async def _create_order_from_alert(self, alert_event: AlertEvent) -> Optional[Order]:
        """Create order from alert event"""
        try:
            # Map alert side to order side
            side_map = {
                "buy": OrderSide.BUY,
                "sell": OrderSide.SELL,
                "long": OrderSide.BUY,
                "short": OrderSide.SELL,
                "close": OrderSide.SELL  # Simplified
            }
            
            order_side = side_map.get(alert_event.order_side, OrderSide.BUY)
            
            # Map order type
            type_map = {
                "market": OrderType.MARKET,
                "limit": OrderType.LIMIT,
                "stop": OrderType.STOP,
                "stop_limit": OrderType.STOP_LIMIT
            }
            
            order_type = type_map.get(alert_event.order_type, OrderType.MARKET)
            
            order = Order(
                symbol=alert_event.symbol,
                order_type=order_type,
                side=order_side,
                quantity=alert_event.order_quantity or 100,  # Default quantity
                price=alert_event.order_price,
                alert_id=alert_event.alert_id
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Error creating order from alert: {e}")
            return None
    
    async def _monitor_orders(self) -> None:
        """Monitor active orders for fills and updates"""
        while True:
            try:
                if not self.active_orders:
                    await asyncio.sleep(1)
                    continue
                
                # Check each active order
                orders_to_remove = []
                for order_id, order in self.active_orders.items():
                    try:
                        if order.broker_order_id:
                            status_data = await self.tradier.get_order_status(order.broker_order_id)
                            
                            # Update order status
                            new_status = self._map_tradier_status(status_data.get("status", ""))
                            if new_status != order.status:
                                order.status = new_status
                                logger.info(f"Order {order_id} status updated: {new_status}")
                                
                                # Handle fills
                                if new_status == OrderStatus.FILLED:
                                    await self._handle_order_fill(order, status_data)
                                    orders_to_remove.append(order_id)
                                elif new_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                                    orders_to_remove.append(order_id)
                    
                    except Exception as e:
                        logger.error(f"Error monitoring order {order_id}: {e}")
                
                # Remove completed orders
                for order_id in orders_to_remove:
                    del self.active_orders[order_id]
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in order monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _handle_order_fill(self, order: Order, status_data: Dict[str, Any]) -> None:
        """Handle order fill and update portfolio"""
        try:
            # Create execution record
            execution = Execution(
                order_id=order.id,
                broker="Tradier",
                broker_execution_id=status_data.get("id"),
                symbol=order.symbol,
                side=order.side,
                quantity=float(status_data.get("exec_quantity", order.quantity)),
                price=float(status_data.get("exec_price", order.price or 0)),
                commission=float(status_data.get("commission", 0))
            )
            
            self.executions.append(execution)
            
            # Update portfolio
            if self.portfolio:
                await self._update_portfolio_position(execution)
            
            # Update session P&L
            pnl_impact = execution.net_value if execution.side == OrderSide.SELL else -execution.net_value
            self.session.daily_pnl += pnl_impact
            
            logger.info(f"Order filled: {order.id} - {execution.quantity} @ {execution.price}")
            
            # Run order fill hooks (e.g., TradeNote logging)
            for hook in self.order_fill_hooks:
                try:
                    await hook(execution, order, status_data)
                except Exception as hook_error:
                    logger.error(f"Error in order fill hook: {hook_error}")
            
        except Exception as e:
            logger.error(f"Error handling order fill: {e}")
    
    def _map_tradier_status(self, tradier_status: str) -> OrderStatus:
        """Map Tradier order status to internal status"""
        status_map = {
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
            "pending": OrderStatus.PENDING,
            "open": OrderStatus.OPEN,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "expired": OrderStatus.EXPIRED
        }
        return status_map.get(tradier_status.lower(), OrderStatus.PENDING)
    
    async def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        # Simplified market hours check
        # In production, you'd want to check against actual market calendar
        current_time = datetime.now(timezone.utc)
        weekday = current_time.weekday()
        hour = current_time.hour
        
        # Rough market hours: Monday-Friday, 9:30 AM - 4:00 PM ET (14:30-21:00 UTC)
        if weekday < 5:  # Monday = 0, Friday = 4
            return 14 <= hour < 21  # Simplified UTC check
        return False
    
    async def _load_portfolio(self) -> None:
        """Load portfolio from persistent storage"""
        try:
            if self.redis:
                portfolio_data = await self.redis.get("portfolio")
                if portfolio_data:
                    # TODO: Deserialize portfolio from Redis
                    pass
            
            # For now, create a basic portfolio
            if not self.portfolio:
                self.portfolio = Portfolio(
                    id="main",
                    name="Main Trading Portfolio",
                    account_id=self.tradier.account_id or "default",
                    portfolio_type="mixed",
                    cash_balance=10000.0  # Default
                )
                
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
    
    async def _update_portfolio(self) -> None:
        """Periodically update portfolio with current positions and prices"""
        while True:
            try:
                if self.portfolio:
                    # Get current positions from broker
                    positions = await self.tradier.get_positions()
                    
                    # Update portfolio positions
                    self.portfolio.positions.clear()
                    for position in positions:
                        portfolio_position = PortfolioPosition(
                            symbol=position.symbol,
                            quantity=position.quantity,
                            avg_price=position.avg_price,
                            weight=0.0  # Will be calculated
                        )
                        self.portfolio.positions.append(portfolio_position)
                    
                    # Update values and weights
                    self.portfolio.update_values()
                    
                    # Save to Redis
                    if self.redis:
                        # TODO: Serialize and save portfolio
                        pass
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error updating portfolio: {e}")
                await asyncio.sleep(60)
    
    async def _update_portfolio_position(self, execution: Execution) -> None:
        """Update portfolio position based on execution"""
        if not self.portfolio:
            return
        
        try:
            existing_position = self.portfolio.get_position(execution.symbol)
            
            if existing_position:
                # Update existing position
                if execution.side == OrderSide.BUY:
                    # Add to position
                    total_cost = (existing_position.quantity * existing_position.avg_price + 
                                execution.quantity * execution.price)
                    total_quantity = existing_position.quantity + execution.quantity
                    existing_position.avg_price = total_cost / total_quantity
                    existing_position.quantity = total_quantity
                else:
                    # Reduce position
                    existing_position.quantity -= execution.quantity
                    if existing_position.quantity <= 0:
                        self.portfolio.remove_position(execution.symbol)
            else:
                # Create new position
                if execution.side == OrderSide.BUY:
                    new_position = PortfolioPosition(
                        symbol=execution.symbol,
                        quantity=execution.quantity,
                        avg_price=execution.price,
                        weight=0.0
                    )
                    self.portfolio.add_position(new_position)
            
            # Update portfolio values
            self.portfolio.update_values()
            
        except Exception as e:
            logger.error(f"Error updating portfolio position: {e}")
    
    async def _publish_execution_result(
        self,
        alert_event: AlertEvent,
        result: ExecutionResult
    ) -> None:
        """Publish execution result to Redis pub/sub"""
        try:
            if self.redis:
                message = {
                    "type": "execution_result",
                    "alert_id": alert_event.alert_id,
                    "symbol": alert_event.symbol,
                    "result": result.dict(),
                    "timestamp": int(time.time())
                }
                
                await self.redis.publish("trading_executions", json.dumps(message))
                
        except Exception as e:
            logger.error(f"Error publishing execution result: {e}")
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    def add_pre_execution_hook(self, hook: Callable) -> None:
        """Add pre-execution hook"""
        self.pre_execution_hooks.append(hook)
    
    def add_post_execution_hook(self, hook: Callable) -> None:
        """Add post-execution hook"""
        self.post_execution_hooks.append(hook)
    
    def add_risk_check_hook(self, hook: Callable) -> None:
        """Add custom risk check hook"""
        self.risk_check_hooks.append(hook)
    
    def add_order_fill_hook(self, hook: Callable) -> None:
        """Add order fill hook (called when orders are filled)"""
        self.order_fill_hooks.append(hook)
    
    async def emergency_stop(self) -> None:
        """Emergency stop all trading"""
        self.session.emergency_stop = True
        self.session.is_active = False
        
        # Cancel all active orders
        for order in self.active_orders.values():
            if order.broker_order_id:
                try:
                    await self.tradier.cancel_order(order.broker_order_id)
                except Exception as e:
                    logger.error(f"Error cancelling order {order.id}: {e}")
        
        logger.warning("EMERGENCY STOP ACTIVATED - All trading halted")
    
    async def resume_trading(self) -> None:
        """Resume trading after emergency stop"""
        self.session.emergency_stop = False
        self.session.is_active = True
        logger.info("Trading resumed")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get execution engine performance statistics"""
        return {
            "session_start": self.session.session_start,
            "trades_today": self.session.trades_today,
            "daily_pnl": self.session.daily_pnl,
            "active_orders": len(self.active_orders),
            "total_executions": len(self.executions),
            "avg_execution_time": sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0,
            "avg_risk_check_time": sum(self.risk_check_times) / len(self.risk_check_times) if self.risk_check_times else 0,
            "emergency_stop": self.session.emergency_stop,
            "session_active": self.session.is_active
        }
    
    async def close(self) -> None:
        """Close execution engine and cleanup resources"""
        self.session.is_active = False
        
        if self.redis:
            await self.redis.close()
        
        logger.info("Execution engine closed")