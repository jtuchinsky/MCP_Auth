# Database Schema Documentation

## Overview

This document provides comprehensive documentation of the database schema for the **MCP Auth** multi-tenant authentication service.

**Database Technology**: SQLite (development) / PostgreSQL (production recommended)
**ORM Framework**: SQLAlchemy 2.0 with declarative mapping
**Migration Tool**: Alembic
**Python Version**: 3.12+

---

## Architecture Principles

### Multi-Tenancy

The schema implements **tenant-based multi-user architecture** where:

- Each **tenant** represents an independent organization/account
- Each **user** belongs to exactly one tenant
- Data is isolated by `tenant_id` at the application layer
- JWT tokens include `tenant_id` claim for authorization

### Security by Design

- **Password hashing**: bcrypt with 12 rounds
- **Email normalization**: Lowercase storage for case-insensitive lookups
- **Token rotation**: Refresh tokens rotated on each use
- **Cascade deletes**: Database-enforced referential integrity
- **Composite constraints**: Username unique per tenant, not globally

### Performance Optimization

- **Strategic indexing**: All lookup columns indexed
- **Foreign key indexes**: Automatic for relationship queries
- **Composite indexes**: Multi-column uniqueness constraints
- **Timezone-aware timestamps**: UTC storage with timezone metadata

---

## Schema Diagram

```
┌──────────────────────────────────┐
│          TENANTS                 │
├──────────────────────────────────┤
│ id (PK)                          │
│ email (UNIQUE, INDEXED)          │
│ tenant_name (OPTIONAL)           │◄── NEW FIELD
│ password_hash                    │
│ is_active                        │
│ created_at (UTC)                 │
│ updated_at (UTC)                 │
└──────────────────────────────────┘
              │
              │ 1:N (CASCADE DELETE)
              │
              ▼
┌──────────────────────────────────┐
│           USERS                  │
├──────────────────────────────────┤
│ id (PK)                          │
│ tenant_id (FK, INDEXED) ─────────┘
│ tenant_name (OPTIONAL)           │◄── NEW FIELD (denormalized)
│ username (INDEXED)               │
│ email (UNIQUE, INDEXED)          │
│ password_hash                    │
│ role (OWNER/ADMIN/MEMBER)        │
│ totp_secret (NULLABLE)           │
│ is_totp_enabled (DEFAULT FALSE)  │
│ is_active (DEFAULT TRUE)         │
│ created_at (UTC)                 │
│ updated_at (UTC)                 │
│ UNIQUE(tenant_id, username)      │
└──────────────────────────────────┘
              │
              │ 1:N (CASCADE DELETE)
              │
              ▼
┌──────────────────────────────────┐
│      REFRESH_TOKENS              │
├──────────────────────────────────┤
│ id (PK)                          │
│ user_id (FK) ────────────────────┘
│ token (UNIQUE, INDEXED)          │
│ client_id (NULLABLE)             │
│ scope (NULLABLE)                 │
│ is_revoked (DEFAULT FALSE)       │
│ expires_at (UTC)                 │
│ created_at (UTC)                 │
└──────────────────────────────────┘
```

---

## Table Definitions

### 1. `tenants` Table

**Purpose**: Stores tenant organizations. Each tenant is an independent account with its own users.

#### Columns

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | Unique tenant identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | - | Tenant's email address (globally unique, case-insensitive) |
| `tenant_name` | VARCHAR(255) | NULLABLE | NULL | Tenant's organization name (optional, for display) |
| `password_hash` | VARCHAR(255) | NOT NULL | - | Bcrypt-hashed password (12 rounds) |
| `is_active` | BOOLEAN | NOT NULL | TRUE | Whether tenant account is active |
| `created_at` | DATETIME | NOT NULL, TIMEZONE AWARE | UTC NOW | Timestamp when tenant was created |
| `updated_at` | DATETIME | NOT NULL, TIMEZONE AWARE | UTC NOW | Timestamp of last update (auto-updated) |

#### Indexes

- **Primary Key**: `id`
- **Unique Index**: `ix_tenants_email` on `email` (case-insensitive lookups via LOWER())

#### Constraints

- **UNIQUE**: `email` - No duplicate tenant emails
- **NOT NULL**: `email`, `password_hash`, `is_active`, `created_at`, `updated_at`

#### SQLAlchemy Model

```python
# app/models/tenant.py
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    tenant_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
```

#### SQL Definition (SQLite)

```sql
CREATE TABLE tenants (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    tenant_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE UNIQUE INDEX ix_tenants_email ON tenants(email);
```

#### Business Rules

1. **Email Normalization**
   - All emails converted to lowercase before storage
   - Lookups use `LOWER(email)` for case-insensitive matching
   - Prevents duplicates: `user@EXAMPLE.com` == `user@example.com`

2. **Auto-Creation on First Login**
   - New tenants created automatically when logging in with unknown email
   - Owner user created simultaneously (same email/password)
   - No explicit registration endpoint needed

3. **Password Management**
   - Passwords hashed with bcrypt (12 rounds, cost factor 2^12)
   - Owner user inherits tenant's password_hash
   - Password changes sync between tenant and owner user

4. **Tenant Name**
   - Optional display name for organization (e.g., "Acme Corporation")
   - Can be set during first login or updated later
   - Nullable - defaults to NULL if not provided

5. **Active Status**
   - `is_active=False` disables tenant and all associated users
   - Used for soft deletion or account suspension
   - Does not delete data (hard delete via CASCADE)

#### Example Data

```sql
-- Default tenant (created during migration)
INSERT INTO tenants (id, email, tenant_name, password_hash, is_active, created_at, updated_at)
VALUES (
    1,
    'default@system.local',
    'Default Tenant',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyKDLbkDOKim',
    1,
    '2026-01-07 22:06:59.123456',
    '2026-01-07 22:06:59.123456'
);

-- Real tenant organization
INSERT INTO tenants (id, email, tenant_name, password_hash, is_active, created_at, updated_at)
VALUES (
    2,
    'company@example.com',
    'Acme Corporation',
    '$2b$12$YmVhY2hzdGF0ZW1lbnQuLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLg',
    1,
    '2026-01-11 10:30:00.000000',
    '2026-01-11 10:30:00.000000'
);

-- Tenant without organization name
INSERT INTO tenants (id, email, tenant_name, password_hash, is_active, created_at, updated_at)
VALUES (
    3,
    'freelancer@example.com',
    NULL,
    '$2b$12$ZnJlZWxhbmNlciBwYXNzd29yZC4uLi4uLi4uLi4uLi4uLi4uLi4uLg',
    1,
    '2026-01-11 11:00:00.000000',
    '2026-01-11 11:00:00.000000'
);
```

#### Common Queries

```python
# Get tenant by email (case-insensitive)
from sqlalchemy import func
tenant = db.query(Tenant).filter(
    func.lower(Tenant.email) == email.lower()
).first()

# Get active tenants
active_tenants = db.query(Tenant).filter(Tenant.is_active == True).all()

# Get tenant with users (eager loading)
tenant_with_users = db.query(Tenant).options(
    joinedload(Tenant.users)
).filter(Tenant.id == tenant_id).first()

# Count users per tenant
from sqlalchemy import func
user_counts = db.query(
    Tenant.id,
    Tenant.email,
    Tenant.tenant_name,
    func.count(User.id).label('user_count')
).join(User).group_by(Tenant.id).all()
```

---

### 2. `users` Table

**Purpose**: Stores users within tenants. Each user belongs to exactly one tenant and has a role within that tenant.

#### Columns

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | Global unique user identifier |
| `tenant_id` | INTEGER | FOREIGN KEY, NOT NULL, INDEXED | - | Reference to tenant (CASCADE DELETE) |
| `tenant_name` | VARCHAR(255) | NULLABLE | NULL | Tenant's organization name (denormalized for performance) |
| `username` | VARCHAR(100) | NOT NULL, INDEXED | - | Username (unique per tenant, not globally) |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | - | User's email address (globally unique) |
| `password_hash` | VARCHAR(255) | NOT NULL | - | Bcrypt-hashed password (12 rounds) |
| `role` | VARCHAR(50) | NOT NULL | 'MEMBER' | User role: OWNER, ADMIN, or MEMBER |
| `totp_secret` | VARCHAR(32) | NULLABLE | NULL | Base32-encoded TOTP secret for 2FA |
| `is_totp_enabled` | BOOLEAN | NOT NULL | FALSE | Whether 2FA is enabled for this user |
| `is_active` | BOOLEAN | NOT NULL | TRUE | Whether user account is active |
| `created_at` | DATETIME | NOT NULL, TIMEZONE AWARE | UTC NOW | Timestamp when user was created |
| `updated_at` | DATETIME | NOT NULL, TIMEZONE AWARE | UTC NOW | Timestamp of last update (auto-updated) |

#### Indexes

- **Primary Key**: `id`
- **Unique Index**: `ix_users_email` on `email`
- **Index**: `ix_users_username` on `username`
- **Index**: `ix_users_tenant_id` on `tenant_id`
- **Composite Unique Index**: `uq_tenant_username` on `(tenant_id, username)`

#### Constraints

- **FOREIGN KEY**: `tenant_id` → `tenants.id` (ON DELETE CASCADE)
- **UNIQUE**: `email` - Globally unique across all tenants
- **UNIQUE**: `(tenant_id, username)` - Username unique per tenant
- **NOT NULL**: All columns except `totp_secret`

#### SQLAlchemy Model

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MEMBER",
    )

    totp_secret: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    is_totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_tenant_username"),
    )
```

#### SQL Definition (SQLite)

```sql
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    tenant_name VARCHAR(255),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'MEMBER',
    totp_secret VARCHAR(32),
    is_totp_enabled BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT uq_tenant_username UNIQUE (tenant_id, username)
);

CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_tenant_id ON users(tenant_id);
```

#### User Roles

| Role | Code | Description | Permissions |
|------|------|-------------|-------------|
| Owner | `OWNER` | Tenant owner, first user in tenant | Full control, can invite users, manage tenant settings |
| Admin | `ADMIN` | Administrator within tenant | Manage users, elevated permissions (future) |
| Member | `MEMBER` | Standard user | Basic access, read/write own data (future) |

**Role Assignment Rules**:
- First user in new tenant automatically gets `role=OWNER`
- Owner user has same email and password as tenant
- Future: Only OWNER and ADMIN can invite new users
- Future: Role-based access control (RBAC) for API endpoints

#### Business Rules

1. **Tenant Isolation**
   - Every user MUST belong to a tenant (`tenant_id` NOT NULL)
   - Users cannot access data from other tenants
   - JWT tokens include `tenant_id` claim for validation
   - All queries MUST filter by `tenant_id`

2. **Username Scoping**
   - Username unique per tenant (not globally)
   - Allows: tenant1:alice, tenant2:alice (different users)
   - Composite constraint: `UNIQUE(tenant_id, username)`

3. **Email Uniqueness**
   - Email globally unique across all tenants
   - Used for notifications, password reset, invitations
   - Prevents user from joining multiple tenants (current design)

4. **Owner User Creation**
   - Owner created automatically with new tenant
   - Owner has `username = tenant.email`
   - Owner has `email = tenant.email`
   - Owner has `password_hash = tenant.password_hash`
   - Owner has `role = 'OWNER'`

5. **TOTP (Two-Factor Authentication)**
   - `totp_secret` stored as Base32-encoded string (32 chars)
   - `is_totp_enabled` becomes TRUE after verification
   - Setup flow: generate secret → save to DB → user verifies → enable
   - Login requires TOTP code if enabled

6. **Cascade Deletion**
   - Deleting tenant deletes all associated users
   - Deleting user deletes all associated refresh tokens
   - Database-level CASCADE for data integrity

#### Example Data

```sql
-- Owner user for tenant #2 (Acme Corporation)
INSERT INTO users (id, tenant_id, username, email, password_hash, role, totp_secret, is_totp_enabled, is_active, created_at, updated_at)
VALUES (
    1,
    2,
    'company@example.com',
    'company@example.com',
    '$2b$12$YmVhY2hzdGF0ZW1lbnQuLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLg',
    'OWNER',
    NULL,
    0,
    1,
    '2026-01-11 10:30:00.000000',
    '2026-01-11 10:30:00.000000'
);

-- Additional user in same tenant (future: when invitations implemented)
INSERT INTO users (id, tenant_id, username, email, password_hash, role, totp_secret, is_totp_enabled, is_active, created_at, updated_at)
VALUES (
    2,
    2,
    'alice',
    'alice@acme.com',
    '$2b$12$QWxpY2UncyBwYXNzd29yZC4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLg',
    'MEMBER',
    'JBSWY3DPEHPK3PXP',
    1,
    1,
    '2026-01-11 11:00:00.000000',
    '2026-01-11 11:00:00.000000'
);

-- Admin user with TOTP disabled
INSERT INTO users (id, tenant_id, username, email, password_hash, role, totp_secret, is_totp_enabled, is_active, created_at, updated_at)
VALUES (
    3,
    2,
    'bob',
    'bob@acme.com',
    '$2b$12$Qm9iJ3MgcGFzc3dvcmQuLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLg',
    'ADMIN',
    'JBSWY3DPEHPK3PXQ',
    0,
    1,
    '2026-01-11 12:00:00.000000',
    '2026-01-11 12:00:00.000000'
);
```

#### Common Queries

```python
# Get all users in a tenant
users = db.query(User).filter(User.tenant_id == tenant_id).all()

# Get tenant owner
owner = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.role == "OWNER"
).first()

# Get user by tenant and username (for login)
user = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.username == username
).first()

# Get user by email (globally unique)
user = db.query(User).filter(
    func.lower(User.email) == email.lower()
).first()

# Count active users per tenant
count = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.is_active == True
).count()

# Get users with TOTP enabled
totp_users = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.is_totp_enabled == True
).all()
```

---

### 3. `refresh_tokens` Table

**Purpose**: Stores JWT refresh tokens for secure token rotation and session management.

#### Columns

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | Unique token record identifier |
| `user_id` | INTEGER | FOREIGN KEY, NOT NULL | - | Reference to user (CASCADE DELETE) |
| `token` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | - | Refresh token value (UUID or JWT) |
| `client_id` | VARCHAR(255) | NULLABLE | NULL | OAuth 2.1 client identifier (MCP) |
| `scope` | VARCHAR(500) | NULLABLE | NULL | OAuth 2.1 scopes (space-separated) |
| `is_revoked` | BOOLEAN | NOT NULL | FALSE | Whether token has been revoked |
| `expires_at` | DATETIME | NOT NULL, TIMEZONE AWARE | - | Token expiration timestamp (UTC) |
| `created_at` | DATETIME | NOT NULL, TIMEZONE AWARE | UTC NOW | Timestamp when token was created |

#### Indexes

- **Primary Key**: `id`
- **Unique Index**: `ix_refresh_tokens_token` on `token`
- **Index**: `ix_refresh_tokens_user_id` on `user_id`

#### Constraints

- **FOREIGN KEY**: `user_id` → `users.id` (ON DELETE CASCADE)
- **UNIQUE**: `token` - Each token globally unique
- **NOT NULL**: `user_id`, `token`, `is_revoked`, `expires_at`, `created_at`

#### SQLAlchemy Model

```python
# app/models/token.py
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    client_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    scope: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
```

#### SQL Definition (SQLite)

```sql
CREATE TABLE refresh_tokens (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    client_id VARCHAR(255),
    scope VARCHAR(500),
    is_revoked BOOLEAN NOT NULL DEFAULT 0,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);
```

#### Business Rules

1. **Token Rotation (OAuth 2.1 Requirement)**
   - Each refresh operation generates NEW refresh token
   - Old refresh token is revoked (`is_revoked=True`)
   - Prevents token reuse attacks
   - Implementation: `/auth/refresh` endpoint

2. **Token Expiration**
   - Default lifetime: 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
   - Tokens checked against `expires_at` on each use
   - Expired tokens rejected even if not revoked
   - Cleanup job can delete expired tokens periodically

3. **Token Revocation**
   - Logout sets `is_revoked=True` on all user's tokens
   - Revoked tokens cannot be used even if not expired
   - Database query: `WHERE is_revoked=False AND expires_at > NOW()`

4. **OAuth 2.1 / MCP Integration**
   - `client_id`: Identifies MCP client application
   - `scope`: Space-separated OAuth scopes (e.g., "read write")
   - Optional fields for future OAuth features
   - Currently not enforced in authentication flow

5. **Cascade Deletion**
   - Deleting user deletes all their refresh tokens
   - Deleting tenant → deletes users → deletes tokens
   - Ensures no orphaned tokens in database

#### Example Data

```sql
-- Active refresh token
INSERT INTO refresh_tokens (id, user_id, token, client_id, scope, is_revoked, expires_at, created_at)
VALUES (
    1,
    1,
    '550e8400-e29b-41d4-a716-446655440000',
    'mcp-client-001',
    'read write',
    0,
    '2026-02-10 10:30:00.000000',
    '2026-01-11 10:30:00.000000'
);

-- Revoked token (after logout or rotation)
INSERT INTO refresh_tokens (id, user_id, token, client_id, scope, is_revoked, expires_at, created_at)
VALUES (
    2,
    1,
    '660e8400-e29b-41d4-a716-446655440001',
    'mcp-client-001',
    'read write',
    1,
    '2026-02-10 09:00:00.000000',
    '2026-01-11 09:00:00.000000'
);

-- Expired token
INSERT INTO refresh_tokens (id, user_id, token, client_id, scope, is_revoked, expires_at, created_at)
VALUES (
    3,
    2,
    '770e8400-e29b-41d4-a716-446655440002',
    NULL,
    NULL,
    0,
    '2026-01-01 00:00:00.000000',
    '2025-12-02 00:00:00.000000'
);
```

#### Common Queries

```python
# Get valid refresh token
from datetime import datetime, timezone
token = db.query(RefreshToken).filter(
    RefreshToken.token == token_value,
    RefreshToken.is_revoked == False,
    RefreshToken.expires_at > datetime.now(timezone.utc)
).first()

# Revoke all user's tokens (logout)
db.query(RefreshToken).filter(
    RefreshToken.user_id == user_id
).update({"is_revoked": True})

# Delete expired tokens (cleanup job)
db.query(RefreshToken).filter(
    RefreshToken.expires_at < datetime.now(timezone.utc)
).delete()

# Count active tokens per user
from sqlalchemy import func
token_counts = db.query(
    RefreshToken.user_id,
    func.count(RefreshToken.id).label('token_count')
).filter(
    RefreshToken.is_revoked == False
).group_by(RefreshToken.user_id).all()
```

---

## Relationships

### Tenant → Users (One-to-Many)

**Cardinality**: 1 Tenant : N Users

**SQLAlchemy Relationship**:
```python
# In Tenant model
users: Mapped[list["User"]] = relationship(
    "User",
    back_populates="tenant",
    cascade="all, delete-orphan"
)
```

**Behavior**:
- One tenant can have many users (0 to unlimited)
- Each user belongs to exactly one tenant
- Deleting tenant deletes all its users (CASCADE)
- Owner user created automatically with new tenant

**Example**:
```python
tenant = db.query(Tenant).filter(Tenant.id == 2).first()
users = tenant.users  # List of User objects
owner = [u for u in users if u.role == "OWNER"][0]
```

---

### User → Tenant (Many-to-One)

**Cardinality**: N Users : 1 Tenant

**SQLAlchemy Relationship**:
```python
# In User model
tenant: Mapped["Tenant"] = relationship(
    "Tenant",
    back_populates="users"
)
```

**Behavior**:
- Each user has exactly one tenant (NOT NULL constraint)
- Many users can belong to same tenant
- Foreign key enforced at database level

**Example**:
```python
user = db.query(User).filter(User.id == 1).first()
tenant = user.tenant  # Tenant object
print(f"User {user.username} belongs to {tenant.email}")
```

---

### User → RefreshTokens (One-to-Many)

**Cardinality**: 1 User : N RefreshTokens

**SQLAlchemy Relationship**:
```python
# In User model
refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
    "RefreshToken",
    back_populates="user",
    cascade="all, delete-orphan"
)
```

**Behavior**:
- One user can have many refresh tokens (multiple devices/sessions)
- Each refresh token belongs to exactly one user
- Deleting user deletes all their tokens (CASCADE)

**Example**:
```python
user = db.query(User).filter(User.id == 1).first()
active_tokens = [t for t in user.refresh_tokens if not t.is_revoked]
print(f"User has {len(active_tokens)} active sessions")
```

---

## Security Considerations

### Password Hashing

**Algorithm**: bcrypt
**Cost Factor**: 12 rounds (2^12 iterations)

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
password_hash = pwd_context.hash("user_password")

# Verify password
is_valid = pwd_context.verify("user_password", password_hash)
```

**Security Properties**:
- Adaptive hashing (cost factor increases over time)
- Automatic salt generation (unique per password)
- Timing-attack resistant verification
- Future-proof (supports algorithm upgrades)

---

### Email Normalization

**Rule**: All emails stored and queried in lowercase

```python
# Before storage
email = email.lower()

# In queries
from sqlalchemy import func
user = db.query(User).filter(
    func.lower(User.email) == email.lower()
).first()
```

**Benefits**:
- Case-insensitive authentication
- Prevents duplicate accounts with different casing
- Consistent behavior across platforms

---

### Tenant Isolation

**Enforcement Layers**:

1. **Database Level**:
   - Foreign key constraints
   - Composite unique constraints
   - CASCADE deletion

2. **Application Level**:
   - All queries filter by `tenant_id`
   - JWT tokens include `tenant_id` claim
   - Dependencies validate tenant access

3. **API Level**:
   - Endpoints require authentication
   - Token validation extracts `tenant_id`
   - User actions scoped to their tenant

**Example Secure Query**:
```python
# BAD - No tenant isolation
all_users = db.query(User).all()

# GOOD - Tenant-scoped query
tenant_users = db.query(User).filter(User.tenant_id == tenant_id).all()
```

---

### Composite Unique Constraints

**Constraint**: `UNIQUE(tenant_id, username)`

**Purpose**: Allow same username across different tenants

**Examples**:
- ✅ Allowed: tenant1:alice, tenant2:alice (different tenants)
- ❌ Blocked: tenant1:alice, tenant1:alice (duplicate in same tenant)
- ✅ Allowed: tenant1:alice, tenant1:bob (different usernames)

**Database Enforcement**:
```sql
CREATE UNIQUE INDEX uq_tenant_username ON users(tenant_id, username);
```

---

## Performance Optimization

### Index Strategy

All frequently queried columns are indexed:

| Table | Column(s) | Index Type | Purpose |
|-------|-----------|------------|---------|
| `tenants` | `id` | PRIMARY KEY | Fast lookups by ID |
| `tenants` | `email` | UNIQUE | Fast tenant login |
| `users` | `id` | PRIMARY KEY | Fast lookups by ID |
| `users` | `email` | UNIQUE | Fast user login (global) |
| `users` | `username` | INDEX | Fast username searches |
| `users` | `tenant_id` | INDEX | Fast tenant-scoped queries |
| `users` | `(tenant_id, username)` | COMPOSITE UNIQUE | Fast tenant user login |
| `refresh_tokens` | `id` | PRIMARY KEY | Fast lookups by ID |
| `refresh_tokens` | `token` | UNIQUE | Fast token validation |
| `refresh_tokens` | `user_id` | INDEX | Fast user token queries |

### Query Patterns

**Good Patterns**:
```python
# Use indexes
user = db.query(User).filter(User.id == user_id).first()
tenant = db.query(Tenant).filter(Tenant.email == email).first()
users = db.query(User).filter(User.tenant_id == tenant_id).all()

# Use eager loading for relationships
tenant = db.query(Tenant).options(
    joinedload(Tenant.users)
).filter(Tenant.id == tenant_id).first()
```

**Anti-Patterns**:
```python
# Full table scans
all_users = db.query(User).all()

# N+1 queries
for tenant in db.query(Tenant).all():
    users = tenant.users  # Lazy load for each tenant
```

### Cascade Deletes

**Database-Level Cascades** (no application code needed):
```sql
-- Deleting tenant deletes all users
DELETE FROM tenants WHERE id = ?;
-- CASCADE automatically deletes from users

-- Deleting user deletes all refresh tokens
DELETE FROM users WHERE id = ?;
-- CASCADE automatically deletes from refresh_tokens
```

---

## Database Maintenance

### Cleanup Expired Tokens

**Frequency**: Daily cronjob or background task

```sql
DELETE FROM refresh_tokens
WHERE expires_at < datetime('now');
```

```python
# Python implementation
from datetime import datetime, timezone
db.query(RefreshToken).filter(
    RefreshToken.expires_at < datetime.now(timezone.utc)
).delete()
db.commit()
```

### Deactivate Tenants

**Soft Delete** (preserves data):
```sql
UPDATE tenants
SET is_active = 0, updated_at = datetime('now')
WHERE id = ?;
```

**Hard Delete** (cascades to users and tokens):
```sql
DELETE FROM tenants WHERE id = ?;
```

### Count Users Per Tenant

```sql
SELECT
    t.id,
    t.email,
    t.tenant_name,
    COUNT(u.id) as user_count
FROM tenants t
LEFT JOIN users u ON t.id = u.tenant_id AND u.is_active = 1
GROUP BY t.id, t.email, t.tenant_name
ORDER BY user_count DESC;
```

### Find Tenants Without Users

```sql
SELECT t.*
FROM tenants t
LEFT JOIN users u ON t.id = u.tenant_id
WHERE u.id IS NULL;
```

---

## Migration History

### Current Schema Version

**Alembic Head**: `24d546efdc36`
**Last Updated**: 2026-01-11

### Migration Timeline

| Revision | Date | Description |
|----------|------|-------------|
| `e9258cf92b4d` | 2026-01-07 | Add tenant-based authentication (tenants table, user.tenant_id, user.role) |
| `e340c902e215` | 2026-01-11 | Add tenant_name field to tenants table (optional VARCHAR(255)) |
| `24d546efdc36` | 2026-01-11 | Add tenant_name field to users table (denormalized for performance) |

### Applying Migrations

```bash
# View current version
alembic current

# View migration history
alembic history

# Upgrade to latest version
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade e9258cf92b4d
```

---

## Future Enhancements

### Planned Schema Changes

#### 1. User Invitations Table

**Purpose**: Track pending invitations to join tenants

```sql
CREATE TABLE user_invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    invited_by_user_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'MEMBER',
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    accepted_at DATETIME,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (tenant_id, email)
);
```

#### 2. Audit Log Table

**Purpose**: Track security events and user actions

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

#### 3. API Keys Table

**Purpose**: Alternative authentication for MCP clients

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    scopes VARCHAR(500),
    last_used_at DATETIME,
    expires_at DATETIME,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## References

### Alembic Migrations

- `alembic/versions/e9258cf92b4d_add_tenant_based_authentication.py`
- `alembic/versions/e340c902e215_add_tenant_name_field_to_tenants_table.py`
- `alembic/versions/24d546efdc36_add_tenant_name_field_to_users_table.py`

### SQLAlchemy Models

- `app/models/tenant.py` - Tenant model
- `app/models/user.py` - User model
- `app/models/token.py` - RefreshToken model

### Repositories (Data Access Layer)

- `app/repositories/tenant_repository.py` - Tenant CRUD operations
- `app/repositories/user_repository.py` - User CRUD operations
- `app/repositories/token_repository.py` - Token management

### Services (Business Logic)

- `app/services/tenant_service.py` - Tenant operations
- `app/services/auth_service.py` - Authentication logic
- `app/services/jwt_service.py` - JWT token creation/validation

### Tests

- `tests/unit/test_tenant_repository.py` - Tenant repository tests
- `tests/unit/test_tenant_service.py` - Tenant service tests
- `tests/unit/test_database.py` - Schema validation tests
- `tests/integration/test_auth_endpoints.py` - Authentication API tests

### External Documentation

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [OAuth 2.1 Specification](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-07)
- [TOTP RFC 6238](https://datatracker.ietf.org/doc/html/rfc6238)

---

**Document Version**: 2.0
**Last Updated**: 2026-01-11
**Maintained By**: MCP Auth Development Team
