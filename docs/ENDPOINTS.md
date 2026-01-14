# MCP Auth - API Endpoints Reference

**Version:** 0.1.0
**Last Updated:** January 13, 2026
**Status:** Production Ready
**Base URL:** `http://127.0.0.1:8000`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication](#2-authentication)
3. [Authentication Endpoints](#3-authentication-endpoints)
4. [TOTP (Two-Factor Authentication)](#4-totp-two-factor-authentication)
5. [Protected User Endpoints](#5-protected-user-endpoints)
6. [Tenant Management Endpoints](#6-tenant-management-endpoints)
7. [MCP Metadata Endpoints](#7-mcp-metadata-endpoints)
8. [Error Responses](#8-error-responses)
9. [Quick Reference](#9-quick-reference)

---

## 1. Overview

### 1.1 API Design Principles

- **RESTful Architecture** - Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **JWT Authentication** - Bearer token in Authorization header
- **JSON Request/Response** - All payloads use JSON format
- **Standard HTTP Status Codes** - 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found
- **Multi-Tenancy Support** - Tenant isolation via JWT tenant_id claim
- **MCP OAuth 2.1 Compliance** - Full OAuth 2.1 and MCP specification support

### 1.2 Endpoint Categories

| Category | Base Path | Description | Authentication Required |
|----------|-----------|-------------|------------------------|
| **Authentication** | `/auth` | Login, registration, token management | No (public) |
| **TOTP/2FA** | `/auth/totp` | Two-factor authentication setup/validation | Yes |
| **Protected** | `/api/protected` | User profile management | Yes |
| **Tenants** | `/tenants` | Tenant management with cascade updates | Yes (OWNER/ADMIN) |
| **MCP Metadata** | `/.well-known` | OAuth 2.1 metadata discovery | No (public) |

### 1.3 Authentication Methods

**Bearer Token (JWT)**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Payload Structure:**
```json
{
  "sub": "1",              // User ID
  "email": "user@example.com",
  "tenant_id": "1",        // Tenant ID (multi-tenancy)
  "username": "user",
  "role": "OWNER",         // OWNER, ADMIN, or MEMBER
  "scopes": [],
  "iat": 1704067200,       // Issued at
  "exp": 1704068100        // Expires at (15 min)
}
```

---

## 2. Authentication

### 2.1 Token Types

| Token Type | Lifetime | Storage | Purpose |
|------------|----------|---------|---------|
| **Access Token** | 15 minutes | Memory (not stored in DB) | API authentication |
| **Refresh Token** | 30 days | Database (can be revoked) | Get new access tokens |

### 2.2 Token Lifecycle

```
1. Login → Get access + refresh tokens
2. Use access token for API calls (valid 15 min)
3. Access token expires → Use refresh token to get new pair
4. Refresh token rotates → Old token revoked, new token issued
5. Logout → Refresh token revoked in database
```

### 2.3 Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **OWNER** | Full tenant control (update, deactivate, delete), manage all users |
| **ADMIN** | Manage users, update tenant info (cannot deactivate/delete tenant) |
| **MEMBER** | Read-only access to own profile |

---

## 3. Authentication Endpoints

### 3.1 POST /auth/login

**Tenant Login (Auto-Registration)**

Login as tenant owner. Automatically creates tenant + owner user on first login.

**Authorization:** None (public)

**Request Body:**
```json
{
  "tenant_email": "acme@example.com",
  "password": "SecurePassword123!",
  "tenant_name": "Acme Corporation",  // Optional, only used for new tenants
  "totp_code": "123456"               // Optional, required if TOTP enabled
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - TOTP required but not provided (use `/auth/totp/validate`)

**Notes:**
- First-time login: Creates tenant + owner user automatically
- Returning user: Authenticates existing tenant owner
- Owner user has username = tenant_email, role = OWNER

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "acme@example.com",
    "password": "SecurePassword123!",
    "tenant_name": "Acme Corporation"
  }'
```

---

### 3.2 POST /auth/login-user

**User Login (Multi-User within Tenant)**

Login as a non-owner user within an existing tenant.

**Authorization:** None (public)

**Request Body:**
```json
{
  "tenant_email": "acme@example.com",
  "username": "alice",
  "password": "AlicePassword123!",
  "totp_code": "123456"  // Optional, required if TOTP enabled
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials or tenant doesn't exist
- `403 Forbidden` - TOTP required but not provided, or tenant inactive

**Notes:**
- For non-owner users (ADMIN, MEMBER roles)
- Requires existing tenant
- Owner users should use `/auth/login` instead

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/login-user \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "acme@example.com",
    "username": "alice",
    "password": "AlicePassword123!"
  }'
```

---

### 3.3 POST /auth/refresh

**Refresh Access Token**

Use refresh token to obtain new access and refresh tokens.

**Authorization:** None (uses refresh token in body)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // New token
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid, expired, or revoked refresh token

**Notes:**
- **Token Rotation**: Old refresh token is revoked, new one issued
- Old refresh token cannot be reused (prevents replay attacks)
- User must be active in database

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGc..."
  }'
```

---

### 3.4 POST /auth/logout

**Logout and Revoke Refresh Token**

Revoke the provided refresh token to logout user.

**Authorization:** None (uses refresh token in body)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `204 No Content` (no response body)

**Error Responses:**
- None - Idempotent operation (succeeds even if token doesn't exist)

**Notes:**
- **Idempotent** - Safe to call multiple times
- Only revokes refresh token (access token remains valid until expiration)
- Client should delete tokens from local storage

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGc..."
  }'
```

---

## 4. TOTP (Two-Factor Authentication)

### 4.1 POST /auth/totp/setup

**Setup TOTP 2FA**

Generate TOTP secret and QR code for authenticator app setup.

**Authorization:** Bearer token (TOTP must NOT be enabled)

**Request:** No body required

**Response:** `200 OK`
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/MCP%20Auth%20Service:acme@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MCP%20Auth%20Service",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
}
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - TOTP already enabled

**Workflow:**
1. Call this endpoint to get QR code
2. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
3. Call `/auth/totp/verify` with 6-digit code to enable TOTP

**Notes:**
- Secret is saved to user but TOTP not enabled yet
- Must verify code with `/auth/totp/verify` to complete setup
- QR code is base64-encoded PNG image (data URI)

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/totp/setup \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 4.2 POST /auth/totp/verify

**Verify TOTP Code and Enable 2FA**

Verify TOTP code from authenticator app to complete 2FA setup.

**Authorization:** Bearer token

**Request Body:**
```json
{
  "totp_code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "acme@example.com",
  "email": "acme@example.com",
  "role": "OWNER",
  "is_totp_enabled": true,  // Now enabled
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - TOTP setup not initiated or invalid code
- `401 Unauthorized` - Not authenticated

**Notes:**
- Must call `/auth/totp/setup` first
- Validates code against secret from setup step
- Once enabled, all future logins require TOTP code

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/totp/verify \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "totp_code": "123456"
  }'
```

---

### 4.3 POST /auth/totp/validate

**Login with TOTP (Alternative Login Endpoint)**

Authenticate with email, password, and TOTP code for users with 2FA enabled.

**Authorization:** None (public)

**Request Body:**
```json
{
  "email": "acme@example.com",
  "password": "SecurePassword123!",
  "totp_code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials or TOTP code
- `403 Forbidden` - TOTP not enabled (use `/auth/login` instead)

**Notes:**
- Alternative to `/auth/login` with `totp_code` field
- Required when TOTP is enabled
- TOTP codes change every 30 seconds

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/auth/totp/validate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "acme@example.com",
    "password": "SecurePassword123!",
    "totp_code": "123456"
  }'
```

---

## 5. Protected User Endpoints

### 5.1 GET /api/protected/me

**Get Current User Profile**

Retrieve authenticated user's profile information.

**Authorization:** Bearer token (any role)

**Request:** No body required

**Response:** `200 OK`
```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "acme@example.com",
  "email": "acme@example.com",
  "role": "OWNER",
  "tenant_name": "Acme Corporation",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired access token
- `403 Forbidden` - User account inactive

**Example:**
```bash
curl -X GET http://127.0.0.1:8000/api/protected/me \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 5.2 PATCH /api/protected/profile

**Update User Profile**

Update authenticated user's email and/or password.

**Authorization:** Bearer token (any role)

**Request Body:**
```json
{
  "email": "newemail@example.com",  // Optional
  "password": "NewSecurePassword123!"  // Optional
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "acme@example.com",
  "email": "newemail@example.com",  // Updated
  "role": "OWNER",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T11:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Email already exists
- `401 Unauthorized` - Invalid or expired access token

**Notes:**
- Both fields are optional (can update either or both)
- Email must be unique across all users
- Password is automatically hashed

**Example:**
```bash
curl -X PATCH http://127.0.0.1:8000/api/protected/profile \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "password": "NewSecurePassword123!"
  }'
```

---

## 6. Tenant Management Endpoints

### 6.1 GET /tenants/me

**Get Current Tenant**

Retrieve information about the authenticated user's tenant.

**Authorization:** Bearer token (any role)

**Request:** No body required

**Response:** `200 OK`
```json
{
  "id": 2,
  "email": "acme@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired access token
- `404 Not Found` - Tenant not found

**Example:**
```bash
curl -X GET http://127.0.0.1:8000/tenants/me \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 6.2 PUT /tenants/me

**Update Tenant Information**

Update tenant name with automatic cascade to all users.

**Authorization:** Bearer token (OWNER or ADMIN role)

**Request Body:**
```json
{
  "tenant_name": "Acme Corporation Inc"
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "email": "acme@example.com",
  "tenant_name": "Acme Corporation Inc",  // Updated
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T14:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired access token
- `403 Forbidden` - User role is MEMBER (requires OWNER or ADMIN)
- `404 Not Found` - Tenant not found
- `422 Unprocessable Entity` - Validation error (empty tenant_name)

**✨ Cascade Behavior:**
- Updates tenant's `tenant_name`
- Automatically updates `tenant_name` for ALL users in the tenant
- Atomic operation (both succeed or both fail)
- Uses efficient bulk UPDATE (single SQL statement)

**Example:**
```bash
curl -X PUT http://127.0.0.1:8000/tenants/me \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Acme Corporation Inc"
  }'
```

---

### 6.3 PATCH /tenants/me/status

**Update Tenant Status**

Activate or deactivate tenant with automatic cascade to all users.

**Authorization:** Bearer token (OWNER role only)

**Request Body:**
```json
{
  "is_active": false
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "email": "acme@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": false,  // Deactivated
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T15:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired access token
- `403 Forbidden` - User role is not OWNER (ADMIN cannot perform this)
- `404 Not Found` - Tenant not found

**⚠️ Cascade Behavior:**
- **Deactivation**: Tenant deactivated → ALL users deactivated (including OWNER)
- **Reactivation**: Tenant reactivated → ALL users reactivated
- Users cannot login when deactivated
- Existing access tokens remain valid until expiration (15 min)
- Manual database access required to reactivate if OWNER is deactivated

**Why OWNER-only?**
- Deactivating tenant affects ALL users (high impact operation)
- Prevents ADMIN from locking out OWNER
- Only tenant owner should have this power

**Example (Deactivate):**
```bash
curl -X PATCH http://127.0.0.1:8000/tenants/me/status \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

**Example (Reactivate):**
```bash
curl -X PATCH http://127.0.0.1:8000/tenants/me/status \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true
  }'
```

---

### 6.4 DELETE /tenants/me

**Delete Tenant (Soft Delete)**

Soft delete tenant by marking as inactive (with cascade to all users).

**Authorization:** Bearer token (OWNER role only)

**Request:** No body required

**Response:** `204 No Content` (no response body)

**Error Responses:**
- `401 Unauthorized` - Invalid or expired access token
- `403 Forbidden` - User role is not OWNER (ADMIN cannot perform this)
- `404 Not Found` - Tenant not found

**⚠️ Important Notes:**
- **Soft Delete** - Data is NOT removed, just marked `is_active = false`
- All users in tenant are automatically deactivated
- Data preserved for audit trails and compliance
- Requires manual database access to reactivate

**Cascade Behavior:**
```sql
-- Tenant and all users marked inactive, not deleted
UPDATE tenants SET is_active = 0 WHERE id = 2;
UPDATE users SET is_active = 0 WHERE tenant_id = 2;

-- NO DELETE statements - data preserved!
```

**Post-Deletion:**
- Login attempts return `403 Forbidden`
- Existing access tokens fail with `403 Forbidden`
- Refresh tokens fail with `403 Forbidden`

**Example:**
```bash
curl -X DELETE http://127.0.0.1:8000/tenants/me \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 6.5 GET /tenants/me/users

**List Users in Tenant**

Get all users in the current user's tenant.

**Authorization:** Bearer token (OWNER or ADMIN role)

**Request:** No body required

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 2,
    "username": "acme@example.com",
    "email": "acme@example.com",
    "role": "OWNER",
    "tenant_name": "Acme Corporation",
    "is_totp_enabled": false,
    "is_active": true,
    "created_at": "2026-01-10T08:00:00Z",
    "updated_at": "2026-01-13T10:30:00Z"
  },
  {
    "id": 2,
    "tenant_id": 2,
    "username": "alice",
    "email": "alice@acme.com",
    "role": "ADMIN",
    "tenant_name": "Acme Corporation",
    "is_totp_enabled": true,
    "is_active": true,
    "created_at": "2026-01-11T09:00:00Z",
    "updated_at": "2026-01-12T14:30:00Z"
  },
  {
    "id": 3,
    "tenant_id": 2,
    "username": "bob",
    "email": "bob@acme.com",
    "role": "MEMBER",
    "tenant_name": "Acme Corporation",
    "is_totp_enabled": false,
    "is_active": true,
    "created_at": "2026-01-11T10:00:00Z",
    "updated_at": "2026-01-11T10:00:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired access token
- `403 Forbidden` - User role is MEMBER (requires OWNER or ADMIN)

**Notes:**
- Returns all users in the tenant (including inactive users)
- Ordered by creation date (oldest first)
- Tenant isolation enforced (can only see users in own tenant)

**Example:**
```bash
curl -X GET http://127.0.0.1:8000/tenants/me/users \
  -H "Authorization: Bearer eyJhbGc..."
```

---

## 7. MCP Metadata Endpoints

### 7.1 GET /.well-known/oauth-authorization-server

**OAuth 2.1 Authorization Server Metadata**

RFC 8414 compliant OAuth 2.1 authorization server metadata for MCP clients.

**Authorization:** None (public)

**Request:** No body required

**Response:** `200 OK`
```json
{
  "issuer": "http://127.0.0.1:8000",
  "authorization_endpoint": "http://127.0.0.1:8000/auth/authorize",
  "token_endpoint": "http://127.0.0.1:8000/auth/token",
  "jwks_uri": "http://127.0.0.1:8000/.well-known/jwks.json",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "revocation_endpoint": "http://127.0.0.1:8000/auth/revoke",
  "revocation_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "introspection_endpoint": "http://127.0.0.1:8000/auth/introspect",
  "introspection_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "resource_indicators_supported": true,
  "mcp_version": "1.0",
  "mcp_features": ["oauth2.1", "pkce", "resource_indicators", "refresh_token_rotation", "totp"]
}
```

**MCP OAuth 2.1 Compliance:**
- ✅ **PKCE Required** - S256 code challenge method
- ✅ **Resource Indicators** - RFC 8707 support
- ✅ **Refresh Token Rotation** - Automatic token rotation on refresh
- ✅ **TOTP-based 2FA** - Two-factor authentication support

**Notes:**
- Discovery endpoint for MCP clients
- Base URL dynamically constructed from request
- Used by clients to discover server capabilities

**Example:**
```bash
curl -X GET http://127.0.0.1:8000/.well-known/oauth-authorization-server
```

---

## 8. Error Responses

### 8.1 Standard Error Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### 8.2 Common HTTP Status Codes

| Status Code | Meaning | When Used |
|-------------|---------|-----------|
| `200 OK` | Success | Request completed successfully |
| `201 Created` | Resource created | New resource created (not used currently) |
| `204 No Content` | Success, no body | Logout, DELETE operations |
| `400 Bad Request` | Invalid input | Validation errors, invalid TOTP code |
| `401 Unauthorized` | Authentication failed | Invalid credentials, expired token |
| `403 Forbidden` | Permission denied | Insufficient role, inactive account, TOTP required |
| `404 Not Found` | Resource not found | Tenant/user doesn't exist |
| `422 Unprocessable Entity` | Validation error | Pydantic validation failed |
| `500 Internal Server Error` | Server error | Unexpected server errors |

### 8.3 Error Examples

#### 401 Unauthorized - Invalid Credentials
```json
{
  "detail": "Incorrect password"
}
```

#### 403 Forbidden - TOTP Required
```json
{
  "detail": "TOTP verification required. Provide totp_code or use /auth/totp/validate endpoint."
}
```

#### 403 Forbidden - Insufficient Role
```json
{
  "detail": "This endpoint requires ADMIN or OWNER role. Your role: MEMBER"
}
```

#### 403 Forbidden - Inactive Account
```json
{
  "detail": "User account is inactive"
}
```

#### 400 Bad Request - Invalid TOTP Code
```json
{
  "detail": "Invalid TOTP code."
}
```

#### 422 Unprocessable Entity - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 9. Quick Reference

### 9.1 Endpoint Summary Table

| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| **POST** | `/auth/login` | ❌ | - | Login as tenant (auto-register) |
| **POST** | `/auth/login-user` | ❌ | - | Login as user within tenant |
| **POST** | `/auth/refresh` | ❌ | - | Refresh access token |
| **POST** | `/auth/logout` | ❌ | - | Logout and revoke refresh token |
| **POST** | `/auth/totp/setup` | ✅ | Any | Setup TOTP 2FA |
| **POST** | `/auth/totp/verify` | ✅ | Any | Verify TOTP and enable 2FA |
| **POST** | `/auth/totp/validate` | ❌ | - | Login with TOTP |
| **GET** | `/api/protected/me` | ✅ | Any | Get current user profile |
| **PATCH** | `/api/protected/profile` | ✅ | Any | Update user profile |
| **GET** | `/tenants/me` | ✅ | Any | Get current tenant |
| **PUT** | `/tenants/me` | ✅ | OWNER/ADMIN | Update tenant (cascade) |
| **PATCH** | `/tenants/me/status` | ✅ | OWNER | Update tenant status (cascade) |
| **DELETE** | `/tenants/me` | ✅ | OWNER | Soft delete tenant (cascade) |
| **GET** | `/tenants/me/users` | ✅ | OWNER/ADMIN | List users in tenant |
| **GET** | `/.well-known/oauth-authorization-server` | ❌ | - | OAuth 2.1 metadata |

### 9.2 Common Request Headers

```http
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 9.3 Typical Workflow

```
1. Register/Login
   POST /auth/login
   → Get access_token + refresh_token

2. Access Protected Resources
   GET /api/protected/me
   Header: Authorization: Bearer {access_token}

3. Token Expires (after 15 min)
   POST /auth/refresh
   Body: { "refresh_token": "..." }
   → Get new access_token + refresh_token

4. Logout
   POST /auth/logout
   Body: { "refresh_token": "..." }
   → Token revoked
```

### 9.4 TOTP Setup Workflow

```
1. Setup TOTP
   POST /auth/totp/setup
   → Get QR code

2. Scan QR code with authenticator app

3. Verify code
   POST /auth/totp/verify
   Body: { "totp_code": "123456" }
   → TOTP enabled

4. Future logins require TOTP
   POST /auth/login
   Body: { "tenant_email": "...", "password": "...", "totp_code": "123456" }
```

### 9.5 Cascade Update Operations

All tenant management operations automatically cascade to users:

| Operation | Tenant Change | User Cascade |
|-----------|---------------|--------------|
| **PUT /tenants/me** | Update `tenant_name` | Update `tenant_name` for all users |
| **PATCH /tenants/me/status** | Update `is_active` | Update `is_active` for all users |
| **DELETE /tenants/me** | Set `is_active = false` | Set `is_active = false` for all users |

**Key Features:**
- ✅ Atomic operations (all or nothing)
- ✅ Efficient bulk updates (single SQL statement)
- ✅ Tenant isolation (only affects target tenant)
- ✅ Transaction safety with rollback

---

## Interactive Documentation

For interactive API testing and detailed schema information:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

---

## Additional Resources

- **USER_MANUAL.md** - Step-by-step tutorials and examples
- **WORKFLOWS.md** - Detailed workflow diagrams and sequences
- **SCHEMAS.md** - Database schema and architecture documentation
- **CLAUDE.md** - Development guide and code conventions

---

**Last Updated**: January 13, 2026
**Version**: 0.1.0
**Status**: Production Ready

🤖 Generated with [Claude Code](https://claude.com/claude-code)
