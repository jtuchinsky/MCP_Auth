"""Custom exception classes for MCP Auth Service."""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """
    Exception raised when authentication fails.

    This includes cases like:
    - Invalid credentials (wrong email/password)
    - User not found
    - Invalid or expired tokens
    """

    def __init__(
        self,
        detail: str = "Authentication failed",
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize authentication error.

        Args:
            detail: Human-readable error message
            headers: Optional HTTP headers (e.g., WWW-Authenticate)
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
        )


class AuthorizationError(HTTPException):
    """
    Exception raised when authorization fails.

    This includes cases like:
    - User lacks required permissions
    - Access to forbidden resource
    - Invalid or insufficient scopes
    """

    def __init__(
        self,
        detail: str = "Not authorized to access this resource",
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize authorization error.

        Args:
            detail: Human-readable error message
            headers: Optional HTTP headers
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
        )


class TOTPError(HTTPException):
    """
    Exception raised when TOTP (Time-based One-Time Password) operations fail.

    This includes cases like:
    - Invalid TOTP code
    - TOTP code expired
    - TOTP not enabled for user
    - TOTP secret generation failed
    """

    def __init__(
        self,
        detail: str = "TOTP verification failed",
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize TOTP error.

        Args:
            detail: Human-readable error message
            headers: Optional HTTP headers
        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
        )
