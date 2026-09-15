from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.routers import query, compliance, translate, voice, standards, feedback
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.core.middleware import RequestTracingAndAuthMiddleware

app = FastAPI(
    title="BIS Compliance Assistant API - Hardened & Production Ready",
    description="Backend + Compliance Decision Engine with Bhashini Multilingual, Rate Limiting, Caching, & Tracing",
    version="2.1.0"
)

# Exception Handlers (Step 1)
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Tracing, Auth & Rate Limiting Middleware (Steps 2, 4, 10)
app.add_middleware(RequestTracingAndAuthMiddleware)

# Routers
app.include_router(query.router)
app.include_router(compliance.router)
app.include_router(translate.router)
app.include_router(voice.router)
app.include_router(standards.router)
app.include_router(feedback.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "bis-compliance-backend"}
