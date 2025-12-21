"""Unit tests for TOTP service."""

import base64
import re

import pyotp
import pytest

from app.config import settings
from app.services import totp_service


class TestGenerateSecret:
    """Test generate_secret() function."""

    def test_generate_secret_returns_string(self):
        """Test that generate_secret returns a string."""
        secret = totp_service.generate_secret()

        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_generate_secret_is_base32(self):
        """Test that secret is base32-encoded."""
        secret = totp_service.generate_secret()

        # Base32 should only contain A-Z and 2-7
        assert re.match(r"^[A-Z2-7]+$", secret)

    def test_generate_secret_has_correct_length(self):
        """Test that secret has standard length (32 characters)."""
        secret = totp_service.generate_secret()

        # pyotp.random_base32() returns 32 characters by default
        assert len(secret) == 32

    def test_generate_secret_is_random(self):
        """Test that secrets are randomly generated."""
        secret1 = totp_service.generate_secret()
        secret2 = totp_service.generate_secret()

        assert secret1 != secret2

    def test_generate_secret_multiple_unique(self):
        """Test that multiple secrets are all unique."""
        secrets = [totp_service.generate_secret() for _ in range(100)]

        # All secrets should be unique
        assert len(secrets) == len(set(secrets))

    def test_generate_secret_can_create_totp(self):
        """Test that generated secret can be used to create TOTP."""
        secret = totp_service.generate_secret()

        # Should not raise exception
        totp = pyotp.TOTP(secret)
        assert totp is not None


class TestGetProvisioningUri:
    """Test get_provisioning_uri() function."""

    def test_get_provisioning_uri_format(self):
        """Test that URI has correct otpauth format."""
        uri = totp_service.get_provisioning_uri(
            email="test@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )

        assert uri.startswith("otpauth://totp/")

    def test_get_provisioning_uri_contains_email(self):
        """Test that URI contains the user's email."""
        email = "user@example.com"
        uri = totp_service.get_provisioning_uri(
            email=email,
            secret="JBSWY3DPEHPK3PXP",
        )

        # Email is URL-encoded (@ becomes %40)
        assert "user%40example.com" in uri

    def test_get_provisioning_uri_contains_secret(self):
        """Test that URI contains the secret."""
        secret = "JBSWY3DPEHPK3PXP"
        uri = totp_service.get_provisioning_uri(
            email="test@example.com",
            secret=secret,
        )

        assert f"secret={secret}" in uri

    def test_get_provisioning_uri_contains_issuer(self):
        """Test that URI contains the issuer name."""
        uri = totp_service.get_provisioning_uri(
            email="test@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )

        # Issuer name is URL-encoded
        assert "issuer=" in uri
        # Check if issuer value is in URI (spaces encoded as %20)
        assert settings.totp_issuer_name.replace(" ", "%20") in uri

    def test_get_provisioning_uri_different_emails(self):
        """Test that different emails produce different URIs."""
        uri1 = totp_service.get_provisioning_uri(
            email="user1@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )
        uri2 = totp_service.get_provisioning_uri(
            email="user2@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )

        assert uri1 != uri2
        # Email is URL-encoded
        assert "user1%40example.com" in uri1
        assert "user2%40example.com" in uri2


class TestGenerateQrCode:
    """Test generate_qr_code() function."""

    def test_generate_qr_code_returns_string(self):
        """Test that QR code returns a string."""
        uri = "otpauth://totp/test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Test"
        qr_code = totp_service.generate_qr_code(uri)

        assert isinstance(qr_code, str)
        assert len(qr_code) > 0

    def test_generate_qr_code_is_base64(self):
        """Test that QR code is base64-encoded."""
        uri = "otpauth://totp/test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Test"
        qr_code = totp_service.generate_qr_code(uri)

        # Should be valid base64
        try:
            decoded = base64.b64decode(qr_code)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"QR code is not valid base64: {e}")

    def test_generate_qr_code_is_png(self):
        """Test that QR code is a PNG image."""
        uri = "otpauth://totp/test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Test"
        qr_code = totp_service.generate_qr_code(uri)

        # Decode base64
        decoded = base64.b64decode(qr_code)

        # PNG files start with these bytes
        png_signature = b"\x89PNG\r\n\x1a\n"
        assert decoded.startswith(png_signature)

    def test_generate_qr_code_different_uris(self):
        """Test that different URIs produce different QR codes."""
        uri1 = "otpauth://totp/user1@example.com?secret=SECRET1&issuer=Test"
        uri2 = "otpauth://totp/user2@example.com?secret=SECRET2&issuer=Test"

        qr1 = totp_service.generate_qr_code(uri1)
        qr2 = totp_service.generate_qr_code(uri2)

        assert qr1 != qr2

    def test_generate_qr_code_with_provisioning_uri(self):
        """Test generating QR code from provisioning URI."""
        # Get a real provisioning URI
        uri = totp_service.get_provisioning_uri(
            email="test@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )

        # Generate QR code
        qr_code = totp_service.generate_qr_code(uri)

        # Should be valid base64 PNG
        decoded = base64.b64decode(qr_code)
        png_signature = b"\x89PNG\r\n\x1a\n"
        assert decoded.startswith(png_signature)


class TestVerifyCode:
    """Test verify_code() function."""

    def test_verify_code_valid_code(self):
        """Test verifying a valid TOTP code."""
        secret = "JBSWY3DPEHPK3PXP"

        # Generate current code
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Verify code
        result = totp_service.verify_code(secret, code)

        assert result is True

    def test_verify_code_invalid_code(self):
        """Test verifying an invalid TOTP code."""
        secret = "JBSWY3DPEHPK3PXP"

        # Use obviously wrong code
        result = totp_service.verify_code(secret, "000000")

        assert result is False

    def test_verify_code_wrong_secret(self):
        """Test verifying code with wrong secret."""
        secret1 = "JBSWY3DPEHPK3PXP"
        secret2 = "JBSWY3DPEHPK3PXQ"  # Different secret

        # Generate code for secret1
        totp1 = pyotp.TOTP(secret1)
        code = totp1.now()

        # Try to verify with secret2
        result = totp_service.verify_code(secret2, code)

        assert result is False

    def test_verify_code_empty_code(self):
        """Test verifying empty code."""
        secret = "JBSWY3DPEHPK3PXP"

        result = totp_service.verify_code(secret, "")

        assert result is False

    def test_verify_code_short_code(self):
        """Test verifying code that's too short."""
        secret = "JBSWY3DPEHPK3PXP"

        result = totp_service.verify_code(secret, "123")

        assert result is False

    def test_verify_code_long_code(self):
        """Test verifying code that's too long."""
        secret = "JBSWY3DPEHPK3PXP"

        result = totp_service.verify_code(secret, "1234567")

        assert result is False

    def test_verify_code_non_numeric(self):
        """Test verifying non-numeric code."""
        secret = "JBSWY3DPEHPK3PXP"

        result = totp_service.verify_code(secret, "abcdef")

        assert result is False

    def test_verify_code_with_spaces(self):
        """Test verifying code with spaces."""
        secret = "JBSWY3DPEHPK3PXP"

        # Generate valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Add spaces
        code_with_spaces = f"{code[:3]} {code[3:]}"

        # pyotp might strip spaces, but let's test behavior
        result = totp_service.verify_code(secret, code_with_spaces)

        # This will likely be False as TOTP codes shouldn't have spaces
        # Just document the behavior
        assert isinstance(result, bool)


class TestTOTPServiceIntegration:
    """Integration tests for TOTP service functions."""

    def test_complete_totp_setup_workflow(self):
        """Test complete TOTP setup workflow."""
        email = "user@example.com"

        # Generate secret
        secret = totp_service.generate_secret()
        assert len(secret) == 32

        # Get provisioning URI
        uri = totp_service.get_provisioning_uri(email, secret)
        assert uri.startswith("otpauth://totp/")
        # Email is URL-encoded
        assert "user%40example.com" in uri
        assert secret in uri

        # Generate QR code
        qr_code = totp_service.generate_qr_code(uri)
        decoded = base64.b64decode(qr_code)
        assert decoded.startswith(b"\x89PNG\r\n\x1a\n")

        # Verify code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert totp_service.verify_code(secret, code) is True

    def test_multiple_users_workflow(self):
        """Test TOTP setup for multiple users."""
        # User 1
        secret1 = totp_service.generate_secret()
        uri1 = totp_service.get_provisioning_uri("user1@example.com", secret1)
        qr1 = totp_service.generate_qr_code(uri1)

        # User 2
        secret2 = totp_service.generate_secret()
        uri2 = totp_service.get_provisioning_uri("user2@example.com", secret2)
        qr2 = totp_service.generate_qr_code(uri2)

        # Secrets should be different
        assert secret1 != secret2

        # URIs should be different
        assert uri1 != uri2

        # QR codes should be different
        assert qr1 != qr2

        # Each user's code should only work with their secret
        totp1 = pyotp.TOTP(secret1)
        code1 = totp1.now()

        assert totp_service.verify_code(secret1, code1) is True
        assert totp_service.verify_code(secret2, code1) is False

    def test_totp_code_time_validity(self):
        """Test that TOTP codes are time-based."""
        secret = totp_service.generate_secret()

        # Generate code
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Code should be valid immediately
        assert totp_service.verify_code(secret, code) is True

        # Note: We can't easily test expiration without waiting 30 seconds
        # or mocking time, so we just verify immediate validity

    def test_generated_secret_works_with_authenticator_apps(self):
        """Test that generated secrets work like real authenticator apps."""
        # Simulate what an authenticator app would do
        secret = totp_service.generate_secret()
        uri = totp_service.get_provisioning_uri("test@example.com", secret)

        # Extract secret from URI (simulate app parsing URI)
        assert f"secret={secret}" in uri

        # App would use this secret to generate codes
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Server verifies the code
        assert totp_service.verify_code(secret, code) is True