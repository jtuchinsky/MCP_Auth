"""Integration tests for tenant cascade endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories import tenant_repository, user_repository
from app.services import auth_service, tenant_service


class TestTenantUpdateCascade:
    """Test PUT /tenants/me cascades to users."""

    def test_update_tenant_name_cascades_to_users(self, client: TestClient, db_session: Session):
        """Test PUT /tenants/me updates tenant_name for all users."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Old Company Name",
        )

        # Create additional users in the tenant
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )
        user3 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="member1",
            email="member1@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Login to get access token
        response = client.post(
            "/auth/login",
            json={
                "tenant_email": "company@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]

        # Update tenant name via API
        response = client.put(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"tenant_name": "New Company Name"},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_name"] == "New Company Name"

        # Verify all users have updated tenant_name
        db_session.refresh(owner)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert owner.tenant_name == "New Company Name"
        assert user2.tenant_name == "New Company Name"
        assert user3.tenant_name == "New Company Name"

    def test_update_tenant_name_as_admin_cascades(self, client: TestClient, db_session: Session):
        """Test PUT /tenants/me works for ADMIN role and cascades."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Old Name",
        )

        # Create admin user
        admin = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )

        # Login as admin
        # Create tokens for admin
        access_token, _ = auth_service.create_tokens(
            db=db_session,
            user=admin,
            client_id=None,
            scope=None,
        )

        # Update tenant name via API as admin
        response = client.put(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"tenant_name": "Updated by Admin"},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_name"] == "Updated by Admin"

        # Verify all users have updated tenant_name
        db_session.refresh(owner)
        db_session.refresh(admin)

        assert owner.tenant_name == "Updated by Admin"
        assert admin.tenant_name == "Updated by Admin"

    def test_update_tenant_name_as_member_fails(self, client: TestClient, db_session: Session):
        """Test PUT /tenants/me fails for MEMBER role."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company Name",
        )

        # Create member user
        member = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="member1",
            email="member1@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Login as member
        access_token, _ = auth_service.create_tokens(
            db=db_session,
            user=member,
            client_id=None,
            scope=None,
        )

        # Attempt to update tenant name via API as member
        response = client.put(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"tenant_name": "Attempted Update"},
        )

        # Verify forbidden
        assert response.status_code == 403
        assert ("ADMIN" in response.json()["detail"] or "OWNER" in response.json()["detail"])


class TestTenantStatusCascade:
    """Test PATCH /tenants/me/status cascades to users."""

    def test_deactivate_tenant_deactivates_all_users(self, client: TestClient, db_session: Session):
        """Test PATCH /tenants/me/status deactivates all users."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company",
        )

        # Create additional users
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )
        user3 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="member1",
            email="member1@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Verify all start as active
        assert tenant.is_active is True
        assert owner.is_active is True
        assert user2.is_active is True
        assert user3.is_active is True

        # Login to get access token
        response = client.post(
            "/auth/login",
            json={
                "tenant_email": "company@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]

        # Deactivate tenant via API
        response = client.patch(
            "/tenants/me/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"is_active": False},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

        # Verify all users are now inactive
        db_session.refresh(tenant)
        db_session.refresh(owner)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert tenant.is_active is False
        assert owner.is_active is False
        assert user2.is_active is False
        assert user3.is_active is False

    def test_reactivate_tenant_reactivates_all_users(self, client: TestClient, db_session: Session):
        """Test PATCH /tenants/me/status reactivates all users."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company",
        )

        # Create additional user
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )

        # Deactivate tenant and users first
        tenant_repository.update_status(db=db_session, tenant_id=tenant.id, is_active=False)
        user_repository.bulk_update_user_status(db=db_session, tenant_id=tenant.id, is_active=False)

        db_session.refresh(tenant)
        db_session.refresh(owner)
        db_session.refresh(user2)

        assert tenant.is_active is False
        assert owner.is_active is False
        assert user2.is_active is False

        # Manually reactivate tenant and owner to enable login
        # (In production, this would require manual DB intervention)
        tenant_repository.update_status(db=db_session, tenant_id=tenant.id, is_active=True)
        owner.is_active = True
        db_session.commit()

        # Login to get access token
        response = client.post(
            "/auth/login",
            json={
                "tenant_email": "company@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]

        # Reactivate tenant via API (should cascade to all users)
        response = client.patch(
            "/tenants/me/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"is_active": True},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

        # Verify all users are now active
        db_session.refresh(tenant)
        db_session.refresh(owner)
        db_session.refresh(user2)

        assert tenant.is_active is True
        assert owner.is_active is True
        assert user2.is_active is True

    def test_deactivate_tenant_as_admin_fails(self, client: TestClient, db_session: Session):
        """Test PATCH /tenants/me/status fails for ADMIN role."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company",
        )

        # Create admin user
        admin = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )

        # Login as admin
        access_token, _ = auth_service.create_tokens(
            db=db_session,
            user=admin,
            client_id=None,
            scope=None,
        )

        # Attempt to deactivate tenant via API as admin
        response = client.patch(
            "/tenants/me/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"is_active": False},
        )

        # Verify forbidden
        assert response.status_code == 403
        assert "OWNER" in response.json()["detail"]


class TestTenantDeleteCascade:
    """Test DELETE /tenants/me cascades to users."""

    def test_delete_tenant_deactivates_all_users(self, client: TestClient, db_session: Session):
        """Test DELETE /tenants/me deactivates all users."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company",
        )

        # Create additional users
        user2 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )
        user3 = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="member1",
            email="member1@company.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Verify all start as active
        assert tenant.is_active is True
        assert owner.is_active is True
        assert user2.is_active is True
        assert user3.is_active is True

        # Login to get access token
        response = client.post(
            "/auth/login",
            json={
                "tenant_email": "company@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]

        # Delete tenant via API
        response = client.delete(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify response
        assert response.status_code == 204
        assert response.text == ""  # No content

        # Verify tenant and all users are now inactive
        db_session.refresh(tenant)
        db_session.refresh(owner)
        db_session.refresh(user2)
        db_session.refresh(user3)

        assert tenant.is_active is False
        assert owner.is_active is False
        assert user2.is_active is False
        assert user3.is_active is False

    def test_delete_tenant_as_admin_fails(self, client: TestClient, db_session: Session):
        """Test DELETE /tenants/me fails for ADMIN role."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company",
        )

        # Create admin user
        admin = user_repository.create(
            db=db_session,
            tenant_id=tenant.id,
            username="admin1",
            email="admin1@company.com",
            password_hash="hashed",
            role="ADMIN",
        )

        # Login as admin
        access_token, _ = auth_service.create_tokens(
            db=db_session,
            user=admin,
            client_id=None,
            scope=None,
        )

        # Attempt to delete tenant via API as admin
        response = client.delete(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify forbidden
        assert response.status_code == 403
        assert "OWNER" in response.json()["detail"]

        # Verify tenant and users are still active
        db_session.refresh(tenant)
        db_session.refresh(owner)
        db_session.refresh(admin)

        assert tenant.is_active is True
        assert owner.is_active is True
        assert admin.is_active is True

    def test_delete_tenant_preserves_data(self, client: TestClient, db_session: Session):
        """Test DELETE /tenants/me is soft delete - data preserved."""
        # Create tenant with owner
        tenant, owner = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company@example.com",
            password="password123",
            tenant_name="Company",
        )

        tenant_id = tenant.id
        owner_id = owner.id
        original_email = tenant.email
        original_tenant_name = tenant.tenant_name

        # Login and delete
        response = client.post(
            "/auth/login",
            json={
                "tenant_email": "company@example.com",
                "password": "password123",
            },
        )
        access_token = response.json()["access_token"]

        response = client.delete(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # Verify tenant still exists in database
        deleted_tenant = tenant_repository.get_by_id(db_session, tenant_id)
        assert deleted_tenant is not None
        assert deleted_tenant.email == original_email
        assert deleted_tenant.tenant_name == original_tenant_name
        assert deleted_tenant.is_active is False  # Just marked inactive

        # Verify owner still exists in database
        deleted_owner = user_repository.get_by_id(db_session, owner_id)
        assert deleted_owner is not None
        assert deleted_owner.email == owner.email
        assert deleted_owner.is_active is False  # Just marked inactive


class TestCascadeIsolation:
    """Test cascade operations only affect target tenant."""

    def test_tenant_update_does_not_affect_other_tenants(
        self, client: TestClient, db_session: Session
    ):
        """Test updating tenant 1 doesn't affect tenant 2's users."""
        # Create two tenants with users
        tenant1, owner1 = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company1@example.com",
            password="password123",
            tenant_name="Company 1",
        )
        user1_t1 = user_repository.create(
            db=db_session,
            tenant_id=tenant1.id,
            username="user1",
            email="user1@company1.com",
            password_hash="hashed",
            role="MEMBER",
        )

        tenant2, owner2 = tenant_service.create_tenant_with_owner(
            db=db_session,
            email="company2@example.com",
            password="password123",
            tenant_name="Company 2",
        )
        user1_t2 = user_repository.create(
            db=db_session,
            tenant_id=tenant2.id,
            username="user1",
            email="user1@company2.com",
            password_hash="hashed",
            role="MEMBER",
        )

        # Login as tenant 1 owner
        response = client.post(
            "/auth/login",
            json={
                "tenant_email": "company1@example.com",
                "password": "password123",
            },
        )
        access_token_t1 = response.json()["access_token"]

        # Update tenant 1 name
        response = client.put(
            "/tenants/me",
            headers={"Authorization": f"Bearer {access_token_t1}"},
            json={"tenant_name": "Updated Company 1"},
        )
        assert response.status_code == 200

        # Verify tenant 1 users updated
        db_session.refresh(owner1)
        db_session.refresh(user1_t1)
        assert owner1.tenant_name == "Updated Company 1"
        assert user1_t1.tenant_name == "Updated Company 1"

        # Verify tenant 2 users NOT updated
        db_session.refresh(owner2)
        db_session.refresh(user1_t2)
        assert owner2.tenant_name is None
        assert user1_t2.tenant_name is None
