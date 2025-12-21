"""User schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="User's password (min 8 chars)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "secure_password_123",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: int = Field(..., description="User's unique ID")
    email: str = Field(..., description="User's email address")
    is_totp_enabled: bool = Field(..., description="Whether TOTP 2FA is enabled")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_totp_enabled": False,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    email: EmailStr | None = Field(None, description="New email address")
    password: str | None = Field(
        None, min_length=8, max_length=100, description="New password (min 8 chars)"
    )
    is_active: bool | None = Field(None, description="Account active status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "password": "new_secure_password",
            }
        }
    )