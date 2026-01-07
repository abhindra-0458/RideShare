from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, and_, func
from models import User, Ride, RideParticipant
from schemas import UserRole
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """User data access operations"""

    @staticmethod
    async def create(session: AsyncSession, user_data: dict) -> User:
        """Create new user"""
        try:
            user = User(**user_data)
            session.add(user)
            await session.flush()
            await session.refresh(user)
            logger.info(f"User created: {user.email}")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    async def find_by_id(session: AsyncSession, user_id: str) -> User | None:
        """Find user by ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding user by ID: {e}")
            raise

    @staticmethod
    async def find_by_email(session: AsyncSession, email: str) -> User | None:
        """Find user by email"""
        try:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            raise

    @staticmethod
    async def find_by_refresh_token(session: AsyncSession, refresh_token: str) -> User | None:
        """Find user by refresh token"""
        try:
            stmt = select(User).where(User.refresh_token == refresh_token)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding user by refresh token: {e}")
            raise

    @staticmethod
    async def update(session: AsyncSession, user_id: str, update_data: dict) -> User | None:
        """Update user"""
        try:
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                return None
            
            for key, value in update_data.items():
                if value is not None:
                    setattr(user, key, value)
            
            await session.flush()
            await session.refresh(user)
            logger.info(f"User updated: {user_id}")
            return user
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise

    @staticmethod
    async def update_password(session: AsyncSession, user_id: str, hashed_password: str) -> bool:
        """Update user password"""
        try:
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                return False
            
            user.password = hashed_password
            await session.flush()
            logger.info(f"Password updated for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            raise

    @staticmethod
    async def set_refresh_token(session: AsyncSession, user_id: str, refresh_token: str) -> bool:
        """Set refresh token"""
        try:
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                return False
            
            user.refresh_token = refresh_token
            await session.flush()
            return True
        except Exception as e:
            logger.error(f"Error setting refresh token: {e}")
            raise

    @staticmethod
    async def clear_refresh_token(session: AsyncSession, user_id: str) -> bool:
        """Clear refresh token"""
        try:
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                return False
            
            user.refresh_token = None
            await session.flush()
            return True
        except Exception as e:
            logger.error(f"Error clearing refresh token: {e}")
            raise

    @staticmethod
    async def get_user_stats(session: AsyncSession, user_id: str) -> dict:
        """Get user statistics"""
        try:
            # Count rides created
            rides_created_stmt = select(func.count(Ride.id)).where(Ride.created_by == user_id)
            rides_created_result = await session.execute(rides_created_stmt)
            rides_created = rides_created_result.scalar() or 0

            # Count rides joined
            rides_joined_stmt = select(func.count(RideParticipant.id)).where(
                and_(
                    RideParticipant.user_id == user_id,
                    RideParticipant.status == "accepted"
                )
            )
            rides_joined_result = await session.execute(rides_joined_stmt)
            rides_joined = rides_joined_result.scalar() or 0

            # Count completed rides
            completed_rides_stmt = select(func.count(Ride.id)).where(
                and_(
                    Ride.created_by == user_id,
                    Ride.status == "completed"
                )
            )
            completed_rides_result = await session.execute(completed_rides_stmt)
            completed_rides = completed_rides_result.scalar() or 0

            return {
                "rides_created": rides_created,
                "rides_joined": rides_joined,
                "completed_rides": completed_rides
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise

    @staticmethod
    async def search(
        session: AsyncSession,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[User]:
        """Search users by name or email"""
        try:
            stmt = select(User).where(
                and_(
                    User.is_active == True,
                    User.is_profile_visible == True,
                    or_(
                        User.first_name.ilike(f"%{query}%"),
                        User.last_name.ilike(f"%{query}%"),
                        User.email.ilike(f"%{query}%")
                    )
                )
            ).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            raise

    @staticmethod
    async def deactivate(session: AsyncSession, user_id: str) -> bool:
        """Deactivate user account"""
        try:
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                return False
            
            user.is_active = False
            await session.flush()
            logger.info(f"User deactivated: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            raise

    @staticmethod
    async def update_last_login(session: AsyncSession, user_id: str) -> bool:
        """Update last login time"""
        try:
            from datetime import datetime
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                return False
            
            user.last_login_at = datetime.utcnow()
            await session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            raise
