"""TOTP service for two-factor authentication."""

import base64
import io

import pyotp
import qrcode

from app.config import settings


def generate_secret() -> str:
    """
    Generate a random TOTP secret.

    Returns:
        Base32-encoded secret string

    Example:
        >>> secret = generate_secret()
        >>> print(len(secret) == 32)
        True
    """
    return pyotp.random_base32()


def get_provisioning_uri(email: str, secret: str) -> str:
    """
    Generate a provisioning URI for authenticator apps.

    Args:
        email: User's email address
        secret: Base32-encoded TOTP secret

    Returns:
        otpauth:// URI string

    Example:
        >>> uri = get_provisioning_uri("user@example.com", "JBSWY3DPEHPK3PXP")
        >>> print(uri.startswith("otpauth://totp/"))
        True
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name=settings.totp_issuer_name,
    )


def generate_qr_code(uri: str) -> str:
    """
    Generate a QR code image from a provisioning URI.

    Args:
        uri: otpauth:// provisioning URI

    Returns:
        Base64-encoded PNG image string

    Example:
        >>> uri = "otpauth://totp/user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MCP+Auth+Service"
        >>> qr = generate_qr_code(uri)
        >>> print(qr.startswith("iVBOR"))
        True
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return img_base64


def generate_code(secret: str) -> str:
    """
    Generate a current TOTP code for testing purposes.

    Args:
        secret: Base32-encoded TOTP secret

    Returns:
        6-digit TOTP code as string

    Example:
        >>> secret = "JBSWY3DPEHPK3PXP"
        >>> code = generate_code(secret)
        >>> print(len(code) == 6)
        True
        >>> print(code.isdigit())
        True
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


def verify_code(secret: str, code: str) -> bool:
    """
    Verify a TOTP code.

    Args:
        secret: Base32-encoded TOTP secret
        code: 6-digit TOTP code to verify

    Returns:
        True if code is valid, False otherwise

    Example:
        >>> secret = "JBSWY3DPEHPK3PXP"
        >>> totp = pyotp.TOTP(secret)
        >>> code = totp.now()
        >>> print(verify_code(secret, code))
        True
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code)