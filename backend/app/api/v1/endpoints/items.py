from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse

router = APIRouter()

# Mock data for demonstration
mock_items = [
    {
        "id": 1,
        "name": "Laptop Computer",
        "description": "High-performance laptop for work and gaming",
        "price": 999.99,
        "category": "Electronics",
        "sku": "LAP001",
        "stock_quantity": 50,
        "is_active": True,
        "images": ["laptop1.jpg", "laptop2.jpg"],
        "tags": ["laptop", "computer", "electronics"],
        "owner_id": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with long battery life",
        "price": 29.99,
        "category": "Electronics",
        "sku": "MOU001",
        "stock_quantity": 100,
        "is_active": True,
        "images": ["mouse1.jpg"],
        "tags": ["mouse", "wireless", "accessories"],
        "owner_id": 1,
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z"
    },
    {
        "id": 3,
        "name": "Office Chair",
        "description": "Comfortable ergonomic office chair",
        "price": 199.99,
        "category": "Furniture",
        "sku": "CHR001",
        "stock_quantity": 25,
        "is_active": False,
        "images": ["chair1.jpg", "chair2.jpg"],
        "tags": ["chair", "office", "furniture"],
        "owner_id": 2,
        "created_at": "2024-01-03T00:00:00Z",
        "updated_at": "2024-01-03T00:00:00Z"
    }
]


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(item_data: ItemCreate):
    """Create a new item (mock implementation)."""
    # Check if item with same SKU exists
    for item in mock_items:
        if item["sku"] == item_data.sku:
            raise HTTPException(status_code=409, detail="Item with this SKU already exists")
    
    # Create new item
    new_item = {
        "id": len(mock_items) + 1,
        "name": item_data.name,
        "description": item_data.description,
        "price": item_data.price,
        "category": item_data.category,
        "sku": item_data.sku,
        "stock_quantity": item_data.stock_quantity,
        "is_active": True,
        "images": item_data.images or [],
        "tags": item_data.tags or [],
        "owner_id": item_data.owner_id,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    mock_items.append(new_item)
    return ItemResponse(**new_item)


@router.get("/", response_model=ItemListResponse)
async def get_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search term for name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get list of items with pagination and filtering (mock implementation)."""
    filtered_items = mock_items
    
    # Apply filters
    if is_active is not None:
        filtered_items = [item for item in filtered_items if item["is_active"] == is_active]
    
    if category:
        filtered_items = [item for item in filtered_items if item["category"].lower() == category.lower()]
    
    if min_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] >= min_price]
    
    if max_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] <= max_price]
    
    if search:
        filtered_items = [
            item for item in filtered_items
            if search.lower() in item["name"].lower() or search.lower() in item["description"].lower()
        ]
    
    # Apply pagination
    paginated_items = filtered_items[skip:skip + limit]
    
    return ItemListResponse(
        items=[ItemResponse(**item) for item in paginated_items],
        total=len(filtered_items),
        skip=skip,
        limit=limit
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get item by ID (mock implementation)."""
    for item in mock_items:
        if item["id"] == item_id:
            return ItemResponse(**item)
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item_data: ItemUpdate):
    """Update item by ID (mock implementation)."""
    for i, item in enumerate(mock_items):
        if item["id"] == item_id:
            # Check SKU uniqueness if SKU is being updated
            if item_data.sku and item_data.sku != item["sku"]:
                for other_item in mock_items:
                    if other_item["sku"] == item_data.sku and other_item["id"] != item_id:
                        raise HTTPException(status_code=409, detail="Item with this SKU already exists")
            
            # Update item data
            update_data = item_data.dict(exclude_unset=True)
            mock_items[i].update(update_data)
            mock_items[i]["updated_at"] = "2024-01-01T00:00:00Z"
            return ItemResponse(**mock_items[i])
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int):
    """Delete item by ID (mock implementation)."""
    for i, item in enumerate(mock_items):
        if item["id"] == item_id:
            del mock_items[i]
            return
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.get("/categories/", response_model=List[str])
async def get_categories():
    """Get list of available item categories (mock implementation)."""
    categories = list(set(item["category"] for item in mock_items))
    return sorted(categories)


@router.patch("/{item_id}/toggle-active", response_model=ItemResponse)
async def toggle_item_active(item_id: int):
    """Toggle item active status (mock implementation)."""
    for i, item in enumerate(mock_items):
        if item["id"] == item_id:
            mock_items[i]["is_active"] = not mock_items[i]["is_active"]
            mock_items[i]["updated_at"] = "2024-01-01T00:00:00Z"
            return ItemResponse(**mock_items[i])
    
    raise HTTPException(status_code=404, detail="Item not found")