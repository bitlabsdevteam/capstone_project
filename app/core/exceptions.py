"""Custom exceptions and error handling for the multi-agent Web3 application builder."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
import traceback

# Base custom exceptions
class BaseCustomException(Exception):
    """Base exception class for custom exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

# LLM-related exceptions
class LLMException(BaseCustomException):
    """Base exception for LLM-related errors."""
    pass

class LLMProviderException(LLMException):
    """Exception for LLM provider errors."""
    
    def __init__(self, provider: str, message: str, **kwargs):
        super().__init__(
            message=f"LLM Provider '{provider}' error: {message}",
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider, **kwargs},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class LLMModelNotFoundException(LLMException):
    """Exception for when an LLM model is not found."""
    
    def __init__(self, model: str, provider: str = None, **kwargs):
        super().__init__(
            message=f"Model '{model}' not found" + (f" for provider '{provider}'" if provider else ""),
            error_code="LLM_MODEL_NOT_FOUND",
            details={"model": model, "provider": provider, **kwargs},
            status_code=status.HTTP_404_NOT_FOUND
        )

class LLMRateLimitException(LLMException):
    """Exception for LLM rate limit errors."""
    
    def __init__(self, provider: str, retry_after: int = None, **kwargs):
        super().__init__(
            message=f"Rate limit exceeded for provider '{provider}'",
            error_code="LLM_RATE_LIMIT_EXCEEDED",
            details={"provider": provider, "retry_after": retry_after, **kwargs},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class LLMTokenLimitException(LLMException):
    """Exception for token limit errors."""
    
    def __init__(self, model: str, token_count: int, max_tokens: int, **kwargs):
        super().__init__(
            message=f"Token limit exceeded for model '{model}': {token_count}/{max_tokens}",
            error_code="LLM_TOKEN_LIMIT_EXCEEDED",
            details={"model": model, "token_count": token_count, "max_tokens": max_tokens, **kwargs},
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

# Agent-related exceptions
class AgentException(BaseCustomException):
    """Base exception for agent-related errors."""
    pass

class AgentNotFoundException(AgentException):
    """Exception for when an agent is not found."""
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(
            message=f"Agent '{agent_id}' not found",
            error_code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id, **kwargs},
            status_code=status.HTTP_404_NOT_FOUND
        )

class AgentExecutionException(AgentException):
    """Exception for agent execution errors."""
    
    def __init__(self, agent_id: str, task_type: str, error_details: str, **kwargs):
        super().__init__(
            message=f"Agent '{agent_id}' failed to execute task '{task_type}': {error_details}",
            error_code="AGENT_EXECUTION_ERROR",
            details={"agent_id": agent_id, "task_type": task_type, "error_details": error_details, **kwargs},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class WorkflowException(AgentException):
    """Exception for workflow-related errors."""
    
    def __init__(self, workflow_id: str, message: str, **kwargs):
        super().__init__(
            message=f"Workflow '{workflow_id}' error: {message}",
            error_code="WORKFLOW_ERROR",
            details={"workflow_id": workflow_id, **kwargs},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Web3-related exceptions
class Web3Exception(BaseCustomException):
    """Base exception for Web3-related errors."""
    pass

class Web3ConnectionException(Web3Exception):
    """Exception for Web3 connection errors."""
    
    def __init__(self, network: str, provider_url: str, **kwargs):
        super().__init__(
            message=f"Failed to connect to {network} network at {provider_url}",
            error_code="WEB3_CONNECTION_ERROR",
            details={"network": network, "provider_url": provider_url, **kwargs},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class ContractCompilationException(Web3Exception):
    """Exception for smart contract compilation errors."""
    
    def __init__(self, contract_name: str, compilation_errors: list, **kwargs):
        super().__init__(
            message=f"Failed to compile contract '{contract_name}'",
            error_code="CONTRACT_COMPILATION_ERROR",
            details={"contract_name": contract_name, "compilation_errors": compilation_errors, **kwargs},
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ContractDeploymentException(Web3Exception):
    """Exception for smart contract deployment errors."""
    
    def __init__(self, contract_name: str, network: str, error_details: str, **kwargs):
        super().__init__(
            message=f"Failed to deploy contract '{contract_name}' to {network}: {error_details}",
            error_code="CONTRACT_DEPLOYMENT_ERROR",
            details={"contract_name": contract_name, "network": network, "error_details": error_details, **kwargs},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class InsufficientFundsException(Web3Exception):
    """Exception for insufficient funds errors."""
    
    def __init__(self, required_amount: str, available_amount: str, **kwargs):
        super().__init__(
            message=f"Insufficient funds: required {required_amount}, available {available_amount}",
            error_code="INSUFFICIENT_FUNDS",
            details={"required_amount": required_amount, "available_amount": available_amount, **kwargs},
            status_code=status.HTTP_402_PAYMENT_REQUIRED
        )

class InvalidContractAddressException(Web3Exception):
    """Exception for invalid contract address errors."""
    
    def __init__(self, address: str, **kwargs):
        super().__init__(
            message=f"Invalid contract address: {address}",
            error_code="INVALID_CONTRACT_ADDRESS",
            details={"address": address, **kwargs},
            status_code=status.HTTP_400_BAD_REQUEST
        )

# Security-related exceptions
class SecurityException(BaseCustomException):
    """Base exception for security-related errors."""
    pass

class AuthenticationException(SecurityException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=kwargs,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationException(SecurityException):
    """Exception for authorization errors."""
    
    def __init__(self, required_scopes: list = None, **kwargs):
        super().__init__(
            message="Insufficient permissions",
            error_code="AUTHORIZATION_ERROR",
            details={"required_scopes": required_scopes, **kwargs},
            status_code=status.HTTP_403_FORBIDDEN
        )

class RateLimitException(SecurityException):
    """Exception for rate limit errors."""
    
    def __init__(self, limit: int, window: str, retry_after: int = None, **kwargs):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window, "retry_after": retry_after, **kwargs},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

# Validation exceptions
class ValidationException(BaseCustomException):
    """Exception for validation errors."""
    
    def __init__(self, field: str, value: Any, message: str, **kwargs):
        super().__init__(
            message=f"Validation error for field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value), "validation_message": message, **kwargs},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

# Configuration exceptions
class ConfigurationException(BaseCustomException):
    """Exception for configuration errors."""
    
    def __init__(self, config_key: str, message: str, **kwargs):
        super().__init__(
            message=f"Configuration error for '{config_key}': {message}",
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, **kwargs},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Error handlers
async def custom_exception_handler(request: Request, exc: BaseCustomException) -> JSONResponse:
    """Handle custom exceptions."""
    logger.error(
        f"Custom exception occurred: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": logger.bind().opt().record["time"].isoformat() if hasattr(logger.bind().opt(), 'record') else None
            }
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    error_id = logger.bind().opt().record.get("extra", {}).get("request_id", "unknown") if hasattr(logger.bind().opt(), 'record') else "unknown"
    
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "error_id": error_id,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {
                    "error_id": error_id
                }
            }
        }
    )

# Validation helpers
def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present in data."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationException(
            field="multiple",
            value=missing_fields,
            message=f"Missing required fields: {', '.join(missing_fields)}"
        )

def validate_field_type(field_name: str, value: Any, expected_type: type) -> None:
    """Validate that a field has the expected type."""
    if not isinstance(value, expected_type):
        raise ValidationException(
            field=field_name,
            value=value,
            message=f"Expected type {expected_type.__name__}, got {type(value).__name__}"
        )

def validate_field_length(field_name: str, value: str, min_length: int = None, max_length: int = None) -> None:
    """Validate string field length."""
    if min_length is not None and len(value) < min_length:
        raise ValidationException(
            field=field_name,
            value=value,
            message=f"Minimum length is {min_length}, got {len(value)}"
        )
    
    if max_length is not None and len(value) > max_length:
        raise ValidationException(
            field=field_name,
            value=value,
            message=f"Maximum length is {max_length}, got {len(value)}"
        )

def validate_enum_value(field_name: str, value: Any, enum_class) -> None:
    """Validate that a value is a valid enum member."""
    try:
        enum_class(value)
    except ValueError:
        valid_values = [e.value for e in enum_class]
        raise ValidationException(
            field=field_name,
            value=value,
            message=f"Invalid value. Valid options are: {', '.join(valid_values)}"
        )