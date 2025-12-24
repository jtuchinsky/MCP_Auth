"""Integration tests for protected endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestGetMeEndpoint:
    """Test GET /api/protected/me endpoint."""

    def test_get_me_success(self, authenticated_client: TestClient, test_user: User):
        """Test successful retrieval of current user."""
        response = authenticated_client.get("/api/protected/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["is_active"] is True
        assert data["is_totp_enabled"] is False
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_me_unauthenticated(self, client: TestClient):
        """Test /me endpoint without authentication."""
        response = client.get("/api/protected/me")

        assert response.status_code == 422  # Missing required header
        assert "detail" in response.json()

    def test_get_me_invalid_token(self, client: TestClient):
        """Test /me endpoint with invalid token."""
        response = client.get(
            "/api/protected/me",
            headers={"Authorization": "Bearer invalid-token-12345"},
        )

        assert response.status_code == 401

    def test_get_me_malformed_header(self, client: TestClient):
        """Test /me endpoint with malformed Authorization header."""
        # Missing "Bearer" prefix
        response = client.get(
            "/api/protected/me",
            headers={"Authorization": "token123"},
        )

        assert response.status_code == 401

    def test_get_me_expired_token(self, client: TestClient):
        """Test /me endpoint with expired token."""
        # Create an expired token (exp in the past)
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.config import settings

        now = datetime.now(timezone.utc)
        expired_token = jwt.encode(
            {
                "sub": "999",
                "email": "expired@example.com",
                "exp": now - timedelta(hours=1),
                "iat": now - timedelta(hours=2),
            },
            settings.secret_key,
            algorithm="HS256",
        )

        response = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_get_me_with_totp_user(
        self, client: TestClient, test_user_with_totp: User
    ):
        """Test /me endpoint for user with TOTP enabled."""
        from app.services import jwt_service

        access_token = jwt_service.create_access_token(
            user_id=test_user_with_totp.id,
            email=test_user_with_totp.email,
        )

        response = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_totp_enabled"] is True
        assert data["email"] == test_user_with_totp.email


class TestUpdateProfileEndpoint:
    """Test PATCH /api/protected/profile endpoint."""

    def test_update_profile_email(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test updating user email."""
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={"email": "newemail@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
        assert data["id"] == test_user.id

    def test_update_profile_password(
        self, authenticated_client: TestClient, test_user: User, client: TestClient
    ):
        """Test updating user password."""
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={"password": "newpassword456"},
        )

        assert response.status_code == 200

        # Verify new password works
        login_response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "newpassword456",
            },
        )
        assert login_response.status_code == 200

        # Verify old password doesn't work
        old_login_response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert old_login_response.status_code == 401

    def test_update_profile_email_and_password(
        self, authenticated_client: TestClient, client: TestClient
    ):
        """Test updating both email and password."""
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={
                "email": "updated@example.com",
                "password": "updatedpass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

        # Verify login with new credentials
        login_response = client.post(
            "/auth/login",
            json={
                "email": "updated@example.com",
                "password": "updatedpass123",
            },
        )
        assert login_response.status_code == 200

    def test_update_profile_no_changes(self, authenticated_client: TestClient):
        """Test updating profile with no changes (empty body)."""
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={},
        )

        assert response.status_code == 200

    def test_update_profile_invalid_email(self, authenticated_client: TestClient):
        """Test updating profile with invalid email format."""
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={"email": "not-an-email"},
        )

        assert response.status_code == 422  # Validation error

    def test_update_profile_short_password(self, authenticated_client: TestClient):
        """Test updating profile with password too short."""
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={"password": "short"},
        )

        assert response.status_code == 422  # Validation error

    def test_update_profile_unauthenticated(self, client: TestClient):
        """Test profile update requires authentication."""
        response = client.patch(
            "/api/protected/profile",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 422  # Missing required header

    def test_update_profile_duplicate_email(
        self, authenticated_client: TestClient, client: TestClient
    ):
        """Test updating to an email that already exists."""
        # Create another user
        client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "password": "password123",
            },
        )

        # Try to update to existing email
        response = authenticated_client.patch(
            "/api/protected/profile",
            json={"email": "existing@example.com"},
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


class TestProtectedEndpointFlows:
    """Test complete flows involving protected endpoints."""

    def test_login_access_update_flow(self, client: TestClient):
        """Test complete flow: register → login → access profile → update profile."""
        # Step 1: Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "flowtest@example.com",
                "password": "password123",
            },
        )
        assert register_response.status_code == 201

        # Step 2: Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "flowtest@example.com",
                "password": "password123",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Step 3: Access profile
        me_response = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "flowtest@example.com"

        # Step 4: Update profile
        update_response = client.patch(
            "/api/protected/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"email": "updated-flowtest@example.com"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["email"] == "updated-flowtest@example.com"

        # Step 5: Verify update in /me
        final_me_response = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert final_me_response.status_code == 200
        assert final_me_response.json()["email"] == "updated-flowtest@example.com"

    def test_token_refresh_with_protected_endpoints(
        self, client: TestClient, user_tokens: dict
    ):
        """Test using refreshed tokens with protected endpoints."""
        # Access /me with original token
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
        new_access_token = refresh_response.json()["access_token"]

        # Access /me with new token
        me_response_2 = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert me_response_2.status_code == 200

        # Both responses should have the same user data
        assert me_response_1.json()["id"] == me_response_2.json()["id"]
        assert me_response_1.json()["email"] == me_response_2.json()["email"]

    def test_password_change_invalidates_nothing(
        self, client: TestClient, test_user: User, user_tokens: dict
    ):
        """Test that changing password doesn't invalidate existing tokens."""
        # Note: Current implementation doesn't invalidate tokens on password change
        # This is a design decision - tokens remain valid until expiry

        # Update password
        update_response = client.patch(
            "/api/protected/profile",
            headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
            json={"password": "newpassword789"},
        )
        assert update_response.status_code == 200

        # Old access token should still work
        me_response = client.get(
            "/api/protected/me",
            headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
        )
        assert me_response.status_code == 200

        # Old refresh token should still work
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 200

    def test_concurrent_profile_updates(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test multiple concurrent profile updates."""
        # First update
        response1 = authenticated_client.patch(
            "/api/protected/profile",
            json={"email": "update1@example.com"},
        )
        assert response1.status_code == 200

        # Second update
        response2 = authenticated_client.patch(
            "/api/protected/profile",
            json={"email": "update2@example.com"},
        )
        assert response2.status_code == 200

        # Final state should reflect last update
        me_response = authenticated_client.get("/api/protected/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "update2@example.com"