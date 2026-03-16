"""
Test Ollama Adapter
===================

Tests for Ollama adapter functionality.
"""

import pytest
from adapters.ollama import OllamaAdapter


def test_ollama_adapter_init():
    """Test Ollama adapter initialization."""
    config = {
        "base_url": "http://localhost:11434",
        "default_model": "codellama:13b",
        "timeout": 300,
    }
    
    adapter = OllamaAdapter(config)
    assert adapter.base_url == "http://localhost:11434"
    assert adapter.default_model == "codellama:13b"
    assert adapter.timeout == 300


def test_ollama_adapter_defaults():
    """Test Ollama adapter with default values."""
    adapter = OllamaAdapter({})
    assert adapter.base_url == "http://localhost:11434"
    assert adapter.default_model == "codellama:13b"
    assert adapter.timeout == 300


def test_ollama_provider_name():
    """Test Ollama provider name."""
    adapter = OllamaAdapter({})
    assert adapter.get_provider_name() == "ollama"


def test_ollama_list_models():
    """Test Ollama list_models returns list."""
    adapter = OllamaAdapter({})
    models = adapter.list_models()
    assert isinstance(models, list)
    # May be empty if Ollama not running, but should be a list


@pytest.mark.asyncio
async def test_ollama_test_connection_offline():
    """Test Ollama connection test when offline."""
    adapter = OllamaAdapter({"base_url": "http://localhost:99999"})
    result = await adapter.test_connection()
    
    assert "ok" in result
    assert "message" in result
    assert result["ok"] is False
