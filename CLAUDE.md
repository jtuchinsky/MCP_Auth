# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MCP-Compatible Authentication Service** - A production-ready FastAPI authentication service implementing OAuth 2.1 with Model Context Protocol (MCP) compliance.

Version: 0.1.0

This service provides secure user authentication, JWT-based access control, TOTP two-factor authentication, multi-tenant support, and full OAuth 2.1 compliance for MCP clients.

## Features

- ✅ **Tenant-Based Authentication** - Multi-tenant architecture with auto-creation on first login
- ✅ **Tenant CRUD Management** - Full tenant lifecycle management (view, update, status, delete, list users) with role-based authorization
- ✅ **User Registration & Login** - Secure account creation with bcrypt password hashing for tenants and users
- ✅ **JWT Access Tokens** - Short-lived tokens (15 minutes) with HS256 signing, includes `tenant_id` and `role` claims
- ✅ **Refresh Tokens** - Long-lived tokens (30 days) with automatic rotation
- ✅ **TOTP 2FA** - Time-based One-Time Password authentication with QR code generation
- ✅ **Multi-Tenancy** - Complete tenant isolation with role-based access control (OWNER, ADMIN, MEMBER)
- ✅ **MCP OAuth 2.1 Compliance** - Full support for MCP authorization flows
- ✅ **Protected Endpoints** - User profile management with JWT authentication
- ✅ **Token Rotation** - Refresh tokens are rotated on each use for enhanced security
- ✅ **Comprehensive Testing** - 100+ passing tests (48 tenant/JWT unit + 52 integration)

## Architecture

### Layered Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       API Layer (Routes)                              │
│  /auth/*  |  /api/protected/*  |  /tenants/*  |  /.well-known/*     │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Business Logic Layer (Services)             │
│  tenant_service  |  auth_service  |  jwt_service  | ...  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Data Access Layer (Repositories)            │
│  tenant_repository  |  user_repository  |  token_repo   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Database Layer (Models)                │
│         Tenant  |  User  |  RefreshToken (SQLite)        │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Routes** (`app/routes/`) - FastAPI endpoint handlers
   - `auth.py` - Authentication endpoints (tenant login, user login, TOTP)
   - `tenants.py` - Tenant CRUD endpoints (view, update, status, delete, list users)
   - `protected.py` - Protected user profile endpoints
   - `well_known.py` - OAuth 2.1 metadata discovery

2. **Services** (`app/services/`) - Business logic
   - `tenant_service.py` - Tenant authentication with auto-creation
   - `auth_service.py` - User authentication and token management
   - `jwt_service.py` - JWT token creation and validation (includes tenant_id, role)
   - `totp_service.py` - TOTP secret generation and verification
   - `oauth2_service.py` - MCP OAuth 2.1 metadata

3. **Repositories** (`app/repositories/`) - Database operations
   - `tenant_repository.py` - Tenant CRUD operations
   - `user_repository.py` - User CRUD operations with tenant-scoped queries
   - `token_repository.py` - Refresh token management

4. **Models** (`app/models/`) - SQLAlchemy ORM models
   - `tenant.py` - Tenant table (email, password, is_active)
   - `user.py` - User table with tenant_id, username, role, TOTP support
   - `token.py` - RefreshToken table with revocation

5. **Dependencies** (`app/dependencies.py`) - FastAPI dependency injection
   - `get_current_user()` - Extracts JWT, validates tenant isolation, checks tenant/user active status
   - `require_owner()` - Enforces OWNER role requirement
   - `require_admin_or_owner()` - Enforces ADMIN or OWNER role requirement
   - `require_totp_disabled()` - Ensures TOTP is not already enabled (for setup)

### Dependency Injection Pattern

This project uses FastAPI's dependency injection system for authentication and database sessions:

```python
# In route handlers, dependencies are injected via Depends()
@router.get("/api/protected/me")
async def get_me(user: User = Depends(get_current_user)):
    # user is automatically extracted from JWT token
    return user

# Database sessions are injected similarly
@router.post("/auth/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    # db is a SQLAlchemy session
    return auth_service.register_user(db, data)
```

The `get_current_user` dependency:
1. Extracts the `Authorization: Bearer <token>` header
2. Validates and decodes the JWT using `jwt_service`
3. Extracts `tenant_id` and `role` from JWT payload
4. Fetches the user from the database
5. **Validates tenant_id matches** (tenant isolation - prevents token tampering)
6. Checks both user and tenant are active
7. Returns the User object or raises AuthenticationError/AuthorizationError

## Technology Stack

- **Framework**: FastAPI 0.126.0+
- **ASGI Server**: Uvicorn 0.38.0+
- **Database**: SQLite (via SQLAlchemy 2.0.36+)
- **Migrations**: Alembic 1.14.0+
- **Authentication**: PyJWT 2.10.1+, bcrypt 4.0.0+
- **TOTP/2FA**: pyotp 2.9.0+, qrcode[pil] 8.0+
- **Validation**: Pydantic 2.x with email-validator
- **Testing**: pytest 8.3.4+, pytest-asyncio, pytest-cov
- **Python Version**: >=3.12
- **Dependency Management**: uv

## Project Structure

```
MCP_Auth/
├── app/
│   ├── core/
│   │   ├── exceptions.py      # Custom exception classes
│   │   └── security.py        # Password hashing utilities
│   ├── models/
│   │   ├── tenant.py         # Tenant ORM model
│   │   ├── user.py           # User ORM model (with tenant_id, username, role)
│   │   └── token.py          # RefreshToken ORM model
│   ├── repositories/
│   │   ├── tenant_repository.py  # Tenant database operations
│   │   ├── user_repository.py    # User database operations (tenant-scoped)
│   │   └── token_repository.py   # Token database operations
│   ├── routes/
│   │   ├── auth.py           # Authentication endpoints (tenant login, user login)
│   │   ├── tenants.py        # Tenant CRUD endpoints (view, update, status, delete, list users)
│   │   ├── protected.py      # Protected user endpoints
│   │   └── well_known.py     # OAuth 2.1 metadata
│   ├── schemas/
│   │   ├── tenant.py         # Tenant request/response schemas (TenantUpdate, TenantStatusUpdate)
│   │   ├── auth.py           # Auth request/response schemas
│   │   ├── totp.py           # TOTP schemas
│   │   └── user.py           # User schemas (with tenant_id, username, role)
│   ├── services/
│   │   ├── tenant_service.py # Tenant authentication with auto-creation
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── jwt_service.py    # JWT token management (includes tenant_id, role)
│   │   ├── totp_service.py   # TOTP/2FA logic
│   │   └── oauth2_service.py # MCP metadata
│   ├── config.py             # Settings with pydantic-settings
│   ├── database.py           # SQLAlchemy setup
│   └── dependencies.py       # FastAPI dependencies (with tenant isolation)
├── alembic/
│   ├── versions/             # Database migrations
│   │   └── e9258cf92b4d_add_tenant_based_authentication.py  # Tenant migration
│   └── env.py               # Alembic configuration
├── tests/
│   ├── unit/                # Unit tests (48+ tests)
│   │   ├── test_tenant_repository.py
│   │   ├── test_tenant_service.py
│   │   ├── test_jwt_service.py
│   │   └── ... (other unit tests)
│   ├── integration/         # Integration tests (52+ passing)
│   │   ├── test_auth_endpoints.py
│   │   ├── test_totp_flow.py
│   │   └── test_protected_endpoints.py
│   └── conftest.py          # Shared test fixtures (with tenant support)
├── docs/
│   ├── TENANT_REFACTORING.md  # Refactoring status
│   ├── SCHEMAS.md             # Database schema documentation
│   ├── RUNNING.md             # Quick start guide
│   └── PLAN.md                # Original implementation plan
├── main.py                  # FastAPI application
├── pyproject.toml           # Project configuration
├── .env.example             # Environment variable template
├── .gitignore              # Git ignore rules
└── CLAUDE.md               # This file
```

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

### Required Variables

```bash
# Database
DATABASE_URL=sqlite:///./mcp_auth.db

# JWT Configuration (REQUIRED - generate a secure random key)
SECRET_KEY=your-super-secret-key-min-32-characters-long-change-this-in-production

# JWT Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15    # Access token lifetime
REFRESH_TOKEN_EXPIRE_DAYS=30      # Refresh token lifetime

# TOTP Configuration
TOTP_ISSUER_NAME=MCP Auth Service # Appears in authenticator apps
```

### Generating a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Development Commands

### Setup

```bash
# Clone the repository
git clone https://github.com/jtuchinsky/MCP_Auth.git
cd MCP_Auth

# Create .env file
cp .env.example .env
# Edit .env and set SECRET_KEY to a secure random value

# Install dependencies (uses uv)
uv sync --extra dev

# Run database migrations
alembic upgrade head
```

### Running the Application

```bash
# Development server with auto-reload
uvicorn main:app --reload

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server runs on `http://127.0.0.1:8000` by default.

### API Documentation

Once running, access interactive API documentation:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Test Coverage

Current test coverage: **100+ passing tests** (tenant refactoring complete)

- **Unit Tests** (48+ tenant/JWT tests passing):
  - `test_tenant_repository.py` - Tenant CRUD operations (13 tests)
  - `test_tenant_service.py` - Tenant authentication & auto-creation (10 tests)
  - `test_jwt_service.py` - JWT token operations with tenant_id/role (25 tests)
  - Plus: `test_security.py`, `test_totp_service.py`, and other unit tests

- **Integration Tests** (52+ tests passing out of 59):
  - `test_auth_endpoints.py` - Tenant/user auth endpoints (24 tests, all passing)
  - `test_totp_flow.py` - TOTP/2FA flows (15 passing)
  - `test_protected_endpoints.py` - Protected endpoints with tenant context (13 passing)

### Test Database

Integration tests use a separate SQLite database (`test_integration.db`) that is created and destroyed for each test function to ensure test isolation. Test fixtures in `tests/conftest.py` handle database setup and teardown automatically.

## API Endpoints

For detailed API endpoint documentation including request/response examples, see:
- **README.md** - Full API endpoint reference with curl examples
- **Swagger UI** - http://127.0.0.1:8000/docs (when server is running)
- **ReDoc** - http://127.0.0.1:8000/redoc (alternative documentation)

Key endpoints:

**Authentication:**
- `POST /auth/login` - **Tenant login** (auto-creates tenant + owner on first use)
- `POST /auth/login-user` - **User login** within existing tenant
- `POST /auth/register` - ⚠️ **Deprecated** - Register new user within tenant
- `POST /auth/totp/validate` - Login with TOTP (for 2FA users)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and revoke refresh token

**Tenant Management (CRUD):**
- `GET /tenants/me` - Get current tenant info (any role)
- `PUT /tenants/me` - Update tenant name (OWNER/ADMIN)
- `PATCH /tenants/me/status` - Activate/deactivate tenant (OWNER only)
- `DELETE /tenants/me` - Soft delete tenant (OWNER only)
- `GET /tenants/me/users` - List all users in tenant (OWNER/ADMIN)

**Protected Resources:**
- `GET /api/protected/me` - Get current user (includes tenant_id, username, role)

**MCP Compliance:**
- `GET /.well-known/oauth-authorization-server` - OAuth 2.1 metadata

## MCP OAuth 2.1 Compliance

This service implements the following OAuth 2.1 and MCP specifications:

### ✅ Implemented Features

- **PKCE Required** (RFC 7636) - Proof Key for Code Exchange with S256 method
- **Resource Indicators** (RFC 8707) - Audience claims in JWT tokens
- **Authorization Server Metadata** (RFC 8414) - Discovery endpoint at `/.well-known/oauth-authorization-server`
- **Refresh Token Rotation** - New refresh token issued on each refresh, old token is revoked
- **TOTP-based 2FA** - Multi-factor authentication support with QR code setup

### OAuth 2.1 Changes from OAuth 2.0

1. ✅ **PKCE is mandatory** for authorization code flow
2. ✅ **Refresh token rotation** is implemented
3. ✅ **Implicit grant removed** (not supported)
4. ✅ **Resource Owner Password Credentials grant removed** (not supported)

## Security Features

### Password Security
- **bcrypt hashing** with automatic salt generation (12 rounds)
- **Separate passwords**: Tenants and users both have bcrypt-hashed passwords
- **Minimum password length**: 8 characters
- Passwords are never stored in plaintext

### JWT Security
- **HS256 algorithm** for token signing
- **Short-lived access tokens**: 15 minutes (configurable)
- **Token payload includes**: user ID (`sub`), email, **tenant_id**, **role**, scopes, issued (`iat`), expiry (`exp`)
- **Secret key validation**: Minimum 32 characters
- **Tenant isolation enforced**: JWT `tenant_id` validated against database user.tenant_id to prevent token tampering

### Tenant Isolation
- **Database-level isolation**: Users belong to tenants via foreign key with CASCADE delete
- **JWT-level validation**: `get_current_user()` dependency validates `tenant_id` in token matches user's tenant
- **Cross-tenant access prevention**: Authorization error if token tenant_id doesn't match user's tenant_id
- **Tenant status checks**: Both user AND tenant must be active for authentication

### Role-Based Access Control (RBAC)
- **Three roles**: OWNER (tenant creator), ADMIN (elevated privileges), MEMBER (standard user)
- **Role enforcement**: `require_owner()` and `require_admin_or_owner()` dependencies
- **Role in JWT**: All access tokens include user's role for authorization decisions
- **Owner privileges**: Only OWNERs can invite users and manage tenant settings (future feature)

### Refresh Token Security
- **Long-lived but revocable**: 30 days (configurable)
- **Automatic rotation**: New token issued on each refresh
- **Database-backed**: Can be revoked at any time
- **Logout invalidates tokens**: Prevents reuse after logout

### TOTP/2FA Security
- **RFC 6238 compliant**: Standard TOTP algorithm
- **30-second time window**: Codes expire quickly
- **Base32 encoded secrets**: Secure random generation
- **QR code support**: Easy setup with authenticator apps

### API Security
- **Input validation**: Pydantic schemas validate all inputs
- **Email validation**: RFC 5322 compliant email checking
- **SQL injection protection**: SQLAlchemy ORM prevents SQL injection
- **CORS configured**: Can be restricted in production

## Database Schema

For complete database schema documentation, see [docs/SCHEMAS.md](./docs/SCHEMAS.md).

### Tenants Table

```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,           -- Globally unique tenant identifier
    password_hash VARCHAR(255) NOT NULL,          -- Bcrypt hashed password
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,                   -- Foreign key to tenants
    username VARCHAR(100) NOT NULL,               -- Unique per tenant
    email VARCHAR(255) UNIQUE NOT NULL,           -- Globally unique
    password_hash VARCHAR(255) NOT NULL,          -- Bcrypt hashed password
    role VARCHAR(50) NOT NULL DEFAULT 'MEMBER',   -- OWNER, ADMIN, or MEMBER
    is_totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    totp_secret VARCHAR(32),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE (tenant_id, username)                  -- Username unique per tenant
);
```

### RefreshToken Table

```sql
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Key Schema Design Decisions

1. **Tenant Identification**: Tenants are identified by globally unique email addresses
2. **Auto-Creation**: First login with a new email creates tenant + owner user atomically
3. **Username Scope**: Usernames are unique per tenant, not globally unique
4. **Email Uniqueness**: User emails remain globally unique to prevent confusion
5. **Cascade Delete**: Deleting a tenant deletes all associated users
6. **Default Tenant**: Database includes a default tenant (id=1) for backward compatibility

## Code Conventions

### General Principles
- **Async/await**: All route handlers are async
- **Type hints**: Use Python 3.12+ type annotations
- **Pydantic models**: For request/response validation
- **Repository pattern**: Separate data access from business logic
- **Dependency injection**: FastAPI Depends for loose coupling

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore()`

### Error Handling
- **Custom exceptions**: `AuthenticationError`, `AuthorizationError`, `TOTPError`
- **HTTP exceptions**: Use FastAPI `HTTPException` in routes
- **Validation errors**: Handled automatically by Pydantic (422 status)

### Testing Conventions
- **Test files**: `test_*.py`
- **Test classes**: `TestClassName`
- **Test methods**: `test_method_name_scenario`
- **Fixtures**: Defined in `conftest.py`
- **Assertions**: Use pytest's `assert` statements

## Common Development Tasks

### Adding a New Endpoint

1. Create route handler in appropriate file (`app/routes/`)
2. Define request/response schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add database operations in `app/repositories/` if needed
5. Write unit tests for services
6. Write integration tests for endpoints

### Adding a Database Field

1. Update model in `app/models/`
2. Create migration: `alembic revision --autogenerate -m "Add field"`
3. Review and apply migration: `alembic upgrade head`
4. Update schemas in `app/schemas/`
5. Update repository methods if needed
6. Update tests

### Debugging

```bash
# Run with detailed logging
uvicorn main:app --reload --log-level debug
```

Set breakpoints in route handlers to inspect Request objects. FastAPI automatically formats exceptions as JSON responses.

## Multi-Tenancy Support

This service includes **built-in multi-tenancy support** through JWT token claims, enabling tenant isolation in multi-tenant applications.

### How It Works

Every JWT access token includes a `tenant_id` claim:
```json
{
  "sub": "123",
  "email": "user@example.com",
  "tenant_id": "1",
  "scopes": [],
  "iat": 1234567890,
  "exp": 1234568790
}
```

### Default Behavior

- **Single-tenant mode** (default): All tokens use `tenant_id=1` (shared tenant)
- No database changes required for single-tenant deployments
- Multi-tenant features are **opt-in** and backward compatible

### Implementation in JWT Service

The `create_access_token` function in `app/services/jwt_service.py` includes:

```python
def create_access_token(
    user_id: int,
    email: str,
    scopes: list[str] | None = None,
    audience: str | None = None,
    tenant_id: int = 1,  # Defaults to shared tenant
) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "tenant_id": str(tenant_id),  # Always included in token
        "exp": expires_at,
        "iat": now,
        "scopes": scopes or [],
    }
    # ...
```

### Enabling Multi-Tenancy

To enable multi-tenant mode, extend the service as follows:

#### 1. Add Tenant ID to User Model

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)  # Add this
    # ... rest of fields
```

#### 2. Update Database Migration

```bash
alembic revision --autogenerate -m "Add tenant_id to users"
alembic upgrade head
```

#### 3. Pass Tenant ID During Token Creation

```python
# app/services/auth_service.py - modify create_tokens()
def create_tokens(db: Session, user: User, ...) -> tuple[str, str]:
    access_token = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        scopes=scopes,
        tenant_id=user.tenant_id,  # Pass user's tenant ID
    )
    # ...
```

#### 4. Add Tenant Validation in Dependencies

```python
# app/dependencies.py - enhance get_current_user()
async def get_current_user(...) -> User:
    # ... existing token validation ...

    # Extract and validate tenant_id
    token_tenant_id = int(payload.get("tenant_id", 1))

    if hasattr(user, 'tenant_id') and user.tenant_id != token_tenant_id:
        raise AuthorizationError("User does not belong to this tenant")

    return user
```

#### 5. Add Tenant Filtering to Queries

```python
# app/repositories/user_repository.py
def get_by_email(db: Session, email: str, tenant_id: int | None = None) -> User | None:
    query = db.query(User).filter(User.email == email)

    if tenant_id is not None:
        query = query.filter(User.tenant_id == tenant_id)

    return query.first()
```

### Multi-Tenant Use Cases

**SaaS Applications**:
- Multiple organizations sharing the same service
- Each organization's data is isolated by `tenant_id`
- Single codebase, separate data per tenant
- Example: Company A (tenant_id=100) cannot access Company B's data (tenant_id=200)

**Enterprise Deployments**:
- Department-level isolation within an organization
- Different access levels per tenant
- Centralized authentication with distributed authorization

**Development Environments**:
- Separate `tenant_id` for dev (1), staging (2), production (3+)
- Test tenant isolation without changing code

### Security Considerations

1. **Token Validation**: Always verify `tenant_id` matches the user's tenant in the database
2. **Query Filtering**: Include `tenant_id` in all database queries to prevent cross-tenant data access
3. **Audit Logging**: Log `tenant_id` in all authentication and authorization events
4. **Admin Routes**: Create special admin endpoints that can access multiple tenants if needed
5. **Index Optimization**: Add database indexes on `tenant_id` for better query performance

### Testing Multi-Tenancy

Example test for tenant isolation:

```python
def test_user_cannot_access_different_tenant_data():
    # Create users in different tenants
    user_tenant_1 = create_user(email="user1@example.com", tenant_id=1)
    user_tenant_2 = create_user(email="user2@example.com", tenant_id=2)

    # User 1 gets token with tenant 1
    token_1 = create_access_token(
        user_id=user_tenant_1.id,
        email=user_tenant_1.email,
        tenant_id=1
    )

    # Verify tenant_id is in token
    payload = decode_access_token(token_1)
    assert payload["tenant_id"] == "1"
    assert payload["email"] == "user1@example.com"

    # With proper tenant filtering, user 1 cannot access user 2's data
    # even though both are valid users
```

### Migration Path

For existing deployments without multi-tenancy:

1. **Phase 1**: Code is already multi-tenancy ready with `tenant_id=1` default
2. **Phase 2**: Add `tenant_id` column to users table when needed
3. **Phase 3**: Implement tenant validation in dependencies
4. **Phase 4**: Add tenant filtering to all repository queries
5. **Phase 5**: Update registration to assign tenant IDs

**No breaking changes required** - the default `tenant_id=1` maintains backward compatibility.

## Important Notes

### Configuration Management
All settings are managed via `app/config.py` using pydantic-settings:
- Environment variables are loaded from `.env` file
- Settings are cached using `@lru_cache` decorator
- The `SECRET_KEY` must be at least 32 characters (validated on startup)
- Access via `from app.config import settings`

### Exception Handling
Custom exceptions are handled globally in `main.py`:
- `AuthenticationError` → 401 Unauthorized
- `AuthorizationError` → 403 Forbidden
- `TOTPError` → 400 Bad Request
- Routes should raise these custom exceptions, not HTTPException

### Virtual Environment
**Always activate the virtual environment** before running commands:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

For detailed troubleshooting and first-time setup, see `docs/RUNNING.md` - it includes verification steps, common database issues, and recommended setup flow.

## Additional Documentation

- **README.md** - Overview, features, API endpoints with examples
- **docs/RUNNING.md** - Quick start guide with troubleshooting
- **docs/PLAN.md** - Implementation plan and architecture decisions
- **Swagger UI** - http://127.0.0.1:8000/docs (interactive API testing)
- **FastAPI Docs** - https://fastapi.tiangolo.com
- **SQLAlchemy 2.0** - https://docs.sqlalchemy.org
- **MCP Specification** - https://modelcontextprotocol.io