from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.routers import query, compliance, translate, voice, standards, feedback
from app.api import (
    chat as api_chat,
    documents as api_documents,
    flashcards as api_flashcards,
    ocr as api_ocr,
    translation as api_translation,
    health as api_health,
)
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.core.middleware import RequestTracingAndAuthMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup:
      - Initialize IndicTrans2 provider object (lazy mode: model NOT loaded into RAM on boot).

    On shutdown:
      - Clean up resources.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("BIS Backend starting up...")

    # Initialize IndicTrans2 provider object lightweightly (models load lazily on 1st request)
    try:
        from app.providers.translation.indictrans2 import initialize_indictrans2
        initialize_indictrans2()
        logger.info("IndicTrans2 provider registered (Lazy mode active).")
    except Exception as exc:
        logger.warning(
            "IndicTrans2 provider setup failed at startup: %s. "
            "Translation will fall back to passthrough until resolved.",
            exc,
        )

    # Pre-warm the TranslationService singleton
    try:
        from app.providers.translation.base import get_translation_service
        get_translation_service()
        logger.info("TranslationService singleton ready.")
    except Exception as exc:
        logger.warning("TranslationService setup failed: %s", exc)

    yield  # Application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("BIS Backend shutting down.")


app = FastAPI(
    title="BIS Compliance & Intelligence Assistant API",
    description=(
        "Backend AI Assistant with Production RAG, OCR, Compliance Engine, "
        "IndicTrans2 Multilingual Translation & Flashcards"
    ),
    version="2.5.0",
    lifespan=lifespan,
)

# Exception Handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Middleware
app.add_middleware(RequestTracingAndAuthMiddleware)

# Existing Routers (for backwards compatibility)
app.include_router(query.router)
app.include_router(compliance.router)
app.include_router(translate.router)
app.include_router(voice.router)
app.include_router(standards.router)
app.include_router(feedback.router)

# Production Unified API Routers (/api/...)
app.include_router(api_chat.router, prefix="/api")
app.include_router(api_documents.router, prefix="/api")
app.include_router(api_flashcards.router, prefix="/api")
app.include_router(api_ocr.router, prefix="/api")
app.include_router(api_translation.router, prefix="/api")
app.include_router(api_health.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "bis-compliance-backend"}
