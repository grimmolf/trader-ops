"""
Tastytrade Trading API

Provides order placement, management, and execution for stocks, options, and futures
through the Tastytrade platform.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from decimal import Decimal

import httpx
from pydantic import BaseModel, Field, validator

from .auth import TastytradeAuth

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by Tastytrade"""
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"
    STOP_LIMIT = "Stop Limit"


class OrderAction(Enum):
    """Order actions"""
    BUY_TO_OPEN = "Buy to Open"
    BUY_TO_CLOSE = "Buy to Close"
    SELL_TO_OPEN = "Sell to Open"
    SELL_TO_CLOSE = "Sell to Close"


class OrderTimeInForce(Enum):
    """Time in force types"""
    DAY = "Day"
    GTC = "GTC"  # Good Till Cancelled
    GTD = "GTD"  # Good Till Date
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill


class OrderStatus(Enum):
    """Order status types"""
    RECEIVED = "Received"
    CANCELLED = "Cancelled"
    FILLED = "Filled"
    EXPIRED = "Expired"
    PENDING = "Pending"
    REJECTED = "Rejected"
    CONTINGENT = "Contingent"
    ROUTED = "Routed"
    IN_FLIGHT = "In Flight"
    LIVE = "Live"
    QUEUED = "Queued"


class TastytradeOrderLeg(BaseModel):
    """Individual order leg for multi-leg strategies"""
    
    instrument_type: str
    symbol: str
    action: OrderAction
    quantity: int
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class TastytradeOrder(BaseModel):
    """Order request/response model"""
    
    # Core order fields
    order_type: OrderType
    time_in_force: OrderTimeInForce = OrderTimeInForce.DAY
    price: Optional[Decimal] = None
    price_effect: str = "Debit"  # Debit or Credit
    
    # Order legs
    legs: List[TastytradeOrderLeg]
    
    # Metadata
    account_number: Optional[str] = None
    order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Execution details
    filled_quantity: Optional[int] = None
    remaining_quantity: Optional[int] = None
    
    @validator('legs')
    def must_have_legs(cls, v):
        if not v:
            raise ValueError('Order must have at least one leg')
        return v
    
    @property
    def total_quantity(self) -> int:
        """Get total quantity across all legs"""
        return sum(leg.quantity for leg in self.legs)
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_working(self) -> bool:
        """Check if order is active/working"""
        return self.status in [OrderStatus.RECEIVED, OrderStatus.ROUTED, OrderStatus.LIVE, OrderStatus.QUEUED]
    
    @classmethod
    def create_equity_order(
        cls,
        symbol: str,
        action: OrderAction,
        quantity: int,
        order_type: OrderType,
        price: Optional[Decimal] = None,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY
    ) -> "TastytradeOrder":
        """
        Create a simple equity order.
        
        Args:
            symbol: Stock symbol
            action: Buy to open, sell to close, etc.
            quantity: Number of shares
            order_type: Market, limit, etc.
            price: Limit price (required for limit orders)
            time_in_force: Order duration
            
        Returns:
            TastytradeOrder: Configured order
        """
        leg = TastytradeOrderLeg(
            instrument_type="Equity",
            symbol=symbol.upper(),
            action=action,
            quantity=quantity
        )
        
        return cls(
            order_type=order_type,
            time_in_force=time_in_force,
            price=price,
            legs=[leg]
        )
    
    def to_tastytrade_format(self) -> Dict[str, Any]:
        """Convert to Tastytrade API format"""
        order_data = {
            "order-type": self.order_type.value,
            "time-in-force": self.time_in_force.value,
            "price-effect": self.price_effect,
            "legs": []
        }
        
        # Add pricing if specified
        if self.price is not None:
            order_data["price"] = str(self.price)
        
        # Add order legs
        for leg in self.legs:
            leg_data = {
                "instrument-type": leg.instrument_type,
                "symbol": leg.symbol,
                "action": leg.action.value,
                "quantity": leg.quantity
            }
            order_data["legs"].append(leg_data)
        
        return order_data
    
    @classmethod
    def from_tastytrade_data(cls, data: Dict[str, Any]) -> "TastytradeOrder":
        """Create order from Tastytrade API response"""
        # Parse order legs
        legs = []
        for leg_data in data.get("legs", []):
            leg = TastytradeOrderLeg(
                instrument_type=leg_data.get("instrument-type", "Equity"),
                symbol=leg_data.get("symbol", ""),
                action=OrderAction(leg_data.get("action", "Buy to Open")),
                quantity=leg_data.get("quantity", 0)
            )
            legs.append(leg)
        
        # Parse dates
        filled_at = None
        if data.get("filled-at"):
            filled_at = datetime.fromisoformat(data["filled-at"])
        
        cancelled_at = None
        if data.get("cancelled-at"):
            cancelled_at = datetime.fromisoformat(data["cancelled-at"])
        
        return cls(
            order_type=OrderType(data.get("order-type", "Market")),
            time_in_force=OrderTimeInForce(data.get("time-in-force", "Day")),
            price=Decimal(str(data["price"])) if data.get("price") else None,
            price_effect=data.get("price-effect", "Debit"),
            legs=legs,
            account_number=data.get("account-number"),
            order_id=data.get("id"),
            status=OrderStatus(data["status"]) if data.get("status") else None,
            filled_at=filled_at,
            cancelled_at=cancelled_at,
            filled_quantity=data.get("filled-quantity"),
            remaining_quantity=data.get("remaining-quantity")
        )


class TastytradeOrders:
    """
    Tastytrade trading API client.
    
    Provides order management and execution capabilities:
    - Place equity and option orders
    - Cancel and modify orders
    - Query order status and history
    - Account-specific trading operations
    """
    
    def __init__(self, auth: TastytradeAuth):
        self.auth = auth
        self.base_url = auth.api_base_url
    
    async def place_order(self, account_number: str, order: TastytradeOrder) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            account_number: Account number to trade in
            order: Order to place
            
        Returns:
            Dict[str, Any]: Order placement response
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            order_data = order.to_tastytrade_format()
            
            response = await client.post(
                f"{self.base_url}/accounts/{account_number}/orders",
                headers=headers,
                json=order_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Order placed successfully: {order.legs[0].symbol} {order.legs[0].action.value} {order.total_quantity}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error placing order: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to place order: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, account_number: str, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.delete(
                f"{self.base_url}/accounts/{account_number}/orders/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Order cancelled successfully: {order_id}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error cancelling order: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to cancel order: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise
    
    async def get_order(self, account_number: str, order_id: str) -> TastytradeOrder:
        """Get details for a specific order"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_number}/orders/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            order = TastytradeOrder.from_tastytrade_data(data)
            order.account_number = account_number
            
            logger.info(f"Retrieved order details for {order_id}")
            return order
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting order: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get order: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            raise
    
    async def get_orders(
        self,
        account_number: str,
        page_offset: Optional[int] = None,
        per_page: Optional[int] = None,
        sort: Optional[str] = None
    ) -> List[TastytradeOrder]:
        """Get orders for an account"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if page_offset is not None:
                params["page-offset"] = page_offset
            if per_page is not None:
                params["per-page"] = per_page
            if sort:
                params["sort"] = sort
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_number}/orders",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            orders = []
            if "data" in data and "items" in data["data"]:
                for order_data in data["data"]["items"]:
                    try:
                        order = TastytradeOrder.from_tastytrade_data(order_data)
                        order.account_number = account_number
                        orders.append(order)
                    except Exception as e:
                        logger.warning(f"Failed to parse order: {e}")
            
            logger.info(f"Retrieved {len(orders)} orders")
            return orders
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting orders: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get orders: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise
    
    async def replace_order(self, account_number: str, order_id: str, new_order: TastytradeOrder) -> Dict[str, Any]:
        """Replace an existing order with a new one"""
        try:
            # Cancel existing order
            await self.cancel_order(account_number, order_id)
            
            # Place new order
            result = await self.place_order(account_number, new_order)
            
            logger.info(f"Successfully replaced order {order_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error replacing order {order_id}: {e}")
            raise