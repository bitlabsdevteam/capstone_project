"""
Frontend Agent Module

This module contains the Frontend Agent responsible for creating frontend websites
with Web3 integration capabilities. It handles React/Next.js development,
Web3 wallet integration, smart contract interaction, and modern UI/UX design.

Key Components:
- FrontendAgent: Main frontend development agent
- Web3 integration tools and utilities
- Frontend project scaffolding and component generation
- Wallet connection and blockchain interaction setup
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
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrontendWorkflowState(TypedDict):
    """State definition for frontend development workflows."""
    messages: Annotated[List[BaseMessage], operator.add]
    project_requirements: Dict[str, Any]
    web3_requirements: Dict[str, Any]
    frontend_stack: Dict[str, Any]
    component_specifications: List[Dict[str, Any]]
    generated_code: Annotated[List[Dict[str, Any]], operator.add]
    deployment_config: Dict[str, Any]
    testing_results: List[Dict[str, Any]]
    execution_metadata: Dict[str, Any]


class FrontendAgent:
    """Frontend Agent specialized in Web3-enabled frontend development."""
    
    def __init__(self, 
                 model_name: str = "gpt-4o",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Frontend Agent.
        
        Args:
            model_name: OpenAI model to use (default: gpt-4o)
            openai_api_key: OpenAI API key (optional, can use env var)
        """
        self.model_name = model_name
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
            
        # Initialize the language model
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=self.openai_api_key,
            temperature=0.1
        )
        
        # Frontend development system prompt
        self.system_prompt = """
        You are a Frontend Development Agent specialized in creating modern, 
        responsive web applications with Web3 integration capabilities.
        
        Your expertise includes:
        - React.js and Next.js development
        - TypeScript and modern JavaScript
        - Web3 wallet integration (MetaMask, WalletConnect)
        - Ethereum and other blockchain interactions
        - Smart contract integration using ethers.js/web3.js
        - Modern UI frameworks (Tailwind CSS, Material-UI, Chakra UI)
        - State management (Redux, Zustand, Context API)
        - Testing frameworks (Jest, React Testing Library)
        - Deployment strategies (Vercel, Netlify, IPFS)
        
        Always follow best practices for:
        - Security in Web3 applications
        - User experience and accessibility
        - Performance optimization
        - Code organization and maintainability
        - Responsive design principles
        """
        
        logger.info(f"Frontend Agent initialized with model: {model_name}")
    
    def analyze_frontend_requirements(self, requirements: str) -> Dict[str, Any]:
        """
        Analyze frontend project requirements and determine tech stack.
        
        Args:
            requirements: Project requirements description
            
        Returns:
            Analysis result with recommended tech stack and architecture
        """
        try:
            prompt = f"""
            Analyze the following frontend project requirements and provide a detailed analysis:
            
            Requirements: {requirements}
            
            Please provide:
            1. Recommended tech stack (framework, libraries, tools)
            2. Web3 integration requirements
            3. UI/UX considerations
            4. Project structure recommendations
            5. Development timeline estimate
            6. Potential challenges and solutions
            
            Format your response as a structured JSON object.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse the response (assuming it's JSON formatted)
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to structured text parsing
                analysis = {
                    "tech_stack": "React + Next.js + TypeScript + Tailwind CSS",
                    "web3_integration": "ethers.js + MetaMask",
                    "analysis": response.content
                }
            
            return {
                "status": "success",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing frontend requirements: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_project_structure(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate project structure and initial setup files.
        
        Args:
            analysis: Frontend requirements analysis result
            
        Returns:
            Project structure and setup instructions
        """
        try:
            prompt = f"""
            Based on the following analysis, generate a complete project structure 
            for a Web3-enabled frontend application:
            
            Analysis: {json.dumps(analysis, indent=2)}
            
            Please provide:
            1. Complete folder structure
            2. Package.json dependencies
            3. Configuration files (next.config.js, tailwind.config.js, etc.)
            4. Environment variables setup
            5. Initial component structure
            6. Web3 integration setup files
            
            Format as a structured response with file contents.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "project_structure": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating project structure: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_web3_components(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Web3-specific components and utilities.
        
        Args:
            requirements: Web3 integration requirements
            
        Returns:
            Generated Web3 components and utilities
        """
        try:
            prompt = f"""
            Generate Web3 integration components based on these requirements:
            
            Requirements: {json.dumps(requirements, indent=2)}
            
            Please create:
            1. Wallet connection component
            2. Smart contract interaction hooks
            3. Web3 context provider
            4. Transaction handling utilities
            5. Error handling for Web3 operations
            6. Network switching functionality
            
            Provide complete, production-ready React/TypeScript code.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "web3_components": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating Web3 components: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_ui_components(self, specifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate UI components based on specifications.
        
        Args:
            specifications: List of component specifications
            
        Returns:
            Generated UI components
        """
        try:
            prompt = f"""
            Generate modern, responsive UI components based on these specifications:
            
            Specifications: {json.dumps(specifications, indent=2)}
            
            Requirements:
            - Use TypeScript and React functional components
            - Implement responsive design with Tailwind CSS
            - Include proper accessibility features
            - Add loading states and error handling
            - Follow modern React patterns (hooks, context)
            
            Provide complete component code with proper TypeScript types.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "ui_components": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating UI components: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def frontend_agent_node(state: FrontendWorkflowState) -> FrontendWorkflowState:
    """
    Frontend agent node for processing frontend development tasks.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with frontend development results
    """
    try:
        agent = FrontendAgent()
        
        # Extract the latest message for processing
        if state["messages"]:
            latest_message = state["messages"][-1]
            task_description = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)
        else:
            task_description = "Generate a modern Web3-enabled frontend application"
        
        # Analyze requirements
        analysis_result = agent.analyze_frontend_requirements(task_description)
        
        # Generate project structure
        structure_result = agent.generate_project_structure(analysis_result)
        
        # Generate Web3 components if needed
        web3_result = agent.generate_web3_components(state.get("web3_requirements", {}))
        
        # Create result message
        result_message = AIMessage(
            content=f"Frontend development completed:\n\n"
                   f"Analysis: {analysis_result['status']}\n"
                   f"Structure: {structure_result['status']}\n"
                   f"Web3 Components: {web3_result['status']}"
        )
        
        # Update execution metadata
        execution_metadata = state.get("execution_metadata", {})
        execution_metadata["frontend_agent"] = {
            "executed_at": datetime.now().isoformat(),
            "analysis_result": analysis_result,
            "structure_result": structure_result,
            "web3_result": web3_result
        }
        
        return {
            **state,
            "messages": [result_message],
            "generated_code": [{
                "type": "frontend",
                "analysis": analysis_result,
                "structure": structure_result,
                "web3_components": web3_result,
                "timestamp": datetime.now().isoformat()
            }],
            "execution_metadata": execution_metadata
        }
        
    except Exception as e:
        logger.error(f"Error in frontend agent node: {str(e)}")
        error_message = AIMessage(content=f"Frontend agent error: {str(e)}")
        
        return {
            **state,
            "messages": [error_message],
            "execution_metadata": {
                **state.get("execution_metadata", {}),
                "frontend_agent_error": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
        }


__all__ = [
    "FrontendAgent",
    "FrontendWorkflowState",
    "frontend_agent_node"
]