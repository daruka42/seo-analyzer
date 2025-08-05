import os
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://seouser:seopassword123@postgres:5432/seo_analyzer"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Crawler Settings
    CRAWLER_MAX_WORKERS: int = 10
    CRAWLER_REQUEST_DELAY: float = 1.0
    CRAWLER_TIMEOUT: int = 30
    
    # External APIs (optional)
    AHREFS_API_KEY: Optional[str] = None
    MAJESTIC_API_KEY: Optional[str] = None
    SERP_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://frontend:3000",
        "http://127.0.0.1:3000"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
