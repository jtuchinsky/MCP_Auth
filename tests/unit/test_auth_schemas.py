"""Unit tests for auth schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse


class TestLoginRequest:
    """Test LoginRequest schema."""

    def test_login_request_valid_without_totp(self):
        """Test creating LoginRequest without TOTP code."""
        data = {
            "email": "user@example.com",
            "password": "secure_password",
        }
        login = LoginRequest(**data)

        assert login.email == "user@example.com"
        assert login.password == "secure_password"
        assert login.totp_code is None

    def test_login_request_valid_with_totp(self):
        """Test creating LoginRequest with TOTP code."""
        data = {
            "email": "user@example.com",
            "password": "secure_password",
            "totp_code": "123456",
        }
        login = LoginRequest(**data)

        assert login.email == "user@example.com"
        assert login.password == "secure_password"
        assert login.totp_code == "123456"

    def test_login_request_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
        ]

        for email in valid_emails:
            login = LoginRequest(email=email, password="password123")
            assert login.email == email

    def test_login_request_invalid_email(self):
        """Test that invalid email raises ValidationError."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                LoginRequest(email=email, password="password123")

    def test_login_request_missing_email(self):
        """Test that email is required."""
        with pytest.raises(ValidationError):
            LoginRequest(password="password123")

    def test_login_request_missing_password(self):
        """Test that password is required."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com")

    def test_login_request_totp_code_length(self):
        """Test TOTP code must be exactly 6 digits."""
        # Valid 6-digit code
        login = LoginRequest(
            email="user@example.com", password="password", totp_code="123456"
        )
        assert login.totp_code == "123456"

        # Too short
        with pytest.raises(ValidationError):
            LoginRequest(
                email="user@example.com", password="password", totp_code="12345"
            )

        # Too long
        with pytest.raises(ValidationError):
            LoginRequest(
                email="user@example.com", password="password", totp_code="1234567"
            )

    def test_login_request_totp_code_digits_only(self):
        """Test TOTP code must be digits only."""
        # Valid digits
        login = LoginRequest(
            email="user@example.com", password="password", totp_code="000000"
        )
        assert login.totp_code == "000000"

        # Contains letters
        with pytest.raises(ValidationError):
            LoginRequest(
                email="user@example.com", password="password", totp_code="12345a"
            )

        # Contains special characters
        with pytest.raises(ValidationError):
            LoginRequest(
                email="user@example.com", password="password", totp_code="12345!"
            )

    def test_login_request_empty_password(self):
        """Test that empty password is allowed (validation happens server-side)."""
        # Empty password is technically allowed in schema
        # (actual validation happens during authentication)
        login = LoginRequest(email="user@example.com", password="")
        assert login.password == ""

    def test_login_request_model_dump(self):
        """Test serializing LoginRequest to dict."""
        login = LoginRequest(
            email="user@example.com", password="password", totp_code="123456"
        )
        data = login.model_dump()

        assert data["email"] == "user@example.com"
        assert data["password"] == "password"
        assert data["totp_code"] == "123456"

    def test_login_request_model_dump_json(self):
        """Test serializing LoginRequest to JSON."""
        login = LoginRequest(email="user@example.com", password="password")
        json_str = login.model_dump_json()

        assert "user@example.com" in json_str
        assert "password" in json_str


class TestTokenResponse:
    """Test TokenResponse schema."""

    def test_token_response_valid(self):
        """Test creating TokenResponse with valid data."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1",
            "token_type": "bearer",
            "expires_in": 900,
        }
        response = TokenResponse(**data)

        assert response.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert response.refresh_token == "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1"
        assert response.token_type == "bearer"
        assert response.expires_in == 900

    def test_token_response_default_token_type(self):
        """Test that token_type defaults to 'bearer'."""
        data = {
            "access_token": "access_token_string",
            "refresh_token": "refresh_token_string",
            "expires_in": 900,
        }
        response = TokenResponse(**data)

        assert response.token_type == "bearer"

    def test_token_response_missing_access_token(self):
        """Test that access_token is required."""
        with pytest.raises(ValidationError):
            TokenResponse(
                refresh_token="refresh_token_string",
                expires_in=900,
            )

    def test_token_response_missing_refresh_token(self):
        """Test that refresh_token is required."""
        with pytest.raises(ValidationError):
            TokenResponse(
                access_token="access_token_string",
                expires_in=900,
            )

    def test_token_response_missing_expires_in(self):
        """Test that expires_in is required."""
        with pytest.raises(ValidationError):
            TokenResponse(
                access_token="access_token_string",
                refresh_token="refresh_token_string",
            )

    def test_token_response_expires_in_types(self):
        """Test expires_in accepts various numeric types."""
        # Integer
        response1 = TokenResponse(
            access_token="token1",
            refresh_token="refresh1",
            expires_in=900,
        )
        assert response1.expires_in == 900

        # Can be zero
        response2 = TokenResponse(
            access_token="token2",
            refresh_token="refresh2",
            expires_in=0,
        )
        assert response2.expires_in == 0

    def test_token_response_token_type_custom(self):
        """Test that token_type can be customized."""
        response = TokenResponse(
            access_token="token",
            refresh_token="refresh",
            token_type="custom",
            expires_in=900,
        )
        assert response.token_type == "custom"

    def test_token_response_model_dump(self):
        """Test serializing TokenResponse to dict."""
        response = TokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=900,
        )
        data = response.model_dump()

        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_token_response_model_dump_json(self):
        """Test serializing TokenResponse to JSON."""
        response = TokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=900,
        )
        json_str = response.model_dump_json()

        assert "access_token" in json_str
        assert "refresh_token" in json_str
        assert "bearer" in json_str
        assert "900" in json_str


class TestRefreshRequest:
    """Test RefreshRequest schema."""

    def test_refresh_request_valid(self):
        """Test creating RefreshRequest with valid data."""
        data = {
            "refresh_token": "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1",
        }
        request = RefreshRequest(**data)

        assert request.refresh_token == "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1"

    def test_refresh_request_missing_refresh_token(self):
        """Test that refresh_token is required."""
        with pytest.raises(ValidationError):
            RefreshRequest()

    def test_refresh_request_empty_refresh_token(self):
        """Test that empty refresh_token is allowed (validated server-side)."""
        request = RefreshRequest(refresh_token="")
        assert request.refresh_token == ""

    def test_refresh_request_various_token_formats(self):
        """Test various refresh token formats."""
        tokens = [
            "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1",  # Alphanumeric
            "token-with-dashes",  # With dashes
            "token_with_underscores",  # With underscores
            "VeryLongTokenStringThatIsStillValid" * 10,  # Long token
        ]

        for token in tokens:
            request = RefreshRequest(refresh_token=token)
            assert request.refresh_token == token

    def test_refresh_request_model_dump(self):
        """Test serializing RefreshRequest to dict."""
        request = RefreshRequest(refresh_token="my_refresh_token")
        data = request.model_dump()

        assert data["refresh_token"] == "my_refresh_token"

    def test_refresh_request_model_dump_json(self):
        """Test serializing RefreshRequest to JSON."""
        request = RefreshRequest(refresh_token="my_refresh_token")
        json_str = request.model_dump_json()

        assert "my_refresh_token" in json_str


class TestAuthSchemasIntegration:
    """Integration tests for auth schemas."""

    def test_login_to_token_workflow(self):
        """Test complete login to token response workflow."""
        # 1. Client sends login request
        login = LoginRequest(
            email="user@example.com",
            password="secure_password",
            totp_code="123456",
        )

        assert login.email == "user@example.com"
        assert login.password == "secure_password"
        assert login.totp_code == "123456"

        # 2. Server validates and returns tokens
        token_response = TokenResponse(
            access_token="jwt_access_token_here",
            refresh_token="refresh_token_here",
            expires_in=900,
        )

        assert token_response.token_type == "bearer"
        assert token_response.expires_in == 900

    def test_refresh_token_workflow(self):
        """Test token refresh workflow."""
        # 1. Client has existing refresh token
        refresh_request = RefreshRequest(refresh_token="existing_refresh_token")

        assert refresh_request.refresh_token == "existing_refresh_token"

        # 2. Server validates and returns new tokens
        new_tokens = TokenResponse(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_in=900,
        )

        assert new_tokens.access_token != refresh_request.refresh_token
        assert new_tokens.refresh_token != refresh_request.refresh_token

    def test_all_schemas_json_serializable(self):
        """Test that all auth schemas are JSON serializable."""
        import json

        # LoginRequest
        login = LoginRequest(
            email="user@example.com",
            password="password",
            totp_code="123456",
        )
        json.loads(login.model_dump_json())

        # TokenResponse
        tokens = TokenResponse(
            access_token="access",
            refresh_token="refresh",
            expires_in=900,
        )
        json.loads(tokens.model_dump_json())

        # RefreshRequest
        refresh = RefreshRequest(refresh_token="refresh_token")
        json.loads(refresh.model_dump_json())

    def test_login_without_2fa(self):
        """Test login workflow without 2FA."""
        # User without TOTP enabled
        login = LoginRequest(
            email="user@example.com",
            password="password",
        )

        assert login.totp_code is None

        # Serialize without totp_code
        data = login.model_dump()
        assert data["totp_code"] is None

    def test_login_with_2fa(self):
        """Test login workflow with 2FA enabled."""
        # User with TOTP enabled
        login = LoginRequest(
            email="user@example.com",
            password="password",
            totp_code="654321",
        )

        assert login.totp_code == "654321"

        # Serialize with totp_code
        data = login.model_dump()
        assert data["totp_code"] == "654321"