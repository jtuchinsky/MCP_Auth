"""User schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user within a tenant.

    Used for inviting additional users to a tenant (future feature).
    """

    tenant_id: int = Field(..., description="Tenant ID the user belongs to")
    username: str = Field(..., min_length=3, max_length=100, description="User's username (unique per tenant)")
    email: EmailStr = Field(..., description="User's email address (globally unique)")
    password: str = Field(
        ..., min_length=8, max_length=100, description="User's password (min 8 chars)"
    )
    role: str = Field(default="MEMBER", description="User's role (OWNER, ADMIN, MEMBER)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_id": 1,
                "username": "alice",
                "email": "alice@example.com",
                "password": "secure_password_123",
                "role": "MEMBER",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: int = Field(..., description="User's unique ID")
    tenant_id: int = Field(..., description="Tenant ID the user belongs to")
    username: str = Field(..., description="User's username within the tenant")
    email: str = Field(..., description="User's email address")
    role: str = Field(..., description="User's role (OWNER, ADMIN, MEMBER)")
    is_totp_enabled: bool = Field(..., description="Whether TOTP 2FA is enabled")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "tenant_id": 2,
                "username": "company@example.com",
                "email": "company@example.com",
                "role": "OWNER",
                "is_totp_enabled": False,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    username: str | None = Field(None, min_length=3, max_length=100, description="New username")
    email: EmailStr | None = Field(None, description="New email address")
    password: str | None = Field(
        None, min_length=8, max_length=100, description="New password (min 8 chars)"
    )
    is_active: bool | None = Field(None, description="Account active status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "newalice",
                "email": "newemail@example.com",
                "password": "new_secure_password",
            }
        }
    )