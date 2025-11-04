"""Authentication API routes"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from .models import GoogleLoginRequest, TokenRefreshRequest, TokenResponse, UserProfile
from .service import get_auth_service, AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]
    auth_service = get_auth_service()
    payload = auth_service.verify_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get('sub')
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/google/login", response_model=TokenResponse)
async def google_login(
    request: GoogleLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with Google ID token

    Flow:
    1. Client gets ID token from Google Sign-In
    2. Client sends ID token to this endpoint
    3. Server verifies token with Google
    4. Server creates or updates user
    5. Server returns JWT access and refresh tokens
    """
    try:
        # Verify Google ID token
        google_info = auth_service.verify_google_token(request.id_token)

        # Get or create user
        user = auth_service.get_or_create_user(google_info)

        # Create JWT tokens
        access_token = auth_service.create_access_token(
            user['user_id'],
            user['email'],
            user['role']
        )

        refresh_token = auth_service.create_refresh_token(user['user_id'])

        # Store refresh token
        auth_service.store_refresh_token(user['user_id'], refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth_service.access_token_expire_minutes * 60,  # Convert to seconds
            user=UserProfile(
                user_id=user['user_id'],
                email=user['email'],
                full_name=user['full_name'],
                role=user['role'],
                profile_picture_url=user.get('profile_picture_url'),
                phone=user.get('phone'),
                created_at=user.get('created_at'),
                last_login=user.get('last_login')
            )
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/refresh")
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token

    Returns new access token if refresh token is valid
    """
    try:
        # Verify refresh token
        user_id = auth_service.verify_refresh_token(request.refresh_token)

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Get user
        user = auth_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Create new access token
        access_token = auth_service.create_access_token(
            user['user_id'],
            user['email'],
            user['role']
        )

        return {
            "access_token": access_token,
            "expires_in": auth_service.access_token_expire_minutes * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user's profile

    Requires valid JWT access token in Authorization header
    """
    return UserProfile(
        user_id=current_user['user_id'],
        email=current_user['email'],
        full_name=current_user['full_name'],
        role=current_user['role'],
        profile_picture_url=current_user.get('profile_picture_url'),
        phone=current_user.get('phone'),
        created_at=current_user.get('created_at'),
        last_login=current_user.get('last_login')
    )


@router.post("/logout")
async def logout(
    request: TokenRefreshRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout and invalidate refresh token

    Requires valid JWT access token in Authorization header
    """
    try:
        auth_service.logout(current_user['user_id'], request.refresh_token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")
