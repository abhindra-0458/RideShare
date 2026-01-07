from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func, desc
from models import LocationUpdate, User, DriftAlert, Ride, RideParticipant
from helpers import Helpers
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LocationRepository:
    """Location data access operations"""

    @staticmethod
    async def create_location_update(
        session: AsyncSession,
        user_id: str,
        location_data: dict
    ) -> LocationUpdate:
        """Create location update"""
        try:
            location = LocationUpdate(
                user_id=user_id,
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                accuracy=location_data.get("accuracy"),
                timestamp=location_data.get("timestamp") or datetime.utcnow()
            )
            session.add(location)
            await session.flush()
            
            # Update user's current location
            user = await session.get(User, user_id)
            if user:
                user.current_latitude = location.latitude
                user.current_longitude = location.longitude
                user.last_location_update = location.timestamp
                await session.flush()
            
            logger.info(f"Location updated for user {user_id}")
            return location
        except Exception as e:
            logger.error(f"Error creating location update: {e}")
            raise

    @staticmethod
    async def get_user_location_history(
        session: AsyncSession,
        user_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        ride_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[LocationUpdate]:
        """Get user's location history"""
        try:
            stmt = select(LocationUpdate).where(
                LocationUpdate.user_id == user_id
            )
            
            if start_date:
                stmt = stmt.where(LocationUpdate.timestamp >= start_date)
            if end_date:
                stmt = stmt.where(LocationUpdate.timestamp <= end_date)
            
            if ride_id:
                # Get ride timing
                ride = await session.get(Ride, ride_id)
                if ride:
                    ride_start = ride.scheduled_date_time
                    ride_end = ride_start + timedelta(
                        minutes=ride.estimated_duration_minutes or 120
                    )
                    stmt = stmt.where(
                        and_(
                            LocationUpdate.timestamp >= ride_start,
                            LocationUpdate.timestamp <= ride_end
                        )
                    )
            
            stmt = stmt.order_by(desc(LocationUpdate.timestamp)).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting location history: {e}")
            raise

    @staticmethod
    async def get_ride_participant_locations(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> list[dict]:
        """Get current locations of ride participants"""
        try:
            # Verify user is a participant
            participant_stmt = select(RideParticipant).where(
                and_(
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.user_id == user_id
                )
            )
            participant_result = await session.execute(participant_stmt)
            if not participant_result.scalar_one_or_none():
                raise ValueError("User is not a participant in this ride")
            
            # Get all accepted participants' current locations
            stmt = select(User).join(
                RideParticipant,
                and_(
                    User.id == RideParticipant.user_id,
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.status == "accepted"
                )
            ).where(
                and_(
                    User.current_latitude.isnot(None),
                    User.current_longitude.isnot(None)
                )
            )
            
            result = await session.execute(stmt)
            participants = result.scalars().all()
            
            locations = []
            for participant in participants:
                locations.append({
                    "id": participant.id,
                    "first_name": participant.first_name,
                    "last_name": participant.last_name,
                    "profile_picture_url": participant.profile_picture_url,
                    "latitude": participant.current_latitude,
                    "longitude": participant.current_longitude,
                    "last_location_update": participant.last_location_update
                })
            
            return locations
        except Exception as e:
            logger.error(f"Error getting ride participant locations: {e}")
            raise

    @staticmethod
    async def get_nearby_users(
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 5,
        exclude_user_id: str = None
    ) -> list[dict]:
        """Get nearby active users"""
        try:
            stmt = select(User).where(
                and_(
                    User.is_active == True,
                    User.is_profile_visible == True,
                    User.current_latitude.isnot(None),
                    User.current_longitude.isnot(None)
                )
            )
            
            if exclude_user_id:
                stmt = stmt.where(User.id != exclude_user_id)
            
            stmt = stmt.limit(50)
            
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            # Calculate distances
            nearby = []
            for user in users:
                distance = Helpers.calculate_distance(
                    latitude, longitude,
                    user.current_latitude, user.current_longitude
                )
                
                if distance <= radius_km:
                    nearby.append({
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "profile_picture_url": user.profile_picture_url,
                        "latitude": user.current_latitude,
                        "longitude": user.current_longitude,
                        "last_location_update": user.last_location_update,
                        "distance_km": round(distance, 2)
                    })
            
            # Sort by distance
            nearby.sort(key=lambda x: x["distance_km"])
            return nearby
        except Exception as e:
            logger.error(f"Error getting nearby users: {e}")
            raise

    @staticmethod
    async def check_drift_alerts(
        session: AsyncSession,
        ride_id: str
    ) -> list[dict]:
        """Check for drift alerts in a ride"""
        try:
            # Get all accepted ride participants with locations
            stmt = select(User).join(
                RideParticipant,
                and_(
                    User.id == RideParticipant.user_id,
                    RideParticipant.ride_id == ride_id,
                    RideParticipant.status == "accepted"
                )
            ).where(
                and_(
                    User.current_latitude.isnot(None),
                    User.current_longitude.isnot(None)
                )
            )
            
            result = await session.execute(stmt)
            participants = result.scalars().all()
            
            if len(participants) < 2:
                return []
            
            # Calculate center point
            center_lat = sum(p.current_latitude for p in participants) / len(participants)
            center_lon = sum(p.current_longitude for p in participants) / len(participants)
            
            # Check for drift
            from config import settings
            alerts = []
            
            for participant in participants:
                distance = Helpers.calculate_distance(
                    center_lat, center_lon,
                    participant.current_latitude, participant.current_longitude
                )
                
                if distance > settings.drift_alert_distance_km:
                    alert = DriftAlert(
                        ride_id=ride_id,
                        user_id=participant.id,
                        distance=distance,
                        latitude=participant.current_latitude,
                        longitude=participant.current_longitude
                    )
                    session.add(alert)
                    
                    alerts.append({
                        "user_id": participant.id,
                        "user_name": f"{participant.first_name} {participant.last_name}",
                        "distance_from_group": round(distance, 2),
                        "max_allowed_distance": settings.drift_alert_distance_km,
                        "latitude": participant.current_latitude,
                        "longitude": participant.current_longitude,
                        "timestamp": datetime.utcnow()
                    })
            
            await session.flush()
            logger.warning(f"{len(alerts)} drift alerts detected for ride {ride_id}")
            return alerts
        except Exception as e:
            logger.error(f"Error checking drift alerts: {e}")
            raise

    @staticmethod
    async def clean_old_location_data(
        session: AsyncSession,
        older_than_days: int = 30
    ) -> int:
        """Delete old location records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            
            stmt = select(LocationUpdate).where(
                LocationUpdate.created_at < cutoff_date
            )
            result = await session.execute(stmt)
            locations = result.scalars().all()
            
            for location in locations:
                await session.delete(location)
            
            await session.flush()
            
            deleted_count = len(locations)
            logger.info(f"Cleaned {deleted_count} old location records")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning old location data: {e}")
            raise
