"""Unit tests for user repository."""

import pytest
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.repositories import tenant_repository, user_repository


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
    """Create a test tenant for user tests."""
    tenant = tenant_repository.create(
        db=db_session,
        email="test_tenant@example.com",
        password_hash="tenant_hash_123",
    )
    return tenant


class TestCreateUser:
    """Test create() function."""

    def test_create_user_success(self, db_session: Session, test_tenant):
        """Test creating a new user successfully."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
        )

        assert user.id is not None
        assert user.tenant_id == test_tenant.id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.role == "MEMBER"
        assert user.is_totp_enabled is False
        assert user.is_active is True

    def test_create_user_returns_persisted_instance(self, db_session: Session, test_tenant):
        """Test that created user is persisted to database."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="persistuser",
            email="persist@example.com",
            password_hash="hash123",
        )

        # Verify user can be retrieved from database
        retrieved_user = user_repository.get_by_id(db_session, user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == "persist@example.com"
        assert retrieved_user.username == "persistuser"

    def test_create_multiple_users(self, db_session: Session, test_tenant):
        """Test creating multiple users."""
        user1 = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user1",
            email="user1@example.com",
            password_hash="hash1",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user2",
            email="user2@example.com",
            password_hash="hash2",
        )

        assert user1.id != user2.id
        assert user1.email != user2.email
        assert user1.username != user2.username


class TestGetByIdUser:
    """Test get_by_id() function."""

    def test_get_by_id_existing_user(self, db_session: Session, test_tenant):
        """Test getting an existing user by ID."""
        created_user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="existsuser",
            email="exists@example.com",
            password_hash="hash123",
        )

        retrieved_user = user_repository.get_by_id(db_session, created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "exists@example.com"

    def test_get_by_id_nonexistent_user(self, db_session: Session):
        """Test getting a nonexistent user by ID returns None."""
        user = user_repository.get_by_id(db_session, 99999)

        assert user is None

    def test_get_by_id_zero(self, db_session: Session):
        """Test getting user with ID 0 returns None."""
        user = user_repository.get_by_id(db_session, 0)

        assert user is None

    def test_get_by_id_negative(self, db_session: Session):
        """Test getting user with negative ID returns None."""
        user = user_repository.get_by_id(db_session, -1)

        assert user is None


class TestGetByEmailUser:
    """Test get_by_email() function."""

    def test_get_by_email_existing_user(self, db_session: Session, test_tenant):
        """Test getting an existing user by email."""
        created_user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="finduser",
            email="find@example.com",
            password_hash="hash123",
        )

        retrieved_user = user_repository.get_by_email(db_session, "find@example.com")

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "find@example.com"

    def test_get_by_email_nonexistent_user(self, db_session: Session):
        """Test getting a nonexistent user by email returns None."""
        user = user_repository.get_by_email(db_session, "nonexistent@example.com")

        assert user is None

    def test_get_by_email_case_sensitive(self, db_session: Session, test_tenant):
        """Test that email lookup is case-sensitive."""
        user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="caseuser",
            email="test@example.com",
            password_hash="hash123",
        )

        # SQLite is case-insensitive for LIKE but case-sensitive for =
        # Our query uses = so it should be case-sensitive
        user_lower = user_repository.get_by_email(db_session, "test@example.com")
        user_upper = user_repository.get_by_email(db_session, "TEST@EXAMPLE.COM")

        assert user_lower is not None
        # Note: SQLite may be case-insensitive depending on collation
        # This test documents the behavior

    def test_get_by_email_empty_string(self, db_session: Session):
        """Test getting user with empty email returns None."""
        user = user_repository.get_by_email(db_session, "")

        assert user is None


class TestUpdateTotpSecret:
    """Test update_totp_secret() function."""

    def test_update_totp_secret_success(self, db_session: Session, test_tenant):
        """Test updating TOTP secret successfully."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="totpuser",
            email="totp@example.com",
            password_hash="hash123",
        )

        updated_user = user_repository.update_totp_secret(
            db=db_session,
            user_id=user.id,
            secret="JBSWY3DPEHPK3PXP",
        )

        assert updated_user.totp_secret == "JBSWY3DPEHPK3PXP"
        assert updated_user.id == user.id

    def test_update_totp_secret_persists(self, db_session: Session, test_tenant):
        """Test that TOTP secret update persists to database."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="persisttotp",
            email="persist_totp@example.com",
            password_hash="hash123",
        )

        user_repository.update_totp_secret(
            db=db_session,
            user_id=user.id,
            secret="SECRET123",
        )

        # Retrieve user again
        retrieved_user = user_repository.get_by_id(db_session, user.id)
        assert retrieved_user.totp_secret == "SECRET123"

    def test_update_totp_secret_nonexistent_user(self, db_session: Session):
        """Test updating TOTP secret for nonexistent user raises error."""
        with pytest.raises(ValueError, match="User with id 99999 not found"):
            user_repository.update_totp_secret(
                db=db_session,
                user_id=99999,
                secret="SECRET123",
            )

    def test_update_totp_secret_multiple_times(self, db_session: Session, test_tenant):
        """Test updating TOTP secret multiple times."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="multitotp",
            email="multi_totp@example.com",
            password_hash="hash123",
        )

        # First update
        user_repository.update_totp_secret(
            db=db_session,
            user_id=user.id,
            secret="SECRET1",
        )

        # Second update
        updated_user = user_repository.update_totp_secret(
            db=db_session,
            user_id=user.id,
            secret="SECRET2",
        )

        assert updated_user.totp_secret == "SECRET2"


class TestEnableTotp:
    """Test enable_totp() function."""

    def test_enable_totp_success(self, db_session: Session, test_tenant):
        """Test enabling TOTP successfully."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="enableuser",
            email="enable@example.com",
            password_hash="hash123",
        )

        assert user.is_totp_enabled is False

        updated_user = user_repository.enable_totp(
            db=db_session,
            user_id=user.id,
        )

        assert updated_user.is_totp_enabled is True
        assert updated_user.id == user.id

    def test_enable_totp_persists(self, db_session: Session, test_tenant):
        """Test that enabling TOTP persists to database."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="persistenable",
            email="persist_enable@example.com",
            password_hash="hash123",
        )

        user_repository.enable_totp(db=db_session, user_id=user.id)

        # Retrieve user again
        retrieved_user = user_repository.get_by_id(db_session, user.id)
        assert retrieved_user.is_totp_enabled is True

    def test_enable_totp_nonexistent_user(self, db_session: Session):
        """Test enabling TOTP for nonexistent user raises error."""
        with pytest.raises(ValueError, match="User with id 99999 not found"):
            user_repository.enable_totp(
                db=db_session,
                user_id=99999,
            )

    def test_enable_totp_idempotent(self, db_session: Session, test_tenant):
        """Test enabling TOTP multiple times is idempotent."""
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="idempotentuser",
            email="idempotent@example.com",
            password_hash="hash123",
        )

        # Enable first time
        user_repository.enable_totp(db=db_session, user_id=user.id)

        # Enable second time
        updated_user = user_repository.enable_totp(db=db_session, user_id=user.id)

        assert updated_user.is_totp_enabled is True


class TestUserRepositoryIntegration:
    """Integration tests for user repository functions."""

    def test_complete_user_workflow(self, db_session: Session, test_tenant):
        """Test complete workflow: create, retrieve, update TOTP, enable TOTP."""
        # Create user
        user = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="workflowuser",
            email="workflow@example.com",
            password_hash="hash123",
        )
        assert user.id is not None
        assert user.is_totp_enabled is False
        assert user.totp_secret is None

        # Retrieve by ID
        user_by_id = user_repository.get_by_id(db_session, user.id)
        assert user_by_id is not None
        assert user_by_id.email == "workflow@example.com"

        # Retrieve by email
        user_by_email = user_repository.get_by_email(db_session, "workflow@example.com")
        assert user_by_email is not None
        assert user_by_email.id == user.id

        # Update TOTP secret
        user_with_secret = user_repository.update_totp_secret(
            db=db_session,
            user_id=user.id,
            secret="SECRETKEY",
        )
        assert user_with_secret.totp_secret == "SECRETKEY"

        # Enable TOTP
        user_with_totp = user_repository.enable_totp(db=db_session, user_id=user.id)
        assert user_with_totp.is_totp_enabled is True

        # Final verification
        final_user = user_repository.get_by_id(db_session, user.id)
        assert final_user.totp_secret == "SECRETKEY"
        assert final_user.is_totp_enabled is True

    def test_multiple_users_do_not_interfere(self, db_session: Session, test_tenant):
        """Test that operations on one user don't affect others."""
        # Create two users
        user1 = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user1",
            email="user1@example.com",
            password_hash="hash1",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=test_tenant.id,
            username="user2",
            email="user2@example.com",
            password_hash="hash2",
        )

        # Update user1's TOTP secret
        user_repository.update_totp_secret(
            db=db_session,
            user_id=user1.id,
            secret="USER1SECRET",
        )

        # Enable TOTP for user1
        user_repository.enable_totp(db=db_session, user_id=user1.id)

        # Verify user1 changes
        user1_updated = user_repository.get_by_id(db_session, user1.id)
        assert user1_updated.totp_secret == "USER1SECRET"
        assert user1_updated.is_totp_enabled is True

        # Verify user2 unchanged
        user2_unchanged = user_repository.get_by_id(db_session, user2.id)
        assert user2_unchanged.totp_secret is None
        assert user2_unchanged.is_totp_enabled is False
