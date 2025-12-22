"""Authentication schemas for API requests and responses."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User's email address")
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
                "email": "user@example.com",
                "password": "secure_password_123",
                "totp_code": "123456",
            }
        }
    )


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Refresh token to exchange")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "8f7d6e5c4b3a2d1e0f9g8h7i6j5k4l3m2n1",
            }
        }
    )