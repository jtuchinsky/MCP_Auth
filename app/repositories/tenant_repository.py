"""Repository for tenant database operations."""

from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def create(db: Session, email: str, password_hash: str, tenant_name: str | None = None) -> Tenant:
    """
    Create a new tenant.

    Args:
        db: Database session
        email: Tenant's email address (globally unique)
        password_hash: Bcrypt hashed password
        tenant_name: Tenant's organization name (optional)

    Returns:
        Created Tenant instance

    Example:
        >>> tenant = create(db, "company@example.com", hashed_password, "Acme Corp")
        >>> print(tenant.email)
        company@example.com
    """
    tenant = Tenant(
        email=email.lower(),  # Normalize email to lowercase
        tenant_name=tenant_name,
        password_hash=password_hash,
        is_active=True,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def get_by_id(db: Session, tenant_id: int) -> Tenant | None:
    """
    Get tenant by ID.

    Args:
        db: Database session
        tenant_id: Tenant's ID

    Returns:
        Tenant instance or None if not found

    Example:
        >>> tenant = get_by_id(db, 1)
        >>> if tenant:
        ...     print(tenant.email)
    """
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_by_email(db: Session, email: str) -> Tenant | None:
    """
    Get tenant by email address (case-insensitive).

    Args:
        db: Database session
        email: Tenant's email address

    Returns:
        Tenant instance or None if not found

    Example:
        >>> tenant = get_by_email(db, "Company@Example.com")
        >>> if tenant:
        ...     print(tenant.email)  # Will be lowercase: company@example.com
    """
    return db.query(Tenant).filter(Tenant.email == email.lower()).first()


def update_status(db: Session, tenant_id: int, is_active: bool) -> Tenant | None:
    """
    Update tenant's active status.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        is_active: New active status (True = active, False = disabled)

    Returns:
        Updated Tenant instance or None if not found

    Example:
        >>> tenant = update_status(db, 1, False)  # Deactivate tenant
        >>> if tenant:
        ...     print(tenant.is_active)  # False
    """
    tenant = get_by_id(db, tenant_id)
    if not tenant:
        return None

    tenant.is_active = is_active
    db.commit()
    db.refresh(tenant)
    return tenant


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[Tenant]:
    """
    Get all tenants with pagination.

    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List of Tenant instances

    Example:
        >>> tenants = get_all(db, skip=0, limit=10)
        >>> for tenant in tenants:
        ...     print(tenant.email)
    """
    return db.query(Tenant).offset(skip).limit(limit).all()


def count_all(db: Session) -> int:
    """
    Count total number of tenants.

    Args:
        db: Database session

    Returns:
        Total count of tenants

    Example:
        >>> total = count_all(db)
        >>> print(f"Total tenants: {total}")
    """
    return db.query(Tenant).count()


def update(db: Session, tenant_id: int, tenant_name: str | None = None) -> Tenant | None:
    """
    Update tenant information.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        tenant_name: New tenant name (optional, if provided will update the name)

    Returns:
        Updated Tenant instance or None if not found

    Example:
        >>> tenant = update(db, 1, "New Company Name")
        >>> if tenant:
        ...     print(f"Updated tenant: {tenant.tenant_name}")
    """
    tenant = get_by_id(db, tenant_id)
    if not tenant:
        return None

    # Only update fields that are provided (not None)
    if tenant_name is not None:
        tenant.tenant_name = tenant_name

    db.commit()
    db.refresh(tenant)
    return tenant