"""RefreshToken model for managing user refresh tokens."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    """
    RefreshToken model for storing user refresh tokens.

    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        token: The refresh token string (unique, indexed)
        client_id: Optional client identifier
        scope: Optional OAuth2 scopes
        is_revoked: Whether the token has been revoked
        expires_at: When the token expires
        created_at: When the token was created
        user: Relationship to the User who owns this token
    """

    __tablename__ = "refresh_tokens"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key to User
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token Information
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # OAuth2 Fields
    client_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    scope: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    # Token Status
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_tokens",
    )

    def __repr__(self) -> str:
        """String representation of RefreshToken."""
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"