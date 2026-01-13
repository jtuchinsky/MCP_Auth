# MCP Auth - User Manual

**Version:** 0.1.0
**Last Updated:** January 12, 2026
**Status:** Production Ready

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Core Concepts](#3-core-concepts)
4. [Basic Tutorials](#4-basic-tutorials)
5. [Advanced Features](#5-advanced-features)
6. [API Reference](#6-api-reference)
7. [Integration Guide](#7-integration-guide)
8. [Troubleshooting](#8-troubleshooting)
9. [Security Best Practices](#9-security-best-practices)
10. [Appendix](#10-appendix)

---

## 1. Introduction

### 1.1 What is MCP Auth?

**MCP Auth** is a production-ready authentication service built with FastAPI that implements:
- **Multi-tenant architecture** - Separate accounts for different organizations
- **OAuth 2.1 compliance** - Modern, secure authentication standard
- **Model Context Protocol (MCP)** - Compatible with AI agents and tools
- **Two-factor authentication** - Optional TOTP-based 2FA for enhanced security

### 1.2 Who Should Use This Service?

MCP Auth is ideal for:
- **SaaS applications** requiring tenant-based authentication
- **AI-powered tools** needing MCP-compliant OAuth
- **Multi-user platforms** with organization-level isolation
- **Developers** building secure authentication systems

### 1.3 Key Features

| Feature | Description |
|---------|-------------|
| **Tenant-Based Authentication** | Each organization (tenant) has its own account |
| **Secure Password Storage** | Bcrypt hashing with 12-round salt |
| **JWT Tokens** | Access tokens (15 min) + refresh tokens (30 days) |
| **Two-Factor Authentication** | Optional TOTP with QR code setup |
| **Token Rotation** | Refresh tokens rotated on each use |
| **Role-Based Access** | OWNER, ADMIN, and MEMBER roles |
| **OAuth 2.1 Compliant** | Full MCP compatibility |

### 1.4 How This Manual is Organized

- **Sections 2-3**: Setup and conceptual overview
- **Section 4**: Step-by-step tutorials for common tasks
- **Section 5**: Advanced features and use cases
- **Sections 6-7**: Complete API reference and integration guide
- **Sections 8-10**: Troubleshooting, security, and reference materials

---

## 2. Getting Started

### 2.1 Prerequisites

Before installing MCP Auth, ensure you have:

#### Required Software
- **Python 3.12 or higher** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **uv** (recommended) or pip ([Install uv](https://github.com/astral-sh/uv))

#### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **RAM**: Minimum 512MB (1GB recommended)
- **Disk Space**: 100MB for application + database
- **Network**: Internet connection for initial setup

#### Knowledge Prerequisites
- Basic command-line usage
- Understanding of HTTP/REST APIs
- Familiarity with JSON format
- Basic authentication concepts (recommended)

### 2.2 Installation

#### Step 1: Clone the Repository

```bash
# Navigate to your projects directory
cd ~/projects

# Clone the repository
git clone https://github.com/jtuchinsky/MCP_Auth.git
cd MCP_Auth
```

#### Step 2: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

**Edit `.env` file** and update the following:

```bash
# REQUIRED: Generate a secure secret key
SECRET_KEY=<your-generated-secret-key>

# Optional: Customize token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Optional: Customize TOTP issuer name
TOTP_ISSUER_NAME=My Company Auth
```

**Generate a Secure Secret Key:**

```bash
# Run this command to generate a secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output:
# 8N3K5L9M2P7Q4R6S1T8U0V3W5X7Y9Z2A

# Copy the output and paste it in .env:
# SECRET_KEY=8N3K5L9M2P7Q4R6S1T8U0V3W5X7Y9Z2A
```

#### Step 3: Install Dependencies

```bash
# Using uv (recommended)
uv sync --extra dev

# OR using pip
pip install -r requirements.txt
```

#### Step 4: Initialize the Database

```bash
# Run database migrations
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> e9258cf92b4d, add tenant-based authentication
INFO  [alembic.runtime.migration] Running upgrade e9258cf92b4d -> e340c902e215, add tenant_name field to tenants
INFO  [alembic.runtime.migration] Running upgrade e340c902e215 -> 24d546efdc36, add tenant_name field to users
```

#### Step 5: Start the Server

```bash
# Start with auto-reload (development)
uvicorn main:app --reload

# OR start for production
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2.3 Verify Installation

#### Check Server Status

Open your browser and visit:
```
http://127.0.0.1:8000/docs
```

You should see the **Swagger UI** interactive API documentation.

#### Run Health Check

```bash
curl http://127.0.0.1:8000/
```

**Expected Response:**
```json
{
  "message": "MCP-Compatible Authentication Service",
  "version": "0.1.0",
  "status": "operational"
}
```

#### Verify Database

```bash
# Check that the database file exists
ls -lh mcp_auth.db

# Inspect tables
sqlite3 mcp_auth.db ".tables"
```

**Expected Output:**
```
alembic_version  refresh_tokens   tenants          users
```

### 2.4 Quick Start Example

Let's create your first tenant and log in:

```bash
# 1. First login creates tenant + owner user automatically
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "mycompany@example.com",
    "tenant_name": "My Company",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Congratulations!** You've successfully:
- Created a new tenant account
- Created an owner user
- Received authentication tokens

---

## 3. Core Concepts

### 3.1 Multi-Tenant Architecture

#### What is a Tenant?

A **tenant** is an independent organization account within the system. Each tenant has:
- **Unique email address** (globally unique across all tenants)
- **Organization name** (optional, e.g., "Acme Corporation")
- **Password** (bcrypt-hashed, shared with owner user)
- **One or more users** (future: invite additional users)

#### Tenant Isolation

Tenants are completely isolated from each other:
- Tenant A cannot access Tenant B's data
- Each tenant has its own user list
- JWT tokens include `tenant_id` for authorization

#### Example Tenant Structure

```
Tenant: mycompany@example.com (ID: 2, Name: "My Company")
├── Owner User: mycompany@example.com (Role: OWNER)
├── User: alice (Role: ADMIN) [Future]
└── User: bob (Role: MEMBER) [Future]

Tenant: competitor@example.com (ID: 3, Name: "Competitor Corp")
├── Owner User: competitor@example.com (Role: OWNER)
└── User: charlie (Role: MEMBER) [Future]
```

### 3.2 Users and Roles

#### User Types

| Role | Description | Capabilities |
|------|-------------|--------------|
| **OWNER** | Tenant owner | Full control, first user in tenant, can invite users (future) |
| **ADMIN** | Administrator | Manage users, elevated permissions (future) |
| **MEMBER** | Standard user | Basic access, read/write own data (future) |

#### Owner User Auto-Creation

When you create a new tenant, an **owner user** is automatically created with:
- **Username** = tenant email
- **Email** = tenant email
- **Password** = tenant password
- **Role** = OWNER

#### Username vs Email

- **Username**: Unique per tenant (e.g., "alice" in Tenant A, "alice" in Tenant B)
- **Email**: Globally unique (e.g., alice@example.com can only belong to one tenant)

### 3.3 Authentication Flow

#### Tenant Login Flow

```
1. Client sends tenant_email + password
   ↓
2. Server looks up tenant by email
   ↓
   ┌─── Tenant exists? ───┐
   │                       │
   YES                    NO
   │                       │
   ├─ Verify password     └─ Create new tenant + owner user
   │                          ↓
   └───────────────────────────┤
                               │
3. Find/create owner user      │
   ↓                          │
4. Generate JWT tokens ────────┘
   ↓
5. Return access_token + refresh_token
```

#### User Login Flow (Future)

```
1. Client sends tenant_email + username + password
   ↓
2. Server looks up tenant by email
   ↓
3. Server looks up user by tenant_id + username
   ↓
4. Verify password
   ↓
5. Generate JWT tokens
   ↓
6. Return access_token + refresh_token
```

### 3.4 Token Management

#### Access Tokens

- **Purpose**: Short-lived token for API authentication
- **Lifetime**: 15 minutes (configurable)
- **Storage**: Client memory (not localStorage)
- **Usage**: Include in `Authorization: Bearer <token>` header

**Access Token Structure (JWT):**
```json
{
  "sub": "1",              // User ID
  "email": "user@example.com",
  "tenant_id": "2",        // Tenant ID
  "username": "alice",     // Username within tenant
  "role": "OWNER",         // User role
  "scopes": [],            // OAuth scopes
  "iat": 1704067200,       // Issued at (Unix timestamp)
  "exp": 1704068100        // Expires at (Unix timestamp)
}
```

#### Refresh Tokens

- **Purpose**: Long-lived token to obtain new access tokens
- **Lifetime**: 30 days (configurable)
- **Storage**: Secure HTTP-only cookies or encrypted storage
- **Usage**: Submit to `/auth/refresh` to get new tokens
- **Rotation**: New refresh token issued on each refresh

**Refresh Token Security:**
- Stored in database for revocation capability
- Single-use (rotated on each refresh)
- Revoked on logout
- Includes client_id for tracking (future)

#### Token Lifecycle

```
1. Login → Receive access + refresh tokens
   ↓
2. Use access token for API calls (15 min)
   ↓
3. Access token expires
   ↓
4. Use refresh token to get new tokens
   ↓
5. Receive new access + refresh tokens (old refresh revoked)
   ↓
6. Repeat steps 2-5 until refresh token expires (30 days)
   ↓
7. Refresh token expires → Re-login required
```

### 3.5 Two-Factor Authentication (TOTP)

#### What is TOTP?

**TOTP (Time-based One-Time Password)** is a 2FA method that generates 6-digit codes that change every 30 seconds.

#### TOTP Setup Flow

```
1. User enables TOTP
   ↓
2. Server generates secret key
   ↓
3. Server returns secret + QR code
   ↓
4. User scans QR code with authenticator app
   ↓
5. User enters 6-digit code to verify
   ↓
6. Server validates code and enables TOTP
   ↓
7. Future logins require TOTP code
```

#### TOTP Login Flow

```
1. User submits email + password
   ↓
2. Server validates credentials
   ↓
   ┌─── TOTP enabled? ───┐
   │                      │
   YES                   NO
   │                      │
   ├─ Require TOTP code  └─ Generate tokens
   │                         ↓
   ├─ User submits code      Return tokens
   │  ↓
   ├─ Validate TOTP code
   │  ↓
   └─ Generate tokens
      ↓
      Return tokens
```

#### Supported Authenticator Apps

- Google Authenticator (iOS, Android)
- Microsoft Authenticator (iOS, Android)
- Authy (iOS, Android, Desktop)
- 1Password (cross-platform)
- Bitwarden (cross-platform)

---

## 4. Basic Tutorials

### 4.1 Tutorial: Create Your First Tenant

In this tutorial, you'll create a new tenant account with an owner user.

#### Step 1: Send Login Request

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "acme@example.com",
    "tenant_name": "Acme Corporation",
    "password": "SecurePassword123!"
  }'
```

#### Step 2: Understand the Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhY21lQGV4YW1wbGUuY29tIiwidGVuYW50X2lkIjoiMiIsInVzZXJuYW1lIjoiYWNtZUBleGFtcGxlLmNvbSIsInJvbGUiOiJPV05FUiIsInNjb3BlcyI6W10sImlhdCI6MTcwNDA2NzIwMCwiZXhwIjoxNzA0MDY4MTAwfQ.XYZ123",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE3MDQwNjcyMDAsImV4cCI6MTcwNjY1OTIwMH0.ABC456",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**What happened:**
1. **Tenant created** with ID=2, email=acme@example.com, name="Acme Corporation"
2. **Owner user created** with username=email, role=OWNER
3. **Tokens generated** for the owner user
4. **expires_in** shows access token valid for 900 seconds (15 minutes)

#### Step 3: Save Your Tokens

**Save the tokens securely:**
```bash
# Export to environment variables (for testing only)
export ACCESS_TOKEN="eyJhbGc..."
export REFRESH_TOKEN="eyJhbGc..."
```

⚠️ **Security Note**: In production, store tokens in:
- **Access tokens**: Memory only (never localStorage)
- **Refresh tokens**: HTTP-only cookies or encrypted storage

#### Step 4: Decode Your Access Token

Visit [jwt.io](https://jwt.io) and paste your access token to inspect:

```json
{
  "sub": "1",
  "email": "acme@example.com",
  "tenant_id": "2",
  "username": "acme@example.com",
  "role": "OWNER",
  "scopes": [],
  "iat": 1704067200,
  "exp": 1704068100
}
```

### 4.2 Tutorial: Access Protected Endpoints

Now let's use your access token to call a protected endpoint.

#### Step 1: Get Current User Profile

```bash
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### Step 2: Understand the Response

```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "acme@example.com",
  "email": "acme@example.com",
  "role": "OWNER",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2026-01-12T10:30:00Z",
  "updated_at": "2026-01-12T10:30:00Z"
}
```

**What you see:**
- Your user ID (unique across all tenants)
- Your tenant ID (organization you belong to)
- Your username and email (same for owner users)
- Your role (OWNER for first user in tenant)
- TOTP status (disabled by default)
- Account creation timestamps

#### Step 3: Try Without Authorization

```bash
curl -X GET "http://127.0.0.1:8000/api/protected/me"
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

**Why?** Protected endpoints require a valid access token in the `Authorization` header.

### 4.3 Tutorial: Refresh Your Tokens

When your access token expires (after 15 minutes), use the refresh token to get new tokens.

#### Step 1: Check Token Expiration

```bash
# Decode your access token at jwt.io
# Look for "exp" field (Unix timestamp)

# Example: exp=1704068100
# Convert to human-readable:
date -r 1704068100
# Output: Sun Jan  1 00:01:40 UTC 2024
```

#### Step 2: Refresh Tokens

```bash
curl -X POST "http://127.0.0.1:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

#### Step 3: Receive New Tokens

```json
{
  "access_token": "eyJhbGc...NEW_TOKEN",
  "refresh_token": "eyJhbGc...NEW_REFRESH_TOKEN",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**What happened:**
1. Server validated your refresh token
2. Server generated new access + refresh tokens
3. **Old refresh token was revoked** (can't be reused)
4. You have 15 more minutes of access

#### Step 4: Update Your Tokens

```bash
# Update environment variables with new tokens
export ACCESS_TOKEN="eyJhbGc...NEW_TOKEN"
export REFRESH_TOKEN="eyJhbGc...NEW_REFRESH_TOKEN"
```

### 4.4 Tutorial: Enable Two-Factor Authentication

Let's secure your account with TOTP-based 2FA.

#### Step 1: Enable TOTP

```bash
curl -X POST "http://127.0.0.1:8000/api/protected/totp/enable" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### Step 2: Receive TOTP Setup Data

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_data_uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
  "issuer": "MCP Auth Service",
  "account_name": "acme@example.com"
}
```

**What you received:**
- **secret**: Base32-encoded secret key (backup manually)
- **qr_code_data_uri**: QR code image (scan with authenticator app)
- **issuer**: Service name shown in authenticator app
- **account_name**: Your email shown in authenticator app

#### Step 3: Scan QR Code

1. Open your authenticator app (Google Authenticator, Authy, etc.)
2. Tap "Add account" or "+"
3. Choose "Scan QR code"
4. Scan the QR code displayed in your browser (paste data URI in HTML)
5. Verify the account shows "MCP Auth Service (acme@example.com)"

**Alternative: Manual Entry**
1. Choose "Enter setup key" in your authenticator app
2. Enter account name: `acme@example.com`
3. Enter secret key: `JBSWY3DPEHPK3PXP`
4. Choose "Time-based" (not counter-based)

#### Step 4: Verify TOTP

Your authenticator app now shows a 6-digit code that changes every 30 seconds. Let's verify it:

```bash
# Get the current code from your authenticator app
# Example: 123456

curl -X POST "http://127.0.0.1:8000/api/protected/totp/verify" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"totp_code": "123456"}'
```

#### Step 5: Confirmation Response

```json
{
  "message": "TOTP verification successful",
  "is_totp_enabled": true
}
```

**TOTP is now enabled!** Future logins will require your authenticator code.

#### Step 6: Test TOTP Login

```bash
# Logout first (optional)
curl -X POST "http://127.0.0.1:8000/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Now login with TOTP
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "acme@example.com",
    "password": "SecurePassword123!",
    "totp_code": "789012"
  }'
```

**Replace `789012` with the current code from your authenticator app.**

### 4.5 Tutorial: Logout and Revoke Tokens

#### Step 1: Logout

```bash
curl -X POST "http://127.0.0.1:8000/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### Step 2: Confirmation Response

```json
{
  "message": "Successfully logged out"
}
```

**What happened:**
- Your refresh token was revoked in the database
- You can no longer use it to get new access tokens
- Your access token is still valid until it expires (15 min)

#### Step 3: Verify Logout

```bash
# Try to refresh with old token
curl -X POST "http://127.0.0.1:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

#### Step 4: Wait for Access Token Expiration

Your access token remains valid for up to 15 minutes after logout. To immediately invalidate it, you would need to:
- Implement token blacklist (not currently in service)
- Wait for natural expiration
- Client-side: Delete the token from memory

---

## 5. Advanced Features

### 5.1 OAuth 2.1 Discovery

MCP Auth implements OAuth 2.1 server metadata for automatic discovery.

#### Get Server Metadata

```bash
curl http://127.0.0.1:8000/.well-known/oauth-authorization-server
```

#### Response

```json
{
  "issuer": "http://127.0.0.1:8000",
  "authorization_endpoint": "http://127.0.0.1:8000/auth/authorize",
  "token_endpoint": "http://127.0.0.1:8000/auth/token",
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "revocation_endpoint": "http://127.0.0.1:8000/auth/revoke"
}
```

**Use Cases:**
- OAuth client auto-configuration
- MCP agent discovery
- Dynamic service integration

### 5.2 Token Inspection

#### Decode Access Token (Client-Side)

```javascript
// JavaScript example
function decodeJWT(token) {
  const payload = token.split('.')[1];
  const decoded = atob(payload);
  return JSON.parse(decoded);
}

const accessToken = "eyJhbGc...";
const payload = decodeJWT(accessToken);
console.log(payload);
// {
//   "sub": "1",
//   "email": "acme@example.com",
//   "tenant_id": "2",
//   "exp": 1704068100
// }
```

#### Check Token Expiration

```javascript
function isTokenExpired(token) {
  const payload = decodeJWT(token);
  const now = Math.floor(Date.now() / 1000);
  return payload.exp < now;
}

if (isTokenExpired(accessToken)) {
  // Refresh the token
  refreshAccessToken();
}
```

### 5.3 Handling Token Refresh Automatically

#### JavaScript/TypeScript Example

```javascript
class AuthClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.accessToken = null;
    this.refreshToken = null;
  }

  async login(tenantEmail, password, totpCode = null) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_email: tenantEmail,
        password: password,
        totp_code: totpCode
      })
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    return data;
  }

  async refreshAccessToken() {
    const response = await fetch(`${this.baseURL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    return data;
  }

  async request(endpoint, options = {}) {
    // Add authorization header
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`
    };

    let response = await fetch(`${this.baseURL}${endpoint}`, options);

    // If 401, try refreshing token once
    if (response.status === 401) {
      await this.refreshAccessToken();
      options.headers['Authorization'] = `Bearer ${this.accessToken}`;
      response = await fetch(`${this.baseURL}${endpoint}`, options);
    }

    return response.json();
  }
}

// Usage
const auth = new AuthClient('http://127.0.0.1:8000');
await auth.login('acme@example.com', 'SecurePassword123!');

// Automatically handles token refresh
const profile = await auth.request('/api/protected/me');
console.log(profile);
```

#### Python Example

```python
import requests
from datetime import datetime, timedelta

class AuthClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def login(self, tenant_email, password, totp_code=None):
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "tenant_email": tenant_email,
                "password": password,
                "totp_code": totp_code
            }
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_at = datetime.now() + timedelta(seconds=data["expires_in"])

        return data

    def refresh_access_token(self):
        response = requests.post(
            f"{self.base_url}/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_at = datetime.now() + timedelta(seconds=data["expires_in"])

        return data

    def request(self, endpoint, method="GET", **kwargs):
        # Check if token needs refresh
        if self.expires_at and datetime.now() >= self.expires_at:
            self.refresh_access_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )

        # If 401, try refreshing once
        if response.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )

        response.raise_for_status()
        return response.json()

# Usage
auth = AuthClient("http://127.0.0.1:8000")
auth.login("acme@example.com", "SecurePassword123!")

# Automatically handles token refresh
profile = auth.request("/api/protected/me")
print(profile)
```

### 5.4 TOTP Backup and Recovery

#### Backup Your TOTP Secret

When you enable TOTP, **save the secret key** in a secure location:

```
Secret: JBSWY3DPEHPK3PXP
Account: acme@example.com
Issuer: MCP Auth Service
```

#### Manual Entry on New Device

1. Open authenticator app on new device
2. Select "Enter setup key manually"
3. Enter saved secret key
4. Choose "Time-based" type
5. Verify 6-digit code matches original device

#### Lost Authenticator Access

⚠️ **Currently not implemented**: TOTP recovery mechanism

**Workarounds:**
1. Use TOTP secret backup to restore on new device
2. Admin can reset TOTP in database (development only)
3. Future: Recovery codes feature

### 5.5 Working with Multiple Tenants

#### Scenario: Managing Multiple Organizations

As a developer or user with multiple tenant accounts:

```bash
# Tenant 1: Personal account
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "personal@example.com",
    "password": "Password1"
  }'
# Save tokens as PERSONAL_ACCESS_TOKEN, PERSONAL_REFRESH_TOKEN

# Tenant 2: Work account
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "work@company.com",
    "password": "Password2"
  }'
# Save tokens as WORK_ACCESS_TOKEN, WORK_REFRESH_TOKEN

# Access personal account
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer $PERSONAL_ACCESS_TOKEN"

# Access work account
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer $WORK_ACCESS_TOKEN"
```

#### Client-Side Multi-Tenant Management

```javascript
class MultiTenantAuth {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.tenants = new Map(); // email -> AuthClient
    this.currentTenant = null;
  }

  async addTenant(email, password) {
    const client = new AuthClient(this.baseURL);
    await client.login(email, password);
    this.tenants.set(email, client);
    this.currentTenant = email;
    return client;
  }

  switchTenant(email) {
    if (!this.tenants.has(email)) {
      throw new Error(`Tenant ${email} not logged in`);
    }
    this.currentTenant = email;
  }

  getCurrentClient() {
    return this.tenants.get(this.currentTenant);
  }

  async request(endpoint, options = {}) {
    const client = this.getCurrentClient();
    return client.request(endpoint, options);
  }
}

// Usage
const auth = new MultiTenantAuth('http://127.0.0.1:8000');
await auth.addTenant('personal@example.com', 'Pass1');
await auth.addTenant('work@company.com', 'Pass2');

// Switch between tenants
auth.switchTenant('personal@example.com');
const personalProfile = await auth.request('/api/protected/me');

auth.switchTenant('work@company.com');
const workProfile = await auth.request('/api/protected/me');
```

---

## 6. API Reference

### 6.1 Authentication Endpoints

#### POST /auth/login

**Description**: Login as tenant (auto-creates tenant + owner user if new)

**Request Body:**
```json
{
  "tenant_email": "company@example.com",
  "tenant_name": "Acme Corporation",  // Optional
  "password": "SecurePassword123!",
  "totp_code": "123456"               // Required if TOTP enabled
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Errors:**
- `400 Bad Request`: Invalid email format
- `401 Unauthorized`: Incorrect password
- `401 Unauthorized`: Invalid or missing TOTP code

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "acme@example.com",
    "tenant_name": "Acme Corp",
    "password": "SecurePassword123!"
  }'
```

---

#### POST /auth/login-user

**Description**: Login as user within tenant (future: when multiple users exist)

**Status**: 🚧 Pending (requires user invitation system)

**Request Body:**
```json
{
  "tenant_email": "company@example.com",
  "username": "alice",
  "password": "UserPassword123!",
  "totp_code": "123456"
}
```

---

#### POST /auth/refresh

**Description**: Refresh access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...NEW",
  "refresh_token": "eyJhbGc...NEW",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token
- `401 Unauthorized`: Refresh token has been revoked

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGc..."}'
```

---

#### POST /auth/logout

**Description**: Revoke refresh token and logout

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/auth/logout" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 6.2 Protected Endpoints

#### GET /api/protected/me

**Description**: Get current user profile

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "tenant_id": 2,
  "username": "acme@example.com",
  "email": "acme@example.com",
  "role": "OWNER",
  "is_totp_enabled": false,
  "is_active": true,
  "created_at": "2026-01-12T10:30:00Z",
  "updated_at": "2026-01-12T10:30:00Z"
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `403 Forbidden`: User is inactive

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 6.3 TOTP Endpoints

#### POST /api/protected/totp/enable

**Description**: Enable TOTP 2FA (step 1: get secret + QR code)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_data_uri": "data:image/png;base64,iVBORw0KGg...",
  "issuer": "MCP Auth Service",
  "account_name": "acme@example.com"
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `400 Bad Request`: TOTP already enabled

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/protected/totp/enable" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### POST /api/protected/totp/verify

**Description**: Verify TOTP code (step 2: complete TOTP setup)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "totp_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "TOTP verification successful",
  "is_totp_enabled": true
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `400 Bad Request`: Invalid TOTP code
- `400 Bad Request`: TOTP not set up yet (call /enable first)

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/protected/totp/verify" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"totp_code": "123456"}'
```

---

#### POST /api/protected/totp/disable

**Description**: Disable TOTP 2FA

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "totp_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "TOTP disabled successfully"
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `400 Bad Request`: Invalid TOTP code
- `400 Bad Request`: TOTP not enabled

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/protected/totp/disable" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"totp_code": "123456"}'
```

---

### 6.4 Discovery Endpoints

#### GET /.well-known/oauth-authorization-server

**Description**: OAuth 2.1 server metadata (RFC 8414)

**Response (200 OK):**
```json
{
  "issuer": "http://127.0.0.1:8000",
  "authorization_endpoint": "http://127.0.0.1:8000/auth/authorize",
  "token_endpoint": "http://127.0.0.1:8000/auth/token",
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "revocation_endpoint": "http://127.0.0.1:8000/auth/revoke"
}
```

**Example:**
```bash
curl http://127.0.0.1:8000/.well-known/oauth-authorization-server
```

---

### 6.5 Tenant Management Endpoints

#### GET /tenants/me

**Description**: Get current user's tenant information

**Authorization**: Any authenticated user (OWNER, ADMIN, MEMBER)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "company@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": true,
  "created_at": "2026-01-11T10:30:00Z",
  "updated_at": "2026-01-11T10:30:00Z"
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `404 Not Found`: Tenant not found

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/tenants/me" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### PUT /tenants/me

**Description**: Update current user's tenant information (e.g., tenant name)

**Authorization**: OWNER or ADMIN role required

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "tenant_name": "New Company Name"
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "company@example.com",
  "tenant_name": "New Company Name",
  "is_active": true,
  "created_at": "2026-01-11T10:30:00Z",
  "updated_at": "2026-01-12T15:45:00Z"
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `403 Forbidden`: User is not OWNER or ADMIN
- `404 Not Found`: Tenant not found

**Example:**
```bash
curl -X PUT "http://127.0.0.1:8000/tenants/me" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"tenant_name": "New Company Name"}'
```

---

#### PATCH /tenants/me/status

**Description**: Activate or deactivate the tenant

**Authorization**: OWNER role required

**⚠️ Warning**: Deactivating a tenant will prevent all users in the tenant from logging in.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "company@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": false,
  "created_at": "2026-01-11T10:30:00Z",
  "updated_at": "2026-01-12T16:00:00Z"
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `403 Forbidden`: User is not OWNER
- `404 Not Found`: Tenant not found

**Example:**
```bash
# Deactivate tenant
curl -X PATCH "http://127.0.0.1:8000/tenants/me/status" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Reactivate tenant
curl -X PATCH "http://127.0.0.1:8000/tenants/me/status" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

---

#### DELETE /tenants/me

**Description**: Soft delete (deactivate) current user's tenant

**Authorization**: OWNER role required

**⚠️ Important**: This is a soft delete - the tenant is marked as inactive but not removed from the database. All users in this tenant will be unable to log in.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):**
No response body

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `403 Forbidden`: User is not OWNER
- `404 Not Found`: Tenant not found

**Example:**
```bash
curl -X DELETE "http://127.0.0.1:8000/tenants/me" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### GET /tenants/me/users

**Description**: List all users in the current user's tenant

**Authorization**: OWNER or ADMIN role required

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "tenant_id": 2,
    "tenant_name": "Acme Corporation",
    "username": "company@example.com",
    "email": "company@example.com",
    "role": "OWNER",
    "is_totp_enabled": false,
    "is_active": true,
    "created_at": "2026-01-11T10:30:00Z",
    "updated_at": "2026-01-11T10:30:00Z"
  },
  {
    "id": 2,
    "tenant_id": 2,
    "tenant_name": "Acme Corporation",
    "username": "alice",
    "email": "alice@acme.com",
    "role": "MEMBER",
    "is_totp_enabled": true,
    "is_active": true,
    "created_at": "2026-01-11T11:00:00Z",
    "updated_at": "2026-01-11T11:00:00Z"
  }
]
```

**Errors:**
- `401 Unauthorized`: Missing or invalid access token
- `403 Forbidden`: User is not OWNER or ADMIN

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/tenants/me/users" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

**Role-Based Authorization Matrix:**

| Endpoint | OWNER | ADMIN | MEMBER |
|----------|-------|-------|--------|
| GET /tenants/me | ✅ | ✅ | ✅ |
| PUT /tenants/me | ✅ | ✅ | ❌ |
| PATCH /tenants/me/status | ✅ | ❌ | ❌ |
| DELETE /tenants/me | ✅ | ❌ | ❌ |
| GET /tenants/me/users | ✅ | ✅ | ❌ |

---

## 7. Integration Guide

### 7.1 Integration Checklist

Before integrating MCP Auth into your application:

- [ ] MCP Auth service is running and accessible
- [ ] You have tested tenant creation and login
- [ ] You understand token lifecycle (access + refresh)
- [ ] You have a plan for storing tokens securely
- [ ] You know how to handle token refresh
- [ ] You have tested 2FA flow (if using TOTP)

### 7.2 Web Application Integration

#### Frontend (React Example)

**1. Create Auth Context:**

```javascript
// contexts/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { AuthClient } from '../services/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const auth = new AuthClient('http://127.0.0.1:8000');

  useEffect(() => {
    // Load tokens from storage on mount
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (accessToken && refreshToken) {
      auth.accessToken = accessToken;
      auth.refreshToken = refreshToken;
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const profile = await auth.request('/api/protected/me');
      setUser(profile);
    } catch (error) {
      console.error('Failed to load user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, totpCode) => {
    const data = await auth.login(email, password, totpCode);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    await loadUser();
    return data;
  };

  const logout = () => {
    auth.logout();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, auth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

**2. Login Component:**

```javascript
// components/Login.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password, totpCode || null);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}

      <input
        type="email"
        placeholder="Tenant Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <input
        type="text"
        placeholder="2FA Code (if enabled)"
        value={totpCode}
        onChange={(e) => setTotpCode(e.target.value)}
        maxLength={6}
      />

      <button type="submit">Login</button>
    </form>
  );
};
```

**3. Protected Route:**

```javascript
// components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  return children;
};
```

#### Backend (Node.js/Express Example)

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');
const axios = require('axios');

const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://127.0.0.1:8000';

async function verifyToken(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid authorization header' });
  }

  const token = authHeader.slice(7); // Remove 'Bearer '

  try {
    // Option 1: Verify JWT locally (faster, but requires shared secret)
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();

    // Option 2: Validate with auth service (slower, but always accurate)
    // const response = await axios.get(`${AUTH_SERVICE_URL}/api/protected/me`, {
    //   headers: { Authorization: `Bearer ${token}` }
    // });
    // req.user = response.data;
    // next();

  } catch (error) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

module.exports = { verifyToken };
```

```javascript
// routes/api.js
const express = require('express');
const { verifyToken } = require('../middleware/auth');

const router = express.Router();

// Protected route example
router.get('/profile', verifyToken, (req, res) => {
  res.json({
    message: `Hello ${req.user.username}!`,
    tenant_id: req.user.tenant_id,
    role: req.user.role
  });
});

module.exports = router;
```

### 7.3 Mobile Application Integration

#### iOS (Swift Example)

```swift
// AuthService.swift
import Foundation

class AuthService {
    static let shared = AuthService()
    private let baseURL = "http://127.0.0.1:8000"

    var accessToken: String?
    var refreshToken: String?

    func login(tenantEmail: String, password: String, totpCode: String? = nil) async throws -> LoginResponse {
        let url = URL(string: "\(baseURL)/auth/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "tenant_email": tenantEmail,
            "password": password,
            "totp_code": totpCode ?? NSNull()
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw AuthError.loginFailed
        }

        let loginResponse = try JSONDecoder().decode(LoginResponse.self, from: data)
        self.accessToken = loginResponse.accessToken
        self.refreshToken = loginResponse.refreshToken

        // Save tokens to Keychain
        try saveToKeychain(accessToken: loginResponse.accessToken, refreshToken: loginResponse.refreshToken)

        return loginResponse
    }

    func request<T: Decodable>(endpoint: String, method: String = "GET") async throws -> T {
        guard var accessToken = accessToken else {
            throw AuthError.notAuthenticated
        }

        let url = URL(string: "\(baseURL)\(endpoint)")!
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        var (data, response) = try await URLSession.shared.data(for: request)

        // If 401, try refreshing token
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 401 {
            try await refreshAccessToken()
            accessToken = self.accessToken!
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
            (data, response) = try await URLSession.shared.data(for: request)
        }

        return try JSONDecoder().decode(T.self, from: data)
    }

    private func refreshAccessToken() async throws {
        // Implementation similar to login
    }

    private func saveToKeychain(accessToken: String, refreshToken: String) throws {
        // Implementation using Keychain Services
    }
}

struct LoginResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let expiresIn: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
        case expiresIn = "expires_in"
    }
}

enum AuthError: Error {
    case loginFailed
    case notAuthenticated
}
```

#### Android (Kotlin Example)

```kotlin
// AuthService.kt
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*

interface AuthApi {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("auth/refresh")
    suspend fun refresh(@Body request: RefreshRequest): LoginResponse

    @GET("api/protected/me")
    suspend fun getProfile(@Header("Authorization") auth: String): UserProfile
}

data class LoginRequest(
    val tenant_email: String,
    val password: String,
    val totp_code: String? = null
)

data class RefreshRequest(
    val refresh_token: String
)

data class LoginResponse(
    val access_token: String,
    val refresh_token: String,
    val token_type: String,
    val expires_in: Int
)

data class UserProfile(
    val id: Int,
    val tenant_id: Int,
    val username: String,
    val email: String,
    val role: String
)

class AuthService {
    private val retrofit = Retrofit.Builder()
        .baseUrl("http://127.0.0.1:8000/")
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    private val api = retrofit.create(AuthApi::class.java)

    var accessToken: String? = null
    var refreshToken: String? = null

    suspend fun login(email: String, password: String, totpCode: String? = null): LoginResponse {
        val response = api.login(LoginRequest(email, password, totpCode))
        accessToken = response.access_token
        refreshToken = response.refresh_token
        return response
    }

    suspend fun getProfile(): UserProfile {
        return api.getProfile("Bearer $accessToken")
    }

    suspend fun refreshAccessToken() {
        val response = api.refresh(RefreshRequest(refreshToken!!))
        accessToken = response.access_token
        refreshToken = response.refresh_token
    }
}
```

### 7.4 API Gateway Integration

If you're using an API gateway (e.g., Kong, AWS API Gateway), configure it to validate JWT tokens:

#### Kong Example

```bash
# Add JWT plugin to Kong service
curl -X POST http://localhost:8001/services/my-service/plugins \
  --data "name=jwt" \
  --data "config.secret_is_base64=false" \
  --data "config.key_claim_name=sub"

# Add JWT credential for consumer
curl -X POST http://localhost:8001/consumers/my-consumer/jwt \
  --data "algorithm=HS256" \
  --data "secret=your-jwt-secret-key"
```

#### NGINX Example

```nginx
# nginx.conf
location /api/ {
    auth_request /auth;
    proxy_pass http://backend:3000;
}

location = /auth {
    internal;
    proxy_pass http://127.0.0.1:8000/api/protected/me;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
}
```

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Issue: "Not authenticated" Error

**Symptoms:**
```json
{
  "detail": "Not authenticated"
}
```

**Possible Causes:**
1. Missing `Authorization` header
2. Incorrect header format (should be `Bearer <token>`)
3. Expired access token
4. Invalid token (corrupted or tampered with)

**Solutions:**
```bash
# Check header format
curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: Bearer eyJhbGc..."  # Correct

curl -X GET "http://127.0.0.1:8000/api/protected/me" \
  -H "Authorization: eyJhbGc..."  # WRONG - missing "Bearer "

# Refresh your token
curl -X POST "http://127.0.0.1:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'

# Login again if refresh fails
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "your_email@example.com",
    "password": "your_password"
  }'
```

---

#### Issue: "Invalid or expired refresh token"

**Symptoms:**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

**Possible Causes:**
1. Refresh token has expired (after 30 days)
2. Refresh token was revoked (after logout)
3. Token was already used (single-use rotation)

**Solutions:**
- Re-login to get new tokens
- Check if you logged out from another session
- Ensure you're using the latest refresh token (updated after each refresh)

---

#### Issue: "Incorrect password" or "User not found"

**Symptoms:**
```json
{
  "detail": "Incorrect password"
}
```

**Possible Causes:**
1. Wrong password
2. Wrong tenant email
3. Case sensitivity in email
4. TOTP code required but not provided

**Solutions:**
```bash
# Verify email is correct (case-insensitive)
# Both work: mycompany@example.com, MyCompany@example.com

# If TOTP enabled, include code
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_email": "mycompany@example.com",
    "password": "correct_password",
    "totp_code": "123456"
  }'

# Reset password (not implemented yet)
# Contact admin to reset in database
```

---

#### Issue: "TOTP verification failed"

**Symptoms:**
```json
{
  "detail": "Invalid TOTP code"
}
```

**Possible Causes:**
1. Code expired (codes change every 30 seconds)
2. Time sync issue between server and authenticator
3. Wrong TOTP secret entered in authenticator app

**Solutions:**
1. Try next code (wait 30 seconds)
2. Check server time: `date` (should be accurate)
3. Check device time sync (enable automatic time)
4. Verify TOTP secret matches what you scanned

---

#### Issue: Database Migration Errors

**Symptoms:**
```
sqlalchemy.exc.OperationalError: no such table: users
```

**Possible Causes:**
1. Migrations not run
2. Database file deleted
3. Wrong database URL

**Solutions:**
```bash
# Check current migration version
alembic current

# Run all pending migrations
alembic upgrade head

# If database is corrupted, reset (CAUTION: deletes all data)
rm mcp_auth.db
alembic upgrade head
```

---

#### Issue: "SECRET_KEY must be at least 32 characters"

**Symptoms:**
```
ValueError: SECRET_KEY must be at least 32 characters
```

**Solution:**
```bash
# Generate a new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
echo "SECRET_KEY=<generated-key>" >> .env

# Restart server
uvicorn main:app --reload
```

---

### 8.2 Debugging Tips

#### Enable Debug Logging

```bash
# Run with debug logging
uvicorn main:app --reload --log-level debug
```

#### Inspect JWT Token

Visit [jwt.io](https://jwt.io) and paste your token to decode:
- Verify `sub` (user ID)
- Check `exp` (expiration timestamp)
- Confirm `tenant_id` is correct

#### Check Database State

```bash
# Open database
sqlite3 mcp_auth.db

# List tenants
SELECT id, email, tenant_name, is_active FROM tenants;

# List users
SELECT id, tenant_id, username, email, role FROM users;

# List refresh tokens
SELECT id, user_id, is_revoked, expires_at FROM refresh_tokens;

# Exit
.exit
```

#### Test with Swagger UI

1. Open http://127.0.0.1:8000/docs
2. Click "Authorize" button
3. Enter `Bearer <your_access_token>`
4. Try endpoints directly in browser

### 8.3 Performance Optimization

#### Caching Access Tokens

```javascript
// Don't fetch profile on every request
// Cache user data in memory or Redux store

const [user, setUser] = useState(null);

// Load once on mount
useEffect(() => {
  if (!user) {
    loadProfile();
  }
}, []);

// Only reload on token refresh
const handleRefresh = async () => {
  await refreshAccessToken();
  await loadProfile(); // Reload profile with new token
};
```

#### Batch API Calls

```javascript
// Instead of multiple sequential calls
const profile = await auth.request('/api/protected/me');
const settings = await auth.request('/api/protected/settings');
const teams = await auth.request('/api/protected/teams');

// Make parallel requests
const [profile, settings, teams] = await Promise.all([
  auth.request('/api/protected/me'),
  auth.request('/api/protected/settings'),
  auth.request('/api/protected/teams')
]);
```

---

## 9. Security Best Practices

### 9.1 Password Security

#### Strong Password Requirements

Implement these rules in your client:
- **Minimum 8 characters** (12+ recommended)
- **Mix of uppercase and lowercase**
- **At least one number**
- **At least one special character**
- **No common passwords** (password123, qwerty, etc.)

#### Password Storage

**Server-side (MCP Auth):**
- ✅ Bcrypt hashing with 12 rounds (automatically done)
- ✅ Salting (automatically done by bcrypt)
- ✅ Never store plaintext passwords

**Client-side:**
- ❌ Never store passwords in localStorage
- ❌ Never store passwords in cookies
- ❌ Never log passwords to console
- ✅ Clear password fields after submission

### 9.2 Token Security

#### Access Token Storage

**DO:**
- ✅ Store in memory (React state, Vuex store)
- ✅ Use short expiration (15 minutes)
- ✅ Include in Authorization header only

**DON'T:**
- ❌ Store in localStorage (XSS vulnerable)
- ❌ Store in sessionStorage (XSS vulnerable)
- ❌ Include in URL query params (logged in server logs)

#### Refresh Token Storage

**Best Practices:**
- ✅ Store in HTTP-only cookies (not accessible via JavaScript)
- ✅ Use secure flag in production (HTTPS only)
- ✅ Set SameSite=Strict to prevent CSRF
- ⚠️ Alternative: Encrypted localStorage (less secure than HTTP-only cookies)

**Example (Express):**
```javascript
// Set refresh token as HTTP-only cookie
res.cookie('refresh_token', refreshToken, {
  httpOnly: true,      // Not accessible via JavaScript
  secure: true,        // HTTPS only (production)
  sameSite: 'strict',  // CSRF protection
  maxAge: 30 * 24 * 60 * 60 * 1000  // 30 days
});
```

### 9.3 HTTPS in Production

⚠️ **CRITICAL**: Always use HTTPS in production

#### Why HTTPS is Required

- **Prevents token interception** (man-in-the-middle attacks)
- **Protects passwords** during transmission
- **Required for secure cookies** (secure flag)
- **Required for OAuth 2.1 compliance**

#### Setting Up HTTPS

**Option 1: Reverse Proxy (NGINX)**
```nginx
server {
    listen 443 ssl;
    server_name auth.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/auth.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/auth.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

**Option 2: Uvicorn with SSL**
```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile ./privkey.pem \
  --ssl-certfile ./fullchain.pem
```

### 9.4 CORS Configuration

#### Development (Allow All)

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Production (Restrict Origins)

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 9.5 Rate Limiting

Implement rate limiting to prevent brute-force attacks:

```python
# Example using slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, data: LoginRequest):
    # Login logic
    pass
```

### 9.6 Security Checklist

Before deploying to production:

#### Server Configuration
- [ ] `SECRET_KEY` is randomly generated (32+ characters)
- [ ] `SECRET_KEY` is stored in environment variable (not in code)
- [ ] HTTPS is enabled
- [ ] CORS is restricted to your domains
- [ ] Rate limiting is implemented
- [ ] Database is backed up regularly

#### Token Configuration
- [ ] Access token expiration is short (15 minutes)
- [ ] Refresh token expiration is reasonable (30 days)
- [ ] Tokens are rotated on refresh
- [ ] Tokens are revoked on logout

#### Client Configuration
- [ ] Access tokens stored in memory only
- [ ] Refresh tokens stored in HTTP-only cookies
- [ ] Passwords never stored client-side
- [ ] HTTPS used for all requests
- [ ] Token refresh implemented correctly

#### Monitoring
- [ ] Failed login attempts logged
- [ ] Unusual activity alerts configured
- [ ] Token expiration metrics tracked
- [ ] Database backups automated

---

## 10. Appendix

### 10.1 Error Codes Reference

| Status Code | Error | Description | Solution |
|-------------|-------|-------------|----------|
| 400 | Bad Request | Invalid request format or parameters | Check request body format |
| 401 | Not authenticated | Missing or invalid access token | Login or refresh token |
| 401 | Incorrect password | Wrong password | Verify password |
| 401 | Invalid TOTP code | Wrong 2FA code | Check authenticator app |
| 401 | Invalid refresh token | Refresh token expired or revoked | Login again |
| 403 | Forbidden | User is inactive | Contact admin |
| 404 | Not Found | Endpoint doesn't exist | Check URL |
| 422 | Validation Error | Pydantic validation failed | Check request fields |
| 500 | Internal Server Error | Server error | Check server logs |

### 10.2 Glossary

| Term | Definition |
|------|------------|
| **Access Token** | Short-lived JWT used to authenticate API requests (15 min) |
| **Authenticator App** | Mobile app generating TOTP codes (Google Authenticator, Authy) |
| **Base32** | Encoding format for TOTP secrets (letters A-Z, numbers 2-7) |
| **Bcrypt** | Password hashing algorithm with automatic salting |
| **JWT** | JSON Web Token - secure token format for authentication |
| **MCP** | Model Context Protocol - AI agent communication standard |
| **OAuth 2.1** | Modern authentication and authorization protocol |
| **Owner User** | First user in tenant with full privileges |
| **PKCE** | Proof Key for Code Exchange - OAuth security extension |
| **QR Code** | 2D barcode for easily transferring TOTP secrets |
| **Refresh Token** | Long-lived token used to obtain new access tokens (30 days) |
| **Role** | User permission level (OWNER, ADMIN, MEMBER) |
| **Tenant** | Independent organization account within the system |
| **TOTP** | Time-based One-Time Password - 6-digit 2FA codes |
| **2FA/MFA** | Two-Factor/Multi-Factor Authentication |

### 10.3 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./mcp_auth.db` | Database connection string |
| `SECRET_KEY` | Yes | - | JWT signing key (min 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `30` | Refresh token lifetime |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `TOTP_ISSUER_NAME` | No | `MCP Auth Service` | Name in authenticator app |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins |

### 10.4 Database Schema Summary

#### Tenants Table
```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    tenant_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    tenant_name VARCHAR(255),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'MEMBER',
    totp_secret VARCHAR(32),
    is_totp_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE (tenant_id, username)
);
```

#### Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token VARCHAR UNIQUE NOT NULL,
    client_id VARCHAR,
    scope VARCHAR,
    is_revoked BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 10.5 Useful Commands

#### Database
```bash
# View database schema
sqlite3 mcp_auth.db ".schema"

# Backup database
cp mcp_auth.db mcp_auth.db.backup

# Restore database
cp mcp_auth.db.backup mcp_auth.db

# Reset database (CAUTION: deletes all data)
rm mcp_auth.db && alembic upgrade head
```

#### Server
```bash
# Start server
uvicorn main:app --reload

# Start with specific port
uvicorn main:app --port 8080

# Start with HTTPS
uvicorn main:app --ssl-keyfile key.pem --ssl-certfile cert.pem

# Run in background
nohup uvicorn main:app &
```

#### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/integration/test_auth_endpoints.py

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 10.6 Additional Resources

#### Documentation
- **MCP Auth GitHub**: https://github.com/jtuchinsky/MCP_Auth
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **JWT.io**: https://jwt.io (decode and inspect tokens)
- **OAuth 2.1 Spec**: https://oauth.net/2.1/
- **RFC 6238 (TOTP)**: https://tools.ietf.org/html/rfc6238

#### Tools
- **Postman**: API testing tool with collection support
- **Insomnia**: Alternative API testing tool
- **curl**: Command-line HTTP client
- **jq**: JSON processor for command-line
- **Swagger UI**: Interactive API documentation (built-in)

#### Authenticator Apps
- **Google Authenticator**: https://g.co/authenticator
- **Microsoft Authenticator**: https://www.microsoft.com/en-us/security/mobile-authenticator-app
- **Authy**: https://authy.com
- **1Password**: https://1password.com
- **Bitwarden**: https://bitwarden.com

---

## Support and Feedback

### Getting Help

- **Issues**: Report bugs at https://github.com/jtuchinsky/MCP_Auth/issues
- **Discussions**: Ask questions at https://github.com/jtuchinsky/MCP_Auth/discussions
- **Email**: contact@yourdomain.com

### Contributing

Contributions are welcome! See CONTRIBUTING.md for guidelines.

### License

This project is licensed under the MIT License. See LICENSE for details.

---

**Last Updated**: January 12, 2026
**Version**: 0.1.0
**Status**: Production Ready

🤖 Generated with [Claude Code](https://claude.com/claude-code)
