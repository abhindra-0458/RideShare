from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List
import os
from functools import lru_cache

class Settings(BaseSettings):
    # API Configuration
    port: int = int(os.getenv("PORT", 8000))
    environment: str = os.getenv("ENVIRONMENT", "development")
    api_version: str = os.getenv("API_VERSION", "v1")
    api_title: str = "RideShare API"
    api_description: str = "Rideshare backend service with location tracking"
    
    # Database Configuration
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "rideshare_db")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'rideshare_db')}"
    )
    
    # JWT Configuration
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    jwt_refresh_secret: str = os.getenv("JWT_REFRESH_SECRET", "your-refresh-secret-key")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", 15))
    jwt_refresh_expire_days: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", 7))
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Upload Configuration
    upload_path: str = os.getenv("UPLOAD_PATH", "uploads/")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 5242880))  # 5MB
    allowed_file_types: List[str] = ["jpg", "jpeg", "png", "gif"]
    
    # Rate Limiting Configuration
    rate_limit_window_minutes: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", 15))
    rate_limit_max_requests: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 100))
    auth_rate_limit_max_requests: int = 5
    location_rate_limit_max_requests: int = 30
    
    # Location Configuration
    drift_alert_distance_km: float = float(os.getenv("DRIFT_ALERT_DISTANCE_KM", 2.0))
    location_update_interval_ms: int = int(os.getenv("LOCATION_UPDATE_INTERVAL_MS", 30000))
    
    # WebSocket Configuration
    websocket_cors_origin: str = os.getenv("WEBSOCKET_CORS_ORIGIN", "http://localhost:3000")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
