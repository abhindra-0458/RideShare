from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, and_, func, desc
from models import Ride, RideParticipant, User
from schemas import RideStatus, ParticipantStatus
from helpers import Helpers
import logging

logger = logging.getLogger(__name__)

class RideRepository:
    """Ride data access operations"""

    @staticmethod
    async def create(session: AsyncSession, ride_data: dict, created_by: str) -> Ride:
        """Create new ride with creator as participant"""
        try:
            ride = Ride(**ride_data, created_by=created_by, status=RideStatus.SCHEDULED)
            session.add(ride)
            await session.flush()
            await session.refresh(ride)
            
            # Add creator as participant
            participant = RideParticipant(
                ride_id=ride.id,
                user_id=created_by,
                status=ParticipantStatus.ACCEPTED
            )
            session.add(participant)
            await session.flush()
            
            logger.info(f"Ride created: {ride.id} by user {created_by}")
            return ride
        except Exception as e:
            logger.error(f"Error creating ride: {e}")
            raise

    @staticmethod
    async def find_by_id(
        session: AsyncSession,
        ride_id: str,
        user_id: str = None
    ) -> Ride | None:
        """Find ride by ID with optional user info"""
        try:
            stmt = select(Ride).options(
                selectinload(Ride.creator),
                selectinload(Ride.participants).selectinload(RideParticipant.user)
            ).where(Ride.id == ride_id)
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding ride by ID: {e}")
            raise

    @staticmethod
    async def update(
        session: AsyncSession,
        ride_id: str,
        update_data: dict,
        user_id: str
    ) -> Ride | None:
        """Update ride (only by creator)"""
        try:
            ride = await RideRepository.find_by_id(session, ride_id, user_id)
            if not ride or ride.created_by != user_id:
                return None
            
            for key, value in update_data.items():
                if value is not None:
                    setattr(ride, key, value)
            
            await session.flush()
            await session.refresh(ride)
            logger.info(f"Ride updated: {ride_id}")
            return ride
        except Exception as e:
            logger.error(f"Error updating ride: {e}")
            raise

    @staticmethod
    async def delete(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> bool:
        """Delete ride (only by creator)"""
        try:
            ride = await RideRepository.find_by_id(session, ride_id)
            if not ride or ride.created_by != user_id:
                return False
            
            await session.delete(ride)
            await session.flush()
            logger.info(f"Ride deleted: {ride_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting ride: {e}")
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
    ) -> list[Ride]:
        """Get user's rides (created or joined)"""
        try:
            stmt = select(Ride).options(
                selectinload(Ride.creator),
                selectinload(Ride.participants)
            )
            
            if ride_type == "created":
                stmt = stmt.where(Ride.created_by == user_id)
            elif ride_type == "joined":
                stmt = stmt.join(RideParticipant).where(
                    and_(
                        RideParticipant.user_id == user_id,
                        Ride.created_by != user_id
                    )
                )
            else:  # "all"
                stmt = stmt.where(
                    or_(
                        Ride.created_by == user_id,
                        Ride.id.in_(
                            select(RideParticipant.ride_id).where(
                                RideParticipant.user_id == user_id
                            )
                        )
                    )
                )
            
            if status:
                stmt = stmt.where(Ride.status == status)
            
            # Sort
            sort_column = getattr(Ride, sort_by, Ride.scheduled_date_time)
            if sort_order == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(sort_column)
            
            stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user rides: {e}")
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
    ) -> list[Ride]:
        """Search rides by location and filters"""
        try:
            stmt = select(Ride).options(
                selectinload(Ride.creator),
                selectinload(Ride.participants)
            ).where(
                and_(
                    Ride.status == RideStatus.SCHEDULED,
                    Ride.is_public == is_public
                )
            )
            
            # Location-based search using distance calculation
            if latitude and longitude:
                # In production, use PostGIS ST_DWithin for better performance
                # For now, we'll filter in memory or use approximate distance
                pass
            
            # Date range filter
            if start_date:
                stmt = stmt.where(Ride.scheduled_date_time >= start_date)
            if end_date:
                stmt = stmt.where(Ride.scheduled_date_time <= end_date)
            
            # Difficulty filter
            if difficulty:
                stmt = stmt.where(Ride.difficulty == difficulty)
            
            # Exclude user's own rides
            if user_id:
                stmt = stmt.where(Ride.created_by != user_id)
            
            stmt = stmt.order_by(Ride.scheduled_date_time).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            rides = result.scalars().all()
            
            # Calculate distances if location provided
            if latitude and longitude:
                for ride in rides:
                    ride.distance_km = Helpers.calculate_distance(
                        latitude, longitude,
                        ride.start_latitude, ride.start_longitude
                    )
            
            return rides
        except Exception as e:
            logger.error(f"Error searching rides: {e}")
            raise

    @staticmethod
    async def get_ride_participants(
        session: AsyncSession,
        ride_id: str
    ) -> list[RideParticipant]:
        """Get ride participants with user info"""
        try:
            stmt = select(RideParticipant).options(
                selectinload(RideParticipant.user)
            ).where(
                RideParticipant.ride_id == ride_id
            ).order_by(RideParticipant.joined_at)
            
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting ride participants: {e}")
            raise

    @staticmethod
    async def join_ride(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> RideParticipant | None:
        """Join ride (with validations)"""
        try:
            # Check ride exists and is available
            ride = await RideRepository.find_by_id(session, ride_id)
            if not ride or ride.status != RideStatus.SCHEDULED:
                return None
            
            # Check participant count
            participant_count_stmt = select(func.count(RideParticipant.id)).where(
                and_(
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.status == ParticipantStatus.ACCEPTED
                )
            )
            participant_count_result = await session.execute(participant_count_stmt)
            participant_count = participant_count_result.scalar() or 0
            
            if participant_count >= ride.max_participants:
                return None  # Ride is full
            
            # Check if already a participant
            existing_stmt = select(RideParticipant).where(
                and_(
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.user_id == user_id
                )
            )
            existing_result = await session.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                return None  # Already participant
            
            # Add participant
            participant = RideParticipant(
                ride_id=ride_id,
                user_id=user_id,
                status=ParticipantStatus.ACCEPTED if ride.is_public else ParticipantStatus.PENDING
            )
            session.add(participant)
            await session.flush()
            await session.refresh(participant)
            
            logger.info(f"User {user_id} joined ride {ride_id}")
            return participant
        except Exception as e:
            logger.error(f"Error joining ride: {e}")
            raise

    @staticmethod
    async def leave_ride(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> bool:
        """Leave ride"""
        try:
            stmt = select(RideParticipant).where(
                and_(
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.user_id == user_id
                )
            )
            result = await session.execute(stmt)
            participant = result.scalar_one_or_none()
            
            if not participant:
                return False
            
            await session.delete(participant)
            await session.flush()
            
            logger.info(f"User {user_id} left ride {ride_id}")
            return True
        except Exception as e:
            logger.error(f"Error leaving ride: {e}")
            raise

    @staticmethod
    async def update_participant_status(
        session: AsyncSession,
        ride_id: str,
        user_id: str,
        status: str,
        updated_by: str
    ) -> RideParticipant | None:
        """Update participant status (only by creator)"""
        try:
            # Verify updater is ride creator
            ride = await RideRepository.find_by_id(session, ride_id)
            if not ride or ride.created_by != updated_by:
                return None
            
            stmt = select(RideParticipant).where(
                and_(
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.user_id == user_id
                )
            )
            result = await session.execute(stmt)
            participant = result.scalar_one_or_none()
            
            if not participant:
                return None
            
            participant.status = status
            await session.flush()
            await session.refresh(participant)
            
            logger.info(f"Participant {user_id} status updated to {status} in ride {ride_id}")
            return participant
        except Exception as e:
            logger.error(f"Error updating participant status: {e}")
            raise

    @staticmethod
    async def invite_users(
        session: AsyncSession,
        ride_id: str,
        user_ids: list[str],
        invited_by: str
    ) -> list[dict]:
        """Invite users to ride"""
        try:
            # Verify inviter is ride creator
            ride = await RideRepository.find_by_id(session, ride_id)
            if not ride or ride.created_by != invited_by:
                raise ValueError("Only ride creator can invite users")
            
            invitations = []
            for user_id in user_ids:
                try:
                    # Check if already participant
                    existing_stmt = select(RideParticipant).where(
                        and_(
                            RideParticipant.ride_id == ride_id,
                            RideParticipant.user_id == user_id
                        )
                    )
                    existing_result = await session.execute(existing_stmt)
                    if existing_result.scalar_one_or_none():
                        invitations.append({
                            "user_id": user_id,
                            "status": "already_participant"
                        })
                        continue
                    
                    # Add as pending participant
                    participant = RideParticipant(
                        ride_id=ride_id,
                        user_id=user_id,
                        status=ParticipantStatus.PENDING
                    )
                    session.add(participant)
                    await session.flush()
                    
                    invitations.append({
                        "user_id": user_id,
                        "status": "invited"
                    })
                except Exception as e:
                    invitations.append({
                        "user_id": user_id,
                        "status": "failed",
                        "error": str(e)
                    })
            
            logger.info(f"{len(user_ids)} users invited to ride {ride_id}")
            return invitations
        except Exception as e:
            logger.error(f"Error inviting users: {e}")
            raise

    @staticmethod
    async def get_participant_count(
        session: AsyncSession,
        ride_id: str
    ) -> int:
        """Get accepted participant count for ride"""
        try:
            stmt = select(func.count(RideParticipant.id)).where(
                and_(
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.status == ParticipantStatus.ACCEPTED
                )
            )
            result = await session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting participant count: {e}")
            raise
