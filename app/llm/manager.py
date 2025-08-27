"""LLM Manager for model interoperability and switching"""

from typing import Dict, List, Optional, AsyncGenerator, Union
from app.llm.base import (
    BaseLLMProvider, ChatMessage, LLMResponse, LLMConfig, LLMProvider
)
from app.llm.providers import OpenAIProvider, DeepSeekProvider, GeminiProvider
from app.core.config import settings
from app.core.logging import logger
import litellm
from litellm import acompletion, aembedding

class LLMManager:
    """Manager for LLM providers with model interoperability"""
    
    def __init__(self):
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.current_provider: Optional[LLMProvider] = None
        self.current_model: Optional[str] = None
        
        # Configure LiteLLM
        litellm.set_verbose = settings.LITELLM_LOG == "DEBUG"
        litellm.drop_params = settings.LITELLM_DROP_PARAMS
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available LLM providers"""
        try:
            # Initialize OpenAI provider
            if settings.OPENAI_API_KEY:
                openai_config = LLMConfig(
                    provider=LLMProvider.OPENAI,
                    model=settings.DEFAULT_MODEL if settings.DEFAULT_LLM_PROVIDER == "openai" else "gpt-3.5-turbo",
                    api_key=settings.OPENAI_API_KEY
                )
                self.providers[LLMProvider.OPENAI] = OpenAIProvider(openai_config)
                logger.info("OpenAI provider initialized")
            
            # Initialize DeepSeek provider
            if settings.DEEPSEEK_API_KEY:
                deepseek_config = LLMConfig(
                    provider=LLMProvider.DEEPSEEK,
                    model=settings.DEFAULT_MODEL if settings.DEFAULT_LLM_PROVIDER == "deepseek" else "deepseek-chat",
                    api_key=settings.DEEPSEEK_API_KEY
                )
                self.providers[LLMProvider.DEEPSEEK] = DeepSeekProvider(deepseek_config)
                logger.info("DeepSeek provider initialized")
            
            # Initialize Gemini provider
            if settings.GEMINI_API_KEY:
                gemini_config = LLMConfig(
                    provider=LLMProvider.GEMINI,
                    model=settings.DEFAULT_MODEL if settings.DEFAULT_LLM_PROVIDER == "gemini" else "gemini-pro",
                    api_key=settings.GEMINI_API_KEY
                )
                self.providers[LLMProvider.GEMINI] = GeminiProvider(gemini_config)
                logger.info("Gemini provider initialized")
            
            # Set default provider
            if settings.DEFAULT_LLM_PROVIDER:
                default_provider = LLMProvider(settings.DEFAULT_LLM_PROVIDER)
                if default_provider in self.providers:
                    self.current_provider = default_provider
                    self.current_model = settings.DEFAULT_MODEL
                    logger.info(f"Default provider set to: {default_provider.value}")
            
            if not self.providers:
                logger.warning("No LLM providers initialized. Please check your API keys.")
                
        except Exception as e:
            logger.error(f"Error initializing LLM providers: {str(e)}")
    
    async def switch_provider(self, provider: Union[str, LLMProvider], model: Optional[str] = None) -> bool:
        """Switch to a different LLM provider"""
        try:
            if isinstance(provider, str):
                provider = LLMProvider(provider)
            
            if provider not in self.providers:
                logger.error(f"Provider {provider.value} not available")
                return False
            
            self.current_provider = provider
            
            if model:
                # Update model for the provider
                current_provider_instance = self.providers[provider]
                if model in current_provider_instance.get_available_models():
                    current_provider_instance.model = model
                    self.current_model = model
                else:
                    logger.warning(f"Model {model} not available for {provider.value}")
            
            logger.info(f"Switched to provider: {provider.value}, model: {self.current_model}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching provider: {str(e)}")
            return False
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        provider: Optional[Union[str, LLMProvider]] = None,
        model: Optional[str] = None,
        use_litellm: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion with optional provider/model override"""
        try:
            # Use LiteLLM for cross-provider compatibility
            if use_litellm:
                return await self._litellm_chat_completion(messages, provider, model, **kwargs)
            
            # Use direct provider implementation
            target_provider = self._get_target_provider(provider)
            if not target_provider:
                raise ValueError("No provider available")
            
            provider_instance = self.providers[target_provider]
            
            # Temporarily switch model if specified
            original_model = provider_instance.model
            if model and model in provider_instance.get_available_models():
                provider_instance.model = model
            
            try:
                response = await provider_instance.chat_completion(messages, **kwargs)
                return response
            finally:
                # Restore original model
                provider_instance.model = original_model
                
        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise
    
    async def stream_chat_completion(
        self, 
        messages: List[ChatMessage], 
        provider: Optional[Union[str, LLMProvider]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion"""
        try:
            target_provider = self._get_target_provider(provider)
            if not target_provider:
                raise ValueError("No provider available")
            
            provider_instance = self.providers[target_provider]
            
            # Temporarily switch model if specified
            original_model = provider_instance.model
            if model and model in provider_instance.get_available_models():
                provider_instance.model = model
            
            try:
                async for chunk in provider_instance.stream_chat_completion(messages, **kwargs):
                    yield chunk
            finally:
                # Restore original model
                provider_instance.model = original_model
                
        except Exception as e:
            logger.error(f"Streaming chat completion error: {str(e)}")
            raise
    
    async def _litellm_chat_completion(
        self,
        messages: List[ChatMessage],
        provider: Optional[Union[str, LLMProvider]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Use LiteLLM for cross-provider chat completion"""
        try:
            # Convert messages to LiteLLM format
            litellm_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            # Determine model string for LiteLLM
            if provider and model:
                if isinstance(provider, LLMProvider):
                    provider = provider.value
                model_string = f"{provider}/{model}"
            elif self.current_provider and self.current_model:
                model_string = f"{self.current_provider.value}/{self.current_model}"
            else:
                model_string = "gpt-3.5-turbo"  # fallback
            
            # Set API keys for LiteLLM
            if "openai" in model_string and settings.OPENAI_API_KEY:
                litellm.openai_key = settings.OPENAI_API_KEY
            elif "deepseek" in model_string and settings.DEEPSEEK_API_KEY:
                litellm.api_key = settings.DEEPSEEK_API_KEY
            elif "gemini" in model_string and settings.GEMINI_API_KEY:
                litellm.vertex_ai_key = settings.GEMINI_API_KEY
            
            logger.info(f"Making LiteLLM chat completion request with model: {model_string}")
            
            response = await acompletion(
                model=model_string,
                messages=litellm_messages,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=LLMProvider(provider) if provider else self.current_provider,
                model=model or self.current_model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id,
                    "via_litellm": True
                }
            )
            
        except Exception as e:
            logger.error(f"LiteLLM chat completion error: {str(e)}")
            raise
    
    def _get_target_provider(self, provider: Optional[Union[str, LLMProvider]]) -> Optional[LLMProvider]:
        """Get target provider for request"""
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider)
            return provider if provider in self.providers else None
        return self.current_provider
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [provider.value for provider in self.providers.keys()]
    
    def get_available_models(self, provider: Optional[Union[str, LLMProvider]] = None) -> List[str]:
        """Get available models for a provider"""
        target_provider = self._get_target_provider(provider)
        if target_provider and target_provider in self.providers:
            return self.providers[target_provider].get_available_models()
        return []
    
    async def validate_provider(self, provider: Union[str, LLMProvider]) -> bool:
        """Validate a specific provider connection"""
        if isinstance(provider, str):
            provider = LLMProvider(provider)
        
        if provider in self.providers:
            return await self.providers[provider].validate_connection()
        return False
    
    def get_provider_info(self, provider: Optional[Union[str, LLMProvider]] = None) -> Dict:
        """Get information about a provider"""
        target_provider = self._get_target_provider(provider)
        if target_provider and target_provider in self.providers:
            return self.providers[target_provider].get_provider_info()
        return {}

# Global LLM manager instance
llm_manager = LLMManager()