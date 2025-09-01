"""
Supervisor Agent Module

This module contains all supervisor-related functionalities and decision-making logic
for coordinating parallel agent workflows in LangGraph.

Key Components:
- SupervisorAgent: Main supervisor class with decision-making capabilities
- SupervisorWorkflowState: State management for supervisor workflows
- Supervisor node functions and conditional logic
- Integration with OpenAI GPT-4o and Tavily search
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from typing_extensions import Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
import operator
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupervisorWorkflowState(TypedDict):
    """Enhanced state definition for supervisor-coordinated workflows."""
    messages: Annotated[List[BaseMessage], operator.add]
    task_description: str
    parallel_tasks: List[Dict[str, Any]]
    task_results: Annotated[List[Dict[str, Any]], operator.add]
    supervisor_decision: str
    next_agent: str
    final_result: str
    execution_metadata: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    confidence_score: float


class SupervisorAgent:
    """Enhanced Supervisor Agent with GPT-4o and Tavily search integration."""
    
    def __init__(self, 
                 model_name: str = "gpt-4o",
                 tavily_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Supervisor Agent.
        
        Args:
            model_name: OpenAI model to use (default: gpt-4o)
            tavily_api_key: Tavily API key for search functionality
            openai_api_key: OpenAI API key for GPT-4o
        """
        # Set up API keys
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        if not self.tavily_api_key:
            raise ValueError("Tavily API key is required. Set TAVILY_API_KEY environment variable.")
        
        # Initialize GPT-4o model
        self.model = ChatOpenAI(
            model=model_name,
            api_key=self.openai_api_key,
            temperature=0.1
        )
        
        # Initialize Tavily search tool
        self.search_tool = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
            api_key=self.tavily_api_key
        )
        
        # Supervisor system prompt
        self.system_prompt = """
        You are an advanced AI Supervisor Agent powered by GPT-4o with internet search capabilities.
        
        Your responsibilities:
        1. Analyze complex tasks and break them into parallel subtasks
        2. Coordinate multiple specialized agents (research, analysis, planning)
        3. Make intelligent decisions about task distribution and execution flow
        4. Conduct internet research when additional information is needed
        5. Ensure quality control and validate agent outputs
        6. Synthesize results from multiple agents into coherent final outputs
        
        Decision-making principles:
        - Prioritize tasks based on complexity and dependencies
        - Leverage internet search for real-time information
        - Ensure parallel execution efficiency
        - Maintain high confidence scores through validation
        - Provide clear reasoning for all decisions
        """
    
    def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """Analyze a task and determine the best execution strategy."""
        logger.info(f"Supervisor analyzing task: {task_description}")
        
        # Generate search queries for additional context
        search_queries = self._generate_search_queries(task_description)
        
        # Perform internet research
        search_results = []
        for query in search_queries:
            try:
                results = self.search_tool.run(query)
                search_results.extend(results if isinstance(results, list) else [results])
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {str(e)}")
        
        # Analyze task with search context
        analysis_prompt = f"""
        Task to analyze: {task_description}
        
        Search results context:
        {self._format_search_results(search_results)}
        
        Based on this task and available context, provide:
        1. Task complexity assessment (1-10)
        2. Recommended parallel subtasks
        3. Agent assignments (research, analysis, planning)
        4. Execution priority and dependencies
        5. Success criteria and validation methods
        
        Respond in JSON format with clear reasoning.
        """
        
        try:
            response = self.model.invoke([HumanMessage(content=analysis_prompt)])
            return {
                "analysis": response.content,
                "search_results": search_results,
                "confidence_score": self._calculate_confidence_score(search_results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Task analysis failed: {str(e)}")
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "search_results": search_results,
                "confidence_score": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def create_parallel_tasks(self, task_description: str, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create parallel tasks based on supervisor analysis."""
        logger.info("Supervisor creating parallel task distribution")
        
        # Enhanced task creation with search context
        parallel_tasks = [
            {
                "id": "research_task",
                "agent": "research_agent",
                "description": f"Research and gather comprehensive information about: {task_description}",
                "priority": "high",
                "search_context": analysis_result.get("search_results", []),
                "expected_output": "Detailed research findings with sources and insights"
            },
            {
                "id": "analysis_task",
                "agent": "analysis_agent",
                "description": f"Analyze requirements, constraints, and feasibility for: {task_description}",
                "priority": "medium",
                "dependencies": ["research_task"],
                "expected_output": "Comprehensive analysis with risk assessment"
            },
            {
                "id": "planning_task",
                "agent": "planning_agent",
                "description": f"Create detailed execution plan and strategy for: {task_description}",
                "priority": "high",
                "dependencies": ["research_task", "analysis_task"],
                "expected_output": "Actionable execution plan with timelines"
            }
        ]
        
        return parallel_tasks
    
    def make_execution_decision(self, state: SupervisorWorkflowState) -> str:
        """Make intelligent decisions about workflow execution."""
        logger.info("Supervisor making execution decision")
        
        task_description = state["task_description"]
        
        # Decision logic based on task complexity and available information
        if not task_description or len(task_description.strip()) < 10:
            return "insufficient_information"
        
        # Check if we need additional research
        if "research" in task_description.lower() or "analyze" in task_description.lower():
            return "execute_parallel_tasks"
        
        # Default to parallel execution for complex tasks
        return "execute_parallel_tasks"
    
    def validate_results(self, task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and quality-check results from parallel agents."""
        logger.info("Supervisor validating agent results")
        
        validation_summary = {
            "total_results": len(task_results),
            "successful_results": 0,
            "failed_results": 0,
            "quality_score": 0.0,
            "validation_timestamp": datetime.now().isoformat()
        }
        
        for result in task_results:
            if result.get("status") == "completed":
                validation_summary["successful_results"] += 1
            else:
                validation_summary["failed_results"] += 1
        
        # Calculate quality score
        if validation_summary["total_results"] > 0:
            validation_summary["quality_score"] = (
                validation_summary["successful_results"] / validation_summary["total_results"]
            )
        
        return validation_summary
    
    def _generate_search_queries(self, task_description: str) -> List[str]:
        """Generate relevant search queries for task context."""
        # Extract key terms and generate search queries
        queries = [
            f"{task_description} best practices",
            f"{task_description} implementation guide",
            f"{task_description} latest trends 2024"
        ]
        return queries[:2]  # Limit to 2 queries to avoid rate limits
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results for prompt context."""
        if not search_results:
            return "No search results available."
        
        formatted = []
        for i, result in enumerate(search_results[:3], 1):  # Limit to top 3 results
            if isinstance(result, dict):
                title = result.get("title", "No title")
                content = result.get("content", result.get("snippet", "No content"))
                formatted.append(f"{i}. {title}: {content[:200]}...")
        
        return "\n".join(formatted)
    
    def _calculate_confidence_score(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on available information."""
        if not search_results:
            return 0.5  # Medium confidence without search results
        
        # Higher confidence with more comprehensive search results
        base_score = 0.7
        result_bonus = min(len(search_results) * 0.05, 0.3)
        
        return min(base_score + result_bonus, 1.0)


# Supervisor node functions
def supervisor_node(state: SupervisorWorkflowState) -> SupervisorWorkflowState:
    """Enhanced supervisor node with GPT-4o and search capabilities."""
    logger.info("Enhanced supervisor analyzing task and creating execution plan")
    
    # Initialize supervisor agent
    supervisor = SupervisorAgent()
    
    task = state["task_description"]
    
    # Analyze task with internet research
    analysis_result = supervisor.analyze_task(task)
    
    # Create parallel tasks based on analysis
    parallel_tasks = supervisor.create_parallel_tasks(task, analysis_result)
    
    # Make execution decision
    decision = supervisor.make_execution_decision(state)
    
    supervisor_message = AIMessage(
        content=f"Enhanced supervisor analyzed task and created {len(parallel_tasks)} parallel tasks with search context"
    )
    
    return {
        "messages": [supervisor_message],
        "parallel_tasks": parallel_tasks,
        "supervisor_decision": decision,
        "search_results": analysis_result.get("search_results", []),
        "confidence_score": analysis_result.get("confidence_score", 0.0),
        "execution_metadata": {
            "supervisor_timestamp": datetime.now().isoformat(),
            "total_parallel_tasks": len(parallel_tasks),
            "analysis_result": analysis_result.get("analysis", ""),
            "search_queries_executed": len(analysis_result.get("search_results", []))
        }
    }


# Conditional logic functions
def should_execute_parallel(state: SupervisorWorkflowState) -> Literal["parallel_coordinator", "end"]:
    """Enhanced conditional logic for parallel execution decisions."""
    decision = state.get("supervisor_decision", "")
    confidence = state.get("confidence_score", 0.0)
    
    # Execute parallel tasks if supervisor decides and confidence is sufficient
    if decision == "execute_parallel_tasks" and confidence >= 0.3:
        return "parallel_coordinator"
    
    logger.warning(f"Parallel execution skipped. Decision: {decision}, Confidence: {confidence}")
    return "end"


def should_aggregate_results(state: SupervisorWorkflowState) -> Literal["result_aggregator", "end"]:
    """Enhanced conditional logic for result aggregation."""
    task_results = state.get("task_results", [])
    parallel_tasks = state.get("parallel_tasks", [])
    
    # Aggregate if we have results from all expected agents
    expected_agents = len(parallel_tasks)
    completed_results = len([r for r in task_results if r.get("status") == "completed"])
    
    if completed_results >= expected_agents or len(task_results) >= 3:
        return "result_aggregator"
    
    logger.info(f"Waiting for more results. Completed: {completed_results}, Expected: {expected_agents}")
    return "end"


# Export key components
__all__ = [
    "SupervisorAgent",
    "SupervisorWorkflowState", 
    "supervisor_node",
    "should_execute_parallel",
    "should_aggregate_results"
]