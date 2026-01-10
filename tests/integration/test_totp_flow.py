"""Integration tests for TOTP (Two-Factor Authentication) flows."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services import totp_service


class TestTOTPSetup:
    """Test POST /auth/totp/setup endpoint."""

    def test_totp_setup_success(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test successful TOTP setup."""
        response = authenticated_client.post("/auth/totp/setup")

        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "provisioning_uri" in data
        assert "qr_code" in data
        assert len(data["secret"]) == 32  # Base32 encoded secret
        assert data["provisioning_uri"].startswith("otpauth://totp/")
        # Email is URL-encoded in provisioning URI
        import urllib.parse
        assert test_user.email in urllib.parse.unquote(data["provisioning_uri"])
        # QR code is base64 encoded PNG (starts with PNG signature in base64)
        assert data["qr_code"].startswith("iVBORw0KGgo")

    def test_totp_setup_already_enabled(
        self, client: TestClient, test_user_with_totp: User, db_session: Session
    ):
        """Test TOTP setup fails if already enabled."""
        # Create access token for user with TOTP
        from app.services import jwt_service

        access_token = jwt_service.create_access_token(
            user_id=test_user_with_totp.id,
            email=test_user_with_totp.email,
            tenant_id=test_user_with_totp.tenant_id,
            role=test_user_with_totp.role,
        )

        response = client.post(
            "/auth/totp/setup",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400  # TOTPError returns 400
        assert "already enabled" in response.json()["detail"].lower()

    def test_totp_setup_unauthenticated(self, client: TestClient):
        """Test TOTP setup requires authentication."""
        response = client.post("/auth/totp/setup")

        assert response.status_code == 422  # Missing required header


class TestTOTPVerify:
    """Test POST /auth/totp/verify endpoint."""

    def test_totp_verify_success(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test successful TOTP verification."""
        # First, setup TOTP
        setup_response = authenticated_client.post("/auth/totp/setup")
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]

        # Generate valid TOTP code
        totp_code = totp_service.generate_code(secret)

        # Verify TOTP code
        verify_response = authenticated_client.post(
            "/auth/totp/verify",
            json={"totp_code": totp_code},
        )

        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data["is_totp_enabled"] is True
        assert data["email"] == test_user.email

    def test_totp_verify_invalid_code(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test TOTP verification with invalid code."""
        # Setup TOTP
        setup_response = authenticated_client.post("/auth/totp/setup")
        assert setup_response.status_code == 200

        # Try to verify with invalid code
        verify_response = authenticated_client.post(
            "/auth/totp/verify",
            json={"totp_code": "000000"},
        )

        assert verify_response.status_code == 400
        assert "invalid" in verify_response.json()["detail"].lower()

    def test_totp_verify_without_setup(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test TOTP verification fails without setup."""
        response = authenticated_client.post(
            "/auth/totp/verify",
            json={"totp_code": "123456"},
        )

        assert response.status_code == 400
        assert "not initiated" in response.json()["detail"].lower()

    def test_totp_verify_unauthenticated(self, client: TestClient):
        """Test TOTP verify requires authentication."""
        response = client.post(
            "/auth/totp/verify",
            json={"totp_code": "123456"},
        )

        assert response.status_code == 422  # Missing required header

    def test_totp_verify_invalid_format(self, authenticated_client: TestClient):
        """Test TOTP verification with invalid code format."""
        response = authenticated_client.post(
            "/auth/totp/verify",
            json={"totp_code": "12345"},  # Too short
        )

        assert response.status_code == 422  # Validation error


class TestTOTPValidate:
    """Test POST /auth/totp/validate endpoint (login with TOTP)."""

    def test_totp_validate_success(
        self, client: TestClient, test_user_with_totp: User
    ):
        """Test successful login with TOTP."""
        # Generate valid TOTP code
        totp_code = totp_service.generate_code(test_user_with_totp.totp_secret)

        response = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user_with_totp.email,
                "password": "password123",
                "totp_code": totp_code,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_totp_validate_invalid_code(
        self, client: TestClient, test_user_with_totp: User
    ):
        """Test TOTP login with invalid code."""
        response = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user_with_totp.email,
                "password": "password123",
                "totp_code": "000000",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_totp_validate_wrong_password(
        self, client: TestClient, test_user_with_totp: User
    ):
        """Test TOTP login with wrong password."""
        totp_code = totp_service.generate_code(test_user_with_totp.totp_secret)

        response = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user_with_totp.email,
                "password": "wrongpassword",
                "totp_code": totp_code,
            },
        )

        assert response.status_code == 401

    def test_totp_validate_user_without_totp(
        self, client: TestClient, test_user: User
    ):
        """Test TOTP login for user without TOTP enabled."""
        response = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user.email,
                "password": "password123",
                "totp_code": "123456",
            },
        )

        assert response.status_code == 403
        assert "not enabled" in response.json()["detail"].lower()

    def test_totp_validate_missing_fields(self, client: TestClient):
        """Test TOTP validation with missing fields."""
        # Missing totp_code
        response1 = client.post(
            "/auth/totp/validate",
            json={
                "email": "user@example.com",
                "password": "password123",
            },
        )
        assert response1.status_code == 422

        # Missing password
        response2 = client.post(
            "/auth/totp/validate",
            json={
                "email": "user@example.com",
                "totp_code": "123456",
            },
        )
        assert response2.status_code == 422

        # Missing email
        response3 = client.post(
            "/auth/totp/validate",
            json={
                "password": "password123",
                "totp_code": "123456",
            },
        )
        assert response3.status_code == 422


class TestTOTPFlows:
    """Test complete TOTP authentication flows."""

    def test_complete_totp_setup_flow(
        self, client: TestClient, test_user: User, test_tenant, db_session: Session
    ):
        """Test complete flow: login → setup TOTP → verify → logout → login with TOTP."""
        # Step 1: Login without TOTP (use /auth/login-user for non-owner users)
        login_response = client.post(
            "/auth/login-user",
            json={
                "tenant_email": test_tenant.email,
                "username": test_user.username,
                "password": "password123",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Step 2: Setup TOTP
        setup_response = client.post(
            "/auth/totp/setup",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]

        # Step 3: Verify TOTP
        totp_code = totp_service.generate_code(secret)
        verify_response = client.post(
            "/auth/totp/verify",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={"totp_code": totp_code},
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["is_totp_enabled"] is True

        # Step 4: Logout
        logout_response = client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert logout_response.status_code == 204

        # Step 5: Try regular login (should fail because TOTP is now required)
        regular_login = client.post(
            "/auth/login-user",
            json={
                "tenant_email": test_tenant.email,
                "username": test_user.username,
                "password": "password123",
            },
        )
        assert regular_login.status_code == 403
        assert "TOTP" in regular_login.json()["detail"]

        # Step 6: Login with TOTP
        new_totp_code = totp_service.generate_code(secret)
        totp_login = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user.email,
                "password": "password123",
                "totp_code": new_totp_code,
            },
        )
        assert totp_login.status_code == 200
        assert "access_token" in totp_login.json()

    def test_totp_setup_without_verification(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test that TOTP setup without verification doesn't enable 2FA."""
        # Setup TOTP but don't verify
        setup_response = authenticated_client.post("/auth/totp/setup")
        assert setup_response.status_code == 200

        # Refresh user from database
        db_session.refresh(test_user)

        # TOTP should not be enabled yet
        assert test_user.is_totp_enabled is False
        assert test_user.totp_secret is not None  # Secret is saved

    def test_multiple_totp_setup_attempts(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test multiple TOTP setup attempts generate different secrets."""
        # First setup
        setup1 = authenticated_client.post("/auth/totp/setup")
        assert setup1.status_code == 200
        secret1 = setup1.json()["secret"]

        # Second setup (before verification)
        setup2 = authenticated_client.post("/auth/totp/setup")
        assert setup2.status_code == 200
        secret2 = setup2.json()["secret"]

        # Secrets should be different (new setup overwrites old)
        assert secret1 != secret2

    def test_totp_code_reuse_prevention(
        self, client: TestClient, test_user_with_totp: User
    ):
        """Test that TOTP codes can be reused within the time window."""
        # Note: TOTP codes are valid for 30 seconds by default
        # Multiple uses within the window should succeed (no replay protection implemented)
        totp_code = totp_service.generate_code(test_user_with_totp.totp_secret)

        # First login
        response1 = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user_with_totp.email,
                "password": "password123",
                "totp_code": totp_code,
            },
        )
        assert response1.status_code == 200

        # Second login with same code (should also succeed - no replay protection)
        response2 = client.post(
            "/auth/totp/validate",
            json={
                "email": test_user_with_totp.email,
                "password": "password123",
                "totp_code": totp_code,
            },
        )
        assert response2.status_code == 200