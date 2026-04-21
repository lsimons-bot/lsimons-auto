#!/usr/bin/env python3
"""
start_the_day.py - A lightweight daily startup script for macOS

See AGENTS.md for agent instructions and DESIGN.md for design decisions.
"""

import argparse
import datetime
import os
import socket
import subprocess
import sys
import time
import tomllib


def get_config_path(test_mode: bool = False) -> str:
    """Get the path to the configuration file."""
    if test_mode:
        return os.path.expanduser("~/.start_the_day_test.toml")
    return os.path.expanduser("~/.start_the_day.toml")


def parse_toml_simple(content: str) -> dict[str, str]:
    """Parse TOML content into a flat dictionary using Python's built-in tomllib."""
    try:
        data = tomllib.loads(content)
        # Convert all values to strings for backward compatibility
        return {str(k): str(v) for k, v in data.items()}
    except tomllib.TOMLDecodeError as e:
        print(f"Warning: Could not parse TOML content: {e}")
        return {}


def write_toml_simple(config: dict[str, str], filepath: str) -> None:
    """Simple TOML writer for our basic needs."""
    lines: list[str] = []
    lines.append("# start_the_day.py execution state")
    lines.append(f"# Generated on {datetime.datetime.now().isoformat()}")
    lines.append("")

    for key, value in config.items():
        lines.append(f'{key} = "{value}"')

    with open(filepath, "w") as f:
        _ = f.write("\n".join(lines) + "\n")


def load_execution_state(test_mode: bool = False) -> dict[str, str]:
    """Load execution state from config file."""
    config_path = get_config_path(test_mode)

    if not os.path.exists(config_path):
        return {}

    try:
        with open(config_path) as f:
            content = f.read()
        return parse_toml_simple(content)
    except OSError as e:
        print(f"Warning: Could not read config file {config_path}: {e}")
        return {}


def save_execution_state(config: dict[str, str], test_mode: bool = False) -> None:
    """Save execution state to config file."""
    config_path = get_config_path(test_mode)

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        write_toml_simple(config, config_path)
    except OSError as e:
        print(f"Error: Could not write config file {config_path}: {e}")
        sys.exit(1)


def get_today_date() -> str:
    """Get today's date in UTC as an ISO 8601 string."""
    return datetime.datetime.now(datetime.UTC).date().isoformat()


def already_ran_today(test_mode: bool = False) -> bool:
    """Check if the script already ran today."""
    config = load_execution_state(test_mode)
    last_run = config.get("last_run_date")
    today = get_today_date()

    return last_run == today


def update_execution_state(test_mode: bool = False) -> None:
    """Update the execution state to mark today as completed."""
    config = load_execution_state(test_mode)
    config["last_run_date"] = get_today_date()
    save_execution_state(config, test_mode)


def colorize_text(text: str, color: str, force_color: bool = False) -> str:
    """Apply ANSI color codes to text if output is to a terminal or forced."""
    # ANSI color codes
    colors = {
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "reset": "\033[0m",
    }

    if (sys.stdout.isatty() or force_color) and color in colors:
        return f"{colors[color]}{text}{colors['reset']}"
    return text


def run_command(command: list[str], action_name: str, success_message: str) -> bool:
    """Run a command with error handling and status messages. Returns True on success."""
    print(colorize_text(f"{action_name}: `{' '.join(command)}`...", "blue"))
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        print(colorize_text(f"✓ {success_message}", "green"))
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to {action_name.lower()}: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return False


def wait_for_network(
    host: str = "api.github.com",
    port: int = 443,
    timeout_seconds: int = 300,
) -> bool:
    """Wait until a TCP connection to host:port succeeds. Returns False on timeout.

    # Why: launchd StartCalendarInterval can fire during DarkWake before Wi-Fi is
    # usable. Block here so downstream steps don't silently fail on a half-awake
    # machine; callers should exit without marking the day done so the next wake retries.
    """
    deadline = time.monotonic() + timeout_seconds
    delay = 2.0
    while True:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except OSError as e:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print(f"Network check to {host}:{port} failed after {timeout_seconds}s: {e}")
                return False
            sleep_for = min(delay, remaining)
            print(f"Network not ready ({e}); retrying in {sleep_for:.0f}s...")
            time.sleep(sleep_for)
            delay = min(delay * 2, 30.0)


def start_the_day() -> bool:
    """Run the daily startup routine. Returns True only if all steps succeeded."""
    print(colorize_text("Good morning!", "yellow"))
    print(colorize_text("Starting your day...", "blue"))

    if not wait_for_network():
        print(colorize_text("Aborting — network unavailable. Will retry on next wake.", "yellow"))
        return False

    results: list[bool] = [
        run_command(["auto", "organize-desktop"], "Organizing desktop", "Desktop organized"),
        run_command(["auto", "git-sync"], "Syncing git repositories", "Git repositories synced"),
        run_command(
            ["auto", "clean-tmp"], "Cleaning scratch directory", "Scratch directory cleaned"
        ),
    ]

    # run_command(
    #     ["auto", "update-desktop-background"],
    #     "Updating desktop background",
    #     "Desktop background updated",
    # )

    # run_command(
    #     ["auto", "launch-apps"],
    #     "Launching apps",
    #     "Apps launched",
    # )

    all_ok = all(results)
    if all_ok:
        print(colorize_text("✓ Daily startup routine completed", "green"))
    else:
        print(colorize_text("✗ Daily startup had failures — will retry on next wake.", "yellow"))
    return all_ok


def main() -> None:
    """Main entry point with argument parsing."""
    print(f"Current date and time (UTC): {datetime.datetime.now(datetime.UTC).isoformat()}")

    parser = argparse.ArgumentParser(description="Daily startup script for macOS")

    _ = parser.add_argument(
        "--force", action="store_true", help="Force run even if already ran today"
    )

    args = parser.parse_args()

    # Check if already ran today (unless forced)
    if not args.force and already_ran_today():  # pyright: ignore[reportAny]
        print("Already ran today. Have a great day!")
        sys.exit(0)

    # Run the daily routine
    try:
        succeeded = start_the_day()
        if succeeded:
            update_execution_state()
            print("Daily startup completed successfully!")
        else:
            print("Daily startup incomplete — not marking today as done.")
            sys.exit(1)
    except Exception as e:
        print(f"Error during startup routine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
