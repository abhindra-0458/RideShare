from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import LocationUpdate, BatchLocationUpdate
from services.location_service import LocationService
from database import get_db
from auth import get_current_user
from response_handler import ApiResponse
from exceptions import NotFoundError, BadRequestError
from helpers import Helpers
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])

@router.post(
    "/update",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    summary="Update user location",
    description="Update current user location"
)
async def update_location(
    request: LocationUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update user location"""
    try:
        location = await LocationService.update_user_location(
            session,
            current_user["user_id"],
            latitude=request.latitude,
            longitude=request.longitude,
            accuracy=request.accuracy,
            timestamp=request.timestamp
        )
        
        return ApiResponse.success(
            data=location,
            message="Location updated successfully"
        )
    except Exception as e:
        logger.error(f"Update location error: {e}")
        return ApiResponse.error(
            message="Location update failed",
            status_code=500
        )

@router.post(
    "/batch-update",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    summary="Batch update locations",
    description="Update multiple location points"
)
async def batch_update_locations(
    request: BatchLocationUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Batch update locations"""
    try:
        results = await LocationService.batch_update_locations(
            session,
            current_user["user_id"],
            [loc.dict() for loc in request.locations]
        )
        
        return ApiResponse.success(
            data=results,
            message="Batch location update completed"
        )
    except Exception as e:
        logger.error(f"Batch update locations error: {e}")
        return ApiResponse.error(
            message="Batch location update failed",
            status_code=500
        )

@router.get(
    "/ride/{ride_id}",
    response_model=dict,
    summary="Get ride participant locations",
    description="Get current locations of all ride participants"
)
async def get_ride_locations(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get ride participant locations"""
    try:
        locations = await LocationService.get_ride_participant_locations(
            session,
            ride_id,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=locations,
            message="Ride locations retrieved successfully"
        )
    except BadRequestError as e:
        return ApiResponse.error(
            message=e.message,
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Get ride locations error: {e}")
        return ApiResponse.error(
            message="Failed to get ride locations",
            status_code=500
        )

@router.get(
    "/history",
    response_model=dict,
    summary="Get location history",
    description="Get user's location history with optional filtering"
)
async def get_location_history(
    start_date: str = Query(None),
    end_date: str = Query(None),
    ride_id: str = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get location history"""
    try:
        start_date_obj = datetime.fromisoformat(start_date) if start_date else None
        end_date_obj = datetime.fromisoformat(end_date) if end_date else None
        
        history = await LocationService.get_user_location_history(
            session,
            current_user["user_id"],
            start_date=start_date_obj,
            end_date=end_date_obj,
            ride_id=ride_id,
            limit=limit,
            offset=offset
        )
        
        pagination = Helpers.get_pagination_meta(
            page=(offset // limit) + 1,
            limit=limit,
            total=len(history)
        )
        
        return ApiResponse.success(
            data={
                "history": history,
                "pagination": pagination
            },
            message="Location history retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Get location history error: {e}")
        return ApiResponse.error(
            message="Failed to get location history",
            status_code=500
        )

@router.get(
    "/nearby",
    response_model=dict,
    summary="Get nearby users",
    description="Find users nearby current location"
)
async def get_nearby_users(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(5, ge=0.1, le=100),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get nearby users"""
    try:
        nearby = await LocationService.get_nearby_users(
            session,
            latitude,
            longitude,
            radius,
            current_user["user_id"]
        )
        
        return ApiResponse.success(
            data=nearby,
            message="Nearby users retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Get nearby users error: {e}")
        return ApiResponse.error(
            message="Failed to get nearby users",
            status_code=500
        )

@router.get(
    "/drift-alerts/{ride_id}",
    response_model=dict,
    summary="Check drift alerts",
    description="Check for location drift alerts in a ride"
)
async def check_drift_alerts(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Check drift alerts"""
    try:
        alerts = await LocationService.check_drift_alerts(session, ride_id)
        
        return ApiResponse.success(
            data=alerts,
            message="Drift alerts retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Check drift alerts error: {e}")
        return ApiResponse.error(
            message="Failed to check drift alerts",
            status_code=500
        )
