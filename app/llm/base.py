"""Base LLM provider interface for Vizuara Web3 Application Builder"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel
from enum import Enum

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"

class MessageRole(str, Enum):
    """Message roles for chat completion"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(BaseModel):
    """Chat message model"""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    """LLM response model"""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMConfig(BaseModel):
    """LLM configuration model"""
    provider: LLMProvider
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    additional_params: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
        self.model = config.model
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    async def stream_chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion"""
        pass
    
    @abstractmethod
    async def text_completion(
        self, 
        prompt: str, 
        **kwargs
    ) -> LLMResponse:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate provider connection and API key"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "config": self.config.dict(exclude={"api_key"})
        }