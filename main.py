"""Main FastAPI application entry point for Vizuara Web3 Application Builder"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.exceptions import (
    BaseCustomException,
    custom_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.api import api_router

settings = get_settings()

# Setup logging
setup_logging()

app = FastAPI(
    title="Multi-Agent Web3 Application Builder",
    description="A no-code Web3 application builder powered by multi-agent AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middleware(app, settings)

# Configure CORS (fallback, middleware handles this too)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(BaseCustomException, custom_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent Web3 Application Builder API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "llm_integration": "active",
            "agent_framework": "active",
            "web3_functionality": "active",
            "api_endpoints": "active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )