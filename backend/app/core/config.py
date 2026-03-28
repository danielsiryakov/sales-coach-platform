from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    xai_api_key: str = ""
    openai_api_key: str = ""

    # Database (SQLite for development, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./sales_coach.db"

    # S3 Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_recordings_bucket: str = "sales-coach-recordings"

    # Local storage fallback
    local_recordings_path: str = "./recordings"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Grok Voice API
    grok_voice_url: str = "wss://api.x.ai/v1/realtime"
    grok_voice_model: str = "grok-2-voice"

    # Analysis
    analysis_model: str = "gpt-4.1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
