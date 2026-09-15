from fastapi import FastAPI
from app.routers import query, compliance, translate, voice

app = FastAPI(
    title="BIS Compliance Assistant API",
    description="Backend + Compliance Decision Engine with Bhashini Multilingual & Voice Integration",
    version="2.0.0"
)

app.include_router(query.router)
app.include_router(compliance.router)
app.include_router(translate.router)
app.include_router(voice.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "bis-compliance-backend"}
