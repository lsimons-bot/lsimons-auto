"""
agent_impl - Implementation package for the agent action.

This package provides multi-agent Claude Code session management using tmux.
"""

from .cli import create_parser, main
from .session import (
    SESSIONS_DIR,
    AgentPane,
    AgentSession,
    find_pane_by_target,
    get_most_recent_session,
    list_sessions,
)
from .workspace import GIT_ROOT, discover_workspaces, fuzzy_match_workspace
from .worktree import ensure_worktree, ensure_worktrees_dir

__all__ = [
    # Main entry point
    "main",
    "create_parser",
    # Session management
    "AgentPane",
    "AgentSession",
    "SESSIONS_DIR",
    "list_sessions",
    "get_most_recent_session",
    "find_pane_by_target",
    # Workspace discovery
    "GIT_ROOT",
    "discover_workspaces",
    "fuzzy_match_workspace",
    # Worktree management
    "ensure_worktrees_dir",
    "ensure_worktree",
]
