#!/usr/bin/env python3
"""
agent.py - Manage multiple Claude Code CLI instances in tmux

Spawns tmux sessions with configurable agent pane layouts, integrates with
Zed editor, and provides session management for multi-agent workflows.

This module is a thin wrapper that delegates to the agent_impl package.
All implementation is in lsimons_auto/actions/agent_impl/.
"""

# Handle both package import and direct script execution
try:
    # Package import (when imported as lsimons_auto.actions.agent)
    from .agent_impl import (
        GIT_ROOT,
        SESSIONS_DIR,
        AgentPane,
        AgentSession,
        create_parser,
        discover_workspaces,
        find_pane_by_target,
        fuzzy_match_workspace,
        get_most_recent_session,
        list_sessions,
        main,
    )
    from .agent_impl.cli import (
        cmd_attach,
        cmd_broadcast,
        cmd_close,
        cmd_focus,
        cmd_kill,
        cmd_list,
        cmd_send,
        cmd_spawn,
    )
    from .agent_impl.layout import create_layout, start_agents_in_panes
    from .agent_impl.tmux import (
        attach_session,
        create_session,
        focus_pane_direction,
        kill_pane,
        kill_session,
        run_tmux,
        select_pane,
        send_keys,
        session_exists,
        split_pane_horizontal,
        split_pane_vertical,
    )
    from .agent_impl.worktree import (
        ensure_worktree,
        ensure_worktrees_dir,
        get_worktree_branch,
        list_worktrees,
        remove_worktree,
    )
except ImportError:
    # Direct script execution (when run as `python agent.py`)
    from agent_impl import (  # pyright: ignore[reportMissingImports]
        GIT_ROOT,
        SESSIONS_DIR,
        AgentPane,
        AgentSession,
        create_parser,
        discover_workspaces,
        find_pane_by_target,
        fuzzy_match_workspace,
        get_most_recent_session,
        list_sessions,
        main,
    )
    from agent_impl.cli import (  # pyright: ignore[reportMissingImports]
        cmd_attach,
        cmd_broadcast,
        cmd_close,
        cmd_focus,
        cmd_kill,
        cmd_list,
        cmd_send,
        cmd_spawn,
    )
    from agent_impl.layout import (  # pyright: ignore[reportMissingImports]
        create_layout,
        start_agents_in_panes,
    )
    from agent_impl.tmux import (  # pyright: ignore[reportMissingImports]
        attach_session,
        create_session,
        focus_pane_direction,
        kill_pane,
        kill_session,
        run_tmux,
        select_pane,
        send_keys,
        session_exists,
        split_pane_horizontal,
        split_pane_vertical,
    )
    from agent_impl.worktree import (  # pyright: ignore[reportMissingImports]
        ensure_worktree,
        ensure_worktrees_dir,
        get_worktree_branch,
        list_worktrees,
        remove_worktree,
    )

__all__ = [
    # Main entry point
    "main",
    "create_parser",
    # Data classes
    "AgentPane",
    "AgentSession",
    # Constants
    "SESSIONS_DIR",
    "GIT_ROOT",
    # Session management
    "list_sessions",
    "get_most_recent_session",
    "find_pane_by_target",
    # Workspace discovery
    "discover_workspaces",
    "fuzzy_match_workspace",
    # Worktree management
    "ensure_worktrees_dir",
    "ensure_worktree",
    "get_worktree_branch",
    "remove_worktree",
    "list_worktrees",
    # tmux control
    "run_tmux",
    "session_exists",
    "create_session",
    "split_pane_horizontal",
    "split_pane_vertical",
    "select_pane",
    "send_keys",
    "kill_pane",
    "kill_session",
    "attach_session",
    "focus_pane_direction",
    # Layout
    "create_layout",
    "start_agents_in_panes",
    # Subcommand handlers
    "cmd_spawn",
    "cmd_attach",
    "cmd_send",
    "cmd_broadcast",
    "cmd_focus",
    "cmd_list",
    "cmd_close",
    "cmd_kill",
]

if __name__ == "__main__":
    main()
