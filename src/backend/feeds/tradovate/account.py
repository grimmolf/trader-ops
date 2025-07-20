"""
Tradovate Account Management

Handles account information, balances, positions, and performance metrics.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from .auth import TradovateAuth

logger = logging.getLogger(__name__)


class TradovateAccountInfo(BaseModel):
    """Tradovate account information"""
    
    id: int
    name: str
    account_type: str = Field(description="Account type (Live, Demo, etc.)")
    status: str = Field(description="Account status")
    archived: bool = False
    
    # Account classification
    user_id: int
    clearing_house_id: Optional[int] = None
    risk_category_id: Optional[int] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_tradovate_account(cls, account_data: dict) -> "TradovateAccountInfo":
        """Create from Tradovate account response"""
        return cls(
            id=account_data.get("id"),
            name=account_data.get("name", ""),
            account_type=account_data.get("accountType", "Unknown"),
            status=account_data.get("active", "Unknown"),
            archived=account_data.get("archived", False),
            user_id=account_data.get("userId", 0),
            clearing_house_id=account_data.get("clearingHouseId"),
            risk_category_id=account_data.get("riskCategoryId")
        )


class CashBalance(BaseModel):
    """Account cash balance information"""
    
    account_id: int
    
    # Core balance fields
    cash_balance: float = Field(description="Current cash balance")
    open_pl: float = Field(description="Open P&L from positions")
    day_open_pl: float = Field(description="Day open P&L")
    day_closed_pl: float = Field(description="Day closed P&L")
    
    # Available funds
    purchasing_power: float = Field(description="Available purchasing power")
    excess_liquidity: float = Field(description="Excess liquidity")
    
    # Margin information
    initial_margin: float = Field(description="Initial margin requirement")
    maintenance_margin: float = Field(description="Maintenance margin requirement")
    margin_available: float = Field(description="Available margin")
    
    # Risk metrics
    net_liquidation_value: float = Field(description="Net liquidation value")
    currency: str = Field(default="USD")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_tradovate_balance(cls, balance_data: dict) -> "CashBalance":
        """Create from Tradovate cash balance response"""
        return cls(
            account_id=balance_data.get("accountId", 0),
            cash_balance=balance_data.get("cashBalance", 0.0),
            open_pl=balance_data.get("openPL", 0.0),
            day_open_pl=balance_data.get("dayOpenPL", 0.0),
            day_closed_pl=balance_data.get("dayClosedPL", 0.0),
            purchasing_power=balance_data.get("purchasingPower", 0.0),
            excess_liquidity=balance_data.get("excessLiquidity", 0.0),
            initial_margin=balance_data.get("initialMargin", 0.0),
            maintenance_margin=balance_data.get("maintenanceMargin", 0.0),
            margin_available=balance_data.get("marginAvailable", 0.0),
            net_liquidation_value=balance_data.get("netLiquidationValue", 0.0)
        )
    
    @property
    def total_pnl(self) -> float:
        """Calculate total P&L"""
        return self.day_closed_pl + self.open_pl
    
    @property
    def margin_utilization(self) -> float:
        """Calculate margin utilization percentage"""
        if self.net_liquidation_value <= 0:
            return 0.0
        return (self.initial_margin / self.net_liquidation_value) * 100


class Position(BaseModel):
    """Trading position information"""
    
    account_id: int
    contract_id: int
    symbol: Optional[str] = None
    
    # Position details
    net_position: int = Field(description="Net position (positive=long, negative=short)")
    average_price: float = Field(description="Average entry price")
    
    # P&L information
    open_pl: float = Field(description="Open P&L")
    day_open_pl: float = Field(description="Day open P&L")
    day_closed_pl: float = Field(description="Day closed P&L")
    
    # Market data
    mark_price: Optional[float] = Field(description="Current mark price")
    market_value: Optional[float] = Field(description="Current market value")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_tradovate_position(cls, position_data: dict) -> "Position":
        """Create from Tradovate position response"""
        return cls(
            account_id=position_data.get("accountId", 0),
            contract_id=position_data.get("contractId", 0),
            net_position=position_data.get("netPos", 0),
            average_price=position_data.get("avgPrice", 0.0),
            open_pl=position_data.get("openPL", 0.0),
            day_open_pl=position_data.get("dayOpenPL", 0.0),
            day_closed_pl=position_data.get("dayClosedPL", 0.0),
            mark_price=position_data.get("markPrice"),
            market_value=position_data.get("marketValue")
        )
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.net_position > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.net_position < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat"""
        return self.net_position == 0
    
    @property
    def total_pnl(self) -> float:
        """Calculate total P&L"""
        return self.day_closed_pl + self.open_pl


class TradovateAccount:
    """
    Tradovate account management client.
    
    Handles account-related operations including:
    - Account information retrieval
    - Cash balance monitoring
    - Position tracking
    - Performance metrics
    """
    
    def __init__(self, auth: TradovateAuth):
        self.auth = auth
        self._account_cache: Dict[int, TradovateAccountInfo] = {}
        logger.info("Initialized Tradovate account manager")
    
    async def get_accounts(self) -> List[TradovateAccountInfo]:
        """
        Get all accounts for the authenticated user.
        
        Returns:
            List[TradovateAccountInfo]: List of account information
        """
        try:
            response = await self.auth.make_authenticated_request("GET", "/account/list")
            
            if response.status_code == 200:
                accounts_data = response.json()
                accounts = []
                
                for account_data in accounts_data:
                    account = TradovateAccountInfo.from_tradovate_account(account_data)
                    accounts.append(account)
                    
                    # Cache account info
                    self._account_cache[account.id] = account
                
                logger.info(f"Retrieved {len(accounts)} accounts")
                return accounts
            else:
                logger.error(f"Failed to get accounts: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    async def get_account_info(self, account_id: int) -> Optional[TradovateAccountInfo]:
        """
        Get information for a specific account.
        
        Args:
            account_id: Account ID to retrieve
            
        Returns:
            TradovateAccountInfo: Account information or None if not found
        """
        # Check cache first
        if account_id in self._account_cache:
            return self._account_cache[account_id]
        
        # Fetch all accounts and find the requested one
        accounts = await self.get_accounts()
        return next((acc for acc in accounts if acc.id == account_id), None)
    
    async def get_cash_balance(self, account_id: int) -> Optional[CashBalance]:
        """
        Get cash balance for an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            CashBalance: Current cash balance information
        """
        try:
            response = await self.auth.make_authenticated_request(
                "GET",
                "/cashBalance/getcashbalancesnapshot",
                params={"accountId": account_id}
            )
            
            if response.status_code == 200:
                balance_data = response.json()
                return CashBalance.from_tradovate_balance(balance_data)
            else:
                logger.error(f"Failed to get cash balance: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cash balance for account {account_id}: {e}")
            return None
    
    async def get_positions(self, account_id: int) -> List[Position]:
        """
        Get all positions for an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            List[Position]: List of current positions
        """
        try:
            response = await self.auth.make_authenticated_request(
                "GET",
                "/position/list",
                params={"accountId": account_id}
            )
            
            if response.status_code == 200:
                positions_data = response.json()
                positions = []
                
                for position_data in positions_data:
                    # Only include non-zero positions
                    if position_data.get("netPos", 0) != 0:
                        position = Position.from_tradovate_position(position_data)
                        
                        # Enrich with symbol information if available
                        await self._enrich_position_with_symbol(position)
                        
                        positions.append(position)
                
                logger.info(f"Retrieved {len(positions)} positions for account {account_id}")
                return positions
            else:
                logger.error(f"Failed to get positions: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions for account {account_id}: {e}")
            return []
    
    async def _enrich_position_with_symbol(self, position: Position):
        """Enrich position with symbol information"""
        try:
            response = await self.auth.make_authenticated_request(
                "GET",
                "/contract/item",
                params={"id": position.contract_id}
            )
            
            if response.status_code == 200:
                contract_data = response.json()
                position.symbol = contract_data.get("name", f"CONTRACT_{position.contract_id}")
            
        except Exception as e:
            logger.debug(f"Could not enrich position with symbol: {e}")
    
    async def get_position_for_symbol(self, account_id: int, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.
        
        Args:
            account_id: Account ID
            symbol: Trading symbol (e.g., "ES", "NQ")
            
        Returns:
            Position: Position for symbol or None if no position
        """
        try:
            # Get contract ID for symbol
            contract_id = await self._get_contract_id(symbol)
            if not contract_id:
                return None
            
            # Get position for contract
            response = await self.auth.make_authenticated_request(
                "GET",
                "/position/find",
                params={
                    "accountId": account_id,
                    "contractId": contract_id
                }
            )
            
            if response.status_code == 200:
                position_data = response.json()
                if position_data and position_data.get("netPos", 0) != 0:
                    position = Position.from_tradovate_position(position_data)
                    position.symbol = symbol
                    return position
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None
    
    async def _get_contract_id(self, symbol: str) -> Optional[int]:
        """Get contract ID for symbol"""
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
    
    async def get_account_performance(self, account_id: int) -> Dict[str, float]:
        """
        Calculate account performance metrics.
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict[str, float]: Performance metrics
        """
        try:
            # Get cash balance and positions
            balance = await self.get_cash_balance(account_id)
            positions = await self.get_positions(account_id)
            
            if not balance:
                return {}
            
            # Calculate metrics
            total_day_pnl = balance.day_closed_pl + sum(pos.day_open_pl for pos in positions)
            total_open_pnl = sum(pos.open_pl for pos in positions)
            total_pnl = total_day_pnl + total_open_pnl
            
            return {
                "account_id": account_id,
                "cash_balance": balance.cash_balance,
                "net_liquidation_value": balance.net_liquidation_value,
                "day_pnl": total_day_pnl,
                "open_pnl": total_open_pnl,
                "total_pnl": total_pnl,
                "margin_utilization": balance.margin_utilization,
                "position_count": len(positions),
                "purchasing_power": balance.purchasing_power,
                "excess_liquidity": balance.excess_liquidity
            }
            
        except Exception as e:
            logger.error(f"Error calculating account performance: {e}")
            return {}
    
    async def is_account_eligible_for_trading(self, account_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if account is eligible for trading.
        
        Args:
            account_id: Account ID to check
            
        Returns:
            tuple: (is_eligible, reason_if_not)
        """
        try:
            # Get account info
            account = await self.get_account_info(account_id)
            if not account:
                return False, "Account not found"
            
            if account.archived:
                return False, "Account is archived"
            
            if account.status != "Active":
                return False, f"Account status is {account.status}"
            
            # Check cash balance
            balance = await self.get_cash_balance(account_id)
            if not balance:
                return False, "Cannot retrieve account balance"
            
            if balance.cash_balance <= 0:
                return False, "Insufficient cash balance"
            
            if balance.purchasing_power <= 0:
                return False, "No purchasing power available"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking account eligibility: {e}")
            return False, f"Error checking account: {str(e)}"