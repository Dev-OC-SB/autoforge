"""
Gitbot-Style Git Sync
=====================

Replicates Agent Zero's Gitbot workflow for internal SeaForge agents.
Handles branch creation, cherry-picking, commits, and PR creation.
"""

import subprocess
import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Agent mascot names (imported from schemas)
AGENT_MASCOTS = ["Spark", "Fizz", "Octo", "Hoot", "Buzz"]


def get_git_identity(agent_type: str, agent_index: int) -> tuple[str, str]:
    """
    Get git user.name and user.email for agent.
    
    Args:
        agent_type: "initializer", "coding", or "testing"
        agent_index: Agent index (0-4 for mascots)
    
    Returns:
        Tuple of (name, email)
    """
    if agent_type == "initializer":
        return ("SeaForge Initializer", "initializer@seaforge.ai")
    
    mascot = AGENT_MASCOTS[agent_index % len(AGENT_MASCOTS)]
    
    if agent_type == "coding":
        return (mascot, f"{mascot.lower()}@seaforge.ai")
    elif agent_type == "testing":
        return (f"{mascot} (Testing)", f"{mascot.lower()}-testing@seaforge.ai")
    
    return ("SeaForge Agent", "agent@seaforge.ai")


class GitbotStyleSync:
    """Handles git operations for internal agents using Gitbot workflow."""
    
    def __init__(
        self,
        project_dir: Path,
        repo_url: str,
        auth_token: str,
        task_code: str
    ):
        """
        Initialize GitbotStyleSync.
        
        Args:
            project_dir: Project directory (temp directory)
            repo_url: GitHub repository URL
            auth_token: GitHub Personal Access Token
            task_code: Project task code (e.g., SF001)
        """
        self.project_dir = Path(project_dir)
        self.repo_url = repo_url
        self.auth_token = auth_token
        self.task_code = task_code
        
        # Build authenticated remote URL
        if "github.com" in repo_url:
            # https://github.com/user/repo -> https://token@github.com/user/repo
            self.auth_repo_url = repo_url.replace("https://", f"https://{auth_token}@")
        else:
            self.auth_repo_url = repo_url
    
    def _run_git(self, *args, check=True) -> subprocess.CompletedProcess:
        """Run git command in project directory."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: git {' '.join(args)}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise
    
    def ensure_git_initialized(self):
        """Initialize git repository if not already initialized."""
        if not (self.project_dir / ".git").exists():
            logger.info(f"Initializing git in {self.project_dir}")
            self._run_git("init")
            self._run_git("remote", "add", "origin", self.auth_repo_url)
        else:
            # Update remote URL (in case token changed)
            self._run_git("remote", "set-url", "origin", self.auth_repo_url)
    
    def ensure_main_branch_exists(self):
        """Ensure main branch exists on remote (create if needed)."""
        logger.info("Checking if main branch exists")
        
        result = self._run_git("fetch", "origin", "main", check=False)
        
        if result.returncode != 0:
            # Main doesn't exist, create it
            logger.info("Main branch doesn't exist, creating orphan main")
            self._run_git("checkout", "--orphan", "main")
            self._run_git("commit", "--allow-empty", "-m", "init: main branch")
            self._run_git("push", "origin", "main")
    
    def setup_git_identity(self, agent_type: str, agent_index: int):
        """Configure git identity for agent."""
        name, email = get_git_identity(agent_type, agent_index)
        
        logger.info(f"Setting git identity: {name} <{email}>")
        self._run_git("config", "user.name", name)
        self._run_git("config", "user.email", email)
    
    def create_branch_from_main(self, branch_name: str):
        """Create new branch from main."""
        logger.info(f"Creating branch {branch_name} from main")
        
        self._run_git("fetch", "origin", "main")
        self._run_git("checkout", "-b", branch_name, "origin/main")
    
    def cherry_pick_from_previous(self, previous_branch: str):
        """Cherry-pick commits from previous branch."""
        if not previous_branch or previous_branch == "main":
            logger.info("No previous branch to cherry-pick from")
            return
        
        logger.info(f"Cherry-picking from {previous_branch}")
        
        # Fetch previous branch
        self._run_git("fetch", "origin", previous_branch)
        
        # Get commits in chronological order
        result = self._run_git(
            "log", f"origin/{previous_branch}",
            "--pretty=format:%H", "--reverse"
        )
        
        commits = result.stdout.strip().split("\n")
        
        if not commits or commits == [""]:
            logger.info("No commits to cherry-pick")
            return
        
        logger.info(f"Cherry-picking {len(commits)} commits")
        
        for commit in commits:
            # Try cherry-pick without auto-commit
            result = self._run_git("cherry-pick", commit, "--no-commit", check=False)
            
            if result.returncode != 0:
                # Conflict occurred - use theirs strategy
                logger.warning(f"Cherry-pick conflict on {commit}, using theirs strategy")
                self._run_git("checkout", "--theirs", ".")
                self._run_git("add", "-A")
                self._run_git("commit", "-m", f"cherry-pick: {commit} (resolved)")
    
    def commit_changes(self, commit_message: str) -> Optional[str]:
        """
        Commit changes if any exist.
        
        Returns:
            Commit hash if committed, None if no changes
        """
        # Check if there are changes
        result = self._run_git("diff", "--cached", "--quiet", check=False)
        
        if result.returncode == 0:
            # No staged changes, check unstaged
            result = self._run_git("diff", "--quiet", check=False)
            if result.returncode == 0:
                logger.info("No changes to commit")
                return None
        
        # Stage all changes
        self._run_git("add", "-A")
        
        # Commit
        logger.info(f"Committing: {commit_message}")
        self._run_git("commit", "-m", commit_message)
        
        # Get commit hash
        result = self._run_git("rev-parse", "HEAD")
        commit_hash = result.stdout.strip()
        
        return commit_hash
    
    def push_branch(self, branch_name: str):
        """Push branch to GitHub."""
        logger.info(f"Pushing {branch_name} to GitHub")
        self._run_git("push", "origin", branch_name)
    
    async def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        base: str = "main"
    ) -> Optional[str]:
        """
        Create pull request via GitHub API.
        
        Returns:
            PR URL if successful, None otherwise
        """
        import httpx
        
        # Extract owner and repo from URL
        # https://github.com/owner/repo
        parts = self.repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1].replace(".git", "")
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        
        headers = {
            "Authorization": f"token {self.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "head": branch_name,
            "base": base,
            "body": body
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                pr_data = response.json()
                pr_url = pr_data["html_url"]
                
                logger.info(f"Created PR: {pr_url}")
                return pr_url
        
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None
