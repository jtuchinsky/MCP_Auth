"""Tenant schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantLoginRequest(BaseModel):
    """Schema for tenant login request.

    Used when logging in as a tenant (owner). If the tenant doesn't exist,
    it will be created automatically along with an owner user.
    """

    tenant_email: EmailStr = Field(..., description="Tenant's email address (globally unique)")
    tenant_name: str | None = Field(None, max_length=255, description="Tenant's organization name (optional)")
    password: str = Field(..., description="Tenant's password")
    totp_code: str | None = Field(
        None,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="TOTP code (required if 2FA enabled for owner)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_email": "company@example.com",
                "tenant_name": "Acme Corporation",
                "password": "secure_password_123",
                "totp_code": "123456",
            }
        }
    )


class TenantUserLoginRequest(BaseModel):
    """Schema for user login within a tenant.

    Used when logging in as a non-owner user within an existing tenant.
    """

    tenant_email: EmailStr = Field(..., description="Tenant's email address")
    username: str = Field(..., description="User's username within the tenant")
    password: str = Field(..., description="User's password")
    totp_code: str | None = Field(
        None,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="TOTP code (required if 2FA enabled)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_email": "company@example.com",
                "username": "alice",
                "password": "secure_password_123",
                "totp_code": "123456",
            }
        }
    )


class TenantResponse(BaseModel):
    """Schema for tenant data in API responses."""

    id: int = Field(..., description="Tenant's unique ID")
    email: str = Field(..., description="Tenant's email address")
    tenant_name: str | None = Field(None, description="Tenant's organization name")
    is_active: bool = Field(..., description="Whether tenant account is active")
    created_at: datetime = Field(..., description="Tenant creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "email": "company@example.com",
                "tenant_name": "Acme Corporation",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class TenantCreate(BaseModel):
    """Schema for creating a new tenant (admin use).

    Note: In normal operation, tenants are created automatically via login.
    This schema is for administrative tenant creation.
    """

    email: EmailStr = Field(..., description="Tenant's email address (globally unique)")
    tenant_name: str | None = Field(None, max_length=255, description="Tenant's organization name (optional)")
    password: str = Field(
        ..., min_length=8, max_length=100, description="Tenant's password (min 8 chars)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newcompany@example.com",
                "tenant_name": "New Company Inc",
                "password": "secure_password_123",
            }
        }
    )


class TenantUpdate(BaseModel):
    """Schema for updating tenant information.

    Only OWNER or ADMIN roles can update tenant information.
    Used by PUT /tenants/me endpoint.
    """

    tenant_name: str | None = Field(None, max_length=255, description="New tenant name (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_name": "Updated Company Name",
            }
        }
    )


class TenantStatusUpdate(BaseModel):
    """Schema for updating tenant status (activate/deactivate).

    Only OWNER role can update tenant status.
    Used by PATCH /tenants/me/status endpoint.
    """

    is_active: bool = Field(..., description="New tenant status (true=active, false=inactive)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_active": False,
            }
        }
    )