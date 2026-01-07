from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from redis_client import redis_client
from helpers import Helpers
from exceptions import (
    ConflictError, NotFoundError, UnauthorizedError,
    BadRequestError
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserService:
    """User business logic"""

    @staticmethod
    async def register_user(
        session: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str
    ) -> dict:
        """Register new user"""
        try:
            # Check if user already exists
            existing_user = await UserRepository.find_by_email(session, email)
            if existing_user:
                raise ConflictError("User with this email already exists")
            
            # Hash password
            hashed_password = await Helpers.hash_password(password)
            
            # Create user
            user_data = {
                "email": email,
                "password": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "role": "user"
            }
            
            user = await UserRepository.create(session, user_data)
            await session.commit()
            
            # Generate tokens
            tokens = Helpers.generate_tokens({
                "user_id": user.id,
                "email": user.email,
                "role": user.role
            })
            
            # Store refresh token in DB
            await UserRepository.set_refresh_token(
                session, user.id, tokens["refresh_token"]
            )
            await session.commit()
            
            # Cache user
            await redis_client.set(f"user:{user.id}", {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }, 3600)
            
            sanitized_user = Helpers.sanitize_user({
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "is_profile_visible": user.is_profile_visible,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            })
            
            logger.info(f"New user registered: {email}")
            
            return {
                "user": sanitized_user,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer"
            }
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"User registration error: {e}")
            raise

    @staticmethod
    async def login_user(
        session: AsyncSession,
        email: str,
        password: str
    ) -> dict:
        """Login user"""
        try:
            user = await UserRepository.find_by_email(session, email)
            if not user:
                raise UnauthorizedError("Invalid email or password")
            
            if not user.is_active:
                raise UnauthorizedError("Account is deactivated")
            
            # Verify password
            is_valid = await Helpers.compare_password(password, user.password)
            if not is_valid:
                raise UnauthorizedError("Invalid email or password")
            
            # Generate tokens
            tokens = Helpers.generate_tokens({
                "user_id": user.id,
                "email": user.email,
                "role": user.role
            })
            
            # Store refresh token
            await UserRepository.set_refresh_token(
                session, user.id, tokens["refresh_token"]
            )
            
            # Update last login
            await UserRepository.update_last_login(session, user.id)
            await session.commit()
            
            # Cache user
            sanitized_user = Helpers.sanitize_user({
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "is_profile_visible": user.is_profile_visible,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            })
            
            await redis_client.set(f"user:{user.id}", sanitized_user, 3600)
            
            logger.info(f"User logged in: {email}")
            
            return {
                "user": sanitized_user,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer"
            }
        except UnauthorizedError:
            raise
        except Exception as e:
            logger.error(f"User login error: {e}")
            raise

    @staticmethod
    async def refresh_tokens(
        session: AsyncSession,
        refresh_token: str
    ) -> dict:
        """Refresh access token"""
        try:
            # Verify refresh token
            try:
                decoded = Helpers.verify_refresh_token(refresh_token)
            except Exception:
                raise UnauthorizedError("Invalid refresh token")
            
            # Find user with this token
            user = await UserRepository.find_by_refresh_token(session, refresh_token)
            if not user or not user.is_active:
                raise UnauthorizedError("Invalid refresh token")
            
            # Generate new tokens
            new_tokens = Helpers.generate_tokens({
                "user_id": user.id,
                "email": user.email,
                "role": user.role
            })
            
            # Update refresh token
            await UserRepository.set_refresh_token(
                session, user.id, new_tokens["refresh_token"]
            )
            await session.commit()
            
            # Update cache
            sanitized_user = Helpers.sanitize_user({
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "is_profile_visible": user.is_profile_visible,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            })
            
            await redis_client.set(f"user:{user.id}", sanitized_user, 3600)
            
            logger.info(f"Tokens refreshed for user: {user.id}")
            
            return {
                "user": sanitized_user,
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens["refresh_token"],
                "token_type": "bearer"
            }
        except UnauthorizedError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise

    @staticmethod
    async def logout_user(session: AsyncSession, user_id: str) -> bool:
        """Logout user"""
        try:
            await UserRepository.clear_refresh_token(session, user_id)
            await session.commit()
            
            # Remove from cache
            await redis_client.delete(f"user:{user_id}")
            
            logger.info(f"User logged out: {user_id}")
            return True
        except Exception as e:
            logger.error(f"User logout error: {e}")
            raise

    @staticmethod
    async def get_user_profile(
        session: AsyncSession,
        user_id: str
    ) -> dict:
        """Get user profile with stats"""
        try:
            # Try cache first
            cached_user = await redis_client.get(f"user:{user_id}")
            if cached_user:
                user_dict = cached_user
            else:
                user = await UserRepository.find_by_id(session, user_id)
                if not user:
                    raise NotFoundError("User not found")
                
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": user.phone,
                    "bio": user.bio,
                    "profile_picture_url": user.profile_picture_url,
                    "is_active": user.is_active,
                    "is_profile_visible": user.is_profile_visible,
                    "role": user.role,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                }
                
                await redis_client.set(f"user:{user_id}", user_dict, 3600)
            
            # Get stats
            stats = await UserRepository.get_user_stats(session, user_id)
            
            return {
                **user_dict,
                "stats": stats
            }
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Get user profile error: {e}")
            raise

    @staticmethod
    async def update_user_profile(
        session: AsyncSession,
        user_id: str,
        update_data: dict
    ) -> dict:
        """Update user profile"""
        try:
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            user = await UserRepository.update(session, user_id, update_data)
            if not user:
                raise NotFoundError("User not found")
            
            await session.commit()
            
            # Update cache
            user_dict = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "bio": user.bio,
                "profile_picture_url": user.profile_picture_url,
                "is_active": user.is_active,
                "is_profile_visible": user.is_profile_visible,
                "role": user.role,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            
            await redis_client.set(f"user:{user_id}", user_dict, 3600)
            
            logger.info(f"User profile updated: {user_id}")
            
            return user_dict
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Update user profile error: {e}")
            raise

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        try:
            user = await UserRepository.find_by_id(session, user_id)
            if not user:
                raise NotFoundError("User not found")
            
            # Verify current password
            is_valid = await Helpers.compare_password(current_password, user.password)
            if not is_valid:
                raise BadRequestError("Current password is incorrect")
            
            # Update password
            hashed_password = await Helpers.hash_password(new_password)
            await UserRepository.update_password(session, user_id, hashed_password)
            
            # Clear refresh token (force re-login on all devices)
            await UserRepository.clear_refresh_token(session, user_id)
            await session.commit()
            
            logger.info(f"Password changed for user: {user_id}")
            return True
        except (NotFoundError, BadRequestError):
            raise
        except Exception as e:
            logger.error(f"Change password error: {e}")
            raise

    @staticmethod
    async def search_users(
        session: AsyncSession,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        """Search users"""
        try:
            users = await UserRepository.search(session, query, limit, offset)
            
            return [
                {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_picture_url": user.profile_picture_url,
                    "is_profile_visible": user.is_profile_visible
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"Search users error: {e}")
            raise

    @staticmethod
    async def deactivate_user(
        session: AsyncSession,
        user_id: str
    ) -> bool:
        """Deactivate user account"""
        try:
            success = await UserRepository.deactivate(session, user_id)
            if not success:
                raise NotFoundError("User not found")
            
            await session.commit()
            
            # Remove from cache
            await redis_client.delete(f"user:{user_id}")
            
            logger.info(f"User deactivated: {user_id}")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Deactivate user error: {e}")
            raise
