"""Unit tests for tenant service."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.services import tenant_service


class TestAuthenticateOrCreateTenant:
    """Test suite for authenticate_or_create_tenant function."""

    def test_create_new_tenant(self, db_session: Session):
        """Test creating a new tenant when it doesn't exist."""
        tenant_email = "newcompany@example.com"
        password = "securepassword123"

        tenant, owner, is_new = tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, password
        )

        # Verify new tenant was created
        assert is_new is True
        assert tenant.id is not None
        assert tenant.email == "newcompany@example.com"
        assert tenant.is_active is True

        # Verify owner user was created
        assert owner.id is not None
        assert owner.tenant_id == tenant.id
        assert owner.username == tenant_email  # Username defaults to email
        assert owner.email == tenant_email
        assert owner.role == "OWNER"
        assert owner.is_active is True

    def test_authenticate_existing_tenant(self, db_session: Session):
        """Test authenticating an existing tenant."""
        tenant_email = "existing@example.com"
        password = "password123"

        # First, create the tenant
        tenant1, owner1, is_new1 = tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, password
        )
        assert is_new1 is True

        # Now authenticate with same credentials
        tenant2, owner2, is_new2 = tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, password
        )

        # Verify existing tenant was authenticated
        assert is_new2 is False
        assert tenant2.id == tenant1.id
        assert owner2.id == owner1.id

    def test_authenticate_existing_tenant_wrong_password(self, db_session: Session):
        """Test authenticating existing tenant with wrong password fails."""
        tenant_email = "company@example.com"
        correct_password = "correctpassword"
        wrong_password = "wrongpassword"

        # Create tenant
        tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, correct_password
        )

        # Try to authenticate with wrong password
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            tenant_service.authenticate_or_create_tenant(
                db_session, tenant_email, wrong_password
            )

    def test_authenticate_inactive_tenant(self, db_session: Session):
        """Test authenticating inactive tenant fails."""
        tenant_email = "inactive@example.com"
        password = "password123"

        # Create tenant
        tenant, owner, _ = tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, password
        )

        # Deactivate tenant
        tenant.is_active = False
        db_session.commit()

        # Try to authenticate
        with pytest.raises(AuthenticationError, match="Tenant account is disabled"):
            tenant_service.authenticate_or_create_tenant(
                db_session, tenant_email, password
            )

    def test_authenticate_tenant_with_inactive_owner(self, db_session: Session):
        """Test authenticating tenant with inactive owner fails."""
        tenant_email = "company@example.com"
        password = "password123"

        # Create tenant
        tenant, owner, _ = tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, password
        )

        # Deactivate owner
        owner.is_active = False
        db_session.commit()

        # Try to authenticate
        with pytest.raises(AuthenticationError, match="Tenant owner account is disabled"):
            tenant_service.authenticate_or_create_tenant(
                db_session, tenant_email, password
            )

    def test_email_normalization(self, db_session: Session):
        """Test that tenant email is normalized to lowercase."""
        tenant_email = "Company@Example.COM"
        password = "password123"

        tenant, owner, is_new = tenant_service.authenticate_or_create_tenant(
            db_session, tenant_email, password
        )

        assert tenant.email == "company@example.com"
        assert owner.email == "company@example.com"


class TestCreateTenantWithOwner:
    """Test suite for create_tenant_with_owner function."""

    def test_create_tenant_with_owner_default_username(self, db_session: Session):
        """Test creating tenant with owner using default username (email)."""
        email = "owner@example.com"
        password = "password123"

        tenant, owner = tenant_service.create_tenant_with_owner(
            db_session, email, password
        )

        assert tenant.id is not None
        assert tenant.email == "owner@example.com"

        assert owner.id is not None
        assert owner.tenant_id == tenant.id
        assert owner.username == email  # Defaults to email
        assert owner.email == email
        assert owner.role == "OWNER"

    def test_create_tenant_with_owner_custom_username(self, db_session: Session):
        """Test creating tenant with owner using custom username."""
        email = "owner@example.com"
        password = "password123"
        username = "customowner"

        tenant, owner = tenant_service.create_tenant_with_owner(
            db_session, email, password, username=username
        )

        assert owner.username == username
        assert owner.email == email  # Email still same as tenant

    def test_owner_has_same_password_as_tenant(self, db_session: Session):
        """Test that owner user has the same password hash as tenant."""
        email = "owner@example.com"
        password = "password123"

        tenant, owner = tenant_service.create_tenant_with_owner(
            db_session, email, password
        )

        # Both should have the same password hash
        assert tenant.password_hash == owner.password_hash

    def test_multiple_tenants_created(self, db_session: Session):
        """Test creating multiple tenants independently."""
        tenant1, owner1 = tenant_service.create_tenant_with_owner(
            db_session, "tenant1@example.com", "password1"
        )
        tenant2, owner2 = tenant_service.create_tenant_with_owner(
            db_session, "tenant2@example.com", "password2"
        )

        # Tenants should be different
        assert tenant1.id != tenant2.id
        assert owner1.id != owner2.id
        assert owner1.tenant_id == tenant1.id
        assert owner2.tenant_id == tenant2.id