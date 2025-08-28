#!/usr/bin/env python3
"""
Workflow Manager for LangGraph workflows.

Simplified workflow management following official LangGraph documentation patterns.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Type

from core.logging import get_logger
from core.exceptions import (
    WorkflowException,
    WorkflowNotFoundException
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
from .base import BaseWorkflow, WorkflowState, WorkflowConfig
from .registry import WorkflowRegistry

logger = get_logger(__name__)


class WorkflowExecution:
    """Represents a workflow execution instance"""
    
    def __init__(
        self,
        execution_id: str,
        workflow: BaseWorkflow,
        input_data: Dict[str, Any],
        config: Optional[WorkflowConfig] = None
    ):
        self.execution_id = execution_id
        self.workflow = workflow
        self.input_data = input_data
        self.config = config or WorkflowConfig()
        self.state: Optional[WorkflowState] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = WorkflowStatus.PENDING
        self.error_message: Optional[str] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary"""
        return {
            "execution_id": self.execution_id,
            "workflow_name": self.workflow.name,
            "workflow_version": self.workflow.version,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "input_data": self.input_data,
            "output_data": self.state["output_data"] if self.state else {},
            "progress_percentage": self.state["progress_percentage"] if self.state else 0.0
        }


class WorkflowManager:
    """Manages workflow lifecycle and execution using official LangGraph patterns"""
    
    def __init__(self, max_concurrent_executions: int = 10):
        self.registry = WorkflowRegistry()
        self.executions: Dict[str, WorkflowExecution] = {}
        self.max_concurrent_executions = max_concurrent_executions
        self.logger = get_logger(f"{__name__}.WorkflowManager")
        
        # Statistics
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
    
    def register_workflow(
        self,
        workflow_class: Type[BaseWorkflow],
        config: Optional[WorkflowConfig] = None
    ) -> str:
        """Register a workflow class"""
        return self.registry.register(workflow_class, config)
    
    def unregister_workflow(self, workflow_name: str) -> bool:
        """Unregister a workflow"""
        return self.registry.unregister(workflow_name)
    
    def get_workflow(self, workflow_name: str) -> BaseWorkflow:
        """Get a workflow instance by name"""
        workflow = self.registry.get_workflow(workflow_name)
        if not workflow:
            raise WorkflowNotFoundException(workflow_name)
        return workflow
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows"""
        return self.registry.list_workflows()
    
    def create_workflow(
        self,
        request: WorkflowCreateRequest
    ) -> WorkflowResponse:
        """Create a new workflow configuration"""
        try:
            # Validate workflow exists
            workflow = self.get_workflow(request.name)
            
            # Create workflow configuration
            config = WorkflowConfig(
                timeout_seconds=request.timeout_seconds,
                max_retries=request.max_retries,
                enable_step_logging=request.enable_logging,
                custom_params=request.config or {}
            )
            
            # Update registry with new config
            workflow_id = self.registry.register(
                workflow.__class__,
                config
            )
            
            self.logger.info(
                f"Workflow created: {request.name}",
                extra={"workflow_id": workflow_id, "config": config.to_dict()}
            )
            
            return WorkflowResponse(
                id=workflow_id,
                name=workflow.name,
                description=workflow.description,
                version=workflow.version,
                status=WorkflowStatus.PENDING,
                config=config.to_dict(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {str(e)}")
            raise WorkflowException(f"Workflow creation failed: {str(e)}")
    

    
    def execute_workflow(
        self,
        request: WorkflowExecuteRequest
    ) -> WorkflowExecutionResponse:
        """Execute a workflow using official LangGraph invoke method"""
        try:
            # Get workflow
            workflow = self.get_workflow(request.workflow_name)
            
            # Validate input
            if not workflow.validate_input(request.input_data):
                raise WorkflowException("Invalid input data for workflow")
            
            # Create execution
            execution_id = request.execution_id or f"exec_{uuid.uuid4().hex[:12]}"
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow=workflow,
                input_data=request.input_data,
                config=request.config
            )
            
            # Check concurrent execution limit
            active_executions = sum(
                1 for exec in self.executions.values()
                if exec.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]
            )
            
            if active_executions >= self.max_concurrent_executions:
                raise WorkflowException(
                    f"Maximum concurrent executions ({self.max_concurrent_executions}) reached"
                )
            
            # Store execution
            self.executions[execution_id] = execution
            
            # Execute workflow
            execution.started_at = datetime.utcnow()
            execution.status = WorkflowStatus.RUNNING
            
            self.logger.info(
                f"Starting workflow execution: {request.workflow_name}",
                extra={
                    "execution_id": execution_id,
                    "workflow_name": request.workflow_name
                }
            )
            
            try:
                # Execute the workflow using official invoke method
                result_state = workflow.execute(
                    request.input_data,
                    execution_id
                )
                
                # Update execution
                execution.state = result_state
                execution.completed_at = datetime.utcnow()
                execution.status = WorkflowStatus(result_state["status"])
                
                if execution.status == WorkflowStatus.FAILED:
                    execution.error_message = result_state.get("error_message")
                    self._failed_executions += 1
                else:
                    self._successful_executions += 1
                
                self._total_executions += 1
                
                self.logger.info(
                    f"Workflow execution completed: {request.workflow_name}",
                    extra={
                        "execution_id": execution_id,
                        "status": execution.status.value,
                        "duration_seconds": (
                            execution.completed_at - execution.started_at
                        ).total_seconds()
                    }
                )
                
                return WorkflowExecutionResponse(
                    execution_id=execution_id,
                    workflow_name=request.workflow_name,
                    status=execution.status,
                    input_data=request.input_data,
                    output_data=result_state.get("output_data", {}),
                    error_message=execution.error_message,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    progress_percentage=result_state.get("progress_percentage", 100.0),
                    steps=workflow.get_workflow_steps(result_state)
                )
                
            except Exception as e:
                execution.completed_at = datetime.utcnow()
                execution.status = WorkflowStatus.FAILED
                execution.error_message = str(e)
                self._failed_executions += 1
                self._total_executions += 1
                
                self.logger.error(
                    f"Workflow execution failed: {request.workflow_name}",
                    extra={
                        "execution_id": execution_id,
                        "error": str(e)
                    }
                )
                
                raise WorkflowException(f"Workflow execution failed: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Failed to execute workflow: {str(e)}")
            raise
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self.executions.get(execution_id)
    
    def list_executions(
        self,
        workflow_name: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List workflow executions with filtering"""
        executions = list(self.executions.values())
        
        # Apply filters
        if workflow_name:
            executions = [
                exec for exec in executions
                if exec.workflow.name == workflow_name
            ]
        
        if status:
            executions = [
                exec for exec in executions
                if exec.status == status
            ]
        
        # Sort by started_at (most recent first)
        executions.sort(
            key=lambda x: x.started_at or datetime.min,
            reverse=True
        )
        
        # Apply pagination
        executions = executions[offset:offset + limit]
        
        return [exec.to_dict() for exec in executions]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        if execution.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            execution.error_message = "Execution cancelled by user"
            
            self.logger.info(
                f"Execution cancelled: {execution_id}",
                extra={"execution_id": execution_id}
            )
            return True
        
        return False
    
    def cleanup_executions(self, older_than_hours: int = 24) -> int:
        """Clean up old executions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        executions_to_remove = [
            exec_id for exec_id, execution in self.executions.items()
            if execution.completed_at and execution.completed_at < cutoff_time
        ]
        
        for exec_id in executions_to_remove:
            del self.executions[exec_id]
        
        self.logger.info(
            f"Cleaned up {len(executions_to_remove)} old executions",
            extra={"cutoff_hours": older_than_hours}
        )
        
        return len(executions_to_remove)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        active_executions = sum(
            1 for exec in self.executions.values()
            if exec.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]
        )
        
        return {
            "total_executions": self._total_executions,
            "successful_executions": self._successful_executions,
            "failed_executions": self._failed_executions,
            "success_rate": (
                self._successful_executions / self._total_executions * 100
                if self._total_executions > 0 else 0
            ),
            "active_executions": active_executions,
            "registered_workflows": len(self.registry.list_workflows()),
            "max_concurrent_executions": self.max_concurrent_executions
        }
    
    def get_workflow_list_response(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> WorkflowListResponse:
        """Get paginated workflow list response"""
        workflows = self.list_workflows()
        total = len(workflows)
        
        # Apply pagination
        paginated_workflows = workflows[offset:offset + limit]
        
        workflow_responses = []
        for workflow_info in paginated_workflows:
            workflow_responses.append(
                WorkflowResponse(
                    id=workflow_info["id"],
                    name=workflow_info["name"],
                    description=workflow_info["description"],
                    version=workflow_info["version"],
                    status=WorkflowStatus.PENDING,  # Default status
                    config=workflow_info.get("config", {}),
                    created_at=datetime.utcnow(),  # This should be actual creation time
                    updated_at=datetime.utcnow()
                )
            )
        
        return WorkflowListResponse(
            workflows=workflow_responses,
            total=total,
            limit=limit,
            offset=offset
        )