# MCP-Compatible Authentication Service

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.126+-green.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-384%20passing-brightgreen.svg)](./tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready FastAPI authentication service implementing OAuth 2.1 with full Model Context Protocol (MCP) compliance.

## Features

- 🔐 **Secure Authentication** - User registration and login with bcrypt password hashing
- 🎫 **JWT Tokens** - Short-lived access tokens (15 min) with refresh token rotation
- 🔑 **TOTP 2FA** - Time-based One-Time Password authentication with QR code setup
- 🏢 **Multi-Tenancy Ready** - Built-in tenant isolation via JWT `tenant_id` claims (opt-in)
- 🌐 **MCP OAuth 2.1** - Full compliance with Model Context Protocol specifications
- 👤 **User Management** - Protected endpoints for profile management
- ✅ **Comprehensive Testing** - 384 passing tests (325 unit + 59 integration)
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

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### 2. Login

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3. Access Protected Endpoint

```bash
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
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

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Create new user account | No |
| POST | `/auth/login` | Login (users without TOTP) | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout and revoke token | No |

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

**Test Coverage**: 384 passing tests
- Unit Tests: 325 tests (security, JWT, TOTP, auth service)
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
- **bcrypt** - Secure password hashing
- **pyotp** - TOTP/2FA implementation
- **Pydantic** - Data validation and settings management

## MCP OAuth 2.1 Compliance

This service implements the following OAuth 2.1 features:

- ✅ **PKCE Required** (RFC 7636) - Proof Key for Code Exchange
- ✅ **Resource Indicators** (RFC 8707) - Audience claims in tokens
- ✅ **Authorization Server Metadata** (RFC 8414) - Discovery endpoint
- ✅ **Refresh Token Rotation** - Enhanced security through rotation
- ✅ **TOTP 2FA Support** - Multi-factor authentication
- ✅ **Multi-Tenancy Support** - JWT tokens include `tenant_id` claims for tenant isolation

## Security Features

- **Password Security**: bcrypt hashing with automatic salts
- **JWT Tokens**: HS256 signing with configurable expiration
- **Multi-Tenancy**: Built-in `tenant_id` claims for tenant isolation (defaults to tenant 1)
- **Refresh Tokens**: Database-backed with rotation and revocation
- **TOTP/2FA**: RFC 6238 compliant with QR code generation
- **Input Validation**: Comprehensive Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM parameterization

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
│   ├── repositories/  # Database operations
│   ├── routes/        # API endpoints
│   ├── schemas/       # Pydantic models
│   ├── services/      # Business logic
│   ├── config.py      # Settings management
│   ├── database.py    # Database setup
│   └── dependencies.py # FastAPI dependencies
├── alembic/           # Database migrations
├── tests/             # Test suite
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
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

- **Developer Guide**: See [CLAUDE.md](./CLAUDE.md)
- **Implementation Plan**: See [docs/PLAN.md](./docs/PLAN.md)
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