# MCP-Compatible Authentication Service - Implementation Plan

## ⚠️ NOTE: This document describes the original single-user implementation

**For the current tenant-based refactoring in progress, see [TENANT_REFACTORING.md](./TENANT_REFACTORING.md)**

This document describes the original implementation plan for basic single-user authentication. The service is currently being refactored to support tenant-based multi-user authentication (40% complete).

---

## Overview

Build a production-ready FastAPI authentication service with:
- User registration and login
- OAuth2/JWT tokens (MCP-compatible)
- TOTP-based 2FA
- Protected MCP resource endpoints
- Comprehensive test coverage

**Technology Stack:**
- FastAPI + Uvicorn
- SQLite + SQLAlchemy + Alembic
- python-jose (JWT)
- passlib (password hashing)
- pyotp + qrcode (2FA)
- pytest (testing)

## Architecture

```
MCP Clients → FastAPI App → SQLite
              ├── Routes Layer (API endpoints)
              ├── Services Layer (business logic)
              ├── Repositories Layer (data access)
              └── Models Layer (database schema)
```

## Final Project Structure

```
MCP_Auth/
├── main.py                          # FastAPI app initialization
├── pyproject.toml                   # Dependencies
├── .env.example                     # Environment template
├── .gitignore
├── alembic.ini                      # Migration config
├── alembic/versions/                # Database migrations
├── app/
│   ├── config.py                    # Settings management
│   ├── database.py                  # DB session management
│   ├── dependencies.py              # FastAPI dependencies
│   ├── models/
│   │   ├── user.py                  # User table
│   │   └── token.py                 # RefreshToken table
│   ├── schemas/
│   │   ├── user.py                  # UserCreate, UserResponse
│   │   ├── auth.py                  # TokenResponse, LoginRequest
│   │   └── totp.py                  # TOTP schemas
│   ├── repositories/
│   │   ├── user_repository.py       # User CRUD
│   │   └── token_repository.py      # Token CRUD
│   ├── services/
│   │   ├── auth_service.py          # Registration, login logic
│   │   ├── jwt_service.py           # JWT creation/validation
│   │   ├── totp_service.py          # 2FA logic
│   │   └── oauth2_service.py        # MCP OAuth 2.1 metadata
│   ├── routes/
│   │   ├── auth.py                  # /auth/* endpoints
│   │   ├── protected.py             # /api/protected/* endpoints
│   │   └── well_known.py            # /.well-known/* (MCP metadata)
│   └── core/
│       ├── security.py              # Password hashing
│       └── exceptions.py            # Custom exceptions
└── tests/
    ├── conftest.py                  # Test fixtures
    ├── unit/
    │   ├── test_auth_service.py
    │   ├── test_jwt_service.py
    │   ├── test_totp_service.py
    │   └── test_security.py
    └── integration/
        ├── test_auth_endpoints.py
        ├── test_protected_endpoints.py
        └── test_totp_flow.py
```

## Implementation Phases

### Phase 1: Foundation (Steps 1-6)

**Step 1: Dependencies & Environment** ✅ COMPLETED
- Update `pyproject.toml` with dependencies:
  - sqlalchemy>=2.0.36, alembic>=1.14.0
  - python-jose[cryptography]>=3.3.0
  - passlib[bcrypt]>=1.7.4
  - python-multipart>=0.0.19
  - pydantic-settings>=2.7.0
  - pyotp>=2.9.0, qrcode[pil]>=8.0
  - python-dotenv>=1.0.1
  - Dev: pytest>=8.3.4, pytest-asyncio>=0.25.2, httpx>=0.28.1
- Run `uv sync`
- Create `.env.example` with DATABASE_URL, SECRET_KEY, token expiration times
- Create `.gitignore` (include `.env`, `*.db`, `__pycache__/`)

**Step 2: Configuration**
- Create `app/config.py` using pydantic-settings
  - Settings: DATABASE_URL, SECRET_KEY, JWT settings, TOTP issuer name

**Step 3: Database Setup**
- Create `app/database.py`:
  - SQLAlchemy engine (SQLite)
  - SessionLocal factory
  - Base declarative class
  - get_db() dependency
- Initialize Alembic: `alembic init alembic`
- Configure `alembic/env.py` to import models

**Step 4: Core Utilities**
- Create `app/core/security.py`:
  - hash_password(password) → bcrypt hash
  - verify_password(plain, hashed) → bool
- Create `app/core/exceptions.py`:
  - Custom exceptions: AuthenticationError, AuthorizationError, TOTPError

**Step 5: Database Models**
- Create `app/models/user.py`:
  - User table: id, email, password_hash, totp_secret, is_totp_enabled, created_at, updated_at, is_active
- Create `app/models/token.py`:
  - RefreshToken table: id, user_id, token, client_id, scope, is_revoked, expires_at, created_at

**Step 6: Initial Migration**
- Run `alembic revision --autogenerate -m "Initial schema"`
- Review migration
- Run `alembic upgrade head`

### Phase 2: Data Layer (Steps 7-8)

**Step 7: User Repository**
- Create `app/repositories/user_repository.py`:
  - create(email, password_hash) → User
  - get_by_id(user_id) → User | None
  - get_by_email(email) → User | None
  - update_totp_secret(user_id, secret) → User
  - enable_totp(user_id) → User

**Step 8: Token Repository**
- Create `app/repositories/token_repository.py`:
  - create_refresh_token(user_id, token, expires_at, client_id, scope) → RefreshToken
  - get_by_token(token) → RefreshToken | None
  - revoke_token(token)
  - revoke_all_user_tokens(user_id)

### Phase 3: Business Logic (Steps 9-12)

**Step 9: JWT Service**
- Create `app/services/jwt_service.py`:
  - create_access_token(user_id, email, scopes, audience) → JWT string
    - Payload: sub, email, exp, iat, scopes, aud
    - Sign with HS256
  - create_refresh_token() → random token (32 bytes)
  - decode_access_token(token) → dict (validate signature/expiration)

**Step 10: TOTP Service**
- Create `app/services/totp_service.py`:
  - generate_secret() → base32 string
  - get_provisioning_uri(email, secret) → otpauth:// URI
  - generate_qr_code(uri) → base64 PNG
  - verify_code(secret, code) → bool

**Step 11: Auth Service**
- Create `app/services/auth_service.py`:
  - register_user(email, password) → User
  - authenticate_user(email, password) → User
  - create_tokens(user, client_id, scope) → (access_token, refresh_token)
  - refresh_access_token(refresh_token) → (new_access_token, new_refresh_token)

**Step 12: OAuth2 Service (MCP)**
- Create `app/services/oauth2_service.py`:
  - get_authorization_server_metadata() → RFC 8414 metadata dict
    - Includes PKCE support, resource indicators (RFC 8707)

### Phase 4: API Schemas (Steps 13-15)

**Step 13: User Schemas**
- Create `app/schemas/user.py`:
  - UserCreate: email (EmailStr), password (min 8 chars)
  - UserResponse: id, email, is_totp_enabled, created_at
  - UserUpdate: optional profile fields

**Step 14: Auth Schemas**
- Create `app/schemas/auth.py`:
  - LoginRequest: email, password
  - TokenResponse: access_token, refresh_token, token_type, expires_in
  - RefreshRequest: refresh_token

**Step 15: TOTP Schemas**
- Create `app/schemas/totp.py`:
  - TOTPSetupResponse: secret, provisioning_uri, qr_code
  - TOTPVerifyRequest: code (6 digits)
  - TOTPValidateRequest: email, password, totp_code

### Phase 5: API Endpoints (Steps 16-19)

**Step 16: Dependencies**
- Create `app/dependencies.py`:
  - get_current_user(token: str) → User (decode JWT, validate user)
  - require_totp_disabled(user: User) → User (prevent TOTP re-setup)

**Step 17: Auth Routes**
- Create `app/routes/auth.py` (prefix `/auth`):
  - POST /register → register user
  - POST /login → authenticate, return tokens (or require TOTP)
  - POST /refresh → refresh access token
  - POST /logout → revoke refresh token
  - POST /totp/setup → generate TOTP secret + QR code
  - POST /totp/verify → verify TOTP code, enable 2FA
  - POST /totp/validate → validate email+password+TOTP, issue tokens

**Step 18: Protected Routes**
- Create `app/routes/protected.py` (prefix `/api/protected`):
  - GET /me → return current user info (requires auth)
  - PATCH /profile → update profile (placeholder)

**Step 19: Well-Known Routes**
- Create `app/routes/well_known.py` (prefix `/.well-known`):
  - GET /oauth-authorization-server → MCP OAuth 2.1 metadata

### Phase 6: Application Assembly (Steps 20-21)

**Step 20: Update main.py**
- Initialize FastAPI with custom metadata:
  - Title: "MCP-Compatible Auth Service"
  - OAuth2 security schemes with PKCE
- Include routers: auth, protected, well_known
- Add exception handlers
- Add CORS middleware

**Step 21: Custom OpenAPI**
- Tag endpoints (Auth, Protected, MCP Metadata)
- Add security definitions
- Add request/response examples
- Document MCP-specific features

### Phase 7: Testing (Steps 22-26)

**Step 22: Test Setup**
- Create `tests/conftest.py`:
  - Fixtures: test_db, client, test_user, authenticated_client, user_with_totp

**Step 23: Unit Tests - Security**
- Create `tests/unit/test_security.py`:
  - Test password hashing and verification

**Step 24: Unit Tests - Services**
- Create `tests/unit/test_jwt_service.py`: JWT creation, decoding, expiration
- Create `tests/unit/test_totp_service.py`: TOTP generation, verification, QR codes
- Create `tests/unit/test_auth_service.py`: registration, login, token flows

**Step 25: Integration Tests - Auth**
- Create `tests/integration/test_auth_endpoints.py`:
  - Test registration, login, refresh, logout flows

**Step 26: Integration Tests - TOTP & Protected**
- Create `tests/integration/test_totp_flow.py`:
  - Test TOTP setup, verification, validation during login
- Create `tests/integration/test_protected_endpoints.py`:
  - Test protected endpoints with/without valid tokens

### Phase 8: Documentation (Step 27)

**Step 27: Documentation**
- Update CLAUDE.md with architecture, commands, testing
- Document MCP OAuth 2.1 compliance
- Document environment variables
- Add API usage examples

## Key API Endpoints

### Authentication (`/auth/*`)
- POST /auth/register - User registration
- POST /auth/login - Email/password login
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Revoke refresh token
- POST /auth/totp/setup - Generate TOTP QR code
- POST /auth/totp/verify - Verify TOTP, enable 2FA
- POST /auth/totp/validate - Login with TOTP

### Protected Resources (`/api/protected/*`)
- GET /api/protected/me - Get current user (requires JWT)

### MCP Metadata (`/.well-known/*`)
- GET /.well-known/oauth-authorization-server - OAuth 2.1 metadata

## Database Schema

### Users Table
```sql
id: Integer (PK)
email: String(255) (unique, indexed)
password_hash: String(255)
totp_secret: String(32) (nullable)
is_totp_enabled: Boolean (default: False)
created_at: DateTime
updated_at: DateTime
is_active: Boolean (default: True)
```

### RefreshTokens Table
```sql
id: Integer (PK)
user_id: Integer (FK → users.id)
token: String(255) (unique, indexed)
client_id: String(255) (nullable)
scope: String(500) (nullable)
is_revoked: Boolean (default: False)
expires_at: DateTime
created_at: DateTime
```

## JWT Structure (MCP-Compatible)

```json
{
  "sub": "123",
  "email": "user@example.com",
  "exp": 1735689600,
  "iat": 1735686000,
  "scopes": ["read:profile"],
  "aud": "https://your-domain.com/api/protected"
}
```

## MCP OAuth 2.1 Compliance

- ✅ PKCE required (S256 method)
- ✅ Resource indicators (RFC 8707) - `aud` claim in JWT
- ✅ Metadata endpoint (RFC 8414)
- ✅ Refresh token rotation
- ✅ No client secrets (PKCE-only)

## Testing Strategy

**Unit Tests:**
- Security utilities (password hashing)
- All service methods (auth, JWT, TOTP)
- Repository CRUD operations

**Integration Tests:**
- Complete user flows (registration → login → protected access)
- TOTP setup and verification
- Token refresh and rotation
- Error cases (invalid credentials, expired tokens)

**Test Database:**
- In-memory SQLite for speed
- Fixtures for consistent data
- Reset between tests

## Critical Files for Implementation

1. **app/services/auth_service.py** - Core authentication orchestration
2. **app/services/jwt_service.py** - JWT creation with MCP compliance
3. **app/routes/auth.py** - Main authentication API surface
4. **app/routes/well_known.py** - MCP metadata endpoint
5. **app/dependencies.py** - Security boundary for protected endpoints

## Development Workflow

1. Implement foundation (config, database, models)
2. Build data layer (repositories)
3. Build business logic (services)
4. Create API schemas
5. Implement routes
6. Write tests for each layer
7. Document and refine

## Security Considerations

- Bcrypt password hashing (cost factor 12)
- JWT with HS256 signing
- TOTP with time-based validation window
- Refresh token rotation on refresh
- Secure random token generation (32 bytes)
- SQLAlchemy ORM for SQL injection protection
- Pydantic validation for XSS protection
- HTTPS required in production
- SECRET_KEY must be 256-bit minimum
- Rate limiting on auth endpoints (future)

## Environment Variables (.env.example)

```
DATABASE_URL=sqlite:///./mcp_auth.db
SECRET_KEY=your-secret-key-here-min-256-bits
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
TOTP_ISSUER_NAME=MCP Auth Service
```

## Extension Points

- Email verification
- Password reset flow
- Full OAuth2 authorization endpoint
- Multiple TOTP devices + backup codes
- RBAC (roles and permissions)
- Audit logging
- Rate limiting (Redis)
- WebAuthn/Passkeys
- Session management
