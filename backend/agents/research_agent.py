"""Research Agent for Web Search and Information Retrieval.

This module implements a research agent with web search capabilities
using the Tavily search API for information retrieval and synthesis.
"""

import os
from typing import Any, Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.tools import Tool

from core.logging import get_logger
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
logger.info("Initialized Gemini LLM for research agent")

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


class ResearchAgent:
    """Research agent with web search capabilities focused on Web3 development."""
    name = "research_agent"
    
    def __call__(self, state):
        try:
            # Get the latest user message
            user_msg = state["messages"][-1]["content"]
            logger.info(f"Research agent processing: {user_msg}")
            
            # Enhance query with Web3 focus
            web3_focused_query = f"Web3 development: {user_msg}"
            
            # Perform web search
            tool_result = search_tool.run(web3_focused_query)
            
            # Ask LLM to synthesize findings with Web3 focus
            resp = llm.invoke([
                {"role": "system", "content": "You are a Web3 development expert. Synthesize findings from the search text, focusing on:\n"
                                      "- Smart contract deployment processes\n"
                                      "- Smart contract writing best practices\n"
                                      "- Wallet integration methods\n"
                                      "- Other relevant Web3 development topics\n"
                                      "Provide clear, factual information tailored for Web3 application development."}, 
                {"role": "user", "content": tool_result}
            ])
            
            return {"messages": [{"role": "assistant", "content": resp.content}]}
        except Exception as e:
            logger.error(f"Research agent error: {e}")
            return {"messages": [{"role": "assistant", "content": f"Research failed: {str(e)}"}]}


# Create agent instance
research_agent = ResearchAgent()


# Factory function for creating research agent instances
def create_research_agent() -> ResearchAgent:
    """Factory function to create a configured research agent.
    
    Returns:
        Configured ResearchAgent instance
    """
    return ResearchAgent()