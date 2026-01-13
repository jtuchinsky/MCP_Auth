# Running MCP_Auth - Quick Start Guide

This guide walks you through getting the project running from scratch.

## Prerequisites

- Python 3.12 or higher
- Git
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

## 1. Clone the Repository

```bash
git clone https://github.com/jtuchinsky/MCP_Auth.git
cd MCP_Auth
```

## 2. Set Up Environment

### Create `.env` file

```bash
# Copy the example environment file
cp .env.example .env

# Generate a secure secret key and add it to .env
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}'))" >> .env
```

Your `.env` file should now contain:
```bash
DATABASE_URL=sqlite:///./mcp_auth.db
SECRET_KEY=<your-generated-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
TOTP_ISSUER_NAME=MCP Auth Service
```

### Install Dependencies

```bash
# Using uv (recommended)
uv sync --extra dev

# OR using pip
pip install -e ".[dev]"
```

**This will create a `.venv` directory with all dependencies installed.**

### Verify Installation

```bash
# Check Python version in venv
.venv/bin/python --version

# Expected output: Python 3.12.x or higher

# Verify key packages are installed
.venv/bin/python -c "import fastapi, sqlalchemy, bcrypt; print('✓ Dependencies installed correctly')"
```

## 3. Set Up Database

### Run Database Migrations

```bash
alembic upgrade head
```

This creates the `mcp_auth.db` file with the following tables:
- `users` - User accounts
- `refresh_tokens` - JWT refresh tokens
- `alembic_version` - Migration tracking

### Verify Database Setup

```bash
# Check migration status
alembic current

# Expected output: 3972af504055 (head)

# Check tables exist
sqlite3 mcp_auth.db ".tables"

# Expected output: alembic_version  refresh_tokens  tenants  users
```

### Verify Tenant Table

Check that the tenants table exists and has the default tenant:

```bash
sqlite3 mcp_auth.db "SELECT * FROM tenants;"
```

**Expected output** (default tenant created during migration):
```
1|default@system.local|$2b$12$...|1|2026-01-07 22:06:59|2026-01-07 22:06:59
```

This default tenant (id=1) is used for backward compatibility with existing users.

## 4. Start the Server

### Activate Virtual Environment (Recommended)

**Important:** Always activate the virtual environment to ensure you're using the correct Python and dependencies.

```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

**You'll know it's activated when you see `(.venv)` at the start of your terminal prompt.**

**Alternative:** You can run commands without activating by using the full path:
```bash
.venv/bin/uvicorn main:app --reload  # macOS/Linux
.venv\Scripts\uvicorn main:app --reload  # Windows
```

### Run the Development Server

```bash
uvicorn main:app --reload
```

The server will start on `http://127.0.0.1:8000`

**Server Output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/MCP_Auth']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify Server is Running

Open your browser and visit:
- **Interactive API Docs**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc

## 5. Before Running Tests

### Option A: Run Tests with Existing Server

If the server is already running, stop it first (`Ctrl+C`), then:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

**Expected Output:**
```
======================== 383 passed in X.XXs ========================
```

### Option B: Run Tests While Server is Running

Tests use a separate test database (`test_integration.db`), so you can run tests while the server is running on port 8000.

### Clean Up Test Database (Optional)

```bash
rm test_integration.db
```

## 6. Before Calling Endpoints with curl

### Ensure Server is Running

Make sure the server is running on port 8000:
```bash
uvicorn main:app --reload
```

### Test Basic Connectivity

```bash
curl http://127.0.0.1:8000/
```

**Expected Response:**
```json
{"message": "Hello World"}
```

### Common API Workflows

#### A. First Login (Auto-Creates Tenant + Owner User)

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "company@example.com",
    "tenant_name": "Acme Corporation",
    "password": "securepassword123"
  }'
```

**What happens:**
- Creates new tenant with email `company@example.com` and name `Acme Corporation`
- Creates owner user (username=email, role=OWNER)
- Returns JWT tokens for owner user

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### B. Login

**Login as Tenant Owner (Existing Tenant):**

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "company@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Login as User Within Tenant** (Future: When Multiple Users Exist):

```bash
curl -X POST "http://127.0.0.1:8000/auth/login-user" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "company@example.com",
    "username": "alice",
    "password": "user_password"
  }'
```

#### C. Access Protected Endpoint

```bash
# Save the access token from login response
export ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "company@example.com",
  "email": "company@example.com",
  "role": "OWNER",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### D. Tenant Management

The service includes comprehensive tenant management endpoints with role-based authorization.

**Authorization Requirements:**
- **Any role** (OWNER, ADMIN, MEMBER): View tenant info
- **OWNER or ADMIN**: Update tenant name, list users
- **OWNER only**: Update tenant status, soft delete tenant

**1. View Current Tenant Info** (Any Role)

```bash
curl -X GET "http://127.0.0.1:8000/tenants/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 5,
  "email": "company@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": true,
  "created_at": "2026-01-12T15:30:00Z",
  "updated_at": "2026-01-12T15:30:00Z"
}
```

**2. Update Tenant Name** (OWNER or ADMIN)

```bash
curl -X PUT "http://127.0.0.1:8000/tenants/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Acme Corp - New Name"
  }'
```

**Response:**
```json
{
  "id": 5,
  "email": "company@example.com",
  "tenant_name": "Acme Corp - New Name",
  "is_active": true,
  "created_at": "2026-01-12T15:30:00Z",
  "updated_at": "2026-01-12T15:35:00Z"
}
```

**Authorization Error (if MEMBER tries):**
```json
{
  "detail": "Insufficient permissions. OWNER or ADMIN role required."
}
```

**3. List All Users in Tenant** (OWNER or ADMIN)

```bash
curl -X GET "http://127.0.0.1:8000/tenants/me/users" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 4,
    "tenant_id": 5,
    "username": "company@example.com",
    "email": "company@example.com",
    "role": "OWNER",
    "is_totp_enabled": false,
    "is_active": true,
    "created_at": "2026-01-12T15:30:00Z",
    "updated_at": "2026-01-12T15:30:00Z"
  },
  {
    "id": 5,
    "tenant_id": 5,
    "username": "alice",
    "email": "alice@company.com",
    "role": "ADMIN",
    "is_totp_enabled": false,
    "is_active": true,
    "created_at": "2026-01-12T16:00:00Z",
    "updated_at": "2026-01-12T16:00:00Z"
  }
]
```

**4. Deactivate Tenant** (OWNER Only)

```bash
curl -X PATCH "http://127.0.0.1:8000/tenants/me/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

**Response:**
```json
{
  "id": 5,
  "email": "company@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": false,
  "created_at": "2026-01-12T15:30:00Z",
  "updated_at": "2026-01-12T15:40:00Z"
}
```

**Warning:** Once deactivated, all users in the tenant will be unable to log in. The tenant owner will need administrative intervention to reactivate.

**5. Reactivate Tenant** (OWNER Only - Requires Manual Database Update)

If a tenant is deactivated, reactivation requires manual database intervention since the authentication system blocks inactive tenants:

```bash
# Manual reactivation via database
sqlite3 mcp_auth.db "UPDATE tenants SET is_active = 1 WHERE id = 5;"
```

**6. Soft Delete Tenant** (OWNER Only)

```bash
curl -X DELETE "http://127.0.0.1:8000/tenants/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:** 204 No Content (empty response body)

**What happens:**
- Tenant is marked as `is_active = false` (soft delete)
- All users in the tenant can no longer log in
- Tenant data is preserved in the database
- This is **not a hard delete** - data can be recovered by reactivating

**Role-Based Authorization Matrix:**

| Endpoint | Method | OWNER | ADMIN | MEMBER |
|----------|--------|-------|-------|--------|
| `/tenants/me` | GET | ✅ | ✅ | ✅ |
| `/tenants/me` | PUT | ✅ | ✅ | ❌ |
| `/tenants/me/status` | PATCH | ✅ | ❌ | ❌ |
| `/tenants/me` | DELETE | ✅ | ❌ | ❌ |
| `/tenants/me/users` | GET | ✅ | ✅ | ❌ |

## Troubleshooting

### Error: Address Already in Use

```bash
# Find and kill process on port 8000
lsof -ti :8000 | xargs kill -9

# OR run on a different port
uvicorn main:app --reload --port 8001
```

### Error: Internal Server Error on Registration

This usually means the database wasn't set up properly or is corrupted.

**Step 1: Verify database tables exist**
```bash
sqlite3 mcp_auth.db ".tables"
```

If you only see `alembic_version` without `users` and `refresh_tokens`, the database is corrupted.

**Step 2: Delete and recreate database**
```bash
# Delete corrupted database
rm mcp_auth.db

# Recreate with migrations
alembic upgrade head

# Verify tables now exist
sqlite3 mcp_auth.db ".tables"

# Expected output: alembic_version  refresh_tokens  users
```

**Step 3: Restart the server**
```bash
uvicorn main:app --reload
```

### Error: No such table

```bash
# Run migrations to create tables
alembic upgrade head

# Verify tables were created
sqlite3 mcp_auth.db ".tables"
```

### Error: Module not found

This means dependencies aren't installed or you're using the wrong Python environment.

```bash
# Ensure you're in the virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
uv sync --extra dev

# Verify installation
python -c "import fastapi, sqlalchemy, bcrypt; print('✓ All dependencies available')"
```

### Error: Wrong Python Version or Missing Packages

If you have anaconda or system Python active, you might be using the wrong environment.

```bash
# Check which Python is being used
which python

# Should show: /path/to/MCP_Auth/.venv/bin/python
# If it shows anaconda or system Python, activate venv:
source .venv/bin/activate
```

### Tests Failing

```bash
# Clean up test database
rm test_integration.db

# Ensure venv is active
source .venv/bin/activate

# Re-run tests
pytest

# If still failing, reinstall dependencies
uv sync --extra dev
pytest
```

### Database Corruption Issues

If you encounter `sqlite3.OperationalError: no such index` or similar database errors:

```bash
# This indicates database is in inconsistent state
# Cannot downgrade - delete and recreate

rm mcp_auth.db
alembic upgrade head

# Verify
sqlite3 mcp_auth.db ".schema users"
```

## Common First-Time Setup Tips

### Always Use the Virtual Environment

The most common issues arise from using the wrong Python environment:

```bash
# GOOD - Using venv Python
source .venv/bin/activate
python --version  # Should show Python 3.12.x
uvicorn main:app --reload

# BAD - Using system or anaconda Python
# This may use wrong dependencies or versions
uvicorn main:app --reload  # Without activating venv
```

### Verify Everything After Initial Setup

```bash
# 1. Check venv is active
which python
# Should output: /path/to/MCP_Auth/.venv/bin/python

# 2. Verify dependencies
python -c "import fastapi, sqlalchemy, bcrypt, jwt; print('✓ All imports work')"

# 3. Check database is properly set up
sqlite3 mcp_auth.db ".tables"
# Should output: alembic_version  refresh_tokens  users

# 4. Test server starts
uvicorn main:app --reload
# Should see: "Application startup complete"

# 5. Test basic endpoint
curl http://127.0.0.1:8000/
# Should return: {"message":"Hello World"}
```

### Recommended First-Time Flow

```bash
# 1. Clone and navigate to project
git clone https://github.com/jtuchinsky/MCP_Auth.git
cd MCP_Auth

# 2. Set up environment
cp .env.example .env
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}'))" >> .env

# 3. Install dependencies
uv sync --extra dev

# 4. Verify installation
.venv/bin/python -c "import fastapi; print('✓ Installation successful')"

# 5. Set up database
alembic upgrade head
sqlite3 mcp_auth.db ".tables"

# 6. Activate venv and start server
source .venv/bin/activate
uvicorn main:app --reload

# 7. In another terminal, test the API
curl http://127.0.0.1:8000/
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## Quick Reference: Common Commands

```bash
# Start server
uvicorn main:app --reload

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Check database migration status
alembic current

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View database schema
sqlite3 mcp_auth.db ".schema"

# View database tables
sqlite3 mcp_auth.db ".tables"

# Stop server
# Press Ctrl+C in the terminal running uvicorn
```

## Next Steps

- Read [CLAUDE.md](../CLAUDE.md) for detailed developer documentation
- Read [README.md](../README.md) for API endpoint reference
- Visit http://127.0.0.1:8000/docs for interactive API documentation
- Check [PLAN.md](./PLAN.md) to understand the implementation architecture