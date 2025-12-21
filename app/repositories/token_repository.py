"""Token repository for database operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.token import RefreshToken


def create_refresh_token(
    db: Session,
    user_id: int,
    token: str,
    expires_at: datetime,
    client_id: str | None = None,
    scope: str | None = None,
) -> RefreshToken:
    """
    Create a new refresh token.

    Args:
        db: Database session
        user_id: User's ID
        token: Refresh token string
        expires_at: Token expiration datetime
        client_id: Optional OAuth2 client ID
        scope: Optional OAuth2 scope

    Returns:
        Created RefreshToken instance

    Example:
        >>> from datetime import datetime, timedelta, timezone
        >>> expires = datetime.now(timezone.utc) + timedelta(days=7)
        >>> token = create_refresh_token(db, 1, "token123", expires)
        >>> print(token.user_id)
        1
    """
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        client_id=client_id,
        scope=scope,
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def get_by_token(db: Session, token: str) -> RefreshToken | None:
    """
    Get a refresh token by its token string.

    Args:
        db: Database session
        token: Refresh token string

    Returns:
        RefreshToken instance if found, None otherwise

    Example:
        >>> token = get_by_token(db, "token123")
        >>> if token:
        ...     print(f"Found token for user: {token.user_id}")
    """
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def revoke_token(db: Session, token: str) -> None:
    """
    Revoke a refresh token.

    Args:
        db: Database session
        token: Refresh token string to revoke

    Raises:
        ValueError: If token not found

    Example:
        >>> revoke_token(db, "token123")
    """
    refresh_token = get_by_token(db, token)
    if not refresh_token:
        raise ValueError(f"Token not found")

    refresh_token.is_revoked = True
    db.commit()


def revoke_all_user_tokens(db: Session, user_id: int) -> None:
    """
    Revoke all refresh tokens for a user.

    Args:
        db: Database session
        user_id: User's ID

    Example:
        >>> revoke_all_user_tokens(db, 1)
    """
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
        {"is_revoked": True}
    )
    db.commit()