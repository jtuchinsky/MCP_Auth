"""User repository for database operations."""

from sqlalchemy.orm import Session

from app.models.user import User


def create(db: Session, email: str, password_hash: str) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        email: User's email address
        password_hash: Hashed password

    Returns:
        Created User instance

    Example:
        >>> user = create(db, "user@example.com", "hashed_password")
        >>> print(user.email)
        user@example.com
    """
    user = User(
        email=email,
        password_hash=password_hash,
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