"""Integration tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestRegistrationEndpoint:
    """Test POST /auth/register endpoint."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_totp_enabled"] is False
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "anotherpassword123",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client: TestClient):
        """Test registration with password too short."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",  # Less than 8 characters
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_missing_email(self, client: TestClient):
        """Test registration without email."""
        response = client.post(
            "/auth/register",
            json={
                "password": "password123",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_missing_password(self, client: TestClient):
        """Test registration without password."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
            },
        )

        assert response.status_code == 422  # Validation error


class TestLoginEndpoint:
    """Test POST /auth/login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900  # 15 minutes

    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, test_user: User, db_session: Session):
        """Test login with inactive account."""
        # Deactivate user
        test_user.is_active = False
        db_session.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )

        assert response.status_code == 401

    def test_login_with_totp_user_requires_totp(
        self, client: TestClient, test_user_with_totp: User
    ):
        """Test login with TOTP-enabled user redirects to TOTP endpoint."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user_with_totp.email,
                "password": "password123",
            },
        )

        assert response.status_code == 403
        assert "TOTP" in response.json()["detail"]
        assert "/auth/totp/validate" in response.json()["detail"]

    def test_login_missing_credentials(self, client: TestClient):
        """Test login without credentials."""
        response = client.post("/auth/login", json={})
        assert response.status_code == 422  # Validation error

    def test_login_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format."""
        response = client.post(
            "/auth/login",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422  # Validation error


class TestRefreshEndpoint:
    """Test POST /auth/refresh endpoint."""

    def test_refresh_success(self, client: TestClient, user_tokens: dict):
        """Test successful token refresh."""
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": user_tokens["refresh_token"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

        # Refresh token should always be different (rotation)
        assert data["refresh_token"] != user_tokens["refresh_token"]

        # Access tokens may be the same if created in the same second
        # (JWT payload includes timestamp, so identical times = identical tokens)
        # Just verify it's a valid JWT format
        assert data["access_token"].count(".") == 2

    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid-token-12345",
            },
        )

        assert response.status_code == 401

    def test_refresh_missing_token(self, client: TestClient):
        """Test refresh without token."""
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 422  # Validation error

    def test_refresh_revoked_token(
        self, client: TestClient, user_tokens: dict, db_session: Session
    ):
        """Test refresh with revoked token."""
        # First, revoke the token
        from app.repositories import token_repository

        token_repository.revoke_token(db_session, user_tokens["refresh_token"])

        # Try to refresh
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": user_tokens["refresh_token"],
            },
        )

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()


class TestLogoutEndpoint:
    """Test POST /auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, user_tokens: dict):
        """Test successful logout."""
        response = client.post(
            "/auth/logout",
            json={
                "refresh_token": user_tokens["refresh_token"],
            },
        )

        assert response.status_code == 204
        assert response.content == b""

        # Token should be revoked, refresh should fail
        refresh_response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": user_tokens["refresh_token"],
            },
        )
        assert refresh_response.status_code == 401

    def test_logout_invalid_token(self, client: TestClient):
        """Test logout with invalid token (should still succeed)."""
        response = client.post(
            "/auth/logout",
            json={
                "refresh_token": "invalid-token",
            },
        )

        # Logout should succeed even with invalid token (idempotent)
        assert response.status_code == 204

    def test_logout_missing_token(self, client: TestClient):
        """Test logout without token."""
        response = client.post("/auth/logout", json={})
        assert response.status_code == 422  # Validation error


class TestAuthFlows:
    """Test complete authentication flows."""

    def test_complete_registration_login_flow(self, client: TestClient):
        """Test complete flow: register → login → access protected resource."""
        # Step 1: Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "flowuser@example.com",
                "password": "securepass123",
            },
        )
        assert register_response.status_code == 201
        user_data = register_response.json()

        # Step 2: Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "flowuser@example.com",
                "password": "securepass123",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Step 3: Access protected resource
        me_response = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == user_data["email"]
        assert me_data["id"] == user_data["id"]

    def test_token_refresh_flow(self, client: TestClient, user_tokens: dict):
        """Test token refresh flow."""
        # Use initial access token
        me_response_1 = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
        )
        assert me_response_1.status_code == 200

        # Refresh tokens
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        # Use new access token
        me_response_2 = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert me_response_2.status_code == 200

        # Old refresh token should not work (rotation)
        old_refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        assert old_refresh_response.status_code == 401

    def test_logout_invalidates_refresh_token(
        self, client: TestClient, user_tokens: dict
    ):
        """Test that logout properly invalidates refresh token."""
        # Logout
        logout_response = client.post(
            "/auth/logout",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        assert logout_response.status_code == 204

        # Try to refresh with logged-out token
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 401

    def test_multiple_logins_different_refresh_tokens(
        self, client: TestClient, test_user: User
    ):
        """Test that multiple logins create different refresh tokens."""
        # First login
        login1 = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        tokens1 = login1.json()

        # Second login
        login2 = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        tokens2 = login2.json()

        # Refresh tokens should always be different (random generated)
        assert tokens1["refresh_token"] != tokens2["refresh_token"]

        # Access tokens may be the same if created in the same second
        # (JWT includes timestamp in payload)
        # Just verify both are valid JWTs
        assert tokens1["access_token"].count(".") == 2
        assert tokens2["access_token"].count(".") == 2

        # Both refresh tokens should work
        refresh1 = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens1["refresh_token"]},
        )
        refresh2 = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens2["refresh_token"]},
        )
        assert refresh1.status_code == 200
        assert refresh2.status_code == 200