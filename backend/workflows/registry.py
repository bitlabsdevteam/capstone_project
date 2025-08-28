"""Workflow Registry for LangGraph workflows.

Simplified workflow registration following official LangGraph documentation patterns.
"""

import uuid
from typing import Dict, Any, List, Optional, Type

from core.logging import get_logger
from .base import BaseWorkflow, WorkflowConfig

logger = get_logger(__name__)


class WorkflowRegistry:
    """Registry for managing workflow classes and configurations"""
    
    def __init__(self):
        self._workflows: Dict[str, Type[BaseWorkflow]] = {}
        self._configs: Dict[str, WorkflowConfig] = {}
        self._instances: Dict[str, BaseWorkflow] = {}
        self.logger = get_logger(f"{__name__}.WorkflowRegistry")
    

    
    def register(
        self,
        workflow_class: Type[BaseWorkflow],
        config: Optional[WorkflowConfig] = None
    ) -> str:
        """Register a workflow class"""
        if not issubclass(workflow_class, BaseWorkflow):
            raise ValueError(f"Workflow class must inherit from BaseWorkflow")
        
        # Create instance to get metadata
        temp_instance = workflow_class(config or WorkflowConfig())
        workflow_name = temp_instance.name
        
        # Generate unique ID
        workflow_id = f"{workflow_name}_{uuid.uuid4().hex[:8]}"
        
        # Store workflow class and config
        self._workflows[workflow_name] = workflow_class
        self._configs[workflow_name] = config or WorkflowConfig()
        
        # Create and store instance
        self._instances[workflow_name] = temp_instance
        
        self.logger.info(
            f"Registered workflow: {workflow_name}",
            extra={
                "workflow_id": workflow_id,
                "workflow_class": workflow_class.__name__
            }
        )
        
        return workflow_id
    
    def unregister(self, workflow_name: str) -> bool:
        """Unregister a workflow"""
        if workflow_name not in self._workflows:
            return False
        
        del self._workflows[workflow_name]
        del self._configs[workflow_name]
        del self._instances[workflow_name]
        
        self.logger.info(f"Unregistered workflow: {workflow_name}")
        return True
    
    def get_workflow(self, workflow_name: str) -> Optional[BaseWorkflow]:
        """Get a workflow instance by name"""
        if workflow_name not in self._instances:
            return None
        
        # Return a fresh instance with the registered config
        workflow_class = self._workflows[workflow_name]
        config = self._configs[workflow_name]
        
        return workflow_class(config)
    
    def get_workflow_class(self, workflow_name: str) -> Optional[Type[BaseWorkflow]]:
        """Get a workflow class by name"""
        return self._workflows.get(workflow_name)
    
    def get_config(self, workflow_name: str) -> Optional[WorkflowConfig]:
        """Get workflow configuration by name"""
        return self._configs.get(workflow_name)
    
    def is_registered(self, workflow_name: str) -> bool:
        """Check if a workflow is registered"""
        return workflow_name in self._workflows
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows"""
        workflows = []
        
        for workflow_name, workflow_class in self._workflows.items():
            instance = self._instances[workflow_name]
            config = self._configs[workflow_name]
            
            workflows.append({
                "id": f"{workflow_name}_{uuid.uuid4().hex[:8]}",
                "name": workflow_name,
                "description": instance.description,
                "version": instance.version,
                "class_name": workflow_class.__name__,
                "config": config.to_dict()
            })
        
        return workflows
    
    def get_workflow_names(self) -> List[str]:
        """Get list of registered workflow names"""
        return list(self._workflows.keys())
    
    def clear(self) -> None:
        """Clear all registered workflows"""
        self._workflows.clear()
        self._configs.clear()
        self._instances.clear()
        
        self.logger.info("Cleared all registered workflows")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_registered": len(self._workflows),
            "workflow_names": list(self._workflows.keys()),
            "workflow_classes": [cls.__name__ for cls in self._workflows.values()]
        }