"""Unit tests for tenant repository."""

import pytest
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant import Tenant
from app.repositories import tenant_repository


class TestTenantRepository:
    """Test suite for tenant repository operations."""

    def test_create_tenant(self, db_session: Session):
        """Test creating a new tenant."""
        email = "test@example.com"
        password_hash = hash_password("password123")

        tenant = tenant_repository.create(db_session, email, password_hash)

        assert tenant.id is not None
        assert tenant.email == "test@example.com"
        assert tenant.password_hash == password_hash
        assert tenant.is_active is True

    def test_create_tenant_normalizes_email_to_lowercase(self, db_session: Session):
        """Test that tenant email is normalized to lowercase."""
        email = "Test@Example.COM"
        password_hash = hash_password("password123")

        tenant = tenant_repository.create(db_session, email, password_hash)

        assert tenant.email == "test@example.com"

    def test_get_by_id(self, db_session: Session):
        """Test getting tenant by ID."""
        email = "test@example.com"
        password_hash = hash_password("password123")
        created_tenant = tenant_repository.create(db_session, email, password_hash)

        tenant = tenant_repository.get_by_id(db_session, created_tenant.id)

        assert tenant is not None
        assert tenant.id == created_tenant.id
        assert tenant.email == email

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting tenant by non-existent ID returns None."""
        tenant = tenant_repository.get_by_id(db_session, 99999)

        assert tenant is None

    def test_get_by_email(self, db_session: Session):
        """Test getting tenant by email."""
        email = "test@example.com"
        password_hash = hash_password("password123")
        tenant_repository.create(db_session, email, password_hash)

        tenant = tenant_repository.get_by_email(db_session, email)

        assert tenant is not None
        assert tenant.email == email

    def test_get_by_email_case_insensitive(self, db_session: Session):
        """Test getting tenant by email is case-insensitive."""
        email = "test@example.com"
        password_hash = hash_password("password123")
        tenant_repository.create(db_session, email, password_hash)

        # Query with different case
        tenant = tenant_repository.get_by_email(db_session, "Test@Example.COM")

        assert tenant is not None
        assert tenant.email == "test@example.com"

    def test_get_by_email_not_found(self, db_session: Session):
        """Test getting tenant by non-existent email returns None."""
        tenant = tenant_repository.get_by_email(db_session, "nonexistent@example.com")

        assert tenant is None

    def test_update_status_activate(self, db_session: Session):
        """Test activating a tenant."""
        email = "test@example.com"
        password_hash = hash_password("password123")
        tenant = tenant_repository.create(db_session, email, password_hash)

        # First deactivate
        tenant.is_active = False
        db_session.commit()

        # Then reactivate
        updated_tenant = tenant_repository.update_status(db_session, tenant.id, True)

        assert updated_tenant is not None
        assert updated_tenant.is_active is True

    def test_update_status_deactivate(self, db_session: Session):
        """Test deactivating a tenant."""
        email = "test@example.com"
        password_hash = hash_password("password123")
        tenant = tenant_repository.create(db_session, email, password_hash)

        updated_tenant = tenant_repository.update_status(db_session, tenant.id, False)

        assert updated_tenant is not None
        assert updated_tenant.is_active is False

    def test_update_status_tenant_not_found(self, db_session: Session):
        """Test updating status of non-existent tenant returns None."""
        result = tenant_repository.update_status(db_session, 99999, False)

        assert result is None

    def test_get_all(self, db_session: Session):
        """Test getting all tenants."""
        # Create multiple tenants
        for i in range(3):
            email = f"tenant{i}@example.com"
            password_hash = hash_password(f"password{i}")
            tenant_repository.create(db_session, email, password_hash)

        tenants = tenant_repository.get_all(db_session)

        # Should have at least 3 tenants (plus the default tenant from migration)
        assert len(tenants) >= 3

    def test_get_all_with_pagination(self, db_session: Session):
        """Test getting tenants with pagination."""
        # Create 5 tenants
        for i in range(5):
            email = f"tenant{i}@example.com"
            password_hash = hash_password(f"password{i}")
            tenant_repository.create(db_session, email, password_hash)

        # Get first 2 tenants (skip 0, limit 2)
        tenants_page1 = tenant_repository.get_all(db_session, skip=0, limit=2)
        assert len(tenants_page1) == 2

        # Get next 2 tenants (skip 2, limit 2)
        tenants_page2 = tenant_repository.get_all(db_session, skip=2, limit=2)
        assert len(tenants_page2) == 2

        # Pages should have different tenants
        assert tenants_page1[0].id != tenants_page2[0].id

    def test_count_all(self, db_session: Session):
        """Test counting all tenants."""
        initial_count = tenant_repository.count_all(db_session)

        # Create 3 new tenants
        for i in range(3):
            email = f"tenant{i}@example.com"
            password_hash = hash_password(f"password{i}")
            tenant_repository.create(db_session, email, password_hash)

        final_count = tenant_repository.count_all(db_session)

        assert final_count == initial_count + 3