"""
External Agents Router
======================

API endpoints for managing external agent configurations and integration guides.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db, ExternalAgent
from server.utils.project_helpers import get_project_path, get_project_by_name
from server.services.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/external-agents", tags=["external-agents"])


class ExternalAgentCreate(BaseModel):
    """Schema for creating external agent."""
    project_name: str
    name: str
    agent_type: str = "agent_zero"
    connection_type: str = "docker_network"
    container_name: str | None = None
    host: str | None = None
    port: int = 50001
    use_ssl: bool = False
    url_override: str | None = None
    api_token: str
    capabilities: list[str] = ["gitbot", "git-operations"]


class ExternalAgentUpdate(BaseModel):
    """Schema for updating external agent."""
    name: str | None = None
    connection_type: str | None = None
    container_name: str | None = None
    host: str | None = None
    port: int | None = None
    use_ssl: bool | None = None
    url_override: str | None = None
    api_token: str | None = None
    capabilities: list[str] | None = None
    enabled: bool | None = None


class ExternalAgentResponse(BaseModel):
    """Schema for external agent response."""
    id: int
    project_name: str
    name: str
    agent_type: str
    connection_type: str
    container_name: str | None
    host: str | None
    port: int
    use_ssl: bool
    url_override: str | None
    capabilities: list[str]
    enabled: bool
    last_connected: str | None
    base_url: str


@router.post("", response_model=ExternalAgentResponse)
async def create_external_agent(
    agent: ExternalAgentCreate,
    db: Session = Depends(get_db)
):
    """Create external agent configuration."""
    # Get project
    project = get_project_by_name(agent.project_name, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate connection settings
    if agent.connection_type == "docker_network" and not agent.container_name:
        raise HTTPException(
            status_code=400,
            detail="container_name required for docker_network connection"
        )
    
    if agent.connection_type in ["direct_ip", "domain"] and not agent.host:
        raise HTTPException(
            status_code=400,
            detail="host required for direct_ip or domain connection"
        )
    
    # Create external agent with encrypted token
    external_agent = ExternalAgent(
        project_id=project.id,
        name=agent.name,
        agent_type=agent.agent_type,
        connection_type=agent.connection_type,
        container_name=agent.container_name,
        host=agent.host,
        port=agent.port,
        use_ssl=agent.use_ssl,
        url_override=agent.url_override,
        api_token=encrypt_token(agent.api_token),
        capabilities=agent.capabilities,
        enabled=True
    )
    
    db.add(external_agent)
    db.commit()
    db.refresh(external_agent)
    
    logger.info(f"Created external agent {agent.name} for project {agent.project_name}")
    
    return ExternalAgentResponse(
        id=external_agent.id,
        project_name=agent.project_name,
        name=external_agent.name,
        agent_type=external_agent.agent_type,
        connection_type=external_agent.connection_type,
        container_name=external_agent.container_name,
        host=external_agent.host,
        port=external_agent.port,
        use_ssl=external_agent.use_ssl,
        url_override=external_agent.url_override,
        capabilities=external_agent.capabilities,
        enabled=external_agent.enabled,
        last_connected=external_agent.last_connected.isoformat() if external_agent.last_connected else None,
        base_url=external_agent.base_url
    )


@router.get("/{project_name}", response_model=list[ExternalAgentResponse])
async def list_external_agents(
    project_name: str,
    db: Session = Depends(get_db)
):
    """List all external agents for a project."""
    project = get_project_by_name(project_name, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agents = db.query(ExternalAgent).filter(
        ExternalAgent.project_id == project.id
    ).all()
    
    return [
        ExternalAgentResponse(
            id=agent.id,
            project_name=project_name,
            name=agent.name,
            agent_type=agent.agent_type,
            connection_type=agent.connection_type,
            container_name=agent.container_name,
            host=agent.host,
            port=agent.port,
            use_ssl=agent.use_ssl,
            url_override=agent.url_override,
            capabilities=agent.capabilities,
            enabled=agent.enabled,
            last_connected=agent.last_connected.isoformat() if agent.last_connected else None,
            base_url=agent.base_url
        )
        for agent in agents
    ]


@router.put("/{agent_id}", response_model=ExternalAgentResponse)
async def update_external_agent(
    agent_id: int,
    updates: ExternalAgentUpdate,
    db: Session = Depends(get_db)
):
    """Update external agent configuration."""
    agent = db.query(ExternalAgent).filter(ExternalAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="External agent not found")
    
    # Update fields
    if updates.name is not None:
        agent.name = updates.name
    if updates.connection_type is not None:
        agent.connection_type = updates.connection_type
    if updates.container_name is not None:
        agent.container_name = updates.container_name
    if updates.host is not None:
        agent.host = updates.host
    if updates.port is not None:
        agent.port = updates.port
    if updates.use_ssl is not None:
        agent.use_ssl = updates.use_ssl
    if updates.url_override is not None:
        agent.url_override = updates.url_override
    if updates.api_token is not None:
        agent.api_token = encrypt_token(updates.api_token)
    if updates.capabilities is not None:
        agent.capabilities = updates.capabilities
    if updates.enabled is not None:
        agent.enabled = updates.enabled
    
    db.commit()
    db.refresh(agent)
    
    logger.info(f"Updated external agent {agent.name}")
    
    # Get project name
    from api.database import create_database
    from core.autoforge_paths import get_project_dir
    # This is a simplified approach - in production, we'd query the project
    
    return ExternalAgentResponse(
        id=agent.id,
        project_name="",  # Will be populated properly in UI
        name=agent.name,
        agent_type=agent.agent_type,
        connection_type=agent.connection_type,
        container_name=agent.container_name,
        host=agent.host,
        port=agent.port,
        use_ssl=agent.use_ssl,
        url_override=agent.url_override,
        capabilities=agent.capabilities,
        enabled=agent.enabled,
        last_connected=agent.last_connected.isoformat() if agent.last_connected else None,
        base_url=agent.base_url
    )


@router.delete("/{agent_id}")
async def delete_external_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Delete external agent configuration."""
    agent = db.query(ExternalAgent).filter(ExternalAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="External agent not found")
    
    agent_name = agent.name
    db.delete(agent)
    db.commit()
    
    logger.info(f"Deleted external agent {agent_name}")
    
    return {"message": "External agent deleted successfully"}


@router.post("/{agent_id}/test-connection")
async def test_connection(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Test connection to external agent."""
    agent = db.query(ExternalAgent).filter(ExternalAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="External agent not found")
    
    # Test connection
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try to connect to the agent's base URL
            response = await client.get(f"{agent.base_url}/health", timeout=10)
            
            # Update last_connected
            agent.last_connected = datetime.now()
            db.commit()
            
            return {
                "success": True,
                "message": "Connection successful",
                "status_code": response.status_code
            }
    
    except httpx.TimeoutException:
        return {
            "success": False,
            "message": "Connection timeout",
            "error": "Agent did not respond within 10 seconds"
        }
    
    except httpx.ConnectError as e:
        return {
            "success": False,
            "message": "Connection failed",
            "error": str(e)
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": "Connection error",
            "error": str(e)
        }


@router.get("/integration-guide/view")
async def get_integration_guide(
    agent_type: str = Query("agent_zero", description="Type of external agent"),
    format: str = Query("markdown", description="Format: markdown or plain"),
    project_name: str = Query(None, description="Optional project name for context"),
    task_code: str = Query(None, description="Optional task code for examples")
):
    """
    Generate integration guide for external agents.
    
    Returns markdown or plain text guide with current SeaForge configuration.
    """
    # Import here to avoid circular dependencies
    from server.services.external_agent_guide_generator import ExternalAgentGuideGenerator
    
    generator = ExternalAgentGuideGenerator(
        seaforge_connection_type="docker_network",
        seaforge_container_name="seaforge",
        seaforge_host="localhost",
        seaforge_port=30003,
        seaforge_url_override=None,
        project_name=project_name,
        task_code=task_code
    )
    
    guide = generator.generate_guide(
        agent_type=agent_type,
        format=format
    )
    
    if format == "plain":
        return PlainTextResponse(content=guide)
    else:
        return PlainTextResponse(content=guide, media_type="text/markdown")


@router.get("/integration-guide/download")
async def download_integration_guide(
    agent_type: str = Query("agent_zero"),
    project_name: str = Query(None)
):
    """Download integration guide as a file."""
    from server.services.external_agent_guide_generator import ExternalAgentGuideGenerator
    
    generator = ExternalAgentGuideGenerator(
        seaforge_connection_type="docker_network",
        seaforge_container_name="seaforge",
        seaforge_host="localhost",
        seaforge_port=30003,
        project_name=project_name
    )
    
    guide = generator.generate_guide(agent_type=agent_type, format="markdown")
    
    filename = f"seaforge-{agent_type}-integration-guide.md"
    
    return PlainTextResponse(
        content=guide,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
