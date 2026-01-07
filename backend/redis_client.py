import redis
import json
import logging
from config import settings
from typing import Any, Optional

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper for caching"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.is_connected = False
    
    async def connect(self) -> redis.Redis:
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self.is_connected = True
            logger.info("Redis Client Connected")
            return self.client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            raise
    
    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """Set key-value pair in Redis"""
        if not self.is_connected:
            logger.warning("Redis not connected, skipping cache set")
            return False
        
        try:
            serialized_value = json.dumps(value)
            if expire_seconds:
                self.client.setex(key, expire_seconds, serialized_value)
            else:
                self.client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.is_connected:
            return None
        
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.is_connected:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_connected:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def increment(
        self,
        key: str,
        expire_seconds: Optional[int] = None
    ) -> int:
        """Increment counter in Redis"""
        if not self.is_connected:
            return 1
        
        try:
            value = self.client.incr(key)
            if expire_seconds and value == 1:
                self.client.expire(key, expire_seconds)
            return value
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 1
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            self.client.close()
            self.is_connected = False

# Global instance
redis_client = RedisClient()
