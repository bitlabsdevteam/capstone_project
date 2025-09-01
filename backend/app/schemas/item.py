from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator


class ItemBase(BaseModel):
    """Base item schema with common fields."""
    
    name: str
    description: Optional[str] = None
    price: float
    category: str
    sku: Optional[str] = None
    is_active: bool = True
    stock_quantity: int = 0
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        if len(v) > 255:
            raise ValueError('Name must be less than 255 characters')
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        if v > 999999.99:
            raise ValueError('Price cannot exceed 999,999.99')
        return round(v, 2)
    
    @validator('category')
    def validate_category(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Category cannot be empty')
        if len(v) > 100:
            raise ValueError('Category must be less than 100 characters')
        return v.strip().lower()
    
    @validator('stock_quantity')
    def validate_stock_quantity(cls, v):
        if v < 0:
            raise ValueError('Stock quantity cannot be negative')
        return v
    
    @validator('sku')
    def validate_sku(cls, v):
        if v and len(v) > 100:
            raise ValueError('SKU must be less than 100 characters')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove empty tags and limit to 10 tags
            cleaned_tags = [tag.strip() for tag in v if tag.strip()]
            if len(cleaned_tags) > 10:
                raise ValueError('Maximum 10 tags allowed')
            return cleaned_tags
        return v


class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    
    owner_id: int
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Wireless Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "price": 199.99,
                "category": "electronics",
                "sku": "WH-001",
                "stock_quantity": 50,
                "image_url": "https://example.com/headphones.jpg",
                "tags": ["wireless", "audio", "bluetooth"],
                "owner_id": 1
            }
        }


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    is_active: Optional[bool] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 255:
                raise ValueError('Name must be less than 255 characters')
            return v.strip()
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Price cannot be negative')
            if v > 999999.99:
                raise ValueError('Price cannot exceed 999,999.99')
            return round(v, 2)
        return v
    
    @validator('category')
    def validate_category(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Category cannot be empty')
            if len(v) > 100:
                raise ValueError('Category must be less than 100 characters')
            return v.strip().lower()
        return v
    
    @validator('stock_quantity')
    def validate_stock_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Stock quantity cannot be negative')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            cleaned_tags = [tag.strip() for tag in v if tag.strip()]
            if len(cleaned_tags) > 10:
                raise ValueError('Maximum 10 tags allowed')
            return cleaned_tags
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Premium Wireless Headphones",
                "price": 249.99,
                "stock_quantity": 75,
                "tags": ["wireless", "premium", "audio", "bluetooth"]
            }
        }


class ItemResponse(ItemBase):
    """Schema for item response."""
    
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Wireless Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "price": 199.99,
                "category": "electronics",
                "sku": "WH-001",
                "is_active": True,
                "stock_quantity": 50,
                "image_url": "https://example.com/headphones.jpg",
                "tags": ["wireless", "audio", "bluetooth"],
                "owner_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ItemListResponse(BaseModel):
    """Schema for paginated item list response."""
    
    items: List[ItemResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "Wireless Headphones",
                        "description": "High-quality wireless headphones",
                        "price": 199.99,
                        "category": "electronics",
                        "is_active": True,
                        "stock_quantity": 50,
                        "owner_id": 1,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 100,
                "skip": 0,
                "limit": 10
            }
        }