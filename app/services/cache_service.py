import json
import logging
from typing import Any, Optional
from app.core.redis import get_redis_manager
from app.core.config import settings

logger = logging.getLogger('cache_service')

class CacheService:
    def __init__(self):
        self.redis_manager = get_redis_manager()
        self._fallback_store = {}

    def _get_key(self, key: str) -> str:
        return key

    def get_cache(self, key: str) -> Optional[Any]:
        client = self.redis_manager.get_client()
        if client:
            try:
                val = client.get(key)
                if val is not None:
                    logger.info('CACHE_HIT: Key=' + key)
                    return json.loads(val)
                logger.info('CACHE_MISS: Key=' + key)
                return None
            except Exception as e:
                logger.warning('CACHE_ERROR: Failed GET for key=' + key + '. Fallback. Error: ' + str(e))
        
        # In-memory fallback check
        if key in self._fallback_store:
            logger.info('CACHE_HIT_FALLBACK: Key=' + key)
            return self._fallback_store[key]
        logger.info('CACHE_MISS: Key=' + key)
        return None

    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if ttl is None:
            ttl = settings.RAG_CACHE_TTL

        serialized = json.dumps(value)
        client = self.redis_manager.get_client()
        if client:
            try:
                client.set(key, serialized, ex=ttl)
                logger.info('CACHE_SET: Key=' + key + ' TTL=' + str(ttl))
                return True
            except Exception as e:
                logger.warning('CACHE_ERROR: Failed SET for key=' + key + '. Fallback. Error: ' + str(e))

        # Fallback in-memory
        self._fallback_store[key] = value
        logger.info('CACHE_SET_FALLBACK: Key=' + key)
        return True

    def delete_cache(self, key: str) -> bool:
        client = self.redis_manager.get_client()
        if client:
            try:
                client.delete(key)
                logger.info('CACHE_INVALIDATED: Key=' + key)
            except Exception as e:
                logger.warning('CACHE_ERROR: Failed DELETE for key=' + key + '. Error: ' + str(e))

        if key in self._fallback_store:
            del self._fallback_store[key]
        return True

    def invalidate_document_cache(self, document_id: str):
        self.delete_cache('document:' + document_id)
        self.delete_cache('document_status:' + document_id)
        logger.info('DOCUMENT_CACHE_INVALIDATED: document_id=' + document_id)

_cache_service = None

def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
