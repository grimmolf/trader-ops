"""
Internal Paper Trading Engine for TraderTerminal

Simulates realistic order execution with:
- Real market data integration
- Realistic slippage calculation
- Commission and fee simulation
- Market impact modeling
- Liquidity simulation
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
import math

from .paper_models import (
    PaperTradingAccount, PaperOrder, Fill, OrderStatus, AssetType,
    MarketDataSnapshot, PaperTradingMetrics
)

logger = logging.getLogger(__name__)


class MarketConditions:
    """Market condition simulation for realistic execution"""
    
    def __init__(self):
        self.volatility_multiplier = 1.0
        self.liquidity_factor = 1.0
        self.market_session = "regular"  # regular, extended, closed
        self.news_impact = 0.0  # -1.0 to 1.0
        
    def update_from_time(self, timestamp: datetime) -> None:
        """Update market conditions based on time of day"""
        hour = timestamp.hour
        
        # Market session
        if 9 <= hour < 16:  # 9:30 AM - 4:00 PM ET (approximate)
            self.market_session = "regular"
            self.liquidity_factor = 1.0
        elif 4 <= hour < 9 or 16 <= hour < 20:
            self.market_session = "extended"
            self.liquidity_factor = 0.3  # Lower liquidity
        else:
            self.market_session = "closed"
            self.liquidity_factor = 0.1  # Very low liquidity
        
        # Volatility patterns
        if hour in [9, 10, 15, 16]:  # Market open/close hours
            self.volatility_multiplier = 1.5
        elif hour in [11, 12, 13, 14]:  # Mid-day quiet period
            self.volatility_multiplier = 0.7
        else:
            self.volatility_multiplier = 1.0


class SlippageCalculator:
    """Calculate realistic slippage based on various factors"""
    
    @staticmethod
    def calculate_slippage(
        symbol: str,
        quantity: Decimal,
        order_type: str,
        market_conditions: MarketConditions,
        asset_type: AssetType
    ) -> Decimal:
        """Calculate slippage as a percentage of price"""
        
        # Base slippage by asset type
        base_slippage = {
            AssetType.STOCK: 0.0001,      # 0.01%
            AssetType.FUTURE: 0.0005,     # 0.05%
            AssetType.OPTION: 0.002,      # 0.20%
            AssetType.CRYPTO: 0.001,      # 0.10%
            AssetType.FOREX: 0.00005      # 0.005%
        }.get(asset_type, 0.001)
        
        # Adjust for market conditions
        liquidity_adjustment = (2.0 - market_conditions.liquidity_factor)
        volatility_adjustment = market_conditions.volatility_multiplier
        
        # Size impact (larger orders have more slippage)
        size_impact = min(float(quantity) / 1000, 0.01)  # Max 1% additional
        
        # Order type impact
        order_type_multiplier = {
            "market": 1.0,
            "limit": 0.2,      # Limit orders have less slippage
            "stop": 1.5,       # Stop orders have more slippage
            "stop_limit": 1.2
        }.get(order_type, 1.0)
        
        # Random component (market noise)
        random_factor = random.uniform(0.5, 1.5)
        
        total_slippage = (
            base_slippage * 
            liquidity_adjustment * 
            volatility_adjustment * 
            order_type_multiplier * 
            (1 + size_impact) * 
            random_factor
        )
        
        return Decimal(str(total_slippage))


class CommissionCalculator:
    """Calculate realistic commissions and fees"""
    
    @staticmethod
    def calculate_commission(
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        asset_type: AssetType,
        broker: str = "simulator"
    ) -> Dict[str, Decimal]:
        """Calculate commission and fees"""
        
        if asset_type == AssetType.FUTURE:
            # Futures commission (per contract)
            base_commission = Decimal("2.25")
            exchange_fee = Decimal("1.25")
            regulatory_fee = Decimal("0.02")
            
            commission = base_commission * quantity
            fees = (exchange_fee + regulatory_fee) * quantity
            
        elif asset_type == AssetType.OPTION:
            # Options commission (per contract)
            base_commission = Decimal("0.65")
            exchange_fee = Decimal("0.15")
            regulatory_fee = Decimal("0.02")
            
            commission = base_commission * quantity
            fees = (exchange_fee + regulatory_fee) * quantity
            
        elif asset_type == AssetType.STOCK:
            # Stock commission (many brokers are now free)
            if broker in ["tastytrade_sandbox", "simulator"]:
                commission = Decimal("0")  # Commission-free
                regulatory_fee = Decimal("0.01") * quantity  # SEC fee
                fees = regulatory_fee
            else:
                commission = Decimal("0.005") * quantity  # $0.005 per share
                fees = Decimal("0.01") * quantity
                
        elif asset_type == AssetType.CRYPTO:
            # Crypto trading fees (percentage of notional)
            notional = price * quantity
            commission = notional * Decimal("0.001")  # 0.1%
            fees = Decimal("0")
            
        else:
            commission = Decimal("0")
            fees = Decimal("0")
        
        return {
            "commission": commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "fees": fees.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        }


class InternalPaperTradingEngine:
    """
    Internal paper trading engine with realistic simulation
    
    Features:
    - Real market data integration
    - Realistic slippage calculation
    - Commission and fee simulation
    - Market impact modeling
    - Order execution delay simulation
    """
    
    def __init__(self, testing_mode: bool = False):
        self.market_data_cache: Dict[str, MarketDataSnapshot] = {}
        self.market_conditions = MarketConditions()
        self.slippage_calc = SlippageCalculator()
        self.commission_calc = CommissionCalculator()
        self._initialized = False
        self.testing_mode = testing_mode  # Bypass market hours in testing
        
        # Execution parameters
        self.execution_delay_ms = (50, 200)  # Min/max execution delay
        self.market_data_update_interval = 1.0  # seconds
        
    async def initialize(self) -> None:
        """Initialize the paper trading engine"""
        if self._initialized:
            return
            
        try:
            # Start market data simulation
            asyncio.create_task(self._market_data_simulation_loop())
            
            self._initialized = True
            logger.info("Internal paper trading engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize paper trading engine: {e}")
            raise
    
    async def execute_paper_order(
        self, 
        order: PaperOrder, 
        account: PaperTradingAccount
    ) -> Dict[str, Any]:
        """Execute a paper trading order with realistic simulation"""
        
        try:
            # Update market conditions
            self.market_conditions.update_from_time(datetime.now(timezone.utc))
            
            # Get or simulate market data
            market_data = await self._get_market_data(order.symbol)
            if not market_data:
                return {
                    "status": "error",
                    "message": f"No market data available for {order.symbol}"
                }
            
            # Validate order
            validation_result = await self._validate_order(order, account, market_data)
            if validation_result["status"] != "success":
                return validation_result
            
            # Simulate execution delay
            delay_ms = random.randint(*self.execution_delay_ms)
            await asyncio.sleep(delay_ms / 1000.0)
            
            # Calculate fill price with slippage
            fill_price = await self._calculate_fill_price(order, market_data)
            
            # Calculate commission and fees
            costs = self.commission_calc.calculate_commission(
                order.symbol,
                order.quantity,
                fill_price,
                order.asset_type,
                "simulator"
            )
            
            # Create fill
            fill = Fill(
                order_id=order.id,
                account_id=account.id,
                symbol=order.symbol,
                side="buy" if order.is_buy_order() else "sell",
                quantity=order.quantity,
                price=fill_price,
                commission=costs["commission"],
                fees=costs["fees"],
                slippage=abs(fill_price - market_data.last),
                timestamp=datetime.now(timezone.utc),
                broker="simulator"
            )
            
            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_fill_price = fill_price
            order.filled_at = datetime.now(timezone.utc)
            
            return {
                "status": "success",
                "order_id": order.id,
                "fill": {
                    "price": float(fill.price),
                    "quantity": float(fill.quantity),
                    "commission": float(fill.commission),
                    "fees": float(fill.fees),
                    "slippage": float(fill.slippage),
                    "timestamp": fill.timestamp.isoformat()
                },
                "market_data": {
                    "bid": float(market_data.bid),
                    "ask": float(market_data.ask),
                    "last": float(market_data.last),
                    "spread": float(market_data.spread)
                },
                "execution_details": {
                    "execution_delay_ms": delay_ms,
                    "market_conditions": {
                        "session": self.market_conditions.market_session,
                        "liquidity_factor": self.market_conditions.liquidity_factor,
                        "volatility_multiplier": self.market_conditions.volatility_multiplier
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to execute paper order {order.id}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "order_id": order.id
            }
    
    async def _validate_order(
        self, 
        order: PaperOrder, 
        account: PaperTradingAccount,
        market_data: MarketDataSnapshot
    ) -> Dict[str, Any]:
        """Validate order before execution"""
        
        # Check market hours (skip in testing mode)
        if not self.testing_mode and self.market_conditions.market_session == "closed":
            return {
                "status": "rejected",
                "reason": "Market is closed"
            }
        
        # Check buying power for buy orders
        if order.is_buy_order():
            required_capital = market_data.ask * order.quantity
            multiplier = self._get_multiplier(order.symbol)
            total_required = required_capital * multiplier
            
            if total_required > account.buying_power:
                return {
                    "status": "rejected",
                    "reason": f"Insufficient buying power. Required: ${total_required}, Available: ${account.buying_power}"
                }
        
        # Check position limits for futures
        if order.asset_type == AssetType.FUTURE:
            current_position = account.positions.get(order.symbol)
            if current_position:
                new_quantity = current_position.quantity
                if order.is_buy_order():
                    new_quantity += order.quantity
                else:
                    new_quantity -= order.quantity
                
                # Check position size limits (example: max 10 contracts)
                if abs(new_quantity) > 10:
                    return {
                        "status": "rejected",
                        "reason": f"Position size limit exceeded. Max: 10 contracts"
                    }
        
        # Check minimum price increment
        if order.price:
            tick_size = self._get_tick_size(order.symbol)
            price_remainder = order.price % tick_size
            if price_remainder != 0:
                return {
                    "status": "rejected",
                    "reason": f"Price must be in increments of {tick_size}"
                }
        
        return {"status": "success"}
    
    async def _calculate_fill_price(
        self, 
        order: PaperOrder, 
        market_data: MarketDataSnapshot
    ) -> Decimal:
        """Calculate realistic fill price including slippage"""
        
        # Base price
        if order.order_type.value == "market":
            if order.is_buy_order():
                base_price = market_data.ask
            else:
                base_price = market_data.bid
        elif order.order_type.value == "limit":
            # For paper trading, assume limit orders fill at limit price
            base_price = order.price or market_data.last
        else:
            base_price = market_data.last
        
        # Calculate slippage
        slippage_pct = self.slippage_calc.calculate_slippage(
            order.symbol,
            order.quantity,
            order.order_type.value,
            self.market_conditions,
            order.asset_type
        )
        
        # Apply slippage
        slippage_amount = base_price * slippage_pct
        
        if order.is_buy_order():
            # Buy orders get worse prices (higher)
            fill_price = base_price + slippage_amount
        else:
            # Sell orders get worse prices (lower)
            fill_price = base_price - slippage_amount
        
        # Round to appropriate tick size
        tick_size = self._get_tick_size(order.symbol)
        fill_price = (fill_price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size
        
        return fill_price
    
    async def _get_market_data(self, symbol: str) -> Optional[MarketDataSnapshot]:
        """Get market data for symbol (real or simulated)"""
        
        # Check cache first
        if symbol in self.market_data_cache:
            cached_data = self.market_data_cache[symbol]
            # Use cached data if less than 5 seconds old
            if (datetime.now(timezone.utc) - cached_data.timestamp).total_seconds() < 5:
                return cached_data
        
        # Try to get real market data (would integrate with actual data feeds)
        try:
            # TODO: Integrate with real market data feeds
            # For now, simulate realistic market data
            market_data = await self._simulate_market_data(symbol)
            self.market_data_cache[symbol] = market_data
            return market_data
            
        except Exception as e:
            logger.warning(f"Failed to get market data for {symbol}: {e}")
            return None
    
    async def _simulate_market_data(self, symbol: str) -> MarketDataSnapshot:
        """Simulate realistic market data"""
        
        # Base prices for common symbols
        base_prices = {
            "ES": Decimal("4500"),
            "NQ": Decimal("15800"),
            "YM": Decimal("35000"),
            "RTY": Decimal("2000"),
            "GC": Decimal("2000"),
            "SI": Decimal("25"),
            "CL": Decimal("80"),
            "AAPL": Decimal("180"),
            "MSFT": Decimal("350"),
            "TSLA": Decimal("200"),
            "SPY": Decimal("450"),
            "QQQ": Decimal("380")
        }
        
        base_price = base_prices.get(symbol, Decimal("100"))
        
        # Add random movement (simulate market volatility)
        volatility = 0.02 * self.market_conditions.volatility_multiplier  # 2% volatility
        random_change = random.uniform(-volatility, volatility)
        
        current_price = base_price * (1 + Decimal(str(random_change)))
        
        # Calculate bid/ask spread
        spread_pct = {
            AssetType.FUTURE: 0.0001,  # 0.01%
            AssetType.STOCK: 0.0005,   # 0.05%
            AssetType.OPTION: 0.01,    # 1%
        }.get(self._determine_asset_type(symbol), 0.001)
        
        spread = current_price * Decimal(str(spread_pct))
        
        bid = current_price - (spread / 2)
        ask = current_price + (spread / 2)
        
        # Round to appropriate tick sizes
        tick_size = self._get_tick_size(symbol)
        bid = (bid / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size
        ask = (ask / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size
        current_price = (current_price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size
        
        return MarketDataSnapshot(
            symbol=symbol,
            bid=bid,
            ask=ask,
            last=current_price,
            volume=random.randint(1000, 100000),
            timestamp=datetime.now(timezone.utc)
        )
    
    def _determine_asset_type(self, symbol: str) -> AssetType:
        """Determine asset type from symbol"""
        if symbol in ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL", "NG"]:
            return AssetType.FUTURE
        elif "/" in symbol or symbol.endswith("C") or symbol.endswith("P"):
            return AssetType.OPTION
        elif symbol in ["BTC", "ETH", "BTC-USD", "ETH-USD"]:
            return AssetType.CRYPTO
        else:
            return AssetType.STOCK
    
    def _get_tick_size(self, symbol: str) -> Decimal:
        """Get minimum price increment for symbol"""
        tick_sizes = {
            "ES": Decimal("0.25"),
            "NQ": Decimal("0.25"),
            "YM": Decimal("1.00"),
            "RTY": Decimal("0.10"),
            "GC": Decimal("0.10"),
            "SI": Decimal("0.005"),
            "CL": Decimal("0.01"),
            "NG": Decimal("0.001")
        }
        
        return tick_sizes.get(symbol, Decimal("0.01"))
    
    def _get_multiplier(self, symbol: str) -> Decimal:
        """Get contract multiplier for symbol"""
        multipliers = {
            "ES": Decimal("50"),
            "NQ": Decimal("20"),
            "YM": Decimal("5"),
            "RTY": Decimal("50"),
            "GC": Decimal("100"),
            "SI": Decimal("5000"),
            "CL": Decimal("1000"),
            "NG": Decimal("10000")
        }
        
        return multipliers.get(symbol, Decimal("1"))
    
    async def _market_data_simulation_loop(self) -> None:
        """Background loop to update market data"""
        while True:
            try:
                # Update market conditions
                self.market_conditions.update_from_time(datetime.now(timezone.utc))
                
                # Update cached market data
                for symbol in list(self.market_data_cache.keys()):
                    # Add some random movement to cached prices
                    cached_data = self.market_data_cache[symbol]
                    
                    # Small random movement (0.1% max)
                    movement = random.uniform(-0.001, 0.001) * self.market_conditions.volatility_multiplier
                    
                    new_last = cached_data.last * (1 + Decimal(str(movement)))
                    spread = cached_data.spread
                    
                    self.market_data_cache[symbol] = MarketDataSnapshot(
                        symbol=symbol,
                        bid=new_last - (spread / 2),
                        ask=new_last + (spread / 2),
                        last=new_last,
                        volume=cached_data.volume + random.randint(10, 1000),
                        timestamp=datetime.now(timezone.utc)
                    )
                
                await asyncio.sleep(self.market_data_update_interval)
                
            except Exception as e:
                logger.error(f"Error in market data simulation loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying