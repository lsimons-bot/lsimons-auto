"""
zed.py - Zed editor integration and window positioning.

Provides functions for launching Zed and positioning windows on screen.
"""

import subprocess
import time
from pathlib import Path

from .ghostty import keystroke, run_applescript


def launch_zed_with_terminal(workspace_path: Path) -> None:
    """
    Launch Zed editor with workspace and open terminal panel.

    Note: Opens the original workspace, not worktrees, for unified code viewing.

    Args:
        workspace_path: Path to the git repository to open
    """
    subprocess.Popen(
        ["zed", str(workspace_path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)  # Wait for Zed to launch

    # Send Cmd+J to open terminal panel
    keystroke("Zed", "j", ["command"])


def position_windows_fill_screen() -> None:
    """Position Ghostty and Zed to fill screen (overlapping)."""
    script = """
    tell application "Finder"
        set screenBounds to bounds of window of desktop
        set screenWidth to item 3 of screenBounds
        set screenHeight to item 4 of screenBounds
    end tell

    tell application "System Events"
        tell process "Ghostty"
            try
                set frontWindow to front window
                set position of frontWindow to {0, 25}
                set size of frontWindow to {screenWidth, screenHeight - 25}
            end try
        end tell
    end tell

    tell application "System Events"
        tell process "Zed"
            try
                set frontWindow to front window
                set position of frontWindow to {0, 25}
                set size of frontWindow to {screenWidth, screenHeight - 25}
            end try
        end tell
    end tell
    """
    run_applescript(script)
