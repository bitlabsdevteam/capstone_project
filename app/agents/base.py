"""Base agent framework for Vizuara multi-agent system"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from enum import Enum
from langchain.agents import AgentExecutor
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from app.core.logging import logger

class AgentType(str, Enum):
    """Types of agents in the system"""
    WEB3_BUILDER = "web3_builder"
    CODE_GENERATOR = "code_generator"
    SMART_CONTRACT = "smart_contract"
    UI_DESIGNER = "ui_designer"
    COORDINATOR = "coordinator"
    VALIDATOR = "validator"
    ANALYSIS = "analysis"

class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"

class AgentTask(BaseModel):
    """Agent task model"""
    id: str
    type: str
    description: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.IDLE
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentConfig(BaseModel):
    """Agent configuration model"""
    name: str
    type: AgentType
    description: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tools: List[str] = []
    memory_type: str = "buffer"
    max_memory_size: int = 10
    system_prompt: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.type = config.type
        self.status = AgentStatus.IDLE
        self.current_task: Optional[AgentTask] = None
        self.task_history: List[AgentTask] = []
        
        # Initialize memory
        self.memory = self._initialize_memory()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize LLM (will be set by agent manager)
        self.llm = None
        
        logger.info(f"Initialized agent: {self.name} ({self.type.value})")
    
    def _initialize_memory(self) -> ConversationBufferMemory:
        """Initialize agent memory"""
        if self.config.memory_type == "buffer":
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=self.config.max_memory_size * 100
            )
        # Add other memory types as needed
        return ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    @abstractmethod
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize agent-specific tools"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a specific task"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a message and return response"""
        try:
            self.status = AgentStatus.RUNNING
            
            # Add context to memory if provided
            if context:
                context_message = f"Context: {context}"
                self.memory.chat_memory.add_message(SystemMessage(content=context_message))
            
            # Add user message to memory
            self.memory.chat_memory.add_message(HumanMessage(content=message))
            
            # Get response from agent
            response = await self._generate_response(message, context)
            
            # Add AI response to memory
            self.memory.chat_memory.add_message(AIMessage(content=response))
            
            self.status = AgentStatus.COMPLETED
            return response
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            raise
    
    @abstractmethod
    async def _generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using LLM and tools"""
        pass
    
    def set_llm(self, llm):
        """Set the LLM for this agent"""
        self.llm = llm
    
    def add_task_to_history(self, task: AgentTask):
        """Add completed task to history"""
        self.task_history.append(task)
        # Keep only recent tasks to prevent memory bloat
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-50:]
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "current_task": self.current_task.dict() if self.current_task else None,
            "task_history_count": len(self.task_history),
            "tools": [tool.name for tool in self.tools],
            "config": self.config.dict(exclude={"additional_config"})
        }
    
    def clear_memory(self):
        """Clear agent memory"""
        self.memory.clear()
        logger.info(f"Cleared memory for agent: {self.name}")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of agent memory"""
        messages = self.memory.chat_memory.messages
        return {
            "message_count": len(messages),
            "recent_messages": [
                {"role": msg.__class__.__name__, "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content}
                for msg in messages[-5:]
            ]
        }