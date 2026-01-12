"""Tenant model for multi-tenant authentication."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(Base):
    """
    Tenant model for storing tenant organization information.

    In this multi-tenant authentication system, tenants are identified by
    email addresses and have their own password for authentication. When
    a user logs in with a tenant email + password, the system either
    authenticates the existing tenant or creates a new one.

    Attributes:
        id: Primary key
        email: Tenant's email address (globally unique, indexed)
        tenant_name: Tenant's organization name (optional)
        password_hash: Bcrypt hashed password for tenant authentication
        is_active: Whether the tenant account is active
        created_at: Timestamp when tenant was created
        updated_at: Timestamp when tenant was last updated
        users: Relationship to User model (one tenant has many users)
    """

    __tablename__ = "tenants"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Tenant Credentials
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    tenant_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Account Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of Tenant."""
        return f"<Tenant(id={self.id}, name='{self.tenant_name}', email='{self.email}', is_active={self.is_active})>"