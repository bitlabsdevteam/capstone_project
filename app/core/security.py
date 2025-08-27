"""Security utilities for authentication, authorization, and data protection."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: list[str] = []

class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str

# Security utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except JWTError:
        raise credentials_exception
    
    return token_data

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    token_data = verify_token(token)
    
    # In a real application, you would fetch the user from a database
    # For now, we'll return a mock user
    user = User(
        username=token_data.username,
        email=f"{token_data.username}@example.com",
        scopes=token_data.scopes
    )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_scopes(*required_scopes: str):
    """Decorator to require specific scopes for endpoint access."""
    def scope_checker(current_user: User = Depends(get_current_active_user)):
        if not all(scope in current_user.scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return scope_checker

# API Key management
class APIKeyManager:
    """Manage API keys for external service access."""
    
    def __init__(self):
        self._api_keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_api_key(self, user_id: str, scopes: list[str] = None) -> str:
        """Generate a new API key."""
        api_key = secrets.token_urlsafe(32)
        self._api_keys[api_key] = {
            "user_id": user_id,
            "scopes": scopes or [],
            "created_at": datetime.utcnow(),
            "last_used": None,
            "active": True
        }
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key."""
        key_data = self._api_keys.get(api_key)
        if key_data and key_data["active"]:
            key_data["last_used"] = datetime.utcnow()
            return key_data
        return None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self._api_keys:
            self._api_keys[api_key]["active"] = False
            return True
        return False

# Rate limiting
class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check if request is allowed based on rate limits."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Clean old requests
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self._requests[identifier]) < max_requests:
            self._requests[identifier].append(now)
            return True
        
        return False

# Input validation and sanitization
def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not isinstance(input_string, str):
        return str(input_string)
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()

def validate_web3_address(address: str) -> bool:
    """Validate Ethereum address format."""
    if not address or not isinstance(address, str):
        return False
    
    # Basic Ethereum address validation
    if len(address) != 42 or not address.startswith('0x'):
        return False
    
    try:
        int(address[2:], 16)  # Check if hex
        return True
    except ValueError:
        return False

def validate_contract_code(code: str) -> Dict[str, Any]:
    """Validate Solidity contract code for basic security issues."""
    issues = []
    warnings = []
    
    if not code or not isinstance(code, str):
        issues.append("Invalid or empty contract code")
        return {"valid": False, "issues": issues, "warnings": warnings}
    
    # Check for common security issues
    dangerous_patterns = [
        ("selfdestruct", "Use of selfdestruct can be dangerous"),
        ("delegatecall", "delegatecall can be risky if not properly validated"),
        ("tx.origin", "Using tx.origin for authorization is vulnerable to phishing"),
        ("block.timestamp", "block.timestamp can be manipulated by miners"),
        ("block.number", "block.number should not be used for critical logic"),
    ]
    
    for pattern, warning in dangerous_patterns:
        if pattern in code.lower():
            warnings.append(warning)
    
    # Check for basic Solidity structure
    if "contract" not in code.lower():
        issues.append("No contract definition found")
    
    if "pragma solidity" not in code.lower():
        warnings.append("No pragma solidity version specified")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }

# Global instances
api_key_manager = APIKeyManager()
rate_limiter = RateLimiter()

# Security middleware dependencies
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify API key from Authorization header."""
    api_key = credentials.credentials
    key_data = api_key_manager.validate_api_key(api_key)
    
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return key_data

async def check_rate_limit(request, identifier: str = None):
    """Check rate limits for requests."""
    if not identifier:
        identifier = request.client.host
    
    if not rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )