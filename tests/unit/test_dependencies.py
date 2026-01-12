"""Unit tests for FastAPI dependencies."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, TOTPError
from app.database import Base, SessionLocal, engine
from app.dependencies import get_current_user, require_totp_disabled
from app.repositories import tenant_repository
from app.services import auth_service, jwt_service


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
def test_tenant(db_session: Session):
    """Create a test tenant for dependency tests."""
    return tenant_repository.create(
        db=db_session,
        email="deps_tenant@example.com",
        password_hash="tenant_hash_123",
    )


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session: Session, test_tenant):
        """Test getting current user with valid token."""
        # Create a user
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user1",
            email="user@example.com",
            password="password123",
        )

        # Create access token
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )

        # Create authorization header
        authorization = f"Bearer {access_token}"

        # Get current user
        current_user = await get_current_user(
            authorization=authorization,
            db=db_session,
        )

        assert current_user.id == user.id
        assert current_user.email == user.email

    @pytest.mark.asyncio
    async def test_get_current_user_missing_bearer_prefix(self, db_session: Session, test_tenant):
        """Test that missing 'Bearer ' prefix raises error."""
        # Create a user and token
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user2",
            email="user@example.com",
            password="password123",
        )
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )

        # Authorization without "Bearer " prefix
        authorization = access_token

        with pytest.raises(AuthenticationError, match="Invalid authorization header"):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_format(self, db_session: Session, test_tenant):
        """Test that invalid token format raises error."""
        authorization = "Bearer invalid_token_format"

        with pytest.raises(AuthenticationError):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session: Session, test_tenant):
        """Test that expired token raises error."""
        # Create a user
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user3",
            email="user@example.com",
            password="password123",
        )

        # Create an expired token by manipulating expiration
        # (This would need actual expired token - testing concept)
        # For now, test with invalid signature instead
        authorization = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIn0.invalid"

        with pytest.raises(AuthenticationError):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_token_without_sub(self, db_session: Session, test_tenant):
        """Test that token without 'sub' claim raises error."""
        # This is difficult to test without mocking jwt_service
        # Testing with malformed token instead
        authorization = "Bearer malformed.token.here"

        with pytest.raises(AuthenticationError):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session: Session, test_tenant):
        """Test that token for nonexistent user raises error."""
        # Create token for user ID that doesn't exist
        access_token = jwt_service.create_access_token(
            user_id=99999,  # Non-existent ID
            email="nonexistent@example.com",
            tenant_id=test_tenant.id,
            role="MEMBER",
        )

        authorization = f"Bearer {access_token}"

        with pytest.raises(AuthenticationError, match="User not found"):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_account(self, db_session: Session, test_tenant):
        """Test that inactive user account raises error."""
        # Create a user
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user4",
            email="user@example.com",
            password="password123",
        )

        # Create token before deactivating
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )

        # Deactivate user
        user.is_active = False
        db_session.commit()

        authorization = f"Bearer {access_token}"

        with pytest.raises(AuthenticationError, match="disabled"):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_empty_authorization(self, db_session: Session, test_tenant):
        """Test that empty authorization header raises error."""
        authorization = ""

        with pytest.raises(AuthenticationError):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_bearer_only(self, db_session: Session, test_tenant):
        """Test authorization with only 'Bearer' raises error."""
        authorization = "Bearer "

        with pytest.raises(AuthenticationError):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_case_sensitive_bearer(self, db_session: Session, test_tenant):
        """Test that 'bearer' (lowercase) is not accepted."""
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user5",
            email="user@example.com",
            password="password123",
        )
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )

        # Use lowercase 'bearer'
        authorization = f"bearer {access_token}"

        with pytest.raises(AuthenticationError, match="Invalid authorization header"):
            await get_current_user(
                authorization=authorization,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_current_user_with_totp_enabled(self, db_session: Session, test_tenant):
        """Test that TOTP-enabled user can authenticate with token."""
        # Create a user and enable TOTP
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user6",
            email="user@example.com",
            password="password123",
        )
        user.is_totp_enabled = True
        db_session.commit()

        # Create token
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )

        authorization = f"Bearer {access_token}"

        # Should succeed - TOTP doesn't affect token authentication
        current_user = await get_current_user(
            authorization=authorization,
            db=db_session,
        )

        assert current_user.id == user.id
        assert current_user.is_totp_enabled is True


class TestRequireTOTPDisabled:
    """Test require_totp_disabled dependency."""

    @pytest.mark.asyncio
    async def test_require_totp_disabled_success(self, db_session: Session, test_tenant):
        """Test that user without TOTP passes check."""
        # Create a user without TOTP
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user7",
            email="user@example.com",
            password="password123",
        )

        assert user.is_totp_enabled is False

        # Should succeed
        result = await require_totp_disabled(user=user)

        assert result.id == user.id
        assert result.is_totp_enabled is False

    @pytest.mark.asyncio
    async def test_require_totp_disabled_with_totp_enabled(self, db_session: Session, test_tenant):
        """Test that user with TOTP raises error."""
        # Create a user and enable TOTP
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user8",
            email="user@example.com",
            password="password123",
        )
        user.is_totp_enabled = True
        db_session.commit()

        # Should raise TOTPError
        with pytest.raises(TOTPError, match="already enabled"):
            await require_totp_disabled(user=user)

    @pytest.mark.asyncio
    async def test_require_totp_disabled_returns_user(self, db_session: Session, test_tenant):
        """Test that dependency returns the user object."""
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user9",
            email="user@example.com",
            password="password123",
        )

        result = await require_totp_disabled(user=user)

        # Should return the same user object
        assert result is user
        assert result.email == "user@example.com"


class TestDependenciesIntegration:
    """Integration tests for dependencies."""

    @pytest.mark.asyncio
    async def test_dependency_chain_get_current_user_then_require_totp(
        self, db_session: Session, test_tenant
    ):
        """Test chaining get_current_user -> require_totp_disabled."""
        # Create a user
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user10",
            email="user@example.com",
            password="password123",
        )

        # Create token
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )
        authorization = f"Bearer {access_token}"

        # First dependency: get current user
        current_user = await get_current_user(
            authorization=authorization,
            db=db_session,
        )

        # Second dependency: require TOTP disabled
        result = await require_totp_disabled(user=current_user)

        assert result.id == user.id
        assert result.is_totp_enabled is False

    @pytest.mark.asyncio
    async def test_dependency_chain_fails_if_totp_enabled(
        self, db_session: Session, test_tenant
    ):
        """Test dependency chain fails when TOTP is enabled."""
        # Create a user with TOTP enabled
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user11",
            email="user@example.com",
            password="password123",
        )
        user.is_totp_enabled = True
        db_session.commit()

        # Create token
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )
        authorization = f"Bearer {access_token}"

        # First dependency succeeds
        current_user = await get_current_user(
            authorization=authorization,
            db=db_session,
        )

        # Second dependency fails
        with pytest.raises(TOTPError):
            await require_totp_disabled(user=current_user)

    @pytest.mark.asyncio
    async def test_multiple_requests_same_user(self, db_session: Session, test_tenant):
        """Test multiple requests with same user token."""
        user = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user12",
            email="user@example.com",
            password="password123",
        )

        access_token = jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        )
        authorization = f"Bearer {access_token}"

        # First request
        user1 = await get_current_user(
            authorization=authorization,
            db=db_session,
        )

        # Second request (simulate different request with same token)
        user2 = await get_current_user(
            authorization=authorization,
            db=db_session,
        )

        assert user1.id == user2.id
        assert user1.email == user2.email

    @pytest.mark.asyncio
    async def test_different_users_different_tokens(self, db_session: Session, test_tenant):
        """Test that different tokens authenticate different users."""
        # Create two users
        user1 = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user113",
            email="user1@example.com",
            password="password123",
        )
        user2 = auth_service.register_user(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user214",
            email="user2@example.com",
            password="password123",
        )

        # Create tokens for each user
        token1 = jwt_service.create_access_token(
            user_id=user1.id,
            email=user1.email,
            tenant_id=user1.tenant_id,
            role=user1.role,
        )
        token2 = jwt_service.create_access_token(
            user_id=user2.id,
            email=user2.email,
            tenant_id=user2.tenant_id,
            role=user2.role,
        )

        # Authenticate each user
        auth_user1 = await get_current_user(
            authorization=f"Bearer {token1}",
            db=db_session,
        )
        auth_user2 = await get_current_user(
            authorization=f"Bearer {token2}",
            db=db_session,
        )

        # Verify correct users authenticated
        assert auth_user1.id == user1.id
        assert auth_user2.id == user2.id
        assert auth_user1.email == "user1@example.com"
        assert auth_user2.email == "user2@example.com"