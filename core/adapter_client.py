"""
Adapter-based Client
====================

Unified client for multi-provider LLM access using the adapter system.
This provides an alternative to the Claude SDK client for non-Claude providers.
"""

from pathlib import Path
from typing import Optional

from adapters.registry import AdapterRegistry
from adapters.base import BaseAdapter
from adapters.init_adapters import register_all_adapters
from config.loader import ConfigLoader
from config.schema import SeaForgeConfig


class AdapterClient:
    """Unified client for all LLM providers via adapter system."""
    
    def __init__(self, config: Optional[SeaForgeConfig] = None):
        """
        Initialize adapter client.
        
        Args:
            config: Optional SeaForgeConfig. If None, loads from environment/files.
        """
        # Ensure adapters are registered
        register_all_adapters()
        
        # Load configuration
        self.config = config or ConfigLoader.load()
        
        # Initialize adapter
        self.adapter = self._initialize_adapter()
    
    def _initialize_adapter(self) -> BaseAdapter:
        """
        Initialize the appropriate adapter based on configuration.
        
        Returns:
            Configured adapter instance
            
        Raises:
            ValueError: If no provider is available or configured
        """
        provider = self.config.default_provider
        
        # Auto-select provider if needed
        if provider == "auto":
            provider = self._auto_select_provider()
        
        # Get provider configuration
        provider_config = getattr(self.config, provider, None)
        if not provider_config:
            raise ValueError(f"No configuration for provider: {provider}")
        
        # Convert Pydantic model to dict
        config_dict = provider_config.model_dump()
        
        # Create adapter instance
        return AdapterRegistry.get_adapter(provider, config_dict)
    
    def _auto_select_provider(self) -> str:
        """
        Auto-select best available provider.
        
        Priority: Providers with API keys → Ollama (local)
        
        Returns:
            Provider name
            
        Raises:
            ValueError: If no provider is configured
        """
        # Prioritize providers with API keys (more likely to work)
        if self.config.openrouter and self.config.openrouter.enabled and self.config.openrouter.api_key:
            return "openrouter"
        
        if self.config.openai and self.config.openai.enabled and self.config.openai.api_key:
            return "openai"
        
        # Check Ollama last (requires local installation)
        if self.config.ollama and self.config.ollama.enabled:
            return "ollama"
        
        raise ValueError(
            "No LLM provider configured. Please set up at least one provider:\n"
            "  - Ollama: Install from https://ollama.com\n"
            "  - OpenRouter: Set OPENROUTER_API_KEY environment variable\n"
            "  - OpenAI: Set OPENAI_API_KEY environment variable"
        )
    
    async def execute_task(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Execute agent task using configured adapter.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Optional model override
            **kwargs: Additional arguments passed to adapter
            
        Returns:
            AgentResponse from the adapter
        """
        return await self.adapter.execute(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
    
    async def test_connection(self):
        """
        Test connection to the configured provider.
        
        Returns:
            Dict with 'ok' and 'message' keys
        """
        return await self.adapter.test_connection()
    
    def get_provider_info(self) -> dict:
        """
        Get information about the active provider.
        
        Returns:
            Dict with provider name and configuration
        """
        return {
            "provider": self.adapter.get_provider_name(),
            "models": self.adapter.list_models(),
        }


async def create_adapter_client(
    project_dir: Path,
    model: str,
    config: Optional[SeaForgeConfig] = None,
) -> AdapterClient:
    """
    Create an adapter-based client for non-Claude providers.
    
    Args:
        project_dir: Project directory (for compatibility with existing code)
        model: Model to use (provider-specific)
        config: Optional configuration override
        
    Returns:
        Configured AdapterClient instance
    """
    client = AdapterClient(config)
    
    # Test connection
    test_result = await client.test_connection()
    if not test_result["ok"]:
        raise RuntimeError(
            f"Provider not available: {test_result['message']}\n"
            f"Provider: {client.adapter.get_provider_name()}"
        )
    
    print(f"✓ Using provider: {client.adapter.get_provider_name()}")
    print(f"  Model: {model}")
    
    return client
