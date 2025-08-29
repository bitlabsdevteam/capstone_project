#!/usr/bin/env python3
"""
Configuration Management

Centralized configuration management for different environments
with proper validation and type safety.
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    # Application
    PROJECT_NAME: str = "FastAPI LangGraph Application"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Production-ready FastAPI application with LangGraph workflow management"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: Optional[str] = None
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse ALLOWED_ORIGINS from environment variable."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # LangGraph
    LANGGRAPH_CONFIG_PATH: Optional[str] = None
    WORKFLOW_TIMEOUT: int = 300  # 5 minutes
    MAX_WORKFLOW_STEPS: int = 100
    
    # Database (for future use)
    DATABASE_URL: Optional[str] = None
    
    # Redis (for caching and state management)
    REDIS_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level setting."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()
    
    @validator("LOG_FORMAT")
    def validate_log_format(cls, v):
        """Validate log format setting."""
        allowed = ["json", "text"]
        if v not in allowed:
            raise ValueError(f"Log format must be one of {allowed}")
        return v
    
    @validator("DEBUG", pre=True)
    def validate_debug(cls, v, values):
        """Set debug mode based on environment."""
        if isinstance(v, str):
            v = v.lower() in ("true", "1", "yes", "on")
        
        # Auto-enable debug in development
        if values.get("ENVIRONMENT") == "development":
            return True
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def get_environment_info() -> dict:
    """Get current environment information."""
    settings = get_settings()
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": settings.VERSION,
        "host": settings.HOST,
        "port": settings.PORT,
    }