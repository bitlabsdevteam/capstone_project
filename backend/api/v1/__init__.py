"""API v1 package initialization.

This module sets up the v1 API routing structure.
"""

from fastapi import APIRouter

from .endpoints import workflows, health, agents

# V1 API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["workflows"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"]
)

__all__ = ["api_router"]