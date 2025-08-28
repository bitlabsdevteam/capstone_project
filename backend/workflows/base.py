#!/usr/bin/env python3
"""
Base Workflow Classes

Foundational classes for LangGraph workflow implementation
with state management and configuration following official documentation patterns.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from core.logging import get_logger
from core.exceptions import WorkflowException
from models.workflow import WorkflowStatus, WorkflowStep, WorkflowStepStatus

logger = get_logger(__name__)


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