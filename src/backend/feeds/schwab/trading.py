"""
Charles Schwab Trading API

Provides order placement, management, and execution for stocks and options
through the Schwab trading platform.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from decimal import Decimal

import httpx
from pydantic import BaseModel, Field, validator

from .auth import SchwabAuth

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by Schwab"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"


class OrderAction(Enum):
    """Order actions"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_TO_OPEN = "BUY_TO_OPEN"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"
    SELL_TO_OPEN = "SELL_TO_OPEN"
    SELL_TO_CLOSE = "SELL_TO_CLOSE"


class OrderDuration(Enum):
    """Order duration types"""
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"
    FILL_OR_KILL = "FILL_OR_KILL"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"


class OrderStatus(Enum):
    """Order status types"""
    AWAITING_PARENT_ORDER = "AWAITING_PARENT_ORDER"
    AWAITING_CONDITION = "AWAITING_CONDITION"
    AWAITING_STOP_CONDITION = "AWAITING_STOP_CONDITION"
    AWAITING_MANUAL_REVIEW = "AWAITING_MANUAL_REVIEW"
    ACCEPTED = "ACCEPTED"
    AWAITING_UR_OUT = "AWAITING_UR_OUT"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    QUEUED = "QUEUED"
    WORKING = "WORKING"
    REJECTED = "REJECTED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELED = "CANCELED"
    PENDING_REPLACE = "PENDING_REPLACE"
    REPLACED = "REPLACED"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"


class AssetType(Enum):
    """Asset types for trading"""
    EQUITY = "EQUITY"
    OPTION = "OPTION"
    INDEX = "INDEX"
    MUTUAL_FUND = "MUTUAL_FUND"
    CASH_EQUIVALENT = "CASH_EQUIVALENT"
    FIXED_INCOME = "FIXED_INCOME"
    CURRENCY = "CURRENCY"


class SchwabInstrument(BaseModel):
    """Trading instrument specification"""
    
    asset_type: AssetType
    symbol: str
    description: Optional[str] = None
    
    # Option-specific fields
    put_call: Optional[str] = None  # PUT or CALL
    underlying_symbol: Optional[str] = None
    option_multiplier: Optional[float] = None
    option_deliverables: Optional[List[Dict[str, Any]]] = None


class SchwabOrderLeg(BaseModel):
    """Individual order leg for multi-leg strategies"""
    
    action: OrderAction
    quantity: int
    instrument: SchwabInstrument
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class SchwabOrder(BaseModel):
    """Order request/response model"""
    
    # Core order fields
    order_type: OrderType
    session: str = "NORMAL"  # NORMAL, AM, PM, SEAMLESS
    duration: OrderDuration = OrderDuration.DAY
    order_strategy_type: str = "SINGLE"  # SINGLE, CANCEL_REPLACE, RECALL, PAIR, FLATTEN, TWO_DAY_SWAP, BLAST_ALL, OCO, TRIGGER
    
    # Order legs
    order_leg_collection: List[SchwabOrderLeg]
    
    # Pricing
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    
    # Metadata
    account_id: Optional[str] = None
    order_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    entered_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    tag: Optional[str] = None
    
    # Execution details
    filled_quantity: Optional[int] = None
    remaining_quantity: Optional[int] = None
    
    @validator('order_leg_collection')
    def must_have_legs(cls, v):
        if not v:
            raise ValueError('Order must have at least one leg')
        return v
    
    @property
    def total_quantity(self) -> int:
        """Get total quantity across all legs"""
        return sum(leg.quantity for leg in self.order_leg_collection)
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_working(self) -> bool:
        """Check if order is active/working"""
        return self.status in [OrderStatus.ACCEPTED, OrderStatus.WORKING, OrderStatus.QUEUED]
    
    @classmethod
    def create_equity_order(
        cls,
        symbol: str,
        action: OrderAction,
        quantity: int,
        order_type: OrderType,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        duration: OrderDuration = OrderDuration.DAY,
        tag: Optional[str] = None
    ) -> "SchwabOrder":
        """
        Create a simple equity order.
        
        Args:
            symbol: Stock symbol
            action: BUY or SELL
            quantity: Number of shares
            order_type: Market, limit, etc.
            price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            duration: Order duration
            tag: Optional order tag
            
        Returns:
            SchwabOrder: Configured order
        """
        instrument = SchwabInstrument(
            asset_type=AssetType.EQUITY,
            symbol=symbol.upper()
        )
        
        leg = SchwabOrderLeg(
            action=action,
            quantity=quantity,
            instrument=instrument
        )
        
        return cls(
            order_type=order_type,
            duration=duration,
            order_leg_collection=[leg],
            price=price,
            stop_price=stop_price,
            tag=tag
        )
    
    def to_schwab_format(self) -> Dict[str, Any]:
        """Convert to Schwab API format"""
        order_data = {
            "orderType": self.order_type.value,
            "session": self.session,
            "duration": self.duration.value,
            "orderStrategyType": self.order_strategy_type,
            "orderLegCollection": []
        }
        
        # Add pricing if specified
        if self.price is not None:
            order_data["price"] = float(self.price)
        if self.stop_price is not None:
            order_data["stopPrice"] = float(self.stop_price)
        
        # Add order legs
        for leg in self.order_leg_collection:
            leg_data = {
                "instruction": leg.action.value,
                "quantity": leg.quantity,
                "instrument": {
                    "symbol": leg.instrument.symbol,
                    "assetType": leg.instrument.asset_type.value
                }
            }
            
            # Add option-specific fields
            if leg.instrument.asset_type == AssetType.OPTION:
                if leg.instrument.put_call:
                    leg_data["instrument"]["putCall"] = leg.instrument.put_call
                if leg.instrument.underlying_symbol:
                    leg_data["instrument"]["underlyingSymbol"] = leg.instrument.underlying_symbol
                if leg.instrument.option_multiplier:
                    leg_data["instrument"]["optionMultiplier"] = leg.instrument.option_multiplier
                if leg.instrument.option_deliverables:
                    leg_data["instrument"]["optionDeliverables"] = leg.instrument.option_deliverables
            
            order_data["orderLegCollection"].append(leg_data)
        
        return order_data
    
    @classmethod
    def from_schwab_data(cls, data: Dict[str, Any]) -> "SchwabOrder":
        """Create order from Schwab API response"""
        # Parse order legs
        legs = []
        for leg_data in data.get("orderLegCollection", []):
            instrument_data = leg_data.get("instrument", {})
            
            instrument = SchwabInstrument(
                asset_type=AssetType(instrument_data.get("assetType", "EQUITY")),
                symbol=instrument_data.get("symbol", ""),
                description=instrument_data.get("description"),
                put_call=instrument_data.get("putCall"),
                underlying_symbol=instrument_data.get("underlyingSymbol"),
                option_multiplier=instrument_data.get("optionMultiplier"),
                option_deliverables=instrument_data.get("optionDeliverables")
            )
            
            leg = SchwabOrderLeg(
                action=OrderAction(leg_data.get("instruction", "BUY")),
                quantity=leg_data.get("quantity", 0),
                instrument=instrument
            )
            legs.append(leg)
        
        # Parse dates
        entered_time = None
        if data.get("enteredTime"):
            entered_time = datetime.fromisoformat(data["enteredTime"].replace("Z", "+00:00"))
        
        close_time = None
        if data.get("closeTime"):
            close_time = datetime.fromisoformat(data["closeTime"].replace("Z", "+00:00"))
        
        return cls(
            order_type=OrderType(data.get("orderType", "MARKET")),
            session=data.get("session", "NORMAL"),
            duration=OrderDuration(data.get("duration", "DAY")),
            order_strategy_type=data.get("orderStrategyType", "SINGLE"),
            order_leg_collection=legs,
            price=Decimal(str(data["price"])) if data.get("price") else None,
            stop_price=Decimal(str(data["stopPrice"])) if data.get("stopPrice") else None,
            order_id=data.get("orderId"),
            status=OrderStatus(data["status"]) if data.get("status") else None,
            entered_time=entered_time,
            close_time=close_time,
            tag=data.get("tag"),
            filled_quantity=data.get("filledQuantity"),
            remaining_quantity=data.get("remainingQuantity")
        )


class SchwabTrading:
    """
    Schwab trading API client.
    
    Provides order management and execution capabilities:
    - Place equity and option orders
    - Cancel and modify orders
    - Query order status and history
    - Account-specific trading operations
    """
    
    def __init__(self, auth: SchwabAuth):
        self.auth = auth
        self.base_url = "https://api.schwabapi.com/trader/v1"
    
    async def place_order(self, account_hash: str, order: SchwabOrder) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            account_hash: Account hash identifier
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
            
            order_data = order.to_schwab_format()
            
            response = await client.post(
                f"{self.base_url}/accounts/{account_hash}/orders",
                headers=headers,
                json=order_data
            )
            response.raise_for_status()
            
            # Schwab returns 201 with location header containing order ID
            order_id = None
            if "Location" in response.headers:
                location = response.headers["Location"]
                order_id = location.split("/")[-1]
            
            logger.info(f"Successfully placed order for {order.total_quantity} shares")
            
            return {
                "status": "success",
                "order_id": order_id,
                "message": "Order placed successfully"
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error placing order: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to place order: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, account_hash: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            account_hash: Account hash identifier
            order_id: Order ID to cancel
            
        Returns:
            Dict[str, Any]: Cancellation response
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.delete(
                f"{self.base_url}/accounts/{account_hash}/orders/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            
            logger.info(f"Successfully cancelled order {order_id}")
            
            return {
                "status": "success",
                "message": f"Order {order_id} cancelled successfully"
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error cancelling order: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to cancel order: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise
    
    async def get_order(self, account_hash: str, order_id: str) -> SchwabOrder:
        """
        Get details for a specific order.
        
        Args:
            account_hash: Account hash identifier
            order_id: Order ID to retrieve
            
        Returns:
            SchwabOrder: Order details
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_hash}/orders/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            order = SchwabOrder.from_schwab_data(data)
            order.account_id = account_hash
            
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
        account_hash: str,
        max_results: int = 3000,
        from_entered_time: Optional[datetime] = None,
        to_entered_time: Optional[datetime] = None,
        status: Optional[OrderStatus] = None
    ) -> List[SchwabOrder]:
        """
        Get orders for an account.
        
        Args:
            account_hash: Account hash identifier
            max_results: Maximum number of orders to return
            from_entered_time: Start date for order search
            to_entered_time: End date for order search  
            status: Filter by order status
            
        Returns:
            List[SchwabOrder]: List of orders
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {
                "maxResults": max_results
            }
            
            # Add date filters
            if from_entered_time:
                params["fromEnteredTime"] = from_entered_time.strftime("%Y-%m-%d")
            if to_entered_time:
                params["toEnteredTime"] = to_entered_time.strftime("%Y-%m-%d")
            if status:
                params["status"] = status.value
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_hash}/orders",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse orders
            orders = []
            for order_data in data:
                try:
                    order = SchwabOrder.from_schwab_data(order_data)
                    order.account_id = account_hash
                    orders.append(order)
                except Exception as e:
                    logger.warning(f"Failed to parse order: {e}")
            
            logger.info(f"Retrieved {len(orders)} orders for account")
            return orders
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting orders: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get orders: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise
    
    async def replace_order(self, account_hash: str, order_id: str, new_order: SchwabOrder) -> Dict[str, Any]:
        """
        Replace an existing order with a new one.
        
        Args:
            account_hash: Account hash identifier
            order_id: Order ID to replace
            new_order: New order details
            
        Returns:
            Dict[str, Any]: Replacement response
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            order_data = new_order.to_schwab_format()
            
            response = await client.put(
                f"{self.base_url}/accounts/{account_hash}/orders/{order_id}",
                headers=headers,
                json=order_data
            )
            response.raise_for_status()
            
            logger.info(f"Successfully replaced order {order_id}")
            
            return {
                "status": "success",
                "message": f"Order {order_id} replaced successfully"
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error replacing order: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to replace order: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error replacing order: {e}")
            raise