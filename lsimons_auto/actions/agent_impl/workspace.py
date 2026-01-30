"""
workspace.py - Workspace discovery and fuzzy matching.

Provides functions to scan for git repositories and match user queries.
"""

from pathlib import Path
from typing import Optional


# Constants
GIT_ROOT = Path.home() / "git"


def discover_workspaces(
    git_root: Optional[Path] = None,
) -> dict[str, dict[str, Path]]:
    """
    Scan ~/git for org/repo structure.
    Returns: {"org_name": {"repo_name": Path, ...}, ...}
    """
    if git_root is None:
        git_root = GIT_ROOT

    workspaces: dict[str, dict[str, Path]] = {}

    if not git_root.exists():
        return workspaces

    for org_dir in git_root.iterdir():
        if not org_dir.is_dir() or org_dir.name.startswith("."):
            continue

        repos: dict[str, Path] = {}
        for repo_dir in org_dir.iterdir():
            if (
                repo_dir.is_dir()
                and not repo_dir.name.startswith(".")
                and not repo_dir.name.endswith("-worktrees")
            ):
                repos[repo_dir.name] = repo_dir

        if repos:
            workspaces[org_dir.name] = repos

    return workspaces


def fuzzy_match_workspace(
    query_org: str,
    query_repo: str,
    workspaces: dict[str, dict[str, Path]],
) -> tuple[str, str, Path]:
    """
    Fuzzy match org and repo names (case-insensitive substring).
    Returns (org, repo, path).
    Raises ValueError if ambiguous or not found.
    """
    matching_orgs = [o for o in workspaces if query_org.lower() in o.lower()]

    if len(matching_orgs) == 0:
        raise ValueError(f"No org found matching '{query_org}'")
    if len(matching_orgs) > 1:
        # Prefer exact match if available
        exact = [o for o in matching_orgs if o.lower() == query_org.lower()]
        if len(exact) == 1:
            matching_orgs = exact
        else:
            raise ValueError(f"Ambiguous org match for '{query_org}': {matching_orgs}")

    org = matching_orgs[0]
    repos = workspaces[org]

    matching_repos = [r for r in repos if query_repo.lower() in r.lower()]

    if len(matching_repos) == 0:
        raise ValueError(f"No repo found matching '{query_repo}' in org '{org}'")
    if len(matching_repos) > 1:
        # Prefer exact match if available
        exact = [r for r in matching_repos if r.lower() == query_repo.lower()]
        if len(exact) == 1:
            matching_repos = exact
        else:
            raise ValueError(f"Ambiguous repo match for '{query_repo}': {matching_repos}")

    repo = matching_repos[0]
    return (org, repo, repos[repo])
