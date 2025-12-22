"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, TOTPError
from app.database import get_db
from app.models.user import User
from app.repositories import user_repository
from app.services import jwt_service


async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Authenticated User instance

    Raises:
        AuthenticationError: If token is invalid or user not found

    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(user: User = Depends(get_current_user)):
        >>>     return {"user_id": user.id}
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

    # Fetch user from database
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User not found")

    # Check if user account is active
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

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