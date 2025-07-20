"""
Secure Credential Loader for TraderTerminal Brokers

Loads credentials from secure storage with environment variable fallback.
Provides type-safe credential loading for all broker integrations.
"""

import os
import logging
from typing import Optional, Dict, Any, Type, TypeVar
from dataclasses import dataclass
from pathlib import Path

from .credential_manager import get_credential_manager, CredentialManagerError

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class BrokerCredentials:
    """Base class for broker credentials"""
    pass


@dataclass
class TastytradeCredentials(BrokerCredentials):
    """Tastytrade API credentials"""
    client_id: str
    client_secret: str
    redirect_uri: str
    sandbox: bool = True


@dataclass
class SchwabCredentials(BrokerCredentials):
    """Charles Schwab API credentials"""
    client_id: str
    client_secret: str
    redirect_uri: str
    refresh_token: Optional[str] = None
    account_id: Optional[str] = None


@dataclass
class TradovateCredentials(BrokerCredentials):
    """Tradovate API credentials"""
    username: str
    password: str
    app_id: str
    app_version: str = "1.0"
    cid: str = ""
    sec: str = ""
    demo: bool = False


@dataclass
class TopstepXCredentials(BrokerCredentials):
    """TopstepX API credentials"""
    username: str
    password: str
    api_key: str
    api_url: str = "https://api.topstepx.com"
    sandbox: bool = True


@dataclass
class DataServiceCredentials(BrokerCredentials):
    """Data service API credentials"""
    alpha_vantage_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    thenewsapi_key: Optional[str] = None
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None


class SecureCredentialLoader:
    """
    Secure credential loader with environment variable fallback
    
    Loading priority:
    1. Secure credential storage (keyring/encrypted file)
    2. Environment variables (with warning)
    3. Default values (if provided)
    """
    
    def __init__(self, account: str = "default", warn_env_usage: bool = True):
        """
        Initialize credential loader
        
        Args:
            account: Account namespace for credential storage
            warn_env_usage: Whether to warn when using environment variables
        """
        self.account = account
        self.warn_env_usage = warn_env_usage
        self.manager = get_credential_manager()
        self._warned_keys = set()  # Track warned environment variables
    
    async def _get_credential(self, key: str, env_key: str = None, default: Any = None) -> Any:
        """
        Get credential with fallback chain
        
        Args:
            key: Secure storage key
            env_key: Environment variable key (defaults to key)
            default: Default value if not found
            
        Returns:
            Credential value or default
        """
        if env_key is None:
            env_key = key
        
        # 1. Try secure storage first
        try:
            value = await self.manager.get_credential(key, self.account)
            if value is not None:
                logger.debug(f"Loaded {key} from secure storage")
                return value
        except Exception as e:
            logger.warning(f"Failed to load {key} from secure storage: {e}")
        
        # 2. Fallback to environment variable
        env_value = os.getenv(env_key)
        if env_value is not None:
            if self.warn_env_usage and env_key not in self._warned_keys:
                logger.warning(f"⚠️  Using environment variable for {env_key}. "
                             f"Consider migrating to secure storage: "
                             f"python scripts/manage_credentials.py store --key {key}")
                self._warned_keys.add(env_key)
            
            logger.debug(f"Loaded {key} from environment variable")
            return env_value
        
        # 3. Use default value
        if default is not None:
            logger.debug(f"Using default value for {key}")
            return default
        
        # 4. Not found anywhere
        logger.warning(f"Credential not found: {key}")
        return None
    
    async def load_tastytrade_credentials(self) -> Optional[TastytradeCredentials]:
        """Load Tastytrade credentials"""
        try:
            client_id = await self._get_credential(
                "TASTYTRADE_CLIENT_ID", 
                default="e3f4389d-8216-40f6-af76-c7dc957977fe"  # Pre-configured
            )
            
            client_secret = await self._get_credential("TASTYTRADE_CLIENT_SECRET")
            if not client_secret:
                logger.error("Tastytrade client secret not found. Run: "
                           "python scripts/manage_credentials.py setup-broker --broker tastytrade")
                return None
            
            redirect_uri = await self._get_credential(
                "TASTYTRADE_REDIRECT_URI",
                default="https://127.0.0.1:8182/oauth/tastytrade/callback"
            )
            
            sandbox_str = await self._get_credential("TASTYTRADE_SANDBOX", default="true")
            sandbox = sandbox_str.lower() in ["true", "1", "yes"]
            
            return TastytradeCredentials(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                sandbox=sandbox
            )
            
        except Exception as e:
            logger.error(f"Failed to load Tastytrade credentials: {e}")
            return None
    
    async def load_schwab_credentials(self) -> Optional[SchwabCredentials]:
        """Load Charles Schwab credentials"""
        try:
            client_id = await self._get_credential("SCHWAB_CLIENT_ID")
            client_secret = await self._get_credential("SCHWAB_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                logger.error("Schwab credentials not found. Run: "
                           "python scripts/manage_credentials.py setup-broker --broker schwab")
                return None
            
            redirect_uri = await self._get_credential(
                "SCHWAB_REDIRECT_URI",
                default="https://127.0.0.1:8182/oauth/schwab/callback"
            )
            
            refresh_token = await self._get_credential("SCHWAB_REFRESH_TOKEN")
            account_id = await self._get_credential("SCHWAB_ACCOUNT_ID")
            
            return SchwabCredentials(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                refresh_token=refresh_token,
                account_id=account_id
            )
            
        except Exception as e:
            logger.error(f"Failed to load Schwab credentials: {e}")
            return None
    
    async def load_tradovate_credentials(self) -> Optional[TradovateCredentials]:
        """Load Tradovate credentials"""
        try:
            username = await self._get_credential("TRADOVATE_USERNAME")
            password = await self._get_credential("TRADOVATE_PASSWORD")
            app_id = await self._get_credential("TRADOVATE_APP_ID")
            
            if not username or not password or not app_id:
                logger.error("Tradovate credentials not found. Run: "
                           "python scripts/manage_credentials.py setup-broker --broker tradovate")
                return None
            
            app_version = await self._get_credential("TRADOVATE_APP_VERSION", default="1.0")
            cid = await self._get_credential("TRADOVATE_CID", default="")
            sec = await self._get_credential("TRADOVATE_SEC", default="")
            
            demo_str = await self._get_credential("TRADOVATE_DEMO", default="false")
            demo = demo_str.lower() in ["true", "1", "yes"]
            
            return TradovateCredentials(
                username=username,
                password=password,
                app_id=app_id,
                app_version=app_version,
                cid=cid,
                sec=sec,
                demo=demo
            )
            
        except Exception as e:
            logger.error(f"Failed to load Tradovate credentials: {e}")
            return None
    
    async def load_topstepx_credentials(self) -> Optional[TopstepXCredentials]:
        """Load TopstepX credentials"""
        try:
            username = await self._get_credential("TOPSTEPX_USERNAME")
            password = await self._get_credential("TOPSTEPX_PASSWORD")
            api_key = await self._get_credential("TOPSTEPX_API_KEY")
            
            if not username or not password or not api_key:
                logger.error("TopstepX credentials not found. Run: "
                           "python scripts/manage_credentials.py setup-broker --broker topstepx")
                return None
            
            api_url = await self._get_credential(
                "TOPSTEPX_API_URL",
                default="https://api.topstepx.com"
            )
            
            sandbox_str = await self._get_credential("TOPSTEPX_SANDBOX", default="true")
            sandbox = sandbox_str.lower() in ["true", "1", "yes"]
            
            return TopstepXCredentials(
                username=username,
                password=password,
                api_key=api_key,
                api_url=api_url,
                sandbox=sandbox
            )
            
        except Exception as e:
            logger.error(f"Failed to load TopstepX credentials: {e}")
            return None
    
    async def load_data_service_credentials(self) -> DataServiceCredentials:
        """Load data service credentials (returns partial credentials if some are missing)"""
        try:
            return DataServiceCredentials(
                alpha_vantage_api_key=await self._get_credential("ALPHA_VANTAGE_API_KEY"),
                fred_api_key=await self._get_credential("FRED_API_KEY"),
                thenewsapi_key=await self._get_credential("THENEWSAPI_KEY"),
                binance_api_key=await self._get_credential("BINANCE_API_KEY"),
                binance_api_secret=await self._get_credential("BINANCE_API_SECRET"),
                coinbase_api_key=await self._get_credential("COINBASE_API_KEY"),
                coinbase_api_secret=await self._get_credential("COINBASE_API_SECRET")
            )
            
        except Exception as e:
            logger.error(f"Failed to load data service credentials: {e}")
            return DataServiceCredentials()
    
    async def store_oauth_tokens(self, broker: str, tokens: Dict[str, Any]) -> bool:
        """
        Store OAuth tokens securely after authentication
        
        Args:
            broker: Broker name (tastytrade, schwab, etc.)
            tokens: Dictionary of tokens (access_token, refresh_token, etc.)
            
        Returns:
            True if stored successfully
        """
        try:
            success_count = 0
            total_count = 0
            
            for token_type, token_value in tokens.items():
                if token_value:
                    key = f"{broker.upper()}_{token_type.upper()}"
                    success = await self.manager.store_credential(key, str(token_value), self.account)
                    if success:
                        success_count += 1
                    total_count += 1
            
            logger.info(f"Stored {success_count}/{total_count} {broker} tokens")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Failed to store {broker} tokens: {e}")
            return False
    
    async def get_oauth_tokens(self, broker: str) -> Dict[str, Optional[str]]:
        """
        Retrieve stored OAuth tokens
        
        Args:
            broker: Broker name
            
        Returns:
            Dictionary of tokens
        """
        try:
            tokens = {}
            token_types = ["access_token", "refresh_token", "expires_at", "token_type"]
            
            for token_type in token_types:
                key = f"{broker.upper()}_{token_type.upper()}"
                value = await self.manager.get_credential(key, self.account)
                tokens[token_type] = value
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to retrieve {broker} tokens: {e}")
            return {}
    
    async def validate_required_credentials(self, broker: str) -> Dict[str, bool]:
        """
        Validate that required credentials are available for a broker
        
        Args:
            broker: Broker name
            
        Returns:
            Dictionary of validation results
        """
        validation_results = {}
        
        try:
            if broker == "tastytrade":
                creds = await self.load_tastytrade_credentials()
                validation_results = {
                    "client_id": bool(creds and creds.client_id),
                    "client_secret": bool(creds and creds.client_secret),
                    "redirect_uri": bool(creds and creds.redirect_uri)
                }
            
            elif broker == "schwab":
                creds = await self.load_schwab_credentials()
                validation_results = {
                    "client_id": bool(creds and creds.client_id),
                    "client_secret": bool(creds and creds.client_secret),
                    "redirect_uri": bool(creds and creds.redirect_uri)
                }
            
            elif broker == "tradovate":
                creds = await self.load_tradovate_credentials()
                validation_results = {
                    "username": bool(creds and creds.username),
                    "password": bool(creds and creds.password),
                    "app_id": bool(creds and creds.app_id)
                }
            
            elif broker == "topstepx":
                creds = await self.load_topstepx_credentials()
                validation_results = {
                    "username": bool(creds and creds.username),
                    "password": bool(creds and creds.password),
                    "api_key": bool(creds and creds.api_key)
                }
            
            elif broker == "data_services":
                creds = await self.load_data_service_credentials()
                validation_results = {
                    "alpha_vantage": bool(creds.alpha_vantage_api_key),
                    "fred": bool(creds.fred_api_key),
                    "news": bool(creds.thenewsapi_key)
                }
            
            else:
                validation_results = {"error": f"Unknown broker: {broker}"}
            
        except Exception as e:
            validation_results = {"error": str(e)}
        
        return validation_results


# Global loader instance
_credential_loader: Optional[SecureCredentialLoader] = None


def get_credential_loader(account: str = "default") -> SecureCredentialLoader:
    """Get the global credential loader instance"""
    global _credential_loader
    if _credential_loader is None or _credential_loader.account != account:
        _credential_loader = SecureCredentialLoader(account)
    return _credential_loader


# Convenience functions for common credential loading
async def load_tastytrade_credentials(account: str = "default") -> Optional[TastytradeCredentials]:
    """Load Tastytrade credentials"""
    loader = get_credential_loader(account)
    return await loader.load_tastytrade_credentials()


async def load_schwab_credentials(account: str = "default") -> Optional[SchwabCredentials]:
    """Load Charles Schwab credentials"""
    loader = get_credential_loader(account)
    return await loader.load_schwab_credentials()


async def load_tradovate_credentials(account: str = "default") -> Optional[TradovateCredentials]:
    """Load Tradovate credentials"""
    loader = get_credential_loader(account)
    return await loader.load_tradovate_credentials()


async def load_topstepx_credentials(account: str = "default") -> Optional[TopstepXCredentials]:
    """Load TopstepX credentials"""
    loader = get_credential_loader(account)
    return await loader.load_topstepx_credentials()


async def load_data_service_credentials(account: str = "default") -> DataServiceCredentials:
    """Load data service credentials"""
    loader = get_credential_loader(account)
    return await loader.load_data_service_credentials()