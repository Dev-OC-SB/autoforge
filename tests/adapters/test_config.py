"""
Test Configuration System
==========================

Tests for configuration loading and validation.
"""

import os
import pytest
from config.loader import ConfigLoader
from config.schema import SeaForgeConfig, OllamaConfig, OpenRouterConfig


def test_config_loader_defaults():
    """Test config loader with no files or env vars."""
    # Clear relevant env vars
    env_backup = {}
    for key in ["SEAFORGE_PROVIDER", "OPENROUTER_API_KEY", "OLLAMA_BASE_URL"]:
        env_backup[key] = os.environ.pop(key, None)
    
    try:
        config = ConfigLoader.load()
        assert isinstance(config, SeaForgeConfig)
        assert config.default_provider == "auto"
    finally:
        # Restore env vars
        for key, value in env_backup.items():
            if value is not None:
                os.environ[key] = value


def test_config_env_override_provider():
    """Test environment variable override for provider."""
    os.environ["SEAFORGE_PROVIDER"] = "ollama"
    
    try:
        config = ConfigLoader.load()
        assert config.default_provider == "ollama"
    finally:
        os.environ.pop("SEAFORGE_PROVIDER", None)


def test_config_env_override_openrouter():
    """Test environment variable override for OpenRouter."""
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    os.environ["OPENROUTER_MODEL"] = "test-model"
    
    try:
        config = ConfigLoader.load()
        assert config.openrouter is not None
        assert config.openrouter.api_key == "test-key"
        assert config.openrouter.default_model == "test-model"
        assert config.openrouter.enabled is True
    finally:
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("OPENROUTER_MODEL", None)


def test_config_env_override_ollama():
    """Test environment variable override for Ollama."""
    os.environ["OLLAMA_BASE_URL"] = "http://custom:11434"
    os.environ["OLLAMA_MODEL"] = "custom-model"
    
    try:
        config = ConfigLoader.load()
        assert config.ollama is not None
        assert config.ollama.base_url == "http://custom:11434"
        assert config.ollama.default_model == "custom-model"
        assert config.ollama.enabled is True
    finally:
        os.environ.pop("OLLAMA_BASE_URL", None)
        os.environ.pop("OLLAMA_MODEL", None)


def test_ollama_config_validation():
    """Test Ollama config validation."""
    config = OllamaConfig(
        base_url="http://localhost:11434",
        default_model="codellama:13b",
        timeout=300,
    )
    
    assert config.base_url == "http://localhost:11434"
    assert config.default_model == "codellama:13b"
    assert config.timeout == 300
    assert config.enabled is True


def test_openrouter_config_validation():
    """Test OpenRouter config validation."""
    config = OpenRouterConfig(
        api_key="test-key",
        default_model="anthropic/claude-3.5-sonnet",
    )
    
    assert config.api_key == "test-key"
    assert config.default_model == "anthropic/claude-3.5-sonnet"
    assert config.base_url == "https://openrouter.ai/api/v1"
    assert config.enabled is True
