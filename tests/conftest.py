"""Pytest configuration and shared fixtures for tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.models.tenant import Tenant
from app.models.token import RefreshToken  # noqa: F401 - Import to register with Base
from app.models.user import User
from app.repositories import tenant_repository
from app.services import auth_service, jwt_service, totp_service
from main import app

# Test database configuration (file-based SQLite for integration tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_integration.db"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test function.

    Yields:
        None - Database is ready for use

    Cleanup:
        Drops all tables after test completion
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Provide a database session for tests.

    Args:
        test_db: Test database fixture

    Yields:
        Session: SQLAlchemy database session

    Cleanup:
        Rolls back any uncommitted changes and closes session
    """
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_db, db_session: Session):
    """
    Provide a FastAPI test client with database override.

    Args:
        test_db: Test database fixture (ensures tables are created)
        db_session: Test database session

    Yields:
        TestClient: FastAPI test client

    Example:
        >>> def test_endpoint(client):
        >>>     response = client.get("/")
        >>>     assert response.status_code == 200
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_tenant(db_session: Session) -> Tenant:
    """
    Create a test tenant.

    Args:
        db_session: Test database session

    Returns:
        Tenant: Test tenant instance

    Example:
        >>> def test_with_tenant(test_tenant):
        >>>     assert test_tenant.email == "testtenant@example.com"
    """
    from app.core.security import hash_password

    tenant = tenant_repository.create(
        db=db_session,
        email="testtenant@example.com",
        password_hash=hash_password("tenantpassword123"),
    )
    return tenant


@pytest.fixture(scope="function")
def test_user(db_session: Session, test_tenant: Tenant) -> User:
    """
    Create a test user without TOTP.

    Args:
        db_session: Test database session
        test_tenant: Test tenant instance

    Returns:
        User: Test user instance

    Example:
        >>> def test_login(test_user, client):
        >>>     response = client.post("/auth/login", json={
        >>>         "email": test_user.email,
        >>>         "password": "password123"
        >>>     })
        >>>     assert response.status_code == 200
    """
    user = auth_service.register_user(
        db=db_session,
        tenant_id=test_tenant.id,
        username="testuser",
        email="testuser@example.com",
        password="password123",
        role="MEMBER",
    )
    return user


@pytest.fixture(scope="function")
def test_user_with_totp(db_session: Session, test_tenant: Tenant) -> User:
    """
    Create a test user with TOTP enabled.

    Args:
        db_session: Test database session
        test_tenant: Test tenant instance

    Returns:
        User: Test user instance with TOTP enabled

    Example:
        >>> def test_totp_login(test_user_with_totp, client):
        >>>     # User has TOTP enabled
        >>>     assert test_user_with_totp.is_totp_enabled is True
    """
    # Create user
    user = auth_service.register_user(
        db=db_session,
        tenant_id=test_tenant.id,
        username="totpuser",
        email="totpuser@example.com",
        password="password123",
        role="MEMBER",
    )

    # Generate and set TOTP secret
    secret = totp_service.generate_secret()
    from app.repositories import user_repository

    user_repository.update_totp_secret(db=db_session, user_id=user.id, secret=secret)

    # Enable TOTP
    user = user_repository.enable_totp(db=db_session, user_id=user.id)

    return user


@pytest.fixture(scope="function")
def access_token(test_user: User) -> str:
    """
    Create a valid access token for test user.

    Args:
        test_user: Test user instance

    Returns:
        str: JWT access token

    Example:
        >>> def test_protected_endpoint(access_token, client):
        >>>     headers = {"Authorization": f"Bearer {access_token}"}
        >>>     response = client.get("/api/protected/me", headers=headers)
        >>>     assert response.status_code == 200
    """
    token = jwt_service.create_access_token(
        user_id=test_user.id,
        email=test_user.email,
        tenant_id=test_user.tenant_id,
        role=test_user.role,
    )
    return token


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, access_token: str) -> TestClient:
    """
    Provide an authenticated test client with Authorization header.

    Args:
        client: FastAPI test client
        access_token: Valid JWT access token

    Returns:
        TestClient: Test client with authorization

    Example:
        >>> def test_me_endpoint(authenticated_client):
        >>>     response = authenticated_client.get("/api/protected/me")
        >>>     assert response.status_code == 200
    """
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    return client


@pytest.fixture(scope="function")
def user_tokens(test_user: User, db_session: Session) -> dict:
    """
    Create access and refresh tokens for test user.

    Args:
        test_user: Test user instance
        db_session: Test database session

    Returns:
        dict: Dictionary with 'access_token' and 'refresh_token'

    Example:
        >>> def test_token_refresh(user_tokens, client):
        >>>     response = client.post("/auth/refresh", json={
        >>>         "refresh_token": user_tokens["refresh_token"]
        >>>     })
        >>>     assert response.status_code == 200
    """
    access_token, refresh_token = auth_service.create_tokens(
        db=db_session,
        user=test_user,
        client_id=None,
        scope=None,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }