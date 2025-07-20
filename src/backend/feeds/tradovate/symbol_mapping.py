"""
Tradovate Symbol Mapping and Market Data Utilities

Provides comprehensive symbol information, contract specifications,
and market data utilities for futures trading.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, time
from enum import Enum
import re


class Exchange(Enum):
    """Major futures exchanges"""
    CME = "CME"
    CBOT = "CBOT"
    NYMEX = "NYMEX"
    COMEX = "COMEX"
    ICE = "ICE"


class ContractMonth(Enum):
    """Contract month codes"""
    JANUARY = "F"
    FEBRUARY = "G"
    MARCH = "H"
    APRIL = "J"
    MAY = "K"
    JUNE = "M"
    JULY = "N"
    AUGUST = "Q"
    SEPTEMBER = "U"
    OCTOBER = "V"
    NOVEMBER = "X"
    DECEMBER = "Z"


class SymbolInfo:
    """Comprehensive futures symbol information"""
    
    def __init__(
        self,
        symbol: str,
        name: str,
        exchange: Exchange,
        contract_size: int,
        tick_size: float,
        tick_value: float,
        currency: str = "USD",
        session_times: Optional[str] = None,
        margin_requirement: Optional[float] = None,
        sector: Optional[str] = None,
        description: Optional[str] = None
    ):
        self.symbol = symbol
        self.name = name
        self.exchange = exchange
        self.contract_size = contract_size
        self.tick_size = tick_size
        self.tick_value = tick_value
        self.currency = currency
        self.session_times = session_times
        self.margin_requirement = margin_requirement
        self.sector = sector
        self.description = description
    
    @property
    def point_value(self) -> float:
        """Calculate point value (tick_value / tick_size)"""
        return self.tick_value / self.tick_size
    
    @property
    def minimum_price_movement(self) -> float:
        """Minimum price movement in dollars"""
        return self.tick_value
    
    def format_price(self, price: float) -> str:
        """Format price according to symbol's tick size"""
        decimals = len(str(self.tick_size).split('.')[-1]) if '.' in str(self.tick_size) else 0
        return f"{price:.{decimals}f}"
    
    def calculate_pnl(self, entry_price: float, exit_price: float, quantity: int) -> float:
        """Calculate P&L for a trade"""
        price_diff = exit_price - entry_price
        return price_diff * self.point_value * quantity
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange.value,
            "contract_size": self.contract_size,
            "tick_size": self.tick_size,
            "tick_value": self.tick_value,
            "point_value": self.point_value,
            "currency": self.currency,
            "session_times": self.session_times,
            "margin_requirement": self.margin_requirement,
            "sector": self.sector,
            "description": self.description
        }


class TradovateSymbolMapping:
    """
    Comprehensive symbol mapping for Tradovate futures trading.
    
    Provides symbol information, contract specifications,
    and market data utilities for all major futures contracts.
    """
    
    # Major Index Futures
    INDEX_FUTURES = {
        "ES": SymbolInfo(
            symbol="ES",
            name="E-mini S&P 500",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.25,
            tick_value=12.50,
            session_times="17:00-16:00 ET",
            margin_requirement=12000,
            sector="Equity Index",
            description="Most liquid equity index future"
        ),
        "NQ": SymbolInfo(
            symbol="NQ",
            name="E-mini NASDAQ-100",
            exchange=Exchange.CME,
            contract_size=20,
            tick_size=0.25,
            tick_value=5.00,
            session_times="17:00-16:00 ET",
            margin_requirement=16000,
            sector="Equity Index",
            description="Technology-heavy index future"
        ),
        "YM": SymbolInfo(
            symbol="YM",
            name="E-mini Dow Jones",
            exchange=Exchange.CBOT,
            contract_size=5,
            tick_size=1.00,
            tick_value=5.00,
            session_times="17:00-16:00 ET",
            margin_requirement=8000,
            sector="Equity Index",
            description="Price-weighted industrial average"
        ),
        "RTY": SymbolInfo(
            symbol="RTY",
            name="E-mini Russell 2000",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.10,
            tick_value=5.00,
            session_times="17:00-16:00 ET",
            margin_requirement=7500,
            sector="Equity Index",
            description="Small-cap equity index"
        )
    }
    
    # Bond Futures
    BOND_FUTURES = {
        "ZB": SymbolInfo(
            symbol="ZB",
            name="30-Year T-Bond",
            exchange=Exchange.CBOT,
            contract_size=100000,
            tick_size=0.03125,  # 1/32 of a point
            tick_value=31.25,
            session_times="17:00-16:00 ET",
            margin_requirement=4500,
            sector="Fixed Income",
            description="Long-term treasury bond future"
        ),
        "ZN": SymbolInfo(
            symbol="ZN",
            name="10-Year T-Note",
            exchange=Exchange.CBOT,
            contract_size=100000,
            tick_size=0.015625,  # 1/64 of a point
            tick_value=15.625,
            session_times="17:00-16:00 ET",
            margin_requirement=1500,
            sector="Fixed Income",
            description="Medium-term treasury note"
        ),
        "ZF": SymbolInfo(
            symbol="ZF",
            name="5-Year T-Note",
            exchange=Exchange.CBOT,
            contract_size=100000,
            tick_size=0.0078125,  # 1/128 of a point
            tick_value=7.8125,
            session_times="17:00-16:00 ET",
            margin_requirement=1100,
            sector="Fixed Income",
            description="Short-term treasury note"
        )
    }
    
    # Energy Futures
    ENERGY_FUTURES = {
        "CL": SymbolInfo(
            symbol="CL",
            name="Crude Oil",
            exchange=Exchange.NYMEX,
            contract_size=1000,  # 1000 barrels
            tick_size=0.01,
            tick_value=10.00,
            session_times="17:00-16:00 ET",
            margin_requirement=4500,
            sector="Energy",
            description="West Texas Intermediate crude oil"
        ),
        "NG": SymbolInfo(
            symbol="NG",
            name="Natural Gas",
            exchange=Exchange.NYMEX,
            contract_size=10000,  # 10,000 MMBtu
            tick_size=0.001,
            tick_value=10.00,
            session_times="17:00-16:00 ET",
            margin_requirement=2200,
            sector="Energy",
            description="Henry Hub natural gas"
        ),
        "RB": SymbolInfo(
            symbol="RB",
            name="RBOB Gasoline",
            exchange=Exchange.NYMEX,
            contract_size=42000,  # 42,000 gallons
            tick_size=0.0001,
            tick_value=4.20,
            session_times="17:00-16:00 ET",
            margin_requirement=3300,
            sector="Energy",
            description="Reformulated gasoline blendstock"
        )
    }
    
    # Metal Futures
    METAL_FUTURES = {
        "GC": SymbolInfo(
            symbol="GC",
            name="Gold",
            exchange=Exchange.COMEX,
            contract_size=100,  # 100 troy ounces
            tick_size=0.10,
            tick_value=10.00,
            session_times="17:00-16:00 ET",
            margin_requirement=8500,
            sector="Precious Metals",
            description="Gold futures contract"
        ),
        "SI": SymbolInfo(
            symbol="SI",
            name="Silver",
            exchange=Exchange.COMEX,
            contract_size=5000,  # 5,000 troy ounces
            tick_size=0.005,
            tick_value=25.00,
            session_times="17:00-16:00 ET",
            margin_requirement=14000,
            sector="Precious Metals",
            description="Silver futures contract"
        ),
        "HG": SymbolInfo(
            symbol="HG",
            name="Copper",
            exchange=Exchange.COMEX,
            contract_size=25000,  # 25,000 pounds
            tick_size=0.0005,
            tick_value=12.50,
            session_times="17:00-16:00 ET",
            margin_requirement=3300,
            sector="Industrial Metals",
            description="High-grade copper"
        )
    }
    
    # Agricultural Futures
    AGRICULTURAL_FUTURES = {
        "ZC": SymbolInfo(
            symbol="ZC",
            name="Corn",
            exchange=Exchange.CBOT,
            contract_size=5000,  # 5,000 bushels
            tick_size=0.0025,  # 1/4 cent
            tick_value=12.50,
            session_times="19:00-07:20/08:30-13:20 CT",
            margin_requirement=1500,
            sector="Grains",
            description="No. 2 Yellow Corn"
        ),
        "ZS": SymbolInfo(
            symbol="ZS",
            name="Soybeans",
            exchange=Exchange.CBOT,
            contract_size=5000,  # 5,000 bushels
            tick_size=0.0025,  # 1/4 cent
            tick_value=12.50,
            session_times="19:00-07:20/08:30-13:20 CT",
            margin_requirement=2200,
            sector="Grains",
            description="No. 1 Yellow Soybeans"
        ),
        "ZW": SymbolInfo(
            symbol="ZW",
            name="Wheat",
            exchange=Exchange.CBOT,
            contract_size=5000,  # 5,000 bushels
            tick_size=0.0025,  # 1/4 cent
            tick_value=12.50,
            session_times="19:00-07:20/08:30-13:20 CT",
            margin_requirement=1800,
            sector="Grains",
            description="No. 2 Soft Red Winter Wheat"
        )
    }
    
    # Currency Futures
    CURRENCY_FUTURES = {
        "6E": SymbolInfo(
            symbol="6E",
            name="Euro FX",
            exchange=Exchange.CME,
            contract_size=125000,  # 125,000 EUR
            tick_size=0.00005,
            tick_value=6.25,
            session_times="17:00-16:00 ET",
            margin_requirement=2300,
            sector="Currency",
            description="Euro/US Dollar exchange rate"
        ),
        "6B": SymbolInfo(
            symbol="6B",
            name="British Pound",
            exchange=Exchange.CME,
            contract_size=62500,  # 62,500 GBP
            tick_size=0.0001,
            tick_value=6.25,
            session_times="17:00-16:00 ET",
            margin_requirement=2200,
            sector="Currency",
            description="British Pound/US Dollar"
        ),
        "6J": SymbolInfo(
            symbol="6J",
            name="Japanese Yen",
            exchange=Exchange.CME,
            contract_size=12500000,  # 12,500,000 JPY
            tick_size=0.0000005,
            tick_value=6.25,
            session_times="17:00-16:00 ET",
            margin_requirement=1800,
            sector="Currency",
            description="Japanese Yen/US Dollar"
        )
    }
    
    def __init__(self):
        """Initialize symbol mapping with all futures contracts"""
        self._symbols = {}
        self._symbols.update(self.INDEX_FUTURES)
        self._symbols.update(self.BOND_FUTURES)
        self._symbols.update(self.ENERGY_FUTURES)
        self._symbols.update(self.METAL_FUTURES)
        self._symbols.update(self.AGRICULTURAL_FUTURES)
        self._symbols.update(self.CURRENCY_FUTURES)
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get symbol information for a futures contract.
        
        Args:
            symbol: Futures symbol (e.g., 'ES', 'NQ', 'CL')
            
        Returns:
            SymbolInfo object or None if not found
        """
        return self._symbols.get(symbol.upper())
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if symbol is valid and supported.
        
        Args:
            symbol: Futures symbol to validate
            
        Returns:
            True if symbol is valid
        """
        return symbol.upper() in self._symbols
    
    def get_all_symbols(self) -> List[str]:
        """Get list of all supported symbols"""
        return list(self._symbols.keys())
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """
        Get symbols filtered by sector.
        
        Args:
            sector: Sector name (e.g., 'Equity Index', 'Energy')
            
        Returns:
            List of symbols in the sector
        """
        return [
            symbol for symbol, info in self._symbols.items()
            if info.sector == sector
        ]
    
    def get_symbols_by_exchange(self, exchange: Exchange) -> List[str]:
        """
        Get symbols filtered by exchange.
        
        Args:
            exchange: Exchange enum value
            
        Returns:
            List of symbols on the exchange
        """
        return [
            symbol for symbol, info in self._symbols.items()
            if info.exchange == exchange
        ]
    
    def format_price(self, symbol: str, price: float) -> str:
        """
        Format price according to symbol's tick size.
        
        Args:
            symbol: Futures symbol
            price: Price to format
            
        Returns:
            Formatted price string
        """
        info = self.get_symbol_info(symbol)
        if not info:
            return f"{price:.2f}"
        
        return info.format_price(price)
    
    def calculate_pnl(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: int
    ) -> Optional[float]:
        """
        Calculate P&L for a trade.
        
        Args:
            symbol: Futures symbol
            entry_price: Entry price
            exit_price: Exit price
            quantity: Number of contracts (positive for long, negative for short)
            
        Returns:
            P&L in dollars or None if symbol not found
        """
        info = self.get_symbol_info(symbol)
        if not info:
            return None
        
        return info.calculate_pnl(entry_price, exit_price, quantity)
    
    def get_margin_requirement(self, symbol: str) -> Optional[float]:
        """
        Get margin requirement for a symbol.
        
        Args:
            symbol: Futures symbol
            
        Returns:
            Margin requirement in dollars or None if not available
        """
        info = self.get_symbol_info(symbol)
        return info.margin_requirement if info else None
    
    def validate_price(self, symbol: str, price: float) -> bool:
        """
        Validate that price conforms to symbol's tick size.
        
        Args:
            symbol: Futures symbol
            price: Price to validate
            
        Returns:
            True if price is valid
        """
        info = self.get_symbol_info(symbol)
        if not info:
            return False
        
        # Check if price is a multiple of tick size
        remainder = price % info.tick_size
        return abs(remainder) < 1e-10 or abs(remainder - info.tick_size) < 1e-10
    
    def round_to_tick(self, symbol: str, price: float) -> Optional[float]:
        """
        Round price to nearest valid tick.
        
        Args:
            symbol: Futures symbol
            price: Price to round
            
        Returns:
            Rounded price or None if symbol not found
        """
        info = self.get_symbol_info(symbol)
        if not info:
            return None
        
        # Round to nearest tick
        ticks = round(price / info.tick_size)
        return ticks * info.tick_size
    
    def get_contract_specifications(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get complete contract specifications.
        
        Args:
            symbol: Futures symbol
            
        Returns:
            Dictionary with contract specifications
        """
        info = self.get_symbol_info(symbol)
        return info.dict() if info else None
    
    def search_symbols(self, query: str) -> List[str]:
        """
        Search symbols by name or symbol.
        
        Args:
            query: Search query
            
        Returns:
            List of matching symbols
        """
        query = query.lower()
        matches = []
        
        for symbol, info in self._symbols.items():
            if (query in symbol.lower() or 
                query in info.name.lower() or
                (info.description and query in info.description.lower())):
                matches.append(symbol)
        
        return matches
    
    def get_most_liquid_symbols(self, count: int = 10) -> List[str]:
        """
        Get most liquid symbols (commonly traded).
        
        Args:
            count: Number of symbols to return
            
        Returns:
            List of most liquid symbols
        """
        # Return commonly traded symbols in order of liquidity
        liquid_symbols = [
            "ES",   # E-mini S&P 500
            "NQ",   # E-mini NASDAQ
            "CL",   # Crude Oil
            "GC",   # Gold
            "YM",   # E-mini Dow
            "RTY",  # E-mini Russell 2000
            "ZB",   # 30-Year T-Bond
            "ZN",   # 10-Year T-Note
            "6E",   # Euro FX
            "NG",   # Natural Gas
            "SI",   # Silver
            "ZC",   # Corn
            "ZS",   # Soybeans
            "6B",   # British Pound
            "HG"    # Copper
        ]
        
        return liquid_symbols[:count]
    
    def is_session_active(self, symbol: str, current_time: datetime) -> bool:
        """
        Check if trading session is active for symbol.
        
        Args:
            symbol: Futures symbol
            current_time: Current datetime
            
        Returns:
            True if session is active (simplified implementation)
        """
        # Simplified: most futures trade nearly 24 hours
        # In production, would parse session_times and check actual hours
        info = self.get_symbol_info(symbol)
        if not info:
            return False
        
        # For now, assume most contracts trade Sunday 17:00 - Friday 16:00 ET
        weekday = current_time.weekday()
        hour = current_time.hour
        
        # Monday-Friday: 17:00 previous day to 16:00 current day
        if weekday < 5:  # Monday-Friday
            return True
        elif weekday == 6:  # Sunday
            return hour >= 17
        else:  # Saturday
            return False