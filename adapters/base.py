"""
Base Adapter Interface
======================

Abstract base class and data models for all LLM provider adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ModelInfo:
    """Information about an available model."""
    
    id: str
    name: str
    context_window: int
    supports_tools: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class AgentResponse:
    """Response from an agent execution."""
    
    content: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_used: str
    metadata: Dict[str, Any]


class BaseAdapter(ABC):
    """Base interface for all LLM provider adapters."""
    
    @abstractmethod
    async def execute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AgentResponse:
        """
        Execute agent task with the provider.
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt
            model: Model identifier (provider-specific)
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            AgentResponse with content, tokens, cost, and metadata
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test if provider is accessible and configured.
        
        Returns:
            Dict with 'ok' (bool) and 'message' (str) keys
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """
        List available models for this provider.
        
        Returns:
            List of ModelInfo objects
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Return provider identifier.
        
        Returns:
            Provider name (e.g., 'ollama', 'openrouter', 'openai')
        """
        pass
