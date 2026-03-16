"""
Provider Detection Service
===========================

Detect available LLM providers and recommend best option.
"""

import httpx
import os
from typing import Dict, Any


class ProviderDetector:
    """Detect available LLM providers."""
    
    @staticmethod
    async def detect_all() -> Dict[str, Dict[str, Any]]:
        """
        Detect all available providers.
        
        Returns:
            Dict mapping provider name to availability info
        """
        results = {}
        
        # Check Ollama
        results["ollama"] = await ProviderDetector._check_ollama()
        
        # Check API keys
        results["openrouter"] = ProviderDetector._check_openrouter_key()
        results["openai"] = ProviderDetector._check_openai_key()
        
        return results
    
    @staticmethod
    async def _check_ollama() -> Dict[str, Any]:
        """
        Check if Ollama is running.
        
        Returns:
            Dict with availability status and details
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return {
                        "available": True,
                        "models": [m["name"] for m in models],
                        "message": f"Ollama running with {len(models)} models",
                    }
        except Exception:
            pass
        
        return {
            "available": False,
            "message": "Ollama not running. Install: https://ollama.com",
        }
    
    @staticmethod
    def _check_openrouter_key() -> Dict[str, Any]:
        """
        Check if OpenRouter API key is configured.
        
        Returns:
            Dict with availability status
        """
        if os.getenv("OPENROUTER_API_KEY"):
            return {
                "available": True,
                "message": "OpenRouter API key found",
            }
        return {
            "available": False,
            "message": "Set OPENROUTER_API_KEY environment variable",
        }
    
    @staticmethod
    def _check_openai_key() -> Dict[str, Any]:
        """
        Check if OpenAI API key is configured.
        
        Returns:
            Dict with availability status
        """
        if os.getenv("OPENAI_API_KEY"):
            return {
                "available": True,
                "message": "OpenAI API key found",
            }
        return {
            "available": False,
            "message": "Set OPENAI_API_KEY environment variable",
        }
    
    @staticmethod
    def get_recommended_provider(detection_results: Dict[str, Dict]) -> str:
        """
        Get recommended provider based on availability.
        
        Priority: Ollama → OpenRouter → OpenAI
        
        Args:
            detection_results: Results from detect_all()
            
        Returns:
            Recommended provider name or "none"
        """
        # Priority order
        priority = ["ollama", "openrouter", "openai"]
        
        for provider in priority:
            if detection_results.get(provider, {}).get("available"):
                return provider
        
        return "none"
