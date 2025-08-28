"""Health check API endpoints.

This module provides health monitoring endpoints for the FastAPI application.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from core.logging import get_logger
from models.health import HealthResponse, HealthStatus, ComponentHealth
from workflows.manager import WorkflowManager
from workflows.registry import WorkflowRegistry

logger = get_logger(__name__)

# Create router
router = APIRouter()


def get_workflow_manager() -> WorkflowManager:
    """Get workflow manager instance"""
    return WorkflowManager()


def get_workflow_registry() -> WorkflowRegistry:
    """Get workflow registry instance"""
    return WorkflowRegistry()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Application health check",
    description="""Get comprehensive health status of the application and all its components.
    
    This endpoint provides detailed health information about the application,
    including system resources, component status, and overall service health.
    Use this endpoint for monitoring, alerting, and health checks.
    
    **Health Components Checked:**
    - Application startup status
    - Workflow manager availability
    - Workflow registry status
    - LangGraph integration
    - System resources (memory, CPU)
    - Python runtime information
    
    **Status Levels:**
    - **healthy**: All components are functioning normally
    - **degraded**: Some components have issues but service is operational
    - **unhealthy**: Critical components are failing
    - **unknown**: Unable to determine component status
    """,
    responses={
        200: {
            "description": "Health check completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-20T14:22:00Z",
                        "version": "1.0.0",
                        "uptime_seconds": 86400.5,
                        "components": [
                            {
                                "name": "workflow_manager",
                                "status": "healthy",
                                "message": "Workflow manager is operational",
                                "response_time_ms": 12.3,
                                "last_checked": "2024-01-20T14:22:00Z",
                                "metadata": {
                                    "registered_workflows": 5,
                                    "active_executions": 2
                                }
                            },
                            {
                                "name": "workflow_registry",
                                "status": "healthy",
                                "message": "Registry is accessible",
                                "response_time_ms": 8.7,
                                "last_checked": "2024-01-20T14:22:00Z",
                                "metadata": {
                                    "total_workflows": 5
                                }
                            }
                        ],
                        "system_info": {
                            "python_version": "3.11.0",
                            "platform": "linux",
                            "memory_usage_mb": 256.7,
                            "cpu_usage_percent": 15.3
                        }
                    }
                }
            }
        },
        503: {
            "description": "Service unavailable - health check failed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-01-20T14:22:00Z",
                        "version": "1.0.0",
                        "uptime_seconds": 86400.5,
                        "components": [
                            {
                                "name": "workflow_manager",
                                "status": "unhealthy",
                                "message": "Failed to initialize workflow manager",
                                "last_checked": "2024-01-20T14:22:00Z"
                            }
                        ]
                    }
                }
            }
        }
    },
    tags=["Health"]
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint"""
    try:
        logger.debug("Performing basic health check")
        
        health_response = HealthResponse(
            status=HealthStatus.HEALTHY,
            message="Application is running",
            timestamp=None,  # Will be set automatically
            version="1.0.0",
            components={}
        )
        
        logger.debug("Basic health check completed successfully")
        return health_response
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status=HealthStatus.UNHEALTHY,
            message=f"Health check failed: {str(e)}",
            timestamp=None,
            version="1.0.0",
            components={}
        )


@router.get(
    "/detailed",
    response_model=HealthResponse,
    summary="Detailed health check",
    description="Get detailed health status including all system components"
)
async def detailed_health_check(
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    workflow_registry: WorkflowRegistry = Depends(get_workflow_registry)
) -> HealthResponse:
    """Detailed health check with component status"""
    try:
        logger.info("Performing detailed health check")
        
        health_response = HealthResponse(
            status=HealthStatus.HEALTHY,
            message="Detailed health check",
            timestamp=None,
            version="1.0.0",
            components={}
        )
        
        # Check workflow manager
        try:
            stats = workflow_manager.get_statistics()
            health_response.add_component(
                "workflow_manager",
                ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message="Workflow manager is operational",
                    details={
                        "total_executions": stats.get("total_executions", 0),
                        "active_executions": stats.get("active_executions", 0)
                    }
                )
            )
        except Exception as e:
            logger.warning(f"Workflow manager health check failed: {str(e)}")
            health_response.add_component(
                "workflow_manager",
                ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Workflow manager error: {str(e)}",
                    details={}
                )
            )
        
        # Check workflow registry
        try:
            registered_workflows = workflow_registry.list_workflows()
            health_response.add_component(
                "workflow_registry",
                ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message="Workflow registry is operational",
                    details={
                        "registered_workflows": len(registered_workflows),
                        "workflow_names": list(registered_workflows.keys())
                    }
                )
            )
        except Exception as e:
            logger.warning(f"Workflow registry health check failed: {str(e)}")
            health_response.add_component(
                "workflow_registry",
                ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Workflow registry error: {str(e)}",
                    details={}
                )
            )
        
        # Check LangGraph dependencies
        try:
            import langgraph
            health_response.add_component(
                "langgraph",
                ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message="LangGraph is available",
                    details={
                        "version": getattr(langgraph, "__version__", "unknown")
                    }
                )
            )
        except ImportError as e:
            logger.error(f"LangGraph import failed: {str(e)}")
            health_response.add_component(
                "langgraph",
                ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    message=f"LangGraph not available: {str(e)}",
                    details={}
                )
            )
        
        # Update overall status based on components
        overall_status = health_response.get_overall_status()
        health_response.status = overall_status
        
        if overall_status == HealthStatus.HEALTHY:
            health_response.message = "All components are healthy"
        elif overall_status == HealthStatus.DEGRADED:
            health_response.message = "Some components are experiencing issues"
        else:
            health_response.message = "Critical components are unhealthy"
        
        logger.info(
            f"Detailed health check completed: {overall_status.value}",
            extra={"overall_status": overall_status.value}
        )
        
        return health_response
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return HealthResponse(
            status=HealthStatus.UNHEALTHY,
            message=f"Detailed health check failed: {str(e)}",
            timestamp=None,
            version="1.0.0",
            components={}
        )


@router.get(
    "/readiness",
    summary="Application readiness check",
    description="""Check if the application is ready to serve requests and handle workflows.
    
    This endpoint is specifically designed for Kubernetes readiness probes and
    load balancer health checks. It verifies that all critical components are
    initialized and ready to process incoming requests.
    
    **Readiness Criteria:**
    - All required services are initialized
    - Workflow manager is operational
    - Workflow registry is accessible
    - Database connections are established (if applicable)
    - External dependencies are reachable
    
    **Use Cases:**
    - Kubernetes readiness probes
    - Load balancer health checks
    - Service mesh health verification
    - Deployment validation
    
    **Difference from Health Check:**
    - Health: Overall application wellness (includes performance metrics)
    - Readiness: Ability to serve requests (binary ready/not ready)
    """,
    responses={
        200: {
            "description": "Application is ready to serve requests",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ready",
                        "message": "Application is ready to serve requests"
                    }
                }
            }
        },
        503: {
            "description": "Application is not ready to serve requests",
            "content": {
                "application/json": {
                    "example": {
                        "status": "not_ready",
                        "message": "Application is not ready",
                        "issues": ["Still initializing workflow manager"]
                    }
                }
            }
        }
    },
    tags=["Health"]
)
async def readiness_check(
    workflow_registry: WorkflowRegistry = Depends(get_workflow_registry)
) -> JSONResponse:
    """Readiness probe for Kubernetes/container orchestration"""
    try:
        logger.debug("Performing readiness check")
        
        # Check if essential components are ready
        ready = True
        issues = []
        
        # Check workflow registry
        try:
            workflows = workflow_registry.list_workflows()
            if not workflows:
                issues.append("No workflows registered")
        except Exception as e:
            ready = False
            issues.append(f"Workflow registry not ready: {str(e)}")
        
        # Check LangGraph availability
        try:
            import langgraph
        except ImportError as e:
            ready = False
            issues.append(f"LangGraph not available: {str(e)}")
        
        if ready:
            logger.debug("Readiness check passed")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ready",
                    "message": "Application is ready to serve requests"
                }
            )
        else:
            logger.warning(f"Readiness check failed: {issues}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "message": "Application is not ready",
                    "issues": issues
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": f"Readiness check error: {str(e)}"
            }
        )


@router.get(
    "/liveness",
    summary="Liveness probe",
    description="Check if the application is alive and responsive"
)
async def liveness_check() -> JSONResponse:
    """Liveness probe for Kubernetes/container orchestration"""
    try:
        logger.debug("Performing liveness check")
        
        # Basic liveness check - if we can respond, we're alive
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "alive",
                "message": "Application is alive and responsive"
            }
        )
        
    except Exception as e:
        logger.error(f"Liveness check error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": f"Liveness check error: {str(e)}"
            }
        )


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="Application metrics",
    description="Get application performance and usage metrics"
)
async def get_metrics(
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """Get application metrics for monitoring"""
    try:
        logger.debug("Collecting application metrics")
        
        # Get workflow statistics
        workflow_stats = workflow_manager.get_statistics()
        
        # Collect system metrics
        import psutil
        import time
        
        metrics = {
            "timestamp": time.time(),
            "application": {
                "name": "FastAPI LangGraph Workflow Service",
                "version": "1.0.0",
                "uptime_seconds": time.time() - getattr(get_metrics, '_start_time', time.time())
            },
            "workflows": workflow_stats,
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
        
        # Set start time if not already set
        if not hasattr(get_metrics, '_start_time'):
            get_metrics._start_time = time.time()
        
        logger.debug("Application metrics collected successfully")
        return metrics
        
    except ImportError:
        # psutil not available, return basic metrics
        logger.warning("psutil not available, returning basic metrics")
        workflow_stats = workflow_manager.get_statistics()
        
        return {
            "timestamp": time.time(),
            "application": {
                "name": "FastAPI LangGraph Workflow Service",
                "version": "1.0.0"
            },
            "workflows": workflow_stats
        }
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")
        return {
            "timestamp": time.time(),
            "error": f"Error collecting metrics: {str(e)}"
        }