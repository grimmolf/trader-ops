"""
Webhook security utilities for signature verification and secret management.

Provides HMAC-SHA256 signature verification to ensure webhook authenticity
from TradingView and prevent unauthorized access.
"""

import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Args:
        body: Raw webhook payload bytes
        signature: Provided signature from webhook header
        secret: Webhook secret for verification
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not body or not signature or not secret:
        logger.warning("Missing required parameters for signature verification")
        return False
    
    try:
        # Generate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(f"Invalid webhook signature. Expected: {expected_signature[:8]}..., Got: {signature[:8]}...")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


def generate_webhook_secret() -> str:
    """
    Generate a secure webhook secret.
    
    Returns:
        str: URL-safe base64 encoded secret (256 bits of entropy)
    """
    return secrets.token_urlsafe(32)


def generate_alert_id() -> str:
    """
    Generate unique alert ID.
    
    Returns:
        str: Unique alert identifier with timestamp prefix
    """
    timestamp = int(time.time())
    random_suffix = secrets.token_hex(4)
    return f"alert_{timestamp}_{random_suffix}"


class WebhookRateLimit:
    """
    Simple rate limiting for webhook endpoints.
    
    Prevents webhook spam and abuse by tracking request counts
    per source IP address.
    """
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests: Dict[str, list] = {}  # IP -> [timestamp, ...]
    
    def is_allowed(self, ip_address: str) -> bool:
        """
        Check if request from IP is allowed based on rate limit.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(minutes=self.window_minutes)
        
        # Get existing requests for this IP
        if ip_address not in self.requests:
            self.requests[ip_address] = []
        
        # Remove old requests outside the window
        self.requests[ip_address] = [
            req_time for req_time in self.requests[ip_address] 
            if req_time > cutoff_time
        ]
        
        # Check if under limit
        if len(self.requests[ip_address]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP {ip_address}")
            return False
        
        # Add current request
        self.requests[ip_address].append(current_time)
        return True
    
    def cleanup_old_entries(self):
        """Clean up old rate limit entries to prevent memory bloat"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_minutes * 2)
        
        for ip_address in list(self.requests.keys()):
            self.requests[ip_address] = [
                req_time for req_time in self.requests[ip_address]
                if req_time > cutoff_time
            ]
            
            # Remove empty entries
            if not self.requests[ip_address]:
                del self.requests[ip_address]


# Global rate limiter instance
webhook_rate_limiter = WebhookRateLimit(max_requests=50, window_minutes=1)


def validate_webhook_headers(headers: Dict[str, str]) -> tuple[bool, Optional[str]]:
    """
    Validate required webhook headers.
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_headers = ['content-type']
    
    for header in required_headers:
        if header not in headers:
            return False, f"Missing required header: {header}"
    
    # Check content type
    content_type = headers.get('content-type', '').lower()
    if 'application/json' not in content_type:
        return False, f"Invalid content-type: {content_type}. Expected application/json"
    
    return True, None