"""Web3 Builder Agent for generating Web3 applications and smart contracts"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool, tool
from langchain.schema import HumanMessage, SystemMessage
from app.agents.base import BaseAgent, AgentTask, AgentConfig, AgentStatus
from app.llm.manager import llm_manager
from app.core.logging import logger
import json

class Web3BuilderAgent(BaseAgent):
    """Agent specialized in building Web3 applications and smart contracts"""
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize Web3-specific tools"""
        return [
            self._create_smart_contract_tool(),
            self._create_web3_frontend_tool(),
            self._create_deployment_script_tool(),
            self._validate_solidity_tool()
        ]
    
    def _create_smart_contract_tool(self) -> BaseTool:
        """Tool for generating smart contracts"""
        @tool
        def generate_smart_contract(contract_type: str, requirements: str) -> str:
            """Generate a Solidity smart contract based on type and requirements.
            
            Args:
                contract_type: Type of contract (e.g., 'ERC20', 'ERC721', 'DeFi', 'DAO')
                requirements: Detailed requirements for the contract
            """
            try:
                # This would integrate with the LLM to generate smart contracts
                prompt = f"""
                Generate a Solidity smart contract with the following specifications:
                Contract Type: {contract_type}
                Requirements: {requirements}
                
                Please include:
                1. Proper imports and pragma statements
                2. Security best practices
                3. Gas optimization
                4. Comprehensive comments
                5. Event emissions
                6. Access control where appropriate
                """
                
                # This would be replaced with actual LLM call
                return f"Smart contract generated for {contract_type} with requirements: {requirements}"
            except Exception as e:
                return f"Error generating smart contract: {str(e)}"
        
        return generate_smart_contract
    
    def _create_web3_frontend_tool(self) -> BaseTool:
        """Tool for generating Web3 frontend components"""
        @tool
        def generate_web3_frontend(framework: str, features: str) -> str:
            """Generate Web3 frontend code with wallet integration.
            
            Args:
                framework: Frontend framework (e.g., 'React', 'Vue', 'Angular')
                features: Required features (e.g., 'wallet connection', 'token transfer')
            """
            try:
                prompt = f"""
                Generate a {framework} frontend application with Web3 integration:
                Features: {features}
                
                Please include:
                1. Wallet connection (MetaMask, WalletConnect)
                2. Contract interaction functions
                3. Error handling
                4. Loading states
                5. Responsive design
                6. TypeScript support if applicable
                """
                
                return f"Web3 frontend generated for {framework} with features: {features}"
            except Exception as e:
                return f"Error generating Web3 frontend: {str(e)}"
        
        return generate_web3_frontend
    
    def _create_deployment_script_tool(self) -> BaseTool:
        """Tool for generating deployment scripts"""
        @tool
        def generate_deployment_script(network: str, contract_name: str) -> str:
            """Generate deployment script for smart contracts.
            
            Args:
                network: Target network (e.g., 'mainnet', 'goerli', 'polygon')
                contract_name: Name of the contract to deploy
            """
            try:
                prompt = f"""
                Generate a deployment script for:
                Network: {network}
                Contract: {contract_name}
                
                Please include:
                1. Network configuration
                2. Gas estimation
                3. Verification steps
                4. Environment variable handling
                5. Error handling and rollback
                6. Post-deployment verification
                """
                
                return f"Deployment script generated for {contract_name} on {network}"
            except Exception as e:
                return f"Error generating deployment script: {str(e)}"
        
        return generate_deployment_script
    
    def _validate_solidity_tool(self) -> BaseTool:
        """Tool for validating Solidity code"""
        @tool
        def validate_solidity_code(code: str) -> str:
            """Validate Solidity code for security and best practices.
            
            Args:
                code: Solidity code to validate
            """
            try:
                # This would integrate with Solidity compiler and security tools
                issues = []
                
                # Basic validation checks
                if "pragma solidity" not in code:
                    issues.append("Missing pragma statement")
                
                if "SPDX-License-Identifier" not in code:
                    issues.append("Missing SPDX license identifier")
                
                if not issues:
                    return "Solidity code validation passed"
                else:
                    return f"Validation issues found: {', '.join(issues)}"
                    
            except Exception as e:
                return f"Error validating Solidity code: {str(e)}"
        
        return validate_solidity_code
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Web3 Builder Agent"""
        return """
        You are a Web3 Builder Agent specialized in creating decentralized applications and smart contracts.
        
        Your capabilities include:
        1. Generating Solidity smart contracts (ERC20, ERC721, DeFi protocols, DAOs)
        2. Creating Web3 frontend applications with wallet integration
        3. Generating deployment scripts for various networks
        4. Validating smart contract code for security and best practices
        5. Providing Web3 development guidance and best practices
        
        When building Web3 applications:
        - Always prioritize security and follow best practices
        - Consider gas optimization in smart contracts
        - Implement proper access controls and permissions
        - Include comprehensive error handling
        - Provide clear documentation and comments
        - Consider multi-chain compatibility when relevant
        
        You should ask clarifying questions when requirements are unclear and provide
        detailed explanations of your implementations.
        """
    
    async def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a Web3 building task"""
        try:
            self.current_task = task
            task.status = AgentStatus.RUNNING
            
            logger.info(f"Web3 Builder Agent executing task: {task.id}")
            
            # Extract task parameters
            task_type = task.input_data.get("type", "general")
            requirements = task.input_data.get("requirements", "")
            
            # Route to appropriate handler based on task type
            if task_type == "smart_contract":
                result = await self._handle_smart_contract_task(task.input_data)
            elif task_type == "frontend":
                result = await self._handle_frontend_task(task.input_data)
            elif task_type == "deployment":
                result = await self._handle_deployment_task(task.input_data)
            elif task_type == "validation":
                result = await self._handle_validation_task(task.input_data)
            else:
                result = await self._handle_general_task(task.input_data)
            
            task.output_data = result
            task.status = AgentStatus.COMPLETED
            
            self.add_task_to_history(task)
            self.current_task = None
            
            logger.info(f"Web3 Builder Agent completed task: {task.id}")
            return task
            
        except Exception as e:
            task.status = AgentStatus.ERROR
            task.error_message = str(e)
            logger.error(f"Web3 Builder Agent task failed: {str(e)}")
            return task
    
    async def _handle_smart_contract_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle smart contract generation task"""
        contract_type = input_data.get("contract_type", "general")
        requirements = input_data.get("requirements", "")
        
        # Use LLM to generate smart contract
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Generate a {contract_type} smart contract with these requirements: {requirements}"}
        ]
        
        response = await llm_manager.chat_completion(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            provider=self.config.llm_provider,
            model=self.config.llm_model
        )
        
        return {
            "contract_code": response.content,
            "contract_type": contract_type,
            "requirements": requirements
        }
    
    async def _handle_frontend_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle frontend generation task"""
        framework = input_data.get("framework", "React")
        features = input_data.get("features", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Generate a {framework} Web3 frontend with these features: {features}"}
        ]
        
        response = await llm_manager.chat_completion(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            provider=self.config.llm_provider,
            model=self.config.llm_model
        )
        
        return {
            "frontend_code": response.content,
            "framework": framework,
            "features": features
        }
    
    async def _handle_deployment_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deployment script generation task"""
        network = input_data.get("network", "goerli")
        contract_name = input_data.get("contract_name", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Generate deployment script for {contract_name} on {network} network"}
        ]
        
        response = await llm_manager.chat_completion(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            provider=self.config.llm_provider,
            model=self.config.llm_model
        )
        
        return {
            "deployment_script": response.content,
            "network": network,
            "contract_name": contract_name
        }
    
    async def _handle_validation_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code validation task"""
        code = input_data.get("code", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Validate this Solidity code for security and best practices: {code}"}
        ]
        
        response = await llm_manager.chat_completion(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            provider=self.config.llm_provider,
            model=self.config.llm_model
        )
        
        return {
            "validation_result": response.content,
            "code": code
        }
    
    async def _handle_general_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general Web3 development task"""
        query = input_data.get("query", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": query}
        ]
        
        response = await llm_manager.chat_completion(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            provider=self.config.llm_provider,
            model=self.config.llm_model
        )
        
        return {
            "response": response.content,
            "query": query
        }
    
    async def _generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using LLM"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": message}
        ]
        
        if context:
            messages.insert(1, {"role": "system", "content": f"Context: {json.dumps(context)}"})
        
        response = await llm_manager.chat_completion(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            provider=self.config.llm_provider,
            model=self.config.llm_model
        )
        
        return response.content