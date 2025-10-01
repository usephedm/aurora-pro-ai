"""
Tests for Aurora Pro AI Security Utilities
"""
import pytest
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    sanitize_input
)


def test_password_hashing():
    """Test password hashing and verification"""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_access_token():
    """Test JWT token creation and verification"""
    data = {"sub": "user123", "role": "admin"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"


def test_invalid_token():
    """Test invalid token verification"""
    invalid_token = "invalid.token.here"
    payload = verify_token(invalid_token)
    
    assert payload is None


def test_sanitize_input():
    """Test input sanitization"""
    dangerous = "<script>alert('xss')</script>"
    sanitized = sanitize_input(dangerous)
    
    assert "<script>" not in sanitized
    assert ">" not in sanitized
    
    safe = "Hello World"
    assert sanitize_input(safe) == safe
