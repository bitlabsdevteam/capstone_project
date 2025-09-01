from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse

router = APIRouter()

# Mock data for demonstration
mock_users = [
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "phone_number": "+1234567890",
        "is_active": True,
        "is_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "username": "jane_smith",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "phone_number": "+1987654321",
        "is_active": True,
        "is_verified": False,
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z"
    }
]


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate):
    """Create a new user (mock implementation)."""
    # Check if user already exists
    for user in mock_users:
        if user["email"] == user_data.email:
            raise HTTPException(status_code=409, detail="User with this email already exists")
        if user["username"] == user_data.username:
            raise HTTPException(status_code=409, detail="User with this username already exists")
    
    # Create new user
    new_user = {
        "id": len(mock_users) + 1,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "phone_number": user_data.phone_number,
        "is_active": True,
        "is_verified": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    mock_users.append(new_user)
    return UserResponse(**new_user)


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search term for username or email")
):
    """Get list of users with pagination and search (mock implementation)."""
    filtered_users = mock_users
    
    # Apply search filter
    if search:
        filtered_users = [
            user for user in mock_users
            if search.lower() in user["username"].lower() or search.lower() in user["email"].lower()
        ]
    
    # Apply pagination
    paginated_users = filtered_users[skip:skip + limit]
    
    return UserListResponse(
        users=[UserResponse(**user) for user in paginated_users],
        total=len(filtered_users),
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID (mock implementation)."""
    for user in mock_users:
        if user["id"] == user_id:
            return UserResponse(**user)
    
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate):
    """Update user by ID (mock implementation)."""
    for i, user in enumerate(mock_users):
        if user["id"] == user_id:
            # Check for conflicts if updating email or username
            if user_data.email and user_data.email != user["email"]:
                for other_user in mock_users:
                    if other_user["email"] == user_data.email and other_user["id"] != user_id:
                        raise HTTPException(status_code=409, detail="User with this email already exists")
            
            if user_data.username and user_data.username != user["username"]:
                for other_user in mock_users:
                    if other_user["username"] == user_data.username and other_user["id"] != user_id:
                        raise HTTPException(status_code=409, detail="User with this username already exists")
            
            # Update user data
            update_data = user_data.dict(exclude_unset=True)
            mock_users[i].update(update_data)
            mock_users[i]["updated_at"] = "2024-01-01T00:00:00Z"
            return UserResponse(**mock_users[i])
    
    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """Delete user by ID (mock implementation)."""
    for i, user in enumerate(mock_users):
        if user["id"] == user_id:
            del mock_users[i]
            return
    
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/{user_id}/profile", response_model=UserResponse)
async def get_user_profile(user_id: int):
    """Get user profile by ID (mock implementation)."""
    for user in mock_users:
        if user["id"] == user_id:
            return UserResponse(**user)
    
    raise HTTPException(status_code=404, detail="User profile not found")