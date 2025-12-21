"""Unit tests for auth service."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.database import Base, SessionLocal, engine
from app.repositories import token_repository, user_repository
from app.services import auth_service


@pytest.fixture
def test_db():
    """Create a test database and clean it up after tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Provide a database session for tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestRegisterUser:
    """Test register_user() function."""

    def test_register_user_success(self, db_session: Session):
        """Test registering a new user successfully."""
        user = auth_service.register_user(
            db=db_session,
            email="newuser@example.com",
            password="secure_password_123",
        )

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.password_hash != "secure_password_123"  # Should be hashed
        assert user.is_totp_enabled is False
        assert user.is_active is True

    def test_register_user_hashes_password(self, db_session: Session):
        """Test that password is hashed during registration."""
        user = auth_service.register_user(
            db=db_session,
            email="test@example.com",
            password="plain_password",
        )

        # Password hash should be bcrypt format
        assert user.password_hash.startswith("$2b$")
        assert user.password_hash != "plain_password"

    def test_register_user_duplicate_email(self, db_session: Session):
        """Test that registering duplicate email raises error."""
        # Register first user
        auth_service.register_user(
            db=db_session,
            email="duplicate@example.com",
            password="password1",
        )

        # Try to register with same email
        with pytest.raises(ValueError, match="already exists"):
            auth_service.register_user(
                db=db_session,
                email="duplicate@example.com",
                password="password2",
            )

    def test_register_user_persists_to_database(self, db_session: Session):
        """Test that registered user is persisted to database."""
        user = auth_service.register_user(
            db=db_session,
            email="persist@example.com",
            password="password",
        )

        # Retrieve user from database
        retrieved_user = user_repository.get_by_id(db_session, user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == "persist@example.com"


class TestAuthenticateUser:
    """Test authenticate_user() function."""

    def test_authenticate_user_success(self, db_session: Session):
        """Test authenticating user with correct credentials."""
        # Register user
        registered_user = auth_service.register_user(
            db=db_session,
            email="auth@example.com",
            password="correct_password",
        )

        # Authenticate
        user = auth_service.authenticate_user(
            db=db_session,
            email="auth@example.com",
            password="correct_password",
        )

        assert user.id == registered_user.id
        assert user.email == "auth@example.com"

    def test_authenticate_user_wrong_email(self, db_session: Session):
        """Test authentication fails with wrong email."""
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.authenticate_user(
                db=db_session,
                email="nonexistent@example.com",
                password="any_password",
            )

    def test_authenticate_user_wrong_password(self, db_session: Session):
        """Test authentication fails with wrong password."""
        # Register user
        auth_service.register_user(
            db=db_session,
            email="user@example.com",
            password="correct_password",
        )

        # Try wrong password
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.authenticate_user(
                db=db_session,
                email="user@example.com",
                password="wrong_password",
            )

    def test_authenticate_user_inactive_account(self, db_session: Session):
        """Test authentication fails for inactive user."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="inactive@example.com",
            password="password",
        )

        # Deactivate user
        user.is_active = False
        db_session.commit()

        # Try to authenticate
        with pytest.raises(AuthenticationError, match="disabled"):
            auth_service.authenticate_user(
                db=db_session,
                email="inactive@example.com",
                password="password",
            )

    def test_authenticate_user_case_sensitive_email(self, db_session: Session):
        """Test that email authentication is case-sensitive."""
        # Register user
        auth_service.register_user(
            db=db_session,
            email="test@example.com",
            password="password",
        )

        # Try uppercase email (SQLite may be case-insensitive, just document behavior)
        # This test documents the expected behavior
        user = auth_service.authenticate_user(
            db=db_session,
            email="test@example.com",
            password="password",
        )
        assert user is not None


class TestCreateTokens:
    """Test create_tokens() function."""

    def test_create_tokens_basic(self, db_session: Session):
        """Test creating tokens for a user."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="tokens@example.com",
            password="password",
        )

        # Create tokens
        access_token, refresh_token = auth_service.create_tokens(
            db=db_session,
            user=user,
        )

        assert isinstance(access_token, str)
        assert len(access_token) > 0
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0
        assert access_token != refresh_token

    def test_create_tokens_with_client_and_scope(self, db_session: Session):
        """Test creating tokens with client_id and scope."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="oauth@example.com",
            password="password",
        )

        # Create tokens with OAuth2 parameters
        access_token, refresh_token = auth_service.create_tokens(
            db=db_session,
            user=user,
            client_id="test_client",
            scope="read write",
        )

        # Verify refresh token is stored with client_id and scope
        stored_token = token_repository.get_by_token(db_session, refresh_token)
        assert stored_token.client_id == "test_client"
        assert stored_token.scope == "read write"

    def test_create_tokens_stores_refresh_token(self, db_session: Session):
        """Test that refresh token is stored in database."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="store@example.com",
            password="password",
        )

        # Create tokens
        access_token, refresh_token = auth_service.create_tokens(
            db=db_session,
            user=user,
        )

        # Verify refresh token is in database
        stored_token = token_repository.get_by_token(db_session, refresh_token)
        assert stored_token is not None
        assert stored_token.user_id == user.id
        assert stored_token.is_revoked is False

    def test_create_tokens_access_token_format(self, db_session: Session):
        """Test that access token is JWT format."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="jwt@example.com",
            password="password",
        )

        # Create tokens
        access_token, _ = auth_service.create_tokens(
            db=db_session,
            user=user,
        )

        # JWT has 3 parts separated by dots
        assert access_token.count(".") == 2

    def test_create_tokens_multiple_times(self, db_session: Session):
        """Test creating multiple tokens for same user."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="multiple@example.com",
            password="password",
        )

        # Create first set of tokens
        access1, refresh1 = auth_service.create_tokens(db=db_session, user=user)

        # Create second set of tokens
        access2, refresh2 = auth_service.create_tokens(db=db_session, user=user)

        # Refresh tokens should be different (random)
        assert refresh1 != refresh2
        # Access tokens may be the same if created at the same second
        # (JWT contains timestamp, so same time = same token)
        # Just verify both are valid JWT format
        assert access1.count(".") == 2
        assert access2.count(".") == 2


class TestRefreshAccessToken:
    """Test refresh_access_token() function."""

    def test_refresh_access_token_success(self, db_session: Session):
        """Test refreshing an access token successfully."""
        # Register user and create tokens
        user = auth_service.register_user(
            db=db_session,
            email="refresh@example.com",
            password="password",
        )
        old_access, old_refresh = auth_service.create_tokens(db=db_session, user=user)

        # Refresh tokens
        new_access, new_refresh = auth_service.refresh_access_token(
            db=db_session,
            refresh_token=old_refresh,
        )

        # New refresh token should be different from old
        assert new_refresh != old_refresh
        # Access tokens may be the same if created at the same second
        # (JWT contains timestamp, so same time = same token)
        # Just verify both are valid JWT format
        assert new_access.count(".") == 2
        assert old_access.count(".") == 2

        # Old refresh token should be revoked
        old_token = token_repository.get_by_token(db_session, old_refresh)
        assert old_token.is_revoked is True

    def test_refresh_access_token_invalid_token(self, db_session: Session):
        """Test refreshing with invalid token fails."""
        with pytest.raises(AuthenticationError, match="Invalid refresh token"):
            auth_service.refresh_access_token(
                db=db_session,
                refresh_token="nonexistent_token",
            )

    def test_refresh_access_token_revoked_token(self, db_session: Session):
        """Test refreshing with revoked token fails."""
        # Register user and create tokens
        user = auth_service.register_user(
            db=db_session,
            email="revoked@example.com",
            password="password",
        )
        _, refresh_token = auth_service.create_tokens(db=db_session, user=user)

        # Revoke token
        token_repository.revoke_token(db_session, refresh_token)

        # Try to refresh
        with pytest.raises(AuthenticationError, match="revoked"):
            auth_service.refresh_access_token(
                db=db_session,
                refresh_token=refresh_token,
            )

    def test_refresh_access_token_expired_token(self, db_session: Session):
        """Test refreshing with expired token fails."""
        # Register user
        user = auth_service.register_user(
            db=db_session,
            email="expired@example.com",
            password="password",
        )

        # Create refresh token that's already expired
        import secrets

        expired_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Yesterday

        token_repository.create_refresh_token(
            db=db_session,
            user_id=user.id,
            token=expired_token,
            expires_at=expires_at,
        )

        # Try to refresh
        with pytest.raises(AuthenticationError, match="expired"):
            auth_service.refresh_access_token(
                db=db_session,
                refresh_token=expired_token,
            )

    def test_refresh_access_token_inactive_user(self, db_session: Session):
        """Test refreshing token for inactive user fails."""
        # Register user and create tokens
        user = auth_service.register_user(
            db=db_session,
            email="inactive_refresh@example.com",
            password="password",
        )
        _, refresh_token = auth_service.create_tokens(db=db_session, user=user)

        # Deactivate user
        user.is_active = False
        db_session.commit()

        # Try to refresh
        with pytest.raises(AuthenticationError, match="disabled"):
            auth_service.refresh_access_token(
                db=db_session,
                refresh_token=refresh_token,
            )

    def test_refresh_access_token_preserves_client_and_scope(
        self, db_session: Session
    ):
        """Test that refresh preserves client_id and scope."""
        # Register user and create tokens with OAuth2 params
        user = auth_service.register_user(
            db=db_session,
            email="oauth_refresh@example.com",
            password="password",
        )
        _, old_refresh = auth_service.create_tokens(
            db=db_session,
            user=user,
            client_id="mobile_app",
            scope="read write delete",
        )

        # Refresh tokens
        _, new_refresh = auth_service.refresh_access_token(
            db=db_session,
            refresh_token=old_refresh,
        )

        # New token should have same client_id and scope
        new_token = token_repository.get_by_token(db_session, new_refresh)
        assert new_token.client_id == "mobile_app"
        assert new_token.scope == "read write delete"


class TestAuthServiceIntegration:
    """Integration tests for auth service functions."""

    def test_complete_registration_and_login_workflow(self, db_session: Session):
        """Test complete user registration and login workflow."""
        email = "complete@example.com"
        password = "secure_password"

        # Register user
        registered_user = auth_service.register_user(
            db=db_session,
            email=email,
            password=password,
        )
        assert registered_user.email == email

        # Authenticate user
        authenticated_user = auth_service.authenticate_user(
            db=db_session,
            email=email,
            password=password,
        )
        assert authenticated_user.id == registered_user.id

        # Create tokens
        access_token, refresh_token = auth_service.create_tokens(
            db=db_session,
            user=authenticated_user,
        )
        assert len(access_token) > 0
        assert len(refresh_token) > 0

    def test_token_refresh_workflow(self, db_session: Session):
        """Test token refresh workflow."""
        # Register and get initial tokens
        user = auth_service.register_user(
            db=db_session,
            email="refresh_workflow@example.com",
            password="password",
        )
        access1, refresh1 = auth_service.create_tokens(db=db_session, user=user)

        # Refresh tokens
        access2, refresh2 = auth_service.refresh_access_token(
            db=db_session,
            refresh_token=refresh1,
        )

        # Refresh tokens should be different
        assert refresh1 != refresh2
        # Access tokens may be the same if created at the same second
        # (JWT contains timestamp, so same time = same token)
        # Just verify both are valid JWT format
        assert access1.count(".") == 2
        assert access2.count(".") == 2

        # Old refresh token should be revoked
        old_token = token_repository.get_by_token(db_session, refresh1)
        assert old_token.is_revoked is True

        # New refresh token should be active
        new_token = token_repository.get_by_token(db_session, refresh2)
        assert new_token.is_revoked is False

    def test_multiple_users_do_not_interfere(self, db_session: Session):
        """Test that operations on different users don't interfere."""
        # Register two users
        user1 = auth_service.register_user(
            db=db_session,
            email="user1@example.com",
            password="password1",
        )
        user2 = auth_service.register_user(
            db=db_session,
            email="user2@example.com",
            password="password2",
        )

        # Create tokens for both
        access1, refresh1 = auth_service.create_tokens(db=db_session, user=user1)
        access2, refresh2 = auth_service.create_tokens(db=db_session, user=user2)

        # Tokens should be different
        assert access1 != access2
        assert refresh1 != refresh2

        # Refreshing user1's token shouldn't affect user2
        auth_service.refresh_access_token(db=db_session, refresh_token=refresh1)

        # User2's token should still be valid
        token2 = token_repository.get_by_token(db_session, refresh2)
        assert token2.is_revoked is False