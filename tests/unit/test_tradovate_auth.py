"""
Unit tests for Tradovate authentication module.

Tests authentication, token management, and credential validation
for both demo and live trading environments.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import aiohttp

from src.backend.feeds.tradovate.auth import (
    TradovateAuth, TradovateCredentials, TradovateTokens
)


class TestTradovateCredentials:
    """Test TradovateCredentials model"""
    
    def test_create_demo_credentials(self, demo_credentials):
        """Test creating demo credentials"""
        assert demo_credentials.username == "demo_user"
        assert demo_credentials.password == "demo_password" 
        assert demo_credentials.api_key == "demo_api_key"
        assert demo_credentials.api_secret == "demo_api_secret"
        assert demo_credentials.demo is True
        assert demo_credentials.base_url == "https://demo.tradovateapi.com/v1"
    
    def test_create_live_credentials(self, live_credentials):
        """Test creating live credentials"""
        assert live_credentials.demo is False
        assert live_credentials.base_url == "https://live.tradovateapi.com/v1"
    
    def test_credentials_validation(self):
        """Test credential validation"""
        # Valid credentials
        creds = TradovateCredentials(
            username="user",
            password="pass", 
            api_key="key",
            api_secret="secret"
        )
        assert creds is not None
        
        # Test empty username
        with pytest.raises(ValueError):
            TradovateCredentials(
                username="",
                password="pass",
                api_key="key", 
                api_secret="secret"
            )


class TestTokenResponse:
    """Test TokenResponse model"""
    
    def test_create_token_response(self, valid_token_response):
        """Test creating token response"""
        assert valid_token_response.access_token == "valid_access_token_12345"
        assert valid_token_response.refresh_token == "valid_refresh_token_67890"
        assert valid_token_response.token_type == "Bearer"
        assert valid_token_response.user_id == 12345
        assert valid_token_response.account_id == 67890
    
    def test_token_expiration(self, valid_token_response, expired_token_response):
        """Test token expiration logic"""
        # Valid token should not be expired
        assert not valid_token_response.is_expired
        
        # Expired token should be expired
        assert expired_token_response.is_expired
    
    def test_token_expires_soon(self, valid_token_response):
        """Test token expires soon logic"""
        # Fresh token should not expire soon
        assert not valid_token_response.expires_soon
        
        # Token expiring in 5 minutes should expire soon
        soon_expiring = TokenResponse(
            access_token="token",
            refresh_token="refresh",
            expires_in=300,  # 5 minutes
            token_type="Bearer",
            scope="trading",
            user_id=123,
            account_id=456,
            created_at=datetime.utcnow() - timedelta(minutes=55)  # Created 55 minutes ago
        )
        assert soon_expiring.expires_soon


class TestTradovateAuth:
    """Test TradovateAuth class"""
    
    def test_auth_initialization(self, demo_credentials):
        """Test authentication initialization"""
        auth = TradovateAuth(demo_credentials)
        
        assert auth.credentials == demo_credentials
        assert auth.tokens is None
        assert not auth._authenticated
        assert auth.session is not None
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self, demo_credentials, valid_token_response):
        """Test successful authentication"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "accessToken": "valid_access_token_12345",
            "refreshToken": "valid_refresh_token_67890",
            "expirationTime": "2024-01-01T12:00:00Z",
            "userId": 12345,
            "accountId": 67890
        })
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            result = await auth.authenticate()
            
            assert result is not None
            assert result.access_token == "valid_access_token_12345" 
            assert auth._authenticated is True
            assert auth.tokens is not None
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, demo_credentials):
        """Test authentication failure"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock failed HTTP response
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={
            "error": "Invalid credentials"
        })
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            with pytest.raises(AuthenticationError):
                await auth.authenticate()
            
            assert not auth._authenticated
            assert auth.tokens is None
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, demo_credentials, valid_token_response):
        """Test token refresh functionality"""
        auth = TradovateAuth(demo_credentials)
        auth.tokens = valid_token_response
        auth._authenticated = True
        
        # Mock refresh response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "accessToken": "new_access_token_12345",
            "refreshToken": "new_refresh_token_67890", 
            "expirationTime": "2024-01-01T13:00:00Z",
            "userId": 12345,
            "accountId": 67890
        })
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            result = await auth.refresh_token()
            
            assert result is not None
            assert result.access_token == "new_access_token_12345"
            assert auth.tokens.access_token == "new_access_token_12345"
    
    @pytest.mark.asyncio
    async def test_get_access_token_valid(self, demo_credentials, valid_token_response):
        """Test getting valid access token"""
        auth = TradovateAuth(demo_credentials)
        auth.tokens = valid_token_response
        auth._authenticated = True
        
        token = await auth.get_access_token()
        assert token == "valid_access_token_12345"
    
    @pytest.mark.asyncio
    async def test_get_access_token_expired(self, demo_credentials, expired_token_response):
        """Test getting access token when expired"""
        auth = TradovateAuth(demo_credentials)
        auth.tokens = expired_token_response
        auth._authenticated = True
        
        # Mock refresh response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "accessToken": "refreshed_access_token",
            "refreshToken": "refreshed_refresh_token",
            "expirationTime": "2024-01-01T14:00:00Z",
            "userId": 12345,
            "accountId": 67890
        })
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            token = await auth.get_access_token()
            assert token == "refreshed_access_token"
    
    @pytest.mark.asyncio
    async def test_get_access_token_not_authenticated(self, demo_credentials):
        """Test getting access token when not authenticated"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock authentication response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "accessToken": "new_access_token",
            "refreshToken": "new_refresh_token",
            "expirationTime": "2024-01-01T14:00:00Z",
            "userId": 12345,
            "accountId": 67890
        })
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            token = await auth.get_access_token()
            assert token == "new_access_token"
            assert auth._authenticated is True
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, demo_credentials):
        """Test successful connection test"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock authentication
        mock_auth_response = MagicMock()
        mock_auth_response.status = 200
        mock_auth_response.json = AsyncMock(return_value={
            "accessToken": "test_token",
            "refreshToken": "test_refresh",
            "expirationTime": "2024-01-01T14:00:00Z",
            "userId": 12345,
            "accountId": 67890
        })
        
        # Mock test API call
        mock_test_response = MagicMock()
        mock_test_response.status = 200
        mock_test_response.json = AsyncMock(return_value={"status": "ok"})
        
        with patch.object(auth.session, 'post', return_value=mock_auth_response):
            with patch.object(auth.session, 'get', return_value=mock_test_response):
                result = await auth.test_connection()
                
                assert result["status"] == "success"
                assert "response_time" in result
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, demo_credentials):
        """Test connection test failure"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock authentication failure
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={"error": "Unauthorized"})
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            result = await auth.test_connection()
            
            assert result["status"] == "failed"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_close_session(self, demo_credentials):
        """Test closing authentication session"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock session close
        auth.session.close = AsyncMock()
        
        await auth.close()
        auth.session.close.assert_called_once()
    
    @pytest.mark.asyncio  
    async def test_make_authenticated_request(self, demo_credentials, valid_token_response):
        """Test making authenticated API requests"""
        auth = TradovateAuth(demo_credentials)
        auth.tokens = valid_token_response
        auth._authenticated = True
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        
        with patch.object(auth.session, 'get', return_value=mock_response) as mock_get:
            result = await auth.make_authenticated_request("GET", "/test")
            
            assert result["data"] == "test"
            mock_get.assert_called_once()
            
            # Check that Authorization header was added
            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer valid_access_token_12345'
    
    @pytest.mark.asyncio
    async def test_environment_urls(self):
        """Test demo vs live environment URLs"""
        demo_creds = TradovateCredentials(
            username="demo", password="pass", api_key="key", api_secret="secret", demo=True
        )
        live_creds = TradovateCredentials(
            username="live", password="pass", api_key="key", api_secret="secret", demo=False
        )
        
        demo_auth = TradovateAuth(demo_creds)
        live_auth = TradovateAuth(live_creds)
        
        assert "demo.tradovateapi.com" in demo_creds.base_url
        assert "live.tradovateapi.com" in live_creds.base_url


class TestAuthenticationEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_network_timeout(self, demo_credentials):
        """Test handling of network timeouts"""
        auth = TradovateAuth(demo_credentials)
        
        with patch.object(auth.session, 'post', side_effect=aiohttp.ClientTimeout):
            with pytest.raises(AuthenticationError):
                await auth.authenticate()
    
    @pytest.mark.asyncio
    async def test_malformed_response(self, demo_credentials):
        """Test handling of malformed API responses"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock malformed response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            with pytest.raises(AuthenticationError):
                await auth.authenticate()
    
    @pytest.mark.asyncio
    async def test_refresh_token_failure(self, demo_credentials, expired_token_response):
        """Test handling of refresh token failure"""
        auth = TradovateAuth(demo_credentials)
        auth.tokens = expired_token_response
        auth._authenticated = True
        
        # Mock failed refresh
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={"error": "Invalid refresh token"})
        
        with patch.object(auth.session, 'post', return_value=mock_response):
            # Should fall back to re-authentication
            mock_auth_response = MagicMock()
            mock_auth_response.status = 200
            mock_auth_response.json = AsyncMock(return_value={
                "accessToken": "new_token_after_reauth",
                "refreshToken": "new_refresh_after_reauth",
                "expirationTime": "2024-01-01T15:00:00Z",
                "userId": 12345,
                "accountId": 67890
            })
            
            with patch.object(auth, 'authenticate', return_value=TokenResponse(
                access_token="new_token_after_reauth",
                refresh_token="new_refresh_after_reauth", 
                expires_in=3600,
                token_type="Bearer",
                scope="trading",
                user_id=12345,
                account_id=67890
            )):
                token = await auth.get_access_token()
                assert token == "new_token_after_reauth"


class TestAuthenticationIntegration:
    """Integration tests for authentication workflow"""
    
    @pytest.mark.asyncio
    async def test_full_authentication_workflow(self, demo_credentials):
        """Test complete authentication workflow"""
        auth = TradovateAuth(demo_credentials)
        
        # Mock initial authentication
        mock_auth_response = MagicMock()
        mock_auth_response.status = 200
        mock_auth_response.json = AsyncMock(return_value={
            "accessToken": "initial_token",
            "refreshToken": "initial_refresh",
            "expirationTime": "2024-01-01T12:00:00Z",
            "userId": 12345,
            "accountId": 67890
        })
        
        # Mock test connection
        mock_test_response = MagicMock()
        mock_test_response.status = 200
        mock_test_response.json = AsyncMock(return_value={"status": "ok"})
        
        # Mock API request
        mock_api_response = MagicMock()
        mock_api_response.status = 200
        mock_api_response.json = AsyncMock(return_value={"accounts": []})
        
        with patch.object(auth.session, 'post', return_value=mock_auth_response):
            with patch.object(auth.session, 'get', side_effect=[mock_test_response, mock_api_response]):
                # Step 1: Authenticate
                token_response = await auth.authenticate()
                assert token_response.access_token == "initial_token"
                
                # Step 2: Test connection
                test_result = await auth.test_connection()
                assert test_result["status"] == "success"
                
                # Step 3: Make authenticated request
                api_result = await auth.make_authenticated_request("GET", "/accounts")
                assert "accounts" in api_result
    
    @pytest.mark.asyncio
    async def test_concurrent_token_requests(self, demo_credentials, valid_token_response):
        """Test handling of concurrent token requests"""
        auth = TradovateAuth(demo_credentials)
        auth.tokens = valid_token_response
        auth._authenticated = True
        
        # Multiple concurrent requests for access token
        tokens = await asyncio.gather(*[
            auth.get_access_token() for _ in range(5)
        ])
        
        # All should return the same valid token
        assert all(token == "valid_access_token_12345" for token in tokens)