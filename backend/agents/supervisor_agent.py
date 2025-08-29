"""Supervisor Agent for LangGraph Workflow Orchestration.

This module implements a supervisor agent using the langgraph_supervisor pattern
that manages worker agents for different tasks like research and information retrieval.

The implementation follows the supervisor pattern with:
- Worker agent integration
- Supervisor workflow orchestration
"""

import os
from typing import Any, Dict, List, Optional, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_supervisor import create_supervisor
from langgraph.graph import START, END
from pydantic import BaseModel, Field

from core.logging import get_logger
from core.exceptions import WorkflowException
from core.config import get_settings
from agents.research_agent import research_agent

logger = get_logger(__name__)
settings = get_settings()

# Initialize Gemini LLM (requires GEMINI_API_KEY environment variable)
if not settings.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0,
    google_api_key=settings.GEMINI_API_KEY
)
logger.info("Initialized Gemini LLM for supervisor workflow")


class SupervisorRequest(BaseModel):
    """Request model for supervisor agent."""
    message: str = Field(..., description="User message/query")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class SupervisorResponse(BaseModel):
    """Response model from supervisor agent."""
    messages: List[Dict[str, str]] = Field(..., description="Conversation messages")
    final_response: str = Field(..., description="Final response content")
    session_id: str = Field(..., description="Session identifier")


# Create the supervisor workflow
supervisor_workflow = create_supervisor(
    model=llm,
    agents=[research_agent],
    # Routing policy and expectations
    prompt=(
        "You are a supervisor managing a research agent for Web3 application development:\n"
        "- research_agent: use it for questions requiring web research about Web3, blockchain, Ethereum, smart contracts, and related technologies.\n"
        "Analyze incoming prompts carefully:\n"
        "1. If the prompt is related to building Web3 applications, delegate to the research agent.\n"
        "2. If the prompt is NOT related to Web3 applications, respond with: 'Sorry, we are a platform for building Web3 applications'\n"
        "For Web3-related queries, delegate to the research agent and summarize results for the user."
    ),
    add_handoff_back_messages=True,     # include full handoff context
    output_mode="full_history",         # return all turns for transparency
).compile()


class SupervisorAgent:
    """Supervisor agent for workflow orchestration using langgraph_supervisor.
    
    This agent manages worker agents for different tasks:
    - Research agent for web search and information gathering
    """
    
    def __init__(self):
        """Initialize the supervisor agent."""
        self.workflow = supervisor_workflow
        logger.info("Supervisor agent initialized with research agent")
    
    async def process_request(self, message: str, session_id: Optional[str] = None) -> SupervisorResponse:
        """Process a user request through the supervisor workflow.
        
        Args:
            message: The user's message/query
            session_id: Optional session identifier
            
        Returns:
            SupervisorResponse with conversation history and final response
        """
        try:
            # Check if the message is related to Web3 using the LLM
            web3_check_response = llm.invoke([
                {"role": "system", "content": "You are a classifier that determines if a query is related to Web3 application development. Respond with 'YES' if it's related to Web3, blockchain, Ethereum, smart contracts, DApps, or other Web3 technologies. Otherwise, respond with 'NO'."}, 
                {"role": "user", "content": message}
            ])
            
            is_web3_related = "YES" in web3_check_response.content.upper()
            
            if not is_web3_related:
                # If not Web3 related, return a direct response without using the workflow
                rejection_message = "Sorry, we are a platform for building Web3 applications"
                return SupervisorResponse(
                    messages=[{"role": "assistant", "content": rejection_message}],
                    final_response=rejection_message,
                    session_id=session_id or "default_session"
                )
            
            # Create input for supervisor workflow
            inputs = {"messages": [{"role": "user", "content": message}]}
            
            # Run the supervisor workflow
            result = self.workflow.invoke(inputs)
            
            # Extract final response
            final_response = result["messages"][-1]["content"] if result["messages"] else "No response generated"
            
            return SupervisorResponse(
                messages=result["messages"],
                final_response=final_response,
                session_id=session_id or "default_session"
            )
            
        except Exception as e:
            logger.error(f"Supervisor workflow failed: {e}")
            error_response = f"Error processing request: {str(e)}"
            return SupervisorResponse(
                messages=[{"role": "assistant", "content": error_response}],
                final_response=error_response,
                session_id=session_id or "default_session"
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the supervisor agent."""
        try:
            # Test LLM connectivity
            test_response = llm.invoke([{"role": "user", "content": "Health check"}])
            llm_healthy = bool(test_response.content)
            
            # Test Tavily search (if API key is available)
            tavily_healthy = True
            try:
                if settings.TAVILY_API_KEY:
                    from agents.research_agent import tavily
                    tavily.run("test")
            except Exception:
                tavily_healthy = False
            
            overall_healthy = llm_healthy and tavily_healthy
            
            return {
                "healthy": overall_healthy,
                "components": {
                    "llm": llm_healthy,
                    "tavily_search": tavily_healthy,
                    "research_agent": True
                },
                "agents": ["research_agent"]
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
# Factory function for creating supervisor agent instances
def create_supervisor_agent() -> SupervisorAgent:
    """Factory function to create a configured supervisor agent.
    
    Returns:
        Configured SupervisorAgent instance
    """
    return SupervisorAgent()


# Backward compatibility - alias for existing code
GatekeeperAgent = SupervisorAgent
create_gatekeeper_agent = create_supervisor_agent