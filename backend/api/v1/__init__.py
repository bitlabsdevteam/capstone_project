"""API v1 package initialization.

This module sets up the v1 API routing structure.
"""

from fastapi import APIRouter

from .endpoints import workflow, health

# V1 API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    workflow.router,
    prefix="/workflows",
    tags=["workflows"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

__all__ = ["api_router"]