#!/usr/bin/env python3
"""
Consolidated Workflow Implementation

This module provides a unified implementation of workflow functionality,
combining features from base, gatekeeper, supervisor_frontend, manager, and registry modules.
Follows LangGraph best practices for workflow management and execution.
"""

import uuid
import logging
import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, TypedDict, Literal, AsyncGenerator
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.tools import Tool
from langchain_core.callbacks import AsyncCallbackHandler

from core.logging import get_logger
from core.exceptions import WorkflowException, WorkflowError, WorkflowNotFoundException
from core.config import get_settings
from core.streaming import StreamingCallbackHandler, stream_manager
from models.workflow import WorkflowStatus, WorkflowStep, WorkflowStepStatus
from models.workflow import (
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse
)
from models.streaming import (
    StreamEventType,
    WorkflowStartEvent,
    WorkflowCompleteEvent,
    WorkflowErrorEvent,
    TokenChunkEvent,
    LLMTokenEvent
)
from agents.supervisor_agent import GatekeeperAgent

logger = get_logger(__name__)
settings = get_settings()


# ============================================================================
# Base Workflow Classes
# ============================================================================

class WorkflowState(TypedDict):
    """State schema for LangGraph workflows following official documentation patterns"""
    workflow_id: str
    execution_id: str
    status: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    current_step: Optional[str]
    completed_steps: List[str]
    failed_steps: List[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    progress_percentage: float
    config: Dict[str, Any]
    context: Dict[str, Any]


class WorkflowConfig:
    """Configuration for workflow execution"""
    
    def __init__(
        self,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        max_concurrent_steps: int = 1,
        enable_parallel_execution: bool = False,
        enable_step_logging: bool = True,
        log_level: str = "INFO",
        fail_fast: bool = True,
        continue_on_error: bool = False,
        custom_params: Optional[Dict[str, Any]] = None
    ):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.max_concurrent_steps = max_concurrent_steps
        self.enable_parallel_execution = enable_parallel_execution
        self.enable_step_logging = enable_step_logging
        self.log_level = log_level
        self.fail_fast = fail_fast
        self.continue_on_error = continue_on_error
        self.custom_params = custom_params or {}
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a custom parameter."""
        return self.custom_params.get(key, default)
    
    def set_param(self, key: str, value: Any) -> None:
        """Set a custom parameter."""
        self.custom_params[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "max_concurrent_steps": self.max_concurrent_steps,
            "enable_parallel_execution": self.enable_parallel_execution,
            "enable_step_logging": self.enable_step_logging,
            "log_level": self.log_level,
            "fail_fast": self.fail_fast,
            "continue_on_error": self.continue_on_error,
            "custom_params": self.custom_params
        }


class BaseWorkflow(ABC):
    """Base class for LangGraph workflows following official documentation patterns"""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        self.graph: Optional[StateGraph] = None
        self.compiled_graph = None
        self._nodes: Dict[str, callable] = {}
        
        # Initialize the workflow
        self._initialize_workflow()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Workflow name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Workflow description."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Workflow version."""
        pass
    
    @abstractmethod
    def define_nodes(self) -> Dict[str, callable]:
        """Define workflow nodes - must return dict of node_name: node_function"""
        pass
    
    @abstractmethod
    def define_edges(self, graph: StateGraph) -> None:
        """Define workflow edges using official LangGraph methods"""
        pass
    
    def _initialize_workflow(self) -> None:
        """Initialize the workflow graph using official LangGraph patterns"""
        try:
            # Create StateGraph with WorkflowState schema
            self.graph = StateGraph(WorkflowState)
            
            # Add nodes using official add_node method
            self._nodes = self.define_nodes()
            for node_name, node_function in self._nodes.items():
                self.graph.add_node(node_name, node_function)
            
            # Define edges using official methods
            self.define_edges(self.graph)
            
            # Compile the graph
            self.compiled_graph = self.graph.compile()
            
            logger.info(f"Initialized workflow: {self.name} v{self.version}")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow {self.name}: {str(e)}")
            raise WorkflowException(f"Workflow initialization failed: {str(e)}")
    
    def get_initial_state(self, input_data: Dict[str, Any], execution_id: Optional[str] = None) -> WorkflowState:
        """Get initial workflow state"""
        now = datetime.utcnow().isoformat()
        return {
            "workflow_id": f"wf_{uuid.uuid4().hex[:12]}",
            "execution_id": execution_id or f"exec_{uuid.uuid4().hex[:12]}",
            "status": WorkflowStatus.PENDING.value,
            "input_data": input_data,
            "output_data": {},
            "current_step": None,
            "completed_steps": [],
            "failed_steps": [],
            "started_at": now,
            "completed_at": None,
            "error_message": None,
            "progress_percentage": 0.0,
            "config": self.config.to_dict(),
            "context": {}
        }
    
    def execute(
        self,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> WorkflowState:
        """Execute the workflow using official LangGraph invoke method"""
        if not self.compiled_graph:
            raise WorkflowException("Workflow not initialized")
        
        # Create initial state
        state = self.get_initial_state(input_data, execution_id)
        
        logger.info(
            f"Starting workflow execution: {self.name}",
            extra={
                "workflow_name": self.name,
                "execution_id": state["execution_id"],
                "input_data_keys": list(input_data.keys())
            }
        )
        
        try:
            # Update status to running
            state["status"] = WorkflowStatus.RUNNING.value
            
            # Execute using official invoke method
            result = self.compiled_graph.invoke(state)
            
            # Update final status
            result["status"] = WorkflowStatus.COMPLETED.value
            result["completed_at"] = datetime.utcnow().isoformat()
            result["progress_percentage"] = 100.0
            
            logger.info(
                f"Workflow execution completed: {self.name}",
                extra={
                    "workflow_name": self.name,
                    "execution_id": result["execution_id"]
                }
            )
            
            return result
            
        except Exception as e:
            state["status"] = WorkflowStatus.FAILED.value
            state["error_message"] = str(e)
            state["completed_at"] = datetime.utcnow().isoformat()
            
            logger.error(
                f"Workflow execution failed: {self.name}",
                extra={
                    "workflow_name": self.name,
                    "execution_id": state["execution_id"],
                    "error": str(e)
                }
            )
            
            if not self.config.continue_on_error:
                raise WorkflowException(f"Workflow execution failed: {str(e)}")
            
            return state
    
    async def astream(
        self,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None,
        stream_mode: str = "values",
        enable_token_streaming: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the workflow with async streaming support.
        
        This method implements LangGraph's async streaming patterns for real-time
        token responses and intermediate state updates.
        
        Args:
            input_data: Input data for workflow execution
            execution_id: Optional execution identifier
            stream_mode: Streaming mode ('values', 'updates', 'messages', 'debug')
            enable_token_streaming: Whether to enable LLM token streaming
            
        Yields:
            Streaming updates from workflow execution
            
        Raises:
            WorkflowException: If execution fails
        """
        if not self.compiled_graph:
            raise WorkflowException("Workflow not initialized")
        
        # Setup streaming callback if token streaming is enabled
        streaming_callback = None
        if enable_token_streaming:
            streaming_callback = StreamingCallbackHandler(
                event_emitter=stream_manager.emit_event
            )
            
            # Set callback on workflow instance if it supports it
            if hasattr(self, '_current_streaming_callback'):
                self._current_streaming_callback = streaming_callback
        
        try:
            # Validate input data
            if not self.validate_input(input_data):
                raise WorkflowException(f"Invalid input data for workflow {self.name}")
            
            # Get initial state
            initial_state = self.get_initial_state(input_data, execution_id)
            
            logger.info(
                f"Starting async workflow execution: {self.name}",
                extra={
                    "workflow_name": self.name,
                    "execution_id": initial_state["execution_id"],
                    "stream_mode": stream_mode
                }
            )
            
            # Emit start event
            start_event = WorkflowStartEvent(
                type=StreamEventType.WORKFLOW_START,
                timestamp=datetime.utcnow().isoformat(),
                workflow_name=self.name,
                execution_id=initial_state["execution_id"],
                initial_state=input_data,
                stream_mode=stream_mode
            )
            yield start_event.dict()
            
            # Configure streaming options
            stream_config = {"stream_mode": stream_mode}
            if streaming_callback:
                stream_config["callbacks"] = [streaming_callback]
            
            # Stream workflow execution using LangGraph's astream
            async for chunk in self.compiled_graph.astream(
                initial_state,
                config=stream_config
            ):
                # Process and yield streaming chunk
                processed_chunk = await self._process_stream_chunk(chunk, stream_mode)
                if processed_chunk:
                    yield processed_chunk
            
            # Emit completion event
            completion_event = WorkflowCompleteEvent(
                type=StreamEventType.WORKFLOW_COMPLETE,
                timestamp=datetime.utcnow().isoformat(),
                workflow_name=self.name,
                execution_id=initial_state["execution_id"],
                status="completed"
            )
            yield completion_event.dict()
            
            logger.info(
                f"Async workflow execution completed: {self.name}",
                extra={
                    "workflow_name": self.name,
                    "execution_id": initial_state["execution_id"]
                }
            )
            
        except Exception as e:
            logger.error(
                f"Async workflow execution failed: {self.name} - {str(e)}",
                extra={
                    "workflow_name": self.name,
                    "execution_id": execution_id,
                    "error": str(e)
                }
            )
            
            # Emit error event
            error_event = WorkflowErrorEvent(
                type=StreamEventType.WORKFLOW_ERROR,
                timestamp=datetime.utcnow().isoformat(),
                workflow_name=self.name,
                execution_id=execution_id or "unknown",
                error=str(e),
                status="failed"
            )
            yield error_event.dict()
            
        finally:
            # Clean up streaming callback
            if hasattr(self, '_current_streaming_callback'):
                self._current_streaming_callback = None
    
    async def _process_stream_chunk(
        self,
        chunk: Any,
        stream_mode: str
    ) -> Optional[Dict[str, Any]]:
        """Process streaming chunk based on LangGraph patterns.
        
        Args:
            chunk: Raw chunk from LangGraph stream
            stream_mode: Current streaming mode
            
        Returns:
            Processed chunk for client consumption
        """
        try:
            if stream_mode == "values":
                # Stream complete state values
                return {
                    "type": "state_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": chunk,
                    "stream_mode": stream_mode
                }
            
            elif stream_mode == "updates":
                # Stream only state updates/changes
                return {
                    "type": "state_delta",
                    "timestamp": datetime.utcnow().isoformat(),
                    "updates": chunk,
                    "stream_mode": stream_mode
                }
            
            elif stream_mode == "messages":
                # Stream message updates for conversational workflows
                return {
                    "type": "message_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "messages": chunk,
                    "stream_mode": stream_mode
                }
            
            elif stream_mode == "debug":
                # Stream debug information
                return {
                    "type": "debug_info",
                    "timestamp": datetime.utcnow().isoformat(),
                    "debug_data": chunk,
                    "stream_mode": stream_mode
                }
            
            else:
                # Default processing
                return {
                    "type": "chunk",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": chunk,
                    "stream_mode": stream_mode
                }
                
        except Exception as e:
            logger.warning(f"Failed to process stream chunk: {str(e)}")
            return None
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the workflow."""
        # Override in subclasses for custom validation
        return True
    
    def get_step_status(self, state: WorkflowState) -> List[WorkflowStep]:
        """Get status of all workflow steps."""
        steps = []
        
        for step_name in self._nodes.keys():
            if step_name in state["completed_steps"]:
                status = WorkflowStepStatus.COMPLETED
            elif step_name in state["failed_steps"]:
                status = WorkflowStepStatus.FAILED
            elif step_name == state["current_step"]:
                status = WorkflowStepStatus.RUNNING
            else:
                status = WorkflowStepStatus.PENDING
            
            steps.append(WorkflowStep(
                step_id=step_name,
                name=step_name.replace('_', ' ').title(),
                status=status
            ))
        
        return steps
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow information"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "graph_built": self.graph is not None,
            "compiled": self.compiled_graph is not None,
            "nodes": list(self._nodes.keys())
        }
    
    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}')>"


# ============================================================================
# Gatekeeper Workflow Implementation
# ============================================================================

class GatekeeperWorkflowState(TypedDict):
    """State for the gatekeeper workflow."""
    user_input: str
    context: Dict[str, Any]
    session_id: str
    execution_id: str
    agent_response: Optional[Dict[str, Any]]
    tool_results: Dict[str, Any]
    processing_history: List[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]
    messages: List[BaseMessage]
    current_step: str
    completed: bool


class GatekeeperWorkflow(BaseWorkflow):
    """Workflow wrapper for the gatekeeper agent.
    
    This workflow integrates the gatekeeper agent with the LangGraph workflow system,
    providing a standardized interface for agent execution within workflows.
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the gatekeeper workflow.
        
        Args:
            config: Optional workflow configuration
        """
        super().__init__(config or WorkflowConfig())
        
        # Initialize the gatekeeper agent
        try:
            self.agent = GatekeeperAgent()
            logger.info("Gatekeeper agent initialized in workflow")
        except Exception as e:
            logger.error(f"Failed to initialize gatekeeper agent: {e}")
            raise WorkflowError(f"Agent initialization failed: {e}")
        
        # Build the workflow graph
        self._build_graph()
    
    @property
    def name(self) -> str:
        """Get the workflow name."""
        return "gatekeeper_workflow"
    
    @property
    def description(self) -> str:
        """Get the workflow description."""
        return "Workflow wrapper for the gatekeeper agent decision-making system"
    
    @property
    def version(self) -> str:
        """Get the workflow version."""
        return "1.0.0"
    
    def _build_graph(self) -> None:
        """Build the workflow graph."""
        try:
            # Create the state graph
            workflow = StateGraph(GatekeeperWorkflowState)
            
            # Add nodes
            workflow.add_node("initialize", self._initialize_node)
            workflow.add_node("process_request", self._process_request_node)
            workflow.add_node("execute_tools", self._execute_tools_node)
            workflow.add_node("finalize", self._finalize_node)
            workflow.add_node("handle_error", self._handle_error_node)
            
            # Set entry point
            workflow.set_entry_point("initialize")
            
            # Add edges
            workflow.add_edge("initialize", "process_request")
            workflow.add_conditional_edges(
                "process_request",
                self._should_execute_tools,
                {
                    "execute_tools": "execute_tools",
                    "finalize": "finalize",
                    "error": "handle_error"
                }
            )
            workflow.add_edge("execute_tools", "finalize")
            workflow.add_edge("finalize", END)
            workflow.add_edge("handle_error", END)
            
            # Compile the graph
            self.graph = workflow.compile()
            logger.info("Gatekeeper workflow graph built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build workflow graph: {e}")
            raise WorkflowError(f"Graph building failed: {e}")
    
    async def _initialize_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Initialize the workflow state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Initializing gatekeeper workflow for execution {state.get('execution_id')}")
        
        # Add initialization message
        messages = state.get('messages', [])
        messages.append(HumanMessage(content=state['user_input']))
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "initialize",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "details": {
                "input_length": len(state['user_input']),
                "context_keys": list(state.get('context', {}).keys())
            }
        })
        
        return {
            **state,
            "messages": messages,
            "processing_history": processing_history,
            "current_step": "initialize",
            "metadata": {
                **state.get('metadata', {}),
                "initialized_at": datetime.now().isoformat()
            }
        }
    
    async def _process_request_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Process the request using the gatekeeper agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Processing request with gatekeeper agent for execution {state.get('execution_id')}")
        
        try:
            # Process the request with the agent
            result = await self.agent.process_request(
                user_input=state['user_input'],
                context=state.get('context', {}),
                session_id=state.get('session_id'),
                execution_id=state.get('execution_id')
            )
            
            # Add agent response message
            messages = state.get('messages', [])
            if result.get('agent_response'):
                agent_resp = result['agent_response']
                messages.append(AIMessage(
                    content=f"Decision: {agent_resp.get('decision', 'unknown')} - {agent_resp.get('reasoning', 'No reasoning provided')}"
                ))
            
            # Update processing history
            processing_history = state.get('processing_history', [])
            processing_history.append({
                "step": "process_request",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "details": {
                    "decision": result.get('agent_response', {}).get('decision'),
                    "confidence": result.get('agent_response', {}).get('confidence'),
                    "tools_recommended": len(result.get('agent_response', {}).get('next_actions', []))
                }
            })
            
            return {
                **state,
                "agent_response": result.get('agent_response'),
                "tool_results": result.get('tool_results', {}),
                "messages": messages,
                "processing_history": processing_history,
                "current_step": "process_request"
            }
            
        except Exception as e:
            logger.error(f"Error in process_request node: {e}")
            return {
                **state,
                "error": str(e),
                "current_step": "process_request"
            }
    
    def _should_execute_tools(self, state: GatekeeperWorkflowState) -> str:
        """Determine the next node based on agent response.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if state.get('error'):
            return "error"
        
        agent_response = state.get('agent_response', {})
        next_actions = agent_response.get('next_actions', [])
        
        if next_actions and len(next_actions) > 0:
            return "execute_tools"
        
        return "finalize"
    
    async def _execute_tools_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Execute tools recommended by the agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Executing tools for execution {state.get('execution_id')}")
        
        agent_response = state.get('agent_response', {})
        next_actions = agent_response.get('next_actions', [])
        tool_results = state.get('tool_results', {})
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "execute_tools",
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "details": {
                "tools_to_execute": len(next_actions)
            }
        })
        
        try:
            # Execute each tool
            for action in next_actions:
                tool_name = action.get('tool')
                tool_input = action.get('input', {})
                
                # Execute tool (placeholder for actual tool execution)
                tool_result = {
                    "status": "success",
                    "result": f"Executed {tool_name} with input {tool_input}",
                    "timestamp": datetime.now().isoformat()
                }
                
                tool_results[tool_name] = tool_result
            
            # Update processing history
            processing_history[-1].update({
                "status": "completed",
                "details": {
                    **processing_history[-1]["details"],
                    "tools_executed": len(tool_results)
                }
            })
            
            return {
                **state,
                "tool_results": tool_results,
                "processing_history": processing_history,
                "current_step": "execute_tools"
            }
            
        except Exception as e:
            logger.error(f"Error in execute_tools node: {e}")
            
            # Update processing history
            processing_history[-1].update({
                "status": "failed",
                "details": {
                    **processing_history[-1]["details"],
                    "error": str(e)
                }
            })
            
            return {
                **state,
                "error": str(e),
                "processing_history": processing_history,
                "current_step": "execute_tools"
            }
    
    async def _finalize_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Finalize the workflow execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Finalizing gatekeeper workflow for execution {state.get('execution_id')}")
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "finalize",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "details": {
                "agent_decision": state.get('agent_response', {}).get('decision'),
                "tools_executed": len(state.get('tool_results', {}))
            }
        })
        
        return {
            **state,
            "processing_history": processing_history,
            "current_step": "finalize",
            "completed": True,
            "metadata": {
                **state.get('metadata', {}),
                "completed_at": datetime.now().isoformat()
            }
        }
    
    async def _handle_error_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Handle workflow errors.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.error(f"Error in gatekeeper workflow: {state.get('error')}")
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "handle_error",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "details": {
                "error": state.get('error')
            }
        })
        
        return {
            **state,
            "processing_history": processing_history,
            "current_step": "handle_error",
            "completed": True,
            "metadata": {
                **state.get('metadata', {}),
                "error_at": datetime.now().isoformat()
            }
        }
    
    def define_nodes(self) -> Dict[str, callable]:
        """Define workflow nodes."""
        return {
            "initialize": self._initialize_node,
            "process_request": self._process_request_node,
            "execute_tools": self._execute_tools_node,
            "finalize": self._finalize_node,
            "handle_error": self._handle_error_node
        }
    
    def define_edges(self, graph: StateGraph) -> None:
        """Define workflow edges."""
        graph.add_edge("initialize", "process_request")
        graph.add_conditional_edges(
            "process_request",
            self._should_execute_tools,
            {
                "execute_tools": "execute_tools",
                "finalize": "finalize",
                "error": "handle_error"
            }
        )
        graph.add_edge("execute_tools", "finalize")
        graph.add_edge("finalize", END)
        graph.add_edge("handle_error", END)


# ============================================================================
# Supervisor Frontend Workflow Implementation
# ============================================================================

class SupervisorFrontendState(MessagesState):
    """State schema for supervisor-frontend workflow following LangGraph patterns.
    
    Extends MessagesState to include workflow-specific state management
    for supervisor and frontend_agent coordination.
    """
    # Core workflow state
    workflow_id: str
    execution_id: str
    current_node: Optional[str]
    
    # Agent coordination state
    supervisor_decision: Optional[str]
    frontend_task: Optional[Dict[str, Any]]
    chart_data: Optional[Dict[str, Any]]
    
    # Processing metadata
    processing_history: List[Dict[str, Any]]
    error_message: Optional[str]
    completed: bool
    
    # Context and configuration
    context: Dict[str, Any]
    config: Dict[str, Any]


class SupervisorFrontendWorkflow(BaseWorkflow):
    """Supervisor-Frontend workflow implementation.
    
    This workflow implements a supervisor pattern where:
    - supervisor node: Orchestrates tasks and makes routing decisions
    - frontend_agent node: Handles chart generation and frontend tasks
    - End node: Terminates workflow execution
    
    Follows LangGraph best practices for:
    - State management with MessagesState extension
    - Conditional routing using Command objects
    - Proper node initialization and state passing
    - Industry-standard supervisor pattern architecture
    """
    
    name = "supervisor_frontend_workflow"
    description = "Supervisor-coordinated workflow for frontend chart generation"
    version = "1.0.0"
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the supervisor-frontend workflow.
        
        Args:
            config: Optional workflow configuration
        """
        super().__init__(config or WorkflowConfig())
        
        # Initialize LLM for supervisor decisions
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            streaming=True,  # Enable streaming for real-time responses
            max_tokens=2000,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Streaming callback handler for token events
        self._current_streaming_callback = None
        
        # Initialize search tool for research capabilities
        if settings.TAVILY_API_KEY:
            self.search = TavilySearchAPIWrapper(
                api_key=settings.TAVILY_API_KEY
            )
            self.search_tool = Tool(
                name="tavily_search",
                description="Search the web for information",
                func=self.search.run
            )
        else:
            self.search = None
            self.search_tool = None
            logger.warning("TAVILY_API_KEY not set, search functionality disabled")
    
    def define_nodes(self) -> Dict[str, callable]:
        """Define workflow nodes."""
        return {
            "supervisor": self._supervisor_node,
            "frontend_agent": self._frontend_agent_node,
            "human_in_loop": self._human_in_loop_node
        }
    
    def define_edges(self, graph: StateGraph) -> None:
        """Define workflow edges."""
        # Set entry point
        graph.set_entry_point("supervisor")
        
        # Define conditional routing based on supervisor decisions
        graph.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "frontend_agent": "frontend_agent",
                "human_in_loop": "human_in_loop",
                "end": END
            }
        )
        
        # Define edges from other nodes
        graph.add_conditional_edges(
            "frontend_agent",
            self._route_from_frontend_agent,
            {
                "supervisor": "supervisor",
                "end": END
            }
        )
        
        graph.add_conditional_edges(
            "human_in_loop",
            self._route_from_human_in_loop,
            {
                "supervisor": "supervisor",
                "frontend_agent": "frontend_agent",
                "end": END
            }
        )
    
    def get_initial_state(self, input_data: Dict[str, Any], execution_id: Optional[str] = None) -> SupervisorFrontendState:
        """Get initial workflow state with proper message initialization.
        
        Args:
            input_data: Input data containing user_prompt and optional context
            execution_id: Optional execution ID
            
        Returns:
            Initial SupervisorFrontendState with user prompt converted to HumanMessage
        """
        now = datetime.utcnow().isoformat()
        
        # Extract user prompt from input data
        user_prompt = input_data.get('user_prompt', '')
        if not user_prompt:
            raise WorkflowException("user_prompt is required in input_data")
        
        # Create initial messages with user prompt
        initial_messages = [HumanMessage(content=user_prompt)]
        
        return SupervisorFrontendState(
            messages=initial_messages,
            workflow_id=f"wf_{uuid.uuid4().hex[:12]}",
            execution_id=execution_id or f"exec_{uuid.uuid4().hex[:12]}",
            current_node=None,
            supervisor_decision=None,
            frontend_task=None,
            chart_data=None,
            processing_history=[{
                "step": "initialization",
                "timestamp": now,
                "status": "completed",
                "details": {
                    "user_prompt_length": len(user_prompt),
                    "input_data_keys": list(input_data.keys())
                }
            }],
            error_message=None,
            completed=False,
            context=input_data.get('context', {}),
            config=self.config.to_dict()
        )
    
    async def _supervisor_node(self, state: SupervisorFrontendState) -> SupervisorFrontendState:
        """Supervisor node that orchestrates the workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Executing supervisor node for {state.get('execution_id', 'unknown')}")
        
        # Get the last message from the user
        last_user_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                last_user_message = message.content
                break
        
        if not last_user_message:
            return {
                **state,
                "supervisor_decision": "end",
                "error_message": "No user message found"
            }
        
        # Supervisor prompt
        supervisor_prompt = f"""
        You are a workflow supervisor that decides how to handle user requests.
        
        User request: {last_user_message}
        
        Based on this request, decide which path to take:
        1. If the request is for chart generation or data visualization, route to 'frontend_agent'
        2. If the request requires human intervention or clarification, route to 'human_in_loop'
        3. If the request is complete or cannot be handled, route to 'end'
        
        Respond with a JSON object containing:
        - decision: The routing decision ('frontend_agent', 'human_in_loop', or 'end')
        - reasoning: Brief explanation for your decision
        - next_steps: Suggested actions for the next agent
        """
        
        try:
            # Get supervisor decision
            response = await self.llm.ainvoke([HumanMessage(content=supervisor_prompt)])
            response_content = response.content
            
            # Parse JSON response
            try:
                decision_data = json.loads(response_content)
                decision = decision_data.get("decision", "end")
                reasoning = decision_data.get("reasoning", "No reasoning provided")
                next_steps = decision_data.get("next_steps", [])
            except json.JSONDecodeError:
                # Fallback parsing for non-JSON responses
                if "frontend_agent" in response_content.lower():
                    decision = "frontend_agent"
                elif "human_in_loop" in response_content.lower():
                    decision = "human_in_loop"
                else:
                    decision = "end"
                reasoning = "Parsed from non-JSON response"
                next_steps = []
            
            # Update state with decision
            updated_state = {
                **state,
                "supervisor_decision": decision,
                "processing_history": state.get("processing_history", []) + [{
                    "node": "supervisor",
                    "timestamp": datetime.utcnow().isoformat(),
                    "decision": decision,
                    "reasoning": reasoning
                }]
            }
            
            # Add supervisor message to conversation
            messages = state["messages"].copy()
            messages.append(AIMessage(
                content=f"Supervisor decision: {decision} - {reasoning}"
            ))
            updated_state["messages"] = messages
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in supervisor node: {str(e)}")
            return {
                **state,
                "supervisor_decision": "end",
                "error_message": f"Supervisor error: {str(e)}"
            }
    
    async def _frontend_agent_node(self, state: SupervisorFrontendState) -> SupervisorFrontendState:
        """Frontend agent node that handles chart generation.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Executing frontend agent node for {state.get('execution_id', 'unknown')}")
        
        # Get the last message from the user
        last_user_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                last_user_message = message.content
                break
        
        if not last_user_message:
            return {
                **state,
                "error_message": "No user message found"
            }
        
        # Frontend agent prompt
        frontend_prompt = f"""
        You are a frontend chart generation agent. Generate a chart based on the user request.
        
        User request: {last_user_message}
        
        Respond with a JSON object containing:
        - chart_type: The type of chart to generate (bar, line, pie, etc.)
        - data: Sample data structure for the chart
        - config: Chart configuration options
        - next_action: What to do next ('complete' or 'ask_supervisor')
        """
        
        try:
            # Get frontend agent response
            response = await self.llm.ainvoke([HumanMessage(content=frontend_prompt)])
            response_content = response.content
            
            # Parse JSON response
            try:
                chart_data = json.loads(response_content)
                next_action = chart_data.get("next_action", "complete")
            except json.JSONDecodeError:
                # Fallback for non-JSON responses
                chart_data = {
                    "chart_type": "unknown",
                    "data": {},
                    "config": {},
                    "next_action": "complete"
                }
                next_action = "complete"
            
            # Update state with chart data
            updated_state = {
                **state,
                "chart_data": chart_data,
                "processing_history": state.get("processing_history", []) + [{
                    "node": "frontend_agent",
                    "timestamp": datetime.utcnow().isoformat(),
                    "chart_type": chart_data.get("chart_type"),
                    "next_action": next_action
                }]
            }
            
            # Add frontend agent message to conversation
            messages = state["messages"].copy()
            messages.append(AIMessage(
                content=f"Frontend agent generated a {chart_data.get('chart_type', 'unknown')} chart."
            ))
            updated_state["messages"] = messages
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in frontend agent node: {str(e)}")
            return {
                **state,
                "error_message": f"Frontend agent error: {str(e)}"
            }
    
    async def _human_in_loop_node(self, state: SupervisorFrontendState) -> SupervisorFrontendState:
        """Human-in-the-loop node for handling cases requiring human intervention.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Executing human-in-the-loop node for {state.get('execution_id', 'unknown')}")
        
        # In a real implementation, this would wait for human input
        # For this example, we'll simulate a human response
        
        # Add human-in-the-loop message to conversation
        messages = state["messages"].copy()
        messages.append(AIMessage(
            content="This request requires human intervention. Please provide more information."
        ))
        
        # Update state
        updated_state = {
            **state,
            "messages": messages,
            "processing_history": state.get("processing_history", []) + [{
                "node": "human_in_loop",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "awaiting_human_input"
            }]
        }
        
        # In this example, we'll route back to the supervisor
        # In a real implementation, this would depend on human input
        return updated_state
    
    def _route_from_supervisor(self, state: SupervisorFrontendState) -> str:
        """Determine routing from supervisor node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        decision = state.get("supervisor_decision", "end")
        
        # Log routing decision
        logger.info(f"Routing from supervisor: {decision}")
        
        # Return the decision directly as it maps to node names
        return decision
    
    def _route_from_frontend_agent(self, state: SupervisorFrontendState) -> str:
        """Determine routing from frontend agent node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        chart_data = state.get("chart_data", {})
        next_action = chart_data.get("next_action", "complete")
        
        if next_action == "ask_supervisor":
            return "supervisor"
        
        # Default to end
        return "end"
    
    def _route_from_human_in_loop(self, state: SupervisorFrontendState) -> str:
        """Determine routing from human-in-the-loop node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        # In a real implementation, this would depend on human input
        # For this example, we'll route back to the supervisor
        return "supervisor"


# ============================================================================
# Workflow System Initialization
# ============================================================================
    

    







    

    

    

            
# This section has been moved to manager.py as part of refactoring

# ============================================================================
# Workflow System Initialization
# ============================================================================

# These functions have been moved to registry.py as part of refactoring