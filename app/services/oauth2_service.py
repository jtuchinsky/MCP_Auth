"""OAuth2 service for authorization server metadata."""

from app.config import settings


def get_authorization_server_metadata(base_url: str) -> dict:
    """
    Get OAuth 2.0 Authorization Server Metadata per RFC 8414.

    Args:
        base_url: Base URL of the authorization server (e.g., "https://auth.example.com")

    Returns:
        Dictionary containing authorization server metadata

    Example:
        >>> metadata = get_authorization_server_metadata("https://auth.example.com")
        >>> print(metadata["issuer"])
        https://auth.example.com
    """
    return {
        # RFC 8414 Required fields
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/auth/authorize",
        "token_endpoint": f"{base_url}/auth/token",
        "response_types_supported": [
            "code",  # Authorization code flow (OAuth 2.1 recommended)
        ],
        "grant_types_supported": [
            "authorization_code",  # Standard authorization code
            "refresh_token",  # Token refresh
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",  # Client authentication via POST body
            "client_secret_basic",  # Client authentication via HTTP Basic
            "none",  # Public clients (PKCE required)
        ],
        # RFC 8414 Optional fields
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "scopes_supported": [
            "openid",  # OpenID Connect
            "profile",  # User profile information
            "email",  # User email
            "mcp:read",  # MCP read access
            "mcp:write",  # MCP write access
        ],
        "code_challenge_methods_supported": [
            "S256",  # SHA-256 PKCE (OAuth 2.1 required)
        ],
        "revocation_endpoint": f"{base_url}/auth/revoke",
        "revocation_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
            "none",
        ],
        # RFC 8707 - Resource Indicators
        "resource_indicators_supported": True,
        # Additional metadata
        "service_documentation": f"{base_url}/docs",
        "ui_locales_supported": ["en-US"],
        # MCP-specific metadata
        "mcp_version": "1.0",
        "mcp_features": [
            "oauth2.1",  # OAuth 2.1 compliance
            "pkce",  # PKCE support
            "resource_indicators",  # RFC 8707 support
            "totp",  # Two-factor authentication
        ],
    }