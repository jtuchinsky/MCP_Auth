"""Unit tests for user schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.repositories import tenant_repository
from app.schemas.user import UserCreate, UserResponse, UserUpdate


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
    """Create a test tenant for schema tests."""
    return tenant_repository.create(
        db=db_session,
        email="schemas_tenant@example.com",
        password_hash="tenant_hash_123",
    )


class TestUserCreate:
    """Test UserCreate schema."""

    def test_user_create_valid(self):
        """Test creating UserCreate with valid data."""
        data = {
            "tenant_id": 1,
            "username": "testuser",
            "email": "user@example.com",
            "password": "secure_password_123",
            "role": "MEMBER",
        }
        user = UserCreate(**data)

        assert user.tenant_id == 1
        assert user.username == "testuser"
        assert user.email == "user@example.com"
        assert user.password == "secure_password_123"
        assert user.role == "MEMBER"

    def test_user_create_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.com",
            "user_name@example-domain.com",
        ]

        for email in valid_emails:
            user = UserCreate(
                tenant_id=1,
                username="testuser",
                email=email,
                password="password123",
                role="MEMBER",
            )
            assert user.email == email

    def test_user_create_invalid_email(self):
        """Test that invalid email raises ValidationError."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserCreate(
                    tenant_id=1,
                    username="testuser",
                    email=email,
                    password="password123",
                    role="MEMBER",
                )

    def test_user_create_password_min_length(self):
        """Test that password must be at least 8 characters."""
        # Valid 8-character password
        user = UserCreate(
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            password="12345678",
            role="MEMBER",
        )
        assert len(user.password) == 8

        # Too short password
        with pytest.raises(ValidationError):
            UserCreate(
                tenant_id=1,
                username="testuser",
                email="user@example.com",
                password="1234567",
                role="MEMBER",
            )

    def test_user_create_password_max_length(self):
        """Test that password has maximum length of 100 characters."""
        # Valid 100-character password
        password_100 = "a" * 100
        user = UserCreate(
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            password=password_100,
            role="MEMBER",
        )
        assert len(user.password) == 100

        # Too long password
        password_101 = "a" * 101
        with pytest.raises(ValidationError):
            UserCreate(
                tenant_id=1,
                username="testuser",
                email="user@example.com",
                password=password_101,
                role="MEMBER",
            )

    def test_user_create_missing_email(self):
        """Test that email is required."""
        with pytest.raises(ValidationError):
            UserCreate(
                tenant_id=1,
                username="testuser",
                password="password123",
                role="MEMBER",
            )

    def test_user_create_missing_password(self):
        """Test that password is required."""
        with pytest.raises(ValidationError):
            UserCreate(
                tenant_id=1,
                username="testuser",
                email="user@example.com",
                role="MEMBER",
            )

    def test_user_create_empty_password(self):
        """Test that empty password is invalid."""
        with pytest.raises(ValidationError):
            UserCreate(
                tenant_id=1,
                username="testuser",
                email="user@example.com",
                password="",
                role="MEMBER",
            )

    def test_user_create_special_characters_in_password(self):
        """Test password with special characters."""
        passwords = [
            "p@ssw0rd!",
            "p#a$s%s^w&o*r(d)",
            "password-with_symbols.123",
            "пароль123",  # Unicode (Cyrillic)
            "密码12345678",  # Chinese (8 chars)
        ]

        for password in passwords:
            user = UserCreate(
                tenant_id=1,
                username="testuser",
                email="user@example.com",
                password=password,
                role="MEMBER",
            )
            assert user.password == password

    def test_user_create_model_dump(self):
        """Test serializing UserCreate to dict."""
        user = UserCreate(
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            password="password123",
            role="MEMBER",
        )
        data = user.model_dump()

        assert data == {
            "tenant_id": 1,
            "username": "testuser",
            "email": "user@example.com",
            "password": "password123",
            "role": "MEMBER",
        }

    def test_user_create_model_dump_json(self):
        """Test serializing UserCreate to JSON."""
        user = UserCreate(
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            password="password123",
            role="MEMBER",
        )
        json_str = user.model_dump_json()

        assert "user@example.com" in json_str
        assert "testuser" in json_str
        assert "password123" in json_str


class TestUserResponse:
    """Test UserResponse schema."""

    def test_user_response_valid(self):
        """Test creating UserResponse with valid data."""
        data = {
            "id": 1,
            "tenant_id": 1,
            "username": "testuser",
            "email": "user@example.com",
            "role": "MEMBER",
            "is_totp_enabled": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        user = UserResponse(**data)

        assert user.id == 1
        assert user.tenant_id == 1
        assert user.username == "testuser"
        assert user.email == "user@example.com"
        assert user.role == "MEMBER"
        assert user.is_totp_enabled is False
        assert user.is_active is True

    def test_user_response_from_orm_model(self, test_tenant):
        """Test creating UserResponse from ORM User model."""
        # Create an ORM User instance (not saved to DB)
        orm_user = User(
            id=1,
            tenant_id=test_tenant.id,
            username="ormuser",
            email="user@example.com",
            password_hash="hashed_password",
            role="MEMBER",
            is_totp_enabled=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Convert to Pydantic schema
        user_response = UserResponse.model_validate(orm_user)

        assert user_response.id == 1
        assert user_response.email == "user@example.com"
        assert user_response.is_totp_enabled is True
        assert user_response.is_active is True
        # Should not include password_hash
        assert not hasattr(user_response, "password_hash")

    def test_user_response_missing_required_field(self):
        """Test that all fields are required."""
        # Missing id
        with pytest.raises(ValidationError):
            UserResponse(
                tenant_id=1,
                username="testuser",
                email="user@example.com",
                role="MEMBER",
                is_totp_enabled=False,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        # Missing email
        with pytest.raises(ValidationError):
            UserResponse(
                id=1,
                tenant_id=1,
                username="testuser",
                role="MEMBER",
                is_totp_enabled=False,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    def test_user_response_boolean_fields(self):
        """Test boolean field validation."""
        data = {
            "id": 1,
            "tenant_id": 1,
            "username": "testuser",
            "email": "user@example.com",
            "role": "MEMBER",
            "is_totp_enabled": True,
            "is_active": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        user = UserResponse(**data)

        assert user.is_totp_enabled is True
        assert user.is_active is False

    def test_user_response_datetime_fields(self):
        """Test datetime field handling."""
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "tenant_id": 1,
            "username": "testuser",
            "email": "user@example.com",
            "role": "MEMBER",
            "is_totp_enabled": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        user = UserResponse(**data)

        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.created_at == now
        assert user.updated_at == now

    def test_user_response_model_dump(self):
        """Test serializing UserResponse to dict."""
        now = datetime.now(timezone.utc)
        user = UserResponse(
            id=1,
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            role="MEMBER",
            is_totp_enabled=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        data = user.model_dump()

        assert data["id"] == 1
        assert data["tenant_id"] == 1
        assert data["username"] == "testuser"
        assert data["email"] == "user@example.com"
        assert data["role"] == "MEMBER"
        assert data["is_totp_enabled"] is False
        assert data["is_active"] is True
        assert isinstance(data["created_at"], datetime)

    def test_user_response_model_dump_json(self):
        """Test serializing UserResponse to JSON."""
        user = UserResponse(
            id=1,
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            role="MEMBER",
            is_totp_enabled=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        json_str = user.model_dump_json()

        assert "user@example.com" in json_str
        assert "testuser" in json_str
        assert '"id":1' in json_str or '"id": 1' in json_str


class TestUserUpdate:
    """Test UserUpdate schema."""

    def test_user_update_all_fields(self):
        """Test UserUpdate with all fields provided."""
        data = {
            "email": "newemail@example.com",
            "password": "new_password_123",
            "is_active": False,
        }
        user_update = UserUpdate(**data)

        assert user_update.email == "newemail@example.com"
        assert user_update.password == "new_password_123"
        assert user_update.is_active is False

    def test_user_update_partial_fields(self):
        """Test UserUpdate with only some fields."""
        # Only email
        update1 = UserUpdate(email="newemail@example.com")
        assert update1.email == "newemail@example.com"
        assert update1.password is None
        assert update1.is_active is None

        # Only password
        update2 = UserUpdate(password="new_password_123")
        assert update2.email is None
        assert update2.password == "new_password_123"
        assert update2.is_active is None

        # Only is_active
        update3 = UserUpdate(is_active=False)
        assert update3.email is None
        assert update3.password is None
        assert update3.is_active is False

    def test_user_update_no_fields(self):
        """Test UserUpdate with no fields (all optional)."""
        user_update = UserUpdate()

        assert user_update.email is None
        assert user_update.password is None
        assert user_update.is_active is None

    def test_user_update_email_validation(self):
        """Test email validation in UserUpdate."""
        # Valid email
        update = UserUpdate(email="valid@example.com")
        assert update.email == "valid@example.com"

        # Invalid email
        with pytest.raises(ValidationError):
            UserUpdate(email="invalid-email")

    def test_user_update_password_min_length(self):
        """Test password minimum length in UserUpdate."""
        # Valid password
        update = UserUpdate(password="12345678")
        assert update.password == "12345678"

        # Too short
        with pytest.raises(ValidationError):
            UserUpdate(password="1234567")

    def test_user_update_password_max_length(self):
        """Test password maximum length in UserUpdate."""
        # Valid 100-character password
        password_100 = "a" * 100
        update = UserUpdate(password=password_100)
        assert len(update.password) == 100

        # Too long
        password_101 = "a" * 101
        with pytest.raises(ValidationError):
            UserUpdate(password=password_101)

    def test_user_update_exclude_unset(self):
        """Test excluding unset fields."""
        update = UserUpdate(email="newemail@example.com")
        data = update.model_dump(exclude_unset=True)

        assert "email" in data
        assert "password" not in data
        assert "is_active" not in data

    def test_user_update_model_dump(self):
        """Test serializing UserUpdate to dict."""
        update = UserUpdate(
            email="newemail@example.com",
            password="new_password",
        )
        data = update.model_dump()

        assert data["email"] == "newemail@example.com"
        assert data["password"] == "new_password"
        assert data["is_active"] is None


class TestUserSchemasIntegration:
    """Integration tests for user schemas."""

    def test_create_user_workflow(self, test_tenant):
        """Test complete user creation workflow with schemas."""
        # 1. Client sends UserCreate
        create_data = UserCreate(
            tenant_id=test_tenant.id,
            username="workflowuser",
            email="user@example.com",
            password="secure_password_123",
            role="MEMBER",
        )

        assert create_data.tenant_id == test_tenant.id
        assert create_data.username == "workflowuser"
        assert create_data.email == "user@example.com"
        assert create_data.password == "secure_password_123"
        assert create_data.role == "MEMBER"

        # 2. Server creates ORM model (simulate)
        orm_user = User(
            id=1,
            tenant_id=test_tenant.id,
            username="workflowuser",
            email=create_data.email,
            password_hash="hashed_" + create_data.password,  # Would be bcrypt hash
            role="MEMBER",
            is_totp_enabled=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # 3. Server returns UserResponse
        response = UserResponse.model_validate(orm_user)

        assert response.id == 1
        assert response.email == "user@example.com"
        assert response.is_totp_enabled is False
        assert response.is_active is True
        assert not hasattr(response, "password_hash")

    def test_update_user_workflow(self):
        """Test user update workflow with schemas."""
        # Client sends partial update
        update_data = UserUpdate(email="newemail@example.com")

        # Only email should be set
        assert update_data.email == "newemail@example.com"
        assert update_data.password is None
        assert update_data.is_active is None

        # Check exclude_unset
        updates = update_data.model_dump(exclude_unset=True)
        assert "email" in updates
        assert "password" not in updates

    def test_schemas_json_serialization(self):
        """Test that all schemas are JSON serializable."""
        import json

        # UserCreate
        create = UserCreate(
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            password="password123",
            role="MEMBER",
        )
        json.loads(create.model_dump_json())

        # UserResponse
        response = UserResponse(
            id=1,
            tenant_id=1,
            username="testuser",
            email="user@example.com",
            role="MEMBER",
            is_totp_enabled=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        json.loads(response.model_dump_json())

        # UserUpdate
        update = UserUpdate(email="newemail@example.com")
        json.loads(update.model_dump_json())