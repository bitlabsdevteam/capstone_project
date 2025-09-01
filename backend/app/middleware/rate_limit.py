import time
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import RateLimitException


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory storage."""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, Tuple[int, float]] = {}  # {client_ip: (count, window_start)}
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        current_time = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = (1, current_time)
            return False
        
        count, window_start = self.requests[client_ip]
        
        # Reset window if expired
        if current_time - window_start >= self.window_seconds:
            self.requests[client_ip] = (1, current_time)
            return False
        
        # Check if limit exceeded
        if count >= self.max_requests:
            return True
        
        # Increment counter
        self.requests[client_ip] = (count + 1, window_start)
        return False
    
    def _cleanup_old_entries(self):
        """Clean up expired entries to prevent memory leaks."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, window_start) in self.requests.items()
            if current_time - window_start >= self.window_seconds
        ]
        
        for key in expired_keys:
            del self.requests[key]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                    "timestamp": time.time(),
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Window": str(self.window_seconds),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(self.window_seconds),
                },
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        if client_ip in self.requests:
            count, window_start = self.requests[client_ip]
            remaining = max(0, self.max_requests - count)
            
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Window"] = str(self.window_seconds)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        # Periodic cleanup (every 100 requests)
        if len(self.requests) % 100 == 0:
            self._cleanup_old_entries()
        
        return response