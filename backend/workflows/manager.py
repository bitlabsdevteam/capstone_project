#!/usr/bin/env python3
"""
Workflow Manager Module

This module provides the WorkflowManager class for managing workflow instances,
including creation, execution, and status tracking.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.logging import get_logger
from core.exceptions import WorkflowException, WorkflowNotFoundException
from models.workflow import (
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowStatus
)

logger = get_logger(__name__)


class WorkflowManager:
    """Workflow Manager for handling workflow operations"""
    
    def __init__(self):
        """Initialize the workflow manager"""
        self.registry = None
    
    def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowResponse:
        """Create a new workflow instance"""
        if not self.registry:
            raise WorkflowException("Workflow registry not initialized")
        
        # Check if workflow type exists
        if request.workflow_type not in self.registry.get_workflow_types():
            raise WorkflowNotFoundException(f"Workflow type not found: {request.workflow_type}")
        
        # Generate a unique ID for the workflow
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        
        # Create workflow instance
        workflow = WorkflowResponse(
            id=workflow_id,
            name=request.name,
            description=request.description,
            workflow_type=request.workflow_type,
            status=WorkflowStatus.ACTIVE,
            is_active=True,
            execution_count=0,
            config=request.config or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_execution_at=None
        )
        
        # Store workflow in registry
        self.registry.register_workflow_instance(workflow)
        
        logger.info(f"Created workflow: {workflow.name} (ID: {workflow.id})")
        return workflow
    
    def get_workflow(self, workflow_name: str) -> WorkflowResponse:
        """Get workflow by name"""
        if not self.registry:
            raise WorkflowException("Workflow registry not initialized")
        
        workflow = self.registry.get_workflow_by_name(workflow_name)
        if not workflow:
            raise WorkflowNotFoundException(f"Workflow not found: {workflow_name}")
        
        return workflow
    
    def get_workflow_list_response(self, limit: int = 100, offset: int = 0) -> WorkflowListResponse:
        """Get paginated list of workflows"""
        if not self.registry:
            raise WorkflowException("Workflow registry not initialized")
        
        workflows = self.registry.get_all_workflows()
        
        # Apply pagination
        total_count = len(workflows)
        paginated_workflows = workflows[offset:offset + limit]
        
        # Calculate pagination metadata
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        return WorkflowListResponse(
            workflows=paginated_workflows,
            total_count=total_count,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    def execute_workflow(self, workflow_name: str, request: WorkflowExecuteRequest) -> WorkflowExecutionResponse:
        """Execute a workflow with the provided input data"""
        if not self.registry:
            raise WorkflowException("Workflow registry not initialized")
        
        # Get workflow instance from registry
        workflow_instance = self.registry.get_workflow(workflow_name)
        if not workflow_instance:
            raise WorkflowNotFoundException(f"Workflow '{workflow_name}' not found")
        
        # Generate execution ID
        execution_id = request.execution_id or f"exec_{uuid.uuid4().hex[:12]}"
        
        # Prepare input data with user prompt
        input_data = {
            'user_prompt': request.user_prompt,
            'execution_id': execution_id,
            'execution_mode': request.execution_mode.value,
            'timeout_seconds': request.timeout_seconds
        }
        
        # Add optional input_data if provided
        if request.input_data:
            input_data.update(request.input_data)
        
        # Create initial execution response
        execution = WorkflowExecutionResponse(
            id=execution_id,
            workflow_id=workflow_instance.id,
            status=WorkflowStatus.RUNNING,
            execution_mode=request.execution_mode,
            input_data=input_data,
            output_data=None,
            steps=[],
            started_at=datetime.now(),
            completed_at=None,
            progress_percentage=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        try:
            logger.info(f"Starting workflow execution: {workflow_name} (ID: {execution_id})")
            
            # Execute the workflow
            if request.execution_mode.value == 'sync':
                # Synchronous execution
                result = workflow_instance.execute(input_data, execution_id)
                
                # Update execution response with results
                execution.status = WorkflowStatus.COMPLETED if result.get('success', False) else WorkflowStatus.FAILED
                execution.output_data = result.get('output', {})
                execution.completed_at = datetime.now()
                execution.progress_percentage = 100.0
                execution.updated_at = datetime.now()
                
                # Add execution steps from workflow result
                if 'steps' in result:
                    execution.steps = result['steps']
                
                logger.info(f"Completed workflow execution: {workflow_name} (ID: {execution_id}) - Status: {execution.status}")
                
            else:
                # Asynchronous execution - start background task
                # For now, we'll mark it as running and return immediately
                # In a production system, this would use a task queue like Celery
                logger.info(f"Started async workflow execution: {workflow_name} (ID: {execution_id})")
                execution.progress_percentage = 10.0  # Initial progress
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {workflow_name} (ID: {execution_id}) - Error: {str(e)}")
            execution.status = WorkflowStatus.FAILED
            execution.output_data = {'error': str(e)}
            execution.completed_at = datetime.now()
            execution.updated_at = datetime.now()
            
            # Don't re-raise the exception, return the failed execution response
        
        return execution