import redis
import json
import logging
from typing import Optional, Any
from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            health_check_interval=30
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get serialized value from Redis by key"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set serialized value in Redis with optional TTL"""
        try:
            ttl = ttl or settings.redis_cache_ttl
            return self.redis.setex(
                key, 
                ttl, 
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove key from Redis"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            return self.redis.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

redis_client = RedisClient()