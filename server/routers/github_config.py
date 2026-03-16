"""
GitHub Configuration Router
============================

API endpoints for managing GitHub configuration per project.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path

from api.database import get_db, GitHubConfig
from server.utils.project_helpers import get_project_by_name
from server.services.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github-config", tags=["github-config"])


class GitHubConfigCreate(BaseModel):
    """Schema for creating GitHub configuration."""
    project_name: str
    repo_url: str
    auth_token: str
    task_code: str


class GitHubConfigUpdate(BaseModel):
    """Schema for updating GitHub configuration."""
    repo_url: str | None = None
    auth_token: str | None = None
    task_code: str | None = None


class GitHubConfigResponse(BaseModel):
    """Schema for GitHub configuration response."""
    id: int
    project_name: str
    repo_url: str
    task_code: str
    current_task_id: int
    last_branch: str | None
    git_user_name: str
    git_user_email: str


@router.post("", response_model=GitHubConfigResponse)
async def create_github_config(
    config: GitHubConfigCreate,
    db: Session = Depends(get_db)
):
    """Create GitHub configuration for a project."""
    # Get project
    project = get_project_by_name(config.project_name, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if config already exists
    existing = db.query(GitHubConfig).filter(
        GitHubConfig.project_id == project.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="GitHub configuration already exists for this project"
        )
    
    # Validate task code format (e.g., SF001)
    if not config.task_code or len(config.task_code) < 3:
        raise HTTPException(
            status_code=400,
            detail="Task code must be at least 3 characters"
        )
    
    # Create configuration with encrypted token
    github_config = GitHubConfig(
        project_id=project.id,
        repo_url=config.repo_url,
        auth_token=encrypt_token(config.auth_token),
        task_code=config.task_code,
        current_task_id=0,
        last_branch=None
    )
    
    db.add(github_config)
    db.commit()
    db.refresh(github_config)
    
    logger.info(f"Created GitHub config for project {config.project_name}")
    
    return GitHubConfigResponse(
        id=github_config.id,
        project_name=config.project_name,
        repo_url=github_config.repo_url,
        task_code=github_config.task_code,
        current_task_id=github_config.current_task_id,
        last_branch=github_config.last_branch,
        git_user_name=github_config.git_user_name or "SeaForge",
        git_user_email=github_config.git_user_email or "agents@seaforge.ai"
    )


@router.get("/{project_name}", response_model=GitHubConfigResponse)
async def get_github_config(
    project_name: str,
    db: Session = Depends(get_db)
):
    """Get GitHub configuration for a project."""
    project = get_project_by_name(project_name, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    config = db.query(GitHubConfig).filter(
        GitHubConfig.project_id == project.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="GitHub configuration not found for this project"
        )
    
    return GitHubConfigResponse(
        id=config.id,
        project_name=project_name,
        repo_url=config.repo_url,
        task_code=config.task_code,
        current_task_id=config.current_task_id,
        last_branch=config.last_branch,
        git_user_name=config.git_user_name or "SeaForge",
        git_user_email=config.git_user_email or "agents@seaforge.ai"
    )


@router.put("/{project_name}", response_model=GitHubConfigResponse)
async def update_github_config(
    project_name: str,
    updates: GitHubConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update GitHub configuration for a project."""
    project = get_project_by_name(project_name, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    config = db.query(GitHubConfig).filter(
        GitHubConfig.project_id == project.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="GitHub configuration not found for this project"
        )
    
    # Update fields
    if updates.repo_url is not None:
        config.repo_url = updates.repo_url
    if updates.auth_token is not None:
        config.auth_token = encrypt_token(updates.auth_token)
    if updates.task_code is not None:
        config.task_code = updates.task_code
    
    db.commit()
    db.refresh(config)
    
    logger.info(f"Updated GitHub config for project {project_name}")
    
    return GitHubConfigResponse(
        id=config.id,
        project_name=project_name,
        repo_url=config.repo_url,
        task_code=config.task_code,
        current_task_id=config.current_task_id,
        last_branch=config.last_branch,
        git_user_name=config.git_user_name or "SeaForge",
        git_user_email=config.git_user_email or "agents@seaforge.ai"
    )


@router.delete("/{project_name}")
async def delete_github_config(
    project_name: str,
    db: Session = Depends(get_db)
):
    """Delete GitHub configuration for a project."""
    project = get_project_by_name(project_name, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    config = db.query(GitHubConfig).filter(
        GitHubConfig.project_id == project.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="GitHub configuration not found for this project"
        )
    
    db.delete(config)
    db.commit()
    
    logger.info(f"Deleted GitHub config for project {project_name}")
    
    return {"message": "GitHub configuration deleted successfully"}
