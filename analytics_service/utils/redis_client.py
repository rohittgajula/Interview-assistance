"""
Redis client for caching AI responses and temporary data
"""
import redis
import json
from typing import Any, Optional
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper for caching operations"""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        self.default_ttl = settings.redis_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    def cache_question(self, session_id: str, question_number: int, question_data: dict) -> bool:
        """Cache generated question"""
        key = f"question:{session_id}:{question_number}"
        return self.set(key, question_data, ttl=7200)  # 2 hours

    def get_cached_question(self, session_id: str, question_number: int) -> Optional[dict]:
        """Get cached question"""
        key = f"question:{session_id}:{question_number}"
        return self.get(key)

    def cache_feedback(self, question_id: str, feedback_data: dict) -> bool:
        """Cache generated feedback"""
        key = f"feedback:{question_id}"
        return self.set(key, feedback_data, ttl=7200)  # 2 hours

    def get_cached_feedback(self, question_id: str) -> Optional[dict]:
        """Get cached feedback"""
        key = f"feedback:{question_id}"
        return self.get(key)

    def cache_report(self, session_id: str, report_data: dict) -> bool:
        """Cache generated report"""
        key = f"report:{session_id}"
        return self.set(key, report_data, ttl=86400)  # 24 hours

    def get_cached_report(self, session_id: str) -> Optional[dict]:
        """Get cached report"""
        key = f"report:{session_id}"
        return self.get(key)

    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()
