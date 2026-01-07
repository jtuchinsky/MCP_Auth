# Tenant-Based Authentication Refactoring

## Status: IN PROGRESS (40% Complete)

This document tracks the refactoring of the MCP Auth service from single-user authentication to tenant-based multi-user authentication.

## What Changed

### Architecture Overview

**Old Flow:**
```
User registers with email + password
  → Creates User in database
  → Login with email + password
  → Returns JWT token
```

**New Flow:**
```
Tenant logs in with email + password
  → If tenant doesn't exist: Create Tenant + Owner User
  → If tenant exists: Authenticate tenant password
  → Returns JWT token for Owner user
  → (Future: Additional users can be invited by owner)
```

### Database Schema Changes

#### New: Tenants Table
```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

#### Updated: Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,              -- NEW: Foreign key to tenants
    username VARCHAR(100) NOT NULL,          -- NEW: Username (unique per tenant)
    email VARCHAR(255) UNIQUE NOT NULL,      -- Still globally unique
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'MEMBER',  -- NEW: OWNER, ADMIN, MEMBER
    totp_secret VARCHAR(32),
    is_totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE (tenant_id, username)             -- NEW: Username unique per tenant
);
```

### Key Design Decisions

1. **Tenant = Email + Password**: Tenants are identified by globally unique email addresses
2. **Auto-Creation**: First login with a new email automatically creates tenant + owner user
3. **Same Credentials**: Owner user has same email and password as tenant
4. **Global Email Uniqueness**: Emails remain globally unique (simpler, prevents confusion)
5. **Username Per Tenant**: Usernames are unique within each tenant
6. **User Roles**: OWNER (first user), ADMIN, MEMBER

## Implementation Progress

### ✅ Phase 1: Database Schema (COMPLETED)
- [x] Created `Tenant` model with email, password_hash, is_active
- [x] Updated `User` model with tenant_id, username, role
- [x] Alembic migration with default tenant for backward compatibility
- [x] Fresh database created successfully

**Files Changed:**
- `app/models/tenant.py` (NEW)
- `app/models/user.py` (MODIFIED)
- `app/models/__init__.py` (MODIFIED)
- `alembic/versions/e9258cf92b4d_add_tenant_based_authentication.py` (NEW)

### ✅ Phase 2: Repository Layer (COMPLETED)
- [x] Created `tenant_repository.py` with CRUD operations
- [x] Updated `user_repository.py` with tenant-scoped methods

**New Repository Functions:**
- `tenant_repository.create()`, `get_by_id()`, `get_by_email()`, `update_status()`
- `user_repository.get_by_tenant_and_username()`
- `user_repository.get_tenant_owner()`
- `user_repository.list_by_tenant()`
- `user_repository.count_tenant_users()`

**Files Changed:**
- `app/repositories/tenant_repository.py` (NEW)
- `app/repositories/user_repository.py` (MODIFIED - signature changes)

### ✅ Phase 3.1: Tenant Service (COMPLETED & TESTED)
- [x] Created `tenant_service.py` with auto-creation logic
- [x] Unit tests written and passing (23 tests total)

**Key Functions:**
- `authenticate_or_create_tenant()` - Core tenant auth flow with auto-creation
- `create_tenant_with_owner()` - Creates tenant + owner user atomically

**Test Results:**
- ✅ 13/13 tenant repository tests passing
- ✅ 10/10 tenant service tests passing
- ❌ Existing auth_service tests failing (expected - needs Phase 3.2)

**Files Changed:**
- `app/services/tenant_service.py` (NEW)
- `tests/unit/test_tenant_repository.py` (NEW)
- `tests/unit/test_tenant_service.py` (NEW)

### 🚧 Phase 3.2: Auth Service (PENDING)
- [ ] Update `auth_service.register_user()` to accept tenant_id, username, role
- [ ] Update `auth_service.authenticate_user()` for tenant-scoped auth
- [ ] Update `auth_service.create_tokens()` to include role in JWT

### 🚧 Phase 3.3: JWT Service (PENDING)
- [ ] Update `create_access_token()` to include role parameter
- [ ] Remove default tenant_id=1
- [ ] Add role claim to JWT payload

### 📋 Phase 4: API Schemas (PENDING)
- [ ] Create `app/schemas/tenant.py` with TenantLoginRequest, TenantResponse
- [ ] Update `LoginRequest` to include tenant_email field
- [ ] Update `UserResponse` to include tenant_id, username, role

### 📋 Phase 5: API Routes (PENDING)
- [ ] Update `/auth/login` to handle tenant authentication
- [ ] Add `/auth/login-user` for non-owner users (future)
- [ ] Update TOTP endpoints for tenant awareness
- [ ] Deprecate or update `/auth/register`

### 📋 Phase 6: Dependencies & Authorization (PENDING)
- [ ] Update `get_current_user()` to validate tenant isolation
- [ ] Add `require_owner()` dependency for role-based auth
- [ ] Add `require_admin_or_owner()` dependency

### 📋 Phase 7: Testing (PENDING)
- [ ] Update test fixtures with tenant support
- [ ] Fix failing unit tests (auth_service, jwt_service)
- [ ] Update integration tests with new login flow
- [ ] Add tenant isolation tests

### 📋 Phase 8: Documentation (IN PROGRESS)
- [x] Create this refactoring document
- [ ] Update CLAUDE.md with tenant architecture
- [ ] Update README.md with new API examples
- [ ] Update docs/RUNNING.md with new setup flow

## Current State

### What Works
1. ✅ Database schema with tenants and updated users table
2. ✅ Tenant repository operations (create, get, update, count)
3. ✅ User repository with tenant-scoped queries
4. ✅ Tenant authentication service with auto-creation
5. ✅ Email normalization to lowercase
6. ✅ Password hashing for both tenants and users
7. ✅ 23 unit tests passing

### What's Broken (Intentionally)
1. ❌ Auth service `register_user()` - signature changed
2. ❌ Auth endpoints - need tenant_email field
3. ❌ JWT tokens - missing role claim
4. ❌ Dependencies - no tenant validation yet
5. ❌ Most existing tests - need tenant context

### Database State
```bash
sqlite3 mcp_auth.db "SELECT * FROM tenants;"
# 1|default@system.local|$2b$12$...|1|2026-01-07 22:06:59|2026-01-07 22:06:59
```

Default tenant (id=1) created for backward compatibility.

## Example: New Tenant Creation Flow

```python
# User logs in for the first time
POST /auth/login
{
  "tenant_email": "company@example.com",
  "password": "secure_password"
}

# Backend flow:
1. Look up tenant by email (company@example.com)
2. NOT FOUND → Create new tenant:
   - Tenant: id=2, email=company@example.com, password_hash
   - Owner User: id=1, tenant_id=2, username=company@example.com,
                 email=company@example.com, role=OWNER
3. Return JWT token for owner user:
   {
     "sub": "1",
     "email": "company@example.com",
     "tenant_id": "2",
     "role": "OWNER",
     ...
   }
```

## Next Steps (Priority Order)

1. **Phase 3.2-3.3**: Update Auth & JWT services (unblock API layer)
2. **Phase 4**: Update API schemas (define contracts)
3. **Phase 5**: Update API routes (make endpoints work)
4. **Phase 6**: Update dependencies (add auth/authz)
5. **Phase 7**: Fix all tests (ensure quality)
6. **Phase 8**: Complete documentation (user-facing)

## Additional Documentation

- **Database Schema**: See [SCHEMAS.md](./SCHEMAS.md) for complete database structure documentation
- **Developer Guide**: See [../CLAUDE.md](../CLAUDE.md) for development instructions
- **Quick Start**: See [RUNNING.md](./RUNNING.md) for setup guide

## Migration Path

For existing deployments:
1. Default tenant (id=1) created automatically in migration
2. Existing users migrated to default tenant with username=email_prefix
3. No breaking changes for existing users in default tenant
4. New tenants can be created via login with new emails

## Security Considerations

1. ✅ **Password Hashing**: bcrypt with 12 rounds for both tenants and users
2. ✅ **Email Normalization**: All emails lowercase for consistency
3. ✅ **Case-Insensitive Lookups**: Tenant authentication is case-insensitive
4. ⚠️ **Tenant Isolation**: Not yet enforced in dependencies (Phase 6)
5. ⚠️ **Role-Based Access**: Not yet implemented (Phase 6)
6. ⚠️ **Token Validation**: JWT doesn't include role yet (Phase 3.3)

## Testing Strategy

- **Unit Tests**: Test each layer independently (repository, service, routes)
- **Integration Tests**: Test full authentication flows end-to-end
- **Tenant Isolation Tests**: Verify users cannot access other tenants' data
- **Role Tests**: Verify OWNER/ADMIN/MEMBER permissions

## Estimated Completion

- **Completed**: Phases 1-2, 3.1 (~40%)
- **Remaining**: Phases 3.2-8 (~60%)
- **Time to Complete**: 6-8 hours of focused development

## Questions & Decisions Log

**Q**: Should emails be globally unique or per-tenant unique?
**A**: Globally unique (simpler, prevents confusion, enables invitations)

**Q**: How do we identify the tenant on login?
**A**: By email (tenant_email field in login request)

**Q**: What happens on first login with new email?
**A**: Auto-create tenant + owner user with same credentials

**Q**: Can multiple users exist in one tenant?
**A**: Yes, but invitation system not implemented yet (future)

**Q**: Where is the default tenant used?
**A**: For migrated existing users (backward compatibility)