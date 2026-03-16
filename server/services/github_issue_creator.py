"""
GitHub Issue Creator Service
=============================

Creates GitHub issues for persistent errors.
Avoids duplicate issues and includes full error context.
"""

import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class GitHubIssueCreator:
    """Service for creating GitHub issues for errors."""
    
    def __init__(self, repo_url: str, auth_token: str):
        """
        Initialize GitHub issue creator.
        
        Args:
            repo_url: GitHub repository URL
            auth_token: GitHub Personal Access Token
        """
        self.repo_url = repo_url
        self.auth_token = auth_token
        
        # Extract owner and repo from URL
        # https://github.com/owner/repo or https://github.com/owner/repo.git
        parts = repo_url.rstrip("/").replace(".git", "").split("/")
        self.owner = parts[-2]
        self.repo = parts[-1]
        
        self.api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
    
    async def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] = None
    ) -> Optional[str]:
        """
        Create a GitHub issue.
        
        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of labels to apply
        
        Returns:
            Issue URL if successful, None otherwise
        """
        if labels is None:
            labels = ["seaforge-error"]
        
        headers = {
            "Authorization": f"token {self.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body,
            "labels": labels
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.api_url, headers=headers, json=data)
                response.raise_for_status()
                
                issue_data = response.json()
                issue_url = issue_data["html_url"]
                
                logger.info(f"Created GitHub issue: {issue_url}")
                return issue_url
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create GitHub issue: HTTP {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return None
    
    async def check_duplicate_issue(self, title: str) -> Optional[str]:
        """
        Check if an issue with the same title already exists.
        
        Args:
            title: Issue title to search for
        
        Returns:
            Existing issue URL if found, None otherwise
        """
        headers = {
            "Authorization": f"token {self.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        params = {
            "state": "open",
            "labels": "seaforge-error",
            "per_page": 100
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.api_url, headers=headers, params=params)
                response.raise_for_status()
                
                issues = response.json()
                
                for issue in issues:
                    if issue["title"] == title:
                        logger.info(f"Found duplicate issue: {issue['html_url']}")
                        return issue["html_url"]
                
                return None
        
        except Exception as e:
            logger.error(f"Failed to check for duplicate issues: {e}")
            return None
    
    async def create_issue_if_not_exists(
        self,
        title: str,
        body: str,
        labels: list[str] = None
    ) -> Optional[str]:
        """
        Create a GitHub issue only if one with the same title doesn't exist.
        
        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of labels to apply
        
        Returns:
            Issue URL (existing or newly created)
        """
        # Check for duplicate
        existing_url = await self.check_duplicate_issue(title)
        if existing_url:
            logger.info(f"Using existing issue instead of creating duplicate: {existing_url}")
            return existing_url
        
        # Create new issue
        return await self.create_issue(title, body, labels)
    
    @staticmethod
    def format_error_body(
        error_message: str,
        error_type: str,
        context: dict,
        retry_count: int
    ) -> str:
        """
        Format error information into a GitHub issue body.
        
        Args:
            error_message: Error message
            error_type: Type of error
            context: Error context
            retry_count: Number of retry attempts
        
        Returns:
            Formatted markdown body
        """
        body = f"""## Error Report

**Error Type:** `{error_type}`  
**Retry Attempts:** {retry_count}

### Error Message
```
{error_message}
```

### Context
"""
        
        for key, value in context.items():
            body += f"- **{key}:** `{value}`\n"
        
        body += """

### Troubleshooting Steps
1. Check the error message and context above
2. Verify git configuration and credentials
3. Check network connectivity
4. Review recent changes to the codebase

---
*This issue was automatically created by SeaForge error tracking system.*
"""
        
        return body
