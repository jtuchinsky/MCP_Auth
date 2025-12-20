"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./mcp_auth.db",
        description="Database connection URL",
    )

    # Security Configuration
    secret_key: str = Field(
        ...,  # Required field
        description="Secret key for JWT signing (min 32 characters)",
    )

    # JWT Configuration
    access_token_expire_minutes: int = Field(
        default=15,
        description="Access token expiration time in minutes",
        ge=1,
    )
    refresh_token_expire_days: int = Field(
        default=30,
        description="Refresh token expiration time in days",
        ge=1,
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )

    # TOTP Configuration
    totp_issuer_name: str = Field(
        default="MCP Auth Service",
        description="Issuer name displayed in authenticator apps",
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )
    port: int = Field(
        default=8000,
        description="Server port",
        ge=1,
        le=65535,
    )

    # CORS Configuration
    cors_origins: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that secret key is sufficiently long."""
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def access_token_expire_seconds(self) -> int:
        """Get access token expiration in seconds."""
        return self.access_token_expire_minutes * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        """Get refresh token expiration in seconds."""
        return self.refresh_token_expire_days * 24 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Convenience instance for easy imports
settings = get_settings()
