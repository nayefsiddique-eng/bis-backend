from fastapi import FastAPI
from app.routers import query, compliance

app = FastAPI(
    title="BIS Compliance Assistant API",
    description="Backend + Compliance Decision Engine for Bureau of Indian Standards compliance",
    version="1.0.0"
)

app.include_router(query.router)
app.include_router(compliance.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "bis-compliance-backend"}
