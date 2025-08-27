"""DeepSeek LLM provider implementation"""

import httpx
import json
from typing import List, Dict, Any, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, LLMConfig, LLMProvider
from app.core.logging import logger

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek LLM provider implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        self.available_models = [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-math"
        ]
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using DeepSeek"""
        try:
            # Convert messages to DeepSeek format
            deepseek_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": deepseek_messages,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "stream": False
            }
            
            if self.config.max_tokens:
                params["max_tokens"] = self.config.max_tokens
            
            # Add additional parameters
            if self.config.additional_params:
                params.update(self.config.additional_params)
            
            # Override with kwargs
            params.update(kwargs)
            
            logger.info(f"Making DeepSeek chat completion request with model: {self.model}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=params,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                provider=LLMProvider.DEEPSEEK,
                model=self.model,
                usage={
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens"),
                    "total_tokens": data.get("usage", {}).get("total_tokens")
                } if data.get("usage") else None,
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "response_id": data.get("id")
                }
            )
            
        except Exception as e:
            logger.error(f"DeepSeek chat completion error: {str(e)}")
            raise
    
    async def stream_chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using DeepSeek"""
        try:
            # Convert messages to DeepSeek format
            deepseek_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": deepseek_messages,
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
            
            logger.info(f"Making DeepSeek streaming chat completion request with model: {self.model}")
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=params,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                    
        except Exception as e:
            logger.error(f"DeepSeek streaming chat completion error: {str(e)}")
            raise
    
    async def text_completion(
        self, 
        prompt: str, 
        **kwargs
    ) -> LLMResponse:
        """Generate text completion using DeepSeek (via chat completion)"""
        # DeepSeek uses chat completion format, so convert prompt to message
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat_completion(messages, **kwargs)
    
    async def validate_connection(self) -> bool:
        """Validate DeepSeek connection and API key"""
        try:
            # Make a simple request to validate the connection
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info("DeepSeek connection validated successfully")
                return True
        except Exception as e:
            logger.error(f"DeepSeek connection validation failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available DeepSeek models"""
        return self.available_models