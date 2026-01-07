"""JWT service for creating and validating tokens."""

import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.core.exceptions import AuthenticationError


def create_access_token(
    user_id: int,
    email: str,
    tenant_id: int,
    role: str,
    scopes: list[str] | None = None,
    audience: str | None = None,
) -> str:
    """
    Create a JWT access token with tenant and role information.

    Args:
        user_id: User's ID
        email: User's email address
        tenant_id: Tenant ID for multi-tenant isolation (required)
        role: User's role (OWNER, ADMIN, MEMBER)
        scopes: Optional list of OAuth2 scopes
        audience: Optional OAuth2 audience (resource indicator)

    Returns:
        Signed JWT token string

    Example:
        >>> token = create_access_token(1, "user@example.com", 2, "OWNER", ["read", "write"])
        >>> print(len(token) > 0)
        True
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.access_token_expire_seconds)

    payload = {
        "sub": str(user_id),
        "email": email,
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expires_at,
        "iat": now,
        "scopes": scopes or [],
    }

    if audience:
        payload["aud"] = audience

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


def create_refresh_token() -> str:
    """
    Create a random refresh token.

    Returns:
        URL-safe random token string (32 bytes)

    Example:
        >>> token1 = create_refresh_token()
        >>> token2 = create_refresh_token()
        >>> print(token1 != token2)
        True
    """
    return secrets.token_urlsafe(32)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload as dictionary

    Raises:
        AuthenticationError: If token is invalid or expired

    Example:
        >>> token = create_access_token(1, "user@example.com")
        >>> payload = decode_access_token(token)
        >>> print(payload["email"])
        user@example.com
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},  # Don't enforce audience validation at decode time
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")