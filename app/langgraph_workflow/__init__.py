"""LangGraph Workflow Module

This module provides a basic LangGraph workflow implementation that demonstrates
core functionality through minimal, self-contained examples.

Main Components:
- BasicLangGraphWorkflow: Main workflow class
- WorkflowState: State schema for workflow data
- create_basic_workflow: Factory function for workflow creation

Usage:
    from app.langgraph_workflow import create_basic_workflow
    
    workflow = create_basic_workflow()
    result = workflow.execute("Your text here")
"""

from .basic_workflow import (
    BasicLangGraphWorkflow,
    WorkflowState,
    create_basic_workflow
)

__version__ = "1.0.0"
__author__ = "Vizuara Project"
__description__ = "Basic LangGraph workflow implementation"

__all__ = [
    "BasicLangGraphWorkflow",
    "WorkflowState", 
    "create_basic_workflow"
]