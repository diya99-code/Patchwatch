from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Database Configuration
    database_url: str = Field(default="postgresql://patchwatch:password@localhost:5432/patchwatch")
    test_database_url: str = Field(default="postgresql://patchwatch:password@localhost:5432/patchwatch_test")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # Security Configuration
    secret_key: str = Field(default="development-secret-key-change-in-production")
    access_token_expire_minutes: int = Field(default=30)
    password_min_length: int = Field(default=8)
    
    # Application Configuration
    debug: bool = Field(default=True)
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    
    # External API Configuration
    osv_api_url: str = Field(default="https://api.osv.dev/v1/query")
    npm_registry_url: str = Field(default="https://registry.npmjs.org")
    pypi_api_url: str = Field(default="https://pypi.org/pypi")
    
    # File Upload Configuration
    max_upload_size: int = Field(default=10485760)  # 10MB
    allowed_file_extensions: List[str] = Field(default=[".json", ".txt", ".lock", ".toml"])
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")
    
    # Request Configuration
    request_timeout: int = Field(default=30)
    max_concurrent_requests: int = Field(default=10)


settings = Settings()