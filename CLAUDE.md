# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MCP-Compatible Authentication Service** - A production-ready FastAPI authentication service implementing OAuth 2.1 with Model Context Protocol (MCP) compliance.

Version: 0.1.0

This service provides secure user authentication, JWT-based access control, TOTP two-factor authentication, and full OAuth 2.1 compliance for MCP clients.

## Features

- ✅ **User Registration & Login** - Secure account creation with bcrypt password hashing
- ✅ **JWT Access Tokens** - Short-lived tokens (15 minutes) with HS256 signing
- ✅ **Refresh Tokens** - Long-lived tokens (30 days) with automatic rotation
- ✅ **TOTP 2FA** - Time-based One-Time Password authentication with QR code generation
- ✅ **MCP OAuth 2.1 Compliance** - Full support for MCP authorization flows
- ✅ **Protected Endpoints** - User profile management with JWT authentication
- ✅ **Token Rotation** - Refresh tokens are rotated on each use for enhanced security
- ✅ **Comprehensive Testing** - 383 passing tests (325 unit + 59 integration)

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (Routes)                    │
│  /auth/*  |  /api/protected/*  |  /.well-known/*       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Business Logic Layer (Services)             │
│  auth_service  |  jwt_service  |  totp_service  |  ...  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Data Access Layer (Repositories)            │
│         user_repository  |  token_repository            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Database Layer (Models)                │
│              User  |  RefreshToken (SQLite)              │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Routes** (`app/routes/`) - FastAPI endpoint handlers
   - `auth.py` - Authentication endpoints (register, login, TOTP)
   - `protected.py` - Protected user profile endpoints
   - `well_known.py` - OAuth 2.1 metadata discovery

2. **Services** (`app/services/`) - Business logic
   - `auth_service.py` - User authentication and token management
   - `jwt_service.py` - JWT token creation and validation
   - `totp_service.py` - TOTP secret generation and verification
   - `oauth2_service.py` - MCP OAuth 2.1 metadata

3. **Repositories** (`app/repositories/`) - Database operations
   - `user_repository.py` - User CRUD operations
   - `token_repository.py` - Refresh token management

4. **Models** (`app/models/`) - SQLAlchemy ORM models
   - `user.py` - User table with TOTP support
   - `token.py` - RefreshToken table with revocation

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
│   │   ├── user.py           # User ORM model
│   │   └── token.py          # RefreshToken ORM model
│   ├── repositories/
│   │   ├── user_repository.py    # User database operations
│   │   └── token_repository.py   # Token database operations
│   ├── routes/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── protected.py      # Protected user endpoints
│   │   └── well_known.py     # OAuth 2.1 metadata
│   ├── schemas/
│   │   ├── auth.py           # Auth request/response schemas
│   │   ├── totp.py           # TOTP schemas
│   │   └── user.py           # User schemas
│   ├── services/
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── jwt_service.py    # JWT token management
│   │   ├── totp_service.py   # TOTP/2FA logic
│   │   └── oauth2_service.py # MCP metadata
│   ├── config.py             # Settings with pydantic-settings
│   ├── database.py           # SQLAlchemy setup
│   └── dependencies.py       # FastAPI dependencies
├── alembic/
│   ├── versions/             # Database migrations
│   └── env.py               # Alembic configuration
├── tests/
│   ├── unit/                # Unit tests (325 tests)
│   │   ├── test_security.py
│   │   ├── test_jwt_service.py
│   │   ├── test_totp_service.py
│   │   └── test_auth_service.py
│   ├── integration/         # Integration tests (59 tests)
│   │   ├── test_auth_endpoints.py
│   │   ├── test_totp_flow.py
│   │   └── test_protected_endpoints.py
│   └── conftest.py          # Shared test fixtures
├── docs/
│   └── PLAN.md              # Implementation plan
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

Current test coverage: **383 passing tests**

- **Unit Tests** (325 tests):
  - `test_security.py` - Password hashing (43 tests)
  - `test_jwt_service.py` - JWT token operations (75 tests)
  - `test_totp_service.py` - TOTP generation/validation (75 tests)
  - `test_auth_service.py` - Authentication logic (132 tests)

- **Integration Tests** (59 tests):
  - `test_auth_endpoints.py` - Auth API endpoints (24 tests)
  - `test_totp_flow.py` - TOTP/2FA flows (17 tests)
  - `test_protected_endpoints.py` - Protected endpoints (18 tests)

### Test Database

Integration tests use a separate SQLite database (`test_integration.db`) that is created and destroyed for each test function to ensure test isolation.

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "is_totp_enabled": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### POST /auth/login
Login with email and password (for users without TOTP).

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "abc123...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### POST /auth/refresh
Refresh an access token using a refresh token.

**Request:**
```json
{
  "refresh_token": "abc123..."
}
```

**Response:** `200 OK` (same format as /auth/login)

#### POST /auth/logout
Revoke a refresh token (logout).

**Request:**
```json
{
  "refresh_token": "abc123..."
}
```

**Response:** `204 No Content`

### TOTP/2FA Endpoints

#### POST /auth/totp/setup
Setup TOTP 2FA for the authenticated user.

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/...",
  "qr_code": "iVBORw0KGgo..."
}
```

#### POST /auth/totp/verify
Verify TOTP code and enable 2FA.

**Headers:** `Authorization: Bearer {access_token}`

**Request:**
```json
{
  "totp_code": "123456"
}
```

**Response:** `200 OK` (UserResponse with `is_totp_enabled: true`)

#### POST /auth/totp/validate
Login with email, password, and TOTP code (for users with 2FA enabled).

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "totp_code": "123456"
}
```

**Response:** `200 OK` (same format as /auth/login)

### Protected Endpoints

#### GET /api/protected/me
Get current authenticated user's information.

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "is_totp_enabled": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### PATCH /api/protected/profile
Update user profile (email and/or password).

**Headers:** `Authorization: Bearer {access_token}`

**Request:**
```json
{
  "email": "newemail@example.com",
  "password": "newpassword123"
}
```

**Response:** `200 OK` (UserResponse with updated data)

### MCP Metadata Endpoint

#### GET /.well-known/oauth-authorization-server
OAuth 2.1 authorization server metadata (RFC 8414 compliant).

**Response:** `200 OK`
```json
{
  "issuer": "http://localhost:8000",
  "authorization_endpoint": "http://localhost:8000/auth/authorize",
  "token_endpoint": "http://localhost:8000/auth/token",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "resource_indicators_supported": true,
  "mcp_version": "1.0",
  "mcp_features": ["oauth2.1", "pkce", "resource_indicators", "totp"]
}
```

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
- **bcrypt hashing** with automatic salt generation
- **Minimum password length**: 8 characters
- Passwords are never stored in plaintext

### JWT Security
- **HS256 algorithm** for token signing
- **Short-lived access tokens**: 15 minutes (configurable)
- **Token payload includes**: user ID, email, issued/expiry timestamps
- **Secret key validation**: Minimum 32 characters

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

### User Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_totp_enabled BOOLEAN DEFAULT FALSE,
    totp_secret VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

# Use FastAPI's built-in exception handling
# Errors are automatically formatted as JSON responses

# Access request/response in debugger
# Set breakpoint in route handler to inspect Request object
```

## Deployment Considerations

### Production Checklist

- [ ] Set strong `SECRET_KEY` in production environment
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Configure CORS `allow_origins` to specific domains (remove `["*"]`)
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Set up proper logging and monitoring
- [ ] Use environment-specific configuration files
- [ ] Implement rate limiting (e.g., with slowapi)
- [ ] Set up backup strategy for database
- [ ] Configure proper JWT expiration times for your use case
- [ ] Review and restrict API endpoint access as needed

### Environment Variables for Production

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=<very-long-random-secure-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
TOTP_ISSUER_NAME=Your Production App Name
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Run from project root, ensure virtual environment is activated

**Issue**: `sqlalchemy.exc.OperationalError: no such table`
- **Solution**: Run `alembic upgrade head` to apply migrations

**Issue**: `401 Unauthorized` on protected endpoints
- **Solution**: Ensure `Authorization: Bearer {token}` header is set

**Issue**: TOTP codes not working
- **Solution**: Check system time is synchronized (TOTP is time-based)

**Issue**: Tests fail with database errors
- **Solution**: Tests use separate database, check `tests/conftest.py`

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **SQLAlchemy 2.0 Documentation**: https://docs.sqlalchemy.org
- **Alembic Documentation**: https://alembic.sqlalchemy.org
- **JWT Introduction**: https://jwt.io/introduction
- **RFC 6238 (TOTP)**: https://tools.ietf.org/html/rfc6238
- **RFC 8414 (OAuth Metadata)**: https://tools.ietf.org/html/rfc8414
- **MCP Specification**: https://modelcontextprotocol.io

## Contributing

When contributing to this project:

1. Follow the existing code structure and conventions
2. Write tests for new features (both unit and integration)
3. Update documentation (this file and docstrings)
4. Run `pytest` to ensure all tests pass
5. Use `alembic` for any database schema changes
6. Keep commits focused and write clear commit messages

## License

MIT License - See repository for details.