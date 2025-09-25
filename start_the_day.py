#!/usr/bin/env python3
"""
start_the_day.py - A lightweight daily startup script for macOS

See AGENT.md for agent instructions and DESIGN.md for design decisions.
"""

import os
import sys
import datetime
import argparse


def get_config_path(test_mode: bool = False) -> str:
    """Get the path to the configuration file."""
    if test_mode:
        return os.path.expanduser("~/.start_the_day_test.toml")
    return os.path.expanduser("~/.start_the_day.toml")


def parse_toml_simple(content: str) -> dict[str, str]:
    """Simple TOML parser for our basic needs (last_run_date only)."""
    config: dict[str, str] = {}
    for line in content.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().strip("\"'")
                value = value.strip().strip("\"'")
                config[key] = value
    return config


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
        with open(config_path, "r") as f:
            content = f.read()
        return parse_toml_simple(content)
    except (IOError, OSError) as e:
        print(f"Warning: Could not read config file {config_path}: {e}")
        return {}


def save_execution_state(config: dict[str, str], test_mode: bool = False) -> None:
    """Save execution state to config file."""
    config_path = get_config_path(test_mode)

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        write_toml_simple(config, config_path)
    except (IOError, OSError) as e:
        print(f"Error: Could not write config file {config_path}: {e}")
        sys.exit(1)


def get_today_date() -> str:
    """Get today's date as a string."""
    return datetime.date.today().isoformat()


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


def start_the_day() -> None:
    """Main function that runs the daily startup routine."""
    print(colorize_text("Good morning!", "yellow"))
    print(colorize_text("Starting your day...", "blue"))

    # Add your daily startup tasks here
    print(colorize_text("✓ Daily startup routine completed", "green"))


def main() -> None:
    """Main entry point with argument parsing."""
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
        start_the_day()
        update_execution_state()
        print("Daily startup completed successfully!")
    except Exception as e:
        print(f"Error during startup routine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
