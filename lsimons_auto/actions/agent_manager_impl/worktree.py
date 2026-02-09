"""
worktree.py - Git worktree management for isolated agent workspaces.

Provides functions to create and manage git worktrees for parallel Claude sessions.
"""

import contextlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def ensure_worktrees_dir(workspace_path: Path) -> Path:
    """
    Create worktrees directory if it doesn't exist.

    Creates a sibling directory to the workspace named {repo}-worktrees.
    For example: /Users/lsimons/git/lsimons/lsimons-auto
    becomes:     /Users/lsimons/git/lsimons/lsimons-auto-worktrees

    Args:
        workspace_path: Path to the original git repository

    Returns:
        Path to the worktrees directory
    """
    worktrees_dir = workspace_path.parent / f"{workspace_path.name}-worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)
    return worktrees_dir


def ensure_worktree(
    workspace_path: Path,
    worktree_name: str,
    worktrees_dir: Path,
) -> Path:
    """
    Create a git worktree if it doesn't exist.

    Each worktree gets a unique branch named {worktree_name}-{timestamp}.
    For example: M-20260121-143052, 001-20260121-143052

    Args:
        workspace_path: Path to the original git repository
        worktree_name: Name for the worktree directory (e.g., "M", "001")
        worktrees_dir: Directory to create worktrees in

    Returns:
        Path to the worktree directory
    """
    worktree_path = worktrees_dir / worktree_name

    if worktree_path.exists():
        # Worktree already exists, verify it's valid
        if (worktree_path / ".git").exists():
            return worktree_path
        # Directory exists but isn't a worktree - remove it
        import shutil

        shutil.rmtree(worktree_path)

    # Generate unique branch name with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    branch_name = f"{worktree_name}-{timestamp}"

    # Create the worktree with a new branch
    try:
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
            cwd=workspace_path,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create worktree '{worktree_name}': {e.stderr}") from e

    return worktree_path


def get_worktree_branch(worktree_path: Path) -> str:
    """
    Get the branch name for a worktree.

    Args:
        worktree_path: Path to the worktree

    Returns:
        Name of the branch
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get worktree branch: {e.stderr}") from e


def remove_worktree(workspace_path: Path, worktree_path: Path) -> None:
    """
    Remove a git worktree.

    Args:
        workspace_path: Path to the original git repository
        worktree_path: Path to the worktree to remove
    """
    with contextlib.suppress(subprocess.CalledProcessError):
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=workspace_path,
            check=True,
            capture_output=True,
            text=True,
        )


def list_worktrees(workspace_path: Path) -> list[tuple[Path, str]]:
    """
    List all worktrees for a repository.

    Args:
        workspace_path: Path to the original git repository

    Returns:
        List of (worktree_path, branch_name) tuples
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=workspace_path,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []

    worktrees: list[tuple[Path, str]] = []
    current_path: Path | None = None
    current_branch: str | None = None

    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line[9:])
        elif line.startswith("branch refs/heads/"):
            current_branch = line[18:]
        elif line == "":
            if current_path and current_branch:
                worktrees.append((current_path, current_branch))
            current_path = None
            current_branch = None

    return worktrees
