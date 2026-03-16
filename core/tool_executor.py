"""
Tool Executor for Non-Claude Providers
=======================================

Provides direct execution of MCP feature tools and file system tools
for use in the agentic loop when using OpenRouter/OpenAI/Ollama adapters.

These providers don't have the Claude SDK's built-in tool execution,
so we need to handle tool calls manually.
"""

import json
import os
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools for the agentic loop."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self._mcp_tools = None
        self._init_mcp()
    
    def _init_mcp(self):
        """Initialize MCP feature tools by importing them directly."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        # Set PROJECT_DIR for MCP server
        os.environ["PROJECT_DIR"] = str(self.project_dir)
        
        # Defer database initialization until first tool call
        self._engine = None
        self._session_maker = None
    
    def _ensure_db_initialized(self):
        """Lazy initialization of database connection."""
        if self._session_maker is None:
            from api.database import create_database
            self._engine, self._session_maker = create_database(self.project_dir)
    
    def get_openai_tool_definitions(self) -> List[Dict]:
        """Return tool definitions in OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "feature_claim_and_get",
                    "description": "Atomically claim a feature (mark in-progress) and return its full details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature_id": {"type": "integer", "description": "The ID of the feature to claim"}
                        },
                        "required": ["feature_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "feature_mark_passing",
                    "description": "Mark a feature as passing after successful implementation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature_id": {"type": "integer", "description": "The ID of the feature to mark as passing"}
                        },
                        "required": ["feature_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "feature_mark_failing",
                    "description": "Mark a feature as failing (regression detected).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature_id": {"type": "integer", "description": "The ID of the feature to mark as failing"},
                            "reason": {"type": "string", "description": "Reason for failure"}
                        },
                        "required": ["feature_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "feature_skip",
                    "description": "Skip a feature that can't be implemented right now.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature_id": {"type": "integer", "description": "The ID of the feature to skip"}
                        },
                        "required": ["feature_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "feature_get_stats",
                    "description": "Get statistics about feature completion progress.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "feature_get_by_id",
                    "description": "Get a specific feature by its ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "feature_id": {"type": "integer", "description": "The ID of the feature"}
                        },
                        "required": ["feature_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Creates parent directories if needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path relative to project directory"},
                            "content": {"type": "string", "description": "Content to write to the file"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file's content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path relative to project directory"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Run a shell command in the project directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to execute"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files in a directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path relative to project directory", "default": "."}
                        }
                    }
                }
            },
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool and return the result as a string.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool result as a string
        """
        try:
            if tool_name == "feature_claim_and_get":
                return self._feature_claim_and_get(arguments["feature_id"])
            elif tool_name == "feature_mark_passing":
                return self._feature_mark_passing(arguments["feature_id"])
            elif tool_name == "feature_mark_failing":
                return self._feature_mark_failing(arguments["feature_id"], arguments.get("reason", ""))
            elif tool_name == "feature_skip":
                return self._feature_skip(arguments["feature_id"])
            elif tool_name == "feature_get_stats":
                return self._feature_get_stats()
            elif tool_name == "feature_get_by_id":
                return self._feature_get_by_id(arguments["feature_id"])
            elif tool_name == "write_file":
                return self._write_file(arguments["path"], arguments["content"])
            elif tool_name == "read_file":
                return self._read_file(arguments["path"])
            elif tool_name == "run_command":
                return self._run_command(arguments["command"])
            elif tool_name == "list_files":
                return self._list_files(arguments.get("path", "."))
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})
    
    def _feature_claim_and_get(self, feature_id: int) -> str:
        self._ensure_db_initialized()
        from api.database import Feature
        from sqlalchemy import text
        session = self._session_maker()
        try:
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if feature is None:
                return json.dumps({"error": f"Feature with ID {feature_id} not found"})
            if feature.passes:
                return json.dumps({"error": f"Feature {feature_id} is already passing"})
            result = session.execute(text(
                "UPDATE features SET in_progress = 1 WHERE id = :id AND passes = 0 AND in_progress = 0 AND needs_human_input = 0"
            ), {"id": feature_id})
            session.commit()
            session.refresh(feature)
            result_dict = feature.to_dict()
            result_dict["already_claimed"] = result.rowcount == 0
            return json.dumps(result_dict)
        except Exception as e:
            session.rollback()
            return json.dumps({"error": str(e)})
        finally:
            session.close()
    
    def _feature_mark_passing(self, feature_id: int) -> str:
        self._ensure_db_initialized()
        from api.database import Feature
        from sqlalchemy import text
        session = self._session_maker()
        try:
            result = session.execute(text(
                "UPDATE features SET passes = 1, in_progress = 0 WHERE id = :id"
            ), {"id": feature_id})
            session.commit()
            if result.rowcount == 0:
                return json.dumps({"error": f"Feature {feature_id} not found"})
            return json.dumps({"success": True, "feature_id": feature_id, "status": "passing"})
        except Exception as e:
            session.rollback()
            return json.dumps({"error": str(e)})
        finally:
            session.close()
    
    def _feature_mark_failing(self, feature_id: int, reason: str = "") -> str:
        self._ensure_db_initialized()
        from api.database import Feature
        from sqlalchemy import text
        session = self._session_maker()
        try:
            result = session.execute(text(
                "UPDATE features SET passes = 0, in_progress = 0 WHERE id = :id"
            ), {"id": feature_id})
            session.commit()
            return json.dumps({"success": True, "feature_id": feature_id, "status": "failing"})
        except Exception as e:
            session.rollback()
            return json.dumps({"error": str(e)})
        finally:
            session.close()
    
    def _feature_skip(self, feature_id: int) -> str:
        self._ensure_db_initialized()
        from api.database import Feature
        from sqlalchemy import text
        session = self._session_maker()
        try:
            result = session.execute(text(
                "UPDATE features SET in_progress = 0 WHERE id = :id"
            ), {"id": feature_id})
            session.commit()
            return json.dumps({"success": True, "feature_id": feature_id, "status": "skipped"})
        except Exception as e:
            session.rollback()
            return json.dumps({"error": str(e)})
        finally:
            session.close()
    
    def _feature_get_stats(self) -> str:
        self._ensure_db_initialized()
        from api.database import Feature
        from sqlalchemy import func, case
        session = self._session_maker()
        try:
            result = session.query(
                func.count(Feature.id).label('total'),
                func.sum(case((Feature.passes == True, 1), else_=0)).label('passing'),
                func.sum(case((Feature.in_progress == True, 1), else_=0)).label('in_progress'),
            ).first()
            total = result.total or 0
            passing = int(result.passing or 0)
            in_progress = int(result.in_progress or 0)
            return json.dumps({
                "passing": passing, "in_progress": in_progress,
                "total": total, "percentage": round((passing / total) * 100, 1) if total > 0 else 0.0
            })
        finally:
            session.close()
    
    def _feature_get_by_id(self, feature_id: int) -> str:
        self._ensure_db_initialized()
        from api.database import Feature
        session = self._session_maker()
        try:
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if feature is None:
                return json.dumps({"error": f"Feature {feature_id} not found"})
            return json.dumps(feature.to_dict())
        finally:
            session.close()
    
    def _write_file(self, path: str, content: str) -> str:
        file_path = self.project_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        print(f"   [Write] {path} ({len(content)} bytes)")
        return json.dumps({"success": True, "path": path, "bytes_written": len(content)})
    
    def _read_file(self, path: str) -> str:
        file_path = self.project_dir / path
        if not file_path.exists():
            return json.dumps({"error": f"File not found: {path}"})
        try:
            content = file_path.read_text()
            return content[:10000]  # Limit to 10k chars
        except Exception as e:
            return json.dumps({"error": f"Failed to read file: {str(e)}"})
    
    def _run_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(self.project_dir),
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
            stderr = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
            print(f"   [Bash] {command} (exit: {result.returncode})")
            return json.dumps({
                "exit_code": result.returncode,
                "stdout": output,
                "stderr": stderr
            })
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Command timed out after 60 seconds"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _list_files(self, path: str = ".") -> str:
        dir_path = self.project_dir / path
        if not dir_path.exists():
            return json.dumps({"error": f"Directory not found: {path}"})
        try:
            items = []
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith('.'):
                    continue
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return json.dumps(items[:50])  # Limit to 50 items
        except Exception as e:
            return json.dumps({"error": str(e)})
