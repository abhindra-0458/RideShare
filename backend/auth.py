from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from helpers import Helpers
from database import get_db
from exceptions import JWTError, TokenExpiredError, UnauthorizedError
import jwt
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthToken:
    """Authentication token model"""
    user_id: str
    email: str
    role: str

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        
        # Verify token
        try:
            decoded = Helpers.verify_access_token(token)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token expired")
        except jwt.InvalidTokenError:
            raise JWTError("Invalid token")
        except Exception as e:
            raise JWTError(f"Invalid token: {str(e)}")
        
        user_id = decoded.get("user_id")
        if not user_id:
            raise JWTError("Invalid token payload")
        
        # Verify user still exists and is active
        user = await UserRepository.find_by_id(session, user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        
        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
    except (JWTError, TokenExpiredError, UnauthorizedError):
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise UnauthorizedError("Authentication failed")

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security) if False else None,
    session: AsyncSession = Depends(get_db) if False else None
) -> dict | None:
    """Get optional authenticated user (for public endpoints)"""
    if not credentials:
        return None
    
    try:
        user = await get_current_user(credentials, session)
        return user
    except Exception:
        return None

async def get_current_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current admin user"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_role(allowed_roles: list[str]):
    """Require user to have one of the allowed roles"""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker
