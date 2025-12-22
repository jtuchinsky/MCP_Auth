"""TOTP schemas for API requests and responses."""

from pydantic import BaseModel, ConfigDict, Field


class TOTPSetupResponse(BaseModel):
    """Schema for TOTP setup response."""

    secret: str = Field(..., description="Base32-encoded TOTP secret")
    provisioning_uri: str = Field(
        ..., description="otpauth:// URI for authenticator apps"
    )
    qr_code: str = Field(..., description="Base64-encoded QR code PNG image")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "provisioning_uri": "otpauth://totp/MCP%20Auth%20Service:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MCP%20Auth%20Service",
                "qr_code": "iVBORw0KGgoAAAANSUhEUgAA...",
            }
        }
    )


class TOTPVerifyRequest(BaseModel):
    """Schema for TOTP verification request during setup."""

    totp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code from authenticator app",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "totp_code": "123456",
            }
        }
    )


class TOTPValidateRequest(BaseModel):
    """Schema for TOTP validation request (alias for verify)."""

    totp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code to validate",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "totp_code": "654321",
            }
        }
    )