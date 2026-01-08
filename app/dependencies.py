"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError, TOTPError
from app.database import get_db
from app.models.user import User
from app.repositories import tenant_repository, user_repository
from app.services import jwt_service


async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token with tenant isolation.

    Validates:
    - JWT signature and expiration
    - User exists and is active
    - Tenant exists and is active
    - tenant_id in JWT matches user's tenant_id (tenant isolation)

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Authenticated User instance

    Raises:
        AuthenticationError: If token is invalid, user not found, or validation fails
        AuthorizationError: If tenant_id mismatch detected (security violation)

    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(user: User = Depends(get_current_user)):
        >>>     return {"user_id": user.id, "tenant_id": user.tenant_id}
    """
    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header format")

    token = authorization[7:]  # Remove "Bearer " prefix

    # Decode and validate JWT
    payload = jwt_service.decode_access_token(token)

    # Extract user ID from token payload
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Invalid token payload")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid user ID in token")

    # Extract tenant_id and role from token payload
    tenant_id_str = payload.get("tenant_id")
    if not tenant_id_str:
        raise AuthenticationError("Missing tenant_id in token")

    try:
        token_tenant_id = int(tenant_id_str)
    except ValueError:
        raise AuthenticationError("Invalid tenant_id in token")

    # Fetch user from database
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User not found")

    # Validate tenant_id matches (tenant isolation)
    if user.tenant_id != token_tenant_id:
        raise AuthorizationError(
            "Tenant ID mismatch - possible token tampering or cross-tenant access attempt"
        )

    # Check if user account is active
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # Fetch and validate tenant
    tenant = tenant_repository.get_by_id(db, user.tenant_id)
    if not tenant:
        raise AuthenticationError("Tenant not found")

    if not tenant.is_active:
        raise AuthenticationError("Tenant account is disabled")

    return user


async def require_totp_disabled(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require that user does NOT have TOTP enabled.

    Used for TOTP setup endpoint to prevent re-enabling.

    Args:
        user: Current authenticated user

    Returns:
        User instance if TOTP is not enabled

    Raises:
        TOTPError: If TOTP is already enabled

    Example:
        >>> @app.post("/auth/totp/setup")
        >>> async def totp_setup(user: User = Depends(require_totp_disabled)):
        >>>     return setup_totp_for_user(user)
    """
    if user.is_totp_enabled:
        raise TOTPError("TOTP is already enabled for this user")

    return user


async def require_owner(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require that the authenticated user has OWNER role.

    Used for tenant management endpoints that only owners can access.

    Args:
        user: Current authenticated user

    Returns:
        User instance if role is OWNER

    Raises:
        AuthorizationError: If user does not have OWNER role

    Example:
        >>> @app.post("/api/tenants/invite")
        >>> async def invite_user(user: User = Depends(require_owner)):
        >>>     # Only OWNER can invite new users
        >>>     return invite_new_user(user.tenant_id)
    """
    if user.role != "OWNER":
        raise AuthorizationError(
            f"This endpoint requires OWNER role. Your role: {user.role}"
        )

    return user


async def require_admin_or_owner(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require that the authenticated user has ADMIN or OWNER role.

    Used for administrative endpoints accessible by both admins and owners.

    Args:
        user: Current authenticated user

    Returns:
        User instance if role is ADMIN or OWNER

    Raises:
        AuthorizationError: If user does not have ADMIN or OWNER role

    Example:
        >>> @app.get("/api/tenants/users")
        >>> async def list_tenant_users(user: User = Depends(require_admin_or_owner)):
        >>>     # ADMIN and OWNER can view tenant users
        >>>     return get_users_in_tenant(user.tenant_id)
    """
    if user.role not in ["ADMIN", "OWNER"]:
        raise AuthorizationError(
            f"This endpoint requires ADMIN or OWNER role. Your role: {user.role}"
        )

    return user