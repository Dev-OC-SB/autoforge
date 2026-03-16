"""
Multi-Provider Adapter System
==============================

Provides a flexible adapter pattern for supporting multiple LLM providers
(Ollama, OpenRouter, OpenAI-compatible APIs) without requiring Claude Code CLI.
"""

from .base import BaseAdapter, ModelInfo, AgentResponse
from .registry import AdapterRegistry

__all__ = [
    "BaseAdapter",
    "ModelInfo",
    "AgentResponse",
    "AdapterRegistry",
]
