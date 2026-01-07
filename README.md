# MCP-Compatible Authentication Service

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.126+-green.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-407%20passing-brightgreen.svg)](./tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready FastAPI authentication service implementing OAuth 2.1 with full Model Context Protocol (MCP) compliance and **tenant-based multi-user architecture**.

## 🚧 REFACTORING IN PROGRESS (40% Complete)

**This service is being refactored from single-user to tenant-based multi-user authentication.**

**Current Status**: Database schema and core services complete. API endpoints pending.

See [docs/TENANT_REFACTORING.md](docs/TENANT_REFACTORING.md) for complete refactoring status and architecture changes.

## Features

- 🏢 **Tenant-Based Authentication** - Multi-tenant architecture with auto-tenant creation
- 🔐 **Secure Authentication** - Bcrypt password hashing for tenants and users
- 👥 **Multi-User Support** - Users with roles (OWNER, ADMIN, MEMBER) within tenants
- 🎫 **JWT Tokens** - Short-lived access tokens (15 min) with refresh token rotation
- 🔑 **TOTP 2FA** - Time-based One-Time Password authentication with QR code setup
- 🌐 **MCP OAuth 2.1** - Full compliance with Model Context Protocol specifications
- 👤 **User Management** - Protected endpoints for profile management
- ✅ **Comprehensive Testing** - 407 passing tests (348 unit + 59 integration)
- 📚 **Interactive API Docs** - Swagger UI and ReDoc included

## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/jtuchinsky/MCP_Auth.git
cd MCP_Auth

# Create environment file
cp .env.example .env

# Generate a secure secret key and update .env
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# Install dependencies
uv sync --extra dev

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Architecture Overview

### Tenant-Based Authentication

This service implements a **tenant-first authentication model**:

1. **Tenants** are identified by globally unique email addresses with their own passwords
2. **Users** belong to tenants and have usernames unique within their tenant
3. **First login** with a new email automatically creates a tenant + owner user
4. **Owner users** have the same credentials as their tenant and role=OWNER
5. **Additional users** can be invited by tenant owners (future feature)

### Authentication Flow

```
POST /auth/login (tenant_email, password)
  ↓
  Look up Tenant by email
  ↓
  ┌─────────────────┬─────────────────┐
  │ NOT FOUND       │ FOUND           │
  ├─────────────────┼─────────────────┤
  │ Create Tenant   │ Verify Password │
  │ Create Owner    │ Get Owner User  │
  │ Return Tokens   │ Return Tokens   │
  └─────────────────┴─────────────────┘
```

## Usage Examples

### 1. First Login (Auto-Creates Tenant + Owner)

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "company@example.com",
    "password": "securepassword123"
  }'
```

**What happens**:
- New tenant created with email `company@example.com`
- Owner user created with same credentials, role=OWNER
- Returns JWT tokens for owner user

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 900
}
```

JWT Payload includes:
```json
{
  "sub": "1",
  "email": "company@example.com",
  "tenant_id": "2",
  "role": "OWNER",
  "exp": 1735689600
}
```

### 2. Subsequent Login (Existing Tenant)

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "company@example.com",
    "password": "securepassword123"
  }'
```

**What happens**:
- Tenant found, password verified
- Returns JWT tokens for existing owner user

### 3. Access Protected Endpoint

```bash
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response includes tenant and role information:
```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "company@example.com",
  "email": "company@example.com",
  "role": "OWNER",
  "is_totp_enabled": false,
  "is_active": true
}
```

### 4. Setup TOTP 2FA

```bash
curl -X POST "http://127.0.0.1:8000/auth/totp/setup" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response includes QR code for authenticator app setup.

### 5. Login with TOTP

```bash
curl -X POST "http://127.0.0.1:8000/auth/totp/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "totp_code": "123456"
  }'
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required | Status |
|--------|----------|-------------|---------------|--------|
| POST | `/auth/login` | Login as tenant (auto-creates if new) | No | 🚧 Pending |
| POST | `/auth/login-user` | Login as user within tenant | No | 🚧 Pending |
| POST | `/auth/refresh` | Refresh access token | No | 🚧 Pending |
| POST | `/auth/logout` | Logout and revoke token | No | 🚧 Pending |
| POST | `/auth/register` | ⚠️ Deprecated - use `/auth/login` | No | ⚠️ Legacy |

### TOTP/2FA

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/totp/setup` | Generate TOTP secret & QR code | Yes |
| POST | `/auth/totp/verify` | Verify TOTP code to enable 2FA | Yes |
| POST | `/auth/totp/validate` | Login with TOTP (2FA users) | No |

### Protected Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/protected/me` | Get current user profile | Yes |
| PATCH | `/api/protected/profile` | Update user profile | Yes |

### MCP Metadata

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/.well-known/oauth-authorization-server` | OAuth 2.1 metadata | No |

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

**Test Coverage**: 407 passing tests
- Unit Tests: 348 tests (security, JWT, TOTP, auth service, tenant repository, tenant service)
- Integration Tests: 59 tests (auth endpoints, TOTP flows, protected routes)

## Architecture

The service follows a layered architecture pattern:

```
Routes (API Layer)
    ↓
Services (Business Logic)
    ↓
Repositories (Data Access)
    ↓
Models (Database)
```

### Key Technologies

- **FastAPI** - Modern, high-performance web framework
- **SQLAlchemy 2.0** - Database ORM with Alembic migrations
- **PyJWT** - JSON Web Token implementation
- **bcrypt** - Secure password hashing (12 rounds)
- **pyotp** - TOTP/2FA implementation
- **Pydantic** - Data validation and settings management

### Database Schema

**Tenants Table** (NEW):
- `id` - Auto-incremented primary key
- `email` - Globally unique, identifies tenant
- `password_hash` - Bcrypt hashed password
- `is_active` - Tenant status
- `created_at`, `updated_at` - Timestamps

**Users Table** (UPDATED):
- `id` - Auto-incremented primary key (global)
- `tenant_id` - Foreign key to tenants (with cascade delete)
- `username` - Unique per tenant
- `email` - Globally unique (for notifications/invitations)
- `password_hash` - Bcrypt hashed password
- `role` - OWNER, ADMIN, or MEMBER
- `is_totp_enabled`, `totp_secret` - 2FA fields
- `is_active` - User status

**Composite Unique Constraint**: `(tenant_id, username)` ensures usernames are unique within each tenant.

## MCP OAuth 2.1 Compliance

This service implements the following OAuth 2.1 features:

- ✅ **PKCE Required** (RFC 7636) - Proof Key for Code Exchange
- ✅ **Resource Indicators** (RFC 8707) - Audience claims in tokens
- ✅ **Authorization Server Metadata** (RFC 8414) - Discovery endpoint
- ✅ **Refresh Token Rotation** - Enhanced security through rotation
- ✅ **TOTP 2FA Support** - Multi-factor authentication
- ✅ **Multi-Tenancy Support** - JWT tokens include `tenant_id` claims for tenant isolation

## Security Features

- **Password Security**: bcrypt hashing (12 rounds) with automatic salts for both tenants and users
- **JWT Tokens**: HS256 signing with configurable expiration, includes `tenant_id` and `role` claims
- **Tenant Isolation**: All users belong to a tenant, enforced at database and JWT level
- **Role-Based Access**: OWNER, ADMIN, MEMBER roles for authorization
- **Refresh Tokens**: Database-backed with rotation and revocation
- **TOTP/2FA**: RFC 6238 compliant with QR code generation
- **Input Validation**: Comprehensive Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM parameterization
- **Email Normalization**: All emails normalized to lowercase for consistency
- **Case-Insensitive Lookups**: Tenant authentication is case-insensitive

## Configuration

All configuration is managed through environment variables in `.env`:

```bash
# Database
DATABASE_URL=sqlite:///./mcp_auth.db

# JWT Configuration
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# TOTP
TOTP_ISSUER_NAME=MCP Auth Service
```

## Project Structure

```
MCP_Auth/
├── app/
│   ├── core/          # Security utilities and exceptions
│   ├── models/        # SQLAlchemy ORM models
│   │   ├── tenant.py      # NEW: Tenant model
│   │   ├── user.py        # UPDATED: Added tenant_id, username, role
│   │   └── token.py       # RefreshToken model
│   ├── repositories/  # Database operations
│   │   ├── tenant_repository.py  # NEW: Tenant CRUD
│   │   ├── user_repository.py    # UPDATED: Tenant-scoped queries
│   │   └── token_repository.py   # Token CRUD
│   ├── routes/        # API endpoints
│   ├── schemas/       # Pydantic models
│   ├── services/      # Business logic
│   │   ├── tenant_service.py  # NEW: Tenant auth with auto-creation
│   │   ├── auth_service.py    # PENDING: Needs tenant_id updates
│   │   ├── jwt_service.py     # PENDING: Needs role parameter
│   │   └── totp_service.py    # TOTP/2FA logic
│   ├── config.py      # Settings management
│   ├── database.py    # Database setup
│   └── dependencies.py # FastAPI dependencies
├── alembic/           # Database migrations
│   └── versions/
│       └── e9258cf92b4d_add_tenant_based_authentication.py  # NEW
├── tests/             # Test suite
│   ├── unit/          # Unit tests
│   │   ├── test_tenant_repository.py  # NEW: 13 tests
│   │   └── test_tenant_service.py     # NEW: 10 tests
│   └── integration/   # Integration tests
├── docs/
│   ├── TENANT_REFACTORING.md  # NEW: Refactoring status
│   ├── RUNNING.md
│   └── PLAN.md
├── main.py            # FastAPI application
└── pyproject.toml     # Project configuration
```

## Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

The project follows these conventions:
- **Type hints** for all function signatures
- **Async/await** for all route handlers
- **Repository pattern** for data access
- **Dependency injection** via FastAPI
- **Comprehensive docstrings** for all modules

## Production Deployment

### Checklist

- [ ] Set strong `SECRET_KEY` (32+ random characters)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure CORS for specific origins
- [ ] Enable HTTPS/TLS
- [ ] Set up logging and monitoring
- [ ] Implement rate limiting
- [ ] Configure backup strategy
- [ ] Review token expiration times

### Example Production Setup

```bash
# Install production dependencies only
uv sync

# Use production database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Run with production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Troubleshooting

### Common Issues

**No such table error**
```bash
alembic upgrade head
```

**Module not found**
```bash
uv sync --extra dev
```

**TOTP codes not working**
- Ensure system time is synchronized (TOTP is time-based)

**401 Unauthorized**
- Check `Authorization: Bearer {token}` header format

## Documentation

- **Refactoring Status**: See [docs/TENANT_REFACTORING.md](./docs/TENANT_REFACTORING.md) - **READ THIS FIRST**
- **Database Schema**: See [docs/SCHEMAS.md](./docs/SCHEMAS.md) - Complete schema documentation
- **Developer Guide**: See [CLAUDE.md](./CLAUDE.md)
- **Quick Start**: See [docs/RUNNING.md](./docs/RUNNING.md)
- **Original Implementation Plan**: See [docs/PLAN.md](./docs/PLAN.md)
- **API Documentation**: http://127.0.0.1:8000/docs (when running)

## Contributing

Contributions are welcome! Please:

1. Follow existing code structure and conventions
2. Write tests for new features
3. Update documentation
4. Ensure all tests pass: `pytest`
5. Use clear commit messages

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [OAuth 2.1 Specification](https://oauth.net/2.1/)
- [RFC 6238 (TOTP)](https://tools.ietf.org/html/rfc6238)
- [RFC 8414 (OAuth Metadata)](https://tools.ietf.org/html/rfc8414)
- [Model Context Protocol](https://modelcontextprotocol.io)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

Built with [FastAPI](https://fastapi.tiangolo.com), following OAuth 2.1 and MCP specifications for secure authentication and authorization.

---

**Note**: This is a reference implementation for educational and development purposes. Review security considerations and customize for your production needs.