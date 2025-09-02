"""
Smart Contract Agent Module

This module contains the Smart Contract Agent responsible for creating, building,
and deploying smart contracts in Solidity and Move languages. It handles contract
development, testing, compilation, and testnet deployment.

Key Components:
- SmartContractAgent: Main smart contract development agent
- Solidity contract generation and compilation
- Move contract development for Aptos/Sui
- Testing framework integration
- Testnet deployment automation
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


class SmartContractWorkflowState(TypedDict):
    """State definition for smart contract development workflows."""
    messages: Annotated[List[BaseMessage], operator.add]
    contract_requirements: Dict[str, Any]
    target_blockchains: List[str]
    contract_specifications: List[Dict[str, Any]]
    generated_contracts: Annotated[List[Dict[str, Any]], operator.add]
    compilation_results: List[Dict[str, Any]]
    test_results: List[Dict[str, Any]]
    deployment_results: List[Dict[str, Any]]
    execution_metadata: Dict[str, Any]


class SmartContractAgent:
    """Smart Contract Agent specialized in Solidity and Move development."""
    
    def __init__(self, 
                 model_name: str = "gpt-4o",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Smart Contract Agent.
        
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
        
        # Smart contract development system prompt
        self.system_prompt = """
        You are a Smart Contract Development Agent specialized in creating secure,
        efficient smart contracts in Solidity and Move programming languages.
        
        Your expertise includes:
        - Solidity development for Ethereum and EVM-compatible chains
        - Move development for Aptos and Sui blockchains
        - Smart contract security best practices
        - Gas optimization techniques
        - Contract testing and verification
        - Deployment strategies and automation
        - Integration with development frameworks (Hardhat, Foundry, Aptos CLI)
        
        Security priorities:
        - Reentrancy protection
        - Access control mechanisms
        - Input validation and sanitization
        - Overflow/underflow protection
        - Front-running mitigation
        - Proper error handling
        
        Always follow best practices for:
        - Code readability and documentation
        - Modular contract architecture
        - Upgradability patterns when appropriate
        - Event emission for transparency
        - Testnet-only deployment for development
        """
        
        logger.info(f"Smart Contract Agent initialized with model: {model_name}")
    
    def analyze_contract_requirements(self, requirements: str) -> Dict[str, Any]:
        """
        Analyze smart contract requirements and determine implementation approach.
        
        Args:
            requirements: Contract requirements description
            
        Returns:
            Analysis result with recommended architecture and implementation plan
        """
        try:
            prompt = f"""
            Analyze the following smart contract requirements and provide a detailed analysis:
            
            Requirements: {requirements}
            
            Please provide:
            1. Contract architecture recommendations
            2. Suitable blockchain platforms (Ethereum, Polygon, Aptos, Sui)
            3. Required contract features and functions
            4. Security considerations and mitigation strategies
            5. Gas optimization opportunities
            6. Testing strategy
            7. Deployment plan for testnet
            
            Format your response as a structured JSON object.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse the response
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = {
                    "architecture": "Modular contract design",
                    "platforms": ["Ethereum Sepolia", "Polygon Mumbai"],
                    "analysis": response.content
                }
            
            return {
                "status": "success",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing contract requirements: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_solidity_contract(self, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Solidity smart contract based on specifications.
        
        Args:
            specifications: Contract specifications and requirements
            
        Returns:
            Generated Solidity contract code
        """
        try:
            prompt = f"""
            Generate a complete Solidity smart contract based on these specifications:
            
            Specifications: {json.dumps(specifications, indent=2)}
            
            Requirements:
            - Use Solidity ^0.8.19 or latest stable version
            - Implement proper access controls (OpenZeppelin)
            - Include comprehensive error handling
            - Add detailed NatSpec documentation
            - Implement security best practices
            - Optimize for gas efficiency
            - Include events for all state changes
            - Add proper input validation
            
            Provide:
            1. Main contract code
            2. Interface definitions if needed
            3. Deployment script (Hardhat/Foundry)
            4. Basic test cases
            5. README with deployment instructions
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "language": "solidity",
                "contract_code": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating Solidity contract: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_move_contract(self, specifications: Dict[str, Any], platform: str = "aptos") -> Dict[str, Any]:
        """
        Generate Move smart contract for Aptos or Sui.
        
        Args:
            specifications: Contract specifications and requirements
            platform: Target platform ("aptos" or "sui")
            
        Returns:
            Generated Move contract code
        """
        try:
            prompt = f"""
            Generate a complete Move smart contract for {platform.title()} based on these specifications:
            
            Specifications: {json.dumps(specifications, indent=2)}
            Platform: {platform}
            
            Requirements:
            - Use latest Move language features
            - Implement proper resource management
            - Include comprehensive error handling
            - Add detailed documentation
            - Follow {platform} best practices
            - Implement security patterns
            - Include proper testing modules
            
            Provide:
            1. Main module code
            2. Resource definitions
            3. Public entry functions
            4. Test modules
            5. Deployment configuration
            6. README with setup instructions
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "language": "move",
                "platform": platform,
                "contract_code": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating Move contract: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_deployment_scripts(self, contracts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate deployment scripts for testnet deployment.
        
        Args:
            contracts: List of generated contracts
            
        Returns:
            Deployment scripts and configuration
        """
        try:
            prompt = f"""
            Generate comprehensive deployment scripts for these contracts:
            
            Contracts: {json.dumps(contracts, indent=2)}
            
            Create deployment scripts for:
            1. Ethereum Sepolia testnet (using Hardhat)
            2. Polygon Mumbai testnet
            3. Aptos testnet (if Move contracts present)
            4. Sui testnet (if Sui Move contracts present)
            
            Include:
            - Environment configuration
            - Network configurations
            - Deployment verification
            - Contract interaction examples
            - Error handling and rollback procedures
            - Gas estimation and optimization
            
            Provide complete, production-ready deployment automation.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "deployment_scripts": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating deployment scripts: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_test_suite(self, contracts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive test suite for contracts.
        
        Args:
            contracts: List of generated contracts
            
        Returns:
            Test suite with unit and integration tests
        """
        try:
            prompt = f"""
            Generate a comprehensive test suite for these smart contracts:
            
            Contracts: {json.dumps(contracts, indent=2)}
            
            Create tests for:
            1. Unit tests for all functions
            2. Integration tests for contract interactions
            3. Security vulnerability tests
            4. Gas optimization tests
            5. Edge case and error condition tests
            6. Access control tests
            
            Use appropriate testing frameworks:
            - Hardhat/Foundry for Solidity
            - Move testing framework for Move contracts
            
            Include:
            - Test setup and teardown
            - Mock data and fixtures
            - Coverage reporting configuration
            - Continuous integration setup
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "status": "success",
                "test_suite": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating test suite: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def smart_contract_agent_node(state: SmartContractWorkflowState) -> SmartContractWorkflowState:
    """
    Smart contract agent node for processing contract development tasks.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with smart contract development results
    """
    try:
        agent = SmartContractAgent()
        
        # Extract the latest message for processing
        if state["messages"]:
            latest_message = state["messages"][-1]
            task_description = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)
        else:
            task_description = "Generate secure smart contracts for testnet deployment"
        
        # Analyze requirements
        analysis_result = agent.analyze_contract_requirements(task_description)
        
        generated_contracts = []
        
        # Generate Solidity contract
        solidity_result = agent.generate_solidity_contract(analysis_result.get("analysis", {}))
        if solidity_result["status"] == "success":
            generated_contracts.append(solidity_result)
        
        # Generate Move contract for Aptos
        move_aptos_result = agent.generate_move_contract(analysis_result.get("analysis", {}), "aptos")
        if move_aptos_result["status"] == "success":
            generated_contracts.append(move_aptos_result)
        
        # Generate deployment scripts
        deployment_result = agent.generate_deployment_scripts(generated_contracts)
        
        # Generate test suite
        test_result = agent.generate_test_suite(generated_contracts)
        
        # Create result message
        result_message = AIMessage(
            content=f"Smart contract development completed:\n\n"
                   f"Analysis: {analysis_result['status']}\n"
                   f"Contracts Generated: {len(generated_contracts)}\n"
                   f"Deployment Scripts: {deployment_result['status']}\n"
                   f"Test Suite: {test_result['status']}"
        )
        
        # Update execution metadata
        execution_metadata = state.get("execution_metadata", {})
        execution_metadata["smart_contract_agent"] = {
            "executed_at": datetime.now().isoformat(),
            "analysis_result": analysis_result,
            "contracts_generated": len(generated_contracts),
            "deployment_result": deployment_result,
            "test_result": test_result
        }
        
        return {
            **state,
            "messages": [result_message],
            "generated_contracts": generated_contracts,
            "compilation_results": [],  # To be populated during actual compilation
            "test_results": [test_result],
            "deployment_results": [deployment_result],
            "execution_metadata": execution_metadata
        }
        
    except Exception as e:
        logger.error(f"Error in smart contract agent node: {str(e)}")
        error_message = AIMessage(content=f"Smart contract agent error: {str(e)}")
        
        return {
            **state,
            "messages": [error_message],
            "execution_metadata": {
                **state.get("execution_metadata", {}),
                "smart_contract_agent_error": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
        }


__all__ = [
    "SmartContractAgent",
    "SmartContractWorkflowState",
    "smart_contract_agent_node"
]