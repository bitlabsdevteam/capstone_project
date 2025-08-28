"""API package initialization.

This module sets up the API routing structure for the FastAPI application.
"""

from fastapi import APIRouter

from .v1 import api_router as v1_router

# Main API router
api_router = APIRouter()

# Include version-specific routers
api_router.include_router(v1_router, prefix="/v1")

__all__ = ["api_router"]