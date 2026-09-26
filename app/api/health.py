from fastapi import APIRouter
from app.core.redis import get_redis_manager
from app.core.config import settings

router = APIRouter(tags=['Health & Readiness'])


@router.get('/health')
async def health():
    return {
        'status': 'ok',
        'service': 'bis-compliance-backend',
        'version': '2.5.0'
    }


@router.get('/ready')
async def readiness():
    redis_mgr = get_redis_manager()
    redis_connected = redis_mgr.is_connected()
    redis_status = 'connected' if redis_connected else 'fallback_in_memory'

    bhashini_configured = bool(settings.BHASHINI_USER_ID and settings.BHASHINI_API_KEY)

    # IndicTrans2 model status
    try:
        from app.providers.translation.indictrans2 import _get_indictrans2_singleton
        it2 = _get_indictrans2_singleton()
        indictrans2_status = it2.status if it2 is not None else "uninitialized"
        indictrans2_loaded = it2.is_loaded if it2 is not None else False
        translation_device = it2.device if it2 is not None else "not_initialized"
        indictrans2_error = it2.load_error if it2 is not None else None
    except Exception:
        indictrans2_status = "error"
        indictrans2_loaded = False
        translation_device = "unknown"
        indictrans2_error = None

    response = {
        'status': 'ready',
        'database': 'connected',
        'vector_store': 'connected',
        'redis': redis_status,
        'translation_provider': settings.TRANSLATION_PROVIDER,
        'indictrans2_status': indictrans2_status,
        'indictrans2_model_loaded': indictrans2_loaded,
        'translation_device': translation_device,
        'bhashini_configured': bhashini_configured,
    }

    if indictrans2_error:
        response['indictrans2_load_error'] = indictrans2_error

    return response
