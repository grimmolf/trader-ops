"""
TopstepX Authentication and API Client

Handles OAuth2 authentication, token management, and API access for TopstepX
funded trading accounts with proper security and error handling.
"""

import asyncio
import logging
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from urllib.parse import urlencode, parse_qs, urlparse

import httpx
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class TopstepXCredentials(BaseModel):
    """TopstepX API credentials configuration"""
    
    api_key: str = Field(..., description="TopstepX API key from ProjectX dashboard")
    username: str = Field(..., description="TopstepX account username")
    environment: str = Field(default="LIVE", description="Trading environment: LIVE or DEMO")
    
    class Config:
        str_strip_whitespace = True
    
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['LIVE', 'DEMO']:
            raise ValueError('Environment must be LIVE or DEMO')
        return v


class TopstepXTokens(BaseModel):
    """OAuth2 tokens from TopstepX API"""
    
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1 hour default
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


class TopstepXAuth:
    """
    TopstepX authentication manager.
    
    Handles OAuth2 flow for TopstepX API access including:
    - API key authentication
    - Token management and refresh
    - Environment-specific endpoints
    - Secure HTTP client management
    """
    
    def __init__(self, credentials: TopstepXCredentials):
        self.credentials = credentials
        self.tokens: Optional[TopstepXTokens] = None
        self._client_session: Optional[httpx.AsyncClient] = None
        
        # TopstepX API URLs
        if credentials.environment == "LIVE":
            self.auth_base_url = "https://api.projectx.com/v1/auth"
            self.api_base_url = "https://api.projectx.com/v1"
            self.ws_market_url = "wss://api.projectx.com/markethub"
            self.ws_user_url = "wss://api.projectx.com/userhub"
        else:  # DEMO
            self.auth_base_url = "https://demo-api.projectx.com/v1/auth"
            self.api_base_url = "https://demo-api.projectx.com/v1"
            self.ws_market_url = "wss://demo-api.projectx.com/markethub"
            self.ws_user_url = "wss://demo-api.projectx.com/userhub"
        
        logger.info(f"Initialized TopstepX authentication for {credentials.environment} environment")
    
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
    
    async def authenticate(self) -> TopstepXTokens:
        """
        Authenticate with TopstepX API using API key.
        
        Returns:
            TopstepXTokens: Access token and metadata
        """
        client = await self.get_http_client()
        
        headers = {
            "Authorization": f"ApiKey {self.credentials.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "username": self.credentials.username,
            "environment": self.credentials.environment
        }
        
        try:
            response = await client.post(
                f"{self.auth_base_url}/token",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            # Create tokens object
            expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
            
            self.tokens = TopstepXTokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                expires_at=expires_at,
                scope=token_data.get("scope")
            )
            
            logger.info("Successfully authenticated with TopstepX API")
            return self.tokens
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during authentication: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Authentication failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            raise
    
    async def refresh_access_token(self) -> TopstepXTokens:
        """
        Refresh access token using refresh token or re-authenticate.
        
        Returns:
            TopstepXTokens: New token pair
        """
        if not self.tokens or not self.tokens.refresh_token:
            # No refresh token available, perform full authentication
            logger.info("No refresh token available, performing full authentication")
            return await self.authenticate()
        
        client = await self.get_http_client()
        
        headers = {
            "Authorization": f"Bearer {self.tokens.refresh_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens.refresh_token
        }
        
        try:
            response = await client.post(
                f"{self.auth_base_url}/refresh",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            # Create new tokens object
            expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
            
            self.tokens = TopstepXTokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", self.tokens.refresh_token),
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                expires_at=expires_at,
                scope=token_data.get("scope")
            )
            
            logger.info("Successfully refreshed access token")
            return self.tokens
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token refresh: {e.response.status_code} - {e.response.text}")
            # Fall back to full authentication
            logger.info("Token refresh failed, performing full authentication")
            return await self.authenticate()
        except Exception as e:
            logger.error(f"Error during token refresh: {e}")
            # Fall back to full authentication
            return await self.authenticate()
    
    async def get_valid_access_token(self) -> str:
        """
        Get a valid access token, refreshing or authenticating if necessary.
        
        Returns:
            str: Valid access token
        """
        if not self.tokens:
            logger.info("No tokens available, performing initial authentication")
            await self.authenticate()
        
        if self.tokens and self.tokens.is_expired:
            logger.info("Access token expired, refreshing...")
            await self.refresh_access_token()
        
        if not self.tokens:
            raise Exception("Failed to obtain valid access token")
        
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
            
            # Test with accounts endpoint
            response = await client.get(
                f"{self.api_base_url}/accounts",
                headers=headers
            )
            response.raise_for_status()
            
            accounts_data = response.json()
            
            return {
                "status": "success",
                "message": f"Successfully connected to TopstepX API ({self.credentials.environment})",
                "accounts_found": len(accounts_data) if isinstance(accounts_data, list) else 1,
                "token_expires_in": self.tokens.expires_in_seconds if self.tokens else 0,
                "environment": self.credentials.environment
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "environment": self.credentials.environment
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            "authenticated": self.tokens is not None,
            "token_valid": self.tokens and not self.tokens.is_expired if self.tokens else False,
            "expires_in": self.tokens.expires_in_seconds if self.tokens else 0,
            "environment": self.credentials.environment,
            "username": self.credentials.username,
            "scope": self.tokens.scope if self.tokens else None
        }
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get user account information.
        
        Returns:
            Dict[str, Any]: User information
        """
        try:
            token = await self.get_valid_access_token()
            client = await self.get_http_client()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{self.api_base_url}/user/profile",
                headers=headers
            )
            response.raise_for_status()
            
            user_data = response.json()
            logger.info("Retrieved user profile information")
            
            return user_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user info: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get user info: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise
    
    def get_websocket_urls(self) -> Dict[str, str]:
        """Get WebSocket URLs for real-time data"""
        return {
            "market_data": self.ws_market_url,
            "user_data": self.ws_user_url
        }
    
    async def validate_api_access(self) -> bool:
        """
        Validate that API access is properly configured.
        
        Returns:
            bool: True if API access is valid
        """
        try:
            test_result = await self.test_connection()
            return test_result["status"] == "success"
        except Exception as e:
            logger.error(f"API access validation failed: {e}")
            return False