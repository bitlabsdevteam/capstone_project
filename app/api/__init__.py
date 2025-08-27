"""API module for FastAPI endpoints and frontend integration"""

from fastapi import APIRouter
from .routes import router as main_router
from .workflows import router as workflows_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(main_router, tags=["main"])
api_router.include_router(workflows_router, tags=["workflows"])

__all__ = ["api_router"]