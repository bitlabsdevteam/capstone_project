#!/usr/bin/env python3
"""
Workflow Registry Module

This module provides the WorkflowRegistry class for registering and managing
workflow types and instances.
"""

import uuid
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from core.logging import get_logger
from core.exceptions import WorkflowNotFoundException
from models.workflow import WorkflowResponse, WorkflowStatus

logger = get_logger(__name__)


class WorkflowRegistry:
    """Registry for workflow types and instances"""
    
    def __init__(self):
        """Initialize the workflow registry"""
        self._workflow_types = {}
        self._workflow_instances = {}
        self._workflow_instances_by_name = {}
    
    def register_workflow_type(self, name: str, workflow_class: Any) -> None:
        """Register a workflow type"""
        self._workflow_types[name] = workflow_class
        logger.info(f"Registered workflow type: {name}")
    
    def get_workflow_types(self) -> List[str]:
        """Get list of registered workflow types"""
        return list(self._workflow_types.keys())
    
    def get_workflow_class(self, workflow_type: str) -> Any:
        """Get workflow class by type"""
        if workflow_type not in self._workflow_types:
            raise WorkflowNotFoundException(f"Workflow type not found: {workflow_type}")
        return self._workflow_types[workflow_type]
    
    def register_workflow_instance(self, workflow: WorkflowResponse) -> None:
        """Register a workflow instance"""
        self._workflow_instances[workflow.id] = workflow
        self._workflow_instances_by_name[workflow.name] = workflow
        logger.info(f"Registered workflow instance: {workflow.name} (ID: {workflow.id})")
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Get workflow instance by ID"""
        return self._workflow_instances.get(workflow_id)
    
    def get_workflow_by_name(self, workflow_name: str) -> Optional[WorkflowResponse]:
        """Get workflow instance by name"""
        return self._workflow_instances_by_name.get(workflow_name)
    
    def get_all_workflows(self) -> List[WorkflowResponse]:
        """Get all registered workflow instances"""
        return list(self._workflow_instances.values())
    
    def update_workflow(self, workflow: WorkflowResponse) -> None:
        """Update a workflow instance"""
        if workflow.id not in self._workflow_instances:
            raise WorkflowNotFoundException(f"Workflow not found: {workflow.id}")
        
        self._workflow_instances[workflow.id] = workflow
        self._workflow_instances_by_name[workflow.name] = workflow
        logger.info(f"Updated workflow: {workflow.name} (ID: {workflow.id})")
    
    def delete_workflow(self, workflow_id: str) -> None:
        """Delete a workflow instance"""
        if workflow_id not in self._workflow_instances:
            raise WorkflowNotFoundException(f"Workflow not found: {workflow_id}")
        
        workflow = self._workflow_instances[workflow_id]
        del self._workflow_instances[workflow_id]
        del self._workflow_instances_by_name[workflow.name]
        logger.info(f"Deleted workflow: {workflow.name} (ID: {workflow_id})")


# ============================================================================
# Global Registry Functions
# ============================================================================

# Global registry instance
_workflow_registry = None


def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry instance"""
    global _workflow_registry
    if _workflow_registry is None:
        _workflow_registry = WorkflowRegistry()
    return _workflow_registry


def register_default_workflows() -> None:
    """Register default workflow types with the registry"""
    registry = get_workflow_registry()
    
    # Import workflow classes here to avoid circular imports
    try:
        from .workflow import SupervisorFrontendWorkflow
        registry.register_workflow_type("supervisor_frontend_workflow", SupervisorFrontendWorkflow)
        logger.info("Registered default workflow: supervisor_frontend_workflow")
    except ImportError as e:
        logger.warning(f"Could not register supervisor_frontend_workflow: {e}")
    
    logger.info("Default workflows registration completed")


def initialize_workflow_system() -> None:
    """Initialize the workflow system with default workflows"""
    logger.info("Initializing workflow system...")
    register_default_workflows()
    logger.info("Workflow system initialized successfully")


def get_workflow_registry_info() -> Dict[str, Any]:
    """Get information about the workflow registry"""
    registry = get_workflow_registry()
    return {
        "workflow_types": registry.get_workflow_types(),
        "total_instances": len(registry.get_all_workflows()),
        "registry_status": "active"
    }