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

# Expected output: alembic_version  refresh_tokens  users
```

## 4. Start the Server

### Activate Virtual Environment (Optional)

```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
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

#### A. Register a New User

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2024-12-26T...",
  "updated_at": "2024-12-26T..."
}
```

#### B. Login

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
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
  "email": "user@example.com",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2024-12-26T...",
  "updated_at": "2024-12-26T..."
}
```

## Troubleshooting

### Error: Address Already in Use

```bash
# Find and kill process on port 8000
lsof -ti :8000 | xargs kill -9

# OR run on a different port
uvicorn main:app --reload --port 8001
```

### Error: Internal Server Error on Registration

This usually means the database wasn't set up properly.

```bash
# Delete and recreate database
rm mcp_auth.db
alembic upgrade head

# Restart the server
uvicorn main:app --reload
```

### Error: No such table

```bash
# Run migrations
alembic upgrade head
```

### Error: Module not found

```bash
# Reinstall dependencies
uv sync --extra dev
```

### Tests Failing

```bash
# Clean up test database
rm test_integration.db

# Re-run tests
pytest
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