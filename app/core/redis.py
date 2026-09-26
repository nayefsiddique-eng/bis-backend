import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger('redis_connection')

class RedisManager:
    def __init__(self):
        self._client = None
        self._in_memory_fallback = {}
        self._is_connected = False
        self._init_connection()

    def _init_connection(self):
        try:
            import redis
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self._client.ping()
            self._is_connected = True
            logger.info('REDIS_CONNECTED: Successfully established Redis connection pool.')
        except Exception as e:
            self._is_connected = False
            self._client = None
            logger.warning('REDIS_DISCONNECTED: Redis unreachable. Using graceful in-memory cache fallback. Error: ' + str(e))

    def is_connected(self) -> bool:
        if not self._is_connected or not self._client:
            return False
        try:
            return self._client.ping()
        except Exception:
            self._is_connected = False
            return False

    def get_client(self):
        if self.is_connected():
            return self._client
        return None

_redis_manager = None

def get_redis_manager() -> RedisManager:
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager
