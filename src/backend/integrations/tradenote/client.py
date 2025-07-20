"""
TradeNote HTTP Client for TraderTerminal

Provides automated trade logging to TradeNote journal system via REST API.
Handles authentication, error handling, and batch uploads.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
import httpx
from httpx import AsyncClient, RequestError, HTTPStatusError, TimeoutException

from .models import (
    TradeNoteConfig,
    TradeNoteTradeData,
    TradeNoteExecutionData,
    TradeNoteResponse,
    TradeNoteCalendarData
)

logger = logging.getLogger(__name__)


class TradeNoteClientError(Exception):
    """Base exception for TradeNote client errors"""
    pass


class TradeNoteAuthError(TradeNoteClientError):
    """Authentication error with TradeNote API"""
    pass


class TradeNoteAPIError(TradeNoteClientError):
    """API error from TradeNote service"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class TradeNoteClient:
    """
    HTTP client for TradeNote trade journal integration.
    
    Provides methods for uploading trade data, retrieving analytics,
    and managing trade journal entries in TradeNote.
    """
    
    def __init__(self, config: TradeNoteConfig):
        """
        Initialize TradeNote client with configuration.
        
        Args:
            config: TradeNote configuration with API credentials
        """
        self.config = config
        self._client: Optional[AsyncClient] = None
        self._session_headers = {
            "Content-Type": "application/json",
            "User-Agent": "TraderTerminal/1.0 (TradeNote Integration)"
        }
        
        # Parse server app configuration
        self._parse_server_info = {
            "serverURL": config.base_url.rstrip('/'),
            "appId": config.app_id,
            "masterKey": config.master_key
        }
        
        logger.info(f"TradeNote client initialized for {config.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Initialize HTTP client connection"""
        if self._client is None:
            timeout = httpx.Timeout(
                connect=10.0,
                read=self.config.timeout_seconds,
                write=10.0,
                pool=5.0
            )
            
            self._client = AsyncClient(
                timeout=timeout,
                headers=self._session_headers,
                follow_redirects=True
            )
            
            # Test connection
            try:
                await self._health_check()
                logger.info("TradeNote client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to TradeNote: {e}")
                await self.disconnect()
                raise TradeNoteClientError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close HTTP client connection"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("TradeNote client disconnected")
    
    async def _health_check(self) -> bool:
        """Check if TradeNote service is healthy"""
        try:
            response = await self._client.get(f"{self.config.base_url}/health")
            return response.status_code == 200
        except Exception:
            # Try alternate health endpoint
            try:
                response = await self._client.get(f"{self.config.base_url}/api/ping")
                return response.status_code == 200
            except Exception:
                return False
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> httpx.Response:
        """
        Make authenticated HTTP request to TradeNote API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request payload data
            params: Query parameters
            retry_count: Current retry attempt
            
        Returns:
            HTTP response
            
        Raises:
            TradeNoteAPIError: For API errors
            TradeNoteAuthError: For authentication errors
        """
        if not self._client:
            raise TradeNoteClientError("Client not connected. Call connect() first.")
        
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Add Parse server authentication
        request_data = data.copy() if data else {}
        if data:
            request_data.update(self._parse_server_info)
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=request_data if data else None,
                params=params
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise TradeNoteAuthError("Invalid API credentials or expired session")
            
            # Handle other HTTP errors
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    pass
                
                raise TradeNoteAPIError(
                    f"API request failed: {response.status_code} {response.reason_phrase}",
                    status_code=response.status_code,
                    response_data=error_data
                )
            
            return response
            
        except (RequestError, TimeoutException) as e:
            # Retry on network errors
            if retry_count < self.config.retry_attempts:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            raise TradeNoteAPIError(f"Network error after {retry_count} retries: {e}")
        
        except HTTPStatusError as e:
            raise TradeNoteAPIError(f"HTTP error: {e}")
    
    async def upload_trade(self, trade_data: TradeNoteTradeData) -> TradeNoteResponse:
        """
        Upload a single trade to TradeNote.
        
        Args:
            trade_data: Trade data to upload
            
        Returns:
            API response
        """
        return await self.upload_trades([trade_data])
    
    async def upload_trades(self, trades: List[TradeNoteTradeData]) -> TradeNoteResponse:
        """
        Upload multiple trades to TradeNote in batch.
        
        Args:
            trades: List of trade data to upload
            
        Returns:
            API response with upload results
        """
        if not trades:
            raise ValueError("No trades provided for upload")
        
        if not self.config.enabled:
            logger.info("TradeNote integration disabled, skipping upload")
            return TradeNoteResponse(
                success=True,
                message="Upload skipped - integration disabled"
            )
        
        execution_data = TradeNoteExecutionData(
            data=trades,
            selected_broker=self.config.broker_name,
            upload_mfe_prices=self.config.upload_mfe_prices
        )
        
        try:
            logger.info(f"Uploading {len(trades)} trades to TradeNote")
            
            response = await self._make_request(
                method="POST",
                endpoint="/api/trades",
                data=execution_data.to_api_payload()
            )
            
            result_data = response.json()
            
            # Parse TradeNote response format
            if result_data.get("result") and result_data["result"].get("success"):
                logger.info(f"Successfully uploaded {len(trades)} trades")
                return TradeNoteResponse(
                    success=True,
                    message=f"Uploaded {len(trades)} trades successfully",
                    data=result_data.get("result", {})
                )
            else:
                errors = result_data.get("result", {}).get("errors", ["Unknown error"])
                logger.error(f"Trade upload failed: {errors}")
                return TradeNoteResponse(
                    success=False,
                    message="Trade upload failed",
                    errors=errors
                )
                
        except TradeNoteAPIError as e:
            logger.error(f"API error uploading trades: {e}")
            return TradeNoteResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading trades: {e}")
            return TradeNoteResponse(
                success=False,
                message="Unexpected error during upload",
                errors=[str(e)]
            )
    
    async def get_calendar_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TradeNoteCalendarData]:
        """
        Retrieve calendar heat-map data from TradeNote.
        
        Args:
            start_date: Start date for calendar data
            end_date: End date for calendar data
            
        Returns:
            List of calendar data points
        """
        params = {}
        if start_date:
            params["startDate"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["endDate"] = end_date.strftime("%Y-%m-%d")
        
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/api/calendar",
                params=params
            )
            
            result_data = response.json()
            calendar_data = []
            
            for item in result_data.get("result", []):
                calendar_data.append(TradeNoteCalendarData(
                    date=item["date"],
                    value=item["value"],
                    trades_count=item.get("tradesCount", 0),
                    win_rate=item.get("winRate")
                ))
            
            return calendar_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve calendar data: {e}")
            return []
    
    async def get_trade_statistics(self) -> Dict[str, Any]:
        """
        Retrieve trade statistics from TradeNote.
        
        Returns:
            Dictionary of trade statistics
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/api/stats"
            )
            
            return response.json().get("result", {})
            
        except Exception as e:
            logger.error(f"Failed to retrieve trade statistics: {e}")
            return {}
    
    async def delete_trades(self, trade_ids: List[str]) -> TradeNoteResponse:
        """
        Delete trades from TradeNote by trade IDs.
        
        Args:
            trade_ids: List of trade IDs to delete
            
        Returns:
            API response
        """
        try:
            response = await self._make_request(
                method="POST",
                endpoint="/api/trades/delete",
                data={"tradeIds": trade_ids}
            )
            
            result_data = response.json()
            
            if result_data.get("result", {}).get("success"):
                return TradeNoteResponse(
                    success=True,
                    message=f"Deleted {len(trade_ids)} trades"
                )
            else:
                return TradeNoteResponse(
                    success=False,
                    message="Failed to delete trades",
                    errors=[result_data.get("error", "Unknown error")]
                )
                
        except Exception as e:
            logger.error(f"Failed to delete trades: {e}")
            return TradeNoteResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
    
    async def sync_account_trades(
        self,
        account_name: str,
        trades: List[TradeNoteTradeData],
        clear_existing: bool = False
    ) -> TradeNoteResponse:
        """
        Sync all trades for a specific account.
        
        Args:
            account_name: Trading account identifier
            trades: Complete list of trades for the account
            clear_existing: Whether to clear existing trades first
            
        Returns:
            Sync operation result
        """
        logger.info(f"Syncing {len(trades)} trades for account {account_name}")
        
        try:
            # Optional: Clear existing trades for account first
            if clear_existing:
                # This would require implementing account-specific trade deletion
                # For now, we'll just upload new trades
                pass
            
            # Upload all trades in batches to avoid timeout
            batch_size = 100
            total_uploaded = 0
            
            for i in range(0, len(trades), batch_size):
                batch = trades[i:i + batch_size]
                result = await self.upload_trades(batch)
                
                if result.success:
                    total_uploaded += len(batch)
                else:
                    logger.error(f"Batch upload failed: {result.message}")
                    return result
            
            return TradeNoteResponse(
                success=True,
                message=f"Synced {total_uploaded} trades for account {account_name}"
            )
            
        except Exception as e:
            logger.error(f"Account sync failed: {e}")
            return TradeNoteResponse(
                success=False,
                message=f"Sync failed: {e}",
                errors=[str(e)]
            )


# Factory function for creating configured client
async def create_tradenote_client(config: TradeNoteConfig) -> TradeNoteClient:
    """
    Create and connect TradeNote client.
    
    Args:
        config: TradeNote configuration
        
    Returns:
        Connected TradeNote client
    """
    client = TradeNoteClient(config)
    await client.connect()
    return client


# Utility function for one-off trade uploads
async def upload_trade_to_tradenote(
    trade_data: TradeNoteTradeData,
    config: TradeNoteConfig
) -> TradeNoteResponse:
    """
    Upload a single trade to TradeNote (convenience function).
    
    Args:
        trade_data: Trade data to upload
        config: TradeNote configuration
        
    Returns:
        Upload result
    """
    async with TradeNoteClient(config) as client:
        return await client.upload_trade(trade_data)