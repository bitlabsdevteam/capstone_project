#!/usr/bin/env python3
"""
Exception Handling System

Comprehensive exception handling with custom exceptions,
error responses, and proper HTTP status codes.
"""

import traceback
from typing import Any, Dict, Optional, Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from .logging import get_logger, log_error

logger = get_logger(__name__)


class BaseAPIException(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class WorkflowException(BaseAPIException):
    """Exception for workflow-related errors."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        workflow_details = details or {}
        if workflow_id:
            workflow_details["workflow_id"] = workflow_id
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="WORKFLOW_ERROR",
            details=workflow_details
        )


# Alias for backward compatibility
WorkflowError = WorkflowException


class WorkflowNotFoundException(BaseAPIException):
    """Exception for workflow not found errors."""
    
    def __init__(self, workflow_id: str):
        super().__init__(
            message=f"Workflow with ID '{workflow_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="WORKFLOW_NOT_FOUND",
            details={"workflow_id": workflow_id}
        )


class WorkflowTimeoutException(BaseAPIException):
    """Exception for workflow timeout errors."""
    
    def __init__(self, workflow_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Workflow '{workflow_id}' timed out after {timeout_seconds} seconds",
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            error_code="WORKFLOW_TIMEOUT",
            details={"workflow_id": workflow_id, "timeout_seconds": timeout_seconds}
        )


class ConfigurationException(BaseAPIException):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class RateLimitException(BaseAPIException):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


def create_error_response(
    message: str,
    status_code: int,
    error_code: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response."""
    error_response = {
        "error": {
            "message": message,
            "code": error_code,
            "status_code": status_code,
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["request_id"] = request_id
    
    return error_response


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handle custom API exceptions."""
    request_id = getattr(request.state, "request_id", None)
    
    log_error(
        exc,
        context={
            "request_id": request_id,
            "path": str(request.url),
            "method": request.method,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            details=exc.details,
            request_id=request_id
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "path": str(request.url),
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.detail,
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            request_id=request_id
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    request_id = getattr(request.state, "request_id", None)
    
    # Format validation errors
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Request validation failed",
        extra={
            "request_id": request_id,
            "path": str(request.url),
            "method": request.method,
            "validation_errors": validation_errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"validation_errors": validation_errors},
            request_id=request_id
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", None)
    
    log_error(
        exc,
        context={
            "request_id": request_id,
            "path": str(request.url),
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            request_id=request_id
        )
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the FastAPI application."""
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)