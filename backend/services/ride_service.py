from sqlalchemy.ext.asyncio import AsyncSession
from repositories.ride_repository import RideRepository
from repositories.user_repository import UserRepository
from redis_client import redis_client
from helpers import Helpers
from exceptions import (
    NotFoundError, ForbiddenError, RideNotAvailableError,
    RideFullError, AlreadyParticipantError, BadRequestError
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RideService:
    """Ride business logic"""

    @staticmethod
    async def create_ride(
        session: AsyncSession,
        ride_data: dict,
        created_by: str
    ) -> dict:
        """Create new ride"""
        try:
            ride = await RideRepository.create(session, ride_data, created_by)
            await session.commit()
            
            # Cache ride
            ride_dict = {
                "id": ride.id,
                "title": ride.title,
                "description": ride.description,
                "start_latitude": ride.start_latitude,
                "start_longitude": ride.start_longitude,
                "start_address": ride.start_address,
                "end_latitude": ride.end_latitude,
                "end_longitude": ride.end_longitude,
                "end_address": ride.end_address,
                "scheduled_date_time": ride.scheduled_date_time.isoformat(),
                "status": ride.status,
                "is_public": ride.is_public,
                "max_participants": ride.max_participants,
                "estimated_duration_minutes": ride.estimated_duration_minutes,
                "difficulty": ride.difficulty,
                "created_by": ride.created_by,
                "created_at": ride.created_at.isoformat(),
                "updated_at": ride.updated_at.isoformat()
            }
            
            await redis_client.set(f"ride:{ride.id}", ride_dict, 3600)
            
            logger.info(f"New ride created: {ride.id} by user {created_by}")
            
            return ride_dict
        except Exception as e:
            logger.error(f"Create ride error: {e}")
            raise

    @staticmethod
    async def get_ride_details(
        session: AsyncSession,
        ride_id: str,
        user_id: str = None
    ) -> dict:
        """Get ride details"""
        try:
            # Try cache first
            cached_ride = await redis_client.get(f"ride:{ride_id}")
            if cached_ride:
                ride_data = cached_ride
            else:
                ride = await RideRepository.find_by_id(session, ride_id, user_id)
                if not ride:
                    raise NotFoundError("Ride not found")
                
                ride_data = {
                    "id": ride.id,
                    "title": ride.title,
                    "description": ride.description,
                    "start_latitude": ride.start_latitude,
                    "start_longitude": ride.start_longitude,
                    "start_address": ride.start_address,
                    "end_latitude": ride.end_latitude,
                    "end_longitude": ride.end_longitude,
                    "end_address": ride.end_address,
                    "scheduled_date_time": ride.scheduled_date_time.isoformat(),
                    "status": ride.status,
                    "is_public": ride.is_public,
                    "max_participants": ride.max_participants,
                    "estimated_duration_minutes": ride.estimated_duration_minutes,
                    "difficulty": ride.difficulty,
                    "created_by": ride.created_by,
                    "creator_first_name": ride.creator.first_name if ride.creator else None,
                    "creator_last_name": ride.creator.last_name if ride.creator else None,
                    "creator_profile_picture": ride.creator.profile_picture_url if ride.creator else None,
                    "created_at": ride.created_at.isoformat(),
                    "updated_at": ride.updated_at.isoformat()
                }
                
                await redis_client.set(f"ride:{ride_id}", ride_data, 3600)
            
            # Get participant count
            participant_count = await RideRepository.get_participant_count(session, ride_id)
            ride_data["participant_count"] = participant_count
            
            return ride_data
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Get ride details error: {e}")
            raise

    @staticmethod
    async def update_ride(
        session: AsyncSession,
        ride_id: str,
        update_data: dict,
        user_id: str
    ) -> dict:
        """Update ride"""
        try:
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            ride = await RideRepository.update(session, ride_id, update_data, user_id)
            if not ride:
                raise ForbiddenError("You don't have permission to update this ride")
            
            await session.commit()
            
            # Update cache
            ride_dict = {
                "id": ride.id,
                "title": ride.title,
                "description": ride.description,
                "start_latitude": ride.start_latitude,
                "start_longitude": ride.start_longitude,
                "start_address": ride.start_address,
                "end_latitude": ride.end_latitude,
                "end_longitude": ride.end_longitude,
                "end_address": ride.end_address,
                "scheduled_date_time": ride.scheduled_date_time.isoformat(),
                "status": ride.status,
                "is_public": ride.is_public,
                "max_participants": ride.max_participants,
                "estimated_duration_minutes": ride.estimated_duration_minutes,
                "difficulty": ride.difficulty,
                "created_by": ride.created_by,
                "created_at": ride.created_at.isoformat(),
                "updated_at": ride.updated_at.isoformat()
            }
            
            await redis_client.set(f"ride:{ride_id}", ride_dict, 3600)
            
            logger.info(f"Ride updated: {ride_id}")
            
            return ride_dict
        except ForbiddenError:
            raise
        except Exception as e:
            logger.error(f"Update ride error: {e}")
            raise

    @staticmethod
    async def delete_ride(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> bool:
        """Delete ride"""
        try:
            success = await RideRepository.delete(session, ride_id, user_id)
            if not success:
                raise ForbiddenError("You don't have permission to delete this ride")
            
            await session.commit()
            
            # Remove from cache
            await redis_client.delete(f"ride:{ride_id}")
            
            logger.info(f"Ride deleted: {ride_id}")
            return True
        except ForbiddenError:
            raise
        except Exception as e:
            logger.error(f"Delete ride error: {e}")
            raise

    @staticmethod
    async def get_user_rides(
        session: AsyncSession,
        user_id: str,
        ride_type: str = "all",
        status: str = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "scheduled_date_time",
        sort_order: str = "asc"
    ) -> list[dict]:
        """Get user's rides"""
        try:
            rides = await RideRepository.get_user_rides(
                session, user_id, ride_type, status, limit, offset, sort_by, sort_order
            )
            
            result = []
            for ride in rides:
                ride_dict = {
                    "id": ride.id,
                    "title": ride.title,
                    "description": ride.description,
                    "start_latitude": ride.start_latitude,
                    "start_longitude": ride.start_longitude,
                    "start_address": ride.start_address,
                    "end_latitude": ride.end_latitude,
                    "end_longitude": ride.end_longitude,
                    "end_address": ride.end_address,
                    "scheduled_date_time": ride.scheduled_date_time.isoformat(),
                    "status": ride.status,
                    "is_public": ride.is_public,
                    "max_participants": ride.max_participants,
                    "estimated_duration_minutes": ride.estimated_duration_minutes,
                    "difficulty": ride.difficulty,
                    "created_by": ride.created_by,
                    "creator_first_name": ride.creator.first_name if ride.creator else None,
                    "creator_last_name": ride.creator.last_name if ride.creator else None,
                    "created_at": ride.created_at.isoformat(),
                    "updated_at": ride.updated_at.isoformat(),
                    "participant_count": len([p for p in ride.participants if p.status == "accepted"])
                }
                result.append(ride_dict)
            
            return result
        except Exception as e:
            logger.error(f"Get user rides error: {e}")
            raise

    @staticmethod
    async def search_rides(
        session: AsyncSession,
        latitude: float = None,
        longitude: float = None,
        radius_km: float = 50,
        start_date = None,
        end_date = None,
        difficulty: str = None,
        is_public: bool = True,
        user_id: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        """Search rides"""
        try:
            rides = await RideRepository.search_rides(
                session, latitude, longitude, radius_km, start_date, end_date,
                difficulty, is_public, user_id, limit, offset
            )
            
            result = []
            for ride in rides:
                ride_dict = {
                    "id": ride.id,
                    "title": ride.title,
                    "description": ride.description,
                    "start_latitude": ride.start_latitude,
                    "start_longitude": ride.start_longitude,
                    "start_address": ride.start_address,
                    "end_latitude": ride.end_latitude,
                    "end_longitude": ride.end_longitude,
                    "end_address": ride.end_address,
                    "scheduled_date_time": ride.scheduled_date_time.isoformat(),
                    "status": ride.status,
                    "is_public": ride.is_public,
                    "max_participants": ride.max_participants,
                    "estimated_duration_minutes": ride.estimated_duration_minutes,
                    "difficulty": ride.difficulty,
                    "created_by": ride.created_by,
                    "creator_first_name": ride.creator.first_name if ride.creator else None,
                    "creator_last_name": ride.creator.last_name if ride.creator else None,
                    "created_at": ride.created_at.isoformat(),
                    "updated_at": ride.updated_at.isoformat(),
                    "participant_count": len([p for p in ride.participants if p.status == "accepted"]),
                    "distance_km": getattr(ride, 'distance_km', None)
                }
                result.append(ride_dict)
            
            return result
        except Exception as e:
            logger.error(f"Search rides error: {e}")
            raise

    @staticmethod
    async def join_ride(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> dict:
        """Join a ride"""
        try:
            participant = await RideRepository.join_ride(session, ride_id, user_id)
            if not participant:
                # Check why join failed
                ride = await RideRepository.find_by_id(session, ride_id)
                if not ride:
                    raise NotFoundError("Ride not found")
                if ride.status != "scheduled":
                    raise RideNotAvailableError("Ride is not available")
                
                # Check if full
                participant_count = await RideRepository.get_participant_count(session, ride_id)
                if participant_count >= ride.max_participants:
                    raise RideFullError("Ride is full")
                
                raise AlreadyParticipantError("User is already a participant")
            
            await session.commit()
            
            logger.info(f"User {user_id} joined ride {ride_id}")
            
            return {
                "id": participant.id,
                "ride_id": participant.ride_id,
                "user_id": participant.user_id,
                "status": participant.status,
                "joined_at": participant.joined_at.isoformat()
            }
        except (NotFoundError, RideNotAvailableError, RideFullError, AlreadyParticipantError):
            raise
        except Exception as e:
            logger.error(f"Join ride error: {e}")
            raise

    @staticmethod
    async def leave_ride(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> bool:
        """Leave a ride"""
        try:
            success = await RideRepository.leave_ride(session, ride_id, user_id)
            if not success:
                raise NotFoundError("You are not a participant in this ride")
            
            await session.commit()
            
            # Clear ride cache
            await redis_client.delete(f"ride:{ride_id}")
            
            logger.info(f"User {user_id} left ride {ride_id}")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Leave ride error: {e}")
            raise

    @staticmethod
    async def get_ride_participants(
        session: AsyncSession,
        ride_id: str
    ) -> list[dict]:
        """Get ride participants"""
        try:
            participants = await RideRepository.get_ride_participants(session, ride_id)
            
            return [
                {
                    "id": p.id,
                    "ride_id": p.ride_id,
                    "user_id": p.user_id,
                    "first_name": p.user.first_name,
                    "last_name": p.user.last_name,
                    "profile_picture_url": p.user.profile_picture_url,
                    "email": p.user.email,
                    "status": p.status,
                    "joined_at": p.joined_at.isoformat()
                }
                for p in participants
            ]
        except Exception as e:
            logger.error(f"Get ride participants error: {e}")
            raise

    @staticmethod
    async def update_participant_status(
        session: AsyncSession,
        ride_id: str,
        user_id: str,
        status: str,
        updated_by: str
    ) -> dict:
        """Update participant status"""
        try:
            participant = await RideRepository.update_participant_status(
                session, ride_id, user_id, status, updated_by
            )
            if not participant:
                raise ForbiddenError("Only ride creator can update participant status")
            
            await session.commit()
            
            logger.info(f"Participant {user_id} status updated to {status} in ride {ride_id}")
            
            return {
                "id": participant.id,
                "ride_id": participant.ride_id,
                "user_id": participant.user_id,
                "status": participant.status,
                "joined_at": participant.joined_at.isoformat()
            }
        except ForbiddenError:
            raise
        except Exception as e:
            logger.error(f"Update participant status error: {e}")
            raise

    @staticmethod
    async def invite_users(
        session: AsyncSession,
        ride_id: str,
        user_ids: list[str],
        invited_by: str,
        message: str = ""
    ) -> list[dict]:
        """Invite users to ride"""
        try:
            invitations = await RideRepository.invite_users(
                session, ride_id, user_ids, invited_by
            )
            await session.commit()
            
            # Clear ride cache
            await redis_client.delete(f"ride:{ride_id}")
            
            logger.info(f"{len(user_ids)} users invited to ride {ride_id}")
            
            return invitations
        except ValueError as e:
            raise ForbiddenError(str(e))
        except Exception as e:
            logger.error(f"Invite users error: {e}")
            raise
