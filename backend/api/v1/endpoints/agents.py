"""API endpoints for agent operations.

This module provides REST API endpoints for interacting with the gatekeeper agent
and other workflow agents in the system.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse

from agents.gatekeeper_agent import GatekeeperAgent, SupervisorAgent, SupervisorRequest, SupervisorResponse
from models.agent import (
    AgentProcessRequest,
    AgentProcessResponse,
    AgentConfiguration,
    AgentHealthCheck,
    AgentMemoryInfo,
    AgentToolInfo,
    AgentStatistics,
    ToolInvocationRequest,
    AgentStatus
)
from core.exceptions import WorkflowError

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global agent instances (in production, this would be managed by dependency injection)
_gatekeeper_agent: Optional[GatekeeperAgent] = None
_supervisor_agent: Optional[SupervisorAgent] = None


def get_gatekeeper_agent() -> GatekeeperAgent:
    """Get or create the gatekeeper agent instance.
    
    Returns:
        GatekeeperAgent: The gatekeeper agent instance
        
    Raises:
        HTTPException: If agent initialization fails
    """
    global _gatekeeper_agent
    
    if _gatekeeper_agent is None:
        try:
            _gatekeeper_agent = GatekeeperAgent()
            logger.info("Gatekeeper agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize gatekeeper agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize agent: {str(e)}"
            )
    
    return _gatekeeper_agent


def get_supervisor_agent() -> SupervisorAgent:
    """Get or create the supervisor agent instance.
    
    Returns:
        SupervisorAgent: The supervisor agent instance
        
    Raises:
        HTTPException: If agent initialization fails
    """
    global _supervisor_agent
    
    if _supervisor_agent is None:
        try:
            _supervisor_agent = SupervisorAgent()
            logger.info("Supervisor agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize supervisor agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize supervisor agent: {str(e)}"
            )
    
    return _supervisor_agent


@router.post(
    "/gatekeeper/process",
    response_model=AgentProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process request with gatekeeper agent",
    description="Submit a request to the gatekeeper agent for processing and decision-making.",
    responses={
        200: {
            "description": "Request processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "execution_id": "exec_20240120_142200_123456",
                        "session_id": "session_20240120_143000",
                        "agent_response": {
                            "decision": "approve",
                            "reasoning": "Request is valid and can be processed",
                            "confidence": 0.95,
                            "next_actions": [],
                            "metadata": {}
                        },
                        "tool_results": {},
                        "processing_history": [],
                        "metadata": {
                            "processing_time": 2.34,
                            "model_used": "gpt-4"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request format or parameters"},
        500: {"description": "Internal server error during processing"}
    }
)
async def process_request(
    request: AgentProcessRequest,
    background_tasks: BackgroundTasks,
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> AgentProcessResponse:
    """Process a request using the gatekeeper agent.
    
    Args:
        request: The processing request
        background_tasks: FastAPI background tasks
        agent: The gatekeeper agent instance
        
    Returns:
        AgentProcessResponse: The processing result
        
    Raises:
        HTTPException: If processing fails
    """
    execution_id = request.execution_id or f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Processing request {execution_id} for session {session_id}")
    
    try:
        # Process the request with supervisor agent
        result = agent.process_request(
            message=request.user_input,
            session_id=session_id
        )
        
        logger.info(f"Request {execution_id} processed successfully")
        
        return AgentProcessResponse(
            success=True,
            execution_id=execution_id,
            session_id=session_id,
            agent_response={
                "final_response": result.final_response,
                "messages": result.messages
            },
            tool_results={},
            processing_history=[],
            metadata={"supervisor_workflow": True}
        )
        
    except WorkflowError as e:
        logger.error(f"Workflow error processing request {execution_id}: {e}")
        return AgentProcessResponse(
            success=False,
            execution_id=execution_id,
            session_id=session_id,
            error=str(e),
            error_type="workflow_error",
            metadata={"error_timestamp": datetime.now().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error processing request {execution_id}: {e}")
        return AgentProcessResponse(
            success=False,
            execution_id=execution_id,
            session_id=session_id,
            error=f"Internal processing error: {str(e)}",
            error_type="internal_error",
            metadata={"error_timestamp": datetime.now().isoformat()}
        )


@router.get(
    "/gatekeeper/health",
    response_model=AgentHealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Check gatekeeper agent health",
    description="Get the current health status of the gatekeeper agent and its components."
)
async def get_agent_health(
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> AgentHealthCheck:
    """Get the health status of the gatekeeper agent.
    
    Args:
        agent: The gatekeeper agent instance
        
    Returns:
        AgentHealthCheck: The health status
    """
    try:
        health_info = agent.health_check()
        
        return AgentHealthCheck(
            healthy=health_info.get('healthy', False),
            components=health_info.get('components', {}),
            error=health_info.get('error'),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return AgentHealthCheck(
            healthy=False,
            components={},
            error=str(e),
            timestamp=datetime.now()
        )


@router.get(
    "/gatekeeper/memory",
    response_model=AgentMemoryInfo,
    status_code=status.HTTP_200_OK,
    summary="Get agent memory information",
    description="Retrieve information about the agent's memory state and conversation history."
)
async def get_memory_info(
    session_id: Optional[str] = None,
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> AgentMemoryInfo:
    """Get memory information for the agent.
    
    Args:
        session_id: Optional session ID to get memory for specific session
        agent: The gatekeeper agent instance
        
    Returns:
        AgentMemoryInfo: Memory information
    """
    # Supervisor pattern doesn't maintain persistent memory
    return AgentMemoryInfo(
        summary="Supervisor agent uses stateless workflow processing",
        message_count=0,
        token_count=0,
        last_updated=None
    )


@router.get(
    "/gatekeeper/tools",
    response_model=AgentToolInfo,
    status_code=status.HTTP_200_OK,
    summary="Get available tools information",
    description="Retrieve information about tools available to the gatekeeper agent."
)
async def get_tools_info(
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> AgentToolInfo:
    """Get information about available tools.
    
    Args:
        agent: The gatekeeper agent instance
        
    Returns:
        AgentToolInfo: Tools information
    """
    # Supervisor pattern has built-in worker agents with specific tools
    return AgentToolInfo(
        total_tools=2,
        tool_names=["research_agent", "math_agent"],
        tool_details={
            "research_agent": "Web search and research capabilities using Tavily",
            "math_agent": "Mathematical computations and problem solving"
        }
    )


@router.post(
    "/supervisor",
    response_model=SupervisorResponse,
    status_code=status.HTTP_200_OK,
    summary="Process request with supervisor agent",
    description="Submit a request to the supervisor agent for processing through worker agents."
)
async def process_supervisor_request(
    request: SupervisorRequest,
    agent: SupervisorAgent = Depends(get_supervisor_agent)
) -> SupervisorResponse:
    """Process a request using the supervisor agent.
    
    Args:
        request: The supervisor request
        agent: The supervisor agent instance
        
    Returns:
        SupervisorResponse: The processing result
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing supervisor request: {request.message[:100]}...")
        
        # Process the request with supervisor agent
        result = await agent.process_request(
            message=request.message,
            session_id=request.session_id
        )
        
        logger.info("Supervisor request processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Supervisor processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supervisor processing failed: {str(e)}"
        )


@router.get(
    "/supervisor/health",
    response_model=AgentHealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Check supervisor agent health",
    description="Get the current health status of the supervisor agent and its worker agents."
)
async def get_supervisor_health(
    agent: SupervisorAgent = Depends(get_supervisor_agent)
) -> AgentHealthCheck:
    """Get the health status of the supervisor agent.
    
    Args:
        agent: The supervisor agent instance
        
    Returns:
        AgentHealthCheck: The health status
    """
    try:
        health_info = agent.health_check()
        
        return AgentHealthCheck(
            healthy=health_info.get('healthy', False),
            components=health_info.get('components', {}),
            error=health_info.get('error'),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Supervisor health check failed: {e}")
        return AgentHealthCheck(
            healthy=False,
            components={},
            error=str(e),
            timestamp=datetime.now()
        )


@router.post(
    "/gatekeeper/tools/add",
    status_code=status.HTTP_400_BAD_REQUEST,
    summary="Add tool to agent",
    description="Tool addition not supported in supervisor pattern."
)
async def add_tool(
    tool_request: ToolInvocationRequest,
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> JSONResponse:
    """Add a tool to the agent's registry.
    
    Args:
        tool_request: Tool information
        agent: The gatekeeper agent instance
        
    Returns:
        JSONResponse: Error response
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Dynamic tool addition not supported in supervisor pattern. Available agents: research_agent, math_agent"
    )


@router.get(
    "/gatekeeper/statistics",
    response_model=AgentStatistics,
    status_code=status.HTTP_200_OK,
    summary="Get agent usage statistics",
    description="Retrieve usage statistics and performance metrics for the gatekeeper agent."
)
async def get_statistics(
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> AgentStatistics:
    """Get agent usage statistics.
    
    Args:
        agent: The gatekeeper agent instance
        
    Returns:
        AgentStatistics: Usage statistics
    """
    # Supervisor pattern doesn't maintain persistent statistics
    return AgentStatistics(
        total_requests=0,
        successful_requests=0,
        failed_requests=0,
        average_processing_time=0.0,
        tools_executed=0,
        memory_usage={},
        uptime=0.0
    )


@router.post(
    "/gatekeeper/configure",
    status_code=status.HTTP_400_BAD_REQUEST,
    summary="Configure agent settings",
    description="Configuration not supported in supervisor pattern."
)
async def configure_agent(
    config: AgentConfiguration,
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> JSONResponse:
    """Configure the agent settings.
    
    Args:
        config: New configuration settings
        agent: The gatekeeper agent instance
        
    Returns:
        JSONResponse: Error response
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Dynamic configuration not supported in supervisor pattern. Configuration is set at initialization."
    )


@router.delete(
    "/gatekeeper/memory",
    status_code=status.HTTP_200_OK,
    summary="Clear agent memory",
    description="Clear the conversation memory for a specific session or all sessions."
)
async def clear_memory(
    session_id: Optional[str] = None,
    agent: GatekeeperAgent = Depends(get_gatekeeper_agent)
) -> JSONResponse:
    """Clear agent memory.
    
    Args:
        session_id: Optional session ID to clear specific session memory
        agent: The gatekeeper agent instance
        
    Returns:
        JSONResponse: Memory clear confirmation
    """
    # Supervisor pattern doesn't maintain persistent memory
    message = "Supervisor agent uses stateless processing - no memory to clear"
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": message,
            "session_id": session_id
        }
    )