"""
cli.py - Command-line argument parser and subcommand handlers.

Defines the CLI interface for the agent action.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional

from .layout import create_layout, start_agents_in_panes
from .session import (
    AgentSession,
    find_pane_by_target,
    get_most_recent_session,
    list_sessions,
)
from .tmux import (
    attach_session,
    focus_pane_direction,
    kill_pane,
    kill_session,
    select_pane,
    send_keys,
    session_exists,
)
from .workspace import discover_workspaces, fuzzy_match_workspace


# =============================================================================
# Subcommand Handlers
# =============================================================================


def cmd_spawn(args: argparse.Namespace) -> None:
    """Create new agent layout."""
    # Workspace selection
    if args.org and args.repo:
        workspaces = discover_workspaces()
        org, repo, workspace_path = fuzzy_match_workspace(args.org, args.repo, workspaces)
    else:
        # Interactive mode not implemented - require args
        print("Error: org and repo arguments required")
        print("Usage: auto agent spawn <org> <repo>")
        sys.exit(1)

    print(f"Workspace: {org}/{repo} ({workspace_path})")

    # Generate session ID and tmux session name
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    session_id = f"auto-agent-{timestamp}"
    tmux_session_name = session_id  # Use same name for tmux session

    # Create layout (this also creates worktrees and tmux session)
    print(f"Creating layout with {args.subagents} subagent(s)...")
    panes = create_layout(
        args.subagents, workspace_path, args.command, repo, tmux_session_name
    )

    # Launch Zed if requested (opens original repo, not worktrees)
    if not args.no_zed:
        print("Launching Zed editor...")
        try:
            subprocess.Popen(
                ["zed", str(workspace_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print("Warning: Zed not found, skipping editor launch")

    # Start agents in panes
    print("Starting agents...")
    start_agents_in_panes(panes)

    # Create and save session
    session = AgentSession(
        session_id=session_id,
        workspace_path=str(workspace_path),
        repo_name=repo,
        org_name=org,
        created_at=datetime.now(timezone.utc).isoformat(),
        panes=panes,
        tmux_session_name=tmux_session_name,
    )
    session.save()

    print(f"Session created: {session_id}")
    print(f"Panes: {', '.join(p.id for p in panes)}")

    # Show worktree paths
    for pane in panes:
        if pane.worktree_path:
            print(f"  {pane.id}: {pane.worktree_path}")

    # Attach to tmux session unless --no-attach
    if not args.no_attach:
        print(f"\nAttaching to tmux session: {tmux_session_name}")
        attach_session(tmux_session_name)  # This replaces the current process


def cmd_send(args: argparse.Namespace) -> None:
    """Send text to specific agent."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Check tmux session exists
    if not session.tmux_session_name or not session_exists(session.tmux_session_name):
        print(f"Error: tmux session not found: {session.tmux_session_name}")
        print("The session may have been terminated. Use 'auto agent kill' to clean up.")
        sys.exit(1)

    # Find target pane
    result = find_pane_by_target(session, args.target)
    if not result:
        print(f"Error: Pane not found: {args.target}")
        print(f"Available panes: {', '.join(p.id for p in session.panes)}")
        sys.exit(1)

    pane, _ = result
    text = " ".join(args.text)

    if not pane.tmux_pane_id:
        print(f"Error: Pane {pane.id} has no tmux pane ID")
        sys.exit(1)

    # Send text to pane
    send_keys(pane.tmux_pane_id, text, enter=True)
    print(f"Sent to {pane.id}: {text}")


def cmd_broadcast(args: argparse.Namespace) -> None:
    """Send text to all agents."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Check tmux session exists
    if not session.tmux_session_name or not session_exists(session.tmux_session_name):
        print(f"Error: tmux session not found: {session.tmux_session_name}")
        sys.exit(1)

    text = " ".join(args.text)
    target_panes = session.panes

    if args.exclude_main:
        target_panes = [p for p in target_panes if not p.is_main]

    # Send to each pane
    for pane in target_panes:
        if pane.tmux_pane_id:
            send_keys(pane.tmux_pane_id, text, enter=True)
            print(f"Sent to {pane.id}")

    print(f"Broadcast complete: {text}")


def cmd_focus(args: argparse.Namespace) -> None:
    """Focus agent pane."""
    # Get session first (needed for both direction and pane targeting)
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Check tmux session exists
    if not session.tmux_session_name or not session_exists(session.tmux_session_name):
        print(f"Error: tmux session not found: {session.tmux_session_name}")
        sys.exit(1)

    # Check if it's a direction
    if args.target.lower() in ("left", "right", "up", "down"):
        focus_pane_direction(session.tmux_session_name, args.target.lower())
        print(f"Focused {args.target}")
        return

    # Find target pane
    result = find_pane_by_target(session, args.target)
    if not result:
        print(f"Error: Pane not found: {args.target}")
        sys.exit(1)

    pane, _ = result

    if not pane.tmux_pane_id:
        print(f"Error: Pane {pane.id} has no tmux pane ID")
        sys.exit(1)

    select_pane(pane.tmux_pane_id)
    print(f"Focused: {pane.id}")


def cmd_list(args: argparse.Namespace) -> None:
    """List active sessions."""
    sessions = list_sessions()

    if not sessions:
        print("No active sessions")
        return

    for session in sessions:
        # Check if tmux session still exists
        tmux_active = (
            session.tmux_session_name
            and session_exists(session.tmux_session_name)
        )
        status = "" if tmux_active else " (tmux session gone)"

        if args.verbose:
            print(f"\nSession: {session.session_id}{status}")
            print(f"  Workspace: {session.org_name}/{session.repo_name}")
            print(f"  Path: {session.workspace_path}")
            print(f"  Created: {session.created_at}")
            print(f"  tmux session: {session.tmux_session_name}")
            print(f"  Panes: {len(session.panes)}")
            for pane in session.panes:
                main_marker = " (main)" if pane.is_main else ""
                worktree_info = f" @ {pane.worktree_path}" if pane.worktree_path else ""
                pane_id_info = f" [{pane.tmux_pane_id}]" if pane.tmux_pane_id else ""
                print(f"    - {pane.id}: {pane.command}{main_marker}{pane_id_info}{worktree_info}")
        else:
            pane_count = len(session.panes)
            print(
                f"{session.session_id}: {session.org_name}/{session.repo_name} "
                f"({pane_count} panes){status}"
            )


def cmd_close(args: argparse.Namespace) -> None:
    """Close specific agent pane."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Check tmux session exists
    if not session.tmux_session_name or not session_exists(session.tmux_session_name):
        print(f"Error: tmux session not found: {session.tmux_session_name}")
        sys.exit(1)

    # Find target pane
    result = find_pane_by_target(session, args.target)
    if not result:
        print(f"Error: Pane not found: {args.target}")
        sys.exit(1)

    pane, _ = result

    if not pane.tmux_pane_id:
        print(f"Error: Pane {pane.id} has no tmux pane ID")
        sys.exit(1)

    # Close the pane
    kill_pane(pane.tmux_pane_id)

    # Update session
    session.panes = [p for p in session.panes if p.id != pane.id]
    if session.panes:
        session.save()
    else:
        # All panes closed, clean up session
        session.delete()

    print(f"Closed: {pane.id}")


def cmd_kill(args: argparse.Namespace) -> None:
    """Terminate session and close window."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    if not args.force:
        print(f"Kill session {session.session_id}? [y/N] ", end="", flush=True)
        response = input().strip().lower()
        if response != "y":
            print("Cancelled")
            return

    # Kill tmux session if it exists
    if session.tmux_session_name and session_exists(session.tmux_session_name):
        kill_session(session.tmux_session_name)
        print(f"Killed tmux session: {session.tmux_session_name}")
    else:
        print(f"tmux session not found (may already be closed)")

    # Delete session file
    session.delete()
    print(f"Killed session: {session.session_id}")


def cmd_attach(args: argparse.Namespace) -> None:
    """Attach to an existing tmux session."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    if not session.tmux_session_name:
        print(f"Error: Session {session.session_id} has no tmux session name")
        sys.exit(1)

    if not session_exists(session.tmux_session_name):
        print(f"Error: tmux session not found: {session.tmux_session_name}")
        print("The session may have been terminated. Use 'auto agent kill' to clean up.")
        sys.exit(1)

    print(f"Attaching to: {session.tmux_session_name}")
    attach_session(session.tmux_session_name)  # This replaces the current process


# =============================================================================
# Argument Parser
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="auto agent",
        description="Manage Claude Code agent sessions in tmux",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # spawn subcommand
    spawn_parser = subparsers.add_parser("spawn", help="Create new agent layout")
    spawn_parser.add_argument("org", nargs="?", help="Organization (fuzzy match)")
    spawn_parser.add_argument("repo", nargs="?", help="Repository (fuzzy match)")
    spawn_parser.add_argument(
        "--subagents",
        "-n",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="Number of subagent panes (default: 1)",
    )
    spawn_parser.add_argument(
        "--command",
        "-c",
        default="claude",
        help="Agent command to run (default: claude)",
    )
    spawn_parser.add_argument(
        "--no-zed",
        action="store_true",
        help="Skip launching Zed editor",
    )
    spawn_parser.add_argument(
        "--no-attach",
        action="store_true",
        help="Don't attach to tmux session after creation",
    )

    # attach subcommand
    attach_parser = subparsers.add_parser("attach", help="Attach to existing session")
    attach_parser.add_argument(
        "session", nargs="?", help="Session ID (default: most recent)"
    )

    # send subcommand
    send_parser = subparsers.add_parser("send", help="Send text to specific agent")
    send_parser.add_argument("target", help="Agent ID, pane index, or 'main'")
    send_parser.add_argument("text", nargs="+", help="Text to send")
    send_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )

    # broadcast subcommand
    broadcast_parser = subparsers.add_parser(
        "broadcast", help="Send text to all agents"
    )
    broadcast_parser.add_argument("text", nargs="+", help="Text to broadcast")
    broadcast_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )
    broadcast_parser.add_argument(
        "--exclude-main",
        action="store_true",
        help="Exclude main agent from broadcast",
    )

    # focus subcommand
    focus_parser = subparsers.add_parser("focus", help="Focus agent pane")
    focus_parser.add_argument(
        "target", help="Agent ID, pane index, or direction (left/right/up/down)"
    )
    focus_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )

    # list subcommand
    list_parser = subparsers.add_parser("list", help="List active sessions")
    list_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed session info"
    )

    # close subcommand
    close_parser = subparsers.add_parser("close", help="Close specific agent pane")
    close_parser.add_argument("target", help="Agent ID or pane index")
    close_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )

    # kill subcommand
    kill_parser = subparsers.add_parser(
        "kill", help="Terminate session and close window"
    )
    kill_parser.add_argument(
        "session", nargs="?", help="Session ID (default: most recent)"
    )
    kill_parser.add_argument(
        "--force", "-f", action="store_true", help="Force kill without confirmation"
    )

    return parser


# =============================================================================
# Main Entry Point
# =============================================================================


def main(args: Optional[list[str]] = None) -> None:
    """Main entry point for agent action."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    try:
        if parsed_args.subcommand == "spawn":
            cmd_spawn(parsed_args)
        elif parsed_args.subcommand == "attach":
            cmd_attach(parsed_args)
        elif parsed_args.subcommand == "send":
            cmd_send(parsed_args)
        elif parsed_args.subcommand == "broadcast":
            cmd_broadcast(parsed_args)
        elif parsed_args.subcommand == "focus":
            cmd_focus(parsed_args)
        elif parsed_args.subcommand == "list":
            cmd_list(parsed_args)
        elif parsed_args.subcommand == "close":
            cmd_close(parsed_args)
        elif parsed_args.subcommand == "kill":
            cmd_kill(parsed_args)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(130)
