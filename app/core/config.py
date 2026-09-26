import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "BIS Compliance & Intelligence Assistant"
    API_V1_STR: str = "/api"

    API_KEY: str = os.getenv("API_KEY", "demo-key-123")

    # Storage & Redis Config
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./bis_assistant.db")
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "./chroma_db")

    # Cache TTL Policies (in seconds)
    RAG_CACHE_TTL: int = int(os.getenv("RAG_CACHE_TTL", "3600"))        # 1 Hour
    DOCUMENT_CACHE_TTL: int = int(os.getenv("DOCUMENT_CACHE_TTL", "1800")) # 30 Minutes

    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # OCR & Translation Provider Selection
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "local")  # local, tesseract, paddle, mock
    TRANSLATION_PROVIDER: str = os.getenv("TRANSLATION_PROVIDER", "indictrans2")  # indictrans2, bhashini, auto

    # Bhashini Configuration (API approval pending — preserved for future activation)
    BHASHINI_USER_ID: str = os.getenv("BHASHINI_USER_ID", "")
    BHASHINI_API_KEY: str = os.getenv("BHASHINI_API_KEY", "")
    BHASHINI_PIPELINE_ID: str = os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543cd")
    BHASHINI_PIPELINE_URL: str = os.getenv(
        "BHASHINI_PIPELINE_URL",
        "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    )
    SECONDARY_TRANSLATION_API_KEY: str = os.getenv("SECONDARY_TRANSLATION_API_KEY", "")

    # AI4Bharat IndicTrans2 Configuration (active provider)
    # Device: "auto" = detect CUDA automatically, "cuda" = force GPU, "cpu" = force CPU
    INDICTRANS2_DEVICE: str = os.getenv("INDICTRANS2_DEVICE", "auto")
    # Batch size for inference (reduce if running on low-memory CPU)
    INDICTRANS2_BATCH_SIZE: int = int(os.getenv("INDICTRANS2_BATCH_SIZE", "1"))

    # Safety & Security Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT", "60"))

settings = Settings()


