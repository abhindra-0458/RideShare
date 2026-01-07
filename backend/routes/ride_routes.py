from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import (
    CreateRideRequest, UpdateRideRequest, SearchRidesRequest,
    InviteUsersRequest
)
from services.ride_service import RideService
from database import get_db
from auth import get_current_user
from response_handler import ApiResponse
from exceptions import NotFoundError, ForbiddenError, RideFullError, AlreadyParticipantError
from helpers import Helpers
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rides", tags=["Rides"])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    summary="Create a new ride",
    description="Create a new ride event"
)
async def create_ride(
    request: CreateRideRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create new ride"""
    try:
        ride_data = {
            "title": request.title,
            "description": request.description,
            "start_latitude": request.start_location.latitude,
            "start_longitude": request.start_location.longitude,
            "start_address": request.start_location.address,
            "end_latitude": request.end_location.latitude,
            "end_longitude": request.end_location.longitude,
            "end_address": request.end_location.address,
            "scheduled_date_time": request.scheduled_date_time,
            "is_public": request.is_public,
            "max_participants": request.max_participants,
            "estimated_duration_minutes": request.estimated_duration_minutes,
            "difficulty": request.difficulty
        }
        
        ride = await RideService.create_ride(
            session,
            ride_data,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=ride,
            message="Ride created successfully",
            status_code=201
        )
    except Exception as e:
        logger.error(f"Create ride error: {e}")
        return ApiResponse.error(
            message="Ride creation failed",
            status_code=500
        )

@router.get(
    "/{ride_id}",
    response_model=dict,
    summary="Get ride details",
    description="Retrieve ride information by ID"
)
async def get_ride(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get ride details"""
    try:
        ride = await RideService.get_ride_details(
            session,
            ride_id,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=ride,
            message="Ride retrieved successfully"
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Get ride error: {e}")
        return ApiResponse.error(
            message="Failed to get ride",
            status_code=500
        )

@router.put(
    "/{ride_id}",
    response_model=dict,
    summary="Update ride",
    description="Update ride details (creator only)"
)
async def update_ride(
    ride_id: str,
    request: UpdateRideRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update ride"""
    try:
        update_data = {
            "title": request.title,
            "description": request.description,
            "scheduled_date_time": request.scheduled_date_time,
            "is_public": request.is_public,
            "max_participants": request.max_participants,
            "estimated_duration_minutes": request.estimated_duration_minutes,
            "difficulty": request.difficulty,
            "status": request.status
        }
        
        # Handle location updates
        if request.start_location:
            update_data.update({
                "start_latitude": request.start_location.latitude,
                "start_longitude": request.start_location.longitude,
                "start_address": request.start_location.address
            })
        
        if request.end_location:
            update_data.update({
                "end_latitude": request.end_location.latitude,
                "end_longitude": request.end_location.longitude,
                "end_address": request.end_location.address
            })
        
        ride = await RideService.update_ride(
            session,
            ride_id,
            update_data,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=ride,
            message="Ride updated successfully"
        )
    except ForbiddenError as e:
        return ApiResponse.forbidden(e.message)
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Update ride error: {e}")
        return ApiResponse.error(
            message="Ride update failed",
            status_code=500
        )

@router.delete(
    "/{ride_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete ride",
    description="Delete ride (creator only)"
)
async def delete_ride(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Delete ride"""
    try:
        await RideService.delete_ride(
            session,
            ride_id,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            message="Ride deleted successfully"
        )
    except ForbiddenError as e:
        return ApiResponse.forbidden(e.message)
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Delete ride error: {e}")
        return ApiResponse.error(
            message="Ride deletion failed",
            status_code=500
        )

@router.get(
    "/user/{user_id}",
    response_model=dict,
    summary="Get user's rides",
    description="Retrieve rides created or joined by a user"
)
async def get_user_rides(
    user_id: str,
    ride_type: str = Query("all", regex="^(all|created|joined)$"),
    status: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("scheduled_date_time"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user's rides"""
    try:
        # Users can only see their own rides unless they're admin
        if user_id != current_user["user_id"] and current_user.get("role") != "admin":
            return ApiResponse.forbidden("Cannot access other user's rides")
        
        rides = await RideService.get_user_rides(
            session,
            user_id,
            ride_type=ride_type,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        pagination = Helpers.get_pagination_meta(
            page=(offset // limit) + 1,
            limit=limit,
            total=len(rides)
        )
        
        return ApiResponse.success(
            data={
                "rides": rides,
                "pagination": pagination
            },
            message="User rides retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Get user rides error: {e}")
        return ApiResponse.error(
            message="Failed to get user rides",
            status_code=500
        )

@router.get(
    "/search",
    response_model=dict,
    summary="Search rides",
    description="Search rides by location and filters"
)
async def search_rides(
    latitude: float = Query(None, ge=-90, le=90),
    longitude: float = Query(None, ge=-180, le=180),
    radius_km: float = Query(50, ge=0.1),
    start_date: str = Query(None),
    end_date: str = Query(None),
    difficulty: str = Query(None),
    is_public: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Search rides"""
    try:
        from datetime import datetime
        
        start_date_obj = datetime.fromisoformat(start_date) if start_date else None
        end_date_obj = datetime.fromisoformat(end_date) if end_date else None
        
        rides = await RideService.search_rides(
            session,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            start_date=start_date_obj,
            end_date=end_date_obj,
            difficulty=difficulty,
            is_public=is_public,
            user_id=current_user["user_id"],
            limit=limit,
            offset=offset
        )
        
        pagination = Helpers.get_pagination_meta(
            page=(offset // limit) + 1,
            limit=limit,
            total=len(rides)
        )
        
        return ApiResponse.success(
            data={
                "rides": rides,
                "pagination": pagination
            },
            message="Rides retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Search rides error: {e}")
        return ApiResponse.error(
            message="Ride search failed",
            status_code=500
        )

@router.post(
    "/{ride_id}/join",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    summary="Join a ride",
    description="Join an existing ride"
)
async def join_ride(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Join ride"""
    try:
        participant = await RideService.join_ride(
            session,
            ride_id,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=participant,
            message="Successfully joined ride"
        )
    except (NotFoundError, RideFullError, AlreadyParticipantError) as e:
        return ApiResponse.error(
            message=e.message,
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Join ride error: {e}")
        return ApiResponse.error(
            message="Failed to join ride",
            status_code=500
        )

@router.post(
    "/{ride_id}/leave",
    status_code=status.HTTP_200_OK,
    summary="Leave a ride",
    description="Leave a joined ride"
)
async def leave_ride(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Leave ride"""
    try:
        await RideService.leave_ride(
            session,
            ride_id,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            message="Successfully left ride"
        )
    except NotFoundError as e:
        return ApiResponse.not_found(e.message)
    except Exception as e:
        logger.error(f"Leave ride error: {e}")
        return ApiResponse.error(
            message="Failed to leave ride",
            status_code=500
        )

@router.get(
    "/{ride_id}/participants",
    response_model=dict,
    summary="Get ride participants",
    description="List all participants in a ride"
)
async def get_ride_participants(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get ride participants"""
    try:
        participants = await RideService.get_ride_participants(session, ride_id)
        
        return ApiResponse.success(
            data=participants,
            message="Participants retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Get ride participants error: {e}")
        return ApiResponse.error(
            message="Failed to get participants",
            status_code=500
        )

@router.put(
    "/{ride_id}/participants/{user_id}",
    response_model=dict,
    summary="Update participant status",
    description="Update participant status (creator only)"
)
async def update_participant_status(
    ride_id: str,
    user_id: str,
    status: str = Query(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update participant status"""
    try:
        participant = await RideService.update_participant_status(
            session,
            ride_id,
            user_id,
            status,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=participant,
            message="Participant status updated"
        )
    except ForbiddenError as e:
        return ApiResponse.forbidden(e.message)
    except Exception as e:
        logger.error(f"Update participant status error: {e}")
        return ApiResponse.error(
            message="Failed to update participant status",
            status_code=500
        )

@router.post(
    "/{ride_id}/invite",
    response_model=dict,
    summary="Invite users to ride",
    description="Send invitations to users (creator only)"
)
async def invite_users(
    ride_id: str,
    request: InviteUsersRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Invite users to ride"""
    try:
        invitations = await RideService.invite_users(
            session,
            ride_id,
            request.user_ids,
            current_user["user_id"],
            request.message or ""
        )
        
        return ApiResponse.success(
            data=invitations,
            message="Invitations sent"
        )
    except ForbiddenError as e:
        return ApiResponse.forbidden(e.message)
    except Exception as e:
        logger.error(f"Invite users error: {e}")
        return ApiResponse.error(
            message="Failed to send invitations",
            status_code=500
        )
