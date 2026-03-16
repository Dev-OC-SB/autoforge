"""
SeaForge Path Resolution
=========================

Central module for resolving paths to seaforge-generated files within a project.

Implements a tri-path resolution strategy for backward compatibility:

    1. Check ``project_dir / ".seaforge" / X`` (current layout)
    2. Check ``project_dir / ".autocoder" / X`` (legacy layout)
    3. Check ``project_dir / X`` (legacy root-level layout)
    4. Default to the new location for fresh projects

This allows existing projects with root-level ``features.db``, ``.agent.lock``,
etc. to keep working while new projects store everything under ``.seaforge/``.
Projects using the old ``.autocoder/`` directory are auto-migrated on next start.

The ``migrate_project_layout`` function can move an old-layout project to the
new layout safely, with full integrity checks for SQLite databases.
"""

import logging
import shutil
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# .gitignore content written into every .seaforge/ directory
# ---------------------------------------------------------------------------
_GITIGNORE_CONTENT = """\
# SeaForge runtime files
features.db
features.db-wal
features.db-shm
assistant.db
assistant.db-wal
assistant.db-shm
.agent.lock
.devserver.lock
.pause_drain
.claude_settings.json
.claude_assistant_settings.json
.claude_settings.expand.*.json
.progress_cache
.migration_version
"""


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _resolve_path(project_dir: Path, filename: str) -> Path:
    """Resolve a file path using tri-path strategy.

    Checks the new ``.seaforge/`` location first, then the legacy
    ``.autocoder/`` location, then the root-level location.  If none exist,
    returns the new location so that newly-created files land in ``.seaforge/``.
    """
    new = project_dir / ".seaforge" / filename
    if new.exists():
        return new
    legacy = project_dir / ".autocoder" / filename
    if legacy.exists():
        return legacy
    old = project_dir / filename
    if old.exists():
        return old
    return new  # default for new projects


def _resolve_dir(project_dir: Path, dirname: str) -> Path:
    """Resolve a directory path using tri-path strategy.

    Same logic as ``_resolve_path`` but intended for directories such as
    ``prompts/``.
    """
    new = project_dir / ".seaforge" / dirname
    if new.exists():
        return new
    legacy = project_dir / ".autocoder" / dirname
    if legacy.exists():
        return legacy
    old = project_dir / dirname
    if old.exists():
        return old
    return new


# ---------------------------------------------------------------------------
# .seaforge directory management
# ---------------------------------------------------------------------------

def get_seaforge_dir(project_dir: Path) -> Path:
    """Return the ``.seaforge`` directory path.  Does NOT create it."""
    return project_dir / ".seaforge"


def ensure_seaforge_dir(project_dir: Path) -> Path:
    """Create the ``.seaforge/`` directory (if needed) and write its ``.gitignore``.

    Returns:
        The path to the ``.seaforge`` directory.
    """
    seaforge_dir = get_seaforge_dir(project_dir)
    seaforge_dir.mkdir(parents=True, exist_ok=True)

    gitignore_path = seaforge_dir / ".gitignore"
    gitignore_path.write_text(_GITIGNORE_CONTENT, encoding="utf-8")

    return seaforge_dir


# ---------------------------------------------------------------------------
# Dual-path file helpers
# ---------------------------------------------------------------------------

def get_features_db_path(project_dir: Path) -> Path:
    """Resolve the path to ``features.db``."""
    return _resolve_path(project_dir, "features.db")


def get_assistant_db_path(project_dir: Path) -> Path:
    """Resolve the path to ``assistant.db``."""
    return _resolve_path(project_dir, "assistant.db")


def get_agent_lock_path(project_dir: Path) -> Path:
    """Resolve the path to ``.agent.lock``."""
    return _resolve_path(project_dir, ".agent.lock")


def get_devserver_lock_path(project_dir: Path) -> Path:
    """Resolve the path to ``.devserver.lock``."""
    return _resolve_path(project_dir, ".devserver.lock")


def get_claude_settings_path(project_dir: Path) -> Path:
    """Resolve the path to ``.claude_settings.json``."""
    return _resolve_path(project_dir, ".claude_settings.json")


def get_claude_assistant_settings_path(project_dir: Path) -> Path:
    """Resolve the path to ``.claude_assistant_settings.json``."""
    return _resolve_path(project_dir, ".claude_assistant_settings.json")


def get_pause_drain_path(project_dir: Path) -> Path:
    """Return the path to the ``.pause_drain`` signal file.

    This file is created to request a graceful pause (drain mode).
    Always uses the new location since it's a transient signal file.
    """
    return project_dir / ".seaforge" / ".pause_drain"


def get_progress_cache_path(project_dir: Path) -> Path:
    """Resolve the path to ``.progress_cache``."""
    return _resolve_path(project_dir, ".progress_cache")


def get_prompts_dir(project_dir: Path) -> Path:
    """Resolve the path to the ``prompts/`` directory."""
    return _resolve_dir(project_dir, "prompts")


# ---------------------------------------------------------------------------
# Non-dual-path helpers (always use new location)
# ---------------------------------------------------------------------------

def get_expand_settings_path(project_dir: Path, uuid_hex: str) -> Path:
    """Return the path for an ephemeral expand-session settings file.

    These files are short-lived and always stored in ``.seaforge/``.
    """
    return project_dir / ".seaforge" / f".claude_settings.expand.{uuid_hex}.json"


# ---------------------------------------------------------------------------
# Temp directory helpers (for GitHub-backed projects)
# ---------------------------------------------------------------------------

def get_temp_projects_root() -> Path:
    """Return the root directory for temp projects."""
    return Path.home() / ".seaforge" / "temp-projects"


def get_temp_project_dir(project_name: str) -> Path:
    """Get temp directory path for a project.
    
    Args:
        project_name: Name of the project
    
    Returns:
        Path to temp directory for the project
    """
    return get_temp_projects_root() / project_name


def ensure_temp_project_dir(project_name: str) -> Path:
    """Create temp directory for a project if it doesn't exist.
    
    Args:
        project_name: Name of the project
    
    Returns:
        Path to temp directory
    """
    temp_dir = get_temp_project_dir(project_name)
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def is_temp_project(project_dir: Path) -> bool:
    """Check if a project is in the temp directory.
    
    Args:
        project_dir: Path to the project directory
    
    Returns:
        True if project is in temp directory
    """
    try:
        project_dir = Path(project_dir).resolve()
        temp_root = get_temp_projects_root().resolve()
        return project_dir.is_relative_to(temp_root)
    except (ValueError, OSError):
        return False


# ---------------------------------------------------------------------------
# Lock-file safety check
# ---------------------------------------------------------------------------

def has_agent_running(project_dir: Path) -> bool:
    """Check whether any agent or dev-server lock file exists at either location.

    Inspects the legacy root-level paths, the old ``.autocoder/`` paths, and
    the new ``.seaforge/`` paths so that a running agent is detected
    regardless of project layout.

    Returns:
        ``True`` if any ``.agent.lock`` or ``.devserver.lock`` exists.
    """
    lock_names = (".agent.lock", ".devserver.lock")
    for name in lock_names:
        if (project_dir / name).exists():
            return True
        # Check both old and new directory names for backward compatibility
        if (project_dir / ".autocoder" / name).exists():
            return True
        if (project_dir / ".seaforge" / name).exists():
            return True
    return False


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

def migrate_project_layout(project_dir: Path) -> list[str]:
    """Migrate a project from the legacy root-level layout to ``.seaforge/``.

    The migration is incremental and safe:

    * If the agent is running (lock files present) the migration is skipped
      entirely to avoid corrupting in-use databases.
    * Each file/directory is migrated independently.  If any single step
      fails the error is logged and migration continues with the remaining
      items.  Partial migration is safe because the dual-path resolution
      strategy will find files at whichever location they ended up in.

    Returns:
        A list of human-readable descriptions of what was migrated, e.g.
        ``["prompts/ -> .seaforge/prompts/", "features.db -> .seaforge/features.db"]``.
        An empty list means nothing was migrated (either everything is
        already migrated, or the agent is running).
    """
    # Safety: refuse to migrate while an agent is running
    if has_agent_running(project_dir):
        logger.warning("Migration skipped: agent or dev-server is running for %s", project_dir)
        return []

    # --- 0. Migrate .autocoder/ → .seaforge/ directory -------------------
    old_autocoder_dir = project_dir / ".autocoder"
    new_seaforge_dir = project_dir / ".seaforge"
    if old_autocoder_dir.exists() and old_autocoder_dir.is_dir() and not new_seaforge_dir.exists():
        try:
            old_autocoder_dir.rename(new_seaforge_dir)
            logger.info("Migrated .autocoder/ -> .seaforge/")
            migrated: list[str] = [".autocoder/ -> .seaforge/"]
        except Exception:
            logger.warning("Failed to migrate .autocoder/ -> .seaforge/", exc_info=True)
            migrated = []
    else:
        migrated = []

    seaforge_dir = ensure_seaforge_dir(project_dir)

    # --- 1. Migrate prompts/ directory -----------------------------------
    try:
        old_prompts = project_dir / "prompts"
        new_prompts = seaforge_dir / "prompts"
        if old_prompts.exists() and old_prompts.is_dir() and not new_prompts.exists():
            shutil.copytree(str(old_prompts), str(new_prompts))
            shutil.rmtree(str(old_prompts))
            migrated.append("prompts/ -> .seaforge/prompts/")
            logger.info("Migrated prompts/ -> .seaforge/prompts/")
    except Exception:
        logger.warning("Failed to migrate prompts/ directory", exc_info=True)

    # --- 2. Migrate SQLite databases (features.db, assistant.db) ---------
    db_names = ("features.db", "assistant.db")
    for db_name in db_names:
        try:
            old_db = project_dir / db_name
            new_db = seaforge_dir / db_name
            if old_db.exists() and not new_db.exists():
                # Flush WAL to ensure all data is in the main database file
                conn = sqlite3.connect(str(old_db))
                try:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                finally:
                    conn.close()

                # Copy the main database file (WAL is now flushed)
                shutil.copy2(str(old_db), str(new_db))

                # Verify the copy is intact
                verify_conn = sqlite3.connect(str(new_db))
                try:
                    verify_cursor = verify_conn.cursor()
                    result = verify_cursor.execute("PRAGMA integrity_check").fetchone()
                    if result is None or result[0] != "ok":
                        logger.error(
                            "Integrity check failed for migrated %s: %s",
                            db_name, result,
                        )
                        # Remove the broken copy; old file stays in place
                        new_db.unlink(missing_ok=True)
                        continue
                finally:
                    verify_conn.close()

                # Remove old database files (.db, .db-wal, .db-shm)
                old_db.unlink(missing_ok=True)
                for suffix in ("-wal", "-shm"):
                    wal_file = project_dir / f"{db_name}{suffix}"
                    wal_file.unlink(missing_ok=True)

                migrated.append(f"{db_name} -> .seaforge/{db_name}")
                logger.info("Migrated %s -> .seaforge/%s", db_name, db_name)
        except Exception:
            logger.warning("Failed to migrate %s", db_name, exc_info=True)

    # --- 3. Migrate simple files -----------------------------------------
    simple_files = (
        ".agent.lock",
        ".devserver.lock",
        ".claude_settings.json",
        ".claude_assistant_settings.json",
        ".progress_cache",
    )
    for filename in simple_files:
        try:
            old_file = project_dir / filename
            new_file = seaforge_dir / filename
            if old_file.exists() and not new_file.exists():
                shutil.move(str(old_file), str(new_file))
                migrated.append(f"{filename} -> .seaforge/{filename}")
                logger.info("Migrated %s -> .seaforge/%s", filename, filename)
        except Exception:
            logger.warning("Failed to migrate %s", filename, exc_info=True)

    return migrated
