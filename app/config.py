from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/wallet_db",
    redis_url: str = "redis://localhost:6379/0",
    redis_cache_ttl: int = 300,
    environment: str = "development",
    log_level: str = "INFO",
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()