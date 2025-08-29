"""Streaming utilities for LangGraph workflows."""

from typing import Any, Dict, List, Optional, AsyncGenerator, Callable
import asyncio
import json
from datetime import datetime

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage

from models.streaming import (
    StreamEventType,
    TokenChunkEvent,
    LLMTokenEvent,
    WorkflowStartEvent,
    WorkflowCompleteEvent,
    WorkflowErrorEvent,
    NodeStartEvent,
    NodeCompleteEvent
)
from core.logging import get_logger

logger = get_logger(__name__)


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Async callback handler for streaming LLM tokens and workflow events."""
    
    def __init__(self, event_emitter: Callable[[Dict[str, Any]], None]):
        """Initialize the streaming callback handler.
        
        Args:
            event_emitter: Function to emit streaming events
        """
        super().__init__()
        self.event_emitter = event_emitter
        self.current_node = None
        self.token_buffer = ""
        
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts generating."""
        event = {
            "type": StreamEventType.LLM_START,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "model": serialized.get("id", ["unknown"])[-1],
                "node": self.current_node
            }
        }
        await self._emit_event(event)
        
    async def on_llm_new_token(
        self,
        token: str,
        **kwargs: Any,
    ) -> None:
        """Called when a new token is generated."""
        self.token_buffer += token
        
        # Emit token event
        token_event = LLMTokenEvent(
            type=StreamEventType.LLM_TOKEN,
            timestamp=datetime.utcnow().isoformat(),
            content=token,
            node_name=self.current_node or "unknown"
        )
        
        await self._emit_event(token_event.dict())
        
    async def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """Called when LLM finishes generating."""
        event = {
            "type": StreamEventType.LLM_END,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "node": self.current_node,
                "final_text": self.token_buffer,
                "token_count": len(self.token_buffer.split())
            }
        }
        await self._emit_event(event)
        
        # Reset token buffer
        self.token_buffer = ""
        
    async def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Called when LLM encounters an error."""
        event = {
            "type": StreamEventType.LLM_ERROR,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "error": str(error),
                "node": self.current_node
            }
        }
        await self._emit_event(event)
        
    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when a chain starts."""
        # Extract node name from chain context
        node_name = serialized.get("name", "unknown")
        self.current_node = node_name
        
        event = NodeStartEvent(
            type=StreamEventType.NODE_START,
            timestamp=datetime.utcnow().isoformat(),
            node_name=node_name,
            input_data=inputs
        )
        
        await self._emit_event(event.dict())
        
    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when a chain ends."""
        event = NodeCompleteEvent(
            type=StreamEventType.NODE_COMPLETE,
            timestamp=datetime.utcnow().isoformat(),
            node_name=self.current_node or "unknown",
            output_data=outputs
        )
        
        await self._emit_event(event.dict())
        self.current_node = None
        
    async def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Called when a chain encounters an error."""
        event = {
            "type": StreamEventType.NODE_ERROR,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "error": str(error),
                "node": self.current_node
            }
        }
        await self._emit_event(event)
        
    async def _emit_event(self, event: Dict[str, Any]) -> None:
        """Emit a streaming event."""
        try:
            if asyncio.iscoroutinefunction(self.event_emitter):
                await self.event_emitter(event)
            else:
                self.event_emitter(event)
        except Exception as e:
            logger.error(f"Error emitting streaming event: {e}")


class WorkflowStreamManager:
    """Manager for workflow streaming events."""
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.active_streams = set()
        
    async def create_stream(self, workflow_id: str, execution_id: str) -> AsyncGenerator[str, None]:
        """Create a new streaming session.
        
        Args:
            workflow_id: ID of the workflow
            execution_id: ID of the execution
            
        Yields:
            Server-sent event formatted strings
        """
        stream_id = f"{workflow_id}:{execution_id}"
        self.active_streams.add(stream_id)
        
        try:
            # Emit workflow start event
            start_event = WorkflowStartEvent(
                type=StreamEventType.WORKFLOW_START,
                timestamp=datetime.utcnow().isoformat(),
                workflow_name=workflow_id,
                execution_id=execution_id,
                initial_state={},
                stream_mode="values"
            )
            
            yield self._format_sse_event(start_event.dict())
            
            # Stream events from queue
            while stream_id in self.active_streams:
                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                    
                    # Filter events for this stream
                    if self._should_emit_event(event, stream_id):
                        yield self._format_sse_event(event)
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield "data: {\"type\": \"keepalive\"}\n\n"
                    
        except Exception as e:
            logger.error(f"Error in streaming session {stream_id}: {e}")
            
            # Emit error event
            error_event = WorkflowErrorEvent(
                type=StreamEventType.WORKFLOW_ERROR,
                timestamp=datetime.utcnow().isoformat(),
                workflow_name=workflow_id,
                execution_id=execution_id,
                error=str(e),
                status="failed"
            )
            
            yield self._format_sse_event(error_event.dict())
            
        finally:
            self.active_streams.discard(stream_id)
            
    async def emit_event(self, event: Dict[str, Any]) -> None:
        """Emit an event to all active streams."""
        await self.event_queue.put(event)
        
    def close_stream(self, workflow_id: str, execution_id: str) -> None:
        """Close a streaming session."""
        stream_id = f"{workflow_id}:{execution_id}"
        self.active_streams.discard(stream_id)
        
    def _should_emit_event(self, event: Dict[str, Any], stream_id: str) -> bool:
        """Check if event should be emitted to the stream."""
        # For now, emit all events to all streams
        # In production, you might want to filter by workflow/execution ID
        return True
        
    def _format_sse_event(self, event: Dict[str, Any]) -> str:
        """Format event as Server-Sent Event."""
        event_json = json.dumps(event, default=str)
        return f"data: {event_json}\n\n"


# Global stream manager instance
stream_manager = WorkflowStreamManager()