"""
OpenRouter Adapter
==================

Adapter for OpenRouter API (multi-provider LLM access).
Includes agentic tool-use loop for multi-turn tool calling.
"""

import httpx
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from pathlib import Path

from .base import BaseAdapter, AgentResponse, ModelInfo

logger = logging.getLogger(__name__)


class OpenRouterAdapter(BaseAdapter):
    """OpenRouter API adapter for multiple LLM providers."""
    
    def __init__(self, config: Dict):
        """
        Initialize OpenRouter adapter.
        
        Args:
            config: Configuration dict with:
                - api_key: OpenRouter API key (required)
                - base_url: API base URL (default: https://openrouter.ai/api/v1)
                - default_model: Default model to use
                - site_url: Site URL for tracking
                - app_name: App name for tracking
        """
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("OpenRouter API key required")
        
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.default_model = config.get("default_model", "anthropic/claude-3.5-sonnet")
        self.site_url = config.get("site_url", "https://seaforge.ai")
        self.app_name = config.get("app_name", "SeaForge")
        self._tool_executor = None
    
    def set_tool_executor(self, tool_executor):
        """Set the tool executor for agentic loop."""
        self._tool_executor = tool_executor
    
    def _build_headers(self) -> Dict[str, str]:
        """Build common HTTP headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name
        return headers
    
    async def _chat_completion(
        self,
        messages: List[Dict],
        model: str,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 16384,
        temperature: float = 0.7,
    ) -> Dict:
        """Make a single chat completion API call."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
    async def execute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AgentResponse:
        """Execute via OpenRouter API with agentic tool-use loop."""
        
        use_model = model or self.default_model
        
        # Build initial messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # If we have a tool executor, use the agentic loop
        if self._tool_executor:
            return await self._execute_agentic(messages, use_model, max_tokens, temperature)
        
        # Legacy single-call path (no tool executor)
        data = await self._chat_completion(messages, use_model, tools, max_tokens, temperature)
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return AgentResponse(
            content=choice["message"].get("content") or "",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            cost_usd=self._calculate_cost(data),
            model_used=data.get("model", use_model),
            metadata={
                "provider": "openrouter",
                "finish_reason": choice.get("finish_reason"),
                "raw_response": data,
            },
        )
    
    async def _execute_agentic(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int = 16384,
        temperature: float = 0.7,
        max_turns: int = 30,
    ) -> AgentResponse:
        """
        Execute with agentic tool-use loop.
        
        Sends tool definitions, handles tool_calls responses, executes tools
        locally, feeds results back, and loops until the model stops calling tools.
        """
        tool_defs = self._tool_executor.get_openai_tool_definitions()
        all_text = ""
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        last_model = model
        
        for turn in range(max_turns):
            # Make API call with tools
            data = await self._chat_completion(messages, model, tool_defs, max_tokens, temperature)
            
            choice = data["choices"][0]
            message = choice["message"]
            usage = data.get("usage", {})
            finish_reason = choice.get("finish_reason", "")
            
            total_input_tokens += usage.get("prompt_tokens", 0)
            total_output_tokens += usage.get("completion_tokens", 0)
            total_cost += self._calculate_cost(data)
            last_model = data.get("model", model)
            
            # Collect any text content
            content = message.get("content") or ""
            if content:
                all_text += content
                print(content, end="", flush=True)
            
            # Check for tool calls
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                # No tool calls — model is done
                print(f"\n[Agent] Turn {turn + 1}: No more tool calls, session complete.", flush=True)
                break
            
            # Add assistant message with tool calls to conversation
            messages.append(message)
            
            # Execute each tool call and add results
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                try:
                    arguments = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    arguments = {}
                
                print(f"\n[Tool: {tool_name}] args={arguments}", flush=True)
                
                # Execute the tool
                result = self._tool_executor.execute_tool(tool_name, arguments)
                
                # Truncate long results for display
                display_result = result[:200] + "..." if len(result) > 200 else result
                print(f"   [Result] {display_result}", flush=True)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{turn}"),
                    "content": result,
                })
            
            print(f"\n[Agent] Turn {turn + 1} complete ({len(tool_calls)} tool calls)", flush=True)
        
        return AgentResponse(
            content=all_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_usd=total_cost,
            model_used=last_model,
            metadata={
                "provider": "openrouter",
                "agentic": True,
                "turns": turn + 1 if 'turn' in dir() else 0,
            },
        )
    
    async def execute_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Execute via OpenRouter API with streaming.
        
        Yields text chunks as they arrive from the API.
        """
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
        
        # Add optional headers if provided
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name
        
        # Build request payload with streaming enabled
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,  # Enable streaming
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        # Execute streaming request
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                
                # Parse SSE (Server-Sent Events) format
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # SSE lines start with "data: "
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        # Check for stream end marker
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            # Parse JSON chunk
                            chunk = json.loads(data_str)
                            
                            # Extract content delta
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    yield content
                        
                        except json.JSONDecodeError:
                            # Skip malformed chunks
                            continue
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenRouter connection."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers,
                )
                response.raise_for_status()
                return {
                    "ok": True,
                    "message": "OpenRouter connection successful",
                }
        except Exception as e:
            return {
                "ok": False,
                "message": f"OpenRouter connection failed: {str(e)}",
            }
    
    def list_models(self) -> List[ModelInfo]:
        """List common OpenRouter models."""
        # Common models - could be fetched dynamically from API
        return [
            ModelInfo(
                id="anthropic/claude-3.5-sonnet",
                name="Claude 3.5 Sonnet",
                context_window=200000,
                supports_tools=True,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
            ),
            ModelInfo(
                id="anthropic/claude-3-opus",
                name="Claude 3 Opus",
                context_window=200000,
                supports_tools=True,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
            ),
            ModelInfo(
                id="openai/gpt-4-turbo",
                name="GPT-4 Turbo",
                context_window=128000,
                supports_tools=True,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
            ),
            ModelInfo(
                id="google/gemini-pro-1.5",
                name="Gemini Pro 1.5",
                context_window=1000000,
                supports_tools=True,
                cost_per_1k_input=0.00125,
                cost_per_1k_output=0.005,
            ),
            ModelInfo(
                id="moonshotai/kimi-k2.5",
                name="Moonshot AI Kimi K2.5",
                context_window=128000,
                supports_tools=True,
                cost_per_1k_input=0.002,
                cost_per_1k_output=0.008,
            ),
            ModelInfo(
                id="minimax/minimax-m2.5",
                name="MiniMax M2.5",
                context_window=100000,
                supports_tools=True,
                cost_per_1k_input=0.0015,
                cost_per_1k_output=0.006,
            ),
        ]
    
    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "openrouter"
    
    def _calculate_cost(self, response_data: Dict) -> float:
        """
        Calculate cost from OpenRouter response.
        
        OpenRouter provides cost information in the response metadata.
        """
        # OpenRouter may include cost in usage metadata
        usage = response_data.get("usage", {})
        
        # Check for direct cost field
        if "cost" in usage:
            return float(usage["cost"])
        
        # Fallback: estimate from tokens if pricing available
        # This is approximate - actual costs may vary by model
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # Default pricing (will be overridden by actual response if available)
        cost_per_1k_input = 0.003
        cost_per_1k_output = 0.015
        
        input_cost = (prompt_tokens / 1000) * cost_per_1k_input
        output_cost = (completion_tokens / 1000) * cost_per_1k_output
        
        return input_cost + output_cost
