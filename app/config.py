"""Configuration management for the solar weather API."""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional
import os


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_key: str = Field(default="", env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(default="", env="SUPABASE_SERVICE_KEY")
    database_url: str = Field(default="", env="DATABASE_URL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class AuthConfig(BaseSettings):
    """Authentication configuration settings."""
    
    jwt_secret: str = Field(default="test-secret", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class ModelConfig(BaseSettings):
    """ML model configuration settings."""
    
    huggingface_token: Optional[str] = Field(None, env="HUGGINGFACE_TOKEN")
    model_name: str = Field(default="surya-1.0", env="MODEL_NAME")
    model_cache_dir: str = Field(default="./model_cache", env="MODEL_CACHE_DIR")
    inference_timeout: int = Field(default=30, env="INFERENCE_TIMEOUT_SECONDS")
    prediction_interval_minutes: int = Field(default=10, env="PREDICTION_INTERVAL_MINUTES")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class ExternalServicesConfig(BaseSettings):
    """External services configuration."""
    
    nasa_api_key: Optional[str] = Field(None, env="NASA_API_KEY")
    nasa_base_url: str = Field(default="https://api.nasa.gov", env="NASA_BASE_URL")
    
    razorpay_key_id: Optional[str] = Field(None, env="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(None, env="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: Optional[str] = Field(None, env="RAZORPAY_WEBHOOK_SECRET")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class APIConfig(BaseSettings):
    """API server configuration."""
    
    app_name: str = Field(default="ZERO-COMP Solar Weather API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    cors_origins: list = Field(
        default=["http://localhost:3000", "https://zero-comp.vercel.app"],
        env="CORS_ORIGINS"
    )
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == 'cors_origins':
                return [x.strip() for x in raw_val.split(',')]
            return cls.json_loads(raw_val)


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    auth: AuthConfig = AuthConfig()
    model: ModelConfig = ModelConfig()
    external: ExternalServicesConfig = ExternalServicesConfig()
    api: APIConfig = APIConfig()
    logging: LoggingConfig = LoggingConfig()
    
    # Subscription tier configurations
    subscription_tiers: Dict[str, Dict[str, Any]] = Field(
        default={
            "free": {
                "rate_limits": {"alerts": 10, "history": 5},
                "features": ["dashboard"],
                "price": 0
            },
            "pro": {
                "rate_limits": {"alerts": 1000, "history": 500, "websocket": True},
                "features": ["dashboard", "api", "websocket"],
                "price": 50
            },
            "enterprise": {
                "rate_limits": {"alerts": 10000, "history": 5000, "websocket": True},
                "features": ["dashboard", "api", "websocket", "csv_export", "sla"],
                "price": 500
            }
        }
    )
    
    # Alert thresholds
    default_alert_thresholds: Dict[str, float] = Field(
        default={
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8
        }
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings