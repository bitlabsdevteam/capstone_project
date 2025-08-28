#!/usr/bin/env python3
"""
Structured Logging System

Comprehensive logging configuration with JSON and text formatters,
proper handlers, and production-ready logging practices.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from .config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
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
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """Setup application logging configuration."""
    settings = get_settings()
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set root logger level
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    if settings.LOG_FORMAT == "json":
        console_formatter = JSONFormatter()
    else:
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if settings.LOG_FILE:
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers in production
    if settings.ENVIRONMENT == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def log_request(method: str, path: str, status_code: int, duration: float, **kwargs) -> None:
    """Log HTTP request information."""
    logger = get_logger("api.request")
    logger.info(
        "HTTP request processed",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            **kwargs
        }
    )


def log_workflow_event(workflow_id: str, event_type: str, step: Optional[str] = None, **kwargs) -> None:
    """Log workflow execution events."""
    logger = get_logger("workflow.execution")
    logger.info(
        f"Workflow {event_type}",
        extra={
            "workflow_id": workflow_id,
            "event_type": event_type,
            "step": step,
            **kwargs
        }
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """Log error with context information."""
    logger = get_logger("error")
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            **kwargs
        },
        exc_info=True
    )


def log_security_event(event_type: str, details: Dict[str, Any], **kwargs) -> None:
    """Log security-related events."""
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "details": details,
            **kwargs
        }
    )