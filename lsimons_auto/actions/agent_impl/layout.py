"""
layout.py - tmux pane layout creation and agent startup.

Creates multi-pane tmux layouts with git worktrees for isolated agent sessions.
"""

from pathlib import Path

from .session import AgentPane
from .tmux import (
    create_session,
    select_pane,
    send_keys,
    split_pane_horizontal,
    split_pane_vertical,
)
from .worktree import ensure_worktree, ensure_worktrees_dir


def create_layout(
    num_subagents: int,
    workspace_path: Path,
    command: str,
    repo_name: str,
    tmux_session_name: str,
) -> list[AgentPane]:
    """
    Create tmux layout with main + subagent panes.

    Each pane gets its own git worktree for isolated work:
    - Main pane: {repo}-worktrees/M
    - Subagents: {repo}-worktrees/001, 002, etc.

    Args:
        num_subagents: Number of subagent panes (1-4)
        workspace_path: Path to the original git repository
        command: Agent command to run (e.g., "claude")
        repo_name: Name of the repository
        tmux_session_name: Name for the tmux session

    Returns:
        List of AgentPane objects with worktree paths and tmux pane IDs
    """
    panes: list[AgentPane] = []

    # Create worktrees directory
    worktrees_dir = ensure_worktrees_dir(workspace_path)

    # Create worktree for main pane
    main_worktree = ensure_worktree(workspace_path, "M", worktrees_dir)

    # Create tmux session with main pane
    main_pane_id = create_session(tmux_session_name, main_worktree)

    # Main pane
    main_pane = AgentPane(
        id=f"M-{repo_name}",
        pane_index=0,
        command=command,
        is_main=True,
        worktree_path=str(main_worktree),
        tmux_pane_id=main_pane_id,
    )
    panes.append(main_pane)

    if num_subagents >= 1:
        # Create worktree for first subagent
        worktree_001 = ensure_worktree(workspace_path, "001", worktrees_dir)

        # Split right for first subagent (horizontal split from main)
        pane_001_id = split_pane_horizontal(main_pane_id, worktree_001)
        panes.append(
            AgentPane(
                id=f"001-{repo_name}",
                pane_index=1,
                command=command,
                is_main=False,
                worktree_path=str(worktree_001),
                tmux_pane_id=pane_001_id,
            )
        )

    if num_subagents >= 2:
        # Create worktree for second subagent
        worktree_002 = ensure_worktree(workspace_path, "002", worktrees_dir)

        # Split down from pane 001 (vertical split)
        pane_002_id = split_pane_vertical(panes[1].tmux_pane_id, worktree_002)  # type: ignore[arg-type]
        panes.append(
            AgentPane(
                id=f"002-{repo_name}",
                pane_index=2,
                command=command,
                is_main=False,
                worktree_path=str(worktree_002),
                tmux_pane_id=pane_002_id,
            )
        )

    if num_subagents >= 3:
        # Create worktree for third subagent
        worktree_003 = ensure_worktree(workspace_path, "003", worktrees_dir)

        # Split down from pane 002 (vertical split)
        pane_003_id = split_pane_vertical(panes[2].tmux_pane_id, worktree_003)  # type: ignore[arg-type]
        panes.append(
            AgentPane(
                id=f"003-{repo_name}",
                pane_index=3,
                command=command,
                is_main=False,
                worktree_path=str(worktree_003),
                tmux_pane_id=pane_003_id,
            )
        )

    if num_subagents >= 4:
        # Create worktrees for panes 3 and 4
        worktree_003 = worktrees_dir / "003"
        worktree_004 = ensure_worktree(workspace_path, "004", worktrees_dir)

        # For 4 subagents: main | s1/s2 | s3/s4
        # Split pane 001 horizontally to create right column
        pane_003_id = split_pane_horizontal(panes[1].tmux_pane_id, worktree_003)  # type: ignore[arg-type]
        # Re-assign pane 3 with correct tmux pane ID
        panes[3] = AgentPane(
            id=f"003-{repo_name}",
            pane_index=3,
            command=command,
            is_main=False,
            worktree_path=str(worktree_003),
            tmux_pane_id=pane_003_id,
        )
        # Split pane 003 vertically for pane 004
        pane_004_id = split_pane_vertical(pane_003_id, worktree_004)
        panes.append(
            AgentPane(
                id=f"004-{repo_name}",
                pane_index=4,
                command=command,
                is_main=False,
                worktree_path=str(worktree_004),
                tmux_pane_id=pane_004_id,
            )
        )

    # Focus back to main pane
    select_pane(main_pane_id)

    return panes


def start_agents_in_panes(panes: list[AgentPane]) -> None:
    """
    Start the agent command in each pane using tmux send-keys.

    Args:
        panes: List of AgentPane objects with tmux_pane_id set
    """
    for pane in panes:
        if pane.tmux_pane_id:
            send_keys(pane.tmux_pane_id, pane.command, enter=True)
