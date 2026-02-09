"""
ghostty.py - AppleScript helpers and Ghostty terminal control.

Provides low-level functions for interacting with macOS and Ghostty.
"""

import subprocess
import time

# Constants
APPLESCRIPT_DELAY = 0.3  # seconds between AppleScript actions


def run_applescript(script: str) -> str:
    """Execute AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AppleScript failed: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError("osascript not found. This action requires macOS.") from None


def activate_app(app: str) -> None:
    """Activate (bring to front) an application."""
    script = f'tell application "{app}" to activate'
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def keystroke(app: str, key: str, modifiers: list[str] | None = None) -> None:
    """Send keystroke to application."""
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(f"{m} down" for m in modifiers) + "}"

    script = f'''
    tell application "{app}" to activate
    delay 0.1
    tell application "System Events"
        tell process "{app}"
            keystroke "{key}"{mod_str}
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def key_code(app: str, code: int, modifiers: list[str] | None = None) -> None:
    """Send key code to application."""
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(f"{m} down" for m in modifiers) + "}"

    script = f'''
    tell application "{app}" to activate
    delay 0.1
    tell application "System Events"
        tell process "{app}"
            key code {code}{mod_str}
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def send_text(app: str, text: str) -> None:
    """Type text into the focused application."""
    # Escape special characters for AppleScript
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')

    script = f'''
    tell application "{app}" to activate
    delay 0.1
    tell application "System Events"
        tell process "{app}"
            keystroke "{escaped}"
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def press_return(app: str) -> None:
    """Press return/enter key."""
    key_code(app, 36)  # 36 = return key


# =============================================================================
# Ghostty-specific functions
# =============================================================================


def ghostty_new_window() -> None:
    """Create a new Ghostty window."""
    keystroke("Ghostty", "n", ["command"])
    time.sleep(0.5)  # Extra delay for window creation


def ghostty_split_right() -> None:
    """Split current pane horizontally (Cmd+D)."""
    keystroke("Ghostty", "d", ["command"])


def ghostty_split_down() -> None:
    """Split current pane vertically (Cmd+Shift+D)."""
    keystroke("Ghostty", "D", ["command", "shift"])


def ghostty_focus_direction(direction: str) -> None:
    """Focus pane in given direction using Cmd+Opt+Arrow (Ghostty's goto_split)."""
    # Key codes: left=123, right=124, down=125, up=126
    key_codes = {"left": 123, "right": 124, "down": 125, "up": 126}
    if direction not in key_codes:
        raise ValueError(f"Invalid direction: {direction}. Use: left, right, up, down")
    key_code("Ghostty", key_codes[direction], ["command", "option"])


def ghostty_close_pane() -> None:
    """Close current pane (Cmd+W)."""
    keystroke("Ghostty", "w", ["command"])


def ghostty_run_command(cmd: str) -> None:
    """Type and execute a command in Ghostty."""
    send_text("Ghostty", cmd)
    press_return("Ghostty")
    time.sleep(APPLESCRIPT_DELAY)


def ghostty_get_front_window_id() -> int | None:
    """Get the ID of the front Ghostty window."""
    script = """
    tell application "System Events"
        tell process "Ghostty"
            try
                return id of front window
            on error
                return ""
            end try
        end tell
    end tell
    """
    try:
        result = run_applescript(script)
        if result:
            return int(result)
    except (ValueError, RuntimeError):
        pass
    return None


def ghostty_close_window_by_id(window_id: int) -> bool:
    """Close a specific Ghostty window by its ID. Returns True if successful."""
    # First, bring the target window to front, then close it
    script = f"""
    tell application "System Events"
        tell process "Ghostty"
            try
                set targetWindow to (first window whose id is {window_id})
                -- Bring to front by setting focused
                set frontmost to true
                perform action "AXRaise" of targetWindow
                return "found"
            on error
                return "not_found"
            end try
        end tell
    end tell
    """
    try:
        result = run_applescript(script)
        if result != "found":
            return False
        # Now close the front window
        time.sleep(0.2)
        keystroke("Ghostty", "w", ["command", "shift"])
        return True
    except RuntimeError:
        return False
