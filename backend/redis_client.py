import redis
import json
from config import REDIS
from logger import logger, error as log_error

class RedisClient:
    def __init__(self):
        self.client = None
        self.is_connected = False

    async def connect(self):
        try:
            self.client = redis.from_url(
                REDIS['url'],
                password=REDIS['password'],
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info('Redis Client Connected')
            self.is_connected = True
            return self.client
        except Exception as error:
            log_error(f'Failed to connect to Redis: {str(error)}')
            raise

    async def set(self, key, value, expire_in_seconds=None):
        if not self.is_connected:
            logger.warning('Redis not connected, skipping cache set')
            return False

        try:
            serialized_value = json.dumps(value)
            if expire_in_seconds:
                self.client.setex(key, expire_in_seconds, serialized_value)
            else:
                self.client.set(key, serialized_value)
            return True
        except Exception as error:
            log_error(f'Redis SET error: {str(error)}')
            return False

    async def get(self, key):
        if not self.is_connected:
            return None

        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as error:
            log_error(f'Redis GET error: {str(error)}')
            return None

    async def delete(self, key):
        if not self.is_connected:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as error:
            log_error(f'Redis DEL error: {str(error)}')
            return False

    async def exists(self, key):
        if not self.is_connected:
            return False

        try:
            return self.client.exists(key) == 1
        except Exception as error:
            log_error(f'Redis EXISTS error: {str(error)}')
            return False

    async def incr(self, key, expire_in_seconds=None):
        if not self.is_connected:
            return 1

        try:
            value = self.client.incr(key)
            if expire_in_seconds and value == 1:
                self.client.expire(key, expire_in_seconds)
            return value
        except Exception as error:
            log_error(f'Redis INCR error: {str(error)}')
            return 1

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.is_connected = False

# Singleton instance
redis_client = RedisClient()
