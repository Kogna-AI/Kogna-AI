"""
Unit tests for core/security.py

Tests JWT token creation, validation, and password hashing utilities.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

# Import after conftest sets environment variables
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_token,
)
from core.config import SECRET_KEY, ALGORITHM


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    def test_creates_valid_token(self):
        """Should create a token that can be decoded."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_correct_payload(self):
        """Token should contain the original data plus standard claims."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["token_type"] == "access"
        assert "iat" in payload
        assert "exp" in payload

    def test_token_has_correct_type(self):
        """Token should have token_type set to 'access'."""
        token = create_access_token({"sub": "user-123"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["token_type"] == "access"

    def test_token_expires_in_future(self):
        """Token expiration should be in the future."""
        token = create_access_token({"sub": "user-123"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # exp is a UTC timestamp, so compare with UTC time
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        assert exp_time > datetime.utcnow()


class TestCreateRefreshToken:
    """Tests for create_refresh_token function."""

    def test_returns_tuple_with_three_elements(self):
        """Should return (token, jti, expires_at) tuple."""
        result = create_refresh_token({"sub": "user-123"})

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_token_is_valid_jwt(self):
        """Token should be a valid JWT string."""
        token, jti, expires_at = create_refresh_token({"sub": "user-123"})

        assert isinstance(token, str)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload is not None

    def test_jti_is_unique(self):
        """Each refresh token should have a unique JTI."""
        _, jti1, _ = create_refresh_token({"sub": "user-123"})
        _, jti2, _ = create_refresh_token({"sub": "user-123"})

        assert jti1 != jti2

    def test_token_has_refresh_type(self):
        """Token should have token_type set to 'refresh'."""
        token, _, _ = create_refresh_token({"sub": "user-123"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["token_type"] == "refresh"

    def test_token_contains_jti(self):
        """Token payload should contain JTI claim."""
        token, jti, _ = create_refresh_token({"sub": "user-123"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["jti"] == jti

    def test_expires_at_is_datetime(self):
        """expires_at should be a datetime object."""
        _, _, expires_at = create_refresh_token({"sub": "user-123"})

        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.utcnow()


class TestDecodeAccessToken:
    """Tests for decode_access_token function."""

    def test_decodes_valid_token(self):
        """Should successfully decode a valid access token."""
        token = create_access_token({"sub": "user-123", "email": "test@example.com"})
        payload = decode_access_token(token)

        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"

    def test_rejects_invalid_token(self):
        """Should raise HTTPException for invalid token."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid.token.string")

        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_rejects_refresh_token(self):
        """Should reject refresh tokens used as access tokens."""
        from fastapi import HTTPException

        refresh_token, _, _ = create_refresh_token({"sub": "user-123"})

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(refresh_token)

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail

    def test_rejects_expired_token(self, expired_token):
        """Should reject expired tokens."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(expired_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


class TestDecodeRefreshToken:
    """Tests for decode_refresh_token function."""

    def test_decodes_valid_refresh_token(self):
        """Should successfully decode a valid refresh token."""
        token, jti, _ = create_refresh_token({"sub": "user-123"})
        payload = decode_refresh_token(token)

        assert payload["sub"] == "user-123"
        assert payload["jti"] == jti

    def test_rejects_access_token(self):
        """Should reject access tokens used as refresh tokens."""
        from fastapi import HTTPException

        access_token = create_access_token({"sub": "user-123"})

        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token(access_token)

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail

    def test_rejects_invalid_token(self):
        """Should raise HTTPException for invalid token."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token("invalid.token.string")

        assert exc_info.value.status_code == 401


class TestHashToken:
    """Tests for hash_token function."""

    def test_returns_string(self):
        """Should return a string hash."""
        result = hash_token("test-token")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_same_input_same_output(self):
        """Same token should produce same hash."""
        hash1 = hash_token("test-token")
        hash2 = hash_token("test-token")

        assert hash1 == hash2

    def test_different_input_different_output(self):
        """Different tokens should produce different hashes."""
        hash1 = hash_token("token-1")
        hash2 = hash_token("token-2")

        assert hash1 != hash2

    def test_hash_is_sha256_length(self):
        """Hash should be 64 characters (SHA256 hex digest)."""
        result = hash_token("test-token")

        assert len(result) == 64
