import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from config import settings
import uuid
import math
import os
from typing import Dict, Any, Optional, Tuple
import secrets

class Helpers:
    """Helper functions for password, JWT, distance, and data utilities"""
    
    @staticmethod
    async def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    async def compare_password(password: str, hashed_password: str) -> bool:
        """Compare password with hash"""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    
    @staticmethod
    def generate_tokens(payload: Dict[str, Any]) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        now = datetime.now(timezone.utc)
        
        access_token_payload = {
            **payload,
            "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
            "iat": now,
            "type": "access"
        }
        
        refresh_token_payload = {
            **payload,
            "exp": now + timedelta(days=settings.jwt_refresh_expire_days),
            "iat": now,
            "type": "refresh"
        }
        
        access_token = jwt.encode(
            access_token_payload,
            settings.jwt_secret,
            algorithm="HS256"
        )
        
        refresh_token = jwt.encode(
            refresh_token_payload,
            settings.jwt_refresh_secret,
            algorithm="HS256"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Verify access token"""
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    
    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """Verify refresh token"""
        return jwt.decode(token, settings.jwt_refresh_secret, algorithms=["HS256"])
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in kilometers using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lon / 2) ** 2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate unique filename for uploads"""
        timestamp = datetime.now().timestamp()
        random_str = secrets.token_hex(8)
        extension = original_filename.split('.')[-1] if '.' in original_filename else ''
        return f"{int(timestamp)}-{random_str}.{extension}"
    
    @staticmethod
    def sanitize_user(user: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from user dict"""
        sensitive_fields = ['password', 'refresh_token']
        return {k: v for k, v in user.items() if k not in sensitive_fields}
    
    @staticmethod
    def get_pagination_meta(page: int, limit: int, total: int) -> Dict[str, Any]:
        """Generate pagination metadata"""
        total_pages = (total + limit - 1) // limit  # Ceiling division
        return {
            "current_page": page,
            "total_pages": total_pages,
            "page_size": limit,
            "total_count": total,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
