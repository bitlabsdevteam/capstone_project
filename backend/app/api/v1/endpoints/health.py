from fastapi import APIRouter
import time
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.schemas.health import HealthResponse, DetailedHealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version=settings.VERSION,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check endpoint."""
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=time.time(),
        version=settings.VERSION,
    )