"""
Charles Schwab Account Management API

Provides account information, positions, balances, and transaction history
for Schwab trading accounts.
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


class AccountType(Enum):
    """Account types supported by Schwab"""
    CASH = "CASH"
    MARGIN = "MARGIN"
    IRA = "IRA"
    ROTH_IRA = "ROTH_IRA"
    ROLLOVER_IRA = "ROLLOVER_IRA"
    HSA = "HSA"
    _401K = "401K"
    TRUST = "TRUST"
    JOINT = "JOINT"


class PositionEffect(Enum):
    """Position effect for options"""
    OPENING = "OPENING"
    CLOSING = "CLOSING"


class SchwabPosition(BaseModel):
    """Account position information"""
    
    # Instrument details
    symbol: str
    asset_type: str
    description: Optional[str] = None
    
    # Position details
    long_quantity: Decimal = Decimal("0")
    short_quantity: Decimal = Decimal("0")
    average_price: Optional[Decimal] = None
    current_day_profit_loss: Optional[Decimal] = None
    current_day_profit_loss_percentage: Optional[Decimal] = None
    
    # Market values
    market_value: Optional[Decimal] = None
    day_change: Optional[Decimal] = None
    day_change_percentage: Optional[Decimal] = None
    
    # Option-specific fields
    put_call: Optional[str] = None
    underlying_symbol: Optional[str] = None
    expiration_date: Optional[datetime] = None
    strike_price: Optional[Decimal] = None
    multiplier: Optional[int] = None
    
    @property
    def net_quantity(self) -> Decimal:
        """Get net position quantity (long - short)"""
        return self.long_quantity - self.short_quantity
    
    @property
    def is_long(self) -> bool:
        """Check if position is net long"""
        return self.net_quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is net short"""
        return self.net_quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat (no net exposure)"""
        return self.net_quantity == 0
    
    @classmethod
    def from_schwab_data(cls, data: Dict[str, Any]) -> "SchwabPosition":
        """Create position from Schwab API response"""
        instrument_data = data.get("instrument", {})
        
        # Parse expiration date for options
        expiration_date = None
        if instrument_data.get("expirationDate"):
            try:
                expiration_date = datetime.fromisoformat(instrument_data["expirationDate"])
            except ValueError:
                pass
        
        return cls(
            symbol=instrument_data.get("symbol", ""),
            asset_type=instrument_data.get("assetType", ""),
            description=instrument_data.get("description"),
            long_quantity=Decimal(str(data.get("longQuantity", 0))),
            short_quantity=Decimal(str(data.get("shortQuantity", 0))),
            average_price=Decimal(str(data["averagePrice"])) if data.get("averagePrice") else None,
            current_day_profit_loss=Decimal(str(data["currentDayProfitLoss"])) if data.get("currentDayProfitLoss") else None,
            current_day_profit_loss_percentage=Decimal(str(data["currentDayProfitLossPercentage"])) if data.get("currentDayProfitLossPercentage") else None,
            market_value=Decimal(str(data["marketValue"])) if data.get("marketValue") else None,
            day_change=Decimal(str(data["dayChange"])) if data.get("dayChange") else None,
            day_change_percentage=Decimal(str(data["dayChangePercentage"])) if data.get("dayChangePercentage") else None,
            put_call=instrument_data.get("putCall"),
            underlying_symbol=instrument_data.get("underlyingSymbol"),
            expiration_date=expiration_date,
            strike_price=Decimal(str(instrument_data["strikePrice"])) if instrument_data.get("strikePrice") else None,
            multiplier=instrument_data.get("optionMultiplier")
        )


class SchwabBalance(BaseModel):
    """Account balance information"""
    
    # Cash balances
    available_funds: Optional[Decimal] = None
    buying_power: Optional[Decimal] = None
    cash_balance: Optional[Decimal] = None
    cash_available_for_trading: Optional[Decimal] = None
    cash_receipts: Optional[Decimal] = None
    
    # Account values
    liquidation_value: Optional[Decimal] = None
    long_market_value: Optional[Decimal] = None
    short_market_value: Optional[Decimal] = None
    equity: Optional[Decimal] = None
    
    # Day trading specific
    day_trading_buying_power: Optional[Decimal] = None
    day_trading_buying_power_call: Optional[Decimal] = None
    maintenance_call: Optional[Decimal] = None
    maintenance_requirement: Optional[Decimal] = None
    
    # Margin specific
    reg_t_call: Optional[Decimal] = None
    house_excess: Optional[Decimal] = None
    
    @classmethod
    def from_schwab_data(cls, data: Dict[str, Any]) -> "SchwabBalance":
        """Create balance from Schwab API response"""
        current_balances = data.get("currentBalances", {})
        initial_balances = data.get("initialBalances", {})
        projected_balances = data.get("projectedBalances", {})
        
        # Use current balances as primary, fall back to others
        balance_data = {**initial_balances, **projected_balances, **current_balances}
        
        return cls(
            available_funds=Decimal(str(balance_data["availableFunds"])) if balance_data.get("availableFunds") else None,
            buying_power=Decimal(str(balance_data["buyingPower"])) if balance_data.get("buyingPower") else None,
            cash_balance=Decimal(str(balance_data["cashBalance"])) if balance_data.get("cashBalance") else None,
            cash_available_for_trading=Decimal(str(balance_data["cashAvailableForTrading"])) if balance_data.get("cashAvailableForTrading") else None,
            cash_receipts=Decimal(str(balance_data["cashReceipts"])) if balance_data.get("cashReceipts") else None,
            liquidation_value=Decimal(str(balance_data["liquidationValue"])) if balance_data.get("liquidationValue") else None,
            long_market_value=Decimal(str(balance_data["longMarketValue"])) if balance_data.get("longMarketValue") else None,
            short_market_value=Decimal(str(balance_data["shortMarketValue"])) if balance_data.get("shortMarketValue") else None,
            equity=Decimal(str(balance_data["equity"])) if balance_data.get("equity") else None,
            day_trading_buying_power=Decimal(str(balance_data["dayTradingBuyingPower"])) if balance_data.get("dayTradingBuyingPower") else None,
            day_trading_buying_power_call=Decimal(str(balance_data["dayTradingBuyingPowerCall"])) if balance_data.get("dayTradingBuyingPowerCall") else None,
            maintenance_call=Decimal(str(balance_data["maintenanceCall"])) if balance_data.get("maintenanceCall") else None,
            maintenance_requirement=Decimal(str(balance_data["maintenanceRequirement"])) if balance_data.get("maintenanceRequirement") else None,
            reg_t_call=Decimal(str(balance_data["regTCall"])) if balance_data.get("regTCall") else None,
            house_excess=Decimal(str(balance_data["houseExcess"])) if balance_data.get("houseExcess") else None
        )


class SchwabAccountInfo(BaseModel):
    """Complete account information"""
    
    # Account identifiers
    account_id: str
    account_hash: str
    account_number: Optional[str] = None
    nickname: Optional[str] = None
    
    # Account details
    account_type: Optional[str] = None
    is_day_trader: bool = False
    is_closing_only_restricted: bool = False
    round_trips: int = 0
    
    # Financial information
    balance: Optional[SchwabBalance] = None
    positions: List[SchwabPosition] = Field(default_factory=list)
    
    # Metadata
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
    def equity_positions(self) -> List[SchwabPosition]:
        """Get equity positions only"""
        return [pos for pos in self.positions if pos.asset_type == "EQUITY"]
    
    @property
    def option_positions(self) -> List[SchwabPosition]:
        """Get option positions only"""
        return [pos for pos in self.positions if pos.asset_type == "OPTION"]
    
    @property
    def active_positions(self) -> List[SchwabPosition]:
        """Get positions with non-zero quantity"""
        return [pos for pos in self.positions if not pos.is_flat]
    
    @classmethod
    def from_schwab_data(cls, data: Dict[str, Any]) -> "SchwabAccountInfo":
        """Create account info from Schwab API response"""
        securities_account = data.get("securitiesAccount", data)
        
        # Parse positions
        positions = []
        for pos_data in securities_account.get("positions", []):
            try:
                position = SchwabPosition.from_schwab_data(pos_data)
                positions.append(position)
            except Exception as e:
                logger.warning(f"Failed to parse position: {e}")
        
        # Parse balance
        balance = None
        if any(key in securities_account for key in ["currentBalances", "initialBalances", "projectedBalances"]):
            balance = SchwabBalance.from_schwab_data(securities_account)
        
        return cls(
            account_id=securities_account.get("accountId", ""),
            account_hash=data.get("hashValue", securities_account.get("hashValue", "")),
            account_number=securities_account.get("accountNumber"),
            nickname=securities_account.get("nickname"),
            account_type=securities_account.get("type"),
            is_day_trader=securities_account.get("isDayTrader", False),
            is_closing_only_restricted=securities_account.get("isClosingOnlyRestricted", False),
            round_trips=securities_account.get("roundTrips", 0),
            balance=balance,
            positions=positions
        )


class SchwabTransaction(BaseModel):
    """Transaction history entry"""
    
    # Transaction identifiers
    transaction_id: str
    account_id: str
    activity_id: Optional[str] = None
    
    # Transaction details
    type: str
    description: str
    status: str
    trade_date: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    
    # Financial details
    net_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    
    # Position details
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    
    @classmethod
    def from_schwab_data(cls, data: Dict[str, Any]) -> "SchwabTransaction":
        """Create transaction from Schwab API response"""
        # Parse dates
        trade_date = None
        if data.get("tradeDate"):
            try:
                trade_date = datetime.fromisoformat(data["tradeDate"])
            except ValueError:
                pass
        
        settlement_date = None
        if data.get("settlementDate"):
            try:
                settlement_date = datetime.fromisoformat(data["settlementDate"])
            except ValueError:
                pass
        
        # Extract instrument details
        instrument_data = data.get("transactionItem", {}).get("instrument", {})
        
        return cls(
            transaction_id=str(data.get("transactionId", "")),
            account_id=data.get("accountId", ""),
            activity_id=data.get("activityId"),
            type=data.get("type", ""),
            description=data.get("description", ""),
            status=data.get("status", ""),
            trade_date=trade_date,
            settlement_date=settlement_date,
            net_amount=Decimal(str(data["netAmount"])) if data.get("netAmount") else None,
            gross_amount=Decimal(str(data["grossAmount"])) if data.get("grossAmount") else None,
            fees=Decimal(str(data["fees"])) if data.get("fees") else None,
            symbol=instrument_data.get("symbol"),
            quantity=Decimal(str(data.get("transactionItem", {}).get("amount", 0))),
            price=Decimal(str(data.get("transactionItem", {}).get("price", 0))) if data.get("transactionItem", {}).get("price") else None
        )


class SchwabAccount:
    """
    Schwab account management API client.
    
    Provides access to:
    - Account information and details
    - Account balances and buying power
    - Portfolio positions
    - Transaction history
    """
    
    def __init__(self, auth: SchwabAuth):
        self.auth = auth
        self.base_url = "https://api.schwabapi.com/trader/v1"
    
    async def get_account_numbers(self) -> List[Dict[str, str]]:
        """
        Get account numbers for the authenticated user.
        
        Returns:
            List[Dict[str, str]]: List of account info with hash values
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.base_url}/accounts/accountNumbers",
                headers=headers
            )
            response.raise_for_status()
            
            accounts = response.json()
            logger.info(f"Retrieved {len(accounts)} account numbers")
            
            return accounts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting account numbers: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get account numbers: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting account numbers: {e}")
            raise
    
    async def get_account(self, account_hash: str, fields: Optional[str] = None) -> SchwabAccountInfo:
        """
        Get detailed account information.
        
        Args:
            account_hash: Account hash identifier
            fields: Optional fields to include (positions, orders)
            
        Returns:
            SchwabAccountInfo: Complete account information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if fields:
                params["fields"] = fields
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_hash}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            account_info = SchwabAccountInfo.from_schwab_data(data)
            
            logger.info(f"Retrieved account info for {account_hash}")
            return account_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting account: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get account: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            raise
    
    async def get_all_accounts(self, fields: Optional[str] = None) -> List[SchwabAccountInfo]:
        """
        Get information for all accounts.
        
        Args:
            fields: Optional fields to include (positions, orders)
            
        Returns:
            List[SchwabAccountInfo]: List of account information
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            if fields:
                params["fields"] = fields
            
            response = await client.get(
                f"{self.base_url}/accounts",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse accounts
            accounts = []
            for account_data in data:
                try:
                    account_info = SchwabAccountInfo.from_schwab_data(account_data)
                    accounts.append(account_info)
                except Exception as e:
                    logger.warning(f"Failed to parse account: {e}")
            
            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting accounts: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get accounts: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            raise
    
    async def get_positions(self, account_hash: str) -> List[SchwabPosition]:
        """
        Get positions for an account.
        
        Args:
            account_hash: Account hash identifier
            
        Returns:
            List[SchwabPosition]: List of positions
        """
        account_info = await self.get_account(account_hash, fields="positions")
        return account_info.positions
    
    async def get_transactions(
        self,
        account_hash: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> List[SchwabTransaction]:
        """
        Get transaction history for an account.
        
        Args:
            account_hash: Account hash identifier
            start_date: Start date for transaction search
            end_date: End date for transaction search
            transaction_type: Filter by transaction type
            
        Returns:
            List[SchwabTransaction]: List of transactions
        """
        try:
            token = await self.auth.get_valid_access_token()
            client = await self.auth.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            params = {}
            
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            params["startDate"] = start_date.strftime("%Y-%m-%d")
            params["endDate"] = end_date.strftime("%Y-%m-%d")
            
            if transaction_type:
                params["type"] = transaction_type
            
            response = await client.get(
                f"{self.base_url}/accounts/{account_hash}/transactions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse transactions
            transactions = []
            for txn_data in data:
                try:
                    transaction = SchwabTransaction.from_schwab_data(txn_data)
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