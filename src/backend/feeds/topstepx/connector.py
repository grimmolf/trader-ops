"""
TopstepX API Connector

Complete TopstepX API integration for funded account management including:
- Real-time account monitoring and rule enforcement
- Trading operations with funded account restrictions
- Market data for futures contracts
- WebSocket streaming for live updates
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import uuid

from .auth import TopstepXAuth, TopstepXCredentials
from .models import (
    # API Models
    TopstepXContract, TopstepXQuote, TopstepXOrder, TopstepXPosition,
    OrderType, OrderSide, OrderStatus, TimeInForce, ContractType,
    
    # Business Logic Models
    TopstepAccount, AccountMetrics, FundedAccountRules, TradingRules,
    AccountStatus, TradingPhase, RuleViolation, RuleViolationType
)

logger = logging.getLogger(__name__)


class TopstepXConnector:
    """
    TopstepX API connector for funded account management.
    
    Provides complete integration with TopstepX API including:
    - Account management and monitoring
    - Real-time market data for futures
    - Order placement and management
    - Position tracking and P&L monitoring
    - Funded account rule enforcement
    - WebSocket streaming for live updates
    """
    
    def __init__(self, credentials: TopstepXCredentials):
        """
        Initialize TopstepX connector.
        
        Args:
            credentials: TopstepX API credentials
        """
        self.credentials = credentials
        self.auth = TopstepXAuth(credentials)
        
        # Cached data
        self._contracts_cache: Dict[str, TopstepXContract] = {}
        self._accounts_cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        # Business logic models for funded account management
        self._funded_accounts: Dict[str, TopstepAccount] = {}
        self._mock_accounts: Dict[str, TopstepAccount] = {}
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._authenticated: bool = False
        
        # Initialize mock accounts for development
        self._initialize_mock_accounts()
        
        logger.info(f"TopstepX connector initialized for {credentials.environment} environment")
    
    async def close(self):
        """Close HTTP connections"""
        await self.auth.close()
    
    # =============================================================================
    # Authentication Methods
    # =============================================================================
    
    async def authenticate(self) -> str:
        """Authenticate with TopstepX API and return access token"""
        return await self.auth.get_valid_access_token()
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        return await self.auth.test_connection()
    
    # =============================================================================
    # Account Management Methods
    # =============================================================================
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all TopstepX accounts for the authenticated user.
        
        Returns:
            List[Dict[str, Any]]: List of account information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.auth.api_base_url}/accounts",
                headers=headers
            )
            response.raise_for_status()
            
            accounts_data = response.json()
            logger.info(f"Retrieved {len(accounts_data)} TopstepX accounts")
            
            return accounts_data
            
        except Exception as e:
            logger.error(f"Error getting TopstepX accounts: {e}")
            raise
    
    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """
        Get detailed account information.
        
        Args:
            account_id: TopstepX account ID
            
        Returns:
            Dict[str, Any]: Account details
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.auth.api_base_url}/accounts/{account_id}",
                headers=headers
            )
            response.raise_for_status()
            
            account_data = response.json()
            logger.info(f"Retrieved details for TopstepX account {account_id}")
            
            return account_data
            
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
            raise
    
    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """
        Get account balance information.
        
        Args:
            account_id: TopstepX account ID
            
        Returns:
            Dict[str, Any]: Balance information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.auth.api_base_url}/accounts/{account_id}/balances",
                headers=headers
            )
            response.raise_for_status()
            
            balance_data = response.json()
            logger.info(f"Retrieved balances for TopstepX account {account_id}")
            
            return balance_data
            
        except Exception as e:
            logger.error(f"Error getting account balances: {e}")
            raise
    
    # =============================================================================
    # Contract and Market Data Methods
    # =============================================================================
    
    async def search_contracts(self, query: str = "", exchange: Optional[str] = None) -> List[TopstepXContract]:
        """
        Search for trading contracts.
        
        Args:
            query: Search query for contract symbol or description
            exchange: Filter by exchange (optional)
            
        Returns:
            List[TopstepXContract]: List of matching contracts
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if query:
                params["q"] = query
            if exchange:
                params["exchange"] = exchange
            
            response = await client.get(
                f"{self.auth.api_base_url}/contracts",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            contracts_data = response.json()
            
            # Convert to TopstepXContract models
            contracts = []
            for contract_data in contracts_data:
                try:
                    contract = TopstepXContract.from_topstepx_data(contract_data)
                    contracts.append(contract)
                    
                    # Cache the contract
                    self._contracts_cache[contract.contract_id] = contract
                except Exception as e:
                    logger.warning(f"Failed to parse contract: {e}")
            
            logger.info(f"Found {len(contracts)} contracts matching query '{query}'")
            return contracts
            
        except Exception as e:
            logger.error(f"Error searching contracts: {e}")
            raise
    
    async def get_contract(self, contract_id: str) -> TopstepXContract:
        """
        Get contract details by ID.
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            TopstepXContract: Contract information
        """
        # Check cache first
        if contract_id in self._contracts_cache:
            return self._contracts_cache[contract_id]
        
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.auth.api_base_url}/contracts/{contract_id}",
                headers=headers
            )
            response.raise_for_status()
            
            contract_data = response.json()
            contract = TopstepXContract.from_topstepx_data(contract_data)
            
            # Cache the contract
            self._contracts_cache[contract_id] = contract
            
            logger.info(f"Retrieved contract details for {contract_id}")
            return contract
            
        except Exception as e:
            logger.error(f"Error getting contract {contract_id}: {e}")
            raise
    
    async def get_quote(self, contract_id: str) -> TopstepXQuote:
        """
        Get real-time quote for a contract.
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            TopstepXQuote: Current market quote
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.auth.api_base_url}/market/quotes/{contract_id}",
                headers=headers
            )
            response.raise_for_status()
            
            quote_data = response.json()
            quote = TopstepXQuote.from_topstepx_data(quote_data)
            
            logger.debug(f"Retrieved quote for {contract_id}: {quote.last}")
            return quote
            
        except Exception as e:
            logger.error(f"Error getting quote for {contract_id}: {e}")
            raise
    
    async def get_historical_data(
        self,
        contract_id: str,
        timeframe: str = "1m",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a contract.
        
        Args:
            contract_id: Contract identifier
            timeframe: Data timeframe (1m, 5m, 15m, 1h, 1d)
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of bars to return
            
        Returns:
            List[Dict[str, Any]]: Historical OHLCV data
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {
                "timeframe": timeframe,
                "limit": limit
            }
            
            if start_date:
                params["start"] = start_date.isoformat()
            if end_date:
                params["end"] = end_date.isoformat()
            
            response = await client.get(
                f"{self.auth.api_base_url}/market/historical/{contract_id}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            historical_data = response.json()
            logger.info(f"Retrieved {len(historical_data)} historical bars for {contract_id}")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {contract_id}: {e}")
            raise
    
    # =============================================================================
    # Trading Methods
    # =============================================================================
    
    async def place_order(self, order: TopstepXOrder) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            order: Order to place
            
        Returns:
            Dict[str, Any]: Order placement response
        """
        try:
            # Check funded account rules before placing order
            if order.account_id in self._funded_accounts:
                funded_account = self._funded_accounts[order.account_id]
                can_trade, reason = funded_account.rules.account_rules.can_trade(
                    order.quantity, order.symbol
                )
                if not can_trade:
                    raise Exception(f"Trade rejected by funded account rules: {reason}")
            
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            order_data = order.to_topstepx_format()
            
            response = await client.post(
                f"{self.auth.api_base_url}/orders",
                headers=headers,
                json=order_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Order placed successfully: {order.symbol} {order.side.value} {order.quantity}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.delete(
                f"{self.auth.api_base_url}/orders/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Order cancelled successfully: {order_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise
    
    async def get_orders(self, account_id: Optional[str] = None) -> List[TopstepXOrder]:
        """Get orders for account"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if account_id:
                params["accountId"] = account_id
            
            response = await client.get(
                f"{self.auth.api_base_url}/orders",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            orders_data = response.json()
            
            orders = []
            for order_data in orders_data:
                try:
                    order = TopstepXOrder.from_topstepx_data(order_data)
                    orders.append(order)
                except Exception as e:
                    logger.warning(f"Failed to parse order: {e}")
            
            logger.info(f"Retrieved {len(orders)} orders")
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise
    
    async def get_positions(self, account_id: Optional[str] = None) -> List[TopstepXPosition]:
        """Get positions for account"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if account_id:
                params["accountId"] = account_id
            
            response = await client.get(
                f"{self.auth.api_base_url}/positions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            positions_data = response.json()
            
            positions = []
            for position_data in positions_data:
                try:
                    position = TopstepXPosition.from_topstepx_data(position_data)
                    positions.append(position)
                except Exception as e:
                    logger.warning(f"Failed to parse position: {e}")
            
            logger.info(f"Retrieved {len(positions)} positions")
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise
    
    async def close_position(self, position_id: str, quantity: Optional[int] = None) -> Dict[str, Any]:
        """Close position (full or partial)"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            data = {}
            if quantity:
                data["quantity"] = quantity
            
            response = await client.post(
                f"{self.auth.api_base_url}/positions/{position_id}/close",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Position closed successfully: {position_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            raise
    
    # =============================================================================
    # Funded Account Business Logic Methods
    # =============================================================================
    
    def _initialize_mock_accounts(self):
        """Initialize mock funded accounts for development testing"""
        
        # Mock TopStep Evaluation Account
        mock_rules = FundedAccountRules(
            max_daily_loss=1000.0,
            max_contracts=3,
            trailing_drawdown=2000.0,
            profit_target=3000.0,
            current_daily_pnl=-250.0,
            current_drawdown=500.0,
            max_peak_equity=50000.0,
            min_trading_days=5,
            allow_overnight_positions=False,
            allow_news_trading=False,
            restricted_symbols=["BTCUSD", "ETHUSD"]
        )
        
        mock_trading_rules = TradingRules(
            account_rules=mock_rules,
            trading_hours_start="00:00",  # Allow 24/7 trading for testing
            trading_hours_end="23:59",
            timezone="US/Eastern",
            news_blackout_minutes=2,
            consistency_rule_enabled=True,
            max_daily_profit_percentage=0.5
        )
        
        mock_metrics = AccountMetrics(
            account_id="topstep_eval_001",
            daily_pnl=-250.0,
            total_pnl=1750.0,
            gross_pnl=1800.0,
            net_pnl=1750.0,
            current_drawdown=500.0,
            max_drawdown=800.0,
            max_peak_equity=51750.0,
            open_positions=1,
            total_contracts=2,
            largest_position=2,
            win_rate=65.5,
            profit_factor=1.8,
            avg_win=125.0,
            avg_loss=-85.0,
            max_consecutive_losses=3,
            total_trades=47,
            trading_days=12,
            avg_daily_volume=45000.0
        )
        
        mock_account = TopstepAccount(
            account_id="topstep_eval_001",
            account_name="TopStep Evaluation $50K",
            trader_id="trader_12345",
            account_size=50000.0,
            current_balance=51750.0,
            account_type="Express Evaluation",
            phase=TradingPhase.EVALUATION,
            status=AccountStatus.ACTIVE,
            rules=mock_trading_rules,
            current_metrics=mock_metrics,
            created_at=datetime.utcnow() - timedelta(days=15),
            last_trade_date=datetime.utcnow() - timedelta(hours=2),
            evaluation_end_date=datetime.utcnow() + timedelta(days=15)
        )
        
        self._mock_accounts[mock_account.account_id] = mock_account
        
        # Mock Funded Account
        funded_rules = FundedAccountRules(
            max_daily_loss=2000.0,
            max_contracts=5,
            trailing_drawdown=4000.0,
            profit_target=0.0,  # No target for funded accounts
            current_daily_pnl=150.0,
            current_drawdown=200.0,
            max_peak_equity=125000.0,
            min_trading_days=0,
            allow_overnight_positions=True,
            allow_news_trading=True
        )
        
        funded_trading_rules = TradingRules(
            account_rules=funded_rules,
            trading_hours_start="00:00",  # Allow 24/7 trading for testing
            trading_hours_end="23:59",
            timezone="US/Eastern",
            news_blackout_minutes=0,  # No restrictions for funded
            consistency_rule_enabled=False,
            max_daily_profit_percentage=1.0
        )
        
        funded_metrics = AccountMetrics(
            account_id="topstep_funded_001",
            daily_pnl=150.0,
            total_pnl=8500.0,
            gross_pnl=9200.0,
            net_pnl=8500.0,
            current_drawdown=200.0,
            max_drawdown=1200.0,
            max_peak_equity=133500.0,
            open_positions=0,
            total_contracts=0,
            largest_position=0,
            win_rate=72.3,
            profit_factor=2.1,
            avg_win=185.0,
            avg_loss=-95.0,
            max_consecutive_losses=2,
            total_trades=156,
            trading_days=45,
            avg_daily_volume=85000.0
        )
        
        funded_account = TopstepAccount(
            account_id="topstep_funded_001",
            account_name="TopStep Funded $125K",
            trader_id="trader_12345",
            account_size=125000.0,
            current_balance=133500.0,
            account_type="Funded Account",
            phase=TradingPhase.FUNDED,
            status=AccountStatus.ACTIVE,
            rules=funded_trading_rules,
            current_metrics=funded_metrics,
            created_at=datetime.utcnow() - timedelta(days=90),
            last_trade_date=datetime.utcnow() - timedelta(minutes=30),
            evaluation_end_date=None
        )
        
        self._mock_accounts[funded_account.account_id] = funded_account
        
        logger.info(f"Initialized {len(self._mock_accounts)} mock TopStep accounts")
    
    async def authenticate(self) -> str:
        """
        Authenticate with TopstepX API.
        
        **STUB IMPLEMENTATION**: Returns mock token for development.
        
        Returns:
            str: Access token
            
        Raises:
            NotImplementedError: Until real API is available
        """
        logger.warning("TopstepX authentication: STUB MODE - using mock credentials")
        
        # Simulate authentication delay
        await asyncio.sleep(0.5)
        
        # Mock successful authentication
        self._access_token = f"mock_topstep_token_{uuid.uuid4().hex[:16]}"
        self._authenticated = True
        
        logger.info("TopstepX mock authentication successful")
        return self._access_token
    
    async def get_accounts(self) -> List[TopstepAccount]:
        """
        Get all TopStep accounts for the authenticated user.
        
        Returns:
            List[TopstepAccount]: List of funded accounts
        """
        if not self._authenticated:
            await self.authenticate()
        
        logger.info("Retrieving TopStep accounts (mock data)")
        return list(self._mock_accounts.values())
    
    async def get_account_metrics(self, account_id: str) -> Optional[FundedAccountRules]:
        """
        Get current account metrics and rules.
        
        Args:
            account_id: TopStep account ID
            
        Returns:
            FundedAccountRules: Current account rules and metrics
        """
        if not self._authenticated:
            await self.authenticate()
        
        account = self._mock_accounts.get(account_id)
        if not account:
            logger.warning(f"TopStep account {account_id} not found")
            return None
        
        # Simulate some randomness in daily P&L for testing
        import random
        pnl_change = random.uniform(-50, 50)
        account.rules.account_rules.current_daily_pnl += pnl_change
        account.current_metrics.daily_pnl = account.rules.account_rules.current_daily_pnl
        
        # Update metrics
        account.update_metrics(account.current_metrics)
        
        logger.info(f"Retrieved metrics for TopStep account {account_id}")
        return account.rules.account_rules
    
    async def get_account_info(self, account_id: str) -> Optional[TopstepAccount]:
        """Get complete account information"""
        if not self._authenticated:
            await self.authenticate()
        
        account = self._mock_accounts.get(account_id)
        if account:
            # Update last accessed time
            account.last_updated = datetime.utcnow()
        
        return account
    
    async def check_trading_eligibility(
        self, 
        account_id: str, 
        symbol: str, 
        quantity: int
    ) -> Dict[str, Any]:
        """
        Check if a trade is allowed for the account.
        
        Args:
            account_id: TopStep account ID
            symbol: Trading symbol
            quantity: Number of contracts
            
        Returns:
            Dict[str, Any]: Eligibility result
        """
        if not self._authenticated:
            await self.authenticate()
        
        account = self._mock_accounts.get(account_id)
        if not account:
            return {
                "eligible": False,
                "reason": "Account not found",
                "account_id": account_id
            }
        
        # Check overall trading eligibility
        trading_allowed, trading_reason = account.is_trading_allowed()
        if not trading_allowed:
            return {
                "eligible": False,
                "reason": trading_reason,
                "account_id": account_id
            }
        
        # Check specific trade eligibility
        can_trade, trade_reason = account.rules.account_rules.can_trade(quantity, symbol)
        if not can_trade:
            return {
                "eligible": False,
                "reason": trade_reason,
                "account_id": account_id
            }
        
        return {
            "eligible": True,
            "account_id": account_id,
            "current_metrics": {
                "daily_pnl": account.current_metrics.daily_pnl,
                "drawdown": account.current_metrics.current_drawdown,
                "contracts": account.current_metrics.total_contracts,
                "remaining_loss_buffer": account.rules.account_rules.get_remaining_loss_buffer(),
                "remaining_drawdown_buffer": account.rules.account_rules.get_remaining_drawdown_buffer()
            }
        }
    
    async def emergency_flatten_positions(self, account_id: str) -> Dict[str, Any]:
        """
        Emergency position flattening for rule violations.
        
        **STUB IMPLEMENTATION**: Simulates emergency closure.
        
        Args:
            account_id: Account to flatten
            
        Returns:
            Dict[str, Any]: Flattening result
        """
        if not self._authenticated:
            await self.authenticate()
        
        account = self._mock_accounts.get(account_id)
        if not account:
            return {
                "success": False,
                "message": "Account not found",
                "account_id": account_id
            }
        
        # Simulate emergency flattening
        positions_closed = account.current_metrics.open_positions
        account.current_metrics.open_positions = 0
        account.current_metrics.total_contracts = 0
        
        logger.warning(f"Emergency position flattening for account {account_id}: {positions_closed} positions closed")
        
        return {
            "success": True,
            "message": f"Emergency flattening completed: {positions_closed} positions closed",
            "account_id": account_id,
            "positions_closed": positions_closed,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def report_trade_execution(
        self,
        account_id: str,
        symbol: str,
        quantity: int,
        price: float,
        side: str
    ) -> bool:
        """
        Report trade execution to TopStep for monitoring.
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            quantity: Contracts traded
            price: Execution price
            side: Buy/Sell
            
        Returns:
            bool: Success status
        """
        if not self._authenticated:
            await self.authenticate()
        
        account = self._mock_accounts.get(account_id)
        if not account:
            return False
        
        # Update account metrics based on trade
        trade_value = quantity * price * (100 if symbol.startswith('ES') else 50)  # Mock contract values
        pnl_impact = trade_value * 0.001 * (1 if side.upper() == 'BUY' else -1)  # Mock P&L impact
        
        account.current_metrics.daily_pnl += pnl_impact
        account.current_metrics.total_trades += 1
        account.last_trade_date = datetime.utcnow()
        
        # Update position tracking
        if side.upper() == 'BUY':
            account.current_metrics.total_contracts += quantity
            account.current_metrics.open_positions += 1
        else:
            account.current_metrics.total_contracts = max(0, account.current_metrics.total_contracts - quantity)
            if account.current_metrics.total_contracts == 0:
                account.current_metrics.open_positions = 0
        
        # Update rules with new P&L
        account.rules.account_rules.update_daily_pnl(account.current_metrics.daily_pnl)
        
        logger.info(f"Reported trade execution to TopStep: {symbol} {side} {quantity} @ {price}")
        return True
    
    async def get_rule_violations(self, account_id: str) -> List[RuleViolation]:
        """Get active rule violations for account"""
        if not self._authenticated:
            await self.authenticate()
        
        account = self._mock_accounts.get(account_id)
        if not account:
            return []
        
        return account.active_violations
    
    async def start_realtime_monitoring(self, account_id: str, callback: callable) -> bool:
        """
        Start real-time monitoring for account rule violations.
        
        **STUB IMPLEMENTATION**: Simulates periodic monitoring.
        
        Args:
            account_id: Account to monitor
            callback: Function to call on rule violations
            
        Returns:
            bool: Success status
        """
        logger.warning("TopStep real-time monitoring: STUB MODE - simulating monitoring")
        
        # In real implementation, this would establish WebSocket connection
        # For now, just simulate successful setup
        return True
    
    def get_mock_account_summary(self) -> Dict[str, Any]:
        """Get summary of all mock accounts for development"""
        return {
            "total_accounts": len(self._mock_accounts),
            "accounts": [
                {
                    "account_id": acc.account_id,
                    "name": acc.account_name,
                    "status": acc.status.value,
                    "phase": acc.phase.value,
                    "balance": acc.current_balance,
                    "daily_pnl": acc.current_metrics.daily_pnl,
                    "violations": len(acc.active_violations)
                }
                for acc in self._mock_accounts.values()
            ]
        }
    
    async def close(self):
        """Close TopstepX connection"""
        self._authenticated = False
        self._access_token = None
        logger.info("TopstepX connector closed")