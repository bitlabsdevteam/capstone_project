from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate
from app.core.exceptions import DatabaseException


class ItemService:
    """Service layer for item operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, item_data: ItemCreate) -> Item:
        """Create a new item."""
        try:
            # Convert tags list to comma-separated string
            tags_str = None
            if item_data.tags:
                tags_str = ", ".join(item_data.tags)
            
            # Create item instance
            db_item = Item(
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                category=item_data.category,
                sku=item_data.sku,
                is_active=item_data.is_active,
                stock_quantity=item_data.stock_quantity,
                image_url=item_data.image_url,
                tags=tags_str,
                owner_id=item_data.owner_id,
            )
            
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)
            
            return db_item
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to create item: {str(e)}")
    
    async def get(self, item_id: int) -> Optional[Item]:
        """Get item by ID."""
        return self.db.query(Item).filter(Item.id == item_id).first()
    
    async def get_by_sku(self, sku: str) -> Optional[Item]:
        """Get item by SKU."""
        return self.db.query(Item).filter(Item.sku == sku).first()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Item], int]:
        """Get multiple items with pagination and filtering."""
        query = self.db.query(Item)
        
        if filters:
            # Search filter
            if filters.get("search"):
                search = filters["search"]
                search_filter = or_(
                    Item.name.ilike(f"%{search}%"),
                    Item.description.ilike(f"%{search}%"),
                    Item.tags.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # Category filter
            if filters.get("category"):
                query = query.filter(Item.category == filters["category"])
            
            # Price range filters
            if filters.get("min_price") is not None:
                query = query.filter(Item.price >= filters["min_price"])
            
            if filters.get("max_price") is not None:
                query = query.filter(Item.price <= filters["max_price"])
            
            # Active status filter
            if filters.get("is_active") is not None:
                query = query.filter(Item.is_active == filters["is_active"])
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    async def update(self, item: Item, item_data: ItemUpdate) -> Item:
        """Update item."""
        try:
            # Update fields that are provided
            update_data = item_data.dict(exclude_unset=True)
            
            # Handle tags conversion
            if "tags" in update_data and update_data["tags"] is not None:
                update_data["tags"] = ", ".join(update_data["tags"]) if update_data["tags"] else None
            
            for field, value in update_data.items():
                setattr(item, field, value)
            
            self.db.commit()
            self.db.refresh(item)
            
            return item
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to update item: {str(e)}")
    
    async def delete(self, item_id: int) -> bool:
        """Delete item by ID."""
        try:
            item = await self.get(item_id)
            if item:
                self.db.delete(item)
                self.db.commit()
                return True
            return False
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to delete item: {str(e)}")
    
    async def get_categories(self) -> List[str]:
        """Get list of unique categories."""
        categories = self.db.query(Item.category).distinct().all()
        return [category[0] for category in categories if category[0]]
    
    async def toggle_active(self, item_id: int) -> Optional[Item]:
        """Toggle item active status."""
        try:
            item = await self.get(item_id)
            if item:
                item.is_active = not item.is_active
                self.db.commit()
                self.db.refresh(item)
            return item
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to toggle item status: {str(e)}")
    
    async def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Item], int]:
        """Get items by owner ID."""
        query = self.db.query(Item).filter(Item.owner_id == owner_id)
        
        total = query.count()
        items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    async def search_by_tags(self, tags: List[str], skip: int = 0, limit: int = 100) -> Tuple[List[Item], int]:
        """Search items by tags."""
        if not tags:
            return [], 0
        
        # Create OR conditions for each tag
        tag_conditions = [Item.tags.ilike(f"%{tag}%") for tag in tags]
        query = self.db.query(Item).filter(or_(*tag_conditions))
        
        total = query.count()
        items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    async def get_low_stock_items(self, threshold: int = 10) -> List[Item]:
        """Get items with low stock."""
        return self.db.query(Item).filter(
            and_(
                Item.stock_quantity <= threshold,
                Item.is_active == True
            )
        ).all()
    
    async def get_item_stats(self) -> dict:
        """Get item statistics."""
        total_items = self.db.query(func.count(Item.id)).scalar()
        active_items = self.db.query(func.count(Item.id)).filter(Item.is_active == True).scalar()
        out_of_stock = self.db.query(func.count(Item.id)).filter(Item.stock_quantity == 0).scalar()
        low_stock = self.db.query(func.count(Item.id)).filter(
            and_(Item.stock_quantity > 0, Item.stock_quantity <= 10)
        ).scalar()
        
        avg_price = self.db.query(func.avg(Item.price)).scalar() or 0
        total_value = self.db.query(func.sum(Item.price * Item.stock_quantity)).scalar() or 0
        
        return {
            "total_items": total_items,
            "active_items": active_items,
            "inactive_items": total_items - active_items,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "average_price": round(float(avg_price), 2),
            "total_inventory_value": round(float(total_value), 2),
        }