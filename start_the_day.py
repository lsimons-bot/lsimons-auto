#!/usr/bin/env python3
"""
start_the_day.py - A lightweight daily startup script for macOS

See AGENT.md for agent instructions and DESIGN.md for design decisions.
"""

import os
import sys
import datetime
import argparse
import unittest
from unittest.mock import patch

import tempfile


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
        "--test", action="store_true", help="Run unit tests instead of normal operation"
    )
    _ = parser.add_argument(
        "--force", action="store_true", help="Force run even if already ran today"
    )

    args = parser.parse_args()

    if args.test:  # pyright: ignore[reportAny]
        # Run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestStartTheDay)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 2)

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


# Unit Tests
class TestStartTheDay(unittest.TestCase):
    """Unit tests for start_the_day.py functionality."""

    def setUp(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Set up test environment."""
        # Clean up any existing test config file
        test_config_path = get_config_path(test_mode=True)
        if os.path.exists(test_config_path):
            os.remove(test_config_path)

    def tearDown(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Clean up test environment."""
        # Clean up test config file after each test
        test_config_path = get_config_path(test_mode=True)
        if os.path.exists(test_config_path):
            os.remove(test_config_path)

    def test_parse_toml_simple(self) -> None:
        """Test simple TOML parsing."""
        content = 'last_run_date = "2024-01-15"\n# comment\nother_key = "value"'
        result = parse_toml_simple(content)
        expected = {"last_run_date": "2024-01-15", "other_key": "value"}
        self.assertEqual(result, expected)

    def test_parse_toml_empty(self) -> None:
        """Test parsing empty TOML content."""
        result = parse_toml_simple("")
        self.assertEqual(result, {})

    def test_get_today_date(self) -> None:
        """Test date string format."""
        today = get_today_date()
        # Should be in ISO format YYYY-MM-DD
        self.assertRegex(today, r"^\d{4}-\d{2}-\d{2}$")

        # Should be parseable back to a date
        parsed = datetime.date.fromisoformat(today)
        self.assertEqual(parsed, datetime.date.today())

    def test_load_execution_state(self) -> None:
        """Test loading execution state from file."""
        # Create a test config file
        test_config_path = get_config_path(test_mode=True)
        with open(test_config_path, "w") as f:
            _ = f.write('last_run_date = "2024-01-15"\n')

        result = load_execution_state(test_mode=True)
        expected = {"last_run_date": "2024-01-15"}
        self.assertEqual(result, expected)

    def test_load_execution_state_no_file(self) -> None:
        """Test loading execution state when file doesn't exist."""
        result = load_execution_state(test_mode=True)
        self.assertEqual(result, {})

    def test_write_toml_simple(self) -> None:
        """Test TOML writing functionality."""
        config = {"last_run_date": "2024-01-15", "other_key": "value"}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            temp_path = f.name

        try:
            write_toml_simple(config, temp_path)

            # Read back the file and check content
            with open(temp_path, "r") as f:
                written_content = f.read()

            self.assertIn('last_run_date = "2024-01-15"', written_content)
            self.assertIn('other_key = "value"', written_content)
        finally:
            os.unlink(temp_path)

    def test_already_ran_today_true(self) -> None:
        """Test detection when script already ran today."""
        # Save today's date to test config
        config = {"last_run_date": get_today_date()}
        save_execution_state(config, test_mode=True)

        self.assertTrue(already_ran_today(test_mode=True))

    def test_already_ran_today_false(self) -> None:
        """Test detection when script hasn't run today."""
        # Save yesterday's date to test config
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        config = {"last_run_date": yesterday}
        save_execution_state(config, test_mode=True)

        self.assertFalse(already_ran_today(test_mode=True))

    def test_already_ran_today_no_previous_run(self) -> None:
        """Test detection when script has never run."""
        # No config file exists (cleaned up in setUp)
        self.assertFalse(already_ran_today(test_mode=True))

    def test_update_execution_state(self) -> None:
        """Test updating execution state."""
        update_execution_state(test_mode=True)

        # Verify the state was saved
        self.assertTrue(already_ran_today(test_mode=True))

        # Verify the saved date is today
        config = load_execution_state(test_mode=True)
        self.assertEqual(config["last_run_date"], get_today_date())

    def test_colorize_text_with_color(self) -> None:
        """Test colorization when color is forced."""
        result = colorize_text("test message", "green", force_color=True)
        expected = "\033[92mtest message\033[0m"
        self.assertEqual(result, expected)

    def test_colorize_text_without_color(self) -> None:
        """Test colorization returns plain text when not forced and not TTY."""
        with patch("sys.stdout.isatty", return_value=False):
            result = colorize_text("test message", "green", force_color=False)
            self.assertEqual(result, "test message")

    def test_colorize_text_invalid_color(self) -> None:
        """Test colorization with invalid color returns plain text."""
        result = colorize_text("test message", "invalid", force_color=True)
        self.assertEqual(result, "test message")


if __name__ == "__main__":
    main()
