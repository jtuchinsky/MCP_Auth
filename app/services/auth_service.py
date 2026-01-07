"""Authentication service for user registration and login."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import token_repository, user_repository
from app.services import jwt_service


def register_user(
    db: Session,
    tenant_id: int,
    username: str,
    email: str,
    password: str,
    role: str = "MEMBER",
) -> User:
    """
    Register a new user within a tenant.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        username: User's username (unique per tenant)
        email: User's email address (globally unique)
        password: Plain text password
        role: User's role (OWNER, ADMIN, MEMBER). Defaults to MEMBER.

    Returns:
        Created User instance

    Raises:
        ValueError: If user with email already exists or username is taken in tenant

    Example:
        >>> user = register_user(db, 1, "alice", "alice@example.com", "password", "MEMBER")
        >>> print(user.username)
        alice
    """
    # Check if user with email already exists (globally unique)
    existing_user = user_repository.get_by_email(db, email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")

    # Check if username is taken in this tenant
    existing_username = user_repository.get_by_tenant_and_username(db, tenant_id, username)
    if existing_username:
        raise ValueError(f"Username {username} is already taken in this tenant")

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user = user_repository.create(
        db=db,
        tenant_id=tenant_id,
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
    )

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate a user with email and password (legacy method).

    NOTE: This method authenticates by email only. For tenant-based authentication,
    use authenticate_tenant_user() instead.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password

    Returns:
        User instance if authentication succeeds

    Raises:
        AuthenticationError: If authentication fails

    Example:
        >>> user = authenticate_user(db, "user@example.com", "password")
        >>> print(user.email)
        user@example.com
    """
    # Get user by email
    user = user_repository.get_by_email(db, email)
    if not user:
        raise AuthenticationError("Invalid email or password")

    # Verify password
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    # Check if user is active
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # Check if tenant is active
    if not user.tenant.is_active:
        raise AuthenticationError("Tenant account is disabled")

    return user


def authenticate_tenant_user(
    db: Session,
    tenant_id: int,
    username: str,
    password: str,
) -> User:
    """
    Authenticate a user within a tenant by username and password.

    This is used for multi-user tenants where additional users (beyond the owner)
    log in using their username within the tenant.

    Args:
        db: Database session
        tenant_id: Tenant's ID
        username: User's username
        password: Plain text password

    Returns:
        User instance if authentication succeeds

    Raises:
        AuthenticationError: If authentication fails

    Example:
        >>> user = authenticate_tenant_user(db, 1, "alice", "password")
        >>> print(user.username)
        alice
    """
    # Get user by tenant and username
    user = user_repository.get_by_tenant_and_username(db, tenant_id, username)
    if not user:
        raise AuthenticationError("Invalid username or password")

    # Verify password
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid username or password")

    # Check if user is active
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # Check if tenant is active
    if not user.tenant.is_active:
        raise AuthenticationError("Tenant account is disabled")

    return user


def create_tokens(
    db: Session,
    user: User,
    client_id: str | None = None,
    scope: str | None = None,
) -> tuple[str, str]:
    """
    Create access and refresh tokens for a user.

    The access token includes tenant_id and role claims for multi-tenant
    authorization and role-based access control.

    Args:
        db: Database session
        user: User instance (must have tenant_id and role attributes)
        client_id: Optional OAuth2 client ID
        scope: Optional OAuth2 scope

    Returns:
        Tuple of (access_token, refresh_token)

    Example:
        >>> access, refresh = create_tokens(db, user, "web_app", "read write")
        >>> print(len(access) > 0 and len(refresh) > 0)
        True
    """
    # Create access token with tenant and role information
    scopes = scope.split() if scope else []
    access_token = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        role=user.role,
        scopes=scopes,
    )

    # Create refresh token
    refresh_token_string = jwt_service.create_refresh_token()

    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.refresh_token_expire_seconds
    )

    # Store refresh token in database
    token_repository.create_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token_string,
        expires_at=expires_at,
        client_id=client_id,
        scope=scope,
    )

    return access_token, refresh_token_string


def refresh_access_token(
    db: Session, refresh_token: str
) -> tuple[str, str]:
    """
    Refresh an access token using a refresh token.

    Args:
        db: Database session
        refresh_token: Refresh token string

    Returns:
        Tuple of (new_access_token, new_refresh_token)

    Raises:
        AuthenticationError: If refresh token is invalid or expired

    Example:
        >>> new_access, new_refresh = refresh_access_token(db, old_refresh_token)
        >>> print(new_access != old_access_token)
        True
    """
    # Get refresh token from database
    token = token_repository.get_by_token(db, refresh_token)
    if not token:
        raise AuthenticationError("Invalid refresh token")

    # Check if token is revoked
    if token.is_revoked:
        raise AuthenticationError("Refresh token has been revoked")

    # Check if token is expired
    now = datetime.now(timezone.utc)
    # SQLite stores datetime without timezone info, so remove timezone for comparison
    expires_at_utc = token.expires_at.replace(tzinfo=timezone.utc) if token.expires_at.tzinfo is None else token.expires_at
    if expires_at_utc < now:
        raise AuthenticationError("Refresh token has expired")

    # Get user
    user = user_repository.get_by_id(db, token.user_id)
    if not user:
        raise AuthenticationError("User not found")

    # Check if user is active
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # Revoke old refresh token
    token_repository.revoke_token(db, refresh_token)

    # Create new tokens
    new_access_token, new_refresh_token = create_tokens(
        db=db,
        user=user,
        client_id=token.client_id,
        scope=token.scope,
    )

    return new_access_token, new_refresh_token