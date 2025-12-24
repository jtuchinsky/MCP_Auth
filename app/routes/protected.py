"""Protected routes requiring authentication."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
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

    This is a placeholder endpoint for future profile update functionality.
    Currently returns the user without making any changes.

    Args:
        profile_data: Profile update data (email, password, is_active)
        user: Current authenticated user (injected by dependency)
        db: Database session

    Returns:
        UserResponse with updated user data

    Note:
        This is a placeholder implementation. Full profile update logic
        should be implemented in a future iteration.
    """
    # TODO: Implement profile update logic
    # For now, just return the current user
    # Future implementation should:
    # - Validate email uniqueness if email is being changed
    # - Hash password if password is being changed
    # - Update user fields in database
    # - Handle is_active changes appropriately

    return UserResponse.model_validate(user)