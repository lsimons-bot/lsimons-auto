#!/usr/bin/env python3
"""
Tests for the launch_apps action.

These tests focus on the launch_apps functionality including command line
interface and command execution logic.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from lsimons_auto.actions import launch_apps


class TestLaunchApps(unittest.TestCase):
    """Test cases for launch_apps action."""

    project_root: Path
    launch_apps_script: Path

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test environment."""
        cls.project_root = Path.home() / "dev" / "lsimons-auto"
        cls.launch_apps_script = cls.project_root / "lsimons_auto" / "actions" / "launch_apps.py"

        # Verify test environment
        if not cls.project_root.exists():
            raise unittest.SkipTest(f"Project root not found: {cls.project_root}")
        if not cls.launch_apps_script.exists():
            raise unittest.SkipTest(f"Launch apps script not found: {cls.launch_apps_script}")

    def test_launch_apps_cli_help(self) -> None:
        """Test command line interface help output."""
        result = subprocess.run(
            [sys.executable, str(self.launch_apps_script), "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Launch predefined applications and commands", result.stdout)
        self.assertIn("--list", result.stdout)

    def test_launch_apps_cli_list(self) -> None:
        """Test --list flag shows configured commands."""
        result = subprocess.run(
            [sys.executable, str(self.launch_apps_script), "--list"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Configured launch commands for host", result.stdout)
        self.assertIn("open -g -a /System/Applications/TextEdit.app ~/scratch.txt", result.stdout)

    @patch("lsimons_auto.actions.launch_apps.subprocess.Popen")
    def test_launch_command_success(self, mock_popen: MagicMock) -> None:
        """Test successful command launch."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = launch_apps.launch_command("test command")

        self.assertTrue(result)
        mock_popen.assert_called_once_with(
            "test command",
            shell=True,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("lsimons_auto.actions.launch_apps.subprocess.Popen")
    def test_launch_command_failure(self, mock_popen: MagicMock) -> None:
        """Test command launch failure handling."""
        mock_popen.side_effect = Exception("Command failed")

        result = launch_apps.launch_command("failing command")

        self.assertFalse(result)

    @patch("socket.gethostname")
    def test_get_launch_commands_paddo(self, mock_gethostname: MagicMock) -> None:
        """Test that paddo host gets reduced command set."""
        mock_gethostname.return_value = "paddo"

        commands = launch_apps.get_launch_commands()

        self.assertEqual(commands, launch_apps.PADDO_COMMANDS)
        self.assertEqual(len(commands), 4)

    @patch("socket.gethostname")
    def test_get_launch_commands_paddo_case_insensitive(self, mock_gethostname: MagicMock) -> None:
        """Test that hostname matching is case-insensitive."""
        mock_gethostname.return_value = "PADDO"

        commands = launch_apps.get_launch_commands()

        self.assertEqual(commands, launch_apps.PADDO_COMMANDS)

    @patch("socket.gethostname")
    def test_get_launch_commands_default(self, mock_gethostname: MagicMock) -> None:
        """Test that other hosts get full command set."""
        mock_gethostname.return_value = "otherhostname"

        commands = launch_apps.get_launch_commands()

        self.assertEqual(commands, launch_apps.DEFAULT_COMMANDS)
        self.assertGreater(len(commands), 4)

    @patch("lsimons_auto.actions.launch_apps.launch_command")
    @patch("lsimons_auto.actions.launch_apps.get_launch_commands")
    def test_launch_all_apps_success(
        self, mock_get_commands: MagicMock, mock_launch_command: MagicMock
    ) -> None:
        """Test launching all configured apps successfully."""
        mock_get_commands.return_value = launch_apps.DEFAULT_COMMANDS
        mock_launch_command.return_value = True

        # Redirect stdout to capture output
        with patch("sys.stdout"):
            launch_apps.launch_all_apps()

        # Verify launch_command was called for each configured command
        self.assertEqual(mock_launch_command.call_count, len(launch_apps.DEFAULT_COMMANDS))

    @patch("lsimons_auto.actions.launch_apps.launch_command")
    @patch("lsimons_auto.actions.launch_apps.get_launch_commands")
    def test_launch_all_apps_partial_failure(
        self, mock_get_commands: MagicMock, mock_launch_command: MagicMock
    ) -> None:
        """Test launching apps with some failures."""
        mock_get_commands.return_value = launch_apps.DEFAULT_COMMANDS
        # Create a side_effect list that matches the number of commands
        side_effects = [True, False] + [True] * (len(launch_apps.DEFAULT_COMMANDS) - 2)
        mock_launch_command.side_effect = side_effects

        # Redirect stdout to capture output
        with patch("sys.stdout"):
            launch_apps.launch_all_apps()

        # Verify launch_command was called for each configured command
        self.assertEqual(mock_launch_command.call_count, len(launch_apps.DEFAULT_COMMANDS))

    def test_main_with_list_argument(self) -> None:
        """Test main function with --list argument."""
        with patch("sys.stdout") as mock_stdout:
            launch_apps.main(["--list"])

        # Verify output was printed (we can't easily check exact content due to mocking)
        mock_stdout.write.assert_called()

    @patch("lsimons_auto.actions.launch_apps.launch_all_apps")
    def test_main_launches_apps(self, mock_launch_all_apps: MagicMock) -> None:
        """Test main function launches apps by default."""
        launch_apps.main([])

        mock_launch_all_apps.assert_called_once()

    def test_launch_commands_configured(self) -> None:
        """Test that command sets are properly configured."""
        self.assertGreater(len(launch_apps.DEFAULT_COMMANDS), 0)
        self.assertEqual(len(launch_apps.PADDO_COMMANDS), 4)
        self.assertIn(
            "open -g -a /System/Applications/TextEdit.app ~/scratch.txt",
            launch_apps.DEFAULT_COMMANDS[0],
        )
        self.assertIn(
            "open -g -a /System/Applications/TextEdit.app ~/scratch.txt",
            launch_apps.PADDO_COMMANDS[0],
        )
        # Verify PADDO_COMMANDS contains the expected apps
        paddo_commands_str = " ".join(launch_apps.PADDO_COMMANDS)
        self.assertIn("TextEdit", paddo_commands_str)
        self.assertIn("Ghostty", paddo_commands_str)
        self.assertIn("Zed", paddo_commands_str)
        self.assertIn("IntelliJ IDEA", paddo_commands_str)


if __name__ == "__main__":
    unittest.main()
