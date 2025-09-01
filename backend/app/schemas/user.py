from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v) > 20:
            raise ValueError('Phone number must be less than 20 characters')
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 100:
            raise ValueError('Password must be less than 100 characters')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "password": "securepassword123",
                "bio": "Software developer passionate about technology",
                "phone": "+1234567890",
                "location": "San Francisco, CA",
                "website": "https://johndoe.dev"
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username must be less than 50 characters')
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "bio": "Senior software developer with 10+ years experience",
                "location": "New York, NY",
                "website": "https://johnsmith.dev"
            }
        }


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "avatar_url": "https://example.com/avatar.jpg",
                "bio": "Software developer passionate about technology",
                "phone": "+1234567890",
                "location": "San Francisco, CA",
                "website": "https://johndoe.dev",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T12:00:00Z"
            }
        }


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    
    users: List[UserResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 1,
                        "email": "user1@example.com",
                        "username": "user1",
                        "full_name": "User One",
                        "is_active": True,
                        "is_superuser": False,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 50,
                "skip": 0,
                "limit": 10
            }
        }