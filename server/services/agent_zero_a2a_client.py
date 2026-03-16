"""
Agent Zero A2A Client
=====================

FastA2A client for communicating with Agent Zero instances.
Supports Docker network, Direct IP, and Domain connections.
"""

import asyncio
import httpx
import json
import logging
import re
from typing import AsyncIterator, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentZeroA2AClient:
    """FastA2A client for Agent Zero integration with network flexibility."""
    
    def __init__(
        self,
        agent_name: str,
        base_url: str,
        api_token: str,
        timeout: int = 1800  # 30 minutes for long tasks
    ):
        """
        Initialize Agent Zero A2A client.
        
        Args:
            agent_name: Name of the agent instance
            base_url: Base URL (auto-determined from ExternalAgent config)
            api_token: API token for authentication
            timeout: Request timeout in seconds
        """
        self.agent_name = agent_name
        self.base_url = base_url
        self.api_token = api_token
        self.timeout = timeout
        
        self.a2a_url = f"{base_url}/a2a/t-{api_token}"
        self.stream_url = f"{base_url}/a2a/stream"
        self.context_id = None
        
        logger.info(f"Initialized Agent Zero client: {agent_name} at {base_url}")
    
    async def delegate_task_gb01(
        self,
        task_code: str,
        task_id: int,
        task_type: str,
        repo_url: str,
        auth_token: str,
        previous_branch: Optional[str],
        branch_name: str,
        commit_message: str,
        feature_description: str
    ) -> dict:
        """
        Delegate task to Agent Zero using GB01 skill (Gitbot).
        
        Args:
            task_code: Project task code (e.g., SF001)
            task_id: Sequential task ID (000-099 planning, 100+ development)
            task_type: "planning" or "development"
            repo_url: GitHub repository URL
            auth_token: GitHub Personal Access Token
            previous_branch: Branch to cherry-pick from (or None)
            branch_name: New branch name to create
            commit_message: Git commit message
            feature_description: Feature specification
        
        Returns:
            dict with status, context_id, initial_response
        """
        # Build GB01 task message
        message = f"""GB01

TASK_CODE: {task_code}
TASK_ID: {task_id:03d}
TASK_TYPE: {task_type}
REPO_URL: {repo_url}
AUTH_TOKEN: {auth_token}
PREVIOUS_BRANCH: {previous_branch or "main"}
BRANCH_NAME: {branch_name}
COMMIT_MESSAGE: {commit_message}

{feature_description}

Please execute the Gitbot workflow:
1. Create branch {branch_name} from main
2. Cherry-pick commits from {previous_branch or "main"}
3. Implement the feature
4. Commit with the provided message
5. Push to GitHub
6. Create PR to main (if task_id >= 100)

Report back when complete.
"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Delegating task {task_code}-{task_id:03d} to {self.agent_name}")
                
                response = await client.post(
                    self.a2a_url,
                    json={
                        "message": message,
                        "context_id": self.context_id,
                        "reset": False
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                self.context_id = result.get("context_id")
                
                logger.info(f"Task delegated successfully. Context: {self.context_id}")
                
                return {
                    "status": "delegated",
                    "context_id": self.context_id,
                    "initial_response": result.get("message", ""),
                    "agent_name": self.agent_name
                }
        
        except httpx.TimeoutException:
            logger.error(f"Timeout delegating to {self.agent_name}")
            return {
                "status": "error",
                "error": "Timeout connecting to Agent Zero"
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error delegating to {self.agent_name}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def stream_progress(self) -> AsyncIterator[dict]:
        """
        Subscribe to Agent Zero's SSE stream for real-time progress.
        
        Yields progress updates as they happen.
        """
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                logger.info(f"Subscribing to SSE stream: {self.stream_url}")
                
                async with client.stream("GET", self.stream_url) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                yield {
                                    "agent_name": self.agent_name,
                                    "timestamp": datetime.now().isoformat(),
                                    **data
                                }
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in SSE: {line}")
        
        except Exception as e:
            logger.error(f"Error streaming from {self.agent_name}: {e}")
            yield {
                "agent_name": self.agent_name,
                "error": str(e)
            }
    
    async def send_update(self, message: str) -> bool:
        """
        Send update to Agent Zero (bidirectional communication).
        
        Args:
            message: Update message to send
        
        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.a2a_url,
                    json={
                        "message": message,
                        "context_id": self.context_id
                    }
                )
                
                response.raise_for_status()
                logger.info(f"Sent update to {self.agent_name}")
                return True
        
        except Exception as e:
            logger.error(f"Error sending update to {self.agent_name}: {e}")
            return False
    
    def parse_gitbot_response(self, response: str) -> Optional[dict]:
        """
        Parse Gitbot's completion response.
        
        Expected format:
        ✅ Gitbot Task Complete: SF001-105
        📁 Branch: SF001-105-11/03/26
        🔨 Commit Hash: abc123
        📄 Files Changed:
           - file1.tsx
           - file2.ts
        🍒 Cherry-Picked: 8 commits from SF001-104-11/03/26
        🔗 Merge Request: https://github.com/user/repo/pull/15
        
        Returns:
            dict with parsed fields or None if parsing fails
        """
        if "✅ Gitbot Task Complete" not in response:
            return None
        
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
        
        # Extract cherry-pick count
        if match := re.search(r"🍒 Cherry-Picked: (\d+) commits", response):
            result["cherry_picked_count"] = int(match.group(1))
        
        # Extract PR URL
        if match := re.search(r"🔗 Merge Request: (.+)", response):
            result["pr_url"] = match.group(1).strip()
        
        return result if result else None
