"""Supervisor Agent for LangGraph Workflow Orchestration.

This module implements a supervisor agent using the langgraph_supervisor pattern
that manages worker agents for different tasks like research and math calculations.

The implementation follows the supervisor pattern with:
- Simple worker agent functions
- Tavily search integration for research
- LLM-based math calculations
- Supervisor workflow orchestration
"""

import os
from typing import Any, Dict, List, Optional, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.tools import Tool
from langgraph_supervisor import create_supervisor
from langgraph.graph import START, END
from pydantic import BaseModel, Field

from core.logging import get_logger
from core.exceptions import WorkflowException
from core.config import get_settings

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

# Initialize Tavily search tool (requires TAVILY_API_KEY environment variable)
if not settings.TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is required")

tavily = TavilySearchAPIWrapper(tavily_api_key=settings.TAVILY_API_KEY)
search_tool = Tool(
    name="web_search",
    func=lambda q: tavily.run(q),
    description="Search the web for current information.",
)
logger.info("Initialized Tavily search tool for research agent")


class SupervisorRequest(BaseModel):
    """Request model for supervisor agent."""
    message: str = Field(..., description="User message/query")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class SupervisorResponse(BaseModel):
    """Response model from supervisor agent."""
    messages: List[Dict[str, str]] = Field(..., description="Conversation messages")
    final_response: str = Field(..., description="Final response content")
    session_id: str = Field(..., description="Session identifier")


# Worker agent classes
class ResearchAgent:
    """Research agent with web search capabilities."""
    name = "research_agent"
    
    def __call__(self, state):
        try:
            # Get the latest user message
            user_msg = state["messages"][-1]["content"]
            logger.info(f"Research agent processing: {user_msg}")
            
            # Perform web search
            tool_result = search_tool.run(user_msg)
            
            # Ask LLM to synthesize findings
            resp = llm.invoke([
                {"role": "system", "content": "Synthesize findings from the search text. Provide clear, factual information."}, 
                {"role": "user", "content": tool_result}
            ])
            
            return {"messages": [{"role": "assistant", "content": resp.content}]}
        except Exception as e:
            logger.error(f"Research agent error: {e}")
            return {"messages": [{"role": "assistant", "content": f"Research failed: {str(e)}"}]}


class MathAgent:
    """Math agent for calculations and mathematical reasoning."""
    name = "math_agent"
    
    def __call__(self, state):
        try:
            user_msg = state["messages"][-1]["content"]
            logger.info(f"Math agent processing: {user_msg}")
            
            prompt = [
                {"role": "system", "content": "You are a precise math solver. Show concise reasoning and provide accurate calculations."}, 
                {"role": "user", "content": user_msg},
            ]
            
            resp = llm.invoke(prompt)
            return {"messages": [{"role": "assistant", "content": resp.content}]}
        except Exception as e:
            logger.error(f"Math agent error: {e}")
            return {"messages": [{"role": "assistant", "content": f"Math calculation failed: {str(e)}"}]}


# Create agent instances
research_agent = ResearchAgent()
math_agent = MathAgent()


# Create the supervisor workflow
supervisor_workflow = create_supervisor(
    model=llm,
    agents=[research_agent, math_agent],
    # Routing policy and expectations
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- research_agent: use it for any question requiring web research, facts, or current information.\n"
        "- math_agent: use it for any computation, equations, math proofs, or numerical calculations.\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself—only delegate and summarize results for the user."
    ),
    add_handoff_back_messages=True,     # include full handoff context
    output_mode="full_history",         # return all turns for transparency
).compile()


class SupervisorAgent:
    """Supervisor agent for workflow orchestration using langgraph_supervisor.
    
    This agent manages worker agents for different tasks:
    - Research agent for web search and information gathering
    - Math agent for calculations and mathematical reasoning
    """
    
    def __init__(self):
        """Initialize the supervisor agent."""
        self.workflow = supervisor_workflow
        logger.info("Supervisor agent initialized with research and math agents")
    
    async def process_request(self, message: str, session_id: Optional[str] = None) -> SupervisorResponse:
        """Process a user request through the supervisor workflow.
        
        Args:
            message: The user's message/query
            session_id: Optional session identifier
            
        Returns:
            SupervisorResponse with conversation history and final response
        """
        try:
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
                    tavily.run("test")
            except Exception:
                tavily_healthy = False
            
            overall_healthy = llm_healthy and tavily_healthy
            
            return {
                "healthy": overall_healthy,
                "components": {
                    "llm": llm_healthy,
                    "tavily_search": tavily_healthy,
                    "research_agent": True,
                    "math_agent": True
                },
                "agents": ["research_agent", "math_agent"]
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