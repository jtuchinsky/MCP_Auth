"""MCP-Compatible Authentication Service - FastAPI Application."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import AuthenticationError, AuthorizationError, TOTPError
from app.routes import auth, protected, well_known

# OpenAPI metadata for MCP compliance
DESCRIPTION = """
## MCP-Compatible Authentication Service

A production-ready FastAPI authentication service implementing OAuth 2.1 with MCP (Model Context Protocol) compliance.

### Features

* **User Registration & Login** - Secure account creation and authentication
* **JWT Access Tokens** - Short-lived tokens (15 minutes) with HS256 signing
* **Refresh Tokens** - Long-lived tokens (30 days) with rotation support
* **TOTP 2FA** - Time-based One-Time Password authentication
* **MCP OAuth 2.1 Compliance** - Full support for MCP authorization flows

### OAuth 2.1 & MCP Compliance

This service implements the following OAuth 2.1 and MCP specifications:

* ✅ **PKCE Required** (RFC 7636) - Proof Key for Code Exchange with S256 method
* ✅ **Resource Indicators** (RFC 8707) - Audience claims in JWT tokens
* ✅ **Authorization Server Metadata** (RFC 8414) - Discovery endpoint at `/.well-known/oauth-authorization-server`
* ✅ **Refresh Token Rotation** - New refresh token issued on each refresh
* ✅ **TOTP-based 2FA** - Multi-factor authentication support

### Security

* **bcrypt Password Hashing** - Industry-standard password protection
* **JWT Tokens** - Signed with HS256 algorithm
* **Active Account Validation** - Inactive accounts cannot authenticate
* **Secure Secret Management** - Environment-based configuration

### Authentication Flow

1. **Register** - Create account with email and password
2. **Login** - Authenticate and receive access + refresh tokens
3. **Optional: Enable TOTP** - Setup 2FA with authenticator app
4. **Access Protected Resources** - Use access token in Authorization header
5. **Refresh Tokens** - Get new access token when expired

### MCP Integration

MCP clients can discover authorization server capabilities at:
```
GET /.well-known/oauth-authorization-server
```

This returns RFC 8414 compliant metadata including supported grant types,
PKCE methods, and MCP-specific features.
"""

TAGS_METADATA = [
    {
        "name": "Authentication",
        "description": "User registration, login, token management, and TOTP 2FA operations.",
    },
    {
        "name": "Protected",
        "description": "Protected endpoints requiring valid JWT authentication.",
    },
    {
        "name": "MCP Metadata",
        "description": "OAuth 2.1 authorization server metadata for MCP client discovery (RFC 8414).",
    },
]

# Initialize FastAPI app
app = FastAPI(
    title="MCP-Compatible Auth Service",
    description=DESCRIPTION,
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "MCP Auth Service",
        "url": "https://github.com/jtuchinsky/MCP_Auth",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors (401 Unauthorized)."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(
    request: Request, exc: AuthorizationError
) -> JSONResponse:
    """Handle authorization errors (403 Forbidden)."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(TOTPError)
async def totp_error_handler(request: Request, exc: TOTPError) -> JSONResponse:
    """Handle TOTP-related errors (400 Bad Request)."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


# Include routers
app.include_router(auth.router)
app.include_router(protected.router)
app.include_router(well_known.router)


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Welcome endpoint with API information and links to documentation.",
)
async def root():
    """
    API root endpoint.

    Returns basic information about the API and links to documentation.
    """
    return {
        "message": "MCP-Compatible Authentication Service",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "oauth_metadata": "/.well-known/oauth-authorization-server",
        "mcp_compliant": True,
        "features": [
            "oauth2.1",
            "pkce",
            "resource_indicators",
            "totp",
            "jwt",
            "refresh_tokens",
        ],
    }


# Health check endpoint
@app.get(
    "/health",
    tags=["Root"],
    summary="Health Check",
    description="Simple health check endpoint for monitoring.",
)
async def health():
    """
    Health check endpoint.

    Returns the service status.
    """
    return {"status": "healthy", "service": "mcp-auth"}