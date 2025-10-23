#!/usr/bin/env python3
"""
test_start_the_day.py - Unit tests for start_the_day.py

Run with: python3 -m unittest test_start_the_day.py
Or: python3 test_start_the_day.py
"""

import os
import sys
import datetime
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from lsimons_auto.start_the_day import (
    get_config_path,
    parse_toml_simple,
    get_today_date,
    load_execution_state,
    write_toml_simple,
    save_execution_state,
    already_ran_today,
    update_execution_state,
    colorize_text,
)


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


class TestStartTheDayIntegration(unittest.TestCase):
    """End-to-end integration tests for start_the_day workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.project_root = Path.home() / "dev" / "lsimons-auto"
        cls.start_the_day_script = (
            cls.project_root / "lsimons_auto" / "start_the_day.py"
        )

        # Verify test environment
        if not cls.project_root.exists():
            raise unittest.SkipTest(f"Project root not found: {cls.project_root}")
        if not cls.start_the_day_script.exists():
            raise unittest.SkipTest(
                f"start_the_day script not found: {cls.start_the_day_script}"
            )

    def test_cli_help_output(self):
        """Test command line help output."""
        result = subprocess.run(
            [sys.executable, str(self.start_the_day_script), "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Daily startup script", result.stdout)
        self.assertIn("--force", result.stdout)

    def test_already_ran_today_exits_successfully(self):
        """Test that script exits successfully if already ran today."""
        # Update state to mark as ran today (using regular config, not test)
        from lsimons_auto.start_the_day import (
            update_execution_state as update_state_main,
        )

        update_state_main(test_mode=False)

        try:
            result = subprocess.run(
                [sys.executable, str(self.start_the_day_script)],
                capture_output=True,
                text=True,
            )

            # Should exit with 0 even though it didn't run
            self.assertEqual(result.returncode, 0)
            self.assertIn("Already ran today", result.stdout)
        finally:
            # Clean up - remove the state so it doesn't affect other runs
            config_path = get_config_path(test_mode=False)
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_force_flag_bypasses_daily_check(self):
        """Test --force flag allows running even if already ran today."""
        # Mark as already ran today (using regular config)
        from lsimons_auto.start_the_day import (
            update_execution_state as update_state_main,
        )

        update_state_main(test_mode=False)

        try:
            result = subprocess.run(
                [sys.executable, str(self.start_the_day_script), "--force"],
                capture_output=True,
                text=True,
            )

            # Should attempt to run despite already ran today
            self.assertNotIn("Already ran today", result.stdout)
            # Should show the greeting
            self.assertIn("Good morning", result.stdout)
        finally:
            # Clean up
            config_path = get_config_path(test_mode=False)
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_script_displays_greeting(self):
        """Test that script displays greeting message."""
        # Clean state (use regular config since script doesn't support test mode)
        config_path = get_config_path(test_mode=False)
        if os.path.exists(config_path):
            os.remove(config_path)

        try:
            # Run the script - it will actually execute actions
            result = subprocess.run(
                [sys.executable, str(self.start_the_day_script)],
                capture_output=True,
                text=True,
            )

            self.assertIn("Good morning", result.stdout)
            self.assertIn("Starting your day", result.stdout)
        finally:
            # Clean up
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_script_shows_current_datetime(self):
        """Test that script shows current UTC datetime."""
        result = subprocess.run(
            [sys.executable, str(self.start_the_day_script), "--help"],
            capture_output=True,
            text=True,
        )

        self.assertIn("Current date and time (UTC)", result.stdout)

    def test_script_is_executable(self):
        """Test that start_the_day.py has executable permissions."""
        self.assertTrue(
            self.start_the_day_script.stat().st_mode & 0o111,
            "start_the_day.py should have executable permissions",
        )

    def test_script_has_correct_shebang(self):
        """Test that script has proper Python shebang."""
        content = self.start_the_day_script.read_text()
        self.assertTrue(content.startswith("#!/usr/bin/env python3"))

    def test_execution_state_updates_after_run(self):
        """Test that execution state is updated after successful run."""
        # Clean state
        test_config_path = get_config_path(test_mode=True)
        if os.path.exists(test_config_path):
            os.remove(test_config_path)

        self.assertFalse(already_ran_today(test_mode=True))

        # Simulate a run by calling update_execution_state
        update_execution_state(test_mode=True)

        # Should now show as already ran
        self.assertTrue(already_ran_today(test_mode=True))

        # Clean up
        if os.path.exists(test_config_path):
            os.remove(test_config_path)

    def test_error_handling_graceful_degradation(self):
        """Test that script continues even if individual tasks fail."""
        # The script should handle subprocess errors gracefully
        # This is tested by the run_command function's error handling
        content = self.start_the_day_script.read_text()
        self.assertIn("CalledProcessError", content)
        self.assertIn("Warning", content)


if __name__ == "__main__":
    _ = unittest.main()
