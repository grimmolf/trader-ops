"""
Tradovate OAuth2 Authentication

Handles authentication flow, token management, and API access for Tradovate.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TradovateCredentials(BaseModel):
    """Tradovate API credentials configuration"""
    
    username: str = Field(..., description="Tradovate account username")
    password: str = Field(..., description="Tradovate account password")  
    app_id: str = Field(..., description="Tradovate application ID")
    app_version: str = Field(default="1.0", description="Application version")
    demo: bool = Field(default=True, description="Use demo environment")
    
    class Config:
        str_strip_whitespace = True


class TradovateTokens(BaseModel):
    """OAuth2 tokens from Tradovate"""
    
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    token_type: str = "Bearer"
    
    @property
    def is_expired(self) -> bool:
        """Check if access token is expired"""
        return datetime.utcnow() >= self.expires_at
    
    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until token expires"""
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))


class TradovateAuth:
    """
    Tradovate OAuth2 authentication manager.
    
    Handles the complete authentication flow including:
    - Initial login with username/password
    - Access token management and refresh
    - Automatic token renewal
    - Demo vs Live environment switching
    """
    
    def __init__(self, credentials: TradovateCredentials):
        self.credentials = credentials
        self.tokens: Optional[TradovateTokens] = None
        self._client_session: Optional[httpx.AsyncClient] = None
        
        # Set base URLs based on environment
        if credentials.demo:
            self.auth_url = "https://demo.tradovateapi.com/v1"
            self.api_url = "https://demo.tradovateapi.com/v1"
            self.ws_url = "wss://md-demo.tradovateapi.com/v1/websocket"
        else:
            self.auth_url = "https://live.tradovateapi.com/v1"
            self.api_url = "https://live.tradovateapi.com/v1"
            self.ws_url = "wss://md.tradovateapi.com/v1/websocket"
        
        logger.info(f"Initialized Tradovate auth for {'demo' if credentials.demo else 'live'} environment")
    
    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client_session is None:
            self._client_session = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": f"TraderTerminal/{self.credentials.app_version}"
                }
            )
        return self._client_session
    
    async def close(self):
        """Close HTTP client"""
        if self._client_session:
            await self._client_session.aclose()
            self._client_session = None
    
    async def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if needed.
        
        Returns:
            str: Valid access token
            
        Raises:
            Exception: If authentication fails
        """
        # If no tokens or expired, authenticate
        if not self.tokens or self.tokens.is_expired:
            await self._authenticate()
        
        return self.tokens.access_token
    
    async def _authenticate(self) -> TradovateTokens:
        """
        Perform OAuth2 authentication with Tradovate.
        
        Returns:
            TradovateTokens: Fresh authentication tokens
        """
        logger.info("Authenticating with Tradovate...")
        
        client = await self.get_http_client()
        
        # Build authentication payload
        auth_payload = {
            "name": self.credentials.username,
            "password": self.credentials.password,
            "appId": self.credentials.app_id,
            "appVersion": self.credentials.app_version,
            "cid": 0,  # Client ID (0 for web)
            "sec": ""  # Security (empty for username/password)
        }
        
        try:
            # Make authentication request
            response = await client.post(
                f"{self.auth_url}/auth/accesstokenrequest",
                json=auth_payload
            )
            
            # Handle response
            if response.status_code == 200:
                data = response.json()
                
                # Extract token data
                access_token = data.get("accessToken")
                expiration_time = data.get("expirationTime")  # seconds from now
                
                if not access_token or not expiration_time:
                    raise ValueError("Invalid response: missing token or expiration")
                
                # Calculate expiration datetime (subtract 60 seconds for safety)
                expires_at = datetime.utcnow() + timedelta(seconds=expiration_time - 60)
                
                # Create tokens object
                self.tokens = TradovateTokens(
                    access_token=access_token,
                    expires_at=expires_at
                )
                
                logger.info(f"Authentication successful. Token expires at {expires_at}")
                return self.tokens
                
            elif response.status_code == 401:
                error_data = response.json()
                error_msg = error_data.get("errorText", "Authentication failed")
                logger.error(f"Authentication failed: {error_msg}")
                raise ValueError(f"Invalid credentials: {error_msg}")
                
            else:
                error_text = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Authentication error: {error_text}")
                raise Exception(f"Authentication failed: {error_text}")
                
        except httpx.RequestError as e:
            logger.error(f"Network error during authentication: {e}")
            raise Exception(f"Network error: {e}")
    
    async def refresh_access_token(self) -> str:
        """
        Refresh access token using refresh token.
        
        Note: Tradovate doesn't appear to use refresh tokens in the traditional sense.
        This method re-authenticates with credentials.
        
        Returns:
            str: New access token
        """
        logger.info("Refreshing access token...")
        await self._authenticate()
        return self.tokens.access_token
    
    async def get_authenticated_headers(self) -> Dict[str, str]:
        """
        Get headers with valid authentication token.
        
        Returns:
            Dict[str, str]: Headers including Authorization
        """
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make authenticated HTTP request to Tradovate API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/account/list")
            **kwargs: Additional arguments for httpx.request()
            
        Returns:
            httpx.Response: API response
        """
        client = await self.get_http_client()
        headers = await self.get_authenticated_headers()
        
        # Merge with any provided headers
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        # Build full URL
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = await client.request(method, url, **kwargs)
            
            # Handle token expiration
            if response.status_code == 401:
                logger.warning("Token expired, refreshing...")
                await self.refresh_access_token()
                
                # Retry with new token
                headers = await self.get_authenticated_headers()
                kwargs["headers"] = headers
                response = await client.request(method, url, **kwargs)
            
            return response
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test API connection and authentication.
        
        Returns:
            Dict[str, Any]: Connection test results
        """
        try:
            # Try to get account list as a simple test
            response = await self.make_authenticated_request("GET", "/account/list")
            
            if response.status_code == 200:
                accounts = response.json()
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "environment": "demo" if self.credentials.demo else "live",
                    "account_count": len(accounts) if isinstance(accounts, list) else 0,
                    "token_expires_in": self.tokens.expires_in_seconds if self.tokens else 0
                }
            else:
                return {
                    "status": "error",
                    "message": f"API test failed: HTTP {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Connection test failed: {str(e)}"
            }
    
    def __repr__(self) -> str:
        env = "demo" if self.credentials.demo else "live"
        token_status = "valid" if self.tokens and not self.tokens.is_expired else "expired/missing"
        return f"TradovateAuth(env={env}, token={token_status})"