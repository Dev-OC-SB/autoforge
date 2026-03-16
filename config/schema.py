"""
Configuration Schema
====================

Pydantic models for configuration validation and type safety.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ProviderConfig(BaseModel):
    """Base provider configuration."""
    
    enabled: bool = True
    priority: int = 0  # Higher priority = preferred


class OllamaConfig(ProviderConfig):
    """Ollama provider configuration."""
    
    base_url: str = "http://localhost:11434"
    default_model: str = "codellama:13b"
    timeout: int = 300


class OpenRouterConfig(ProviderConfig):
    """OpenRouter provider configuration."""
    
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-3.5-sonnet"
    site_url: Optional[str] = None
    app_name: Optional[str] = "SeaForge"


class OpenAIConfig(ProviderConfig):
    """OpenAI-compatible provider configuration."""
    
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4-turbo"
    organization: Optional[str] = None


class SeaForgeConfig(BaseModel):
    """Main SeaForge configuration."""
    
    # Provider selection
    default_provider: str = "auto"  # auto, ollama, openrouter, openai
    
    # Provider configurations
    ollama: Optional[OllamaConfig] = None
    openrouter: Optional[OpenRouterConfig] = None
    openai: Optional[OpenAIConfig] = None
    
    # Server settings
    server_host: str = "127.0.0.1"
    server_port: int = 8888
    
    # Agent settings
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Optional integrations
    n8n_webhook_url: Optional[str] = None
