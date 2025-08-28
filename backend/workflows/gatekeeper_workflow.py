"""Gatekeeper Agent Workflow Integration.

This module provides a workflow wrapper for the gatekeeper agent,
allowing it to be integrated with the existing LangGraph workflow system.
"""

import logging
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage

from agents.gatekeeper_agent import GatekeeperAgent, GatekeeperState
from workflows.base import BaseWorkflow, WorkflowConfig
from core.exceptions import WorkflowError

logger = logging.getLogger(__name__)


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
                "current_step": "process_request",
                "metadata": {
                    **state.get('metadata', {}),
                    "processed_at": datetime.now().isoformat(),
                    "agent_decision": result.get('agent_response', {}).get('decision')
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                **state,
                "error": str(e),
                "current_step": "process_request",
                "processing_history": state.get('processing_history', []) + [{
                    "step": "process_request",
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "details": {"error": str(e)}
                }]
            }
    
    async def _execute_tools_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Execute recommended tools.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Executing tools for execution {state.get('execution_id')}")
        
        agent_response = state.get('agent_response', {})
        next_actions = agent_response.get('next_actions', [])
        
        if not next_actions:
            logger.info("No tools to execute")
            return {
                **state,
                "current_step": "execute_tools",
                "processing_history": state.get('processing_history', []) + [{
                    "step": "execute_tools",
                    "timestamp": datetime.now().isoformat(),
                    "status": "skipped",
                    "details": {"reason": "No tools recommended"}
                }]
            }
        
        tool_results = {}
        
        for action in next_actions:
            tool_name = action.get('tool_name')
            if tool_name:
                try:
                    # Execute tool (placeholder - actual tool execution would be implemented here)
                    result = await self._execute_tool(tool_name, action.get('parameters', {}))
                    tool_results[tool_name] = result
                    logger.info(f"Tool '{tool_name}' executed successfully")
                except Exception as e:
                    logger.error(f"Tool '{tool_name}' execution failed: {e}")
                    tool_results[tool_name] = {
                        "success": False,
                        "error": str(e),
                        "executed_at": datetime.now().isoformat()
                    }
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "execute_tools",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "details": {
                "tools_executed": len(tool_results),
                "successful_tools": sum(1 for r in tool_results.values() if r.get('success', False)),
                "failed_tools": sum(1 for r in tool_results.values() if not r.get('success', True))
            }
        })
        
        return {
            **state,
            "tool_results": {**state.get('tool_results', {}), **tool_results},
            "processing_history": processing_history,
            "current_step": "execute_tools"
        }
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool (placeholder implementation).
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        # This is a placeholder implementation
        # In a real system, this would integrate with the actual tool registry
        logger.info(f"Executing tool '{tool_name}' with parameters: {parameters}")
        
        return {
            "success": True,
            "result": f"Tool '{tool_name}' executed successfully",
            "executed_at": datetime.now().isoformat(),
            "execution_time": 0.1
        }
    
    async def _finalize_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Finalize the workflow execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            Final workflow state
        """
        logger.info(f"Finalizing gatekeeper workflow for execution {state.get('execution_id')}")
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "finalize",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "details": {
                "total_steps": len(processing_history) + 1,
                "has_error": bool(state.get('error')),
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
                "completed_at": datetime.now().isoformat(),
                "total_processing_time": self._calculate_processing_time(processing_history)
            }
        }
    
    async def _handle_error_node(self, state: GatekeeperWorkflowState) -> GatekeeperWorkflowState:
        """Handle workflow errors.
        
        Args:
            state: Current workflow state
            
        Returns:
            Error-handled workflow state
        """
        logger.error(f"Handling error in gatekeeper workflow: {state.get('error')}")
        
        # Update processing history
        processing_history = state.get('processing_history', [])
        processing_history.append({
            "step": "handle_error",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "details": {
                "error": state.get('error'),
                "error_step": state.get('current_step')
            }
        })
        
        return {
            **state,
            "processing_history": processing_history,
            "current_step": "handle_error",
            "completed": True,
            "metadata": {
                **state.get('metadata', {}),
                "error_handled_at": datetime.now().isoformat()
            }
        }
    
    def _should_execute_tools(self, state: GatekeeperWorkflowState) -> str:
        """Determine if tools should be executed.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if state.get('error'):
            return "error"
        
        agent_response = state.get('agent_response', {})
        next_actions = agent_response.get('next_actions', [])
        
        if next_actions:
            return "execute_tools"
        else:
            return "finalize"
    
    def _calculate_processing_time(self, processing_history: List[Dict[str, Any]]) -> float:
        """Calculate total processing time from history.
        
        Args:
            processing_history: List of processing steps
            
        Returns:
            Total processing time in seconds
        """
        if not processing_history or len(processing_history) < 2:
            return 0.0
        
        try:
            start_time = datetime.fromisoformat(processing_history[0]['timestamp'])
            end_time = datetime.fromisoformat(processing_history[-1]['timestamp'])
            return (end_time - start_time).total_seconds()
        except (KeyError, ValueError, TypeError):
            return 0.0
    
    async def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the gatekeeper workflow.
        
        Args:
            user_input: User input to process
            context: Additional context
            session_id: Session identifier
            execution_id: Execution identifier
            **kwargs: Additional keyword arguments
            
        Returns:
            Workflow execution result
        """
        # Generate IDs if not provided
        if not execution_id:
            execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create initial state
        initial_state = GatekeeperWorkflowState(
            user_input=user_input,
            context=context or {},
            session_id=session_id,
            execution_id=execution_id,
            agent_response=None,
            tool_results={},
            processing_history=[],
            error=None,
            metadata={
                "started_at": datetime.now().isoformat(),
                "workflow_version": self.version
            },
            messages=[],
            current_step="",
            completed=False
        )
        
        try:
            # Execute the workflow
            logger.info(f"Starting gatekeeper workflow execution {execution_id}")
            result = await self.graph.ainvoke(initial_state)
            
            logger.info(f"Gatekeeper workflow execution {execution_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Gatekeeper workflow execution {execution_id} failed: {e}")
            raise WorkflowError(f"Workflow execution failed: {e}")