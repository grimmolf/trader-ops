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
    Validate required webhook headers and security requirements.
    
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
    
    # Check user agent (TradingView should identify itself)
    user_agent = headers.get('user-agent', '').lower()
    trusted_agents = ['tradingview', 'tv-webhook', 'webhook', 'python', 'curl']  # Allow testing tools
    if user_agent and not any(agent in user_agent for agent in trusted_agents):
        logger.warning(f"Suspicious user agent: {user_agent}")
    
    # Check for suspicious headers that might indicate attack attempts
    suspicious_headers = ['x-forwarded-host', 'x-original-host', 'x-rewrite-url']
    for suspicious_header in suspicious_headers:
        if suspicious_header in headers:
            logger.warning(f"Potentially suspicious header detected: {suspicious_header}")
    
    return True, None


class WebhookSecurityValidator:
    """Enhanced security validation for webhook requests"""
    
    def __init__(self):
        self.suspicious_patterns = [
            # SQL injection patterns
            r"(?i)(union|select|insert|update|delete|drop|exec|script)",
            # XSS patterns  
            r"(?i)(<script|javascript:|data:text/html)",
            # Command injection patterns
            r"(?i)(;|\||&|`|\$\(|\${)",
            # Path traversal patterns
            r"(\.\./|\.\.\\|\.\.\%2f)",
        ]
        
    def validate_payload_security(self, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate payload for security threats.
        
        Args:
            payload: Parsed JSON payload
            
        Returns:
            tuple: (is_safe, security_issue)
        """
        import re
        
        def check_value_security(value, path=""):
            """Recursively check values for security threats"""
            if isinstance(value, str):
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, value):
                        return False, f"Suspicious pattern detected in {path}: {pattern}"
            elif isinstance(value, dict):
                for key, val in value.items():
                    safe, issue = check_value_security(val, f"{path}.{key}")
                    if not safe:
                        return safe, issue
            elif isinstance(value, list):
                for i, val in enumerate(value):
                    safe, issue = check_value_security(val, f"{path}[{i}]")
                    if not safe:
                        return safe, issue
            return True, None
        
        return check_value_security(payload)
    
    def validate_tradingview_fields(self, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that payload contains expected TradingView fields.
        
        Args:
            payload: Parsed JSON payload
            
        Returns:
            tuple: (is_valid, validation_error)
        """
        required_fields = ['symbol', 'action']
        recommended_fields = ['quantity', 'price', 'timestamp']
        
        # Check required fields
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"
        
        # Validate field types and ranges
        if 'quantity' in payload:
            try:
                quantity = float(payload['quantity'])
                if quantity <= 0 or quantity > 1000:  # Reasonable limits
                    return False, f"Invalid quantity: {quantity}"
            except (ValueError, TypeError):
                return False, "Invalid quantity format"
        
        if 'price' in payload:
            try:
                price = float(payload['price'])
                if price <= 0 or price > 1000000:  # Reasonable price limits
                    return False, f"Invalid price: {price}"
            except (ValueError, TypeError):
                return False, "Invalid price format"
        
        # Validate symbol format
        symbol = payload.get('symbol', '')
        if len(symbol) > 20 or not symbol.replace('-', '').replace('_', '').isalnum():
            return False, f"Invalid symbol format: {symbol}"
        
        # Validate action
        valid_actions = ['buy', 'sell', 'long', 'short', 'close', 'exit']
        action = payload.get('action', '').lower()
        if action not in valid_actions:
            return False, f"Invalid action: {action}"
        
        return True, None


# Global security validator instance
webhook_security_validator = WebhookSecurityValidator()