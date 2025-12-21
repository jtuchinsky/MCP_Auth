"""Unit tests for token repository."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.repositories import token_repository, user_repository


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


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user for token tests."""
    return user_repository.create(
        db=db_session,
        email="token_test@example.com",
        password_hash="hashed_password",
    )


class TestCreateRefreshToken:
    """Test create_refresh_token() function."""

    def test_create_refresh_token_success(self, db_session: Session, test_user: User):
        """Test creating a new refresh token successfully."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="test_token_123",
            expires_at=expires_at,
        )

        assert token.id is not None
        assert token.user_id == test_user.id
        assert token.token == "test_token_123"
        assert token.is_revoked is False
        assert isinstance(token.expires_at, datetime)

    def test_create_refresh_token_with_oauth_fields(
        self, db_session: Session, test_user: User
    ):
        """Test creating refresh token with OAuth2 fields."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="oauth_token_123",
            expires_at=expires_at,
            client_id="test_client",
            scope="read write",
        )

        assert token.client_id == "test_client"
        assert token.scope == "read write"

    def test_create_refresh_token_returns_persisted_instance(
        self, db_session: Session, test_user: User
    ):
        """Test that created refresh token is persisted to database."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="persist_token",
            expires_at=expires_at,
        )

        # Verify token can be retrieved from database
        retrieved_token = token_repository.get_by_token(db_session, "persist_token")
        assert retrieved_token is not None
        assert retrieved_token.id == token.id
        assert retrieved_token.user_id == test_user.id

    def test_create_multiple_tokens_for_user(
        self, db_session: Session, test_user: User
    ):
        """Test creating multiple refresh tokens for the same user."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token1 = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="token_1",
            expires_at=expires_at,
        )
        token2 = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="token_2",
            expires_at=expires_at,
        )

        assert token1.id != token2.id
        assert token1.user_id == token2.user_id == test_user.id
        assert token1.token != token2.token


class TestGetByToken:
    """Test get_by_token() function."""

    def test_get_by_token_existing_token(self, db_session: Session, test_user: User):
        """Test getting an existing token."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        created_token = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="find_me",
            expires_at=expires_at,
        )

        retrieved_token = token_repository.get_by_token(db_session, "find_me")

        assert retrieved_token is not None
        assert retrieved_token.id == created_token.id
        assert retrieved_token.token == "find_me"

    def test_get_by_token_nonexistent_token(self, db_session: Session):
        """Test getting a nonexistent token returns None."""
        token = token_repository.get_by_token(db_session, "nonexistent")

        assert token is None

    def test_get_by_token_case_sensitive(self, db_session: Session, test_user: User):
        """Test that token lookup is case-sensitive."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="CaseSensitive",
            expires_at=expires_at,
        )

        token_exact = token_repository.get_by_token(db_session, "CaseSensitive")
        token_lower = token_repository.get_by_token(db_session, "casesensitive")

        assert token_exact is not None
        assert token_lower is None

    def test_get_by_token_empty_string(self, db_session: Session):
        """Test getting token with empty string returns None."""
        token = token_repository.get_by_token(db_session, "")

        assert token is None


class TestRevokeToken:
    """Test revoke_token() function."""

    def test_revoke_token_success(self, db_session: Session, test_user: User):
        """Test revoking a token successfully."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="revoke_me",
            expires_at=expires_at,
        )

        token_repository.revoke_token(db_session, "revoke_me")

        # Verify token is revoked
        revoked_token = token_repository.get_by_token(db_session, "revoke_me")
        assert revoked_token is not None
        assert revoked_token.is_revoked is True

    def test_revoke_token_persists(self, db_session: Session, test_user: User):
        """Test that token revocation persists to database."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="persist_revoke",
            expires_at=expires_at,
        )

        token_repository.revoke_token(db_session, "persist_revoke")

        # Retrieve token again to verify persistence
        retrieved_token = token_repository.get_by_token(db_session, "persist_revoke")
        assert retrieved_token.is_revoked is True

    def test_revoke_nonexistent_token(self, db_session: Session):
        """Test revoking a nonexistent token raises error."""
        with pytest.raises(ValueError, match="Token not found"):
            token_repository.revoke_token(db_session, "nonexistent_token")

    def test_revoke_token_idempotent(self, db_session: Session, test_user: User):
        """Test revoking an already revoked token is idempotent."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="double_revoke",
            expires_at=expires_at,
        )

        # Revoke first time
        token_repository.revoke_token(db_session, "double_revoke")

        # Revoke second time
        token_repository.revoke_token(db_session, "double_revoke")

        # Verify still revoked
        token = token_repository.get_by_token(db_session, "double_revoke")
        assert token.is_revoked is True


class TestRevokeAllUserTokens:
    """Test revoke_all_user_tokens() function."""

    def test_revoke_all_user_tokens_success(
        self, db_session: Session, test_user: User
    ):
        """Test revoking all tokens for a user."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create multiple tokens for user
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="user_token_1",
            expires_at=expires_at,
        )
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="user_token_2",
            expires_at=expires_at,
        )
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="user_token_3",
            expires_at=expires_at,
        )

        # Revoke all tokens
        token_repository.revoke_all_user_tokens(db_session, test_user.id)

        # Verify all tokens are revoked
        token1 = token_repository.get_by_token(db_session, "user_token_1")
        token2 = token_repository.get_by_token(db_session, "user_token_2")
        token3 = token_repository.get_by_token(db_session, "user_token_3")

        assert token1.is_revoked is True
        assert token2.is_revoked is True
        assert token3.is_revoked is True

    def test_revoke_all_user_tokens_does_not_affect_other_users(
        self, db_session: Session
    ):
        """Test that revoking tokens for one user doesn't affect other users."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create two users
        user1 = user_repository.create(
            db=db_session, email="user1@example.com", password_hash="hash1"
        )
        user2 = user_repository.create(
            db=db_session, email="user2@example.com", password_hash="hash2"
        )

        # Create tokens for both users
        token_repository.create_refresh_token(
            db=db_session,
            user_id=user1.id,
            token="user1_token",
            expires_at=expires_at,
        )
        token_repository.create_refresh_token(
            db=db_session,
            user_id=user2.id,
            token="user2_token",
            expires_at=expires_at,
        )

        # Revoke all tokens for user1
        token_repository.revoke_all_user_tokens(db_session, user1.id)

        # Verify user1's token is revoked
        user1_token = token_repository.get_by_token(db_session, "user1_token")
        assert user1_token.is_revoked is True

        # Verify user2's token is NOT revoked
        user2_token = token_repository.get_by_token(db_session, "user2_token")
        assert user2_token.is_revoked is False

    def test_revoke_all_user_tokens_with_no_tokens(self, db_session: Session):
        """Test revoking tokens for user with no tokens doesn't error."""
        # Create user with no tokens
        user = user_repository.create(
            db=db_session, email="no_tokens@example.com", password_hash="hash"
        )

        # Should not raise error
        token_repository.revoke_all_user_tokens(db_session, user.id)

    def test_revoke_all_user_tokens_nonexistent_user(self, db_session: Session):
        """Test revoking tokens for nonexistent user doesn't error."""
        # Should not raise error even for nonexistent user
        token_repository.revoke_all_user_tokens(db_session, 99999)


class TestTokenRepositoryIntegration:
    """Integration tests for token repository functions."""

    def test_complete_token_lifecycle(self, db_session: Session, test_user: User):
        """Test complete token lifecycle: create, retrieve, revoke."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create token
        token = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="lifecycle_token",
            expires_at=expires_at,
            client_id="test_client",
            scope="read",
        )
        assert token.is_revoked is False

        # Retrieve token
        retrieved = token_repository.get_by_token(db_session, "lifecycle_token")
        assert retrieved is not None
        assert retrieved.id == token.id
        assert retrieved.client_id == "test_client"
        assert retrieved.scope == "read"

        # Revoke token
        token_repository.revoke_token(db_session, "lifecycle_token")

        # Verify revocation
        revoked = token_repository.get_by_token(db_session, "lifecycle_token")
        assert revoked.is_revoked is True

    def test_user_logout_scenario(self, db_session: Session):
        """Test user logout scenario: revoke all tokens."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create user
        user = user_repository.create(
            db=db_session, email="logout@example.com", password_hash="hash"
        )

        # Create multiple sessions (tokens)
        token_repository.create_refresh_token(
            db=db_session,
            user_id=user.id,
            token="session_1",
            expires_at=expires_at,
            client_id="web",
        )
        token_repository.create_refresh_token(
            db=db_session,
            user_id=user.id,
            token="session_2",
            expires_at=expires_at,
            client_id="mobile",
        )

        # User logs out from all devices
        token_repository.revoke_all_user_tokens(db_session, user.id)

        # Verify all sessions are revoked
        session1 = token_repository.get_by_token(db_session, "session_1")
        session2 = token_repository.get_by_token(db_session, "session_2")

        assert session1.is_revoked is True
        assert session2.is_revoked is True

    def test_token_refresh_scenario(self, db_session: Session, test_user: User):
        """Test token refresh scenario: revoke old, create new."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create initial token
        token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="old_token",
            expires_at=expires_at,
        )

        # Refresh: revoke old token
        token_repository.revoke_token(db_session, "old_token")

        # Create new token
        new_token = token_repository.create_refresh_token(
            db=db_session,
            user_id=test_user.id,
            token="new_token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        # Verify old token is revoked
        old = token_repository.get_by_token(db_session, "old_token")
        assert old.is_revoked is True

        # Verify new token is active
        assert new_token.is_revoked is False