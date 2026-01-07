# Database Schema Documentation

## Overview

This document describes the database schema for the **tenant-based multi-user authentication system** implemented in MCP Auth.

**Database**: SQLite (development) / PostgreSQL (production recommended)
**ORM**: SQLAlchemy 2.0
**Migration Tool**: Alembic

---

## Schema Diagram

```
┌─────────────────────────────┐
│         TENANTS             │
├─────────────────────────────┤
│ id (PK)                     │
│ email (UNIQUE, INDEXED)     │
│ password_hash               │
│ is_active                   │
│ created_at                  │
│ updated_at                  │
└─────────────────────────────┘
              │
              │ 1:N
              │
              ▼
┌─────────────────────────────┐
│          USERS              │
├─────────────────────────────┤
│ id (PK)                     │
│ tenant_id (FK) ────────────┘
│ username (INDEXED)          │
│ email (UNIQUE, INDEXED)     │
│ password_hash               │
│ role (OWNER/ADMIN/MEMBER)   │
│ totp_secret                 │
│ is_totp_enabled             │
│ is_active                   │
│ created_at                  │
│ updated_at                  │
│ UNIQUE(tenant_id, username) │
└─────────────────────────────┘
              │
              │ 1:N
              │
              ▼
┌─────────────────────────────┐
│     REFRESH_TOKENS          │
├─────────────────────────────┤
│ id (PK)                     │
│ user_id (FK) ───────────────┘
│ token (UNIQUE, INDEXED)     │
│ client_id                   │
│ scope                       │
│ is_revoked                  │
│ expires_at                  │
│ created_at                  │
└─────────────────────────────┘
```

---

## Table Definitions

### 1. `tenants` Table

**Purpose**: Stores tenant organizations. Each tenant represents an independent account/organization.

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique tenant identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Tenant's email address (globally unique) |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt-hashed password (12 rounds) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether tenant account is active |
| `created_at` | DATETIME | NOT NULL | Timestamp when tenant was created |
| `updated_at` | DATETIME | NOT NULL | Timestamp of last update |

#### Indexes

- `ix_tenants_email` (UNIQUE) - Fast tenant lookup by email

#### SQL Definition

```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE UNIQUE INDEX ix_tenants_email ON tenants(email);
```

#### Business Rules

1. **Email is globally unique** - No two tenants can have the same email
2. **Email normalization** - All emails stored in lowercase
3. **Case-insensitive lookups** - Queries normalize email to lowercase
4. **Auto-creation** - New tenants created automatically on first login
5. **Password hashing** - Uses bcrypt with 12 rounds

#### Example Data

```sql
INSERT INTO tenants (id, email, password_hash, is_active, created_at, updated_at)
VALUES (
    1,
    'company@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyKDLbkDOKim',
    1,
    '2026-01-07 10:30:00',
    '2026-01-07 10:30:00'
);
```

---

### 2. `users` Table

**Purpose**: Stores users within tenants. Users belong to exactly one tenant.

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Global unique user identifier |
| `tenant_id` | INTEGER | FOREIGN KEY, NOT NULL, INDEXED | Reference to tenant (CASCADE DELETE) |
| `username` | VARCHAR(100) | NOT NULL, INDEXED | Username (unique per tenant) |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | User's email (globally unique) |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt-hashed password (12 rounds) |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'MEMBER' | User role: OWNER, ADMIN, or MEMBER |
| `totp_secret` | VARCHAR(32) | NULLABLE | Base32-encoded TOTP secret for 2FA |
| `is_totp_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether 2FA is enabled |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether user account is active |
| `created_at` | DATETIME | NOT NULL | Timestamp when user was created |
| `updated_at` | DATETIME | NOT NULL | Timestamp of last update |

#### Indexes

- `ix_users_email` (UNIQUE) - Fast user lookup by email
- `ix_users_username` - Fast username searches
- `ix_users_tenant_id` - Fast tenant-scoped queries

#### Constraints

- **FOREIGN KEY** `tenant_id` → `tenants.id` (ON DELETE CASCADE)
- **UNIQUE** `(tenant_id, username)` - Username unique per tenant

#### SQL Definition

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'MEMBER',
    totp_secret VARCHAR(32),
    is_totp_enabled BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_tenant_id ON users(tenant_id);
CREATE UNIQUE INDEX uq_tenant_username ON users(tenant_id, username);
```

#### Business Rules

1. **Tenant isolation** - All users belong to exactly one tenant
2. **Username per tenant** - Usernames unique within tenant (e.g., tenant1:alice, tenant2:alice allowed)
3. **Global email uniqueness** - Emails globally unique across all tenants (for notifications/invites)
4. **Email normalization** - All emails stored in lowercase
5. **Owner user** - First user in new tenant automatically has role=OWNER
6. **Owner credentials** - Owner has same email/password as tenant
7. **Cascade deletion** - Deleting tenant deletes all its users

#### User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| `OWNER` | Tenant owner | Full access, first user in tenant, can invite users |
| `ADMIN` | Administrator | Manage users, elevated permissions (future) |
| `MEMBER` | Standard user | Basic access (future) |

#### Example Data

```sql
-- Owner user for company@example.com
INSERT INTO users (id, tenant_id, username, email, password_hash, role, is_totp_enabled, is_active, created_at, updated_at)
VALUES (
    1,
    1,
    'company@example.com',
    'company@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyKDLbkDOKim',
    'OWNER',
    0,
    1,
    '2026-01-07 10:30:00',
    '2026-01-07 10:30:00'
);

-- Additional user in same tenant (future feature)
INSERT INTO users (id, tenant_id, username, email, password_hash, role, is_totp_enabled, is_active, created_at, updated_at)
VALUES (
    2,
    1,
    'alice',
    'alice@company.com',
    '$2b$12$...',
    'MEMBER',
    0,
    1,
    '2026-01-07 11:00:00',
    '2026-01-07 11:00:00'
);
```

---

### 3. `refresh_tokens` Table

**Purpose**: Stores JWT refresh tokens for secure token rotation.

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique token identifier |
| `user_id` | INTEGER | FOREIGN KEY, NOT NULL | Reference to user |
| `token` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Refresh token value |
| `client_id` | VARCHAR(255) | NULLABLE | OAuth client identifier (MCP) |
| `scope` | VARCHAR(500) | NULLABLE | OAuth scopes |
| `is_revoked` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether token is revoked |
| `expires_at` | DATETIME | NOT NULL | Token expiration timestamp |
| `created_at` | DATETIME | NOT NULL | Timestamp when token was created |

#### Indexes

- `ix_refresh_tokens_token` (UNIQUE) - Fast token lookup
- `ix_refresh_tokens_user_id` - Fast user token queries

#### Constraints

- **FOREIGN KEY** `user_id` → `users.id` (ON DELETE CASCADE)

#### SQL Definition

```sql
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

1. **Token rotation** - New refresh token issued on each use, old token revoked
2. **Automatic cleanup** - Expired tokens can be purged periodically
3. **Revocation** - Tokens can be manually revoked (logout)
4. **Cascade deletion** - Deleting user deletes all their tokens

---

## Relationships

### Tenant → Users (One-to-Many)

```python
# Tenant model
users: Mapped[list["User"]] = relationship(
    "User",
    back_populates="tenant",
    cascade="all, delete-orphan"
)
```

- **One tenant** can have **many users**
- **Deleting tenant** deletes all its users (CASCADE)
- **Owner user** created automatically with new tenant

### User → Tenant (Many-to-One)

```python
# User model
tenant: Mapped["Tenant"] = relationship(
    "Tenant",
    back_populates="users"
)
```

- **Each user** belongs to **exactly one tenant**
- **Foreign key** enforced at database level
- **Indexed** for fast tenant-scoped queries

### User → RefreshTokens (One-to-Many)

```python
# User model
refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
    "RefreshToken",
    back_populates="user",
    cascade="all, delete-orphan"
)
```

- **One user** can have **many refresh tokens**
- **Deleting user** deletes all their tokens (CASCADE)
- **Revoked tokens** marked with `is_revoked=True`

---

## Migration Path

### Default Tenant

A **default tenant** (id=1) is created during migration for backward compatibility:

```sql
INSERT INTO tenants (id, email, password_hash, is_active, created_at, updated_at)
VALUES (
    1,
    'default@system.local',
    '$2b$12$...',  -- Placeholder hash
    1,
    datetime('now'),
    datetime('now')
);
```

### Existing Users Migration

Existing users are migrated to the default tenant:

```sql
-- Add tenant_id column (nullable first)
ALTER TABLE users ADD COLUMN tenant_id INTEGER;
ALTER TABLE users ADD COLUMN username VARCHAR(100);
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'MEMBER';

-- Migrate existing users to default tenant
UPDATE users
SET
    tenant_id = 1,
    username = substr(email, 1, instr(email, '@') - 1),
    role = 'MEMBER'
WHERE tenant_id IS NULL;

-- Make columns NOT NULL
ALTER TABLE users ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE users ALTER COLUMN username SET NOT NULL;
ALTER TABLE users ALTER COLUMN role SET NOT NULL;
```

---

## Query Examples

### Get All Users in a Tenant

```python
from app.models.user import User

users = db.query(User).filter(User.tenant_id == tenant_id).all()
```

```sql
SELECT * FROM users WHERE tenant_id = ?;
```

### Get Tenant Owner

```python
owner = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.role == "OWNER"
).first()
```

```sql
SELECT * FROM users WHERE tenant_id = ? AND role = 'OWNER' LIMIT 1;
```

### Count Active Users per Tenant

```python
count = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.is_active == True
).count()
```

```sql
SELECT COUNT(*) FROM users WHERE tenant_id = ? AND is_active = 1;
```

### Find Tenant by Email (Case-Insensitive)

```python
from sqlalchemy import func
from app.models.tenant import Tenant

tenant = db.query(Tenant).filter(
    func.lower(Tenant.email) == email.lower()
).first()
```

```sql
SELECT * FROM tenants WHERE LOWER(email) = LOWER(?) LIMIT 1;
```

### Get User by Tenant and Username

```python
user = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.username == username
).first()
```

```sql
SELECT * FROM users WHERE tenant_id = ? AND username = ? LIMIT 1;
```

---

## Security Considerations

### Password Security

- **Hashing algorithm**: bcrypt
- **Rounds**: 12 (cost factor)
- **Storage**: Both `tenants.password_hash` and `users.password_hash`
- **Owner sync**: Owner user has same password_hash as tenant

### Email Normalization

```python
# Always normalize to lowercase before storage
email = email.lower()
```

- **Case-insensitive** authentication
- **Prevents duplicates** with different casing
- **Consistent lookups** across queries

### Tenant Isolation

- **All queries** must filter by `tenant_id`
- **JWT tokens** include `tenant_id` claim
- **Dependencies** validate tenant_id matches
- **Foreign keys** enforce referential integrity

### Composite Unique Constraints

```sql
UNIQUE (tenant_id, username)
```

- **Prevents duplicate** usernames within a tenant
- **Allows same username** across different tenants
- **Database-level enforcement** (not just application)

---

## Performance Optimization

### Indexes

All frequently queried columns are indexed:

- ✅ `tenants.email` (UNIQUE)
- ✅ `users.email` (UNIQUE)
- ✅ `users.username`
- ✅ `users.tenant_id`
- ✅ `users.(tenant_id, username)` (COMPOSITE UNIQUE)
- ✅ `refresh_tokens.token` (UNIQUE)
- ✅ `refresh_tokens.user_id`

### Query Patterns

```python
# BAD - Full table scan
all_users = db.query(User).all()

# GOOD - Tenant-scoped with index
tenant_users = db.query(User).filter(User.tenant_id == tenant_id).all()
```

### Cascade Deletes

- **Database-level** cascade for performance
- **No application-level** cleanup needed
- **Automatic** when tenant deleted

---

## Future Enhancements

### User Invitations Table

```sql
CREATE TABLE user_invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    invited_by_user_id INTEGER NOT NULL,
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'MEMBER',
    expires_at DATETIME NOT NULL,
    accepted_at DATETIME,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Audit Log Table

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

---

## Database Maintenance

### Cleanup Expired Tokens

```sql
DELETE FROM refresh_tokens
WHERE expires_at < datetime('now');
```

### Deactivate Inactive Tenants

```sql
UPDATE tenants
SET is_active = 0, updated_at = datetime('now')
WHERE id = ?;
```

### Count Users per Tenant

```sql
SELECT tenant_id, COUNT(*) as user_count
FROM users
WHERE is_active = 1
GROUP BY tenant_id
ORDER BY user_count DESC;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-07 | Initial multi-tenant schema implementation |

---

## References

- **Alembic Migration**: `alembic/versions/e9258cf92b4d_add_tenant_based_authentication.py`
- **Models**: `app/models/tenant.py`, `app/models/user.py`, `app/models/token.py`
- **Repositories**: `app/repositories/tenant_repository.py`, `app/repositories/user_repository.py`
- **Services**: `app/services/tenant_service.py`
- **Tests**: `tests/unit/test_tenant_repository.py`, `tests/unit/test_tenant_service.py`