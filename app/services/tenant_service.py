"""Tenant service for tenant authentication and management."""

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import hash_password, verify_password
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories import tenant_repository, user_repository


def authenticate_or_create_tenant(
    db: Session,
    tenant_email: str,
    password: str,
) -> tuple[Tenant, User, bool]:
    """
    Authenticate tenant by email + password, or create new tenant if doesn't exist.

    This is the core tenant-based authentication flow:
    1. Look up tenant by email (case-insensitive)
    2. If NOT found:
       - Create tenant with email + password_hash
       - Create owner user (username=email, email=email, password_hash, role=OWNER)
       - Return (tenant, owner, True) to indicate new tenant
    3. If found:
       - Verify password
       - Get owner user (first user with role=OWNER)
       - Return (tenant, owner, False) to indicate existing tenant

    Args:
        db: Database session
        tenant_email: Tenant's email address
        password: Plain text password

    Returns:
        Tuple of (tenant, owner_user, is_new_tenant)
        - tenant: Tenant instance
        - owner_user: User instance with OWNER role
        - is_new_tenant: True if tenant was just created, False if existing

    Raises:
        AuthenticationError: If tenant exists but password is invalid or tenant/user is inactive

    Example:
        >>> tenant, owner, is_new = authenticate_or_create_tenant(db, "company@example.com", "secret")
        >>> if is_new:
        ...     print(f"Created new tenant: {tenant.email}")
        ... else:
        ...     print(f"Authenticated existing tenant: {tenant.email}")
    """
    # Look up tenant by email (case-insensitive)
    tenant = tenant_repository.get_by_email(db, tenant_email)

    if not tenant:
        # Tenant doesn't exist - create new tenant + owner user
        tenant, owner = create_tenant_with_owner(
            db=db,
            email=tenant_email,
            password=password,
        )
        return tenant, owner, True

    # Tenant exists - verify password and get owner
    if not verify_password(password, tenant.password_hash):
        raise AuthenticationError("Invalid email or password")

    # Check if tenant is active
    if not tenant.is_active:
        raise AuthenticationError("Tenant account is disabled")

    # Get owner user
    owner = user_repository.get_tenant_owner(db, tenant.id)
    if not owner:
        raise AuthenticationError("Tenant owner not found")

    # Check if owner is active
    if not owner.is_active:
        raise AuthenticationError("Tenant owner account is disabled")

    return tenant, owner, False


def create_tenant_with_owner(
    db: Session,
    email: str,
    password: str,
    username: str | None = None,
) -> tuple[Tenant, User]:
    """
    Create new tenant and owner user.

    The owner user will have:
    - username = email (or provided username)
    - email = same as tenant email
    - password = same as tenant password
    - role = OWNER

    Args:
        db: Database session
        email: Tenant's email address (globally unique)
        password: Plain text password
        username: Owner's username, defaults to email if None

    Returns:
        Tuple of (tenant, owner_user)

    Example:
        >>> tenant, owner = create_tenant_with_owner(db, "company@example.com", "secret")
        >>> print(f"Created tenant {tenant.id} with owner {owner.username}")
    """
    # Hash password once for both tenant and owner
    password_hash = hash_password(password)

    # Create tenant
    tenant = tenant_repository.create(
        db=db,
        email=email,
        password_hash=password_hash,
    )

    # Create owner user
    # Username defaults to email if not provided
    owner_username = username if username else email.lower()

    owner = user_repository.create(
        db=db,
        tenant_id=tenant.id,
        username=owner_username,
        email=email.lower(),  # Normalize email to lowercase
        password_hash=password_hash,  # Same password as tenant
        role="OWNER",
    )

    return tenant, owner