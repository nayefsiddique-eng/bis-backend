import time
import logging
from typing import Dict, Tuple
from app.core.exceptions import APIException
from app.core.redis import get_redis_manager
from app.core.config import settings

logger = logging.getLogger('rate_limiter')

class RedisRateLimiter:
    def __init__(self, requests_per_window: int = 10, window_seconds: int = 60):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.redis_manager = get_redis_manager()
        self._fallback_store: Dict[str, Tuple[int, float]] = {}
        self._store = self._fallback_store

    def check_rate_limit(self, identifier: str):
        redis_client = self.redis_manager.get_client()
        rate_key = 'rate_limit:' + identifier

        if redis_client:
            try:
                pipeline = redis_client.pipeline()
                pipeline.incr(rate_key)
                pipeline.ttl(rate_key)
                current_count, ttl = pipeline.execute()

                if current_count == 1:
                    redis_client.expire(rate_key, self.window_seconds)
                    ttl = self.window_seconds

                if current_count > self.requests_per_window:
                    logger.warning('RATE_LIMIT_EXCEEDED: Key=' + identifier)
                    retry_after = max(1, ttl if ttl > 0 else self.window_seconds)
                    raise APIException(
                        status_code=429,
                        error_code='RATE_LIMITED',
                        message='Too Many Requests. Rate limit exceeded.',
                        headers={'Retry-After': str(retry_after)}
                    )
                return
            except APIException:
                raise
            except Exception as e:
                logger.warning('REDIS_RATE_LIMIT_FALLBACK: Redis error using in-memory rate limiter. Error: ' + str(e))

        now = time.time()
        if identifier in self._fallback_store:
            count, reset_time = self._fallback_store[identifier]
            if now < reset_time:
                if count >= self.requests_per_window:
                    retry_after = int(reset_time - now) + 1
                    raise APIException(
                        status_code=429,
                        error_code='RATE_LIMITED',
                        message='Rate limit exceeded.',
                        headers={'Retry-After': str(retry_after)}
                    )
                self._fallback_store[identifier] = (count + 1, reset_time)
            else:
                self._fallback_store[identifier] = (1, now + self.window_seconds)
        else:
            self._fallback_store[identifier] = (1, now + self.window_seconds)

rate_limiter = RedisRateLimiter(
    requests_per_window=10,
    window_seconds=60
)
