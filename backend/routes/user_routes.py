from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import UserSearchRequest, UserProfileUpdate
from services.user_service import UserService
from database import get_db
from auth import get_current_user
from response_handler import ApiResponse
from exceptions import NotFoundError, BadRequestError
from helpers import Helpers
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get(
    "/{user_id}",
    response_model=dict,
    summary="Get user profile by ID",
    description="Retrieve user profile information"
)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user profile by ID"""
    try:
        user = await UserService.get_user_profile(session, user_id)
        
        return ApiResponse.success(
            data=user,
            message="User profile retrieved successfully"
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Get user by ID error: {e}")
        return ApiResponse.error(
            message="Failed to get user profile",
            status_code=500
        )

@router.put(
    "/profile",
    response_model=dict,
    summary="Update user profile",
    description="Update authenticated user's profile information"
)
async def update_profile(
    request: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    try:
        update_data = request.dict(exclude_unset=True)
        user = await UserService.update_user_profile(
            session,
            user_id=current_user["user_id"],
            update_data=update_data
        )
        
        return ApiResponse.success(
            data=user,
            message="Profile updated successfully"
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return ApiResponse.error(
            message="Profile update failed",
            status_code=500
        )

@router.get(
    "/search",
    response_model=dict,
    summary="Search users",
    description="Search users by name or email"
)
async def search_users(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Search users"""
    try:
        users = await UserService.search_users(
            session,
            query=q,
            limit=limit,
            offset=offset
        )
        
        total_count = len(users)
        pagination = Helpers.get_pagination_meta(
            page=(offset // limit) + 1,
            limit=limit,
            total=total_count
        )
        
        return ApiResponse.success(
            data={
                "users": users,
                "pagination": pagination
            },
            message="Users retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Search users error: {e}")
        return ApiResponse.error(
            message="User search failed",
            status_code=500
        )

@router.delete(
    "/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Deactivate user account",
    description="Deactivate authenticated user's account"
)
async def deactivate_account(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Deactivate user account"""
    try:
        await UserService.deactivate_user(
            session,
            user_id=current_user["user_id"]
        )
        
        return ApiResponse.success(
            message="Account deactivated successfully"
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Deactivate account error: {e}")
        return ApiResponse.error(
            message="Account deactivation failed",
            status_code=500
        )
