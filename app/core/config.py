import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BIS Compliance Assistant"
    API_V1_STR: str = ""

    API_KEY: str = os.getenv("API_KEY", "demo-key-123")

    BHASHINI_USER_ID: str = os.getenv("BHASHINI_USER_ID", "")
    BHASHINI_API_KEY: str = os.getenv("BHASHINI_API_KEY", "")
    BHASHINI_PIPELINE_ID: str = os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543cd")
    BHASHINI_PIPELINE_URL: str = os.getenv(
        "BHASHINI_PIPELINE_URL",
        "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    )

    class Config:
        case_sensitive = True

settings = Settings()
