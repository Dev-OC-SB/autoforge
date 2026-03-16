"""
Ollama Adapter
==============

Adapter for local Ollama LLM instances.
"""

import httpx
from typing import Any, Dict, List, Optional

from .base import BaseAdapter, AgentResponse, ModelInfo


class OllamaAdapter(BaseAdapter):
    """Ollama local LLM adapter."""
    
    def __init__(self, config: Dict):
        """
        Initialize Ollama adapter.
        
        Args:
            config: Configuration dict with:
                - base_url: Ollama API URL (default: http://localhost:11434)
                - default_model: Default model to use
                - timeout: Request timeout in seconds
        """
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "codellama:13b")
        self.timeout = config.get("timeout", 300)
    
    async def execute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AgentResponse:
        """Execute via Ollama API."""
        
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Build request payload
        payload = {
            "model": model or self.default_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        # Execute request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract response data
        return AgentResponse(
            content=data.get("response", ""),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            cost_usd=0.0,  # Local models are free
            model_used=model or self.default_model,
            metadata={
                "provider": "ollama",
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "raw_response": data,
            },
        )
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                return {
                    "ok": True,
                    "message": f"Ollama running with {len(models)} models",
                    "models": [m["name"] for m in models],
                }
        except Exception as e:
            return {
                "ok": False,
                "message": f"Ollama not accessible: {str(e)}",
            }
    
    def list_models(self) -> List[ModelInfo]:
        """List Ollama models (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._fetch_models())
    
    async def _fetch_models(self) -> List[ModelInfo]:
        """Fetch models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                data = response.json()
                
                models = []
                for m in data.get("models", []):
                    # Extract context window from model details if available
                    details = m.get("details", {})
                    context_length = details.get("context_length", 4096)
                    
                    models.append(ModelInfo(
                        id=m["name"],
                        name=m["name"],
                        context_window=context_length,
                        supports_tools=False,  # Most Ollama models don't support tools
                        cost_per_1k_input=0.0,
                        cost_per_1k_output=0.0,
                    ))
                
                return models
        except Exception:
            # Return empty list if can't fetch models
            return []
    
    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "ollama"
