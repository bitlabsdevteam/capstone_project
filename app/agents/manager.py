"""Agent Manager for coordinating multi-agent workflows"""

from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from datetime import datetime
from app.agents.base import BaseAgent, AgentTask, AgentConfig, AgentType, AgentStatus
from app.agents.web3_builder import Web3BuilderAgent

from app.llm.manager import llm_manager
from app.core.logging import logger
import asyncio
import json

class WorkflowStep:
    """Represents a step in a multi-agent workflow"""
    
    def __init__(
        self,
        agent_type: AgentType,
        task_type: str,
        input_data: Dict[str, Any],
        depends_on: Optional[List[str]] = None
    ):
        self.id = str(uuid4())
        self.agent_type = agent_type
        self.task_type = task_type
        self.input_data = input_data
        self.depends_on = depends_on or []
        self.status = AgentStatus.IDLE
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

class Workflow:
    """Represents a multi-agent workflow"""
    
    def __init__(self, name: str, description: str):
        self.id = str(uuid4())
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.status = AgentStatus.IDLE
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at: Optional[str] = None
        self.results: Dict[str, Any] = {}
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute"""
        ready_steps = []
        
        for step in self.steps:
            if step.status == AgentStatus.IDLE:
                # Check if all dependencies are completed
                dependencies_met = all(
                    any(s.id == dep_id and s.status == AgentStatus.COMPLETED for s in self.steps)
                    for dep_id in step.depends_on
                )
                
                if not step.depends_on or dependencies_met:
                    ready_steps.append(step)
        
        return ready_steps
    
    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return all(step.status in [AgentStatus.COMPLETED, AgentStatus.ERROR] for step in self.steps)

class AgentManager:
    """Manager for coordinating multiple agents and workflows"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.active_tasks: Dict[str, AgentTask] = {}
        
        # Initialize default agents
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agents"""
        try:
            # Web3 Builder Agent
            web3_config = AgentConfig(
                name="web3_builder",
                type=AgentType.WEB3_BUILDER,
                description="Specialized agent for building Web3 applications and smart contracts",
                llm_provider="openai",
                llm_model="gpt-4",
                temperature=0.3,
                tools=["smart_contract_generator", "web3_frontend_generator", "deployment_script_generator"]
            )
            
            web3_agent = Web3BuilderAgent(web3_config)
            web3_agent.set_llm(llm_manager)
            self.agents["web3_builder"] = web3_agent
            

            
            logger.info("Default agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing default agents: {str(e)}")
    
    def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent"""
        try:
            agent_id = f"{config.type.value}_{str(uuid4())[:8]}"
            
            # Create agent based on type
            if config.type == AgentType.WEB3_BUILDER:
                agent = Web3BuilderAgent(config)
                agent.set_llm(llm_manager)
            elif config.type == AgentType.ANALYSIS:
                # For now, default to Web3BuilderAgent for analysis tasks
                # In the future, add other specialized agents
                agent = Web3BuilderAgent(config)
                agent.set_llm(llm_manager)
            else:
                # For now, default to Web3BuilderAgent
                # In the future, add other specialized agents
                agent = Web3BuilderAgent(config)
                agent.set_llm(llm_manager)
            
            self.agents[agent_id] = agent
            
            logger.info(f"Created agent: {agent_id} ({config.type.value})")
            return agent_id
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents"""
        return [agent.get_agent_info() for agent in self.agents.values()]
    
    async def execute_task(
        self, 
        agent_id: str, 
        task_type: str, 
        input_data: Dict[str, Any]
    ) -> AgentTask:
        """Execute a task with a specific agent"""
        try:
            agent = self.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Create task
            task = AgentTask(
                id=str(uuid4()),
                type=task_type,
                description=f"{task_type} task for {agent_id}",
                input_data=input_data,
                created_at=datetime.utcnow().isoformat()
            )
            
            self.active_tasks[task.id] = task
            
            logger.info(f"Executing task {task.id} with agent {agent_id}")
            
            # Execute task
            completed_task = await agent.execute_task(task)
            
            # Update task completion time
            completed_task.completed_at = datetime.utcnow().isoformat()
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            return completed_task
            
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            raise
    
    def create_workflow(self, name: str, description: str) -> str:
        """Create a new workflow"""
        workflow = Workflow(name, description)
        self.workflows[workflow.id] = workflow
        logger.info(f"Created workflow: {workflow.id} ({name})")
        return workflow.id
    
    def add_workflow_step(
        self,
        workflow_id: str,
        agent_type: AgentType,
        task_type: str,
        input_data: Dict[str, Any],
        depends_on: Optional[List[str]] = None
    ) -> str:
        """Add a step to a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        step = WorkflowStep(agent_type, task_type, input_data, depends_on)
        workflow.add_step(step)
        
        logger.info(f"Added step {step.id} to workflow {workflow_id}")
        return step.id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow"""
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow.status = AgentStatus.RUNNING
            logger.info(f"Starting workflow execution: {workflow_id}")
            
            while not workflow.is_completed():
                ready_steps = workflow.get_ready_steps()
                
                if not ready_steps:
                    # Check if we're stuck (no ready steps but not completed)
                    incomplete_steps = [s for s in workflow.steps if s.status == AgentStatus.IDLE]
                    if incomplete_steps:
                        error_msg = f"Workflow {workflow_id} is stuck - no ready steps available"
                        logger.error(error_msg)
                        workflow.status = AgentStatus.ERROR
                        break
                    continue
                
                # Execute ready steps in parallel
                tasks = []
                for step in ready_steps:
                    step.status = AgentStatus.RUNNING
                    task = self._execute_workflow_step(workflow, step)
                    tasks.append(task)
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Determine final workflow status
            if any(step.status == AgentStatus.ERROR for step in workflow.steps):
                workflow.status = AgentStatus.ERROR
            else:
                workflow.status = AgentStatus.COMPLETED
                workflow.completed_at = datetime.utcnow().isoformat()
            
            # Collect results
            workflow.results = {
                step.id: step.result for step in workflow.steps if step.result
            }
            
            logger.info(f"Workflow {workflow_id} completed with status: {workflow.status.value}")
            
            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "results": workflow.results,
                "completed_at": workflow.completed_at
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            if workflow_id in self.workflows:
                self.workflows[workflow_id].status = AgentStatus.ERROR
            raise
    
    async def _execute_workflow_step(self, workflow: Workflow, step: WorkflowStep):
        """Execute a single workflow step"""
        try:
            # Find or create appropriate agent
            agent_id = self._get_or_create_agent_for_step(step)
            
            # Prepare input data with dependencies
            input_data = step.input_data.copy()
            
            # Add results from dependent steps
            for dep_id in step.depends_on:
                dep_step = next((s for s in workflow.steps if s.id == dep_id), None)
                if dep_step and dep_step.result:
                    input_data[f"dependency_{dep_id}"] = dep_step.result
            
            # Execute task
            task = await self.execute_task(agent_id, step.task_type, input_data)
            
            if task.status == AgentStatus.COMPLETED:
                step.status = AgentStatus.COMPLETED
                step.result = task.output_data
            else:
                step.status = AgentStatus.ERROR
                step.error = task.error_message
            
        except Exception as e:
            step.status = AgentStatus.ERROR
            step.error = str(e)
            logger.error(f"Error executing workflow step {step.id}: {str(e)}")
    
    def _get_or_create_agent_for_step(self, step: WorkflowStep) -> str:
        """Get or create an agent for a workflow step"""
        # Look for existing agent of the required type
        for agent_id, agent in self.agents.items():
            if agent.type == step.agent_type and agent.status == AgentStatus.IDLE:
                return agent_id
        
        # Create new agent if none available
        config = AgentConfig(
            name=f"{step.agent_type.value}_workflow",
            type=step.agent_type,
            description=f"Agent for workflow step {step.id}"
        )
        
        return self.create_agent(config)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "created_at": workflow.created_at,
            "completed_at": workflow.completed_at,
            "steps": [
                {
                    "id": step.id,
                    "agent_type": step.agent_type.value,
                    "task_type": step.task_type,
                    "status": step.status.value,
                    "depends_on": step.depends_on,
                    "error": step.error
                }
                for step in workflow.steps
            ]
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        return [self.get_workflow_status(wf_id) for wf_id in self.workflows.keys()]
    
    async def chat_with_agent(
        self, 
        agent_id: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Chat with a specific agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        return await agent.process_message(message, context)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "agents": {
                "total": len(self.agents),
                "by_type": {
                    agent_type.value: sum(1 for agent in self.agents.values() if agent.type == agent_type)
                    for agent_type in AgentType
                },
                "by_status": {
                    status.value: sum(1 for agent in self.agents.values() if agent.status == status)
                    for status in AgentStatus
                }
            },
            "workflows": {
                "total": len(self.workflows),
                "by_status": {
                    status.value: sum(1 for wf in self.workflows.values() if wf.status == status)
                    for status in AgentStatus
                }
            },
            "active_tasks": len(self.active_tasks)
        }

# Global agent manager instance
agent_manager = AgentManager()