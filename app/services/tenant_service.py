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
    tenant_name: str | None = None,
) -> tuple[Tenant, User, bool]:
    """
    Authenticate tenant by email + password, or create new tenant if doesn't exist.

    This is the core tenant-based authentication flow:
    1. Look up tenant by email (case-insensitive)
    2. If NOT found:
       - Create tenant with email + password_hash + tenant_name
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
        tenant_name: Tenant's organization name (optional)

    Returns:
        Tuple of (tenant, owner_user, is_new_tenant)
        - tenant: Tenant instance
        - owner_user: User instance with OWNER role
        - is_new_tenant: True if tenant was just created, False if existing

    Raises:
        AuthenticationError: If tenant exists but password is invalid or tenant/user is inactive

    Example:
        >>> tenant, owner, is_new = authenticate_or_create_tenant(db, "company@example.com", "secret", "Acme Corp")
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
            tenant_name=tenant_name,
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
    tenant_name: str | None = None,
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
        tenant_name: Tenant's organization name (optional)
        username: Owner's username, defaults to email if None

    Returns:
        Tuple of (tenant, owner_user)

    Example:
        >>> tenant, owner = create_tenant_with_owner(db, "company@example.com", "secret", "Acme Corp")
        >>> print(f"Created tenant {tenant.id} with owner {owner.username}")
    """
    # Hash password once for both tenant and owner
    password_hash = hash_password(password)

    # Create tenant
    tenant = tenant_repository.create(
        db=db,
        email=email,
        password_hash=password_hash,
        tenant_name=tenant_name,
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


def update_tenant_with_cascade(
    db: Session,
    tenant_id: int,
    tenant_name: str | None = None,
) -> tuple[Tenant, int]:
    """
    Update tenant information and cascade tenant_name to all users.

    This function performs a coordinated update:
    1. Updates the tenant's tenant_name
    2. Cascades the tenant_name to all users in the tenant (denormalized field)
    3. Returns both the updated tenant and count of affected users

    Transaction Safety: If tenant update fails, user updates are not attempted.
    If user updates fail, changes are rolled back.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        tenant_name: New tenant name (optional)

    Returns:
        Tuple of (updated_tenant, users_affected_count)

    Raises:
        ValueError: If tenant not found
        SQLAlchemyError: If database update fails

    Example:
        >>> tenant, count = update_tenant_with_cascade(db, 1, "New Company Name")
        >>> print(f"Updated tenant and {count} users")
    """
    from sqlalchemy.exc import SQLAlchemyError

    try:
        # Update tenant first
        updated_tenant = tenant_repository.update(
            db=db,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
        )

        if not updated_tenant:
            raise ValueError(f"Tenant with id {tenant_id} not found")

        # Cascade tenant_name to all users
        users_affected = 0
        if tenant_name is not None:
            users_affected = user_repository.bulk_update_tenant_name(
                db=db,
                tenant_id=tenant_id,
                new_tenant_name=tenant_name,
            )

        return updated_tenant, users_affected

    except SQLAlchemyError as e:
        db.rollback()
        raise


def update_tenant_status_with_cascade(
    db: Session,
    tenant_id: int,
    is_active: bool,
) -> tuple[Tenant, int]:
    """
    Update tenant status and cascade to all users.

    This function performs a coordinated status update:
    1. Updates the tenant's is_active status
    2. Cascades the same is_active status to ALL users in the tenant
    3. Returns both the updated tenant and count of affected users

    **Important**: This ensures tenant and user statuses are synchronized.
    When a tenant is deactivated, all users are automatically deactivated.
    When a tenant is reactivated, all users are automatically reactivated.

    Transaction Safety: All updates are performed in a single transaction.
    If any operation fails, all changes are rolled back.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        is_active: New active status (True = active, False = inactive)

    Returns:
        Tuple of (updated_tenant, users_affected_count)

    Raises:
        ValueError: If tenant not found
        SQLAlchemyError: If database update fails

    Example:
        >>> tenant, count = update_tenant_status_with_cascade(db, 1, False)
        >>> print(f"Deactivated tenant and {count} users")
    """
    from sqlalchemy.exc import SQLAlchemyError

    try:
        # Update tenant status first
        updated_tenant = tenant_repository.update_status(
            db=db,
            tenant_id=tenant_id,
            is_active=is_active,
        )

        if not updated_tenant:
            raise ValueError(f"Tenant with id {tenant_id} not found")

        # Cascade status to all users
        users_affected = user_repository.bulk_update_user_status(
            db=db,
            tenant_id=tenant_id,
            is_active=is_active,
        )

        return updated_tenant, users_affected

    except SQLAlchemyError as e:
        db.rollback()
        raise


def get_cascade_impact(db: Session, tenant_id: int) -> dict:
    """
    Get information about how many users will be affected by a cascade operation.

    This is a read-only function to provide impact analysis before performing
    cascade updates. Useful for UI confirmations and audit logging.

    Args:
        db: Database session
        tenant_id: Tenant's ID

    Returns:
        Dictionary with impact information:
        - total_users: Total number of users in tenant
        - active_users: Number of active users
        - inactive_users: Number of inactive users

    Example:
        >>> impact = get_cascade_impact(db, tenant_id=1)
        >>> print(f"This will affect {impact['total_users']} users")
    """
    total = user_repository.count_affected_users(db, tenant_id)
    active = user_repository.count_tenant_users(db, tenant_id)  # Already exists - counts active only
    inactive = total - active

    return {
        "total_users": total,
        "active_users": active,
        "inactive_users": inactive,
    }