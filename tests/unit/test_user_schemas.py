"""Unit tests for user schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class TestUserCreate:
    """Test UserCreate schema."""

    def test_user_create_valid(self):
        """Test creating UserCreate with valid data."""
        data = {
            "email": "user@example.com",
            "password": "secure_password_123",
        }
        user = UserCreate(**data)

        assert user.email == "user@example.com"
        assert user.password == "secure_password_123"

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
            user = UserCreate(email=email, password="password123")
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
                UserCreate(email=email, password="password123")

    def test_user_create_password_min_length(self):
        """Test that password must be at least 8 characters."""
        # Valid 8-character password
        user = UserCreate(email="user@example.com", password="12345678")
        assert len(user.password) == 8

        # Too short password
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", password="1234567")

    def test_user_create_password_max_length(self):
        """Test that password has maximum length of 100 characters."""
        # Valid 100-character password
        password_100 = "a" * 100
        user = UserCreate(email="user@example.com", password=password_100)
        assert len(user.password) == 100

        # Too long password
        password_101 = "a" * 101
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", password=password_101)

    def test_user_create_missing_email(self):
        """Test that email is required."""
        with pytest.raises(ValidationError):
            UserCreate(password="password123")

    def test_user_create_missing_password(self):
        """Test that password is required."""
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com")

    def test_user_create_empty_password(self):
        """Test that empty password is invalid."""
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", password="")

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
            user = UserCreate(email="user@example.com", password=password)
            assert user.password == password

    def test_user_create_model_dump(self):
        """Test serializing UserCreate to dict."""
        user = UserCreate(email="user@example.com", password="password123")
        data = user.model_dump()

        assert data == {
            "email": "user@example.com",
            "password": "password123",
        }

    def test_user_create_model_dump_json(self):
        """Test serializing UserCreate to JSON."""
        user = UserCreate(email="user@example.com", password="password123")
        json_str = user.model_dump_json()

        assert "user@example.com" in json_str
        assert "password123" in json_str


class TestUserResponse:
    """Test UserResponse schema."""

    def test_user_response_valid(self):
        """Test creating UserResponse with valid data."""
        data = {
            "id": 1,
            "email": "user@example.com",
            "is_totp_enabled": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        user = UserResponse(**data)

        assert user.id == 1
        assert user.email == "user@example.com"
        assert user.is_totp_enabled is False
        assert user.is_active is True

    def test_user_response_from_orm_model(self):
        """Test creating UserResponse from ORM User model."""
        # Create an ORM User instance (not saved to DB)
        orm_user = User(
            id=1,
            email="user@example.com",
            password_hash="hashed_password",
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
                email="user@example.com",
                is_totp_enabled=False,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        # Missing email
        with pytest.raises(ValidationError):
            UserResponse(
                id=1,
                is_totp_enabled=False,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    def test_user_response_boolean_fields(self):
        """Test boolean field validation."""
        data = {
            "id": 1,
            "email": "user@example.com",
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
            "email": "user@example.com",
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
            email="user@example.com",
            is_totp_enabled=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        data = user.model_dump()

        assert data["id"] == 1
        assert data["email"] == "user@example.com"
        assert data["is_totp_enabled"] is False
        assert data["is_active"] is True
        assert isinstance(data["created_at"], datetime)

    def test_user_response_model_dump_json(self):
        """Test serializing UserResponse to JSON."""
        user = UserResponse(
            id=1,
            email="user@example.com",
            is_totp_enabled=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        json_str = user.model_dump_json()

        assert "user@example.com" in json_str
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

    def test_create_user_workflow(self):
        """Test complete user creation workflow with schemas."""
        # 1. Client sends UserCreate
        create_data = UserCreate(
            email="user@example.com",
            password="secure_password_123",
        )

        assert create_data.email == "user@example.com"
        assert create_data.password == "secure_password_123"

        # 2. Server creates ORM model (simulate)
        orm_user = User(
            id=1,
            email=create_data.email,
            password_hash="hashed_" + create_data.password,  # Would be bcrypt hash
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
        create = UserCreate(email="user@example.com", password="password123")
        json.loads(create.model_dump_json())

        # UserResponse
        response = UserResponse(
            id=1,
            email="user@example.com",
            is_totp_enabled=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        json.loads(response.model_dump_json())

        # UserUpdate
        update = UserUpdate(email="newemail@example.com")
        json.loads(update.model_dump_json())