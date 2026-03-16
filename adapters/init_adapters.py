"""
Adapter Initialization
======================

Register all available adapters with the registry.
"""

from .registry import AdapterRegistry
from .ollama import OllamaAdapter
from .openrouter import OpenRouterAdapter
from .openai_compatible import OpenAICompatibleAdapter


def register_all_adapters() -> None:
    """Register all available adapters."""
    AdapterRegistry.register("ollama", OllamaAdapter)
    AdapterRegistry.register("openrouter", OpenRouterAdapter)
    AdapterRegistry.register("openai", OpenAICompatibleAdapter)


# Auto-register on import
register_all_adapters()
