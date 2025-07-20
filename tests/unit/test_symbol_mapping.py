"""
Unit tests for Tradovate symbol mapping module.

Tests symbol information, contract specifications, price formatting,
and P&L calculations for futures contracts.
"""

import pytest
from datetime import datetime
from src.backend.feeds.tradovate.symbol_mapping import (
    TradovateSymbolMapping, SymbolInfo, Exchange, ContractMonth
)


class TestSymbolInfo:
    """Test SymbolInfo class"""
    
    def test_create_symbol_info(self):
        """Test creating SymbolInfo object"""
        info = SymbolInfo(
            symbol="ES",
            name="E-mini S&P 500",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.25,
            tick_value=12.50,
            session_times="17:00-16:00 ET",
            margin_requirement=12000,
            sector="Equity Index"
        )
        
        assert info.symbol == "ES"
        assert info.name == "E-mini S&P 500"
        assert info.exchange == Exchange.CME
        assert info.contract_size == 50
        assert info.tick_size == 0.25
        assert info.tick_value == 12.50
    
    def test_point_value_calculation(self):
        """Test point value calculation"""
        info = SymbolInfo(
            symbol="ES",
            name="E-mini S&P 500",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.25,
            tick_value=12.50
        )
        
        # Point value = tick_value / tick_size = 12.50 / 0.25 = 50
        assert info.point_value == 50.0
    
    def test_price_formatting(self):
        """Test price formatting according to tick size"""
        # ES with 0.25 tick size (2 decimals)
        es_info = SymbolInfo(
            symbol="ES",
            name="E-mini S&P 500",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.25,
            tick_value=12.50
        )
        
        assert es_info.format_price(4450.25) == "4450.25"
        assert es_info.format_price(4450.0) == "4450.00"
        
        # YM with 1.0 tick size (0 decimals)
        ym_info = SymbolInfo(
            symbol="YM",
            name="E-mini Dow Jones",
            exchange=Exchange.CBOT,
            contract_size=5,
            tick_size=1.0,
            tick_value=5.0
        )
        
        assert ym_info.format_price(35000.0) == "35000"
        assert ym_info.format_price(35000.5) == "35001"  # Rounded
    
    def test_pnl_calculation(self):
        """Test P&L calculation"""
        info = SymbolInfo(
            symbol="ES",
            name="E-mini S&P 500",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.25,
            tick_value=12.50
        )
        
        # Long 1 contract: entry 4450, exit 4455 = 5 points = $250
        pnl = info.calculate_pnl(4450.0, 4455.0, 1)
        assert pnl == 250.0
        
        # Short 1 contract: entry 4450, exit 4455 = -5 points = -$250
        pnl = info.calculate_pnl(4450.0, 4455.0, -1)
        assert pnl == -250.0
        
        # Long 2 contracts: entry 4450, exit 4452.5 = 2.5 points = $250
        pnl = info.calculate_pnl(4450.0, 4452.5, 2)
        assert pnl == 250.0
    
    def test_symbol_info_dict(self):
        """Test converting SymbolInfo to dictionary"""
        info = SymbolInfo(
            symbol="ES",
            name="E-mini S&P 500",
            exchange=Exchange.CME,
            contract_size=50,
            tick_size=0.25,
            tick_value=12.50,
            margin_requirement=12000,
            sector="Equity Index"
        )
        
        info_dict = info.dict()
        
        assert info_dict["symbol"] == "ES"
        assert info_dict["name"] == "E-mini S&P 500"
        assert info_dict["exchange"] == "CME"
        assert info_dict["point_value"] == 50.0
        assert info_dict["margin_requirement"] == 12000


class TestTradovateSymbolMapping:
    """Test TradovateSymbolMapping class"""
    
    def test_mapping_initialization(self):
        """Test symbol mapping initialization"""
        mapping = TradovateSymbolMapping()
        
        # Should have symbols from all categories
        all_symbols = mapping.get_all_symbols()
        assert len(all_symbols) > 0
        
        # Should include major symbols
        assert "ES" in all_symbols
        assert "NQ" in all_symbols
        assert "CL" in all_symbols
        assert "GC" in all_symbols
    
    def test_get_symbol_info(self):
        """Test getting symbol information"""
        mapping = TradovateSymbolMapping()
        
        # Valid symbol
        es_info = mapping.get_symbol_info("ES")
        assert es_info is not None
        assert es_info.symbol == "ES"
        assert es_info.name == "E-mini S&P 500"
        assert es_info.exchange == Exchange.CME
        
        # Case insensitive
        es_info_lower = mapping.get_symbol_info("es")
        assert es_info_lower is not None
        assert es_info_lower.symbol == "ES"
        
        # Invalid symbol
        invalid_info = mapping.get_symbol_info("INVALID")
        assert invalid_info is None
    
    def test_symbol_validation(self):
        """Test symbol validation"""
        mapping = TradovateSymbolMapping()
        
        # Valid symbols
        assert mapping.is_valid_symbol("ES")
        assert mapping.is_valid_symbol("es")  # Case insensitive
        assert mapping.is_valid_symbol("NQ")
        assert mapping.is_valid_symbol("CL")
        
        # Invalid symbols
        assert not mapping.is_valid_symbol("INVALID")
        assert not mapping.is_valid_symbol("")
        assert not mapping.is_valid_symbol("123")
    
    def test_get_symbols_by_sector(self):
        """Test getting symbols by sector"""
        mapping = TradovateSymbolMapping()
        
        # Equity index symbols
        equity_symbols = mapping.get_symbols_by_sector("Equity Index")
        assert "ES" in equity_symbols
        assert "NQ" in equity_symbols
        assert "YM" in equity_symbols
        assert "RTY" in equity_symbols
        
        # Energy symbols
        energy_symbols = mapping.get_symbols_by_sector("Energy")
        assert "CL" in energy_symbols
        assert "NG" in energy_symbols
        assert "RB" in energy_symbols
        
        # Precious metals
        metal_symbols = mapping.get_symbols_by_sector("Precious Metals")
        assert "GC" in metal_symbols
        assert "SI" in metal_symbols
    
    def test_get_symbols_by_exchange(self):
        """Test getting symbols by exchange"""
        mapping = TradovateSymbolMapping()
        
        # CME symbols
        cme_symbols = mapping.get_symbols_by_exchange(Exchange.CME)
        assert "ES" in cme_symbols
        assert "NQ" in cme_symbols
        assert "RTY" in cme_symbols
        assert "6E" in cme_symbols
        
        # CBOT symbols
        cbot_symbols = mapping.get_symbols_by_exchange(Exchange.CBOT)
        assert "YM" in cbot_symbols
        assert "ZB" in cbot_symbols
        assert "ZC" in cbot_symbols
        
        # NYMEX symbols
        nymex_symbols = mapping.get_symbols_by_exchange(Exchange.NYMEX)
        assert "CL" in nymex_symbols
        assert "NG" in nymex_symbols
    
    def test_price_formatting(self):
        """Test price formatting for different symbols"""
        mapping = TradovateSymbolMapping()
        
        # ES - 0.25 tick size
        es_price = mapping.format_price("ES", 4450.25)
        assert es_price == "4450.25"
        
        # YM - 1.0 tick size
        ym_price = mapping.format_price("YM", 35000.0)
        assert ym_price == "35000"
        
        # Invalid symbol - default formatting
        invalid_price = mapping.format_price("INVALID", 123.456)
        assert invalid_price == "123.46"
    
    def test_pnl_calculation(self):
        """Test P&L calculation for different symbols"""
        mapping = TradovateSymbolMapping()
        
        # ES: 1 contract, 5 point move = $250
        es_pnl = mapping.calculate_pnl("ES", 4450.0, 4455.0, 1)
        assert es_pnl == 250.0
        
        # NQ: 1 contract, 10 point move = $200 (20 * 10)
        nq_pnl = mapping.calculate_pnl("NQ", 15800.0, 15810.0, 1)
        assert nq_pnl == 200.0
        
        # CL: 1 contract, $1 move = $1000 (1000 barrels)
        cl_pnl = mapping.calculate_pnl("CL", 70.0, 71.0, 1)
        assert cl_pnl == 1000.0
        
        # Invalid symbol
        invalid_pnl = mapping.calculate_pnl("INVALID", 100.0, 101.0, 1)
        assert invalid_pnl is None
    
    def test_margin_requirements(self):
        """Test margin requirement retrieval"""
        mapping = TradovateSymbolMapping()
        
        # ES margin
        es_margin = mapping.get_margin_requirement("ES")
        assert es_margin == 12000
        
        # NQ margin
        nq_margin = mapping.get_margin_requirement("NQ")
        assert nq_margin == 16000
        
        # Invalid symbol
        invalid_margin = mapping.get_margin_requirement("INVALID")
        assert invalid_margin is None
    
    def test_price_validation(self):
        """Test price validation against tick size"""
        mapping = TradovateSymbolMapping()
        
        # ES - 0.25 tick size
        assert mapping.validate_price("ES", 4450.0)   # Valid
        assert mapping.validate_price("ES", 4450.25)  # Valid
        assert mapping.validate_price("ES", 4450.50)  # Valid
        assert mapping.validate_price("ES", 4450.75)  # Valid
        assert not mapping.validate_price("ES", 4450.1)   # Invalid
        assert not mapping.validate_price("ES", 4450.333) # Invalid
        
        # YM - 1.0 tick size
        assert mapping.validate_price("YM", 35000.0)  # Valid
        assert mapping.validate_price("YM", 35001.0)  # Valid
        assert not mapping.validate_price("YM", 35000.5)  # Invalid
        
        # Invalid symbol
        assert not mapping.validate_price("INVALID", 100.0)
    
    def test_round_to_tick(self):
        """Test rounding prices to valid ticks"""
        mapping = TradovateSymbolMapping()
        
        # ES - 0.25 tick size
        assert mapping.round_to_tick("ES", 4450.1) == 4450.0
        assert mapping.round_to_tick("ES", 4450.2) == 4450.25
        assert mapping.round_to_tick("ES", 4450.4) == 4450.5
        assert mapping.round_to_tick("ES", 4450.6) == 4450.5
        
        # YM - 1.0 tick size
        assert mapping.round_to_tick("YM", 35000.3) == 35000.0
        assert mapping.round_to_tick("YM", 35000.7) == 35001.0
        
        # Invalid symbol
        assert mapping.round_to_tick("INVALID", 100.1) is None
    
    def test_contract_specifications(self):
        """Test getting complete contract specifications"""
        mapping = TradovateSymbolMapping()
        
        es_specs = mapping.get_contract_specifications("ES")
        assert es_specs is not None
        assert es_specs["symbol"] == "ES"
        assert es_specs["contract_size"] == 50
        assert es_specs["tick_size"] == 0.25
        assert es_specs["tick_value"] == 12.50
        assert es_specs["point_value"] == 50.0
        assert es_specs["exchange"] == "CME"
        
        # Invalid symbol
        invalid_specs = mapping.get_contract_specifications("INVALID")
        assert invalid_specs is None
    
    def test_symbol_search(self):
        """Test symbol search functionality"""
        mapping = TradovateSymbolMapping()
        
        # Search by symbol
        es_results = mapping.search_symbols("ES")
        assert "ES" in es_results
        
        # Search by name
        sp500_results = mapping.search_symbols("S&P")
        assert "ES" in sp500_results
        
        # Search by description
        liquid_results = mapping.search_symbols("liquid")
        assert "ES" in liquid_results
        
        # Case insensitive search
        gold_results = mapping.search_symbols("GOLD")
        assert "GC" in gold_results
        
        # No matches
        no_results = mapping.search_symbols("NONEXISTENT")
        assert len(no_results) == 0
    
    def test_most_liquid_symbols(self):
        """Test getting most liquid symbols"""
        mapping = TradovateSymbolMapping()
        
        # Default count (10)
        liquid_symbols = mapping.get_most_liquid_symbols()
        assert len(liquid_symbols) == 10
        assert "ES" in liquid_symbols
        assert "NQ" in liquid_symbols
        assert "CL" in liquid_symbols
        
        # Custom count
        top_5 = mapping.get_most_liquid_symbols(5)
        assert len(top_5) == 5
        assert "ES" in top_5  # Should be first (most liquid)
    
    def test_session_activity(self):
        """Test session activity checking"""
        mapping = TradovateSymbolMapping()
        
        # Monday 10 AM ET (active)
        monday_10am = datetime(2024, 1, 8, 10, 0, 0)  # Monday
        assert mapping.is_session_active("ES", monday_10am)
        
        # Sunday 6 PM ET (active - Sunday evening start)
        sunday_6pm = datetime(2024, 1, 7, 18, 0, 0)  # Sunday
        assert mapping.is_session_active("ES", sunday_6pm)
        
        # Saturday (inactive)
        saturday = datetime(2024, 1, 6, 10, 0, 0)  # Saturday
        assert not mapping.is_session_active("ES", saturday)
        
        # Invalid symbol
        assert not mapping.is_session_active("INVALID", monday_10am)


class TestContractCategories:
    """Test specific contract categories"""
    
    def test_index_futures(self):
        """Test equity index futures"""
        mapping = TradovateSymbolMapping()
        
        # ES - E-mini S&P 500
        es_info = mapping.get_symbol_info("ES")
        assert es_info.contract_size == 50
        assert es_info.tick_size == 0.25
        assert es_info.tick_value == 12.50
        assert es_info.sector == "Equity Index"
        
        # NQ - E-mini NASDAQ
        nq_info = mapping.get_symbol_info("NQ")
        assert nq_info.contract_size == 20
        assert nq_info.tick_size == 0.25
        assert nq_info.tick_value == 5.00
    
    def test_energy_futures(self):
        """Test energy futures"""
        mapping = TradovateSymbolMapping()
        
        # CL - Crude Oil
        cl_info = mapping.get_symbol_info("CL")
        assert cl_info.contract_size == 1000  # 1000 barrels
        assert cl_info.tick_size == 0.01
        assert cl_info.tick_value == 10.00
        assert cl_info.sector == "Energy"
        
        # NG - Natural Gas
        ng_info = mapping.get_symbol_info("NG")
        assert ng_info.contract_size == 10000  # 10,000 MMBtu
        assert ng_info.sector == "Energy"
    
    def test_metal_futures(self):
        """Test precious metal futures"""
        mapping = TradovateSymbolMapping()
        
        # GC - Gold
        gc_info = mapping.get_symbol_info("GC")
        assert gc_info.contract_size == 100  # 100 troy ounces
        assert gc_info.tick_size == 0.10
        assert gc_info.tick_value == 10.00
        assert gc_info.sector == "Precious Metals"
        
        # SI - Silver
        si_info = mapping.get_symbol_info("SI")
        assert si_info.contract_size == 5000  # 5,000 troy ounces
        assert si_info.sector == "Precious Metals"
    
    def test_bond_futures(self):
        """Test treasury bond futures"""
        mapping = TradovateSymbolMapping()
        
        # ZB - 30-Year T-Bond
        zb_info = mapping.get_symbol_info("ZB")
        assert zb_info.contract_size == 100000
        assert zb_info.tick_size == 0.03125  # 1/32
        assert zb_info.sector == "Fixed Income"
        
        # ZN - 10-Year T-Note
        zn_info = mapping.get_symbol_info("ZN")
        assert zn_info.contract_size == 100000
        assert zn_info.tick_size == 0.015625  # 1/64
    
    def test_agricultural_futures(self):
        """Test agricultural futures"""
        mapping = TradovateSymbolMapping()
        
        # ZC - Corn
        zc_info = mapping.get_symbol_info("ZC")
        assert zc_info.contract_size == 5000  # 5,000 bushels
        assert zc_info.tick_size == 0.0025  # 1/4 cent
        assert zc_info.sector == "Grains"
        
        # ZS - Soybeans
        zs_info = mapping.get_symbol_info("ZS")
        assert zs_info.contract_size == 5000
        assert zs_info.sector == "Grains"
    
    def test_currency_futures(self):
        """Test currency futures"""
        mapping = TradovateSymbolMapping()
        
        # 6E - Euro FX
        euro_info = mapping.get_symbol_info("6E")
        assert euro_info.contract_size == 125000  # 125,000 EUR
        assert euro_info.sector == "Currency"
        
        # 6B - British Pound
        gbp_info = mapping.get_symbol_info("6B")
        assert gbp_info.contract_size == 62500  # 62,500 GBP
        assert gbp_info.sector == "Currency"


class TestPracticalUseCases:
    """Test practical trading use cases"""
    
    def test_portfolio_margin_calculation(self):
        """Test calculating total margin for a portfolio"""
        mapping = TradovateSymbolMapping()
        
        # Portfolio: 1 ES, 1 NQ, 1 CL
        positions = [
            ("ES", 1),
            ("NQ", 1), 
            ("CL", 1)
        ]
        
        total_margin = 0
        for symbol, quantity in positions:
            margin = mapping.get_margin_requirement(symbol)
            if margin:
                total_margin += margin * abs(quantity)
        
        expected = 12000 + 16000 + 4500  # ES + NQ + CL
        assert total_margin == expected
    
    def test_position_pnl_calculation(self):
        """Test calculating P&L for multiple positions"""
        mapping = TradovateSymbolMapping()
        
        # Positions with entry and current prices
        positions = [
            ("ES", 2, 4450.0, 4455.0),     # Long 2 ES
            ("NQ", -1, 15800.0, 15790.0),  # Short 1 NQ
            ("CL", 1, 70.0, 71.5)          # Long 1 CL
        ]
        
        total_pnl = 0
        for symbol, quantity, entry, current in positions:
            pnl = mapping.calculate_pnl(symbol, entry, current, quantity)
            if pnl is not None:
                total_pnl += pnl
        
        # ES: 2 * 5 points * 50 = $500
        # NQ: -1 * -10 points * 20 = $200  
        # CL: 1 * 1.5 * 1000 = $1500
        expected = 500 + 200 + 1500
        assert total_pnl == expected
    
    def test_order_price_validation(self):
        """Test validating order prices before submission"""
        mapping = TradovateSymbolMapping()
        
        orders = [
            ("ES", 4450.25),   # Valid - multiple of 0.25
            ("ES", 4450.1),    # Invalid - not multiple of 0.25
            ("YM", 35000.0),   # Valid - whole number
            ("YM", 35000.5),   # Invalid - not whole number
            ("CL", 70.01),     # Valid - multiple of 0.01
            ("CL", 70.001)     # Invalid - too many decimals
        ]
        
        valid_orders = []
        for symbol, price in orders:
            if mapping.validate_price(symbol, price):
                valid_orders.append((symbol, price))
            else:
                # Round to nearest valid tick
                rounded_price = mapping.round_to_tick(symbol, price)
                if rounded_price is not None:
                    valid_orders.append((symbol, rounded_price))
        
        assert len(valid_orders) == 6  # All orders should be made valid
        assert (("ES", 4450.25) in valid_orders)
        assert (("ES", 4450.0) in valid_orders)  # 4450.1 rounded to 4450.0
        assert (("YM", 35000.0) in valid_orders)
        assert (("YM", 35001.0) in valid_orders)  # 35000.5 rounded to 35001.0