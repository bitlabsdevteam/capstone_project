"""Comprehensive logging configuration for the application"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on settings"""
    
    # Ensure log directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "app.core.logging.JSONFormatter",
            },
            "colored": {
                "()": "app.core.logging.ColoredFormatter",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "colored" if sys.stdout.isatty() else "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "web3": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }
    
    return config

def setup_logging() -> None:
    """Setup logging configuration"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Get logger and log startup message
    logger = logging.getLogger("app")
    logger.info("Logging system initialized")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log format: {settings.LOG_FORMAT}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"app.{name}")

# Convenience function for request logging
def log_request(method: str, url: str, status_code: int, duration: float, **kwargs) -> None:
    """Log HTTP request details"""
    logger = get_logger("requests")
    logger.info(
        "HTTP request processed",
        extra={
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            **kwargs
        }
    )

# Convenience function for error logging
def log_error(error: Exception, context: str = "", **kwargs) -> None:
    """Log error with context"""
    logger = get_logger("errors")
    logger.error(
        f"Error in {context}: {str(error)}",
        exc_info=True,
        extra={
            "error_type": type(error).__name__,
            "context": context,
            **kwargs
        }
    )

# Convenience function for security logging
def log_security_event(event_type: str, details: str, **kwargs) -> None:
    """Log security-related events"""
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event_type} - {details}",
        extra={
            "event_type": event_type,
            "details": details,
            **kwargs
        }
    )