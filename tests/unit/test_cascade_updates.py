"""Unit tests for cascade update functionality."""

import pytest
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.repositories import tenant_repository, user_repository
from app.services import tenant_service


class TestUserRepositoryCascadeMethods:
    """Test bulk update methods in user_repository."""

    def test_bulk_update_tenant_name(self, db_session: Session):
        """Test bulk_update_tenant_name updates all users in a tenant."""
        # Create tenant
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Old Company Name",
        )

        # Create 3 users in the tenant
        user1 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user2",
            email="user2@company.com",
            password_hash="hashed",
            role="ADMIN",
        )
        user3 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user3",
            email="user3@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Bulk update tenant_name
        count = user_repository.bulk_update_tenant_name(
            db=db_session,
            tenant_id=tenant.id,
            new_tenant_name="New Company Name",
        )

        # Verify count
        assert count == 3

        # Verify all users have updated tenant_name
        db_session.refresh(user1)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert user1.tenant_name == "New Company Name"
        assert user2.tenant_name == "New Company Name"
        assert user3.tenant_name == "New Company Name"

    def test_bulk_update_user_status_deactivate(self, db_session: Session):
        """Test bulk_update_user_status deactivates all users in a tenant."""
        # Create tenant
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Company",
        )

        # Create 3 active users
        user1 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user2",
            email="user2@company.com",
            password_hash="hashed",
            role="ADMIN",
        )
        user3 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user3",
            email="user3@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Verify all users start as active
        assert user1.is_active is True
        assert user2.is_active is True
        assert user3.is_active is True

        # Bulk deactivate all users
        count = user_repository.bulk_update_user_status(
            db=db_session,
            tenant_id=tenant.id,
            is_active=False,
        )

        # Verify count
        assert count == 3

        # Verify all users are now inactive
        db_session.refresh(user1)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert user1.is_active is False
        assert user2.is_active is False
        assert user3.is_active is False

    def test_bulk_update_user_status_reactivate(self, db_session: Session):
        """Test bulk_update_user_status reactivates all users in a tenant."""
        # Create tenant
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Company",
        )

        # Create 3 users and manually deactivate them
        user1 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user2",
            email="user2@company.com",
            password_hash="hashed",
            role="ADMIN",
        )
        user3 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user3",
            email="user3@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Deactivate all users first
        user_repository.bulk_update_user_status(db=db_session, tenant_id=tenant.id, is_active=False)
        db_session.refresh(user1)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert user1.is_active is False
        assert user2.is_active is False
        assert user3.is_active is False

        # Reactivate all users
        count = user_repository.bulk_update_user_status(
            db=db_session,
            tenant_id=tenant.id,
            is_active=True,
        )

        # Verify count
        assert count == 3

        # Verify all users are now active again
        db_session.refresh(user1)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert user1.is_active is True
        assert user2.is_active is True
        assert user3.is_active is True

    def test_bulk_update_affects_only_target_tenant(self, db_session: Session):
        """Test bulk updates only affect users in the target tenant."""
        # Create two tenants
        tenant1 = tenant_repository.create(
            db=db_session,
            email="company1@example.com",
            password_hash="hashed",
            tenant_name="Company 1",
        )
        tenant2 = tenant_repository.create(
            db=db_session,
            email="company2@example.com",
            password_hash="hashed",
            tenant_name="Company 2",
        )

        # Create users in tenant 1
        user1_t1 = user_repository.create(
            db=db_session,
            tenant_id=tenant1.id,
            username="user1",
            email="user1@company1.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2_t1 = user_repository.create(
            db=db_session,
            tenant_id=tenant1.id,
            username="user2",
            email="user2@company1.com",
            password_hash="hashed",
            role="ADMIN",
        )

        # Create users in tenant 2
        user1_t2 = user_repository.create(
            db=db_session,
            tenant_id=tenant2.id,
            username="user1",
            email="user1@company2.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2_t2 = user_repository.create(
            db=db_session,
            tenant_id=tenant2.id,
            username="user2",
            email="user2@company2.com",
            password_hash="hashed",
            role="ADMIN",
        )

        # Bulk update tenant 1 only
        count = user_repository.bulk_update_tenant_name(
            db=db_session,
            tenant_id=tenant1.id,
            new_tenant_name="Updated Company 1",
        )

        # Verify only 2 users updated (tenant 1 only)
        assert count == 2

        # Verify tenant 1 users are updated
        db_session.refresh(user1_t1)
        db_session.refresh(user2_t1)
        assert user1_t1.tenant_name == "Updated Company 1"
        assert user2_t1.tenant_name == "Updated Company 1"

        # Verify tenant 2 users are NOT updated
        db_session.refresh(user1_t2)
        db_session.refresh(user2_t2)
        assert user1_t2.tenant_name is None
        assert user2_t2.tenant_name is None

    def test_count_affected_users(self, db_session: Session):
        """Test count_affected_users returns correct count."""
        # Create tenant
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Company",
        )

        # Initially no users
        count = user_repository.count_affected_users(db=db_session, tenant_id=tenant.id)
        assert count == 0

        # Create 3 users
        for i in range(3):
            user_repository.create(
                db=db_session,
                tenant_id=tenant.id,
                username=f"user{i}",
                email=f"user{i}@company.com",
                password_hash="hashed",
                role="MEMBER",
            )

        # Count should now be 3
        count = user_repository.count_affected_users(db=db_session, tenant_id=tenant.id)
        assert count == 3

        # Deactivate users - count should still be 3 (counts all users)
        user_repository.bulk_update_user_status(db=db_session, tenant_id=tenant.id, is_active=False)
        count = user_repository.count_affected_users(db=db_session, tenant_id=tenant.id)
        assert count == 3


class TestTenantServiceCascadeOperations:
    """Test cascade operations in tenant_service."""

    def test_update_tenant_with_cascade_updates_users(self, db_session: Session):
        """Test update_tenant_with_cascade updates both tenant and users."""
        # Create tenant with users
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Old Name",
        )

        user1 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user2",
            email="user2@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Update tenant with cascade
        updated_tenant, users_affected = tenant_service.update_tenant_with_cascade(
            db=db_session,
            tenant_id=tenant.id,
            tenant_name="New Name",
        )

        # Verify tenant updated
        assert updated_tenant.tenant_name == "New Name"
        assert users_affected == 2

        # Verify users updated
        db_session.refresh(user1)
        db_session.refresh(user2)
        assert user1.tenant_name == "New Name"
        assert user2.tenant_name == "New Name"

    def test_update_tenant_status_with_cascade_deactivates_users(self, db_session: Session):
        """Test update_tenant_status_with_cascade deactivates all users."""
        # Create tenant with users
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Company",
        )

        user1 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user2",
            email="user2@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Verify tenant and users start as active
        assert tenant.is_active is True
        assert user1.is_active is True
        assert user2.is_active is True

        # Deactivate tenant with cascade
        updated_tenant, users_affected = tenant_service.update_tenant_status_with_cascade(
            db=db_session,
            tenant_id=tenant.id,
            is_active=False,
        )

        # Verify tenant deactivated
        assert updated_tenant.is_active is False
        assert users_affected == 2

        # Verify users deactivated
        db_session.refresh(user1)
        db_session.refresh(user2)
        assert user1.is_active is False
        assert user2.is_active is False

    def test_update_tenant_status_with_cascade_reactivates_users(self, db_session: Session):
        """Test update_tenant_status_with_cascade reactivates all users."""
        # Create tenant with users
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Company",
        )

        user1 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="hashed",
            role="OWNER",
        )
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user2",
            email="user2@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Deactivate tenant and users first
        tenant_service.update_tenant_status_with_cascade(
            db=db_session,
            tenant_id=tenant.id,
            is_active=False,
        )

        db_session.refresh(tenant)
        db_session.refresh(user1)
        db_session.refresh(user2)
        assert tenant.is_active is False
        assert user1.is_active is False
        assert user2.is_active is False

        # Reactivate tenant with cascade
        updated_tenant, users_affected = tenant_service.update_tenant_status_with_cascade(
            db=db_session,
            tenant_id=tenant.id,
            is_active=True,
        )

        # Verify tenant reactivated
        assert updated_tenant.is_active is True
        assert users_affected == 2

        # Verify users reactivated
        db_session.refresh(user1)
        db_session.refresh(user2)
        assert user1.is_active is True
        assert user2.is_active is True

    def test_get_cascade_impact_returns_user_counts(self, db_session: Session):
        """Test get_cascade_impact returns correct user counts."""
        # Create tenant
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Company",
        )

        # Create 3 active users
        for i in range(3):
            user_repository.create(
                db=db_session,
                tenant_id=tenant.id,
                username=f"user{i}",
                email=f"user{i}@company.com",
                password_hash="hashed",
                role="MEMBER",
            )

        # Get impact
        impact = tenant_service.get_cascade_impact(db=db_session, tenant_id=tenant.id)

        # Verify counts
        assert impact["total_users"] == 3
        assert impact["active_users"] == 3
        assert impact["inactive_users"] == 0

        # Deactivate 2 users manually
        users = user_repository.list_by_tenant(db=db_session, tenant_id=tenant.id)
        users[0].is_active = False
        users[1].is_active = False
        db_session.commit()

        # Get impact again
        impact = tenant_service.get_cascade_impact(db=db_session, tenant_id=tenant.id)

        # Verify counts updated
        assert impact["total_users"] == 3
        assert impact["active_users"] == 1
        assert impact["inactive_users"] == 2

    def test_update_tenant_with_cascade_tenant_not_found(self, db_session: Session):
        """Test update_tenant_with_cascade raises ValueError if tenant not found."""
        with pytest.raises(ValueError, match="Tenant with id 999 not found"):
            tenant_service.update_tenant_with_cascade(
                db=db_session,
                tenant_id=999,
                tenant_name="New Name",
            )

    def test_update_tenant_status_with_cascade_tenant_not_found(self, db_session: Session):
        """Test update_tenant_status_with_cascade raises ValueError if tenant not found."""
        with pytest.raises(ValueError, match="Tenant with id 999 not found"):
            tenant_service.update_tenant_status_with_cascade(
                db=db_session,
                tenant_id=999,
                is_active=False,
            )

    def test_update_tenant_with_cascade_no_users(self, db_session: Session):
        """Test update_tenant_with_cascade works with no users in tenant."""
        # Create tenant without users
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Old Name",
        )

        # Update tenant with cascade
        updated_tenant, users_affected = tenant_service.update_tenant_with_cascade(
            db=db_session,
            tenant_id=tenant.id,
            tenant_name="New Name",
        )

        # Verify tenant updated
        assert updated_tenant.tenant_name == "New Name"
        # No users to update
        assert users_affected == 0

    def test_cascade_preserves_other_user_fields(self, db_session: Session):
        """Test cascade updates don't affect other user fields."""
        # Create tenant with user
        tenant = tenant_repository.create(
            db=db_session,
            email="company@example.com",
            password_hash="hashed",
            tenant_name="Old Name",
        )

        user = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="user1",
            email="user1@company.com",
            password_hash="original_hash",
            role="ADMIN",
        )

        original_email = user.email
        original_password_hash = user.password_hash
        original_role = user.role
        original_created_at = user.created_at

        # Update tenant with cascade
        tenant_service.update_tenant_with_cascade(
            db=db_session,
            tenant_id=tenant.id,
            tenant_name="New Name",
        )

        # Verify only tenant_name changed
        db_session.refresh(user)
        assert user.tenant_name == "New Name"
        assert user.email == original_email
        assert user.password_hash == original_password_hash
        assert user.role == original_role
        assert user.created_at == original_created_at
