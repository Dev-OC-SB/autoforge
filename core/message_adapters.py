"""
Message Format Adapters
========================

Convert between adapter responses and Claude SDK message format.
Provides compatibility layer for non-Claude providers.
"""

from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass


@dataclass
class TextBlock:
    """Text content block compatible with Claude SDK."""
    text: str
    type: str = "text"


@dataclass
class ToolUseBlock:
    """Tool use block compatible with Claude SDK."""
    id: str
    name: str
    input: Dict[str, Any]
    type: str = "tool_use"


@dataclass
class AssistantMessage:
    """Assistant message compatible with Claude SDK."""
    content: List[Any]
    role: str = "assistant"
    
    def __init__(self, content: List[Any]):
        self.content = content
        self.role = "assistant"


class MessageAdapter:
    """Adapts provider responses to Claude SDK message format."""
    
    @staticmethod
    def from_adapter_response(response_text: str) -> AssistantMessage:
        """
        Convert adapter response text to Claude SDK message format.
        
        Args:
            response_text: Raw text response from adapter
            
        Returns:
            AssistantMessage with TextBlock content
        """
        text_block = TextBlock(text=response_text)
        return AssistantMessage(content=[text_block])
    
    @staticmethod
    async def stream_adapter_response(response_text: str) -> AsyncGenerator[AssistantMessage, None]:
        """
        Stream adapter response as async generator of messages.
        
        This simulates streaming by yielding the complete response.
        Future enhancement: implement actual streaming from providers.
        
        Args:
            response_text: Response text to stream
            
        Yields:
            AssistantMessage chunks
        """
        # For now, yield the complete message
        # TODO: Implement actual streaming with httpx
        yield MessageAdapter.from_adapter_response(response_text)
    
    @staticmethod
    def create_tool_use_message(tool_name: str, tool_input: Dict[str, Any], tool_id: str = "tool_0") -> AssistantMessage:
        """
        Create a tool use message.
        
        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            tool_id: Unique tool call ID
            
        Returns:
            AssistantMessage with ToolUseBlock
        """
        tool_block = ToolUseBlock(
            id=tool_id,
            name=tool_name,
            input=tool_input
        )
        return AssistantMessage(content=[tool_block])


class StreamingMessageAdapter:
    """
    Adapter for streaming responses from non-Claude providers.
    
    Converts token stream into async generator format
    compatible with Claude SDK's receive_response() pattern.
    """
    
    def __init__(self, token_generator: Optional[AsyncGenerator[str, None]] = None, response_text: Optional[str] = None):
        """
        Initialize streaming adapter.
        
        Args:
            token_generator: Async generator yielding tokens (for true streaming)
            response_text: Complete response text (for non-streaming fallback)
        """
        self.token_generator = token_generator
        self.response_text = response_text
        self._buffer = ""
        self._yielded = False
    
    def __aiter__(self):
        """Async iterator protocol."""
        return self
    
    async def __anext__(self):
        """
        Yield next message chunk.
        
        Returns:
            AssistantMessage
            
        Raises:
            StopAsyncIteration: When streaming is complete
        """
        if self.token_generator:
            # True streaming mode - accumulate tokens and yield incrementally
            try:
                token = await self.token_generator.__anext__()
                self._buffer += token
                return MessageAdapter.from_adapter_response(self._buffer)
            except StopAsyncIteration:
                # Stream complete
                raise
        else:
            # Non-streaming fallback mode
            if self._yielded:
                raise StopAsyncIteration
            
            self._yielded = True
            return MessageAdapter.from_adapter_response(self.response_text or "")
