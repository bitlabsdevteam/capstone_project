"""Configuration management for Vizuara Web3 Application Builder"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os
import secrets
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application Settings
    APP_NAME: str = "Vizuara Web3 Application Builder"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database Settings
    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM Provider Settings
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    
    # LiteLLM Settings
    LITELLM_LOG: str = "INFO"
    LITELLM_DROP_PARAMS: bool = True
    
    # Web3 Settings
    WEB3_PROVIDER_URL: str = "https://mainnet.infura.io/v3/your-project-id"
    ETHEREUM_NETWORK: str = "mainnet"
    
    # Langchain Settings
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # File upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Security settings
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # minutes
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Error handling settings
    DEBUG_MODE: bool = DEBUG
    ENABLE_ERROR_DETAILS: bool = DEBUG
    ERROR_LOG_LEVEL: str = "ERROR"
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_TIMEOUT: int = 30
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if v:
            return v
        return "sqlite:///./vizuara.db"
    
    @validator("UPLOAD_DIR", pre=True)
    def create_upload_dir(cls, v: str) -> str:
        upload_path = Path(v)
        upload_path.mkdir(exist_ok=True)
        return str(upload_path)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()