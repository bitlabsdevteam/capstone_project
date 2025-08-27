"""Configuration management system for the application"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("config_manager")

class ConfigFormat(Enum):
    """Supported configuration formats"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str
    max_connections: int = 10
    retry_on_timeout: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

@dataclass
class LLMProviderConfig:
    """LLM provider configuration"""
    name: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    enabled: bool = True

@dataclass
class Web3NetworkConfig:
    """Web3 network configuration"""
    name: str
    rpc_url: str
    chain_id: int
    currency_symbol: str
    block_explorer_url: Optional[str] = None
    gas_price_multiplier: float = 1.1
    max_gas_limit: int = 8000000
    enabled: bool = True

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 100
    burst_size: int = 200
    window_size_minutes: int = 1
    enabled: bool = True

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "standard"
    file_rotation_size: str = "10MB"
    file_retention_days: int = 7
    enable_json_logs: bool = False

@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    enable_tracing: bool = False
    jaeger_endpoint: Optional[str] = None

class ConfigManager:
    """Configuration management system"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.settings = get_settings()
        self._configs: Dict[str, Any] = {}
        self._load_default_configs()
    
    def _load_default_configs(self) -> None:
        """Load default configurations"""
        try:
            # Database configuration
            self._configs["database"] = DatabaseConfig(
                url=self.settings.DATABASE_URL,
                pool_size=getattr(self.settings, 'DB_POOL_SIZE', 10),
                echo=self.settings.DEBUG
            )
            
            # Redis configuration
            self._configs["redis"] = RedisConfig(
                url=getattr(self.settings, 'REDIS_URL', 'redis://localhost:6379/0')
            )
            
            # Security configuration
            self._configs["security"] = SecurityConfig(
                secret_key=self.settings.SECRET_KEY,
                access_token_expire_minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            # Rate limiting configuration
            self._configs["rate_limit"] = RateLimitConfig(
                requests_per_minute=self.settings.RATE_LIMIT_REQUESTS,
                window_size_minutes=self.settings.RATE_LIMIT_WINDOW
            )
            
            # Logging configuration
            self._configs["logging"] = LoggingConfig(
                level=self.settings.LOG_LEVEL,
                format=self.settings.LOG_FORMAT
            )
            
            # Monitoring configuration
            self._configs["monitoring"] = MonitoringConfig(
                enable_metrics=self.settings.ENABLE_METRICS,
                metrics_port=self.settings.METRICS_PORT
            )
            
            logger.info("Default configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading default configurations: {e}")
            raise
    
    def load_config(self, name: str, format: ConfigFormat = ConfigFormat.JSON) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        try:
            if format == ConfigFormat.JSON:
                file_path = self.config_dir / f"{name}.json"
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        config = json.load(f)
                        self._configs[name] = config
                        logger.info(f"Loaded {name} configuration from JSON")
                        return config
            
            elif format == ConfigFormat.YAML:
                file_path = self.config_dir / f"{name}.yaml"
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                        self._configs[name] = config
                        logger.info(f"Loaded {name} configuration from YAML")
                        return config
            
            elif format == ConfigFormat.ENV:
                # Load from environment variables with prefix
                prefix = f"{name.upper()}_"
                config = {}
                for key, value in os.environ.items():
                    if key.startswith(prefix):
                        config_key = key[len(prefix):].lower()
                        config[config_key] = value
                
                if config:
                    self._configs[name] = config
                    logger.info(f"Loaded {name} configuration from environment")
                    return config
            
            logger.warning(f"Configuration file for {name} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error loading {name} configuration: {e}")
            return None
    
    def save_config(self, name: str, config: Union[Dict[str, Any], object], 
                   format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Save configuration to file"""
        try:
            # Convert dataclass to dict if needed
            if hasattr(config, '__dataclass_fields__'):
                config_dict = asdict(config)
            else:
                config_dict = config
            
            if format == ConfigFormat.JSON:
                file_path = self.config_dir / f"{name}.json"
                with open(file_path, 'w') as f:
                    json.dump(config_dict, f, indent=2, default=str)
            
            elif format == ConfigFormat.YAML:
                file_path = self.config_dir / f"{name}.yaml"
                with open(file_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            
            self._configs[name] = config_dict
            logger.info(f"Saved {name} configuration to {format.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving {name} configuration: {e}")
            return False
    
    def get_config(self, name: str) -> Optional[Any]:
        """Get configuration by name"""
        return self._configs.get(name)
    
    def update_config(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update existing configuration"""
        try:
            if name in self._configs:
                if isinstance(self._configs[name], dict):
                    self._configs[name].update(updates)
                else:
                    # Handle dataclass updates
                    config_dict = asdict(self._configs[name]) if hasattr(self._configs[name], '__dataclass_fields__') else self._configs[name]
                    config_dict.update(updates)
                    self._configs[name] = config_dict
                
                logger.info(f"Updated {name} configuration")
                return True
            else:
                logger.warning(f"Configuration {name} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating {name} configuration: {e}")
            return False
    
    def add_llm_provider(self, provider_config: LLMProviderConfig) -> bool:
        """Add LLM provider configuration"""
        try:
            if "llm_providers" not in self._configs:
                self._configs["llm_providers"] = {}
            
            self._configs["llm_providers"][provider_config.name] = asdict(provider_config)
            logger.info(f"Added LLM provider configuration: {provider_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding LLM provider configuration: {e}")
            return False
    
    def add_web3_network(self, network_config: Web3NetworkConfig) -> bool:
        """Add Web3 network configuration"""
        try:
            if "web3_networks" not in self._configs:
                self._configs["web3_networks"] = {}
            
            self._configs["web3_networks"][network_config.name] = asdict(network_config)
            logger.info(f"Added Web3 network configuration: {network_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding Web3 network configuration: {e}")
            return False
    
    def get_llm_providers(self) -> Dict[str, LLMProviderConfig]:
        """Get all LLM provider configurations"""
        providers = self._configs.get("llm_providers", {})
        return {name: LLMProviderConfig(**config) for name, config in providers.items()}
    
    def get_web3_networks(self) -> Dict[str, Web3NetworkConfig]:
        """Get all Web3 network configurations"""
        networks = self._configs.get("web3_networks", {})
        return {name: Web3NetworkConfig(**config) for name, config in networks.items()}
    
    def validate_config(self, name: str) -> bool:
        """Validate configuration"""
        try:
            config = self._configs.get(name)
            if not config:
                logger.warning(f"Configuration {name} not found for validation")
                return False
            
            # Basic validation - check required fields exist
            if name == "database":
                required_fields = ["url"]
            elif name == "security":
                required_fields = ["secret_key"]
            elif name == "llm_providers":
                for provider_name, provider_config in config.items():
                    if not all(key in provider_config for key in ["name", "api_key"]):
                        logger.error(f"LLM provider {provider_name} missing required fields")
                        return False
                return True
            else:
                return True  # No specific validation rules
            
            if isinstance(config, dict):
                missing_fields = [field for field in required_fields if field not in config]
                if missing_fields:
                    logger.error(f"Configuration {name} missing required fields: {missing_fields}")
                    return False
            
            logger.info(f"Configuration {name} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating {name} configuration: {e}")
            return False
    
    def export_all_configs(self, format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Export all configurations to files"""
        try:
            for name, config in self._configs.items():
                self.save_config(name, config, format)
            
            logger.info(f"Exported all configurations to {format.value} format")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configurations: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations"""
        return self._configs.copy()
    
    def reload_configs(self) -> bool:
        """Reload all configurations from files"""
        try:
            self._configs.clear()
            self._load_default_configs()
            
            # Try to load from files
            config_files = list(self.config_dir.glob("*.json")) + list(self.config_dir.glob("*.yaml"))
            
            for file_path in config_files:
                name = file_path.stem
                if file_path.suffix == ".json":
                    self.load_config(name, ConfigFormat.JSON)
                elif file_path.suffix == ".yaml":
                    self.load_config(name, ConfigFormat.YAML)
            
            logger.info("Configurations reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading configurations: {e}")
            return False

# Global configuration manager instance
config_manager = ConfigManager()

# Convenience functions
def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    config = config_manager.get_config("database")
    return DatabaseConfig(**config) if isinstance(config, dict) else config

def get_redis_config() -> RedisConfig:
    """Get Redis configuration"""
    config = config_manager.get_config("redis")
    return RedisConfig(**config) if isinstance(config, dict) else config

def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    config = config_manager.get_config("security")
    return SecurityConfig(**config) if isinstance(config, dict) else config

def get_rate_limit_config() -> RateLimitConfig:
    """Get rate limit configuration"""
    config = config_manager.get_config("rate_limit")
    return RateLimitConfig(**config) if isinstance(config, dict) else config