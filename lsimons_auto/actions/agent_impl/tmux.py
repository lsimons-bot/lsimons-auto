"""
tmux.py - tmux terminal multiplexer control.

Provides functions for creating and managing tmux sessions, windows, and panes.
Replaces AppleScript/Ghostty for reliable operation in VMs.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def run_tmux(*args: str, check: bool = True) -> str:
    """Execute tmux command and return output."""
    try:
        result = subprocess.run(
            ["tmux", *args],
            check=check,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"tmux command failed: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "tmux not found. Install with: brew install tmux"
        ) from None


def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    try:
        run_tmux("has-session", "-t", session_name, check=True)
        return True
    except RuntimeError:
        return False


def create_session(session_name: str, working_dir: Path) -> str:
    """Create a new detached tmux session. Returns the pane ID of the first pane."""
    run_tmux(
        "new-session",
        "-d",  # detached
        "-s", session_name,
        "-c", str(working_dir),
        "-P", "-F", "#{pane_id}",  # print pane ID
    )
    # Get the pane ID of the initial pane
    pane_id = run_tmux(
        "list-panes",
        "-t", session_name,
        "-F", "#{pane_id}",
    )
    return pane_id.split("\n")[0]


def split_window_horizontal(session_name: str, working_dir: Path) -> str:
    """Split the current pane horizontally (side by side). Returns new pane ID."""
    output = run_tmux(
        "split-window",
        "-h",  # horizontal split
        "-t", session_name,
        "-c", str(working_dir),
        "-P", "-F", "#{pane_id}",
    )
    return output


def split_window_vertical(session_name: str, working_dir: Path) -> str:
    """Split the current pane vertically (stacked). Returns new pane ID."""
    output = run_tmux(
        "split-window",
        "-v",  # vertical split
        "-t", session_name,
        "-c", str(working_dir),
        "-P", "-F", "#{pane_id}",
    )
    return output


def split_pane_horizontal(pane_id: str, working_dir: Path) -> str:
    """Split a specific pane horizontally. Returns new pane ID."""
    output = run_tmux(
        "split-window",
        "-h",
        "-t", pane_id,
        "-c", str(working_dir),
        "-P", "-F", "#{pane_id}",
    )
    return output


def split_pane_vertical(pane_id: str, working_dir: Path) -> str:
    """Split a specific pane vertically. Returns new pane ID."""
    output = run_tmux(
        "split-window",
        "-v",
        "-t", pane_id,
        "-c", str(working_dir),
        "-P", "-F", "#{pane_id}",
    )
    return output


def select_pane(pane_id: str) -> None:
    """Focus a specific pane."""
    run_tmux("select-pane", "-t", pane_id)


def send_keys(pane_id: str, text: str, enter: bool = True) -> None:
    """Send text to a pane, optionally followed by Enter."""
    args = ["send-keys", "-t", pane_id, text]
    if enter:
        args.append("Enter")
    run_tmux(*args)


def kill_pane(pane_id: str) -> None:
    """Kill a specific pane."""
    run_tmux("kill-pane", "-t", pane_id)


def kill_session(session_name: str) -> None:
    """Kill an entire tmux session."""
    run_tmux("kill-session", "-t", session_name)


def attach_session(session_name: str) -> None:
    """Attach to a tmux session (replaces current process)."""
    # Use exec to replace current process
    os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])


def list_panes(session_name: str) -> list[str]:
    """List all pane IDs in a session."""
    output = run_tmux(
        "list-panes",
        "-t", session_name,
        "-F", "#{pane_id}",
    )
    if not output:
        return []
    return output.split("\n")


def resize_pane(pane_id: str, direction: str, amount: int) -> None:
    """Resize a pane in the given direction (L/R/U/D)."""
    run_tmux("resize-pane", "-t", pane_id, f"-{direction}", str(amount))


def select_layout(session_name: str, layout: str) -> None:
    """Apply a predefined layout to the session.

    Layouts: even-horizontal, even-vertical, main-horizontal, main-vertical, tiled
    """
    run_tmux("select-layout", "-t", session_name, layout)


def get_pane_info(session_name: str) -> list[dict[str, str]]:
    """Get detailed info about all panes in a session."""
    output = run_tmux(
        "list-panes",
        "-t", session_name,
        "-F", "#{pane_id}:#{pane_index}:#{pane_width}:#{pane_height}",
    )
    if not output:
        return []

    panes: list[dict[str, str]] = []
    for line in output.split("\n"):
        parts = line.split(":")
        if len(parts) >= 4:
            panes.append({
                "pane_id": parts[0],
                "pane_index": parts[1],
                "width": parts[2],
                "height": parts[3],
            })
    return panes


def focus_pane_direction(session_name: str, direction: str) -> None:
    """Focus pane in given direction (U/D/L/R)."""
    direction_map = {"up": "U", "down": "D", "left": "L", "right": "R"}
    tmux_dir = direction_map.get(direction.lower(), direction.upper())
    run_tmux("select-pane", "-t", session_name, f"-{tmux_dir}")


def is_inside_tmux() -> bool:
    """Check if we're running inside a tmux session."""
    return "TMUX" in os.environ


def get_current_session() -> Optional[str]:
    """Get the name of the current tmux session if inside one."""
    if not is_inside_tmux():
        return None
    try:
        return run_tmux("display-message", "-p", "#{session_name}")
    except RuntimeError:
        return None
