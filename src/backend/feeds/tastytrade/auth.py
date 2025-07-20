"""
Tastytrade OAuth2 Authentication

Handles the OAuth2 flow for Tastytrade API access including token management,
refresh, and authorization URL generation.
"""

import asyncio
import logging
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse

import httpx
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class TastytradeCredentials(BaseModel):
    """Tastytrade API credentials configuration"""
    
    client_id: str = Field(..., description="Tastytrade client ID")
    client_secret: str = Field(..., description="Tastytrade client secret")
    redirect_uri: str = Field(default="https://127.0.0.1:8182/oauth/tastytrade/callback", description="OAuth redirect URI")
    sandbox: bool = Field(default=False, description="Use sandbox environment")
    
    class Config:
        str_strip_whitespace = True


class TastytradeTokens(BaseModel):
    """OAuth2 tokens from Tastytrade API"""
    
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 28800  # 8 hours default
    expires_at: datetime
    scope: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if access token is expired (with 5 minute buffer)"""
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (self.expires_at - buffer)
    
    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until token expires"""
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))


class TastytradeAuth:
    """
    Tastytrade OAuth2 authentication manager.
    
    Handles the complete OAuth2 flow including:
    - Authorization URL generation
    - Token exchange from authorization code
    - Automatic token refresh
    - Secure token storage and management
    """
    
    def __init__(self, credentials: TastytradeCredentials):
        self.credentials = credentials
        self.tokens: Optional[TastytradeTokens] = None
        self._client_session: Optional[httpx.AsyncClient] = None
        
        # Tastytrade API URLs
        if credentials.sandbox:
            self.auth_base_url = "https://api.cert.tastyworks.com"
            self.api_base_url = "https://api.cert.tastyworks.com"
        else:
            self.auth_base_url = "https://api.tastyworks.com"
            self.api_base_url = "https://api.tastyworks.com"
        
        logger.info(f"Initialized Tastytrade authentication for {'sandbox' if credentials.sandbox else 'production'} environment")
    
    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper headers"""
        if self._client_session is None:
            self._client_session = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "TraderTerminal/1.0"
                }
            )
        return self._client_session
    
    async def close(self):
        """Close HTTP client"""
        if self._client_session:
            await self._client_session.aclose()
            self._client_session = None
    
    def generate_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth2 authorization URL for user consent.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL for user to visit
        """
        if state is None:
            state = secrets.token_urlsafe(16)
        
        params = {
            "response_type": "code",
            "client_id": self.credentials.client_id,
            "redirect_uri": self.credentials.redirect_uri,
            "scope": "read_only trading", 
            "state": state
        }
        
        auth_url = f"{self.auth_base_url}/oauth/authorize?{urlencode(params)}"
        logger.info(f"Generated authorization URL with state: {state}")
        
        return auth_url
    
    async def exchange_code_for_tokens(self, authorization_code: str) -> TastytradeTokens:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Code received from OAuth callback
            
        Returns:
            TastytradeTokens: Token pair for API access
        """
        client = await self.get_http_client()
        
        # Create basic auth header
        auth_string = f"{self.credentials.client_id}:{self.credentials.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.credentials.redirect_uri
        }
        
        try:
            response = await client.post(
                f"{self.auth_base_url}/oauth/token",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            # Create tokens object
            expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 28800))
            
            self.tokens = TastytradeTokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 28800),
                expires_at=expires_at,
                scope=token_data.get("scope")
            )
            
            logger.info("Successfully exchanged authorization code for tokens")
            return self.tokens
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token exchange: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Token exchange failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error during token exchange: {e}")
            raise
    
    async def refresh_access_token(self) -> TastytradeTokens:
        """
        Refresh access token using refresh token.
        
        Returns:
            TastytradeTokens: New token pair
        """
        if not self.tokens or not self.tokens.refresh_token:
            raise Exception("No refresh token available for token refresh")
        
        client = await self.get_http_client()
        
        # Create basic auth header
        auth_string = f"{self.credentials.client_id}:{self.credentials.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens.refresh_token
        }
        
        try:
            response = await client.post(
                f"{self.auth_base_url}/oauth/token",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            # Create new tokens object
            expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 28800))
            
            self.tokens = TastytradeTokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", self.tokens.refresh_token),  # May not provide new refresh token
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 28800),
                expires_at=expires_at,
                scope=token_data.get("scope")
            )
            
            logger.info("Successfully refreshed access token")
            return self.tokens
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token refresh: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Token refresh failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error during token refresh: {e}")
            raise
    
    async def get_valid_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token
        """
        if not self.tokens:
            raise Exception("No tokens available. Complete OAuth flow first.")
        
        if self.tokens.is_expired:
            logger.info("Access token expired, refreshing...")
            await self.refresh_access_token()
        
        return self.tokens.access_token
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test API connection with current tokens.
        
        Returns:
            Dict[str, Any]: Connection test result
        """
        try:
            token = await self.get_valid_access_token()
            client = await self.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Test with customer endpoint
            response = await client.get(
                f"{self.api_base_url}/customers/me",
                headers=headers
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "message": f"Successfully connected to Tastytrade API ({'sandbox' if self.credentials.sandbox else 'production'})",
                "token_expires_in": self.tokens.expires_in_seconds if self.tokens else 0,
                "environment": "sandbox" if self.credentials.sandbox else "production"
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "environment": "sandbox" if self.credentials.sandbox else "production"
            }
    
    def extract_code_from_callback_url(self, callback_url: str) -> str:
        """
        Extract authorization code from OAuth callback URL.
        
        Args:
            callback_url: Full callback URL with parameters
            
        Returns:
            str: Authorization code
        """
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        
        if "code" not in query_params:
            error = query_params.get("error", ["Unknown error"])[0]
            error_description = query_params.get("error_description", ["No description"])[0]
            raise Exception(f"OAuth error: {error} - {error_description}")
        
        return query_params["code"][0]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            "authenticated": self.tokens is not None,
            "token_valid": self.tokens and not self.tokens.is_expired if self.tokens else False,
            "expires_in": self.tokens.expires_in_seconds if self.tokens else 0,
            "environment": "sandbox" if self.credentials.sandbox else "production",
            "scope": self.tokens.scope if self.tokens else None
        }