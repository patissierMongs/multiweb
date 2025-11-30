"""
Redis connection and caching utilities.
"""
import json
from typing import Optional, Any
from redis import asyncio as aioredis
from app.core.config import settings


class RedisClient:
    """Async Redis client wrapper with caching utilities."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        self.redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            True if successful
        """
        if not self.redis:
            return False

        if not isinstance(value, str):
            value = json.dumps(value)

        await self.redis.set(key, value, ex=expire)
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        await self.redis.delete(key)
        return True

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis:
            return False
        return await self.redis.exists(key) > 0

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        if not self.redis:
            return 0
        return await self.redis.incrby(key, amount)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if not self.redis:
            return False
        return await self.redis.expire(key, seconds)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency for getting Redis client."""
    return redis_client
