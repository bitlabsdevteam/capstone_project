"""Gemini LLM provider implementation"""

import google.generativeai as genai
from typing import List, Dict, Any, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, LLMConfig, LLMProvider, MessageRole
from app.core.logging import logger

class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.available_models = [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
    
    def _convert_messages_to_gemini_format(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Convert messages to Gemini format"""
        gemini_messages = []
        
        for msg in messages:
            # Gemini uses 'user' and 'model' roles
            if msg.role == MessageRole.SYSTEM:
                # System messages are treated as user messages with special formatting
                gemini_messages.append({
                    "role": "user",
                    "parts": [f"System: {msg.content}"]
                })
            elif msg.role == MessageRole.USER:
                gemini_messages.append({
                    "role": "user",
                    "parts": [msg.content]
                })
            elif msg.role == MessageRole.ASSISTANT:
                gemini_messages.append({
                    "role": "model",
                    "parts": [msg.content]
                })
        
        return gemini_messages
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using Gemini"""
        try:
            # Initialize the model
            model = genai.GenerativeModel(self.model)
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_output_tokens=self.config.max_tokens,
            )
            
            # Add additional parameters
            if self.config.additional_params:
                for key, value in self.config.additional_params.items():
                    if hasattr(generation_config, key):
                        setattr(generation_config, key, value)
            
            # Override with kwargs
            for key, value in kwargs.items():
                if hasattr(generation_config, key):
                    setattr(generation_config, key, value)
            
            logger.info(f"Making Gemini chat completion request with model: {self.model}")
            
            # For single message, use generate_content
            if len(gemini_messages) == 1:
                response = await model.generate_content_async(
                    gemini_messages[0]["parts"][0],
                    generation_config=generation_config
                )
            else:
                # For multi-turn conversation, use chat
                chat = model.start_chat(history=gemini_messages[:-1])
                response = await chat.send_message_async(
                    gemini_messages[-1]["parts"][0],
                    generation_config=generation_config
                )
            
            return LLMResponse(
                content=response.text,
                provider=LLMProvider.GEMINI,
                model=self.model,
                usage={
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', None),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', None),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', None)
                } if hasattr(response, 'usage_metadata') else None,
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                    "safety_ratings": [rating.category.name for rating in response.candidates[0].safety_ratings] if response.candidates else None
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini chat completion error: {str(e)}")
            raise
    
    async def stream_chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using Gemini"""
        try:
            # Initialize the model
            model = genai.GenerativeModel(self.model)
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_output_tokens=self.config.max_tokens,
            )
            
            # Add additional parameters
            if self.config.additional_params:
                for key, value in self.config.additional_params.items():
                    if hasattr(generation_config, key):
                        setattr(generation_config, key, value)
            
            # Override with kwargs
            for key, value in kwargs.items():
                if hasattr(generation_config, key):
                    setattr(generation_config, key, value)
            
            logger.info(f"Making Gemini streaming chat completion request with model: {self.model}")
            
            # For single message, use generate_content with streaming
            if len(gemini_messages) == 1:
                response_stream = await model.generate_content_async(
                    gemini_messages[0]["parts"][0],
                    generation_config=generation_config,
                    stream=True
                )
            else:
                # For multi-turn conversation, use chat with streaming
                chat = model.start_chat(history=gemini_messages[:-1])
                response_stream = await chat.send_message_async(
                    gemini_messages[-1]["parts"][0],
                    generation_config=generation_config,
                    stream=True
                )
            
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming chat completion error: {str(e)}")
            raise
    
    async def text_completion(
        self, 
        prompt: str, 
        **kwargs
    ) -> LLMResponse:
        """Generate text completion using Gemini"""
        # Gemini uses chat completion format, so convert prompt to message
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        return await self.chat_completion(messages, **kwargs)
    
    async def validate_connection(self) -> bool:
        """Validate Gemini connection and API key"""
        try:
            # Make a simple request to validate the connection
            model = genai.GenerativeModel("gemini-pro")
            response = await model.generate_content_async("Hello")
            logger.info("Gemini connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Gemini connection validation failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        return self.available_models