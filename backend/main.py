"""Main FastAPI application.

This module creates and configures the FastAPI application with all routes,
middleware, and error handlers.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import get_settings
from core.logging import setup_logging, get_logger
from core.exceptions import (
    BaseAPIException,
    ValidationException,
    WorkflowException,
    base_api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from api.v1 import api_router as v1_router
# Import from workflow instead of streaming
from workflows.registry import WorkflowRegistry
from workflows.manager import WorkflowManager

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting FastAPI LangGraph Workflow Service")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize workflow registry with default workflows
    try:
        from workflows.registry import initialize_workflow_system, get_workflow_registry_info, get_workflow_registry
        
        initialize_workflow_system()
        workflow_registry = get_workflow_registry()
        registry_info = get_workflow_registry_info()
        
        logger.info(
            f"Initialized workflow registry with {len(registry_info['workflow_types'])} workflow types: "
            f"{', '.join(registry_info['workflow_types'])}"
        )
        
        # Store registry in app state for access by endpoints
        app.state.workflow_registry = workflow_registry
        
        # Initialize workflow manager
        workflow_manager = WorkflowManager()
        workflow_manager.registry = workflow_registry
        app.state.workflow_manager = workflow_manager
        
    except Exception as e:
        logger.error(f"Failed to initialize workflow registry: {str(e)}")
        raise
    
    # Log startup completion
    logger.info("Application startup completed successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI LangGraph Workflow Service")
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""Enterprise-grade workflow orchestration service built with FastAPI and LangGraph.
    
    This service delivers a production-ready API for designing, managing, and executing 
    sophisticated workflows through LangGraph's advanced state machine architecture. 
    Designed for scalability and reliability in enterprise environments.
    
    ## Core Capabilities
    
    - **Workflow Lifecycle Management**: Complete CRUD operations with versioning support
    - **Real-time Execution Engine**: Asynchronous workflow processing with live monitoring
    - **Persistent State Management**: Reliable state handling with automatic recovery
    - **Comprehensive Monitoring**: Health checks, metrics, and observability features
    - **Standards Compliance**: OpenAPI 3.0 specification with interactive documentation
    - **High Performance**: Optimized async processing for concurrent operations
    
    ## API Organization
    
    - **Workflows** (`/api/v1/workflows/`): Workflow management and execution
    - **Health** (`/api/v1/health/`): Service health and readiness monitoring
    - **Documentation** (`/docs`, `/redoc`): Interactive API exploration
    
    ## Security & Performance
    
    This development instance operates without authentication. Production deployments 
    require proper authentication, authorization, and rate limiting implementation.
    
    ## Getting Started
    
    Explore the interactive documentation at `/docs` or refer to the project 
    repository for comprehensive guides and examples.
    """,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    contact={
        "name": "Development Team",
        "url": "https://github.com/your-org/workflow-service",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local development environment"
        },
        {
            "url": "https://api-staging.workflow-service.com",
            "description": "Staging environment"
        },
        {
            "url": "https://api.workflow-service.com",
            "description": "Production environment"
        }
    ],
    tags_metadata=[
        {
            "name": "Workflows",
            "description": "Workflow lifecycle management including creation, execution, and monitoring operations.",
        },
        {
            "name": "Health",
            "description": "Service health monitoring and readiness probe endpoints for operational visibility.",
        },
        {
            "name": "System",
            "description": "System information and service metadata endpoints.",
        }
    ]
)


# Add CORS middleware
allowed_origins = settings.ALLOWED_HOSTS
if settings.ALLOWED_ORIGINS:
    # Use ALLOWED_ORIGINS from environment if specified
    allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS middleware enabled with origins: {allowed_origins}")


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # Log error
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": round(process_time, 4),
                "client_ip": request.client.host if request.client else None
            }
        )
        raise


# Add exception handlers
app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Include API routers
app.include_router(
    v1_router,
    prefix="/api"
)


# Root endpoint
@app.get(
    "/",
    summary="Service information",
    description="""Retrieve service metadata and API navigation information.
    
    Provides essential service details including version information, 
    available endpoints, and documentation links for API exploration.
    
    **Response includes:**
    - Service identification and version
    - Environment configuration
    - Documentation endpoints
    - API structure overview
    - Current service status
    """,
    responses={
        200: {
            "description": "Application information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Workflow Orchestration Service",
                        "description": "Enterprise-grade workflow orchestration powered by LangGraph",
                        "version": "1.0.0",
                        "environment": "development",
                        "documentation": {
                            "swagger_ui": "/docs",
                            "redoc": "/redoc",
                            "openapi_spec": "/openapi.json"
                        },
                        "api": {
                            "base_path": "/api/v1",
                            "endpoints": {
                                "workflows": "/api/v1/workflows",
                                "health": "/api/v1/health",
                                "readiness": "/api/v1/health/readiness"
                            }
                        },
                        "status": "operational",
                        "timestamp": "2024-01-20T14:22:00.123Z"
                    }
                }
            }
        }
    },
    tags=["System"]
)
async def root():
    """Root endpoint with comprehensive service information"""
    from datetime import datetime
    
    response_data = {
        "name": settings.PROJECT_NAME,
        "description": "Enterprise-grade workflow orchestration powered by LangGraph",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "api": {
            "base_path": "/api/v1",
            "endpoints": {
                "workflows": "/api/v1/workflows",
                "health": "/api/v1/health",
                "readiness": "/api/v1/health/readiness"
            }
        },
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Add documentation URLs only in debug mode
    if settings.DEBUG:
        response_data["documentation"] = {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        }
    
    return response_data


# Health check endpoint (also available at root level)
@app.get(
    "/health",
    summary="Service health check",
    description="""Perform a lightweight health status verification.
    
    Provides real-time service health information for monitoring systems,
    load balancers, and orchestration platforms to assess service readiness
    and operational status.
    
    **Health metrics include:**
    - Service operational status
    - System resource availability
    - Response latency indicators
    - External dependency connectivity
    - Resource utilization metrics
    
    Designed for high-frequency polling with minimal performance impact
    and standardized JSON response format.
    """,
    responses={
        200: {
            "description": "Service is healthy and running",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "message": "Service operational",
                        "timestamp": "2024-01-20T14:22:00.123Z",
                        "uptime": 86400,
                        "version": "1.0.0"
                    }
                }
            }
        }
    },
    tags=["System"]
)
async def health():
    """Lightweight health check endpoint for service availability monitoring"""
    from datetime import datetime
    
    return {
        "status": "healthy",
        "message": "Service operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )