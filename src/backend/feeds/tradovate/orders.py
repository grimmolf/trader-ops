"""
Tradovate Order Management

Handles order placement, execution, and management for Tradovate futures trading.
Includes support for market, limit, stop, and stop-limit orders with risk management.
"""

import logging
from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator

from .auth import TradovateAuth

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Tradovate order types"""
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"
    STOP_LIMIT = "StopLimit"
    MIT = "MIT"  # Market if Touched
    LIT = "LIT"  # Limit if Touched


class OrderSide(Enum):
    """Order side/action"""
    BUY = "Buy"
    SELL = "Sell"


class OrderStatus(Enum):
    """Order status from Tradovate"""
    PENDING = "Pending"
    WORKING = "Working"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    EXPIRED = "Expired"


class TimeInForce(Enum):
    """Time in force options"""
    DAY = "Day"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class TradovateOrderRequest(BaseModel):
    """Order request for Tradovate API"""
    
    account_id: int = Field(..., description="Account ID for order")
    contract_id: int = Field(..., description="Contract ID to trade")
    action: OrderSide = Field(..., description="Buy or Sell")
    order_type: OrderType = Field(..., description="Order type")
    quantity: int = Field(..., gt=0, description="Order quantity (contracts)")
    
    # Price fields (conditional based on order type)
    price: Optional[float] = Field(None, description="Limit price")
    stop_price: Optional[float] = Field(None, description="Stop price")
    
    # Order management
    time_in_force: TimeInForce = Field(default=TimeInForce.DAY, description="Time in force")
    is_automated: bool = Field(default=True, description="Mark as automated order")
    
    # Risk management
    bracket_order: bool = Field(default=False, description="Create bracket order")
    profit_target: Optional[float] = Field(None, description="Profit target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    
    @validator('price')
    def validate_price(cls, v, values):
        """Validate price for limit orders"""
        order_type = values.get('order_type')
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError(f"Price required for {order_type.value} orders")
        return v
    
    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        """Validate stop price for stop orders"""
        order_type = values.get('order_type')
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError(f"Stop price required for {order_type.value} orders")
        return v


class TradovateOrderResponse(BaseModel):
    """Response from Tradovate order submission"""
    
    order_id: Optional[int] = None
    status: str
    message: Optional[str] = None
    filled_quantity: int = 0
    remaining_quantity: int = 0
    avg_fill_price: Optional[float] = None
    commission: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Tradovate specific fields
    order_version: Optional[int] = None
    bracket_orders: Optional[List[int]] = None
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED.value
    
    @property
    def is_working(self) -> bool:
        """Check if order is working (pending fill)"""
        return self.status == OrderStatus.WORKING.value


class TradovateOrders:
    """
    Tradovate order management client.
    
    Handles all order-related operations including:
    - Order placement with validation
    - Order status tracking
    - Position management
    - Risk management integration
    """
    
    def __init__(self, auth: TradovateAuth):
        self.auth = auth
        logger.info("Initialized Tradovate orders client")
    
    async def place_order(
        self,
        account_id: int,
        symbol: str,
        action: str,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        **kwargs
    ) -> TradovateOrderResponse:
        """
        Place a futures order with comprehensive validation.
        
        Args:
            account_id: Tradovate account ID
            symbol: Trading symbol (e.g., "ES", "NQ")
            action: "Buy" or "Sell"
            quantity: Number of contracts
            order_type: Market, Limit, Stop, etc.
            price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            time_in_force: Order duration
            **kwargs: Additional order parameters
            
        Returns:
            TradovateOrderResponse: Order submission result
        """
        try:
            logger.info(f"Placing order: {symbol} {action} {quantity} @ {order_type.value}")
            
            # Step 1: Get contract ID for symbol
            contract_id = await self._get_contract_id(symbol)
            if not contract_id:
                return TradovateOrderResponse(
                    status="Rejected",
                    message=f"Contract not found for symbol: {symbol}"
                )
            
            # Step 2: Validate order parameters
            validation_result = await self._validate_order(
                account_id, contract_id, action, quantity, order_type, price, stop_price
            )
            if not validation_result.get("valid"):
                return TradovateOrderResponse(
                    status="Rejected",
                    message=validation_result.get("reason", "Order validation failed")
                )
            
            # Step 3: Build order request
            order_request = TradovateOrderRequest(
                account_id=account_id,
                contract_id=contract_id,
                action=OrderSide.BUY if action.upper() == "BUY" else OrderSide.SELL,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
                is_automated=kwargs.get("is_automated", True)
            )
            
            # Step 4: Submit order to Tradovate
            response = await self._submit_order(order_request)
            
            # Step 5: Process response
            if response.status_code == 200:
                order_data = response.json()
                
                return TradovateOrderResponse(
                    order_id=order_data.get("orderId"),
                    status=order_data.get("orderStatus", "Pending"),
                    message="Order submitted successfully",
                    remaining_quantity=quantity,
                    order_version=order_data.get("orderVersion")
                )
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("errorText", f"HTTP {response.status_code}")
                
                logger.error(f"Order submission failed: {error_msg}")
                return TradovateOrderResponse(
                    status="Rejected",
                    message=f"Order rejected: {error_msg}"
                )
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return TradovateOrderResponse(
                status="Error",
                message=f"Order placement error: {str(e)}"
            )
    
    async def _get_contract_id(self, symbol: str) -> Optional[int]:
        """Get contract ID for trading symbol"""
        try:
            response = await self.auth.make_authenticated_request(
                "GET",
                "/contract/find",
                params={"name": symbol}
            )
            
            if response.status_code == 200:
                contracts = response.json()
                if contracts:
                    return contracts[0].get("id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contract ID for {symbol}: {e}")
            return None
    
    async def _validate_order(
        self,
        account_id: int,
        contract_id: int,
        action: str,
        quantity: int,
        order_type: OrderType,
        price: Optional[float],
        stop_price: Optional[float]
    ) -> Dict[str, bool]:
        """Validate order before submission"""
        try:
            # Basic validation
            if quantity <= 0:
                return {"valid": False, "reason": "Quantity must be positive"}
            
            if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not price:
                return {"valid": False, "reason": f"Price required for {order_type.value} orders"}
            
            if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and not stop_price:
                return {"valid": False, "reason": f"Stop price required for {order_type.value} orders"}
            
            # Check account status and buying power
            account_valid = await self._validate_account(account_id, quantity)
            if not account_valid.get("valid"):
                return account_valid
            
            # Contract-specific validation
            contract_valid = await self._validate_contract(contract_id, price, stop_price)
            if not contract_valid.get("valid"):
                return contract_valid
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}
    
    async def _validate_account(self, account_id: int, quantity: int) -> Dict[str, bool]:
        """Validate account can support the order"""
        try:
            # Get account information
            response = await self.auth.make_authenticated_request(
                "GET",
                "/account/list"
            )
            
            if response.status_code == 200:
                accounts = response.json()
                account = next((a for a in accounts if a.get("id") == account_id), None)
                
                if not account:
                    return {"valid": False, "reason": "Account not found"}
                
                # Check account status
                if account.get("archived"):
                    return {"valid": False, "reason": "Account is archived"}
                
                # TODO: Add margin/buying power validation
                # This would require getting margin requirements for the contract
                
                return {"valid": True}
            
            return {"valid": False, "reason": "Cannot validate account"}
            
        except Exception as e:
            logger.error(f"Error validating account: {e}")
            return {"valid": False, "reason": f"Account validation error: {str(e)}"}
    
    async def _validate_contract(
        self,
        contract_id: int,
        price: Optional[float],
        stop_price: Optional[float]
    ) -> Dict[str, bool]:
        """Validate contract and price levels"""
        try:
            # Get contract details
            response = await self.auth.make_authenticated_request(
                "GET",
                "/contract/item",
                params={"id": contract_id}
            )
            
            if response.status_code == 200:
                contract = response.json()
                
                # Check if contract is tradeable
                if not contract.get("tradeable", True):
                    return {"valid": False, "reason": "Contract is not tradeable"}
                
                # Validate price increments
                tick_size = contract.get("tickSize", 0.01)
                
                if price and tick_size:
                    if abs(price % tick_size) > 1e-6:  # Account for floating point precision
                        return {"valid": False, "reason": f"Price must be in increments of {tick_size}"}
                
                if stop_price and tick_size:
                    if abs(stop_price % tick_size) > 1e-6:
                        return {"valid": False, "reason": f"Stop price must be in increments of {tick_size}"}
                
                return {"valid": True}
            
            return {"valid": False, "reason": "Cannot validate contract"}
            
        except Exception as e:
            logger.error(f"Error validating contract: {e}")
            return {"valid": False, "reason": f"Contract validation error: {str(e)}"}
    
    async def _submit_order(self, order_request: TradovateOrderRequest) -> object:
        """Submit order to Tradovate API"""
        # Build order payload
        order_payload = {
            "accountId": order_request.account_id,
            "contractId": order_request.contract_id,
            "action": order_request.action.value,
            "orderType": order_request.order_type.value,
            "orderQty": order_request.quantity,
            "timeInForce": order_request.time_in_force.value,
            "isAutomated": order_request.is_automated
        }
        
        # Add conditional fields
        if order_request.price:
            order_payload["price"] = order_request.price
        
        if order_request.stop_price:
            order_payload["stopPrice"] = order_request.stop_price
        
        # Submit order
        return await self.auth.make_authenticated_request(
            "POST",
            "/order/placeorder",
            json=order_payload
        )
    
    async def get_order_status(self, order_id: int) -> Optional[TradovateOrderResponse]:
        """Get current status of an order"""
        try:
            response = await self.auth.make_authenticated_request(
                "GET",
                "/order/item",
                params={"id": order_id}
            )
            
            if response.status_code == 200:
                order_data = response.json()
                
                return TradovateOrderResponse(
                    order_id=order_data.get("id"),
                    status=order_data.get("orderStatus", "Unknown"),
                    filled_quantity=order_data.get("filledQty", 0),
                    remaining_quantity=order_data.get("orderQty", 0) - order_data.get("filledQty", 0),
                    avg_fill_price=order_data.get("avgFillPrice"),
                    commission=order_data.get("commission"),
                    order_version=order_data.get("orderVersion")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel an open order"""
        try:
            response = await self.auth.make_authenticated_request(
                "POST",
                "/order/cancelorder",
                json={"orderId": order_id}
            )
            
            if response.status_code == 200:
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_working_orders(self, account_id: int) -> List[TradovateOrderResponse]:
        """Get all working orders for an account"""
        try:
            response = await self.auth.make_authenticated_request(
                "GET",
                "/order/list",
                params={"accountId": account_id}
            )
            
            if response.status_code == 200:
                orders_data = response.json()
                working_orders = []
                
                for order_data in orders_data:
                    if order_data.get("orderStatus") in ["Working", "Pending"]:
                        order = TradovateOrderResponse(
                            order_id=order_data.get("id"),
                            status=order_data.get("orderStatus"),
                            filled_quantity=order_data.get("filledQty", 0),
                            remaining_quantity=order_data.get("orderQty", 0) - order_data.get("filledQty", 0),
                            avg_fill_price=order_data.get("avgFillPrice"),
                            order_version=order_data.get("orderVersion")
                        )
                        working_orders.append(order)
                
                return working_orders
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting working orders: {e}")
            return []
    
    async def flatten_position(self, account_id: int, symbol: str) -> TradovateOrderResponse:
        """Close/flatten position for a symbol"""
        try:
            # Get current position
            position = await self._get_position(account_id, symbol)
            if not position:
                return TradovateOrderResponse(
                    status="Rejected",
                    message="No position found to flatten"
                )
            
            position_size = position.get("netPos", 0)
            if position_size == 0:
                return TradovateOrderResponse(
                    status="Rejected", 
                    message="Position is already flat"
                )
            
            # Determine action to flatten
            action = "Sell" if position_size > 0 else "Buy"
            quantity = abs(position_size)
            
            # Place market order to flatten
            return await self.place_order(
                account_id=account_id,
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=OrderType.MARKET
            )
            
        except Exception as e:
            logger.error(f"Error flattening position: {e}")
            return TradovateOrderResponse(
                status="Error",
                message=f"Error flattening position: {str(e)}"
            )
    
    async def _get_position(self, account_id: int, symbol: str) -> Optional[Dict]:
        """Get current position for symbol"""
        try:
            # Get contract ID
            contract_id = await self._get_contract_id(symbol)
            if not contract_id:
                return None
            
            # Get positions
            response = await self.auth.make_authenticated_request(
                "GET",
                "/position/list",
                params={"accountId": account_id}
            )
            
            if response.status_code == 200:
                positions = response.json()
                position = next((p for p in positions if p.get("contractId") == contract_id), None)
                return position
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return None