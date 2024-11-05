from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    REPOSITORY_PATH: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()