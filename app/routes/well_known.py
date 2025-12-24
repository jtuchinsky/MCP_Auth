"""Well-known endpoints for MCP OAuth 2.1 metadata."""

from fastapi import APIRouter, Request

from app.services import oauth2_service

router = APIRouter(prefix="/.well-known", tags=["MCP Metadata"])


@router.get(
    "/oauth-authorization-server",
    summary="OAuth 2.1 Authorization Server Metadata",
    description="RFC 8414 compliant OAuth 2.1 authorization server metadata for MCP clients.",
    response_description="Authorization server metadata including endpoints, supported features, and MCP capabilities",
)
async def get_oauth_metadata(request: Request) -> dict:
    """
    Get OAuth 2.1 authorization server metadata.

    Returns RFC 8414 compliant metadata for MCP (Model Context Protocol) clients.
    This endpoint provides discovery information about the authorization server's
    capabilities, supported grant types, and MCP-specific features.

    MCP OAuth 2.1 Compliance:
    - PKCE required (S256 method)
    - Resource indicators (RFC 8707)
    - Refresh token rotation
    - TOTP-based 2FA support

    Args:
        request: FastAPI request object (used to determine base URL)

    Returns:
        Dictionary containing OAuth 2.1 authorization server metadata

    Example Response:
        {
          "issuer": "http://localhost:8000",
          "authorization_endpoint": "http://localhost:8000/auth/authorize",
          "token_endpoint": "http://localhost:8000/auth/token",
          "response_types_supported": ["code"],
          "grant_types_supported": ["authorization_code", "refresh_token"],
          "code_challenge_methods_supported": ["S256"],
          "resource_indicators_supported": true,
          "mcp_version": "1.0",
          "mcp_features": ["oauth2.1", "pkce", "resource_indicators", "totp"]
        }

    See Also:
        - RFC 8414: OAuth 2.0 Authorization Server Metadata
        - RFC 7636: PKCE (Proof Key for Code Exchange)
        - RFC 8707: Resource Indicators for OAuth 2.0
        - MCP Specification: https://modelcontextprotocol.io
    """
    # Construct base URL from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # Get metadata from OAuth2 service
    metadata = oauth2_service.get_authorization_server_metadata(base_url)

    return metadata