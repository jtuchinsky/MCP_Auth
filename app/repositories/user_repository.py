"""User repository for database operations."""

from sqlalchemy.orm import Session

from app.models.user import User


def create(
    db: Session,
    tenant_id: int,
    username: str,
    email: str,
    password_hash: str,
    role: str = "MEMBER",
) -> User:
    """
    Create a new user within a tenant.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        username: User's username (unique per tenant)
        email: User's email address (globally unique)
        password_hash: Hashed password
        role: User's role (OWNER, ADMIN, MEMBER). Defaults to MEMBER.

    Returns:
        Created User instance

    Example:
        >>> user = create(db, tenant_id=1, username="alice", email="alice@example.com", password_hash="hashed", role="MEMBER")
        >>> print(user.username)
        alice
    """
    user = User(
        tenant_id=tenant_id,
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_by_id(db: Session, user_id: int) -> User | None:
    """
    Get a user by their ID.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        User instance if found, None otherwise

    Example:
        >>> user = get_by_id(db, 1)
        >>> if user:
        ...     print(user.email)
    """
    return db.query(User).filter(User.id == user_id).first()


def get_by_email(db: Session, email: str) -> User | None:
    """
    Get a user by their email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User instance if found, None otherwise

    Example:
        >>> user = get_by_email(db, "user@example.com")
        >>> if user:
        ...     print(f"Found user: {user.id}")
    """
    return db.query(User).filter(User.email == email).first()


def update_totp_secret(db: Session, user_id: int, secret: str) -> User:
    """
    Update a user's TOTP secret.

    Args:
        db: Database session
        user_id: User's ID
        secret: TOTP secret (base32 encoded)

    Returns:
        Updated User instance

    Raises:
        ValueError: If user not found

    Example:
        >>> user = update_totp_secret(db, 1, "JBSWY3DPEHPK3PXP")
        >>> print(user.totp_secret)
        JBSWY3DPEHPK3PXP
    """
    user = get_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")

    user.totp_secret = secret
    db.commit()
    db.refresh(user)
    return user


def enable_totp(db: Session, user_id: int) -> User:
    """
    Enable TOTP (2FA) for a user.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        Updated User instance

    Raises:
        ValueError: If user not found

    Example:
        >>> user = enable_totp(db, 1)
        >>> print(user.is_totp_enabled)
        True
    """
    user = get_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")

    user.is_totp_enabled = True
    db.commit()
    db.refresh(user)
    return user


def update_profile(
    db: Session,
    user_id: int,
    email: str | None = None,
    password_hash: str | None = None,
) -> User:
    """
    Update a user's profile information.

    Args:
        db: Database session
        user_id: User's ID
        email: New email address (optional)
        password_hash: New hashed password (optional)

    Returns:
        Updated User instance

    Raises:
        ValueError: If user not found or email already exists

    Example:
        >>> user = update_profile(db, 1, email="newemail@example.com")
        >>> print(user.email)
        newemail@example.com
    """
    user = get_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")

    # Update email if provided
    if email is not None:
        # Check if email is already taken by another user
        existing_user = get_by_email(db, email)
        if existing_user and existing_user.id != user_id:
            raise ValueError(f"User with email {email} already exists")
        user.email = email

    # Update password if provided
    if password_hash is not None:
        user.password_hash = password_hash

    db.commit()
    db.refresh(user)
    return user


def get_by_tenant_and_username(db: Session, tenant_id: int, username: str) -> User | None:
    """
    Get user by tenant ID and username.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        username: User's username

    Returns:
        User instance if found, None otherwise

    Example:
        >>> user = get_by_tenant_and_username(db, tenant_id=1, username="alice")
        >>> if user:
        ...     print(f"Found user {user.email} in tenant {user.tenant_id}")
    """
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.username == username)
        .first()
    )


def get_tenant_owner(db: Session, tenant_id: int) -> User | None:
    """
    Get the owner (first user with OWNER role) of a tenant.

    Args:
        db: Database session
        tenant_id: Tenant's ID

    Returns:
        User instance with OWNER role, or None if not found

    Example:
        >>> owner = get_tenant_owner(db, tenant_id=1)
        >>> if owner:
        ...     print(f"Owner: {owner.email}")
    """
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.role == "OWNER")
        .first()
    )


def list_by_tenant(db: Session, tenant_id: int, skip: int = 0, limit: int = 100) -> list[User]:
    """
    List all users in a tenant with pagination.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of User instances in the tenant

    Example:
        >>> users = list_by_tenant(db, tenant_id=1, skip=0, limit=10)
        >>> for user in users:
        ...     print(f"{user.username} - {user.role}")
    """
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_tenant_users(db: Session, tenant_id: int) -> int:
    """
    Count active users in a tenant.

    Args:
        db: Database session
        tenant_id: Tenant's ID

    Returns:
        Number of active users in the tenant

    Example:
        >>> count = count_tenant_users(db, tenant_id=1)
        >>> print(f"Tenant has {count} users")
    """
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.is_active == True)
        .count()
    )


def bulk_update_tenant_name(db: Session, tenant_id: int, new_tenant_name: str | None) -> int:
    """
    Update tenant_name for all users in a tenant.

    This is a bulk update operation that updates the denormalized tenant_name
    field for all users belonging to a specific tenant. Used when the tenant's
    organization name changes to maintain data consistency.

    Uses SQLAlchemy's bulk UPDATE for efficiency (single SQL statement).

    Args:
        db: Database session
        tenant_id: Tenant's ID
        new_tenant_name: New tenant name to set for all users

    Returns:
        Number of users updated

    Example:
        >>> count = bulk_update_tenant_name(db, tenant_id=1, new_tenant_name="Acme Corp")
        >>> print(f"Updated {count} users")
    """
    result = db.query(User).filter(User.tenant_id == tenant_id).update(
        {"tenant_name": new_tenant_name}
    )
    db.commit()
    return result


def bulk_update_user_status(db: Session, tenant_id: int, is_active: bool) -> int:
    """
    Update is_active status for all users in a tenant.

    This is a bulk update operation that activates or deactivates all users
    belonging to a specific tenant. Used when the tenant is activated or
    deactivated to cascade the status change to all users.

    Uses SQLAlchemy's bulk UPDATE for efficiency (single SQL statement).

    Args:
        db: Database session
        tenant_id: Tenant's ID
        is_active: New active status (True = active, False = inactive)

    Returns:
        Number of users updated

    Example:
        >>> count = bulk_update_user_status(db, tenant_id=1, is_active=False)
        >>> print(f"Deactivated {count} users")
    """
    result = db.query(User).filter(User.tenant_id == tenant_id).update(
        {"is_active": is_active}
    )
    db.commit()
    return result


def count_affected_users(db: Session, tenant_id: int) -> int:
    """
    Count how many users would be affected by a bulk update operation.

    Used before performing cascade operations to determine impact and
    provide feedback about how many accounts will be affected.

    Args:
        db: Database session
        tenant_id: Tenant's ID

    Returns:
        Number of users in the tenant (both active and inactive)

    Example:
        >>> count = count_affected_users(db, tenant_id=1)
        >>> print(f"This operation will affect {count} users")
    """
    return db.query(User).filter(User.tenant_id == tenant_id).count()