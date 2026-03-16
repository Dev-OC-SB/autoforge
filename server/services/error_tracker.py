"""
Error Tracking Service
======================

Tracks errors during git operations and agent execution.
Logs errors with full context and retry history.
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from api.database import ErrorLog

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Service for tracking and logging errors."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_error(
        self,
        project_id: int,
        error_type: str,
        error_message: str,
        context: dict,
        retry_count: int = 0
    ) -> ErrorLog:
        """
        Log an error to the database.
        
        Args:
            project_id: Project ID
            error_type: Type of error (e.g., "git_operation", "agent_failure")
            error_message: Error message
            context: Full error context (dict)
            retry_count: Number of retry attempts
        
        Returns:
            ErrorLog instance
        """
        error_log = ErrorLog(
            project_id=project_id,
            error_type=error_type,
            error_message=error_message,
            context=context,
            retry_count=retry_count,
            resolved=False,
            github_issue_url=None,
            created_at=datetime.now()
        )
        
        self.db.add(error_log)
        self.db.commit()
        self.db.refresh(error_log)
        
        logger.error(
            f"Error logged: {error_type} - {error_message}",
            extra={"error_id": error_log.id, "context": context}
        )
        
        return error_log
    
    def update_issue_url(self, error_id: int, issue_url: str):
        """
        Update error log with GitHub issue URL.
        
        Args:
            error_id: Error log ID
            issue_url: GitHub issue URL
        """
        error_log = self.db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
        
        if error_log:
            error_log.github_issue_url = issue_url
            self.db.commit()
            logger.info(f"Updated error {error_id} with issue URL: {issue_url}")
    
    def mark_resolved(self, error_id: int):
        """
        Mark an error as resolved.
        
        Args:
            error_id: Error log ID
        """
        error_log = self.db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
        
        if error_log:
            error_log.resolved = True
            self.db.commit()
            logger.info(f"Marked error {error_id} as resolved")
    
    def get_unresolved_errors(self, project_id: int) -> list[ErrorLog]:
        """
        Get all unresolved errors for a project.
        
        Args:
            project_id: Project ID
        
        Returns:
            List of unresolved ErrorLog instances
        """
        return self.db.query(ErrorLog).filter(
            ErrorLog.project_id == project_id,
            ErrorLog.resolved == False
        ).all()
    
    def get_recent_errors(self, project_id: int, limit: int = 10) -> list[ErrorLog]:
        """
        Get recent errors for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of errors to return
        
        Returns:
            List of recent ErrorLog instances
        """
        return self.db.query(ErrorLog).filter(
            ErrorLog.project_id == project_id
        ).order_by(ErrorLog.created_at.desc()).limit(limit).all()
