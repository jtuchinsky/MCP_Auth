"""Unit tests for JWT service."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.services import jwt_service


class TestCreateAccessToken:
    """Test create_access_token() function."""

    def test_create_access_token_basic(self):
        """Test creating a basic access token."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_payload_structure(self):
        """Test that token payload has correct structure."""
        token = jwt_service.create_access_token(
            user_id=123,
            email="user@example.com",
            tenant_id=2,
            role="MEMBER",
        )

        # Decode without verification to inspect payload
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == "123"
        assert payload["email"] == "user@example.com"
        assert payload["tenant_id"] == "2"
        assert payload["role"] == "MEMBER"
        assert "exp" in payload
        assert "iat" in payload
        assert payload["scopes"] == []

    def test_create_access_token_with_scopes(self):
        """Test creating token with OAuth2 scopes."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="ADMIN",
            scopes=["read", "write", "admin"],
        )

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["scopes"] == ["read", "write", "admin"]

    def test_create_access_token_with_audience(self):
        """Test creating token with OAuth2 audience."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
            audience="https://api.example.com/resource",
        )

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )

        assert payload["aud"] == "https://api.example.com/resource"

    def test_create_access_token_expiration(self):
        """Test that token has correct expiration time."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="MEMBER",
        )

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        # Token should expire in approximately access_token_expire_minutes
        time_diff = (exp - iat).total_seconds()
        expected_diff = settings.access_token_expire_seconds

        # Allow 1 second tolerance for test execution time
        assert abs(time_diff - expected_diff) < 1

    def test_create_access_token_uses_hs256(self):
        """Test that token is signed with HS256 algorithm."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
        )

        # Decode header to check algorithm
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_create_access_token_is_valid(self):
        """Test that created token can be successfully decoded."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
        )

        # Should not raise exception
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload is not None

    def test_create_access_token_different_users(self):
        """Test that tokens for different users have different payloads."""
        token1 = jwt_service.create_access_token(1, "user1@example.com", 1, "OWNER")
        token2 = jwt_service.create_access_token(2, "user2@example.com", 1, "MEMBER")

        payload1 = jwt.decode(
            token1, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        payload2 = jwt.decode(
            token2, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert payload1["sub"] != payload2["sub"]
        assert payload1["email"] != payload2["email"]


class TestCreateRefreshToken:
    """Test create_refresh_token() function."""

    def test_create_refresh_token_returns_string(self):
        """Test that refresh token is a string."""
        token = jwt_service.create_refresh_token()

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_is_url_safe(self):
        """Test that refresh token is URL-safe."""
        token = jwt_service.create_refresh_token()

        # URL-safe tokens should only contain alphanumeric, -, and _
        import re

        assert re.match(r"^[A-Za-z0-9_-]+$", token)

    def test_create_refresh_token_is_random(self):
        """Test that refresh tokens are randomly generated."""
        token1 = jwt_service.create_refresh_token()
        token2 = jwt_service.create_refresh_token()

        assert token1 != token2

    def test_create_refresh_token_sufficient_length(self):
        """Test that refresh token has sufficient length (32 bytes)."""
        token = jwt_service.create_refresh_token()

        # URL-safe base64 encoding of 32 bytes results in ~43 characters
        assert len(token) >= 40

    def test_create_refresh_token_multiple_unique(self):
        """Test that multiple refresh tokens are all unique."""
        tokens = [jwt_service.create_refresh_token() for _ in range(100)]

        # All tokens should be unique
        assert len(tokens) == len(set(tokens))


class TestDecodeAccessToken:
    """Test decode_access_token() function."""

    def test_decode_access_token_success(self):
        """Test decoding a valid access token."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
        )

        payload = jwt_service.decode_access_token(token)

        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"
        assert payload["tenant_id"] == "1"
        assert payload["role"] == "OWNER"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_access_token_with_scopes(self):
        """Test decoding token with scopes."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="MEMBER",
            scopes=["read", "write"],
        )

        payload = jwt_service.decode_access_token(token)

        assert payload["scopes"] == ["read", "write"]

    def test_decode_access_token_with_audience(self):
        """Test decoding token with audience."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="ADMIN",
            audience="https://api.example.com",
        )

        payload = jwt_service.decode_access_token(token)

        assert payload["aud"] == "https://api.example.com"

    def test_decode_access_token_expired(self):
        """Test decoding an expired token raises error."""
        # Create token that expires immediately
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(seconds=1)

        payload = {
            "sub": "1",
            "email": "test@example.com",
            "exp": expired_time,
            "iat": now - timedelta(seconds=10),
            "scopes": [],
        }

        token = jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(AuthenticationError, match="Token has expired"):
            jwt_service.decode_access_token(token)

    def test_decode_access_token_invalid_signature(self):
        """Test decoding token with invalid signature raises error."""
        token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
        )

        # Tamper with token by changing last character
        tampered_token = token[:-1] + ("X" if token[-1] != "X" else "Y")

        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_service.decode_access_token(tampered_token)

    def test_decode_access_token_malformed(self):
        """Test decoding malformed token raises error."""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_service.decode_access_token("not.a.valid.token")

    def test_decode_access_token_empty_string(self):
        """Test decoding empty string raises error."""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_service.decode_access_token("")

    def test_decode_access_token_wrong_algorithm(self):
        """Test decoding token signed with wrong algorithm raises error."""
        # Create token with different algorithm (if available)
        payload = {
            "sub": "1",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "scopes": [],
        }

        # Try to sign with none algorithm (should fail verification)
        token = jwt.encode(payload, settings.secret_key, algorithm="HS512")

        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_service.decode_access_token(token)


class TestJWTServiceIntegration:
    """Integration tests for JWT service functions."""

    def test_create_and_decode_access_token_workflow(self):
        """Test complete workflow: create token, then decode it."""
        # Create token
        token = jwt_service.create_access_token(
            user_id=42,
            email="workflow@example.com",
            tenant_id=5,
            role="ADMIN",
            scopes=["read", "write"],
            audience="https://api.example.com",
        )

        # Decode token
        payload = jwt_service.decode_access_token(token)

        # Verify all fields
        assert payload["sub"] == "42"
        assert payload["email"] == "workflow@example.com"
        assert payload["tenant_id"] == "5"
        assert payload["role"] == "ADMIN"
        assert payload["scopes"] == ["read", "write"]
        assert payload["aud"] == "https://api.example.com"

    def test_refresh_token_is_different_from_access_token(self):
        """Test that refresh token format is different from access token."""
        access_token = jwt_service.create_access_token(
            user_id=1,
            email="test@example.com",
            tenant_id=1,
            role="OWNER",
        )
        refresh_token = jwt_service.create_refresh_token()

        # Access token should have JWT format (3 parts separated by dots)
        assert access_token.count(".") == 2

        # Refresh token should be random string (no dots)
        assert "." not in refresh_token

        # Refresh token cannot be decoded as JWT
        with pytest.raises(AuthenticationError):
            jwt_service.decode_access_token(refresh_token)

    def test_multiple_users_workflow(self):
        """Test creating and decoding tokens for multiple users."""
        user1_token = jwt_service.create_access_token(1, "user1@example.com", 1, "OWNER")
        user2_token = jwt_service.create_access_token(2, "user2@example.com", 1, "MEMBER")

        user1_payload = jwt_service.decode_access_token(user1_token)
        user2_payload = jwt_service.decode_access_token(user2_token)

        assert user1_payload["sub"] == "1"
        assert user2_payload["sub"] == "2"
        assert user1_payload["email"] != user2_payload["email"]
        assert user1_payload["role"] == "OWNER"
        assert user2_payload["role"] == "MEMBER"

    def test_token_expiration_workflow(self):
        """Test that token expiration is enforced."""
        # Create token with very short expiration
        with patch("app.services.jwt_service.settings") as mock_settings:
            mock_settings.secret_key = settings.secret_key
            mock_settings.jwt_algorithm = settings.jwt_algorithm
            mock_settings.access_token_expire_seconds = 1  # 1 second

            token = jwt_service.create_access_token(1, "test@example.com", 1, "OWNER")

            # Token should be valid immediately
            payload = jwt_service.decode_access_token(token)
            assert payload["sub"] == "1"

            # Wait for token to expire
            time.sleep(2)

            # Token should now be expired
            with pytest.raises(AuthenticationError, match="Token has expired"):
                jwt_service.decode_access_token(token)