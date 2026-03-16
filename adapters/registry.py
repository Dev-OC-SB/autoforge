"""
Adapter Registry
================

Central registry for managing and retrieving adapter instances.
"""

from typing import Dict, Type

from .base import BaseAdapter


class AdapterRegistry:
    """Registry for LLM provider adapters."""
    
    _adapters: Dict[str, Type[BaseAdapter]] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseAdapter]) -> None:
        """
        Register an adapter class.
        
        Args:
            name: Provider name (e.g., 'ollama', 'openrouter')
            adapter_class: Adapter class to register
        """
        cls._adapters[name] = adapter_class
    
    @classmethod
    def get_adapter(cls, name: str, config: Dict) -> BaseAdapter:
        """
        Get adapter instance by name.
        
        Args:
            name: Provider name
            config: Configuration dict for the adapter
            
        Returns:
            Configured adapter instance
            
        Raises:
            ValueError: If adapter not found
        """
        if name not in cls._adapters:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(f"Unknown adapter: {name}. Available: {available}")
        
        adapter_class = cls._adapters[name]
        return adapter_class(config)
    
    @classmethod
    def list_available(cls) -> list[str]:
        """
        List all registered adapter names.
        
        Returns:
            List of provider names
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if an adapter is registered.
        
        Args:
            name: Provider name
            
        Returns:
            True if registered, False otherwise
        """
        return name in cls._adapters
