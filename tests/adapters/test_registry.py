"""
Test Adapter Registry
=====================

Tests for adapter registration and retrieval.
"""

import pytest
from adapters.registry import AdapterRegistry
from adapters.ollama import OllamaAdapter
from adapters.openrouter import OpenRouterAdapter
from adapters.openai_compatible import OpenAICompatibleAdapter


def test_adapter_registration():
    """Test adapter registration."""
    # Register a test adapter
    AdapterRegistry.register("test_ollama", OllamaAdapter)
    
    # Verify it's registered
    assert AdapterRegistry.is_registered("test_ollama")
    assert "test_ollama" in AdapterRegistry.list_available()


def test_get_adapter_ollama():
    """Test getting Ollama adapter."""
    AdapterRegistry.register("ollama", OllamaAdapter)
    
    config = {
        "base_url": "http://localhost:11434",
        "default_model": "codellama:13b",
    }
    
    adapter = AdapterRegistry.get_adapter("ollama", config)
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.get_provider_name() == "ollama"


def test_get_adapter_openrouter():
    """Test getting OpenRouter adapter."""
    AdapterRegistry.register("openrouter", OpenRouterAdapter)
    
    config = {
        "api_key": "test-key",
        "base_url": "https://openrouter.ai/api/v1",
    }
    
    adapter = AdapterRegistry.get_adapter("openrouter", config)
    assert isinstance(adapter, OpenRouterAdapter)
    assert adapter.get_provider_name() == "openrouter"


def test_get_adapter_openai():
    """Test getting OpenAI adapter."""
    AdapterRegistry.register("openai", OpenAICompatibleAdapter)
    
    config = {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
    }
    
    adapter = AdapterRegistry.get_adapter("openai", config)
    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert adapter.get_provider_name() == "openai_compatible"


def test_get_unknown_adapter():
    """Test getting unknown adapter raises error."""
    with pytest.raises(ValueError, match="Unknown adapter"):
        AdapterRegistry.get_adapter("unknown", {})


def test_list_available_adapters():
    """Test listing available adapters."""
    # Clear and register test adapters
    AdapterRegistry._adapters.clear()
    AdapterRegistry.register("ollama", OllamaAdapter)
    AdapterRegistry.register("openrouter", OpenRouterAdapter)
    
    available = AdapterRegistry.list_available()
    assert "ollama" in available
    assert "openrouter" in available
    assert len(available) == 2
