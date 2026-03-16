"""
OpenAI-Compatible Adapter
==========================

Adapter for OpenAI-compatible APIs (OpenAI, Azure, etc.).
"""

import httpx
from typing import Any, Dict, List, Optional

from .base import BaseAdapter, AgentResponse, ModelInfo


class OpenAICompatibleAdapter(BaseAdapter):
    """OpenAI-compatible API adapter."""
    
    def __init__(self, config: Dict):
        """
        Initialize OpenAI-compatible adapter.
        
        Args:
            config: Configuration dict with:
                - api_key: API key (required)
                - base_url: API base URL (default: https://api.openai.com/v1)
                - default_model: Default model to use
                - organization: Optional organization ID
        """
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("API key required for OpenAI-compatible provider")
        
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.default_model = config.get("default_model", "gpt-4-turbo")
        self.organization = config.get("organization")
    
    async def execute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AgentResponse:
        """Execute via OpenAI-compatible API."""
        
        # Build messages array
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        # Build request payload
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        # Execute request
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract response
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return AgentResponse(
            content=choice["message"]["content"],
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            cost_usd=self._estimate_cost(usage, model or self.default_model),
            model_used=data.get("model", model or self.default_model),
            metadata={
                "provider": "openai_compatible",
                "finish_reason": choice.get("finish_reason"),
                "raw_response": data,
            },
        )
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers,
                )
                response.raise_for_status()
                return {
                    "ok": True,
                    "message": "API connection successful",
                }
        except Exception as e:
            return {
                "ok": False,
                "message": f"API connection failed: {str(e)}",
            }
    
    def list_models(self) -> List[ModelInfo]:
        """List common OpenAI models."""
        return [
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                context_window=128000,
                supports_tools=True,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
            ),
            ModelInfo(
                id="gpt-4",
                name="GPT-4",
                context_window=8192,
                supports_tools=True,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                context_window=16385,
                supports_tools=True,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
            ),
        ]
    
    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "openai_compatible"
    
    def _estimate_cost(self, usage: Dict, model: str) -> float:
        """
        Estimate cost based on usage and model.
        
        Args:
            usage: Usage dict with prompt_tokens and completion_tokens
            model: Model identifier
            
        Returns:
            Estimated cost in USD
        """
        # Pricing table for common models
        pricing = {
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-4": (0.03, 0.06),
            "gpt-3.5-turbo": (0.0005, 0.0015),
        }
        
        # Get pricing for model (default to GPT-4 Turbo if unknown)
        input_price, output_price = pricing.get(model, (0.01, 0.03))
        
        # Calculate cost
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1000) * input_price
        output_cost = (output_tokens / 1000) * output_price
        
        return input_cost + output_cost
