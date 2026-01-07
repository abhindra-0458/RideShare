from sqlalchemy.ext.asyncio import AsyncSession
from repositories.location_repository import LocationRepository
from redis_client import redis_client
from exceptions import NotFoundError, BadRequestError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LocationService:
    """Location business logic"""

    @staticmethod
    async def update_user_location(
        session: AsyncSession,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy: float = None,
        timestamp: datetime = None
    ) -> dict:
        """Update user location"""
        try:
            location_data = {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "timestamp": timestamp or datetime.utcnow()
            }
            
            location = await LocationRepository.create_location_update(
                session, user_id, location_data
            )
            await session.commit()
            
            # Cache in Redis
            await redis_client.set(
                f"user_location:{user_id}",
                {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "accuracy": location.accuracy,
                    "timestamp": location.timestamp.isoformat()
                },
                300  # 5 minutes
            )
            
            logger.info(f"Location updated for user {user_id}")
            
            return {
                "id": location.id,
                "user_id": location.user_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "accuracy": location.accuracy,
                "timestamp": location.timestamp.isoformat(),
                "created_at": location.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Update user location error: {e}")
            raise

    @staticmethod
    async def get_ride_participant_locations(
        session: AsyncSession,
        ride_id: str,
        user_id: str
    ) -> list[dict]:
        """Get ride participant locations"""
        try:
            # Try cache first
            cached = await redis_client.get(f"ride_locations:{ride_id}")
            if cached:
                return cached
            
            locations = await LocationRepository.get_ride_participant_locations(
                session, ride_id, user_id
            )
            
            # Cache for 30 seconds (real-time data)
            await redis_client.set(f"ride_locations:{ride_id}", locations, 30)
            
            logger.info(f"Retrieved locations for ride {ride_id}")
            return locations
        except ValueError as e:
            raise BadRequestError(str(e))
        except Exception as e:
            logger.error(f"Get ride participant locations error: {e}")
            raise

    @staticmethod
    async def get_user_location_history(
        session: AsyncSession,
        user_id: str,
        start_date = None,
        end_date = None,
        ride_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """Get user location history"""
        try:
            # Try cache first
            cache_key = f"location_history:{user_id}:{start_date}:{end_date}:{ride_id}:{limit}:{offset}"
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
            
            locations = await LocationRepository.get_user_location_history(
                session, user_id, start_date, end_date, ride_id, limit, offset
            )
            
            result = [
                {
                    "id": loc.id,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "accuracy": loc.accuracy,
                    "timestamp": loc.timestamp.isoformat(),
                    "created_at": loc.created_at.isoformat()
                }
                for loc in locations
            ]
            
            # Cache for 10 minutes
            await redis_client.set(cache_key, result, 600)
            
            logger.info(f"Retrieved location history for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Get location history error: {e}")
            raise

    @staticmethod
    async def get_nearby_users(
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 5,
        exclude_user_id: str = None
    ) -> list[dict]:
        """Get nearby users"""
        try:
            # Try cache first
            cache_key = f"nearby_users:{latitude}:{longitude}:{radius_km}:{exclude_user_id or 'none'}"
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
            
            nearby = await LocationRepository.get_nearby_users(
                session, latitude, longitude, radius_km, exclude_user_id
            )
            
            # Cache for 1 minute
            await redis_client.set(cache_key, nearby, 60)
            
            logger.info(f"Retrieved {len(nearby)} nearby users")
            return nearby
        except Exception as e:
            logger.error(f"Get nearby users error: {e}")
            raise

    @staticmethod
    async def check_drift_alerts(
        session: AsyncSession,
        ride_id: str
    ) -> list[dict]:
        """Check for drift alerts in ride"""
        try:
            alerts = await LocationRepository.check_drift_alerts(session, ride_id)
            await session.commit()
            
            if alerts:
                # Cache alerts for 5 minutes
                await redis_client.set(f"drift_alerts:{ride_id}", alerts, 300)
                logger.warning(f"{len(alerts)} drift alerts detected for ride {ride_id}")
            
            return alerts
        except Exception as e:
            logger.error(f"Check drift alerts error: {e}")
            raise

    @staticmethod
    async def batch_update_locations(
        session: AsyncSession,
        user_id: str,
        locations: list[dict]
    ) -> list[dict]:
        """Batch update locations"""
        try:
            results = []
            
            for location_data in locations:
                try:
                    location = await LocationService.update_user_location(
                        session,
                        user_id,
                        location_data["latitude"],
                        location_data["longitude"],
                        location_data.get("accuracy"),
                        location_data.get("timestamp")
                    )
                    results.append({
                        "success": True,
                        "location": location
                    })
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"Batch location update completed: {len(results)} updates processed")
            return results
        except Exception as e:
            logger.error(f"Batch update locations error: {e}")
            raise

    @staticmethod
    async def clean_old_location_data(
        session: AsyncSession,
        older_than_days: int = 30
    ) -> int:
        """Clean old location records"""
        try:
            deleted_count = await LocationRepository.clean_old_location_data(
                session, older_than_days
            )
            await session.commit()
            
            logger.info(f"Cleaned {deleted_count} old location records")
            return deleted_count
        except Exception as e:
            logger.error(f"Clean old location data error: {e}")
            raise
