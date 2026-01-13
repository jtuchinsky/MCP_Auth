"""Tenant CRUD routes for tenant management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin_or_owner, require_owner
from app.models.user import User
from app.repositories import tenant_repository, user_repository
from app.schemas.tenant import TenantResponse, TenantStatusUpdate, TenantUpdate
from app.schemas.user import UserResponse

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get(
    "/me",
    response_model=TenantResponse,
    summary="Get current user's tenant",
    description="Retrieve information about the authenticated user's tenant. All roles can access.",
)
async def get_my_tenant(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantResponse:
    """
    Get current user's tenant information.

    **Authorization**: Any authenticated user (OWNER, ADMIN, MEMBER)

    Args:
        user: Current authenticated user (from JWT token)
        db: Database session

    Returns:
        TenantResponse with tenant details

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 404: If tenant not found
    """
    tenant = tenant_repository.get_by_id(db, user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse.model_validate(tenant)


@router.put(
    "/me",
    response_model=TenantResponse,
    summary="Update current user's tenant",
    description="Update tenant information (e.g., tenant name). Requires OWNER or ADMIN role.",
)
async def update_my_tenant(
    update_data: TenantUpdate,
    user: User = Depends(require_admin_or_owner),
    db: Session = Depends(get_db),
) -> TenantResponse:
    """
    Update current user's tenant information.

    **Authorization**: OWNER or ADMIN role required

    Args:
        update_data: Tenant update data (tenant_name)
        user: Current authenticated user with OWNER or ADMIN role
        db: Database session

    Returns:
        Updated TenantResponse

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not OWNER or ADMIN
        HTTPException 404: If tenant not found
    """
    # Update tenant
    updated_tenant = tenant_repository.update(
        db=db,
        tenant_id=user.tenant_id,
        tenant_name=update_data.tenant_name,
    )

    if not updated_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse.model_validate(updated_tenant)


@router.patch(
    "/me/status",
    response_model=TenantResponse,
    summary="Update tenant status",
    description="Activate or deactivate the tenant. Requires OWNER role.",
)
async def update_my_tenant_status(
    status_data: TenantStatusUpdate,
    user: User = Depends(require_owner),
    db: Session = Depends(get_db),
) -> TenantResponse:
    """
    Update current user's tenant status (activate/deactivate).

    **Authorization**: OWNER role required

    **Warning**: Deactivating a tenant will prevent all users in the tenant from logging in.

    Args:
        status_data: Status update data (is_active: true/false)
        user: Current authenticated user with OWNER role
        db: Database session

    Returns:
        Updated TenantResponse

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not OWNER
        HTTPException 404: If tenant not found
    """
    # Update tenant status
    updated_tenant = tenant_repository.update_status(
        db=db,
        tenant_id=user.tenant_id,
        is_active=status_data.is_active,
    )

    if not updated_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse.model_validate(updated_tenant)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate (soft delete) tenant",
    description="Soft delete tenant by marking as inactive. Requires OWNER role.",
)
async def delete_my_tenant(
    user: User = Depends(require_owner),
    db: Session = Depends(get_db),
) -> None:
    """
    Soft delete current user's tenant (mark as inactive).

    **Authorization**: OWNER role required

    **Important**: This is a soft delete - the tenant is marked as inactive
    but not removed from the database. All users in this tenant will be
    unable to log in.

    Args:
        user: Current authenticated user with OWNER role
        db: Database session

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not OWNER
        HTTPException 404: If tenant not found
    """
    # Deactivate tenant (soft delete)
    updated_tenant = tenant_repository.update_status(
        db=db,
        tenant_id=user.tenant_id,
        is_active=False,
    )

    if not updated_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Return 204 No Content (no response body)


@router.get(
    "/me/users",
    response_model=list[UserResponse],
    summary="List users in tenant",
    description="Get all users in the current user's tenant. Requires OWNER or ADMIN role.",
)
async def list_tenant_users(
    user: User = Depends(require_admin_or_owner),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    """
    List all users in the current user's tenant.

    **Authorization**: OWNER or ADMIN role required

    Args:
        user: Current authenticated user with OWNER or ADMIN role
        db: Database session

    Returns:
        List of UserResponse objects for all users in the tenant

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not OWNER or ADMIN
    """
    # Get all users in the tenant
    users = user_repository.list_by_tenant(db, user.tenant_id)

    return [UserResponse.model_validate(u) for u in users]