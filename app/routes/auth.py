"""Authentication routes for user registration, login, and TOTP."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, TOTPError
from app.database import get_db
from app.dependencies import get_current_user, require_totp_disabled
from app.models.user import User
from app.repositories import token_repository, user_repository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.totp import TOTPSetupResponse, TOTPValidateRequest, TOTPVerifyRequest
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service, totp_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.

    Args:
        user_data: User registration data (email, password)
        db: Database session

    Returns:
        UserResponse with user details

    Raises:
        HTTPException 400: If user already exists
    """
    try:
        user = auth_service.register_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
        )
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticate user and return access/refresh tokens. Returns 403 if TOTP is required.",
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Login with email and password.

    If user has TOTP enabled, returns 403 with message to use /auth/totp/validate.
    Otherwise, authenticates and returns tokens.

    Args:
        login_data: Login credentials (email, password, optional totp_code)
        db: Database session

    Returns:
        TokenResponse with access_token, refresh_token, token_type, expires_in

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If TOTP is required but not provided
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            db=db,
            email=login_data.email,
            password=login_data.password,
        )

        # Check if TOTP is enabled
        if user.is_totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="TOTP verification required. Use /auth/totp/validate endpoint.",
            )

        # Create tokens
        access_token, refresh_token_str = auth_service.create_tokens(
            db=db,
            user=user,
            client_id=None,
            scope=None,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=900,  # 15 minutes
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access and refresh tokens.",
)
async def refresh(
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token.

    Args:
        refresh_data: Refresh token
        db: Database session

    Returns:
        TokenResponse with new access_token and refresh_token

    Raises:
        HTTPException 401: If refresh token is invalid or expired
    """
    try:
        access_token, new_refresh_token = auth_service.refresh_access_token(
            db=db,
            refresh_token=refresh_data.refresh_token,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900,  # 15 minutes
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
    description="Revoke the provided refresh token. Idempotent operation - succeeds even if token doesn't exist.",
)
async def logout(
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db),
) -> None:
    """
    Logout user by revoking refresh token.

    This is an idempotent operation - it will succeed even if the
    token doesn't exist or is already revoked.

    Args:
        refresh_data: Refresh token to revoke
        db: Database session
    """
    try:
        token_repository.revoke_token(db=db, token=refresh_data.refresh_token)
    except ValueError:
        # Token not found - this is fine, logout is idempotent
        pass


@router.post(
    "/totp/setup",
    response_model=TOTPSetupResponse,
    summary="Setup TOTP 2FA",
    description="Generate TOTP secret and QR code for authenticator app setup. Requires authentication and TOTP must not be enabled.",
)
async def totp_setup(
    user: User = Depends(require_totp_disabled),
    db: Session = Depends(get_db),
) -> TOTPSetupResponse:
    """
    Setup TOTP 2FA for authenticated user.

    Generates a new TOTP secret and returns QR code for authenticator app.
    User must verify the code with /auth/totp/verify to enable TOTP.

    Args:
        user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        TOTPSetupResponse with secret, provisioning_uri, qr_code

    Raises:
        HTTPException 403: If TOTP is already enabled
    """
    # Generate TOTP secret
    secret = totp_service.generate_secret()

    # Save secret to user (but don't enable yet)
    user_repository.update_totp_secret(db=db, user_id=user.id, secret=secret)

    # Generate provisioning URI
    provisioning_uri = totp_service.get_provisioning_uri(
        email=user.email,
        secret=secret,
    )

    # Generate QR code
    qr_code = totp_service.generate_qr_code(provisioning_uri)

    return TOTPSetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_code=qr_code,
    )


@router.post(
    "/totp/verify",
    response_model=UserResponse,
    summary="Verify TOTP code and enable 2FA",
    description="Verify TOTP code to complete 2FA setup. Requires authentication.",
)
async def totp_verify(
    verify_data: TOTPVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Verify TOTP code and enable 2FA.

    Args:
        verify_data: TOTP code from authenticator app
        user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        UserResponse with updated user info

    Raises:
        HTTPException 400: If TOTP secret not set or code is invalid
    """
    # Check if user has TOTP secret
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP setup not initiated. Call /auth/totp/setup first.",
        )

    # Verify TOTP code
    is_valid = totp_service.verify_code(
        secret=user.totp_secret,
        code=verify_data.totp_code,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    # Enable TOTP for user
    updated_user = user_repository.enable_totp(db=db, user_id=user.id)

    return UserResponse.model_validate(updated_user)


@router.post(
    "/totp/validate",
    response_model=TokenResponse,
    summary="Login with TOTP",
    description="Authenticate with email, password, and TOTP code for users with 2FA enabled.",
)
async def totp_validate(
    validate_data: TOTPValidateRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Login with TOTP validation.

    For users with TOTP enabled, this endpoint authenticates with
    email, password, and TOTP code.

    Args:
        validate_data: Email, password, and TOTP code
        db: Database session

    Returns:
        TokenResponse with access_token and refresh_token

    Raises:
        HTTPException 401: If credentials or TOTP code are invalid
        HTTPException 403: If TOTP is not enabled for this user
    """
    try:
        # Authenticate user with password
        user = auth_service.authenticate_user(
            db=db,
            email=validate_data.email,
            password=validate_data.password,
        )

        # Check if TOTP is enabled
        if not user.is_totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="TOTP is not enabled for this user. Use /auth/login instead.",
            )

        # Verify TOTP code
        if not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TOTP secret not found.",
            )

        is_valid = totp_service.verify_code(
            secret=user.totp_secret,
            code=validate_data.totp_code,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code.",
            )

        # Create tokens
        access_token, refresh_token_str = auth_service.create_tokens(
            db=db,
            user=user,
            client_id=None,
            scope=None,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=900,  # 15 minutes
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )