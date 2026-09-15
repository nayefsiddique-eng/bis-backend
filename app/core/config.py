from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BIS Compliance Assistant"
    API_V1_STR: str = ""

    class Config:
        case_sensitive = True

settings = Settings()
