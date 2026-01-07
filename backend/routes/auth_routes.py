from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from schemas import (
    UserRegistrationRequest, UserLoginRequest, RefreshTokenRequest,
    ChangePasswordRequest, UserResponse, UserWithTokenResponse
)
from services.user_service import UserService
from database import get_db
from auth import get_current_user
from response_handler import ApiResponse
from exceptions import ConflictError, UnauthorizedError, BadRequestError, NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
async def register(
    request: UserRegistrationRequest,
    session: AsyncSession = Depends(get_db)
):
    """Register new user"""
    try:
        result = await UserService.register_user(
            session,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone
        )
        
        return ApiResponse.success(
            data=result,
            message="User registered successfully",
            status_code=201
        )
    except ConflictError as e:
        return ApiResponse.error(
            message=e.message,
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return ApiResponse.error(
            message="Registration failed",
            status_code=500
        )

@router.post(
    "/login",
    response_model=dict,
    summary="Login user",
    description="Authenticate user and get access tokens"
)
async def login(
    request: UserLoginRequest,
    session: AsyncSession = Depends(get_db)
):
    """Login user"""
    try:
        result = await UserService.login_user(
            session,
            email=request.email,
            password=request.password
        )
        
        return ApiResponse.success(
            data=result,
            message="Login successful"
        )
    except UnauthorizedError as e:
        return ApiResponse.unauthorized(e.message)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return ApiResponse.error(
            message="Login failed",
            status_code=500
        )

@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    try:
        result = await UserService.refresh_tokens(
            session,
            refresh_token=request.refresh_token
        )
        
        return ApiResponse.success(
            data=result,
            message="Token refreshed successfully"
        )
    except UnauthorizedError as e:
        return ApiResponse.unauthorized(e.message)
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return ApiResponse.error(
            message="Token refresh failed",
            status_code=500
        )

@router.post(
    "/logout",
    summary="Logout user",
    description="Invalidate refresh token and logout"
)
async def logout(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Logout user"""
    try:
        await UserService.logout_user(session, current_user["user_id"])
        
        return ApiResponse.success(
            message="Logout successful"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return ApiResponse.error(
            message="Logout failed",
            status_code=500
        )

@router.put(
    "/change-password",
    summary="Change user password",
    description="Update user's password"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Change user password"""
    try:
        await UserService.change_password(
            session,
            user_id=current_user["user_id"],
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        return ApiResponse.success(
            message="Password changed successfully"
        )
    except BadRequestError as e:
        return ApiResponse.error(
            message=e.message,
            status_code=e.status_code
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return ApiResponse.error(
            message="Password change failed",
            status_code=500
        )

@router.get(
    "/me",
    response_model=dict,
    summary="Get current user profile",
    description="Retrieve authenticated user's profile"
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    try:
        user = await UserService.get_user_profile(
            session,
            user_id=current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=user,
            message="User profile retrieved successfully"
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return ApiResponse.error(
            message="Failed to get user profile",
            status_code=500
        )
