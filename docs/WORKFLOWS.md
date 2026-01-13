# MCP Auth - Workflows Documentation

**Version:** 0.1.0
**Last Updated:** January 13, 2026
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tenant Registration & First Login](#2-tenant-registration--first-login)
3. [Tenant Login (Returning User)](#3-tenant-login-returning-user)
4. [User Login (Multi-User)](#4-user-login-multi-user)
5. [Token Refresh Workflow](#5-token-refresh-workflow)
6. [TOTP Setup Workflow](#6-totp-setup-workflow)
7. [TOTP Login Workflow](#7-totp-login-workflow)
8. [TOTP Disable Workflow](#8-totp-disable-workflow)
9. [Protected Endpoint Access](#9-protected-endpoint-access)
10. [Logout Workflow](#10-logout-workflow)
11. [Tenant Update Workflow](#11-tenant-update-workflow)
12. [Tenant Status Update Workflow](#12-tenant-status-update-workflow)
13. [Tenant Deletion Workflow](#13-tenant-deletion-workflow)
14. [Error Handling Patterns](#14-error-handling-patterns)
15. [State Diagrams](#15-state-diagrams)

---

## 1. Overview

### 1.1 Workflow Categories

MCP Auth implements four categories of workflows:

| Category | Workflows | Description |
|----------|-----------|-------------|
| **Authentication** | Tenant Registration, Login, TOTP Login | User identity verification |
| **Token Management** | Token Refresh, Logout | Access token lifecycle |
| **Security** | TOTP Setup, TOTP Disable | Two-factor authentication |
| **Authorization** | Protected Endpoint Access | Resource access control |
| **Tenant Management** | Tenant Update, Status Update, Deletion | Tenant CRUD with cascade updates |

### 1.2 Workflow Symbols

Throughout this document, we use the following symbols:

```
┌─────┐
│ BOX │  = Process step
└─────┘

───────▶  = Flow direction

◆ Decision point

✓ Success path
✗ Error path

[API] = API endpoint call
{DB}  = Database operation
```

### 1.3 Common HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication failed |
| 403 | Forbidden | Authorization failed |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## 2. Tenant Registration & First Login

### 2.1 Workflow Overview

**Purpose**: Create a new tenant account with an owner user on first login.

**Trigger**: User submits login form with email that doesn't exist in system.

**Result**: New tenant + owner user created, authentication tokens returned.

### 2.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    TENANT REGISTRATION WORKFLOW                  │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /auth/login─────────▶                               │
    │   tenant_email                │                              │
    │   tenant_name (optional)      │                              │
    │   password                    │                              │
    │                               │                              │
    │                               ├─[2] Normalize email─────────▶│
    │                               │     (lowercase)              │
    │                               │                              │
    │                               ├─[3] Query tenant by email───▶│
    │                               │                              │
    │                               │◄─[4] Tenant not found────────┤
    │                               │                              │
    │                               ├─[5] Hash password───────────▶│
    │                               │     (bcrypt 12 rounds)       │
    │                               │                              │
    │                               ├─[6] Create tenant───────────▶│
    │                               │     INSERT INTO tenants      │
    │                               │                              │
    │                               │◄─[7] Return tenant.id────────┤
    │                               │                              │
    │                               ├─[8] Create owner user───────▶│
    │                               │     username = tenant_email  │
    │                               │     role = OWNER             │
    │                               │     INSERT INTO users        │
    │                               │                              │
    │                               │◄─[9] Return user.id──────────┤
    │                               │                              │
    │                               ├─[10] Generate JWT tokens────▶│
    │                               │      access_token (15 min)   │
    │                               │      refresh_token (30 days) │
    │                               │                              │
    │                               ├─[11] Store refresh token────▶│
    │                               │      INSERT refresh_tokens   │
    │                               │                              │
    │◄──[12] Return tokens──────────┤                              │
    │   {                           │                              │
    │     access_token,             │                              │
    │     refresh_token,            │                              │
    │     token_type: "Bearer",     │                              │
    │     expires_in: 900           │                              │
    │   }                           │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 2.3 Step-by-Step Walkthrough

#### Step 1: Client Sends Login Request

```http
POST /auth/login HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "tenant_email": "acme@example.com",
  "tenant_name": "Acme Corporation",
  "password": "SecurePassword123!"
}
```

#### Step 2-4: Server Checks for Existing Tenant

```python
# Normalize email to lowercase
email_lower = tenant_email.lower()

# Query database
tenant = db.query(Tenant).filter(
    func.lower(Tenant.email) == email_lower
).first()

if tenant is None:
    # Tenant doesn't exist - proceed with creation
    pass
```

#### Step 5: Hash Password

```python
from app.core.security import hash_password

password_hash = hash_password(password)
# Example: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyKDLbkDOKim
```

#### Step 6-7: Create Tenant

```python
from app.repositories import tenant_repository

tenant = tenant_repository.create(
    db=db,
    email=email_lower,
    password_hash=password_hash,
    tenant_name=tenant_name
)
# tenant.id = 2
```

#### Step 8-9: Create Owner User

```python
from app.repositories import user_repository

owner = user_repository.create(
    db=db,
    tenant_id=tenant.id,
    username=email_lower,  # Same as tenant email
    email=email_lower,
    password_hash=password_hash,  # Same as tenant password
    role="OWNER"
)
# owner.id = 1
```

#### Step 10: Generate JWT Tokens

```python
from app.services import jwt_service

access_token = jwt_service.create_access_token(
    user_id=owner.id,
    email=owner.email,
    tenant_id=owner.tenant_id,
    username=owner.username,
    role=owner.role,
    scopes=[]
)

refresh_token = jwt_service.create_refresh_token(
    user_id=owner.id
)
```

#### Step 11: Store Refresh Token

```python
from app.repositories import token_repository

token_repository.create_refresh_token(
    db=db,
    user_id=owner.id,
    token=refresh_token,
    expires_at=datetime.now(timezone.utc) + timedelta(days=30)
)
```

#### Step 12: Return Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### 2.4 Database State After Completion

```sql
-- Tenants table
INSERT INTO tenants (id, email, tenant_name, password_hash, is_active)
VALUES (2, 'acme@example.com', 'Acme Corporation', '$2b$12$...', 1);

-- Users table
INSERT INTO users (id, tenant_id, username, email, password_hash, role)
VALUES (1, 2, 'acme@example.com', 'acme@example.com', '$2b$12$...', 'OWNER');

-- Refresh tokens table
INSERT INTO refresh_tokens (id, user_id, token, expires_at, is_revoked)
VALUES (1, 1, 'eyJhbGc...', '2026-02-11 10:30:00', 0);
```

### 2.5 Error Scenarios

#### Email Already Exists

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Incorrect password"
}
```

**Note**: We don't reveal if email exists (security best practice).

#### Invalid Email Format

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "loc": ["body", "tenant_email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

#### Password Too Short

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

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

## 3. Tenant Login (Returning User)

### 3.1 Workflow Overview

**Purpose**: Authenticate existing tenant and return tokens.

**Trigger**: User submits login form with existing tenant email.

**Result**: Authentication tokens returned for owner user.

### 3.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      TENANT LOGIN WORKFLOW                       │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /auth/login─────────▶                               │
    │   tenant_email                │                              │
    │   password                    │                              │
    │                               │                              │
    │                               ├─[2] Normalize email─────────▶│
    │                               │                              │
    │                               ├─[3] Query tenant by email───▶│
    │                               │                              │
    │                               │◄─[4] Return tenant───────────┤
    │                               │                              │
    │                               ├─[5] Verify password─────────▶│
    │                               │     bcrypt.verify()          │
    │                               │                              │
    │                               │   ◆ Password correct?        │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 401 Unauthorized  │
    │                               │                              │
    │                               ├─[6] Get/create owner user───▶│
    │                               │                              │
    │                               │◄─[7] Return user─────────────┤
    │                               │                              │
    │                               │   ◆ TOTP enabled?            │
    │                               │   ├─✓ Yes → Require TOTP code│
    │                               │   └─✗ No → Continue          │
    │                               │                              │
    │                               ├─[8] Generate JWT tokens─────▶│
    │                               │                              │
    │                               ├─[9] Store refresh token─────▶│
    │                               │                              │
    │◄──[10] Return tokens──────────┤                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 3.3 Step-by-Step Walkthrough

#### Step 1: Client Sends Login Request

```http
POST /auth/login HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "tenant_email": "acme@example.com",
  "password": "SecurePassword123!"
}
```

#### Step 2-4: Server Finds Tenant

```python
tenant = db.query(Tenant).filter(
    func.lower(Tenant.email) == tenant_email.lower()
).first()

if not tenant:
    raise AuthenticationError("Incorrect password")  # Don't reveal if email exists
```

#### Step 5: Verify Password

```python
from app.core.security import verify_password

if not verify_password(password, tenant.password_hash):
    raise AuthenticationError("Incorrect password")
```

#### Step 6-7: Get Owner User

```python
owner = db.query(User).filter(
    User.tenant_id == tenant.id,
    User.role == "OWNER"
).first()

if not owner:
    # Create owner user if doesn't exist (legacy migration case)
    owner = user_repository.create(
        db=db,
        tenant_id=tenant.id,
        username=tenant.email,
        email=tenant.email,
        password_hash=tenant.password_hash,
        role="OWNER"
    )
```

#### Step 8-10: Generate and Return Tokens

Same as steps 10-12 in [Tenant Registration](#23-step-by-step-walkthrough).

### 3.4 Error Scenarios

#### Incorrect Password

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Incorrect password"
}
```

#### Tenant Inactive

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Tenant account is inactive"
}
```

---

## 4. User Login (Multi-User)

### 4.1 Workflow Overview

**Purpose**: Authenticate a user within a tenant (non-owner user).

**Status**: 🚧 **Future Feature** - Requires user invitation system.

**Trigger**: User submits login form with tenant email + username.

**Result**: Authentication tokens returned for specified user.

### 4.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      USER LOGIN WORKFLOW (FUTURE)                │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /auth/login-user────▶                               │
    │   tenant_email                │                              │
    │   username                    │                              │
    │   password                    │                              │
    │                               │                              │
    │                               ├─[2] Query tenant by email───▶│
    │                               │                              │
    │                               │◄─[3] Return tenant───────────┤
    │                               │                              │
    │                               ├─[4] Query user──────────────▶│
    │                               │     WHERE tenant_id = ?      │
    │                               │     AND username = ?         │
    │                               │                              │
    │                               │◄─[5] Return user─────────────┤
    │                               │                              │
    │                               ├─[6] Verify password─────────▶│
    │                               │                              │
    │                               │   ◆ Password correct?        │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 401 Unauthorized  │
    │                               │                              │
    │                               │   ◆ User active?             │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 403 Forbidden     │
    │                               │                              │
    │                               │   ◆ TOTP enabled?            │
    │                               │   ├─✓ Yes → Require TOTP code│
    │                               │   └─✗ No → Continue          │
    │                               │                              │
    │                               ├─[7] Generate JWT tokens─────▶│
    │                               │     Include user.role        │
    │                               │                              │
    │                               ├─[8] Store refresh token─────▶│
    │                               │                              │
    │◄──[9] Return tokens───────────┤                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 4.3 Request Example

```http
POST /auth/login-user HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "tenant_email": "acme@example.com",
  "username": "alice",
  "password": "AlicePassword123!"
}
```

### 4.4 Response Example

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Access Token Payload:**
```json
{
  "sub": "5",
  "email": "alice@acme.com",
  "tenant_id": "2",
  "username": "alice",
  "role": "MEMBER",
  "scopes": [],
  "iat": 1704067200,
  "exp": 1704068100
}
```

---

## 5. Token Refresh Workflow

### 5.1 Workflow Overview

**Purpose**: Obtain new access token using refresh token.

**Trigger**: Access token expires (after 15 minutes).

**Result**: New access token + new refresh token returned, old refresh token revoked.

### 5.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    TOKEN REFRESH WORKFLOW                        │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /auth/refresh───────▶                               │
    │   refresh_token               │                              │
    │                               │                              │
    │                               ├─[2] Decode JWT──────────────▶│
    │                               │                              │
    │                               │   ◆ JWT valid?               │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 401 Unauthorized  │
    │                               │                              │
    │                               ├─[3] Query refresh token─────▶│
    │                               │     WHERE token = ?          │
    │                               │                              │
    │                               │◄─[4] Return token record─────┤
    │                               │                              │
    │                               │   ◆ Token exists?            │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 401 Invalid token │
    │                               │                              │
    │                               │   ◆ Token revoked?           │
    │                               │   ├─✗ No                     │
    │                               │   └─✓ Yes → 401 Revoked      │
    │                               │                              │
    │                               │   ◆ Token expired?           │
    │                               │   ├─✗ No                     │
    │                               │   └─✓ Yes → 401 Expired      │
    │                               │                              │
    │                               ├─[5] Get user by ID──────────▶│
    │                               │                              │
    │                               │◄─[6] Return user─────────────┤
    │                               │                              │
    │                               ├─[7] Revoke old token────────▶│
    │                               │     UPDATE SET is_revoked=1  │
    │                               │                              │
    │                               ├─[8] Generate new tokens─────▶│
    │                               │     New access token         │
    │                               │     New refresh token        │
    │                               │                              │
    │                               ├─[9] Store new refresh token─▶│
    │                               │     INSERT refresh_tokens    │
    │                               │                              │
    │◄──[10] Return new tokens──────┤                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 5.3 Step-by-Step Walkthrough

#### Step 1: Client Sends Refresh Request

```http
POST /auth/refresh HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Step 2: Decode and Validate JWT

```python
from app.services import jwt_service

try:
    payload = jwt_service.decode_refresh_token(refresh_token)
    user_id = int(payload["sub"])
except Exception:
    raise AuthenticationError("Invalid or expired refresh token")
```

#### Step 3-4: Query Refresh Token in Database

```python
from app.repositories import token_repository

token_record = token_repository.get_by_token(db, refresh_token)

if not token_record:
    raise AuthenticationError("Invalid or expired refresh token")

if token_record.is_revoked:
    raise AuthenticationError("Refresh token has been revoked")

if datetime.now(timezone.utc) > token_record.expires_at:
    raise AuthenticationError("Refresh token expired")
```

#### Step 5-6: Get User

```python
from app.repositories import user_repository

user = user_repository.get_by_id(db, user_id)

if not user:
    raise AuthenticationError("User not found")

if not user.is_active:
    raise AuthorizationError("User account is inactive")
```

#### Step 7: Revoke Old Refresh Token

```python
token_repository.revoke_token(db, token_record.id)
```

#### Step 8-10: Generate and Return New Tokens

```python
# Generate new tokens
access_token = jwt_service.create_access_token(
    user_id=user.id,
    email=user.email,
    tenant_id=user.tenant_id,
    username=user.username,
    role=user.role
)

refresh_token = jwt_service.create_refresh_token(user_id=user.id)

# Store new refresh token
token_repository.create_refresh_token(
    db=db,
    user_id=user.id,
    token=refresh_token,
    expires_at=datetime.now(timezone.utc) + timedelta(days=30)
)

# Return response
return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "Bearer",
    "expires_in": 900
}
```

### 5.4 Error Scenarios

#### Invalid Refresh Token

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Invalid or expired refresh token"
}
```

#### Revoked Refresh Token

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Refresh token has been revoked"
}
```

### 5.5 Token Rotation Security

**Why Token Rotation?**
- Limits exposure if token is stolen
- One-time use prevents replay attacks
- Automatic cleanup of old tokens

**Rotation Flow:**
```
Old Token: eyJhbGc...ABC (valid) → Revoked after use
New Token: eyJhbGc...XYZ (issued) → Valid for 30 days
```

---

## 6. TOTP Setup Workflow

### 6.1 Workflow Overview

**Purpose**: Enable two-factor authentication for user account.

**Trigger**: User requests TOTP setup from settings.

**Result**: TOTP secret generated, QR code returned, awaiting verification.

### 6.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                       TOTP SETUP WORKFLOW                        │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /totp/enable────────▶                               │
    │   Authorization: Bearer token │                              │
    │                               │                              │
    │                               ├─[2] Verify access token─────▶│
    │                               │     Extract user_id          │
    │                               │                              │
    │                               ├─[3] Get user by ID──────────▶│
    │                               │                              │
    │                               │◄─[4] Return user─────────────┤
    │                               │                              │
    │                               │   ◆ TOTP already enabled?    │
    │                               │   ├─✓ Yes → 400 Bad Request  │
    │                               │   └─✗ No → Continue          │
    │                               │                              │
    │                               ├─[5] Generate TOTP secret────▶│
    │                               │     pyotp.random_base32()    │
    │                               │     Example: JBSWY3DPEHPK3PXP│
    │                               │                              │
    │                               ├─[6] Save secret to user─────▶│
    │                               │     UPDATE users             │
    │                               │     SET totp_secret = ?      │
    │                               │     (is_totp_enabled = FALSE)│
    │                               │                              │
    │                               ├─[7] Generate QR code────────▶│
    │                               │     otpauth://totp/...       │
    │                               │     Convert to PNG image     │
    │                               │     Encode as data URI       │
    │                               │                              │
    │◄──[8] Return setup data───────┤                              │
    │   {                           │                              │
    │     secret,                   │                              │
    │     qr_code_data_uri,         │                              │
    │     issuer,                   │                              │
    │     account_name              │                              │
    │   }                           │                              │
    │                               │                              │
    ├─[9] Display QR code───────────│                              │
    │   User scans with app         │                              │
    │                               │                              │
    ├─[10] POST /totp/verify───────▶                               │
    │   totp_code: "123456"         │                              │
    │                               │                              │
    │                               ├─[11] Get user──────────────▶ │
    │                               │                              │
    │                               ├─[12] Validate TOTP code────▶ │
    │                               │      pyotp.verify()          │
    │                               │                              │
    │                               │   ◆ Code valid?              │
    │                               │   ├─✓ Yes → Enable TOTP      │
    │                               │   └─✗ No → 400 Invalid code  │
    │                               │                              │
    │                               ├─[13] Enable TOTP────────────▶│
    │                               │      UPDATE users            │
    │                               │      SET is_totp_enabled = 1 │
    │                               │                              │
    │◄──[14] Confirmation───────────┤                              │
    │   {                           │                              │
    │     message: "success",       │                              │
    │     is_totp_enabled: true     │                              │
    │   }                           │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 6.3 Step-by-Step Walkthrough

#### Step 1-2: Enable TOTP Request

```http
POST /api/protected/totp/enable HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Step 3-4: Verify User

```python
user = get_current_user(token)  # From dependency injection

if user.is_totp_enabled:
    raise HTTPException(400, "TOTP is already enabled")
```

#### Step 5: Generate TOTP Secret

```python
import pyotp

totp_secret = pyotp.random_base32()
# Example: "JBSWY3DPEHPK3PXP"
```

#### Step 6: Save Secret (Not Enabled Yet)

```python
user_repository.update_totp_secret(
    db=db,
    user_id=user.id,
    secret=totp_secret
)
# is_totp_enabled remains FALSE until verification
```

#### Step 7: Generate QR Code

```python
import qrcode
from io import BytesIO
import base64

# Create provisioning URI
totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
    name=user.email,
    issuer_name="MCP Auth Service"
)
# Example: "otpauth://totp/MCP%20Auth%20Service:acme@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MCP%20Auth%20Service"

# Generate QR code
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(totp_uri)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

# Convert to data URI
buffer = BytesIO()
img.save(buffer, format="PNG")
img_base64 = base64.b64encode(buffer.getvalue()).decode()
qr_code_data_uri = f"data:image/png;base64,{img_base64}"
```

#### Step 8: Return Setup Data

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_data_uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
  "issuer": "MCP Auth Service",
  "account_name": "acme@example.com"
}
```

#### Step 9: User Scans QR Code

User opens authenticator app (Google Authenticator, Authy, etc.) and scans the QR code. The app displays a 6-digit code that changes every 30 seconds.

#### Step 10: Verify TOTP Code

```http
POST /api/protected/totp/verify HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "totp_code": "123456"
}
```

#### Step 11-12: Validate TOTP Code

```python
import pyotp

user = get_current_user(token)

if not user.totp_secret:
    raise HTTPException(400, "TOTP not set up. Call /enable first")

totp = pyotp.TOTP(user.totp_secret)
is_valid = totp.verify(totp_code, valid_window=1)

if not is_valid:
    raise HTTPException(400, "Invalid TOTP code")
```

#### Step 13: Enable TOTP

```python
user_repository.enable_totp(db=db, user_id=user.id)
```

#### Step 14: Return Confirmation

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "TOTP verification successful",
  "is_totp_enabled": true
}
```

### 6.4 Database State Changes

**Before Setup:**
```sql
SELECT id, email, totp_secret, is_totp_enabled FROM users WHERE id = 1;
-- 1 | acme@example.com | NULL | 0
```

**After /totp/enable:**
```sql
SELECT id, email, totp_secret, is_totp_enabled FROM users WHERE id = 1;
-- 1 | acme@example.com | JBSWY3DPEHPK3PXP | 0
```

**After /totp/verify:**
```sql
SELECT id, email, totp_secret, is_totp_enabled FROM users WHERE id = 1;
-- 1 | acme@example.com | JBSWY3DPEHPK3PXP | 1
```

---

## 7. TOTP Login Workflow

### 7.1 Workflow Overview

**Purpose**: Authenticate user with password + TOTP code.

**Trigger**: User submits login form when TOTP is enabled.

**Result**: Authentication tokens returned after TOTP validation.

### 7.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      TOTP LOGIN WORKFLOW                         │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /auth/login─────────▶                               │
    │   tenant_email                │                              │
    │   password                    │                              │
    │   totp_code: "123456"         │                              │
    │                               │                              │
    │                               ├─[2] Find tenant─────────────▶│
    │                               │                              │
    │                               ├─[3] Verify password─────────▶│
    │                               │                              │
    │                               │   ◆ Password correct?        │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 401 Unauthorized  │
    │                               │                              │
    │                               ├─[4] Get user────────────────▶│
    │                               │                              │
    │                               │◄─[5] Return user─────────────┤
    │                               │                              │
    │                               │   ◆ is_totp_enabled?         │
    │                               │   ├─✗ No → Skip TOTP         │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               │   ◆ totp_code provided?      │
    │                               │   ├─✗ No → 400 TOTP required │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               ├─[6] Validate TOTP───────────▶│
    │                               │     pyotp.verify()           │
    │                               │                              │
    │                               │   ◆ TOTP code valid?         │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 401 Invalid TOTP  │
    │                               │                              │
    │                               ├─[7] Generate tokens─────────▶│
    │                               │                              │
    │                               ├─[8] Store refresh token─────▶│
    │                               │                              │
    │◄──[9] Return tokens───────────┤                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 7.3 Request Example

```http
POST /auth/login HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "tenant_email": "acme@example.com",
  "password": "SecurePassword123!",
  "totp_code": "123456"
}
```

### 7.4 TOTP Validation Logic

```python
import pyotp

# Check if TOTP is enabled
if user.is_totp_enabled:
    if not totp_code:
        raise HTTPException(400, "TOTP code is required")

    # Validate TOTP code
    totp = pyotp.TOTP(user.totp_secret)
    is_valid = totp.verify(totp_code, valid_window=1)

    if not is_valid:
        raise AuthenticationError("Invalid TOTP code")
```

**Note**: `valid_window=1` allows codes from previous/next 30-second window (accounts for clock skew).

### 7.5 Error Scenarios

#### TOTP Code Required But Not Provided

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "TOTP code is required for this account"
}
```

#### Invalid TOTP Code

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Invalid TOTP code"
}
```

#### TOTP Code Expired

TOTP codes change every 30 seconds. If the code expires during entry:

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Invalid TOTP code"
}
```

**Client Handling:**
```javascript
// Retry with next code
if (error.status === 401 && error.detail.includes("TOTP")) {
  alert("TOTP code expired. Please enter the current code.");
  // User can immediately try again with new code
}
```

---

## 8. TOTP Disable Workflow

### 8.1 Workflow Overview

**Purpose**: Disable two-factor authentication for user account.

**Trigger**: User requests TOTP disable from settings.

**Result**: TOTP disabled after code verification, secret remains in database.

### 8.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     TOTP DISABLE WORKFLOW                        │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /totp/disable───────▶                               │
    │   Authorization: Bearer token │                              │
    │   totp_code: "123456"         │                              │
    │                               │                              │
    │                               ├─[2] Verify access token─────▶│
    │                               │                              │
    │                               ├─[3] Get user────────────────▶│
    │                               │                              │
    │                               │   ◆ TOTP enabled?            │
    │                               │   ├─✗ No → 400 Not enabled   │
    │                               │   └─✓ Yes → Continue         │
    │                               │                              │
    │                               ├─[4] Validate TOTP code──────▶│
    │                               │     pyotp.verify()           │
    │                               │                              │
    │                               │   ◆ Code valid?              │
    │                               │   ├─✓ Yes                    │
    │                               │   └─✗ No → 400 Invalid code  │
    │                               │                              │
    │                               ├─[5] Disable TOTP────────────▶│
    │                               │     UPDATE users             │
    │                               │     SET is_totp_enabled = 0  │
    │                               │     (totp_secret kept)       │
    │                               │                              │
    │◄──[6] Confirmation────────────┤                              │
    │   {                           │                              │
    │     message: "TOTP disabled"  │                              │
    │   }                           │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 8.3 Request Example

```http
POST /api/protected/totp/disable HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "totp_code": "123456"
}
```

### 8.4 Implementation

```python
from app.dependencies import get_current_user
from app.repositories import user_repository
import pyotp

@router.post("/totp/disable")
async def disable_totp(
    data: TOTPVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if TOTP is enabled
    if not user.is_totp_enabled:
        raise HTTPException(400, "TOTP is not enabled")

    # Validate current TOTP code
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.totp_code, valid_window=1):
        raise HTTPException(400, "Invalid TOTP code")

    # Disable TOTP (keep secret for potential re-enable)
    user.is_totp_enabled = False
    db.commit()

    return {"message": "TOTP disabled successfully"}
```

### 8.5 Database State

**Before Disable:**
```sql
SELECT id, email, totp_secret, is_totp_enabled FROM users WHERE id = 1;
-- 1 | acme@example.com | JBSWY3DPEHPK3PXP | 1
```

**After Disable:**
```sql
SELECT id, email, totp_secret, is_totp_enabled FROM users WHERE id = 1;
-- 1 | acme@example.com | JBSWY3DPEHPK3PXP | 0
```

**Note**: Secret is retained so user can re-enable TOTP without re-scanning QR code.

---

## 9. Protected Endpoint Access

### 9.1 Workflow Overview

**Purpose**: Access protected API endpoints using JWT access token.

**Trigger**: Client makes request to protected endpoint.

**Result**: Resource returned if token is valid, 401 if invalid/expired.

### 9.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                PROTECTED ENDPOINT ACCESS WORKFLOW                │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] GET /api/protected/me────▶                               │
    │   Authorization: Bearer token │                              │
    │                               │                              │
    │                               ├─[2] Extract token───────────▶│
    │                               │     From "Bearer <token>"    │
    │                               │                              │
    │                               │   ◆ Token present?           │
    │                               │   ├─✗ No → 401 Not auth'd    │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               ├─[3] Decode JWT──────────────▶│
    │                               │     Verify signature         │
    │                               │                              │
    │                               │   ◆ JWT valid?               │
    │                               │   ├─✗ No → 401 Invalid token │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               │   ◆ Token expired?           │
    │                               │   ├─✓ Yes → 401 Expired      │
    │                               │   └─✗ No ↓                   │
    │                               │                              │
    │                               ├─[4] Extract user_id─────────▶│
    │                               │     From payload["sub"]      │
    │                               │                              │
    │                               ├─[5] Query user──────────────▶│
    │                               │     WHERE id = ?             │
    │                               │                              │
    │                               │◄─[6] Return user─────────────┤
    │                               │                              │
    │                               │   ◆ User exists?             │
    │                               │   ├─✗ No → 401 Not found     │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               │   ◆ User active?             │
    │                               │   ├─✗ No → 403 Forbidden     │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               ├─[7] Process request─────────▶│
    │                               │     Execute endpoint logic   │
    │                               │                              │
    │◄──[8] Return response─────────┤                              │
    │   200 OK                      │                              │
    │   {user data}                 │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 9.3 Request Example

```http
GET /api/protected/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhY21lQGV4YW1wbGUuY29tIiwidGVuYW50X2lkIjoiMiIsInVzZXJuYW1lIjoiYWNtZUBleGFtcGxlLmNvbSIsInJvbGUiOiJPV05FUiIsInNjb3BlcyI6W10sImlhdCI6MTcwNDA2NzIwMCwiZXhwIjoxNzA0MDY4MTAwfQ.signature
```

### 9.4 Token Extraction and Validation

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    # Extract token
    token = credentials.credentials

    # Decode and validate JWT
    try:
        payload = jwt_service.decode_access_token(token)
    except ExpiredSignatureError:
        raise AuthenticationError("Access token has expired")
    except InvalidTokenError:
        raise AuthenticationError("Invalid access token")

    # Extract user ID
    user_id = int(payload["sub"])

    # Get user from database
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User not found")

    # Verify user is active
    if not user.is_active:
        raise AuthorizationError("User account is inactive")

    return user
```

### 9.5 Response Example

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 1,
  "tenant_id": 2,
  "username": "acme@example.com",
  "email": "acme@example.com",
  "role": "OWNER",
  "is_totp_enabled": true,
  "is_active": true,
  "created_at": "2026-01-12T10:30:00Z",
  "updated_at": "2026-01-12T10:30:00Z"
}
```

### 9.6 Error Scenarios

#### Missing Authorization Header

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Not authenticated"
}
```

#### Invalid Token Format

```http
GET /api/protected/me HTTP/1.1
Authorization: eyJhbGc...  (missing "Bearer")
```

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Invalid authentication credentials"
}
```

#### Expired Access Token

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Access token has expired"
}
```

**Client Action**: Use refresh token to get new access token.

---

## 10. Logout Workflow

### 10.1 Workflow Overview

**Purpose**: Revoke refresh token and logout user.

**Trigger**: User clicks logout button.

**Result**: Refresh token revoked in database, access token remains valid until expiration.

### 10.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        LOGOUT WORKFLOW                           │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] POST /auth/logout────────▶                               │
    │   Authorization: Bearer token │                              │
    │                               │                              │
    │                               ├─[2] Verify access token─────▶│
    │                               │     Extract user_id          │
    │                               │                              │
    │                               ├─[3] Get user────────────────▶│
    │                               │                              │
    │                               │◄─[4] Return user─────────────┤
    │                               │                              │
    │                               ├─[5] Revoke refresh tokens───▶│
    │                               │     UPDATE refresh_tokens    │
    │                               │     SET is_revoked = 1       │
    │                               │     WHERE user_id = ?        │
    │                               │     AND is_revoked = 0       │
    │                               │                              │
    │◄──[6] Confirmation────────────┤                              │
    │   {                           │                              │
    │     message: "Logged out"     │                              │
    │   }                           │                              │
    │                               │                              │
    ├─[7] Delete tokens locally──-──┤                              │
    │   delete accessToken          │                              │
    │   delete refreshToken         │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 10.3 Request Example

```http
POST /auth/logout HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 10.4 Implementation

```python
@router.post("/auth/logout")
async def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Revoke all active refresh tokens for this user
    token_repository.revoke_all_user_tokens(db, user.id)

    return {"message": "Successfully logged out"}
```

**Database Query:**
```sql
UPDATE refresh_tokens
SET is_revoked = 1
WHERE user_id = 1
  AND is_revoked = 0;
```

### 10.5 Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Successfully logged out"
}
```

### 10.6 Client-Side Cleanup

```javascript
// After receiving logout confirmation
function handleLogout() {
  // Clear tokens from memory
  accessToken = null;
  refreshToken = null;

  // Clear from storage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // Clear from state management
  dispatch({ type: 'LOGOUT' });

  // Redirect to login
  navigate('/login');
}
```

### 10.7 Important Notes

#### Access Token Remains Valid

After logout, the access token is **still technically valid** until it expires (15 minutes). This is because:
- JWT tokens are stateless (not stored in database)
- Server cannot "revoke" JWT without a blacklist
- Acceptable risk due to short lifetime

**Mitigation Strategies:**
1. ✅ Short expiration (15 minutes) - built in
2. ⚠️ Token blacklist - not implemented (adds complexity)
3. ✅ Client-side deletion - user's responsibility

#### Refresh Token Revoked Immediately

The refresh token is revoked in the database and **cannot be used** to obtain new tokens.

---

## 11. Tenant Update Workflow

### 11.1 Workflow Overview

**Purpose**: Update tenant information (tenant_name) with automatic cascade to all users.

**Trigger**: OWNER or ADMIN user updates tenant details.

**Result**: Tenant updated + tenant_name cascaded to ALL users in the tenant.

### 11.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│              TENANT UPDATE WORKFLOW (with Cascade)               │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] PUT /tenants/me──────────▶                               │
    │   Authorization: Bearer token │                              │
    │   tenant_name: "New Name"     │                              │
    │                               │                              │
    │                               ├─[2] Verify access token─────▶│
    │                               │     Extract user_id          │
    │                               │                              │
    │                               ├─[3] Get user────────────────▶│
    │                               │                              │
    │                               │◄─[4] Return user─────────────┤
    │                               │                              │
    │                               │   ◆ User role OWNER/ADMIN?   │
    │                               │   ├─✗ No → 403 Forbidden     │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               ├─[5] Update tenant───────────▶│
    │                               │     UPDATE tenants           │
    │                               │     SET tenant_name = ?      │
    │                               │     WHERE id = ?             │
    │                               │                              │
    │                               │◄─[6] Return updated tenant───┤
    │                               │                              │
    │                               ├─[7] Cascade to users────────▶│
    │                               │     UPDATE users             │
    │                               │     SET tenant_name = ?      │
    │                               │     WHERE tenant_id = ?      │
    │                               │                              │
    │                               │◄─[8] Return users affected───┤
    │                               │     (count)                  │
    │                               │                              │
    │◄──[9] Return response─────────┤                              │
    │   {                           │                              │
    │     tenant_name: "New Name",  │                              │
    │     ... other fields          │                              │
    │   }                           │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 11.3 Step-by-Step Walkthrough

#### Step 1: Client Sends Update Request

```http
PUT /tenants/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "tenant_name": "Acme Corporation Inc"
}
```

#### Step 2-4: Verify Authorization

```python
from app.dependencies import require_admin_or_owner

# Dependency injection ensures user is OWNER or ADMIN
user = require_admin_or_owner(token)

# If user is MEMBER, raises:
# HTTPException(403, "This endpoint requires ADMIN or OWNER role")
```

#### Step 5-6: Update Tenant

```python
from app.services import tenant_service

# Service layer coordinates tenant + user updates
updated_tenant, users_affected = tenant_service.update_tenant_with_cascade(
    db=db,
    tenant_id=user.tenant_id,
    tenant_name="Acme Corporation Inc"
)
```

**SQL Executed:**
```sql
-- Step 5: Update tenant
UPDATE tenants
SET tenant_name = 'Acme Corporation Inc',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 2;
```

#### Step 7-8: Cascade Update to Users

```python
# Service automatically cascades to all users
# Using bulk UPDATE for efficiency (single SQL statement)
users_affected = user_repository.bulk_update_tenant_name(
    db=db,
    tenant_id=user.tenant_id,
    new_tenant_name="Acme Corporation Inc"
)
# Returns count of users updated
```

**SQL Executed:**
```sql
-- Step 7: Bulk update all users in tenant
UPDATE users
SET tenant_name = 'Acme Corporation Inc'
WHERE tenant_id = 2;

-- If tenant has 5 users, all 5 are updated in one statement
```

#### Step 9: Return Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 2,
  "email": "acme@example.com",
  "tenant_name": "Acme Corporation Inc",
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T14:30:00Z"
}
```

### 11.4 Database State Changes

**Before Update:**
```sql
SELECT id, email, tenant_name FROM tenants WHERE id = 2;
-- 2 | acme@example.com | Acme Corporation

SELECT id, username, tenant_name FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | NULL
-- 2 | alice           | NULL
-- 3 | bob             | NULL
```

**After Update:**
```sql
SELECT id, email, tenant_name FROM tenants WHERE id = 2;
-- 2 | acme@example.com | Acme Corporation Inc

SELECT id, username, tenant_name FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | Acme Corporation Inc
-- 2 | alice           | Acme Corporation Inc
-- 3 | bob             | Acme Corporation Inc
```

### 11.5 Cascade Behavior

**✨ Key Feature: Automatic Synchronization**

The `tenant_name` field in the users table is denormalized (copied from tenant) for query performance. The cascade update ensures this field stays synchronized:

- **Single Tenant Updated** → All users in that tenant updated
- **Atomic Operation** → Both succeed or both fail (transaction safety)
- **Efficient Execution** → Single SQL UPDATE statement for all users
- **Tenant Isolation** → Only affects users in the target tenant

**Transaction Safety:**
```python
try:
    # 1. Update tenant
    updated_tenant = tenant_repository.update(db, tenant_id, tenant_name)

    # 2. Cascade to users
    users_affected = user_repository.bulk_update_tenant_name(db, tenant_id, tenant_name)

    # Both succeed together
    return updated_tenant, users_affected
except SQLAlchemyError:
    db.rollback()  # Both fail together
    raise
```

### 11.6 Error Scenarios

#### Forbidden - MEMBER Role

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "This endpoint requires ADMIN or OWNER role. Your role: MEMBER"
}
```

#### Tenant Not Found

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Tenant not found"
}
```

#### Validation Error - Empty tenant_name

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "loc": ["body", "tenant_name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 12. Tenant Status Update Workflow

### 12.1 Workflow Overview

**Purpose**: Activate or deactivate tenant with automatic cascade to all users.

**Trigger**: OWNER user updates tenant status (ADMIN cannot do this).

**Result**: Tenant status updated + is_active cascaded to ALL users in the tenant.

**⚠️ Warning**: Deactivating a tenant will automatically deactivate ALL users, preventing any login until reactivated.

### 12.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│          TENANT STATUS UPDATE WORKFLOW (with Cascade)            │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] PATCH /tenants/me/status─▶                               │
    │   Authorization: Bearer token │                              │
    │   is_active: false            │                              │
    │                               │                              │
    │                               ├─[2] Verify access token─────▶│
    │                               │                              │
    │                               ├─[3] Get user────────────────▶│
    │                               │                              │
    │                               │   ◆ User role OWNER?         │
    │                               │   ├─✗ No → 403 Forbidden     │
    │                               │   │   (ADMIN NOT allowed)    │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               ├─[4] Update tenant status────▶│
    │                               │     UPDATE tenants           │
    │                               │     SET is_active = false    │
    │                               │                              │
    │                               │◄─[5] Return updated tenant───┤
    │                               │                              │
    │                               ├─[6] Cascade to users────────▶│
    │                               │     UPDATE users             │
    │                               │     SET is_active = false    │
    │                               │     WHERE tenant_id = ?      │
    │                               │                              │
    │                               │◄─[7] Return users affected───┤
    │                               │     (count)                  │
    │                               │                              │
    │◄──[8] Return response─────────┤                              │
    │   {                           │                              │
    │     is_active: false,         │                              │
    │     ... other fields          │                              │
    │   }                           │                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 12.3 Step-by-Step Walkthrough

#### Step 1: Deactivate Tenant Request

```http
PATCH /tenants/me/status HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "is_active": false
}
```

#### Step 2-3: Verify OWNER Role

```python
from app.dependencies import require_owner

# Dependency injection ensures user is OWNER (not ADMIN)
user = require_owner(token)

# If user is ADMIN or MEMBER, raises:
# HTTPException(403, "This endpoint requires OWNER role")
```

**Why OWNER-only?**
- Deactivating a tenant affects ALL users (high impact)
- Only tenant owner should have this power
- Prevents ADMIN from locking out OWNER

#### Step 4-5: Update Tenant Status

```python
from app.services import tenant_service

updated_tenant, users_affected = tenant_service.update_tenant_status_with_cascade(
    db=db,
    tenant_id=user.tenant_id,
    is_active=False
)
```

**SQL Executed:**
```sql
UPDATE tenants
SET is_active = 0,
    updated_at = CURRENT_TIMESTAMP
WHERE id = 2;
```

#### Step 6-7: Cascade Status to Users

```python
# Automatically cascades to all users in tenant
users_affected = user_repository.bulk_update_user_status(
    db=db,
    tenant_id=user.tenant_id,
    is_active=False
)
```

**SQL Executed:**
```sql
UPDATE users
SET is_active = 0
WHERE tenant_id = 2;

-- If tenant has 5 users, all 5 are deactivated
```

#### Step 8: Return Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 2,
  "email": "acme@example.com",
  "tenant_name": "Acme Corporation",
  "is_active": false,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-13T15:00:00Z"
}
```

### 12.4 Database State Changes

**Deactivation:**
```sql
-- Before
SELECT id, email, is_active FROM tenants WHERE id = 2;
-- 2 | acme@example.com | 1

SELECT id, username, is_active FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | 1
-- 2 | alice           | 1
-- 3 | bob             | 1

-- After deactivation
SELECT id, email, is_active FROM tenants WHERE id = 2;
-- 2 | acme@example.com | 0

SELECT id, username, is_active FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | 0  (OWNER deactivated too!)
-- 2 | alice           | 0
-- 3 | bob             | 0
```

**Reactivation:**
```sql
-- Reactivate tenant via API (as OWNER with manual DB intervention)
PATCH /tenants/me/status
{ "is_active": true }

-- After reactivation
SELECT id, username, is_active FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | 1  (All users reactivated)
-- 2 | alice           | 1
-- 3 | bob             | 1
```

### 12.5 Cascade Behavior

**Deactivation Cascade:**
- Tenant deactivated → **ALL users deactivated** (including OWNER)
- Users cannot login until tenant is reactivated
- Existing access tokens remain valid until expiration (15 min)
- Refresh tokens can still be used (but login returns 403)

**Reactivation Cascade:**
- Tenant reactivated → **ALL users reactivated**
- Users can login immediately
- No manual intervention needed per user

**Important Notes:**
1. **OWNER is also deactivated** when tenant is deactivated
2. **Manual DB access required** to reactivate tenant if OWNER is deactivated
3. **Soft deactivation** - no data is deleted, just marked inactive

### 12.6 Error Scenarios

#### Forbidden - ADMIN Role Attempting Status Change

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "This endpoint requires OWNER role. Your role: ADMIN"
}
```

#### Login Attempt with Inactive Tenant

```http
POST /auth/login
{ "tenant_email": "acme@example.com", "password": "..." }

HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Tenant account is inactive"
}
```

#### Protected Endpoint with Inactive User

```http
GET /api/protected/me
Authorization: Bearer {valid_token}

HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "User account is inactive"
}
```

---

## 13. Tenant Deletion Workflow

### 13.1 Workflow Overview

**Purpose**: Soft delete tenant by marking as inactive (with cascade to users).

**Trigger**: OWNER user deletes tenant account.

**Result**: Tenant + ALL users marked as inactive (soft delete, data preserved).

**⚠️ Important**: This is a **soft delete** - data is not removed, just marked inactive. Requires manual DB intervention to reactivate.

### 13.2 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│            TENANT DELETION WORKFLOW (Soft Delete + Cascade)      │
└──────────────────────────────────────────────────────────────────┘

  CLIENT                          SERVER                      DATABASE
    │                               │                              │
    ├─[1] DELETE /tenants/me───────▶                               │
    │   Authorization: Bearer token │                              │
    │                               │                              │
    │                               ├─[2] Verify access token─────▶│
    │                               │                              │
    │                               ├─[3] Get user────────────────▶│
    │                               │                              │
    │                               │   ◆ User role OWNER?         │
    │                               │   ├─✗ No → 403 Forbidden     │
    │                               │   └─✓ Yes ↓                  │
    │                               │                              │
    │                               ├─[4] Soft delete tenant──────▶│
    │                               │     UPDATE tenants           │
    │                               │     SET is_active = false    │
    │                               │     (NOT DELETE!)            │
    │                               │                              │
    │                               │◄─[5] Return updated tenant───┤
    │                               │                              │
    │                               ├─[6] Cascade to users────────▶│
    │                               │     UPDATE users             │
    │                               │     SET is_active = false    │
    │                               │     WHERE tenant_id = ?      │
    │                               │     (NOT DELETE!)            │
    │                               │                              │
    │                               │◄─[7] Return users affected───┤
    │                               │                              │
    │◄──[8] Return 204 No Content───┤                              │
    │                               │                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### 13.3 Step-by-Step Walkthrough

#### Step 1: Client Sends Delete Request

```http
DELETE /tenants/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Step 2-3: Verify OWNER Role

```python
from app.dependencies import require_owner

user = require_owner(token)

# Only OWNER can delete tenant
# ADMIN cannot delete (too destructive)
```

#### Step 4-7: Soft Delete with Cascade

```python
from app.services import tenant_service

# DELETE endpoint uses the same cascade function as PATCH
updated_tenant, users_affected = tenant_service.update_tenant_status_with_cascade(
    db=db,
    tenant_id=user.tenant_id,
    is_active=False  # Mark inactive, don't delete
)
```

**SQL Executed (Soft Delete):**
```sql
-- Soft delete tenant
UPDATE tenants
SET is_active = 0
WHERE id = 2;

-- Cascade to all users
UPDATE users
SET is_active = 0
WHERE tenant_id = 2;

-- NO DELETE statements - data preserved!
```

#### Step 8: Return Response

```http
HTTP/1.1 204 No Content
```

**Note**: 204 means success with no response body (standard for DELETE).

### 13.4 Soft Delete vs Hard Delete

| Aspect | Soft Delete (Implemented) | Hard Delete (Not Implemented) |
|--------|---------------------------|-------------------------------|
| **SQL** | `UPDATE SET is_active = 0` | `DELETE FROM tenants` |
| **Data** | Preserved in database | Permanently removed |
| **Recovery** | Can be reactivated | Cannot be recovered |
| **Cascade** | Users also inactive | Users also deleted (CASCADE constraint) |
| **Audit** | Full history retained | History lost |
| **Risk** | Low (reversible) | High (irreversible) |

**Why Soft Delete?**
1. ✅ **Data safety** - no accidental permanent loss
2. ✅ **Audit trail** - preserve history for compliance
3. ✅ **Reversible** - can reactivate if needed
4. ✅ **Cascade safety** - users also preserved
5. ⚠️ **Trade-off** - requires manual cleanup of old inactive records

### 13.5 Database State Changes

**Before Deletion:**
```sql
SELECT id, email, tenant_name, is_active FROM tenants WHERE id = 2;
-- 2 | acme@example.com | Acme Corporation | 1

SELECT id, username, email, is_active FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | acme@example.com | 1
-- 2 | alice           | alice@acme.com   | 1
-- 3 | bob             | bob@acme.com     | 1
```

**After Soft Deletion:**
```sql
SELECT id, email, tenant_name, is_active FROM tenants WHERE id = 2;
-- 2 | acme@example.com | Acme Corporation | 0  (Still exists!)

SELECT id, username, email, is_active FROM users WHERE tenant_id = 2;
-- 1 | acme@example.com | acme@example.com | 0  (Still exists!)
-- 2 | alice           | alice@acme.com   | 0
-- 3 | bob             | bob@acme.com     | 0
```

**Key Observation:**
- All records still in database
- Email addresses preserved (for audit)
- Tenant name preserved
- All relationships intact
- Only `is_active` changed to 0

### 13.6 Post-Deletion Behavior

#### Login Attempts Fail

```http
POST /auth/login
{
  "tenant_email": "acme@example.com",
  "password": "SecurePassword123!"
}

HTTP/1.1 403 Forbidden
{
  "detail": "Tenant account is inactive"
}
```

#### Existing Tokens Fail

```http
GET /api/protected/me
Authorization: Bearer {previously_valid_token}

HTTP/1.1 403 Forbidden
{
  "detail": "User account is inactive"
}
```

#### Refresh Token Fails

```http
POST /auth/refresh
{
  "refresh_token": "..."
}

HTTP/1.1 403 Forbidden
{
  "detail": "User account is inactive"
}
```

### 13.7 Reactivation Process

**Manual reactivation** requires direct database access:

```sql
-- Reactivate tenant
UPDATE tenants
SET is_active = 1
WHERE id = 2;

-- Reactivate all users in tenant
UPDATE users
SET is_active = 1
WHERE tenant_id = 2;
```

**Future Enhancement**: Add `POST /admin/tenants/{id}/reactivate` endpoint for admin panel.

### 13.8 Error Scenarios

#### Forbidden - ADMIN Role Attempting Delete

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "This endpoint requires OWNER role. Your role: ADMIN"
}
```

#### Tenant Not Found

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Tenant not found"
}
```

---

## 14. Error Handling Patterns

### 14.1 Common Error Responses

#### 400 Bad Request

**Cause**: Invalid request data or validation failure

```json
{
  "detail": "TOTP code is required"
}
```

**Client Handling:**
- Display error message to user
- Fix input and retry
- No automatic retry

---

#### 401 Unauthorized

**Cause**: Authentication failed (invalid credentials or token)

```json
{
  "detail": "Access token has expired"
}
```

**Client Handling:**
- If access token expired → Use refresh token
- If refresh token invalid → Redirect to login
- If password incorrect → Show error, let user retry

---

#### 403 Forbidden

**Cause**: User is authenticated but lacks permission

```json
{
  "detail": "User account is inactive"
}
```

**Client Handling:**
- Show error message
- Do not retry automatically
- May require admin action

---

#### 422 Unprocessable Entity

**Cause**: Pydantic validation error

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

**Client Handling:**
- Parse validation errors
- Show field-specific error messages
- Let user correct and retry

---

### 14.2 Automatic Error Recovery

#### Token Refresh on 401

```javascript
async function makeRequest(endpoint, options = {}) {
  // Add access token
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${accessToken}`
  };

  let response = await fetch(endpoint, options);

  // If 401, try refreshing token once
  if (response.status === 401) {
    try {
      await refreshAccessToken();

      // Retry with new token
      options.headers['Authorization'] = `Bearer ${accessToken}`;
      response = await fetch(endpoint, options);
    } catch (refreshError) {
      // Refresh failed - redirect to login
      window.location.href = '/login';
      throw refreshError;
    }
  }

  return response;
}
```

#### Exponential Backoff for Server Errors

```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      // Retry on 5xx errors
      if (response.status >= 500 && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
    }
  }
}
```

---

## 15. State Diagrams

### 15.1 User Authentication State

```
┌─────────────────────────────────────────────────────────────────┐
│                   USER AUTHENTICATION STATES                    │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │ LOGGED OUT   │
                         └──────┬───────┘
                                │
                                │ POST /auth/login
                                │ (valid credentials)
                                ▼
                         ┌──────────────┐
                    ┌───▶│ AUTHENTICATED│◄────┐
                    │    └──────┬───────┘     │
                    │           │             │
                    │           │             │
    POST /auth/refresh          │             │ GET /protected/*
    (valid token)               │             │ (with valid token)
                                │             │
                                │             │
                                ▼             │
                         ┌──────────────┐     │
                         │ TOKEN EXPIRED│─────┘
                         └──────┬───────┘
                                │
                                │ POST /auth/refresh
                                │ (invalid token)
                                │ OR
                                │ POST /auth/logout
                                ▼
                         ┌──────────────┐
                         │ LOGGED OUT   │
                         └──────────────┘
```

### 15.2 TOTP State

```
┌─────────────────────────────────────────────────────────────────┐
│                         TOTP STATES                             │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │ TOTP DISABLED│
                         │ (default)    │
                         └──────┬───────┘
                                │
                                │ POST /totp/enable
                                ▼
                         ┌──────────────┐
                         │ TOTP PENDING │
                         │ (secret set, │
                         │ not verified)│
                         └──────┬───────┘
                                │
                                │ POST /totp/verify
                                │ (valid code)
                                ▼
                         ┌──────────────┐
                    ┌───▶│ TOTP ENABLED │
                    │    └──────┬───────┘
                    │           │
                    │           │ POST /totp/disable
                    │           │ (with valid code)
                    │           ▼
                    │    ┌──────────────┐
                    └────┤ TOTP DISABLED│
                         └──────────────┘
```

### 15.3 Token Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOKEN LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────┘

ACCESS TOKEN:
┌─────────┐
│ CREATED │  (15 min lifetime)
└────┬────┘
     │
     ▼
┌─────────┐
│ VALID   │──────┐ Used for API requests
└────┬────┘      │
     │           │
     │ 15 min    │
     ▼           │
┌─────────┐      │
│ EXPIRED │◄─────┘ Cannot be refreshed or extended
└─────────┘


REFRESH TOKEN:
┌─────────┐
│ CREATED │  (30 day lifetime)
└────┬────┘
     │
     ▼
┌─────────┐
│ ACTIVE  │──────┐ Can be used to refresh
└────┬────┘      │
     │           │
     │ Used      │
     ▼           │
┌─────────┐      │
│ REVOKED │◄─────┘ Cannot be reused (rotation)
└─────────┘
     ▲
     │
     │ Logout or 30 days
     └────────────────────
```

---

## Summary

This document covered all workflows in the MCP Auth application:

### Authentication & Token Management
1. **Tenant Registration** - Auto-create tenant + owner on first login
2. **Tenant Login** - Authenticate existing tenant
3. **User Login** - Multi-user authentication (future)
4. **Token Refresh** - Get new tokens using refresh token

### Security (Two-Factor Authentication)
5. **TOTP Setup** - Enable two-factor authentication
6. **TOTP Login** - Login with password + TOTP code
7. **TOTP Disable** - Turn off two-factor authentication

### Access Control
8. **Protected Access** - Use access tokens for API calls
9. **Logout** - Revoke refresh tokens

### Tenant Management (with Cascade Updates)
10. **Tenant Update** - Update tenant_name with automatic cascade to all users
11. **Tenant Status Update** - Activate/deactivate tenant with cascade to all users
12. **Tenant Deletion** - Soft delete tenant with cascade to all users

### Error Handling
13. **Error Handling** - Standard error patterns and automatic recovery

Each workflow includes:
- Visual flow diagrams with CLIENT → SERVER → DATABASE interactions
- Step-by-step implementation details with code examples
- Request/response examples with actual HTTP messages
- Error scenarios and handling strategies
- Database state changes (before/after SQL queries)
- Transaction safety considerations

**✨ New in v0.1.0**: Tenant Management workflows with **automatic cascade updates**:
- Update tenant → automatically updates all users' denormalized fields
- Deactivate tenant → automatically deactivates all users (soft delete)
- Atomic operations with transaction safety (all or nothing)
- Efficient bulk updates using single SQL UPDATE statements

For more information, see:
- **USER_MANUAL.md** - User-facing tutorials and API examples
- **SCHEMAS.md** - Database schema and architecture documentation
- **API Documentation** - http://127.0.0.1:8000/docs (interactive Swagger UI)

---

**Last Updated**: January 13, 2026
**Version**: 0.1.0
**Status**: Production Ready

🤖 Generated with [Claude Code](https://claude.com/claude-code)
