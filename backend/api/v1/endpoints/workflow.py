"""Workflow API endpoints.

This module provides REST API endpoints for workflow management and execution.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status, Request
from fastapi.responses import JSONResponse

from core.logging import get_logger
from core.exceptions import (
    WorkflowException,
    WorkflowNotFoundException,
    ValidationException
)
from models.workflow import (
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowStatus
)
from models.common import (
    ErrorResponse,
    SuccessResponse,
    PaginationParams
)
from workflows.manager import WorkflowManager

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Dependency to get workflow manager
def get_workflow_manager(request: Request) -> WorkflowManager:
    """Get workflow manager instance from app state"""
    workflow_manager = getattr(request.app.state, 'workflow_manager', None)
    if workflow_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workflow manager not initialized"
        )
    return workflow_manager


@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow",
    description="Create a new workflow configuration with specified parameters"
)
async def create_workflow(
    request: WorkflowCreateRequest,
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowResponse:
    """Create a new workflow configuration"""
    try:
        logger.info(
            f"Creating workflow: {request.name}",
            extra={"workflow_name": request.name}
        )
        
        workflow = manager.create_workflow(request)
        
        logger.info(
            f"Workflow created successfully: {workflow.name}",
            extra={"workflow_id": workflow.id}
        )
        
        return workflow
        
    except WorkflowNotFoundException as e:
        logger.error(f"Workflow not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow type not found: {str(e)}"
        )
    except ValidationException as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except WorkflowException as e:
        logger.error(f"Workflow creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow creation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/",
    response_model=WorkflowListResponse,
    summary="List all workflows",
    description="""Retrieve a paginated list of all registered workflows in the system.
    
    This endpoint provides comprehensive information about all available workflows,
    including their current status, execution counts, and metadata. Use pagination
    parameters to control the number of results returned.
    
    **Features:**
    - Pagination support with configurable limits
    - Total count and page information
    - Workflow metadata and execution statistics
    - Active/inactive workflow filtering
    """,
    responses={
        200: {
            "description": "Successfully retrieved workflow list",
            "content": {
                "application/json": {
                    "example": {
                        "workflows": [
                            {
                                "id": "wf_data_pipeline_001",
                                "name": "Data Processing Pipeline",
                                "description": "Processes customer data through multiple transformation steps",
                                "workflow_type": "data_pipeline",
                                "status": "active",
                                "is_active": True,
                                "execution_count": 42,
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-20T14:22:00Z",
                                "last_execution_at": "2024-01-20T14:22:00Z"
                            }
                        ],
                        "total_count": 15,
                        "page": 1,
                        "page_size": 100,
                        "total_pages": 1,
                        "has_next": False,
                        "has_previous": False
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    },
    tags=["Workflows"]
)
async def list_workflows(
    limit: int = Query(
        100, 
        ge=1, 
        le=1000, 
        description="Maximum number of workflows to return per page",
        example=50
    ),
    offset: int = Query(
        0, 
        ge=0, 
        description="Number of workflows to skip (for pagination)",
        example=0
    ),
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowListResponse:
    """List all registered workflows with pagination"""
    try:
        logger.info(
            f"Listing workflows: limit={limit}, offset={offset}"
        )
        
        workflow_list = manager.get_workflow_list_response(limit=limit, offset=offset)
        
        logger.info(
            f"Retrieved {len(workflow_list.workflows)} workflows",
            extra={"total": workflow_list.total}
        )
        
        return workflow_list
        
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{workflow_name}",
    response_model=WorkflowResponse,
    summary="Get workflow details",
    description="""Retrieve detailed information about a specific workflow by name.
    
    This endpoint returns comprehensive information about a single workflow,
    including its configuration, execution history, input/output schemas,
    and current status.
    
    **Use Cases:**
    - Get workflow configuration before execution
    - Check workflow status and metadata
    - Retrieve input/output schema definitions
    - Monitor workflow execution statistics
    """,
    responses={
        200: {
            "description": "Successfully retrieved workflow details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "wf_data_pipeline_001",
                        "name": "Data Processing Pipeline",
                        "description": "Processes customer data through multiple transformation steps",
                        "workflow_type": "data_pipeline",
                        "status": "active",
                        "is_active": True,
                        "execution_count": 42,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T14:22:00Z",
                        "last_execution_at": "2024-01-20T14:22:00Z",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "data": {"type": "array"},
                                "options": {"type": "object"}
                            },
                            "required": ["data"]
                        },
                        "output_schema": {
                            "type": "object",
                            "properties": {
                                "result": {"type": "array"},
                                "metadata": {"type": "object"}
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Workflow not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workflow not found: invalid_workflow_name"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    },
    tags=["Workflows"]
)
async def get_workflow(
    workflow_name: str = Path(
        description="Name of the workflow to retrieve",
        example="data_processing_pipeline",
        min_length=1,
        max_length=100
    ),
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowResponse:
    """Get workflow details by name"""
    try:
        logger.info(
            f"Getting workflow: {workflow_name}",
            extra={"workflow_name": workflow_name}
        )
        
        workflow = manager.get_workflow(workflow_name)
        
        # Create response from workflow instance
        response = WorkflowResponse(
            id=f"{workflow.name}_{workflow.version}",
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            status=WorkflowStatus.PENDING,
            config={},
            created_at=workflow.created_at if hasattr(workflow, 'created_at') else None,
            updated_at=workflow.updated_at if hasattr(workflow, 'updated_at') else None
        )
        
        logger.info(
            f"Retrieved workflow: {workflow_name}",
            extra={"workflow_id": response.id}
        )
        
        return response
        
    except WorkflowNotFoundException as e:
        logger.error(f"Workflow not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_name}"
        )
    except Exception as e:
        logger.error(f"Error getting workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{workflow_name}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute workflow",
    description="""Execute a workflow with a user prompt and optional configuration.
    
    This endpoint starts the execution of a specified workflow with a user prompt as input.
    The workflow processes the user's natural language request and generates appropriate
    responses or actions. Execution can be performed synchronously or asynchronously.
    
    **Input Requirements:**
    - **user_prompt**: Natural language input describing the user's request (required)
    - **input_data**: Optional additional structured data for context
    
    **Execution Modes:**
    - **sync**: Waits for completion and returns final results
    - **async**: Returns immediately with execution ID for status tracking
    
    **Features:**
    - Natural language processing of user prompts
    - Configurable timeout settings
    - Step-by-step execution tracking
    - Error handling and reporting
    - Progress monitoring
    - Callback URL support for async executions
    
    **Best Practices:**
    - Provide clear, specific user prompts for better results
    - Use async mode for complex or long-running requests
    - Set appropriate timeout values based on expected processing time
    - Include relevant context in optional input_data when needed
    """,
    responses={
        200: {
            "description": "Workflow execution started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "exec_abc123def456",
                        "workflow_id": "wf_data_pipeline_001",
                        "status": "running",
                        "execution_mode": "async",
                        "input_data": {
                            "user_prompt": "Create a bar chart showing sales data for Q1 2024",
                            "execution_id": "exec_abc123def456",
                            "execution_mode": "async",
                            "timeout_seconds": 300
                        },
                        "output_data": None,
                        "steps": [
                            {
                                "step_id": "step_validation",
                                "name": "Data Validation",
                                "status": "completed",
                                "started_at": "2024-01-20T14:22:00Z",
                                "completed_at": "2024-01-20T14:22:05Z",
                                "duration_seconds": 5.2
                            },
                            {
                                "step_id": "step_processing",
                                "name": "Data Processing",
                                "status": "running",
                                "started_at": "2024-01-20T14:22:05Z"
                            }
                        ],
                        "started_at": "2024-01-20T14:22:00Z",
                        "progress_percentage": 45.0,
                        "created_at": "2024-01-20T14:22:00Z",
                        "updated_at": "2024-01-20T14:22:10Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid input data or request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Validation failed: user_prompt is required"
                    }
                }
            }
        },
        404: {
            "description": "Workflow not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workflow not found: invalid_workflow_name"
                    }
                }
            }
        },
        422: {
            "description": "Validation error in request body",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "user_prompt"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during execution",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    },
    tags=["Workflows"]
)
async def execute_workflow(
    workflow_name: str = Path(
        description="Name of the workflow to execute",
        example="data_processing_pipeline",
        min_length=1,
        max_length=100
    ),
    request: WorkflowExecuteRequest = Body(
        description="Workflow execution request with user prompt and optional configuration",
        example={
            "user_prompt": "Create a bar chart showing sales data for Q1 2024",
            "input_data": {
                "context": "quarterly_sales",
                "format_preference": "interactive"
            },
            "execution_mode": "async",
            "timeout_seconds": 300,
            "callback_url": "https://api.example.com/webhook/workflow-complete"
        }
    ),
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowExecutionResponse:
    """Execute a workflow with input data"""
    try:
        # Set workflow name from path parameter
        request.workflow_name = workflow_name
        
        logger.info(
            f"Executing workflow: {workflow_name}",
            extra={
                "workflow_name": workflow_name
            }
        )
        
        execution_result = manager.execute_workflow(request)
        
        logger.info(
            f"Workflow execution completed: {workflow_name}",
            extra={
                "execution_id": execution_result.execution_id,
                "status": execution_result.status.value
            }
        )
        
        return execution_result
        
    except WorkflowNotFoundException as e:
        logger.error(f"Workflow not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_name}"
        )
    except ValidationException as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except WorkflowException as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow execution failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error executing workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get execution details",
    description="Get detailed information about a specific workflow execution"
)
async def get_execution(
    execution_id: str,
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowExecutionResponse:
    """Get execution details by ID"""
    try:
        logger.info(
            f"Getting execution: {execution_id}",
            extra={"execution_id": execution_id}
        )
        
        execution = manager.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution not found: {execution_id}"
            )
        
        # Convert execution to response
        response = WorkflowExecutionResponse(
            execution_id=execution.execution_id,
            workflow_name=execution.workflow.name,
            status=execution.status,
            input_data=execution.input_data,
            output_data=execution.state.get("output_data", {}) if execution.state else {},
            error_message=execution.error_message,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            progress_percentage=execution.state.get("progress_percentage", 0.0) if execution.state else 0.0,
            steps=[]
        )
        
        logger.info(
            f"Retrieved execution: {execution_id}",
            extra={"status": execution.status.value}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/executions",
    response_model=List[Dict[str, Any]],
    summary="List executions",
    description="Get a list of workflow executions with optional filtering"
)
async def list_executions(
    workflow_name: Optional[str] = Query(None, description="Filter by workflow name"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by execution status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of executions to return"),
    offset: int = Query(0, ge=0, description="Number of executions to skip"),
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> List[Dict[str, Any]]:
    """List workflow executions with filtering and pagination"""
    try:
        logger.info(
            f"Listing executions: workflow_name={workflow_name}, status={status}, limit={limit}, offset={offset}"
        )
        
        executions = manager.list_executions(
            workflow_name=workflow_name,
            status=status,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Retrieved {len(executions)} executions"
        )
        
        return executions
        
    except Exception as e:
        logger.error(f"Error listing executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/executions/{execution_id}/cancel",
    response_model=SuccessResponse,
    summary="Cancel execution",
    description="Cancel a running workflow execution"
)
async def cancel_execution(
    execution_id: str,
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> SuccessResponse:
    """Cancel a running execution"""
    try:
        logger.info(
            f"Cancelling execution: {execution_id}",
            extra={"execution_id": execution_id}
        )
        
        success = manager.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution not found or cannot be cancelled: {execution_id}"
            )
        
        logger.info(
            f"Execution cancelled successfully: {execution_id}"
        )
        
        return SuccessResponse(
            success=True,
            message=f"Execution {execution_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/statistics",
    response_model=Dict[str, Any],
    summary="Get workflow statistics",
    description="Get comprehensive statistics about workflows and executions"
)
async def get_statistics(
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """Get workflow and execution statistics"""
    try:
        logger.info("Getting workflow statistics")
        
        stats = manager.get_statistics()
        
        logger.info(
            f"Retrieved statistics: {stats['total_executions']} total executions"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/cleanup",
    response_model=SuccessResponse,
    summary="Cleanup old executions",
    description="Clean up old workflow executions to free up memory"
)
async def cleanup_executions(
    older_than_hours: int = Query(24, ge=1, description="Remove executions older than this many hours"),
    manager: WorkflowManager = Depends(get_workflow_manager)
) -> SuccessResponse:
    """Clean up old executions"""
    try:
        logger.info(
            f"Cleaning up executions older than {older_than_hours} hours"
        )
        
        cleaned_count = manager.cleanup_executions(older_than_hours)
        
        logger.info(
            f"Cleaned up {cleaned_count} old executions"
        )
        
        return SuccessResponse(
            success=True,
            message=f"Cleaned up {cleaned_count} old executions"
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )