"""
FastA2A Server Endpoints
=========================

Implements FastA2A protocol endpoints for bidirectional communication
with external agents (Agent Zero).
"""

import asyncio
import json
import logging
from typing import Dict, List
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/a2a", tags=["a2a"])

# Store active SSE connections
sse_connections: List[asyncio.Queue] = []


@router.post("")
async def a2a_handler(request: Request):
    """
    FastA2A endpoint for receiving messages from Agent Zero.
    
    Agent Zero calls this when:
    - Task progress update
    - Task completion
    - Error occurred
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse A2A request: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"}
        )
    
    message = data.get("message", "")
    context_id = data.get("context_id")
    attachments = data.get("attachments", [])
    
    logger.info(f"Received A2A message from external agent. Context: {context_id}")
    
    # Parse Agent Zero's response
    if "✅ Gitbot Task Complete" in message:
        # Extract task info from Gitbot report
        task_info = _parse_gitbot_response(message)
        
        if task_info:
            logger.info(f"Gitbot task complete: {task_info.get('task_code')}-{task_info.get('task_id')}")
            
            # Broadcast to SSE subscribers and WebSocket clients
            await _broadcast_to_sse({
                "type": "external_agent_complete",
                "task_id": task_info.get("task_id"),
                "task_code": task_info.get("task_code"),
                "branch": task_info.get("branch_name"),
                "commit_hash": task_info.get("commit_hash"),
                "pr_url": task_info.get("pr_url"),
                "files_changed": task_info.get("files_changed", []),
                "message": message
            })
    
    elif "in_progress" in message.lower() or "gitbot:" in message.lower():
        # Progress update
        logger.info(f"Gitbot progress update: {message[:100]}")
        
        await _broadcast_to_sse({
            "type": "external_agent_progress",
            "message": message,
            "context_id": context_id
        })
    
    elif "❌" in message or "error" in message.lower():
        # Error notification
        logger.error(f"Gitbot error: {message}")
        
        await _broadcast_to_sse({
            "type": "external_agent_error",
            "message": message,
            "context_id": context_id
        })
    
    # Return acknowledgment
    return JSONResponse(
        content={
            "message": "Acknowledged",
            "context_id": context_id or _generate_context_id()
        }
    )


@router.get("/stream")
async def a2a_stream():
    """
    SSE endpoint for Agent Zero to subscribe to SeaForge updates.
    
    Agent Zero can listen to:
    - Internal agent progress
    - New tasks available
    - Project state changes
    """
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections.append(queue)
        
        try:
            while True:
                event = await queue.get()
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event.get("data", {}))
                }
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        finally:
            sse_connections.remove(queue)
    
    return EventSourceResponse(event_generator())


async def _broadcast_to_sse(event: Dict):
    """Broadcast event to all SSE subscribers."""
    if not sse_connections:
        return
    
    for queue in sse_connections:
        try:
            await queue.put(event)
        except Exception as e:
            logger.error(f"Failed to broadcast to SSE connection: {e}")


def _parse_gitbot_response(response: str) -> Dict:
    """Parse Gitbot completion response."""
    import re
    
    result = {}
    
    # Extract task code and ID
    if match := re.search(r"Gitbot Task Complete: ([A-Z0-9]+-\d+)", response):
        parts = match.group(1).split("-")
        result["task_code"] = parts[0]
        result["task_id"] = int(parts[1])
    
    # Extract branch name
    if match := re.search(r"📁 Branch: (.+)", response):
        result["branch_name"] = match.group(1).strip()
    
    # Extract commit hash
    if match := re.search(r"🔨 Commit Hash: ([a-f0-9]+)", response):
        result["commit_hash"] = match.group(1).strip()
    
    # Extract files changed
    files = []
    if "📄 Files Changed:" in response:
        lines = response.split("\n")
        in_files = False
        for line in lines:
            if "📄 Files Changed:" in line:
                in_files = True
                continue
            if in_files:
                if line.strip().startswith("-"):
                    files.append(line.strip()[1:].strip())
                elif "🍒" in line or "🔗" in line:
                    break
    result["files_changed"] = files
    
    # Extract PR URL
    if match := re.search(r"🔗 Merge Request: (.+)", response):
        result["pr_url"] = match.group(1).strip()
    
    return result


def _generate_context_id() -> str:
    """Generate a unique context ID."""
    import uuid
    return f"seaforge-{uuid.uuid4().hex[:12]}"
