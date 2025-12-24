"""Protected routes requiring authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/api/protected", tags=["Protected"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the authenticated user's profile information.",
)
async def get_me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's information.

    Requires valid JWT access token in Authorization header.

    Args:
        user: Current authenticated user (injected by dependency)

    Returns:
        UserResponse with user profile data

    Example:
        >>> GET /api/protected/me
        >>> Authorization: Bearer <access_token>
        >>> {
        >>>   "id": 1,
        >>>   "email": "user@example.com",
        >>>   "is_totp_enabled": false,
        >>>   "is_active": true,
        >>>   "created_at": "2024-01-01T00:00:00",
        >>>   "updated_at": "2024-01-01T00:00:00"
        >>> }
    """
    return UserResponse.model_validate(user)


@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the authenticated user's profile information (placeholder).",
)
async def update_profile(
    profile_data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile.

    Allows updating email and/or password. Email must be unique.

    Args:
        profile_data: Profile update data (email, password)
        user: Current authenticated user (injected by dependency)
        db: Database session

    Returns:
        UserResponse with updated user data

    Raises:
        HTTPException 400: If email already exists
    """
    # Hash password if provided
    password_hash = None
    if profile_data.password is not None:
        password_hash = security.hash_password(profile_data.password)

    try:
        # Update user profile
        updated_user = user_repository.update_profile(
            db=db,
            user_id=user.id,
            email=profile_data.email,
            password_hash=password_hash,
        )
        return UserResponse.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )