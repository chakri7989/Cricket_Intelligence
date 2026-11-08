import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Cricket Intelligence System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # AI Credentials
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # External Live Cricket API
    CRICKET_API_KEY: str = ""
    CRICKET_API_BASE_URL: str = "https://api.cricapi.com/v1"
    
    # Storage Paths
    SQLITE_DB_PATH: Path = BASE_DIR / "data" / "sqlite" / "cricket_records.db"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "data" / "chroma"
    CRICSHEET_DATA_DIR: Path = BASE_DIR / "data" / "cricsheet"
    
    # Mock fallback flag when no live match is ongoing or API key is unset
    ENABLE_LIVE_MOCK_FALLBACK: bool = True
    
    class Config:
        env_file = BASE_DIR / ".env"
        extra = "ignore"

settings = Settings()

# Ensure required storage directories exist
settings.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
settings.CRICSHEET_DATA_DIR.mkdir(parents=True, exist_ok=True)

