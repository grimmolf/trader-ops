"""
Tastytrade Account Management API

Provides account information, positions, balances, and transaction history
for Tastytrade trading accounts.
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


class AccountType(Enum):
    """Account types supported by Tastytrade"""
    INDIVIDUAL = "Individual"
    ENTITY = "Entity"
    IRA = "IRA"
    ROTH_IRA = "Roth IRA"
    ROLLOVER_IRA = "Rollover IRA"


class TastytradePosition(BaseModel):
    """Account position information"""
    
    # Instrument details
    symbol: str
    instrument_type: str
    underlying_symbol: Optional[str] = None
    
    # Position details
    quantity: Decimal = Decimal("0")
    average_open_price: Optional[Decimal] = None
    mark_price: Optional[Decimal] = None
    
    # Market values
    market_value: Optional[Decimal] = None
    notional_value: Optional[Decimal] = None
    
    # P&L calculations
    realized_day_gain: Optional[Decimal] = None
    unrealized_day_gain: Optional[Decimal] = None
    day_gain_date: Optional[str] = None
    
    # Greeks (for options)
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat"""
        return self.quantity == 0
    
    @property
    def absolute_quantity(self) -> Decimal:
        """Get absolute position size"""
        return abs(self.quantity)
    
    @classmethod
    def from_tastytrade_data(cls, data: Dict[str, Any]) -> "TastytradePosition":
        """Create position from Tastytrade API response"""
        return cls(
            symbol=data.get("symbol", ""),
            instrument_type=data.get("instrument-type", ""),
            underlying_symbol=data.get("underlying-symbol"),
            quantity=Decimal(str(data.get("quantity", 0))),
            average_open_price=Decimal(str(data["average-open-price"])) if data.get("average-open-price") else None,
            mark_price=Decimal(str(data["mark-price"])) if data.get("mark-price") else None,
            market_value=Decimal(str(data["market-value"])) if data.get("market-value") else None,
            notional_value=Decimal(str(data["notional-value"])) if data.get("notional-value") else None,
            realized_day_gain=Decimal(str(data["realized-day-gain"])) if data.get("realized-day-gain") else None,
            unrealized_day_gain=Decimal(str(data["unrealized-day-gain"])) if data.get("unrealized-day-gain") else None,
            day_gain_date=data.get("day-gain-date"),
            delta=Decimal(str(data["delta"])) if data.get("delta") else None,
            gamma=Decimal(str(data["gamma"])) if data.get("gamma") else None,
            theta=Decimal(str(data["theta"])) if data.get("theta") else None,
            vega=Decimal(str(data["vega"])) if data.get("vega") else None,
            created_at=datetime.fromisoformat(data["created-at"]) if data.get("created-at") else None,
            updated_at=datetime.fromisoformat(data["updated-at"]) if data.get("updated-at") else None
        )


class TastytradeBalance(BaseModel):
    """Account balance information"""
    
    # Cash balances
    cash_balance: Optional[Decimal] = None
    long_equity_value: Optional[Decimal] = None
    short_equity_value: Optional[Decimal] = None
    long_derivative_value: Optional[Decimal] = None
    short_derivative_value: Optional[Decimal] = None
    
    # Account values
    account_value: Optional[Decimal] = None
    net_liquidating_value: Optional[Decimal] = None
    buying_power: Optional[Decimal] = None
    
    # Day trading specific
    day_trading_buying_power: Optional[Decimal] = None
    day_trading_excess: Optional[Decimal] = None
    maintenance_excess: Optional[Decimal] = None
    
    # Option specific
    long_option_value: Optional[Decimal] = None
    short_option_value: Optional[Decimal] = None
    
    # Futures specific  
    long_futures_value: Optional[Decimal] = None
    short_futures_value: Optional[Decimal] = None
    
    @classmethod
    def from_tastytrade_data(cls, data: Dict[str, Any]) -> "TastytradeBalance":
        """Create balance from Tastytrade API response"""
        return cls(
            cash_balance=Decimal(str(data["cash-balance"])) if data.get("cash-balance") else None,
            long_equity_value=Decimal(str(data["long-equity-value"])) if data.get("long-equity-value") else None,
            short_equity_value=Decimal(str(data["short-equity-value"])) if data.get("short-equity-value") else None,
            long_derivative_value=Decimal(str(data["long-derivative-value"])) if data.get("long-derivative-value") else None,
            short_derivative_value=Decimal(str(data["short-derivative-value"])) if data.get("short-derivative-value") else None,
            account_value=Decimal(str(data["account-value"])) if data.get("account-value") else None,
            net_liquidating_value=Decimal(str(data["net-liquidating-value"])) if data.get("net-liquidating-value") else None,
            buying_power=Decimal(str(data["buying-power"])) if data.get("buying-power") else None,
            day_trading_buying_power=Decimal(str(data["day-trading-buying-power"])) if data.get("day-trading-buying-power") else None,
            day_trading_excess=Decimal(str(data["day-trading-excess"])) if data.get("day-trading-excess") else None,
            maintenance_excess=Decimal(str(data["maintenance-excess"])) if data.get("maintenance-excess") else None,
            long_option_value=Decimal(str(data["long-option-value"])) if data.get("long-option-value") else None,
            short_option_value=Decimal(str(data["short-option-value"])) if data.get("short-option-value") else None,
            long_futures_value=Decimal(str(data["long-futures-value"])) if data.get("long-futures-value") else None,
            short_futures_value=Decimal(str(data["short-futures-value"])) if data.get("short-futures-value") else None
        )


class TastytradeAccountInfo(BaseModel):
    """Complete account information"""
    
    # Account identifiers
    account_number: str
    nickname: Optional[str] = None
    account_type: Optional[str] = None
    day_trader_status: bool = False
    
    # Financial information
    balance: Optional[TastytradeBalance] = None
    positions: List[TastytradePosition] = Field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_market_value(self) -> Decimal:
        """Calculate total market value of positions"""
        total = Decimal("0")
        for position in self.positions:
            if position.market_value:
                total += position.market_value
        return total
    
    @property
    def equity_positions(self) -> List[TastytradePosition]:
        """Get equity positions only"""
        return [pos for pos in self.positions if pos.instrument_type == "Equity"]
    
    @property
    def option_positions(self) -> List[TastytradePosition]:
        """Get option positions only"""
        return [pos for pos in self.positions if "Option" in pos.instrument_type]
    
    @property
    def futures_positions(self) -> List[TastytradePosition]:
        """Get futures positions only"""
        return [pos for pos in self.positions if "Future" in pos.instrument_type]
    
    @property
    def active_positions(self) -> List[TastytradePosition]:
        """Get positions with non-zero quantity"""
        return [pos for pos in self.positions if not pos.is_flat]
    
    @classmethod
    def from_tastytrade_data(cls, data: Dict[str, Any]) -> "TastytradeAccountInfo":
        """Create account info from Tastytrade API response"""
        # Parse positions
        positions = []
        for pos_data in data.get("positions", []):
            try:
                position = TastytradePosition.from_tastytrade_data(pos_data)
                positions.append(position)
            except Exception as e:
                logger.warning(f"Failed to parse position: {e}")
        
        # Parse balance
        balance = None
        if "balance" in data:
            balance = TastytradeBalance.from_tastytrade_data(data["balance"])
        
        return cls(
            account_number=data.get("account-number", ""),
            nickname=data.get("nickname"),
            account_type=data.get("account-type"),
            day_trader_status=data.get("day-trader-status", False),
            balance=balance,
            positions=positions,
            created_at=datetime.fromisoformat(data["created-at"]) if data.get("created-at") else None
        )


class TastytradeTransaction(BaseModel):
    """Transaction history entry"""
    
    # Transaction identifiers
    id: str
    account_number: str
    
    # Transaction details
    symbol: str
    instrument_type: str
    action: str
    quantity: Decimal
    price: Optional[Decimal] = None
    value: Optional[Decimal] = None
    
    # Financial details
    net_value: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    
    # Timestamps
    executed_at: Optional[datetime] = None
    
    @classmethod
    def from_tastytrade_data(cls, data: Dict[str, Any]) -> "TastytradeTransaction":
        """Create transaction from Tastytrade API response"""
        return cls(
            id=str(data.get("id", "")),
            account_number=data.get("account-number", ""),
            symbol=data.get("symbol", ""),
            instrument_type=data.get("instrument-type", ""),
            action=data.get("action", ""),
            quantity=Decimal(str(data.get("quantity", 0))),
            price=Decimal(str(data["price"])) if data.get("price") else None,
            value=Decimal(str(data["value"])) if data.get("value") else None,
            net_value=Decimal(str(data["net-value"])) if data.get("net-value") else None,
            fees=Decimal(str(data["fees"])) if data.get("fees") else None,
            commission=Decimal(str(data["commission"])) if data.get("commission") else None,
            executed_at=datetime.fromisoformat(data["executed-at"]) if data.get("executed-at") else None
        )


class TastytradeAccount:
    """
    Tastytrade account management API client.
    
    Provides access to:
    - Account information and details
    - Account balances and buying power
    - Portfolio positions
    - Transaction history
    """
    
    def __init__(self, auth: TastytradeAuth):
        self.auth = auth
        self.base_url = auth.api_base_url
    
    async def get_customer_info(self) -> Dict[str, Any]:
        """
        Get customer information for the authenticated user.
        
        Returns:
            Dict[str, Any]: Customer information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.base_url}/customers/me",
                headers=headers
            )
            response.raise_for_status()
            
            customer_data = response.json()
            logger.info("Retrieved customer information")
            
            return customer_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting customer info: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get customer info: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting customer info: {e}")
            raise
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts for the authenticated user.
        
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
                f"{self.base_url}/customers/me/accounts",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            accounts = []
            if "data" in data and "items" in data["data"]:
                accounts = data["data"]["items"]
            
            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting accounts: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get accounts: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            raise
    
    async def get_account(self, account_number: str) -> TastytradeAccountInfo:
        """
        Get detailed account information.
        
        Args:
            account_number: Account number
            
        Returns:
            TastytradeAccountInfo: Complete account information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Get account details
            response = await client.get(
                f"{self.base_url}/accounts/{account_number}",
                headers=headers
            )
            response.raise_for_status()
            
            account_data = response.json()
            
            # Get account balance
            balance_response = await client.get(
                f"{self.base_url}/accounts/{account_number}/balances",
                headers=headers
            )
            balance_response.raise_for_status()
            
            balance_data = balance_response.json()
            if "data" in balance_data:
                account_data["balance"] = balance_data["data"]
            
            # Get positions
            positions_response = await client.get(
                f"{self.base_url}/accounts/{account_number}/positions",
                headers=headers
            )
            positions_response.raise_for_status()
            
            positions_data = positions_response.json()
            if "data" in positions_data and "items" in positions_data["data"]:
                account_data["positions"] = positions_data["data"]["items"]
            
            account_info = TastytradeAccountInfo.from_tastytrade_data(account_data)
            
            logger.info(f"Retrieved account info for {account_number}")
            return account_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting account: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get account: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            raise
    
    async def get_account_balance(self, account_number: str) -> TastytradeBalance:
        """Get account balance information"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_number}/balances",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            balance_data = data.get("data", {})
            balance = TastytradeBalance.from_tastytrade_data(balance_data)
            
            logger.info(f"Retrieved balance for account {account_number}")
            return balance
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting account balance: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get account balance: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            raise
    
    async def get_positions(self, account_number: str) -> List[TastytradePosition]:
        """Get positions for an account"""
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_number}/positions",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            positions = []
            if "data" in data and "items" in data["data"]:
                for pos_data in data["data"]["items"]:
                    try:
                        position = TastytradePosition.from_tastytrade_data(pos_data)
                        positions.append(position)
                    except Exception as e:
                        logger.warning(f"Failed to parse position: {e}")
            
            logger.info(f"Retrieved {len(positions)} positions for account {account_number}")
            return positions
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting positions: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get positions: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise
    
    async def get_transactions(
        self,
        account_number: str,
        page_offset: Optional[int] = None,
        per_page: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[TastytradeTransaction]:
        """Get transaction history for an account"""
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
            if start_date:
                params["start-date"] = start_date
            if end_date:
                params["end-date"] = end_date
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_number}/transactions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            transactions = []
            if "data" in data and "items" in data["data"]:
                for txn_data in data["data"]["items"]:
                    try:
                        transaction = TastytradeTransaction.from_tastytrade_data(txn_data)
                        transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"Failed to parse transaction: {e}")
            
            logger.info(f"Retrieved {len(transactions)} transactions for account")
            return transactions
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting transactions: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get transactions: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            raise