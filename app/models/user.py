"""User model for authentication and user management."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.token import RefreshToken


class User(Base):
    """
    User model for storing user account information.

    In the multi-tenant authentication system, users belong to tenants
    and are identified by their username within a tenant. Each user has
    a globally unique email for notifications and invitations.

    Attributes:
        id: Primary key (global auto-increment)
        tenant_id: Foreign key to tenant
        username: User's username (unique per tenant, indexed)
        email: User's email address (globally unique, indexed)
        password_hash: Bcrypt hashed password
        role: User's role in tenant (OWNER, ADMIN, MEMBER)
        totp_secret: TOTP secret for 2FA (nullable)
        is_totp_enabled: Whether 2FA is enabled for this user
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        is_active: Whether the user account is active
        tenant: Relationship to Tenant model
        refresh_tokens: Relationship to user's refresh tokens
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Tenant Association
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User Identifiers
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # User Credentials
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Role-Based Access Control
    role: Mapped[str] = mapped_column(
        String(50),
        default="MEMBER",
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
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_tenant_username"),
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, tenant_id={self.tenant_id}, username='{self.username}', email='{self.email}', role='{self.role}', is_active={self.is_active})>"