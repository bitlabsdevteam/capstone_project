"""Middleware for security, logging, and request handling."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from loguru import logger
import json

from .security import rate_limiter, sanitize_input
from .exceptions import RateLimitException, SecurityException

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            # Add request ID and process time to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "process_time": round(process_time, 4),
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            raise e

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app, max_requests: int = 100, window_minutes: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_minutes = window_minutes
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_ip, self.max_requests, self.window_minutes):
            logger.warning(
                f"Rate limit exceeded for client: {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "method": request.method,
                    "max_requests": self.max_requests,
                    "window_minutes": self.window_minutes
                }
            )
            
            raise RateLimitException(
                limit=self.max_requests,
                window=f"{self.window_minutes} minutes",
                retry_after=self.window_minutes * 60
            )
        
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for sanitizing user input."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only sanitize for POST, PUT, PATCH requests with JSON content
        if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
            try:
                # Read request body
                body = await request.body()
                if body:
                    # Parse JSON
                    data = json.loads(body.decode())
                    
                    # Sanitize string values recursively
                    sanitized_data = self._sanitize_data(data)
                    
                    # Replace request body with sanitized data
                    sanitized_body = json.dumps(sanitized_data).encode()
                    
                    # Create new request with sanitized body
                    async def receive():
                        return {"type": "http.request", "body": sanitized_body}
                    
                    request._receive = receive
                    
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If we can't parse the JSON, let it pass through
                # The endpoint will handle the invalid JSON
                pass
            except Exception as e:
                logger.warning(
                    f"Error during input sanitization: {str(e)}",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "error": str(e)
                    }
                )
        
        return await call_next(request)
    
    def _sanitize_data(self, data):
        """Recursively sanitize data structure."""
        if isinstance(data, dict):
            return {key: self._sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return sanitize_input(data)
        else:
            return data

class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with enhanced security."""
    
    def __init__(self, app, allowed_origins: list = None, allowed_methods: list = None, allowed_headers: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.status_code = 200
        else:
            response = await call_next(request)
        
        # Add CORS headers
        if origin and ("*" in self.allowed_origins or origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return response

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request body too large: {content_length} bytes (max: {self.max_size})",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "content_length": content_length,
                    "max_size": self.max_size,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            raise SecurityException(
                message=f"Request body too large. Maximum size is {self.max_size} bytes.",
                error_code="REQUEST_TOO_LARGE",
                status_code=413
            )
        
        return await call_next(request)

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check endpoints."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Add health check information to request state
        if request.url.path in ["/health", "/api/v1/system/health"]:
            request.state.is_health_check = True
            
            # Skip some middleware for health checks
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add health check specific headers
            response.headers["X-Health-Check"] = "true"
            response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))  # in milliseconds
            
            return response
        
        return await call_next(request)

# Middleware configuration helper
def setup_middleware(app, settings):
    """Setup all middleware for the FastAPI application."""
    
    # Add middleware in reverse order (last added is executed first)
    
    # Health check middleware (should be first)
    app.add_middleware(HealthCheckMiddleware)
    
    # Request size limiting
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)
    )
    
    # Input sanitization
    app.add_middleware(InputSanitizationMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting
    app.add_middleware(
        RateLimitingMiddleware,
        max_requests=getattr(settings, 'RATE_LIMIT_REQUESTS', 100),
        window_minutes=getattr(settings, 'RATE_LIMIT_WINDOW', 60)
    )
    
    # Request logging (should be last to capture all request/response data)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("All middleware configured successfully")