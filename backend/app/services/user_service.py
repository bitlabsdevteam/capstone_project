from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import DatabaseException

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service layer for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Hash the password
            hashed_password = self._hash_password(user_data.password)
            
            # Create user instance
            db_user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                is_active=user_data.is_active,
                avatar_url=user_data.avatar_url,
                bio=user_data.bio,
                phone=user_data.phone,
                location=user_data.location,
                website=user_data.website,
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            return db_user
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to create user: {str(e)}")
    
    async def get(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Get multiple users with pagination and search."""
        query = self.db.query(User)
        
        # Apply search filter
        if search:
            search_filter = or_(
                User.full_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    async def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user."""
        try:
            # Update fields that are provided
            update_data = user_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            return user
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to update user: {str(e)}")
    
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        try:
            user = await self.get(user_id)
            if user:
                self.db.delete(user)
                self.db.commit()
                return True
            return False
        
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to delete user: {str(e)}")
    
    async def get_with_profile(self, user_id: int) -> Optional[User]:
        """Get user with additional profile information."""
        return self.db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
    
    async def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        user = await self.get(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
        return user
    
    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        user = await self.get(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
        return user
    
    async def get_user_stats(self) -> dict:
        """Get user statistics."""
        total_users = self.db.query(func.count(User.id)).scalar()
        active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        superusers = self.db.query(func.count(User.id)).filter(User.is_superuser == True).scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "superusers": superusers,
        }