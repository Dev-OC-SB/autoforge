"""
Unified Client
==============

Unified client interface that works with both Claude SDK and adapter-based providers.
Provides a consistent API regardless of the underlying provider.
"""

import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator, Any, Union

from claude_agent_sdk import ClaudeSDKClient

from core.adapter_client import AdapterClient
from adapters.base import AgentResponse
from config.loader import ConfigLoader
from config.schema import SeaForgeConfig
from core.message_adapters import MessageAdapter, StreamingMessageAdapter, AssistantMessage


class UnifiedClient:
    """
    Unified client that wraps either ClaudeSDKClient or AdapterClient.
    
    Provides a consistent interface for agent.py to use regardless of provider.
    """
    
    def __init__(
        self,
        backend: Union[ClaudeSDKClient, AdapterClient],
        provider_type: str,
        model: str,
    ):
        """
        Initialize unified client.
        
        Args:
            backend: Either ClaudeSDKClient or AdapterClient instance
            provider_type: Provider identifier (claude_cli, ollama, openrouter, openai)
            model: Model name being used
        """
        self.backend = backend
        self.provider_type = provider_type
        self.model = model
        self._is_claude_sdk = isinstance(backend, ClaudeSDKClient)
        self._current_prompt: Optional[str] = None
        self._current_response: Optional[AgentResponse] = None
        self._stream_mode: bool = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self._is_claude_sdk:
            await self.backend.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._is_claude_sdk:
            await self.backend.__aexit__(exc_type, exc_val, exc_tb)
    
    async def query(self, message: str, stream: bool = False) -> None:
        """
        Send a query to the LLM.
        
        Args:
            message: The prompt/query to send
            stream: Enable streaming responses (default: False for backward compatibility)
        """
        self._stream_mode = stream
        
        if self._is_claude_sdk:
            # Claude SDK client (doesn't support streaming parameter)
            await self.backend.query(message)
        else:
            # Adapter-based client
            # Store the prompt for later execution in receive_response()
            self._current_prompt = message
    
    async def receive_response(self) -> AsyncGenerator[AssistantMessage, None]:
        """
        Receive response from the LLM as an async generator.
        
        Yields:
            AssistantMessage objects compatible with Claude SDK format
        """
        if self._is_claude_sdk:
            # Claude SDK client - pass through directly
            async for msg in self.backend.receive_response():
                yield msg
        else:
            # Adapter-based client - execute and convert to message format
            if self._current_prompt is None:
                raise RuntimeError("No query sent. Call query() first.")
            
            if self._stream_mode:
                # Streaming mode - use execute_stream if available
                if hasattr(self.backend.adapter, 'execute_stream'):
                    # Get streaming token generator
                    token_generator = self.backend.adapter.execute_stream(
                        prompt=self._current_prompt,
                        model=self.model,
                    )
                    
                    # Convert to streaming message format
                    streaming_adapter = StreamingMessageAdapter(token_generator=token_generator)
                    async for msg in streaming_adapter:
                        yield msg
                else:
                    # Fallback to non-streaming if not supported
                    response = await self.backend.execute_task(
                        prompt=self._current_prompt,
                        model=self.model,
                    )
                    self._current_response = response
                    streaming_adapter = StreamingMessageAdapter(response_text=response.content)
                    async for msg in streaming_adapter:
                        yield msg
            else:
                # Non-streaming mode (default)
                response = await self.backend.execute_task(
                    prompt=self._current_prompt,
                    model=self.model,
                )
                
                # Store response for metadata access
                self._current_response = response
                
                # Convert to streaming format
                streaming_adapter = StreamingMessageAdapter(response_text=response.content)
                async for msg in streaming_adapter:
                    yield msg
            
            # Clear prompt after processing
            self._current_prompt = None
    
    def get_provider_type(self) -> str:
        """
        Get the provider type.
        
        Returns:
            Provider identifier (claude_cli, ollama, openrouter, openai)
        """
        return self.provider_type
    
    def get_model(self) -> str:
        """
        Get the model name.
        
        Returns:
            Model identifier
        """
        return self.model
    
    def get_usage_stats(self) -> Optional[dict]:
        """
        Get usage statistics from the last response.
        
        Returns:
            Dict with token counts and cost, or None if not available
        """
        if self._is_claude_sdk:
            # Claude SDK doesn't expose usage stats directly
            return None
        
        if self._current_response is None:
            return None
        
        return {
            "input_tokens": self._current_response.input_tokens,
            "output_tokens": self._current_response.output_tokens,
            "total_tokens": self._current_response.input_tokens + self._current_response.output_tokens,
            "cost_usd": self._current_response.cost_usd,
            "model": self._current_response.model_used,
        }


async def detect_available_provider(config: Optional[SeaForgeConfig] = None) -> tuple[str, str]:
    """
    Detect the best available provider.
    
    Priority: Explicit config → Ollama → OpenRouter → OpenAI → Claude CLI
    
    Args:
        config: Optional configuration override
        
    Returns:
        Tuple of (provider_name, reason)
        
    Raises:
        RuntimeError: If no provider is available
    """
    import shutil
    import httpx
    
    # Load config if not provided
    if config is None:
        config = ConfigLoader.load()
    
    # Check explicit provider setting
    if config.default_provider != "auto":
        return (config.default_provider, f"Explicitly configured: {config.default_provider}")
    
    # Check Ollama (priority 1)
    if config.ollama and config.ollama.enabled:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{config.ollama.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    if models:
                        return ("ollama", f"Ollama running with {len(models)} models")
        except Exception:
            pass
    
    # Check OpenRouter (priority 2)
    if config.openrouter and config.openrouter.enabled and config.openrouter.api_key:
        return ("openrouter", "OpenRouter API key configured")
    
    # Check OpenAI (priority 3)
    if config.openai and config.openai.enabled and config.openai.api_key:
        return ("openai", "OpenAI API key configured")
    
    # Check Claude CLI (priority 4)
    if shutil.which("claude") is not None:
        return ("claude_cli", "Claude CLI installed")
    
    # No provider available
    raise RuntimeError(
        "No LLM provider available. Please set up at least one:\n"
        "  1. Ollama: Install from https://ollama.com and run 'ollama pull codellama:13b'\n"
        "  2. OpenRouter: Set OPENROUTER_API_KEY environment variable\n"
        "  3. OpenAI: Set OPENAI_API_KEY environment variable\n"
        "  4. Claude CLI: Install from https://claude.ai/download"
    )


def get_provider_model(provider: str, config: SeaForgeConfig, requested_model: Optional[str] = None) -> str:
    """
    Get the appropriate model for a provider.
    
    Args:
        provider: Provider name
        config: Configuration object
        requested_model: Optional specific model request
        
    Returns:
        Model identifier for the provider
    """
    if requested_model:
        return requested_model
    
    # Get default model from provider config
    if provider == "ollama" and config.ollama:
        return config.ollama.default_model
    elif provider == "openrouter" and config.openrouter:
        return config.openrouter.default_model
    elif provider == "openai" and config.openai:
        return config.openai.default_model
    elif provider == "claude_cli":
        # Use the requested model for Claude CLI (passed from create_client)
        return requested_model or "claude-sonnet-4-5"
    
    # Fallback defaults
    defaults = {
        "ollama": "codellama:13b",
        "openrouter": "anthropic/claude-3.5-sonnet",
        "openai": "gpt-4-turbo",
        "claude_cli": "claude-sonnet-4-5",
    }
    return defaults.get(provider, "claude-sonnet-4-5")
