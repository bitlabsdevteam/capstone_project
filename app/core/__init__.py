"""Core application components"""

from .config import Settings, get_settings
from .logging import setup_logging, get_logger, log_request, log_error, log_security_event
from .security import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token,
    get_current_user,
    require_scopes,
    APIKeyManager,
    RateLimiter,
    validate_input,
    sanitize_input,
    validate_web3_address,
    validate_solidity_code
)
from .exceptions import (
    BaseCustomException,
    LLMException,
    AgentException,
    Web3Exception,
    SecurityException,
    ValidationException,
    ConfigurationException,
    custom_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from .middleware import setup_middleware
from .config_manager import (
    ConfigManager,
    config_manager,
    DatabaseConfig,
    RedisConfig,
    LLMProviderConfig,
    Web3NetworkConfig,
    SecurityConfig,
    RateLimitConfig,
    get_database_config,
    get_redis_config,
    get_security_config,
    get_rate_limit_config
)

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    "ConfigManager",
    "config_manager",
    "DatabaseConfig",
    "RedisConfig",
    "LLMProviderConfig",
    "Web3NetworkConfig",
    "SecurityConfig",
    "RateLimitConfig",
    "get_database_config",
    "get_redis_config",
    "get_security_config",
    "get_rate_limit_config",
    
    # Logging
    "setup_logging",
    "get_logger",
    "log_request",
    "log_error",
    "log_security_event",
    
    # Security
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "require_scopes",
    "APIKeyManager",
    "RateLimiter",
    "validate_input",
    "sanitize_input",
    "validate_web3_address",
    "validate_solidity_code",
    
    # Exceptions
    "BaseCustomException",
    "LLMException",
    "AgentException",
    "Web3Exception",
    "SecurityException",
    "ValidationException",
    "ConfigurationException",
    "custom_exception_handler",
    "http_exception_handler",
    "general_exception_handler",
    
    # Middleware
    "setup_middleware"
]