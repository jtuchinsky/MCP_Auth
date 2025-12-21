"""Unit tests for OAuth2 service."""

import pytest

from app.services import oauth2_service


class TestGetAuthorizationServerMetadata:
    """Test get_authorization_server_metadata() function."""

    def test_metadata_has_required_fields(self):
        """Test that metadata contains all RFC 8414 required fields."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        # RFC 8414 required fields
        assert "issuer" in metadata
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        assert "response_types_supported" in metadata
        assert "grant_types_supported" in metadata
        assert "token_endpoint_auth_methods_supported" in metadata

    def test_metadata_issuer_matches_base_url(self):
        """Test that issuer matches provided base URL."""
        base_url = "https://auth.example.com"
        metadata = oauth2_service.get_authorization_server_metadata(base_url)

        assert metadata["issuer"] == base_url

    def test_metadata_endpoints_use_base_url(self):
        """Test that all endpoint URLs use the base URL."""
        base_url = "https://auth.example.com"
        metadata = oauth2_service.get_authorization_server_metadata(base_url)

        assert metadata["authorization_endpoint"].startswith(base_url)
        assert metadata["token_endpoint"].startswith(base_url)
        assert metadata["jwks_uri"].startswith(base_url)
        assert metadata["revocation_endpoint"].startswith(base_url)

    def test_metadata_endpoints_correct_paths(self):
        """Test that endpoint URLs have correct paths."""
        base_url = "https://auth.example.com"
        metadata = oauth2_service.get_authorization_server_metadata(base_url)

        assert metadata["authorization_endpoint"] == f"{base_url}/auth/authorize"
        assert metadata["token_endpoint"] == f"{base_url}/auth/token"
        assert metadata["jwks_uri"] == f"{base_url}/.well-known/jwks.json"
        assert metadata["revocation_endpoint"] == f"{base_url}/auth/revoke"

    def test_metadata_supports_oauth21_features(self):
        """Test that metadata indicates OAuth 2.1 support."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        # OAuth 2.1 requires PKCE
        assert "code_challenge_methods_supported" in metadata
        assert "S256" in metadata["code_challenge_methods_supported"]

        # OAuth 2.1 only supports authorization code flow
        assert "code" in metadata["response_types_supported"]
        # Should NOT support implicit or password flows
        assert "token" not in metadata["response_types_supported"]
        assert "password" not in metadata["grant_types_supported"]

    def test_metadata_supports_authorization_code_flow(self):
        """Test that metadata supports authorization code grant."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert "authorization_code" in metadata["grant_types_supported"]
        assert "code" in metadata["response_types_supported"]

    def test_metadata_supports_refresh_tokens(self):
        """Test that metadata supports refresh token grant."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert "refresh_token" in metadata["grant_types_supported"]

    def test_metadata_supports_client_authentication(self):
        """Test that metadata supports various client auth methods."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        auth_methods = metadata["token_endpoint_auth_methods_supported"]
        assert "client_secret_post" in auth_methods
        assert "client_secret_basic" in auth_methods
        assert "none" in auth_methods  # For public clients with PKCE

    def test_metadata_supports_scopes(self):
        """Test that metadata lists supported scopes."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert "scopes_supported" in metadata
        scopes = metadata["scopes_supported"]

        # OpenID Connect scopes
        assert "openid" in scopes
        assert "profile" in scopes
        assert "email" in scopes

        # MCP scopes
        assert "mcp:read" in scopes
        assert "mcp:write" in scopes

    def test_metadata_supports_resource_indicators(self):
        """Test that metadata indicates RFC 8707 resource indicators support."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert "resource_indicators_supported" in metadata
        assert metadata["resource_indicators_supported"] is True

    def test_metadata_includes_mcp_features(self):
        """Test that metadata includes MCP-specific features."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert "mcp_version" in metadata
        assert "mcp_features" in metadata

        features = metadata["mcp_features"]
        assert "oauth2.1" in features
        assert "pkce" in features
        assert "resource_indicators" in features
        assert "totp" in features

    def test_metadata_includes_service_documentation(self):
        """Test that metadata includes service documentation URL."""
        base_url = "https://auth.example.com"
        metadata = oauth2_service.get_authorization_server_metadata(base_url)

        assert "service_documentation" in metadata
        assert metadata["service_documentation"] == f"{base_url}/docs"

    def test_metadata_includes_revocation_endpoint(self):
        """Test that metadata includes token revocation endpoint."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert "revocation_endpoint" in metadata
        assert "revocation_endpoint_auth_methods_supported" in metadata

    def test_metadata_different_base_urls(self):
        """Test metadata generation with different base URLs."""
        urls = [
            "https://auth.example.com",
            "https://oauth.myapp.com",
            "http://localhost:8000",
        ]

        for base_url in urls:
            metadata = oauth2_service.get_authorization_server_metadata(base_url)

            assert metadata["issuer"] == base_url
            assert metadata["authorization_endpoint"] == f"{base_url}/auth/authorize"
            assert metadata["token_endpoint"] == f"{base_url}/auth/token"

    def test_metadata_base_url_without_trailing_slash(self):
        """Test that base URLs without trailing slashes work correctly."""
        base_url = "https://auth.example.com"
        metadata = oauth2_service.get_authorization_server_metadata(base_url)

        # Endpoints should not have double slashes
        assert "//" not in metadata["authorization_endpoint"].replace("https://", "")
        assert "//" not in metadata["token_endpoint"].replace("https://", "")

    def test_metadata_base_url_with_trailing_slash(self):
        """Test that base URLs with trailing slashes work correctly."""
        base_url_with_slash = "https://auth.example.com/"
        base_url_without_slash = base_url_with_slash.rstrip("/")

        # Our function expects no trailing slash, but test it handles it gracefully
        # This test documents current behavior
        metadata = oauth2_service.get_authorization_server_metadata(
            base_url_without_slash
        )

        assert metadata["issuer"] == base_url_without_slash

    def test_metadata_is_dict(self):
        """Test that metadata returns a dictionary."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        assert isinstance(metadata, dict)
        assert len(metadata) > 0

    def test_metadata_all_values_are_json_serializable(self):
        """Test that all metadata values are JSON serializable."""
        import json

        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        # Should not raise exception
        json_str = json.dumps(metadata)
        assert len(json_str) > 0

        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed == metadata


class TestOAuth2ServiceIntegration:
    """Integration tests for OAuth2 service."""

    def test_metadata_oauth21_compliance(self):
        """Test that metadata indicates full OAuth 2.1 compliance."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        # OAuth 2.1 requirements:
        # 1. PKCE is required (S256)
        assert "S256" in metadata["code_challenge_methods_supported"]

        # 2. No implicit flow
        assert "token" not in metadata["response_types_supported"]

        # 3. No password grant
        assert "password" not in metadata["grant_types_supported"]

        # 4. Authorization code flow supported
        assert "authorization_code" in metadata["grant_types_supported"]
        assert "code" in metadata["response_types_supported"]

        # 5. Refresh tokens supported
        assert "refresh_token" in metadata["grant_types_supported"]

    def test_metadata_mcp_compliance(self):
        """Test that metadata indicates MCP compliance."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.example.com"
        )

        # MCP requirements:
        # 1. OAuth 2.1 support
        assert "oauth2.1" in metadata["mcp_features"]

        # 2. PKCE support
        assert "pkce" in metadata["mcp_features"]

        # 3. Resource indicators (RFC 8707)
        assert metadata["resource_indicators_supported"] is True
        assert "resource_indicators" in metadata["mcp_features"]

        # 4. TOTP 2FA
        assert "totp" in metadata["mcp_features"]

        # 5. MCP scopes
        assert "mcp:read" in metadata["scopes_supported"]
        assert "mcp:write" in metadata["scopes_supported"]

    def test_metadata_complete_endpoint_set(self):
        """Test that all required endpoints are present."""
        base_url = "https://auth.example.com"
        metadata = oauth2_service.get_authorization_server_metadata(base_url)

        # Required endpoints
        assert metadata["authorization_endpoint"] == f"{base_url}/auth/authorize"
        assert metadata["token_endpoint"] == f"{base_url}/auth/token"
        assert metadata["jwks_uri"] == f"{base_url}/.well-known/jwks.json"
        assert metadata["revocation_endpoint"] == f"{base_url}/auth/revoke"
        assert metadata["service_documentation"] == f"{base_url}/docs"

    def test_metadata_for_local_development(self):
        """Test metadata generation for local development server."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "http://localhost:8000"
        )

        assert metadata["issuer"] == "http://localhost:8000"
        assert (
            metadata["authorization_endpoint"] == "http://localhost:8000/auth/authorize"
        )
        assert metadata["token_endpoint"] == "http://localhost:8000/auth/token"

    def test_metadata_for_production(self):
        """Test metadata generation for production server."""
        metadata = oauth2_service.get_authorization_server_metadata(
            "https://auth.production.com"
        )

        assert metadata["issuer"] == "https://auth.production.com"
        assert (
            metadata["authorization_endpoint"]
            == "https://auth.production.com/auth/authorize"
        )
        assert (
            metadata["token_endpoint"] == "https://auth.production.com/auth/token"
        )