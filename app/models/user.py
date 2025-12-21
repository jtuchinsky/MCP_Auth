"""User model for authentication and user management."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.token import RefreshToken


class User(Base):
    """
    User model for storing user account information.

    Attributes:
        id: Primary key
        email: User's email address (unique, indexed)
        password_hash: Bcrypt hashed password
        totp_secret: TOTP secret for 2FA (nullable)
        is_totp_enabled: Whether 2FA is enabled for this user
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        is_active: Whether the user account is active
        refresh_tokens: Relationship to user's refresh tokens
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User Credentials
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # TOTP / 2FA Fields
    totp_secret: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        default=None,
    )
    is_totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Account Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"