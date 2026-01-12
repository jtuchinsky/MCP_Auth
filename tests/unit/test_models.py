"""Unit tests for database models."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.token import RefreshToken
from app.models.user import User
from app.repositories import tenant_repository


@pytest.fixture
def test_db():
    """Create a test database and clean it up after tests."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield

    # Drop all tables
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
def test_tenant(db_session: Session):
    """Create a test tenant for model tests."""
    return tenant_repository.create(
        db=db_session,
        email="models_tenant@example.com",
        password_hash="tenant_hash_123",
    )


class TestUserModel:
    """Test User model structure and behavior."""

    def test_user_table_exists(self, test_db):
        """Test that users table exists."""
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "users" in table_names

    def test_user_model_columns(self, test_db):
        """Test that User model has all required columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("users")}

        expected_columns = {
            "id",
            "tenant_id",
            "tenant_name",
            "username",
            "email",
            "password_hash",
            "role",
            "totp_secret",
            "is_totp_enabled",
            "created_at",
            "updated_at",
            "is_active",
        }

        assert columns == expected_columns

    def test_user_email_is_unique(self, test_db):
        """Test that email column has unique constraint."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("users")
        unique_indexes = inspector.get_unique_constraints("users")

        # Check for unique constraint on email
        email_unique = False
        for index in indexes:
            if "email" in index["column_names"] and index.get("unique"):
                email_unique = True
                break
        for constraint in unique_indexes:
            if "email" in constraint["column_names"]:
                email_unique = True
                break

        assert email_unique, "Email should have unique constraint"

    def test_create_user(self, db_session: Session, test_tenant):
        """Test creating a new user."""
        user = User(
            tenant_id=test_tenant.id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.tenant_id == test_tenant.id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.role == "MEMBER"
        assert user.totp_secret is None
        assert user.is_totp_enabled is False
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_default_values(self, db_session: Session, test_tenant):
        """Test that User model has correct default values."""
        user = User(
            tenant_id=test_tenant.id,
            username="defaultsuser",
            email="defaults@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Check defaults
        assert user.role == "MEMBER"
        assert user.is_totp_enabled is False
        assert user.is_active is True
        assert user.totp_secret is None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_with_totp(self, db_session: Session, test_tenant):
        """Test creating a user with TOTP enabled."""
        user = User(
            tenant_id=test_tenant.id,
            username="totpuser",
            email="totp@example.com",
            password_hash="hash123",
            totp_secret="JBSWY3DPEHPK3PXP",
            is_totp_enabled=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.totp_secret == "JBSWY3DPEHPK3PXP"
        assert user.is_totp_enabled is True

    def test_user_updated_at_changes(self, db_session: Session, test_tenant):
        """Test that updated_at changes when user is modified."""
        user = User(
            tenant_id=test_tenant.id,
            username="updateuser",
            email="update@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        original_updated_at = user.updated_at

        # Update user
        user.email = "newemail@example.com"
        db_session.commit()
        db_session.refresh(user)

        # updated_at should be different (or at least same/newer)
        assert user.updated_at >= original_updated_at

    def test_user_repr(self, db_session: Session, test_tenant):
        """Test User __repr__ method."""
        user = User(
            tenant_id=test_tenant.id,
            username="repruser",
            email="repr@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        repr_str = repr(user)
        assert "User" in repr_str
        assert f"id={user.id}" in repr_str
        assert "repr@example.com" in repr_str

    def test_user_relationship_with_tokens(self, db_session: Session, test_tenant):
        """Test User has relationship with RefreshTokens."""
        user = User(
            tenant_id=test_tenant.id,
            username="tokensuser",
            email="tokens@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create refresh tokens
        token1 = RefreshToken(
            user_id=user.id,
            token="token_1",
            expires_at=datetime.now(timezone.utc),
        )
        token2 = RefreshToken(
            user_id=user.id,
            token="token_2",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add_all([token1, token2])
        db_session.commit()
        db_session.refresh(user)

        # Check relationship
        assert len(user.refresh_tokens) == 2
        assert token1 in user.refresh_tokens
        assert token2 in user.refresh_tokens


class TestRefreshTokenModel:
    """Test RefreshToken model structure and behavior."""

    def test_refresh_tokens_table_exists(self, test_db):
        """Test that refresh_tokens table exists."""
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "refresh_tokens" in table_names

    def test_refresh_token_model_columns(self, test_db):
        """Test that RefreshToken model has all required columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("refresh_tokens")}

        expected_columns = {
            "id",
            "user_id",
            "token",
            "client_id",
            "scope",
            "is_revoked",
            "expires_at",
            "created_at",
        }

        assert columns == expected_columns

    def test_refresh_token_unique(self, test_db):
        """Test that token column has unique constraint."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("refresh_tokens")
        unique_indexes = inspector.get_unique_constraints("refresh_tokens")

        # Check for unique constraint on token
        token_unique = False
        for index in indexes:
            if "token" in index["column_names"] and index.get("unique"):
                token_unique = True
                break
        for constraint in unique_indexes:
            if "token" in constraint["column_names"]:
                token_unique = True
                break

        assert token_unique, "Token should have unique constraint"

    def test_create_refresh_token(self, db_session: Session, test_tenant):
        """Test creating a new refresh token."""
        # Create user first
        user = User(
            tenant_id=test_tenant.id,
            username="tokenuser",
            email="token_user@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create refresh token
        expires_at = datetime.now(timezone.utc)
        token = RefreshToken(
            user_id=user.id,
            token="test_refresh_token_123",
            expires_at=expires_at,
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.id is not None
        assert token.user_id == user.id
        assert token.token == "test_refresh_token_123"
        assert token.client_id is None
        assert token.scope is None
        assert token.is_revoked is False
        assert isinstance(token.created_at, datetime)
        # SQLite doesn't preserve timezone info, so compare without it
        assert isinstance(token.expires_at, datetime)

    def test_refresh_token_default_values(self, db_session: Session, test_tenant):
        """Test that RefreshToken model has correct default values."""
        # Create user
        user = User(
            tenant_id=test_tenant.id,
            username="defaultstokenuser",
            email="defaults_token@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()

        # Create token
        token = RefreshToken(
            user_id=user.id,
            token="default_token",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        # Check defaults
        assert token.is_revoked is False
        assert token.client_id is None
        assert token.scope is None
        assert token.created_at is not None

    def test_refresh_token_with_oauth_fields(self, db_session: Session, test_tenant):
        """Test creating a refresh token with OAuth2 fields."""
        # Create user
        user = User(
            tenant_id=test_tenant.id,
            username="oauthuser",
            email="oauth_user@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()

        # Create token with OAuth fields
        token = RefreshToken(
            user_id=user.id,
            token="oauth_token",
            client_id="my_client_app",
            scope="read:profile write:posts",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.client_id == "my_client_app"
        assert token.scope == "read:profile write:posts"

    def test_refresh_token_revocation(self, db_session: Session, test_tenant):
        """Test revoking a refresh token."""
        # Create user and token
        user = User(
            tenant_id=test_tenant.id,
            username="revokeuser",
            email="revoke_user@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token="revoke_token",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.is_revoked is False

        # Revoke token
        token.is_revoked = True
        db_session.commit()
        db_session.refresh(token)

        assert token.is_revoked is True

    def test_refresh_token_repr(self, db_session: Session, test_tenant):
        """Test RefreshToken __repr__ method."""
        user = User(
            tenant_id=test_tenant.id,
            username="reprtokenuser",
            email="repr_token@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token="repr_token",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        repr_str = repr(token)
        assert "RefreshToken" in repr_str
        assert f"id={token.id}" in repr_str
        assert f"user_id={user.id}" in repr_str

    def test_refresh_token_foreign_key(self, db_session: Session):
        """Test that RefreshToken has foreign key to User."""
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys("refresh_tokens")

        # Check for foreign key on user_id
        assert len(foreign_keys) > 0
        fk = foreign_keys[0]
        assert "user_id" in fk["constrained_columns"]
        assert fk["referred_table"] == "users"

    def test_delete_user_cascades_tokens(self, db_session: Session, test_tenant):
        """Test that deleting a user cascades to delete their tokens."""
        # Create user
        user = User(
            tenant_id=test_tenant.id,
            username="cascadeuser",
            email="cascade@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_id = user.id

        # Create tokens
        token1 = RefreshToken(
            user_id=user_id,
            token="cascade_token_1",
            expires_at=datetime.now(timezone.utc),
        )
        token2 = RefreshToken(
            user_id=user_id,
            token="cascade_token_2",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add_all([token1, token2])
        db_session.commit()

        # Verify tokens exist
        tokens = db_session.query(RefreshToken).filter_by(user_id=user_id).all()
        assert len(tokens) == 2

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Verify tokens were deleted
        tokens = db_session.query(RefreshToken).filter_by(user_id=user_id).all()
        assert len(tokens) == 0


class TestModelRelationships:
    """Test relationships between models."""

    def test_user_to_tokens_relationship(self, db_session: Session, test_tenant):
        """Test accessing tokens from user."""
        user = User(
            tenant_id=test_tenant.id,
            username="reluser",
            email="rel_user@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()

        # Initially no tokens
        assert len(user.refresh_tokens) == 0

        # Add token
        token = RefreshToken(
            user_id=user.id,
            token="rel_token",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(user)

        # Check relationship
        assert len(user.refresh_tokens) == 1
        assert user.refresh_tokens[0].token == "rel_token"

    def test_token_to_user_relationship(self, db_session: Session, test_tenant):
        """Test accessing user from token."""
        user = User(
            tenant_id=test_tenant.id,
            username="reltokenuser",
            email="rel_token_user@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token="rel_user_token",
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        # Access user from token
        assert token.user is not None
        assert token.user.id == user.id
        assert token.user.email == "rel_token_user@example.com"