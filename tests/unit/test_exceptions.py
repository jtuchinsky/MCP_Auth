"""Unit tests for custom exception classes."""

import pytest
from fastapi import status

from app.core.exceptions import AuthenticationError, AuthorizationError, TOTPError


class TestAuthenticationError:
    """Test AuthenticationError exception."""

    def test_authentication_error_default_message(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()

        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == "Authentication failed"
        assert error.headers is None

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        custom_message = "Invalid email or password"
        error = AuthenticationError(detail=custom_message)

        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == custom_message

    def test_authentication_error_with_headers(self):
        """Test AuthenticationError with custom headers."""
        headers = {"WWW-Authenticate": 'Bearer realm="api"'}
        error = AuthenticationError(
            detail="Token expired", headers=headers
        )

        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == "Token expired"
        assert error.headers == headers

    def test_authentication_error_is_http_exception(self):
        """Test that AuthenticationError is an HTTPException."""
        from fastapi import HTTPException

        error = AuthenticationError()
        assert isinstance(error, HTTPException)

    def test_authentication_error_can_be_raised(self):
        """Test that AuthenticationError can be raised and caught."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError(detail="User not found")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found"


class TestAuthorizationError:
    """Test AuthorizationError exception."""

    def test_authorization_error_default_message(self):
        """Test AuthorizationError with default message."""
        error = AuthorizationError()

        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == "Not authorized to access this resource"
        assert error.headers is None

    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message."""
        custom_message = "Insufficient permissions"
        error = AuthorizationError(detail=custom_message)

        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == custom_message

    def test_authorization_error_with_headers(self):
        """Test AuthorizationError with custom headers."""
        headers = {"X-Required-Scope": "admin"}
        error = AuthorizationError(
            detail="Admin access required", headers=headers
        )

        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == "Admin access required"
        assert error.headers == headers

    def test_authorization_error_is_http_exception(self):
        """Test that AuthorizationError is an HTTPException."""
        from fastapi import HTTPException

        error = AuthorizationError()
        assert isinstance(error, HTTPException)

    def test_authorization_error_can_be_raised(self):
        """Test that AuthorizationError can be raised and caught."""
        with pytest.raises(AuthorizationError) as exc_info:
            raise AuthorizationError(detail="Access denied")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access denied"


class TestTOTPError:
    """Test TOTPError exception."""

    def test_totp_error_default_message(self):
        """Test TOTPError with default message."""
        error = TOTPError()

        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail == "TOTP verification failed"
        assert error.headers is None

    def test_totp_error_custom_message(self):
        """Test TOTPError with custom message."""
        custom_message = "Invalid TOTP code"
        error = TOTPError(detail=custom_message)

        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail == custom_message

    def test_totp_error_with_headers(self):
        """Test TOTPError with custom headers."""
        headers = {"X-TOTP-Required": "true"}
        error = TOTPError(detail="TOTP not enabled", headers=headers)

        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail == "TOTP not enabled"
        assert error.headers == headers

    def test_totp_error_is_http_exception(self):
        """Test that TOTPError is an HTTPException."""
        from fastapi import HTTPException

        error = TOTPError()
        assert isinstance(error, HTTPException)

    def test_totp_error_can_be_raised(self):
        """Test that TOTPError can be raised and caught."""
        with pytest.raises(TOTPError) as exc_info:
            raise TOTPError(detail="TOTP code expired")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "TOTP code expired"


class TestExceptionStatusCodes:
    """Test that exception status codes are correct."""

    def test_authentication_error_status_code(self):
        """Test AuthenticationError uses 401 Unauthorized."""
        error = AuthenticationError()
        assert error.status_code == 401

    def test_authorization_error_status_code(self):
        """Test AuthorizationError uses 403 Forbidden."""
        error = AuthorizationError()
        assert error.status_code == 403

    def test_totp_error_status_code(self):
        """Test TOTPError uses 400 Bad Request."""
        error = TOTPError()
        assert error.status_code == 400

    def test_status_codes_are_different(self):
        """Test that each exception has a unique status code."""
        auth_error = AuthenticationError()
        authz_error = AuthorizationError()
        totp_error = TOTPError()

        status_codes = {
            auth_error.status_code,
            authz_error.status_code,
            totp_error.status_code,
        }

        # All three should have different status codes
        assert len(status_codes) == 3


class TestExceptionUsageScenarios:
    """Test realistic usage scenarios for exceptions."""

    def test_invalid_credentials_scenario(self):
        """Test authentication error for invalid credentials."""
        with pytest.raises(AuthenticationError) as exc_info:
            # Simulate login with wrong password
            raise AuthenticationError(detail="Invalid email or password")

        assert exc_info.value.status_code == 401

    def test_expired_token_scenario(self):
        """Test authentication error for expired token."""
        with pytest.raises(AuthenticationError) as exc_info:
            # Simulate expired JWT
            raise AuthenticationError(
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        assert exc_info.value.status_code == 401
        assert "WWW-Authenticate" in exc_info.value.headers

    def test_insufficient_permissions_scenario(self):
        """Test authorization error for insufficient permissions."""
        with pytest.raises(AuthorizationError) as exc_info:
            # Simulate user without admin role
            raise AuthorizationError(detail="Admin role required")

        assert exc_info.value.status_code == 403

    def test_invalid_totp_code_scenario(self):
        """Test TOTP error for invalid code."""
        with pytest.raises(TOTPError) as exc_info:
            # Simulate wrong TOTP code
            raise TOTPError(detail="Invalid TOTP code. Please try again.")

        assert exc_info.value.status_code == 400

    def test_totp_not_enabled_scenario(self):
        """Test TOTP error when 2FA is not enabled."""
        with pytest.raises(TOTPError) as exc_info:
            # Simulate attempt to verify TOTP when not enabled
            raise TOTPError(detail="TOTP is not enabled for this user")

        assert exc_info.value.status_code == 400
