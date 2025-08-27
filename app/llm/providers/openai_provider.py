"""OpenAI LLM provider implementation"""

import openai
from typing import List, Dict, Any, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, LLMConfig, LLMProvider
from app.core.logging import logger

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=config.api_key)
        self.available_models = [
            "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            "text-davinci-003", "text-davinci-002"
        ]
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using OpenAI"""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
            }
            
            if self.config.max_tokens:
                params["max_tokens"] = self.config.max_tokens
            
            # Add additional parameters
            if self.config.additional_params:
                params.update(self.config.additional_params)
            
            # Override with kwargs
            params.update(kwargs)
            
            logger.info(f"Making OpenAI chat completion request with model: {self.model}")
            
            response = await self.client.chat.completions.create(**params)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=LLMProvider.OPENAI,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {str(e)}")
            raise
    
    async def stream_chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using OpenAI"""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "stream": True
            }
            
            if self.config.max_tokens:
                params["max_tokens"] = self.config.max_tokens
            
            # Add additional parameters
            if self.config.additional_params:
                params.update(self.config.additional_params)
            
            # Override with kwargs
            params.update(kwargs)
            
            logger.info(f"Making OpenAI streaming chat completion request with model: {self.model}")
            
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming chat completion error: {str(e)}")
            raise
    
    async def text_completion(
        self, 
        prompt: str, 
        **kwargs
    ) -> LLMResponse:
        """Generate text completion using OpenAI"""
        try:
            # For newer models, use chat completion with system message
            if self.model.startswith("gpt-"):
                messages = [ChatMessage(role="user", content=prompt)]
                return await self.chat_completion(messages, **kwargs)
            
            # For older completion models
            params = {
                "model": self.model,
                "prompt": prompt,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
            }
            
            if self.config.max_tokens:
                params["max_tokens"] = self.config.max_tokens
            
            # Add additional parameters
            if self.config.additional_params:
                params.update(self.config.additional_params)
            
            # Override with kwargs
            params.update(kwargs)
            
            logger.info(f"Making OpenAI text completion request with model: {self.model}")
            
            response = await self.client.completions.create(**params)
            
            return LLMResponse(
                content=response.choices[0].text,
                provider=LLMProvider.OPENAI,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI text completion error: {str(e)}")
            raise
    
    async def validate_connection(self) -> bool:
        """Validate OpenAI connection and API key"""
        try:
            # Make a simple request to validate the connection
            await self.client.models.list()
            logger.info("OpenAI connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        return self.available_models