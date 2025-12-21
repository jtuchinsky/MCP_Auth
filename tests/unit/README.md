# Unit Tests

This directory contains unit tests for individual components of the MCP Auth Service.

## Test Files

### test_database.py (Step 3)

Tests for database configuration and session management.

**Test Coverage:**
- ✅ Base declarative class is properly defined
- ✅ SQLAlchemy engine is created correctly
- ✅ Engine can establish database connection
- ✅ SessionLocal factory is created
- ✅ SessionLocal creates valid sessions
- ✅ SessionLocal has correct configuration (autoflush disabled)
- ✅ `get_db()` dependency yields valid sessions
- ✅ `get_db()` properly closes sessions after use
- ✅ `get_db()` works as a context manager
- ✅ `get_db()` handles exceptions gracefully
- ✅ Base.metadata is accessible for migrations
- ✅ Database can be inspected using SQLAlchemy inspector

**Test Results:** 12 passed

### test_security.py (Step 4)

Tests for password hashing and verification using bcrypt.

**Test Coverage:**
- ✅ Password hashing returns valid string
- ✅ Produces bcrypt hash format ($2b$)
- ✅ Uses correct cost factor (12)
- ✅ Same password produces different hashes (salting)
- ✅ Different passwords produce different hashes
- ✅ Handles special characters
- ✅ Handles unicode characters
- ✅ Handles empty strings
- ✅ Verifies correct password returns True
- ✅ Verifies incorrect password returns False
- ✅ Verification is case-sensitive
- ✅ Verification with special characters
- ✅ Verification with unicode
- ✅ Verification with empty string
- ✅ Verification preserves whitespace
- ✅ Invalid hash format raises exception
- ✅ Complete hash and verify workflow
- ✅ Multiple users with same password get different hashes
- ✅ Password change workflow

**Test Results:** 19 passed

### test_exceptions.py (Step 4)

Tests for custom HTTP exception classes.

**Test Coverage:**

**AuthenticationError (401 Unauthorized):**
- ✅ Default message
- ✅ Custom message
- ✅ With headers (WWW-Authenticate)
- ✅ Is HTTPException subclass
- ✅ Can be raised and caught

**AuthorizationError (403 Forbidden):**
- ✅ Default message
- ✅ Custom message
- ✅ With headers
- ✅ Is HTTPException subclass
- ✅ Can be raised and caught

**TOTPError (400 Bad Request):**
- ✅ Default message
- ✅ Custom message
- ✅ With headers
- ✅ Is HTTPException subclass
- ✅ Can be raised and caught

**Status Codes:**
- ✅ Each exception has correct status code
- ✅ All status codes are unique

**Usage Scenarios:**
- ✅ Invalid credentials scenario
- ✅ Expired token scenario
- ✅ Insufficient permissions scenario
- ✅ Invalid TOTP code scenario
- ✅ TOTP not enabled scenario

**Test Results:** 24 passed

## Running Tests

### Run All Unit Tests
```bash
.venv/bin/python -m pytest tests/unit/ -v
```

### Run Specific Test Files
```bash
# Database tests
.venv/bin/python -m pytest tests/unit/test_database.py -v

# Security tests
.venv/bin/python -m pytest tests/unit/test_security.py -v

# Exception tests
.venv/bin/python -m pytest tests/unit/test_exceptions.py -v
```

### Run Specific Test Class
```bash
.venv/bin/python -m pytest tests/unit/test_security.py::TestPasswordHashing -v
```

### Run Specific Test
```bash
.venv/bin/python -m pytest tests/unit/test_security.py::TestPasswordHashing::test_hash_password_uses_correct_cost_factor -v
```

### test_models.py (Step 5)

Tests for database models (User and RefreshToken).

**Test Coverage:**

**User Model:**
- ✅ Users table exists
- ✅ All required columns present
- ✅ Email has unique constraint
- ✅ Create user with required fields
- ✅ Default values (is_totp_enabled=False, is_active=True)
- ✅ User with TOTP enabled
- ✅ updated_at timestamp changes on modification
- ✅ __repr__ method works correctly
- ✅ Relationship with refresh tokens

**RefreshToken Model:**
- ✅ Refresh_tokens table exists
- ✅ All required columns present
- ✅ Token has unique constraint
- ✅ Create refresh token with required fields
- ✅ Default values (is_revoked=False)
- ✅ Token with OAuth2 fields (client_id, scope)
- ✅ Token revocation
- ✅ __repr__ method works correctly
- ✅ Foreign key to User table
- ✅ Cascade delete (deleting user deletes tokens)

**Model Relationships:**
- ✅ Access tokens from user (User.refresh_tokens)
- ✅ Access user from token (RefreshToken.user)

**Test Results:** 21 passed

### test_user_repository.py (Step 7)

Tests for user repository data access layer.

**Test Coverage:**

**Create User:**
- ✅ Create user with required fields successfully
- ✅ Created user is persisted to database
- ✅ Create multiple users with different IDs

**Get User by ID:**
- ✅ Get existing user by ID
- ✅ Get nonexistent user returns None
- ✅ Get user with ID 0 returns None
- ✅ Get user with negative ID returns None

**Get User by Email:**
- ✅ Get existing user by email
- ✅ Get nonexistent user returns None
- ✅ Email lookup case sensitivity
- ✅ Get user with empty email returns None

**Update TOTP Secret:**
- ✅ Update TOTP secret successfully
- ✅ TOTP secret update persists to database
- ✅ Update for nonexistent user raises ValueError
- ✅ Update TOTP secret multiple times

**Enable TOTP:**
- ✅ Enable TOTP successfully
- ✅ Enable TOTP persists to database
- ✅ Enable for nonexistent user raises ValueError
- ✅ Enable TOTP is idempotent

**Integration Tests:**
- ✅ Complete user workflow (create, retrieve, update TOTP, enable TOTP)
- ✅ Operations on one user don't affect others

**Test Results:** 21 passed

### test_token_repository.py (Step 8)

Tests for token repository data access layer.

**Test Coverage:**

**Create Refresh Token:**
- ✅ Create refresh token successfully
- ✅ Create with OAuth2 fields (client_id, scope)
- ✅ Created token is persisted to database
- ✅ Create multiple tokens for same user

**Get Token by String:**
- ✅ Get existing token
- ✅ Get nonexistent token returns None
- ✅ Token lookup is case-sensitive
- ✅ Get token with empty string returns None

**Revoke Token:**
- ✅ Revoke token successfully
- ✅ Token revocation persists to database
- ✅ Revoke nonexistent token raises ValueError
- ✅ Revoke is idempotent

**Revoke All User Tokens:**
- ✅ Revoke all tokens for a user
- ✅ Revoking one user's tokens doesn't affect other users
- ✅ Revoke with no tokens doesn't error
- ✅ Revoke for nonexistent user doesn't error

**Integration Tests:**
- ✅ Complete token lifecycle (create, retrieve, revoke)
- ✅ User logout scenario (revoke all tokens)
- ✅ Token refresh scenario (revoke old, create new)

**Test Results:** 19 passed

### test_jwt_service.py (Step 9)

Tests for JWT service (token creation and validation).

**Test Coverage:**

**Create Access Token:**
- ✅ Create basic access token
- ✅ Token payload has correct structure (sub, email, exp, iat, scopes)
- ✅ Create token with OAuth2 scopes
- ✅ Create token with OAuth2 audience
- ✅ Token has correct expiration time
- ✅ Token is signed with HS256 algorithm
- ✅ Created token can be successfully decoded
- ✅ Tokens for different users have different payloads

**Create Refresh Token:**
- ✅ Refresh token returns string
- ✅ Refresh token is URL-safe
- ✅ Refresh tokens are randomly generated
- ✅ Refresh token has sufficient length (32 bytes)
- ✅ Multiple refresh tokens are all unique

**Decode Access Token:**
- ✅ Decode valid access token
- ✅ Decode token with scopes
- ✅ Decode token with audience
- ✅ Decoding expired token raises AuthenticationError
- ✅ Decoding token with invalid signature raises error
- ✅ Decoding malformed token raises error
- ✅ Decoding empty string raises error
- ✅ Decoding token with wrong algorithm raises error

**Integration Tests:**
- ✅ Complete create and decode workflow
- ✅ Refresh token format differs from access token
- ✅ Multiple users workflow
- ✅ Token expiration is enforced

**Test Results:** 25 passed

### test_totp_service.py (Step 10)

Tests for TOTP service (two-factor authentication).

**Test Coverage:**

**Generate Secret:**
- ✅ Generate secret returns string
- ✅ Secret is base32-encoded
- ✅ Secret has correct length (32 characters)
- ✅ Secrets are randomly generated
- ✅ Multiple secrets are all unique
- ✅ Generated secret can create TOTP

**Get Provisioning URI:**
- ✅ URI has correct otpauth format
- ✅ URI contains user's email (URL-encoded)
- ✅ URI contains secret
- ✅ URI contains issuer name
- ✅ Different emails produce different URIs

**Generate QR Code:**
- ✅ QR code returns string
- ✅ QR code is base64-encoded
- ✅ QR code is PNG image
- ✅ Different URIs produce different QR codes
- ✅ Generate QR code from provisioning URI

**Verify Code:**
- ✅ Verify valid TOTP code
- ✅ Verify invalid code returns False
- ✅ Verify code with wrong secret returns False
- ✅ Verify empty code returns False
- ✅ Verify short code returns False
- ✅ Verify long code returns False
- ✅ Verify non-numeric code returns False
- ✅ Verify code with spaces

**Integration Tests:**
- ✅ Complete TOTP setup workflow (generate, URI, QR, verify)
- ✅ Multiple users workflow
- ✅ TOTP code time validity
- ✅ Generated secret works with authenticator apps

**Test Results:** 28 passed

### test_auth_service.py (Step 11)

Tests for authentication service (high-level orchestration).

**Test Coverage:**

**Register User:**
- ✅ Register user successfully
- ✅ Password is hashed during registration
- ✅ Duplicate email raises error
- ✅ User is persisted to database

**Authenticate User:**
- ✅ Authenticate with correct credentials
- ✅ Wrong email raises AuthenticationError
- ✅ Wrong password raises AuthenticationError
- ✅ Inactive account raises AuthenticationError
- ✅ Email authentication case sensitivity

**Create Tokens:**
- ✅ Create tokens with basic parameters
- ✅ Create tokens with OAuth2 client_id and scope
- ✅ Refresh token is stored in database
- ✅ Access token is JWT format
- ✅ Create multiple tokens for same user

**Refresh Access Token:**
- ✅ Refresh token successfully
- ✅ Invalid refresh token raises error
- ✅ Revoked refresh token raises error
- ✅ Expired refresh token raises error
- ✅ Inactive user refresh raises error
- ✅ Refresh preserves client_id and scope

**Integration Tests:**
- ✅ Complete registration and login workflow
- ✅ Token refresh workflow
- ✅ Multiple users don't interfere

**Test Results:** 23 passed

### test_oauth2_service.py (Step 12)

Tests for OAuth2 authorization server metadata (RFC 8414).

**Test Coverage:**

**Metadata Structure:**
- ✅ Has all RFC 8414 required fields
- ✅ Issuer matches base URL
- ✅ All endpoints use base URL
- ✅ Endpoint URLs have correct paths
- ✅ Metadata is valid dictionary
- ✅ All values are JSON serializable

**OAuth 2.1 Compliance:**
- ✅ Supports PKCE (S256 code challenge method)
- ✅ Supports authorization code flow
- ✅ Supports refresh token grant
- ✅ No implicit flow (OAuth 2.1 requirement)
- ✅ No password grant (OAuth 2.1 requirement)

**Client Authentication:**
- ✅ Supports client_secret_post
- ✅ Supports client_secret_basic
- ✅ Supports public clients (none)

**Scopes and Features:**
- ✅ Supports OpenID Connect scopes (openid, profile, email)
- ✅ Supports MCP scopes (mcp:read, mcp:write)
- ✅ Supports resource indicators (RFC 8707)
- ✅ Includes MCP-specific features

**Endpoints:**
- ✅ Authorization endpoint
- ✅ Token endpoint
- ✅ JWKS URI
- ✅ Revocation endpoint
- ✅ Service documentation

**URL Handling:**
- ✅ Works with different base URLs
- ✅ Handles URLs without trailing slash
- ✅ Handles URLs with trailing slash

**Integration Tests:**
- ✅ Full OAuth 2.1 compliance verification
- ✅ Full MCP compliance verification
- ✅ Complete endpoint set
- ✅ Local development configuration
- ✅ Production configuration

**Test Results:** 23 passed

### test_user_schemas.py (Step 13)

Tests for user Pydantic schemas (API request/response models).

**Test Coverage:**

**UserCreate Schema:**
- ✅ Valid data creates schema
- ✅ Various valid email formats
- ✅ Invalid email raises ValidationError
- ✅ Password minimum length (8 chars)
- ✅ Password maximum length (100 chars)
- ✅ Missing email raises ValidationError
- ✅ Missing password raises ValidationError
- ✅ Empty password is invalid
- ✅ Special characters and Unicode in password
- ✅ Serialization to dict (model_dump)
- ✅ Serialization to JSON (model_dump_json)

**UserResponse Schema:**
- ✅ Valid data creates schema
- ✅ Create from ORM User model (model_validate)
- ✅ Missing required fields raise ValidationError
- ✅ Boolean fields validation
- ✅ Datetime fields handling
- ✅ Serialization to dict
- ✅ Serialization to JSON
- ✅ Password hash not included in response

**UserUpdate Schema:**
- ✅ Update with all fields
- ✅ Partial updates (only some fields)
- ✅ No fields provided (all optional)
- ✅ Email validation
- ✅ Password minimum length
- ✅ Password maximum length
- ✅ Exclude unset fields
- ✅ Serialization to dict

**Integration Tests:**
- ✅ Complete user creation workflow
- ✅ User update workflow with partial data
- ✅ All schemas are JSON serializable

**Test Results:** 29 passed

## Overall Test Results

**Total:** 244 tests
- test_database.py: 12 passed
- test_security.py: 19 passed
- test_exceptions.py: 24 passed
- test_models.py: 21 passed
- test_user_repository.py: 21 passed
- test_token_repository.py: 19 passed
- test_jwt_service.py: 25 passed
- test_totp_service.py: 28 passed
- test_auth_service.py: 23 passed
- test_oauth2_service.py: 23 passed
- test_user_schemas.py: 29 passed

## Test Coverage

To run tests with coverage:
```bash
.venv/bin/python -m pytest tests/unit/ --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## Notes

- **bcrypt Version:** Tests require bcrypt <5.0.0 for compatibility with passlib
- **Warning:** The deprecation warning about 'crypt' module can be safely ignored (it's from passlib, not our code)
