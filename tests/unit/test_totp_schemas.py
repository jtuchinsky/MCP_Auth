"""Unit tests for TOTP schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.totp import TOTPSetupResponse, TOTPValidateRequest, TOTPVerifyRequest


class TestTOTPSetupResponse:
    """Test TOTPSetupResponse schema."""

    def test_totp_setup_response_valid(self):
        """Test creating TOTPSetupResponse with valid data."""
        data = {
            "secret": "JBSWY3DPEHPK3PXP",
            "provisioning_uri": "otpauth://totp/MCP:user@example.com?secret=JBSWY3DPEHPK3PXP",
            "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        }
        response = TOTPSetupResponse(**data)

        assert response.secret == "JBSWY3DPEHPK3PXP"
        assert "otpauth://totp/" in response.provisioning_uri
        assert response.qr_code.startswith("iVBOR")

    def test_totp_setup_response_missing_secret(self):
        """Test that secret is required."""
        with pytest.raises(ValidationError):
            TOTPSetupResponse(
                provisioning_uri="otpauth://totp/test",
                qr_code="base64string",
            )

    def test_totp_setup_response_missing_provisioning_uri(self):
        """Test that provisioning_uri is required."""
        with pytest.raises(ValidationError):
            TOTPSetupResponse(
                secret="JBSWY3DPEHPK3PXP",
                qr_code="base64string",
            )

    def test_totp_setup_response_missing_qr_code(self):
        """Test that qr_code is required."""
        with pytest.raises(ValidationError):
            TOTPSetupResponse(
                secret="JBSWY3DPEHPK3PXP",
                provisioning_uri="otpauth://totp/test",
            )

    def test_totp_setup_response_secret_formats(self):
        """Test various secret formats."""
        secrets = [
            "JBSWY3DPEHPK3PXP",  # Standard base32
            "ABCDEFGHIJKLMNOP",  # Another base32
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",  # Long base32
        ]

        for secret in secrets:
            response = TOTPSetupResponse(
                secret=secret,
                provisioning_uri="otpauth://totp/test",
                qr_code="qr",
            )
            assert response.secret == secret

    def test_totp_setup_response_empty_strings(self):
        """Test that empty strings are allowed (validated server-side)."""
        response = TOTPSetupResponse(
            secret="",
            provisioning_uri="",
            qr_code="",
        )
        assert response.secret == ""
        assert response.provisioning_uri == ""
        assert response.qr_code == ""

    def test_totp_setup_response_provisioning_uri_format(self):
        """Test provisioning URI format validation."""
        # Valid otpauth URI
        response = TOTPSetupResponse(
            secret="SECRET",
            provisioning_uri="otpauth://totp/MCP%20Auth:user@example.com?secret=SECRET&issuer=MCP%20Auth",
            qr_code="qr",
        )
        assert response.provisioning_uri.startswith("otpauth://totp/")

        # Non-otpauth URI is also allowed (no strict validation)
        response2 = TOTPSetupResponse(
            secret="SECRET",
            provisioning_uri="https://example.com",
            qr_code="qr",
        )
        assert response2.provisioning_uri == "https://example.com"

    def test_totp_setup_response_qr_code_base64(self):
        """Test QR code with base64 data."""
        # Valid base64 string
        qr_code = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        response = TOTPSetupResponse(
            secret="SECRET",
            provisioning_uri="otpauth://totp/test",
            qr_code=qr_code,
        )
        assert response.qr_code == qr_code

    def test_totp_setup_response_model_dump(self):
        """Test serializing TOTPSetupResponse to dict."""
        response = TOTPSetupResponse(
            secret="JBSWY3DPEHPK3PXP",
            provisioning_uri="otpauth://totp/test",
            qr_code="qrcode123",
        )
        data = response.model_dump()

        assert data["secret"] == "JBSWY3DPEHPK3PXP"
        assert data["provisioning_uri"] == "otpauth://totp/test"
        assert data["qr_code"] == "qrcode123"

    def test_totp_setup_response_model_dump_json(self):
        """Test serializing TOTPSetupResponse to JSON."""
        response = TOTPSetupResponse(
            secret="JBSWY3DPEHPK3PXP",
            provisioning_uri="otpauth://totp/test",
            qr_code="qrcode",
        )
        json_str = response.model_dump_json()

        assert "JBSWY3DPEHPK3PXP" in json_str
        assert "otpauth://totp/test" in json_str
        assert "qrcode" in json_str


class TestTOTPVerifyRequest:
    """Test TOTPVerifyRequest schema."""

    def test_totp_verify_request_valid(self):
        """Test creating TOTPVerifyRequest with valid code."""
        data = {"totp_code": "123456"}
        request = TOTPVerifyRequest(**data)

        assert request.totp_code == "123456"

    def test_totp_verify_request_missing_code(self):
        """Test that totp_code is required."""
        with pytest.raises(ValidationError):
            TOTPVerifyRequest()

    def test_totp_verify_request_code_length(self):
        """Test TOTP code must be exactly 6 digits."""
        # Valid 6-digit code
        request = TOTPVerifyRequest(totp_code="000000")
        assert request.totp_code == "000000"

        # Too short
        with pytest.raises(ValidationError):
            TOTPVerifyRequest(totp_code="12345")

        # Too long
        with pytest.raises(ValidationError):
            TOTPVerifyRequest(totp_code="1234567")

    def test_totp_verify_request_code_digits_only(self):
        """Test TOTP code must be digits only."""
        # Valid digits
        valid_codes = ["123456", "000000", "999999", "012345"]
        for code in valid_codes:
            request = TOTPVerifyRequest(totp_code=code)
            assert request.totp_code == code

        # Contains letters
        with pytest.raises(ValidationError):
            TOTPVerifyRequest(totp_code="12345a")

        # Contains special characters
        with pytest.raises(ValidationError):
            TOTPVerifyRequest(totp_code="12345!")

        # Contains spaces
        with pytest.raises(ValidationError):
            TOTPVerifyRequest(totp_code="123 456")

    def test_totp_verify_request_empty_code(self):
        """Test that empty code is invalid."""
        with pytest.raises(ValidationError):
            TOTPVerifyRequest(totp_code="")

    def test_totp_verify_request_model_dump(self):
        """Test serializing TOTPVerifyRequest to dict."""
        request = TOTPVerifyRequest(totp_code="123456")
        data = request.model_dump()

        assert data["totp_code"] == "123456"

    def test_totp_verify_request_model_dump_json(self):
        """Test serializing TOTPVerifyRequest to JSON."""
        request = TOTPVerifyRequest(totp_code="654321")
        json_str = request.model_dump_json()

        assert "654321" in json_str


class TestTOTPValidateRequest:
    """Test TOTPValidateRequest schema."""

    def test_totp_validate_request_valid(self):
        """Test creating TOTPValidateRequest with valid code."""
        data = {"totp_code": "987654"}
        request = TOTPValidateRequest(**data)

        assert request.totp_code == "987654"

    def test_totp_validate_request_missing_code(self):
        """Test that totp_code is required."""
        with pytest.raises(ValidationError):
            TOTPValidateRequest()

    def test_totp_validate_request_code_length(self):
        """Test TOTP code must be exactly 6 digits."""
        # Valid 6-digit code
        request = TOTPValidateRequest(totp_code="111111")
        assert request.totp_code == "111111"

        # Too short
        with pytest.raises(ValidationError):
            TOTPValidateRequest(totp_code="12345")

        # Too long
        with pytest.raises(ValidationError):
            TOTPValidateRequest(totp_code="1234567")

    def test_totp_validate_request_code_digits_only(self):
        """Test TOTP code must be digits only."""
        # Valid digits
        request = TOTPValidateRequest(totp_code="456789")
        assert request.totp_code == "456789"

        # Contains non-digits
        with pytest.raises(ValidationError):
            TOTPValidateRequest(totp_code="abcdef")

    def test_totp_validate_request_model_dump(self):
        """Test serializing TOTPValidateRequest to dict."""
        request = TOTPValidateRequest(totp_code="246810")
        data = request.model_dump()

        assert data["totp_code"] == "246810"

    def test_totp_validate_request_model_dump_json(self):
        """Test serializing TOTPValidateRequest to JSON."""
        request = TOTPValidateRequest(totp_code="135790")
        json_str = request.model_dump_json()

        assert "135790" in json_str


class TestTOTPSchemasIntegration:
    """Integration tests for TOTP schemas."""

    def test_totp_setup_workflow(self):
        """Test complete TOTP setup workflow."""
        # 1. Server generates TOTP setup data
        setup_response = TOTPSetupResponse(
            secret="JBSWY3DPEHPK3PXP",
            provisioning_uri="otpauth://totp/MCP:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MCP",
            qr_code="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        )

        assert setup_response.secret == "JBSWY3DPEHPK3PXP"
        assert "otpauth://totp/" in setup_response.provisioning_uri
        assert len(setup_response.qr_code) > 0

        # 2. Client scans QR code and generates code
        # 3. Client sends verification request
        verify_request = TOTPVerifyRequest(totp_code="123456")

        assert verify_request.totp_code == "123456"
        assert len(verify_request.totp_code) == 6

    def test_totp_verify_and_validate_same_structure(self):
        """Test that verify and validate requests have same structure."""
        # Both should accept the same data
        code = "123456"

        verify = TOTPVerifyRequest(totp_code=code)
        validate = TOTPValidateRequest(totp_code=code)

        assert verify.totp_code == validate.totp_code
        assert verify.model_dump() == validate.model_dump()

    def test_all_schemas_json_serializable(self):
        """Test that all TOTP schemas are JSON serializable."""
        import json

        # TOTPSetupResponse
        setup = TOTPSetupResponse(
            secret="SECRET",
            provisioning_uri="otpauth://totp/test",
            qr_code="qr",
        )
        json.loads(setup.model_dump_json())

        # TOTPVerifyRequest
        verify = TOTPVerifyRequest(totp_code="123456")
        json.loads(verify.model_dump_json())

        # TOTPValidateRequest
        validate = TOTPValidateRequest(totp_code="654321")
        json.loads(validate.model_dump_json())

    def test_totp_enable_workflow(self):
        """Test TOTP enable workflow with schemas."""
        # 1. User requests TOTP setup
        # 2. Server generates and returns setup data
        setup = TOTPSetupResponse(
            secret="NEWTOTP SECRET123",
            provisioning_uri="otpauth://totp/App:user@example.com?secret=NEWTOTPSECRET123",
            qr_code="base64_encoded_qr_image_data",
        )

        # 3. User configures authenticator app
        # 4. User verifies with code
        verification = TOTPVerifyRequest(totp_code="654321")

        assert len(verification.totp_code) == 6
        assert verification.totp_code.isdigit()

        # 5. Server enables TOTP for user account
        # (handled in endpoint logic)

    def test_totp_login_workflow(self):
        """Test TOTP validation during login."""
        # During login, user provides TOTP code
        validate_request = TOTPValidateRequest(totp_code="789012")

        assert validate_request.totp_code == "789012"
        assert len(validate_request.totp_code) == 6

    def test_totp_codes_are_strings(self):
        """Test that TOTP codes are strings (not integers)."""
        # Codes like "000123" must preserve leading zeros
        verify = TOTPVerifyRequest(totp_code="000123")
        assert verify.totp_code == "000123"
        assert isinstance(verify.totp_code, str)

        # Verify it's not converted to integer
        validate = TOTPValidateRequest(totp_code="001234")
        assert validate.totp_code == "001234"
        assert validate.totp_code != "1234"