#!/usr/bin/env python3
"""
Integration tests for the actions submodule and command dispatcher.

These tests focus on end-to-end functionality without mocking, following
the testing strategy outlined in spec 002.
"""

import subprocess
import sys
import unittest
from pathlib import Path
import pytest


@pytest.mark.integration
class TestActionsIntegration(unittest.TestCase):
    """Integration tests for the actions system."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.project_root = Path.home() / "dev" / "lsimons-auto"
        cls.dispatcher_script = cls.project_root / "lsimons_auto" / "lsimons_auto.py"
        cls.echo_script = cls.project_root / "lsimons_auto" / "actions" / "echo.py"

        # Verify test environment
        if not cls.project_root.exists():
            raise unittest.SkipTest(f"Project root not found: {cls.project_root}")
        if not cls.dispatcher_script.exists():
            raise unittest.SkipTest(
                f"Dispatcher script not found: {cls.dispatcher_script}"
            )
        if not cls.echo_script.exists():
            raise unittest.SkipTest(f"Echo script not found: {cls.echo_script}")

    def run_command(
        self, cmd: list[str], expect_success: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run a command and return result with proper error handling."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if expect_success and result.returncode != 0:
                self.fail(
                    f"Command failed: {' '.join(cmd)}\n"
                    f"Exit code: {result.returncode}\n"
                    f"Stdout: {result.stdout}\n"
                    f"Stderr: {result.stderr}"
                )

            return result
        except Exception as e:
            self.fail(f"Failed to run command {' '.join(cmd)}: {e}")

    def test_dispatcher_help_shows_actions(self):
        """Test that dispatcher help shows available actions including echo."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "--help"]
        )

        self.assertIn("lsimons-auto command dispatcher", result.stdout)
        self.assertIn("Available actions:", result.stdout)
        self.assertIn("echo", result.stdout)
        self.assertIn("Use 'auto <action> --help'", result.stdout)

    def test_dispatcher_no_args_shows_help(self):
        """Test that dispatcher with no args shows help."""
        result = self.run_command([sys.executable, str(self.dispatcher_script)])

        self.assertIn("lsimons-auto command dispatcher", result.stdout)
        self.assertIn("Available actions:", result.stdout)
        self.assertIn("echo", result.stdout)

    def test_dispatcher_echo_action_help(self):
        """Test that dispatcher forwards help request to echo action."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "--help"]
        )

        self.assertIn("Echo a message", result.stdout)
        self.assertIn("--upper", result.stdout)
        self.assertIn("--prefix", result.stdout)

    def test_dispatcher_echo_basic_message(self):
        """Test dispatcher routes basic echo command correctly."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "hello", "world"]
        )

        self.assertEqual(result.stdout.strip(), "hello world")

    def test_dispatcher_echo_with_upper_flag(self):
        """Test dispatcher forwards flags correctly to echo action."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "--upper", "hello"]
        )

        self.assertEqual(result.stdout.strip(), "HELLO")

    def test_dispatcher_echo_with_prefix_flag(self):
        """Test dispatcher handles flag arguments correctly."""
        result = self.run_command(
            [
                sys.executable,
                str(self.dispatcher_script),
                "echo",
                "--prefix",
                "Test",
                "message",
            ]
        )

        self.assertEqual(result.stdout.strip(), "Test: message")

    def test_dispatcher_echo_combined_flags(self):
        """Test dispatcher handles multiple flags correctly."""
        result = self.run_command(
            [
                sys.executable,
                str(self.dispatcher_script),
                "echo",
                "--upper",
                "--prefix",
                "SUCCESS",
                "hello",
                "world",
            ]
        )

        self.assertEqual(result.stdout.strip(), "SUCCESS: HELLO WORLD")

    def test_dispatcher_invalid_action_error(self):
        """Test dispatcher handles invalid actions gracefully."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "nonexistent"],
            expect_success=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown action 'nonexistent'", result.stdout)
        self.assertIn("Available actions:", result.stdout)
        self.assertIn("echo", result.stdout)

    def test_dispatcher_forwards_unknown_flags_to_action(self):
        """Test that dispatcher forwards unknown flags to actions."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "--unknown-flag"],
            expect_success=False,
        )

        # Should fail with echo's error message, not dispatcher error
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --unknown-flag", result.stderr)

    def test_standalone_echo_basic_functionality(self):
        """Test echo action works when run standalone."""
        result = self.run_command(
            [sys.executable, str(self.echo_script), "standalone", "test"]
        )

        self.assertEqual(result.stdout.strip(), "standalone test")

    def test_standalone_echo_help(self):
        """Test echo action help when run standalone."""
        result = self.run_command([sys.executable, str(self.echo_script), "--help"])

        self.assertIn("Echo a message", result.stdout)
        self.assertIn("--upper", result.stdout)
        self.assertIn("--prefix", result.stdout)

    def test_standalone_echo_with_flags(self):
        """Test echo action flags when run standalone."""
        result = self.run_command(
            [
                sys.executable,
                str(self.echo_script),
                "--upper",
                "--prefix",
                "STANDALONE",
                "test",
            ]
        )

        self.assertEqual(result.stdout.strip(), "STANDALONE: TEST")

    def test_standalone_echo_default_message(self):
        """Test echo action default behavior when run standalone."""
        result = self.run_command([sys.executable, str(self.echo_script)])

        self.assertEqual(result.stdout.strip(), "Hello, World!")

    def test_echo_action_exit_codes(self):
        """Test that echo action returns proper exit codes."""
        # Successful execution should return 0
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "test"]
        )
        self.assertEqual(result.returncode, 0)

        # Invalid arguments should return non-zero
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "--invalid-flag"],
            expect_success=False,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_action_discovery_mechanism(self):
        """Test that action discovery finds echo action correctly."""
        # This tests the discovery indirectly by ensuring echo is available
        result = self.run_command([sys.executable, str(self.dispatcher_script)])

        self.assertIn("echo", result.stdout)
        # Should only show Python files, not __init__.py
        self.assertNotIn("__init__", result.stdout)

    def test_dispatcher_action_returns_nonzero_exit_code(self):
        """Test dispatcher preserves action exit codes."""
        # echo with invalid flag should return non-zero
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "echo", "--invalid-arg"],
            expect_success=False,
        )

        self.assertNotEqual(result.returncode, 0)
        # Dispatcher should forward the exit code from the action
        self.assertGreater(result.returncode, 0)

    def test_dispatcher_with_empty_action_name(self):
        """Test dispatcher handles edge case of empty action name."""
        # Passing just a space or empty string as action
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), ""],
            expect_success=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown action", result.stdout)

    def test_dispatcher_discovers_multiple_actions(self):
        """Test that dispatcher discovers all available actions."""
        result = self.run_command([sys.executable, str(self.dispatcher_script)])

        # Should discover multiple action files
        self.assertIn("echo", result.stdout)
        self.assertIn("organize_desktop", result.stdout)
        self.assertIn("update_desktop_background", result.stdout)
        self.assertIn("launch_apps", result.stdout)

    def test_dispatcher_handles_action_with_no_args(self):
        """Test dispatcher correctly handles action that expects arguments."""
        # organize-desktop should work without args (uses defaults)
        result = self.run_command(
            [
                sys.executable,
                str(self.dispatcher_script),
                "organize_desktop",
                "--dry-run",
            ]
        )

        self.assertEqual(result.returncode, 0)

    def test_dispatcher_unknown_action_shows_available_list(self):
        """Test that error for unknown action shows available actions."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "nonexistent_action"],
            expect_success=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown action 'nonexistent_action'", result.stdout)
        self.assertIn("Available actions:", result.stdout)
        # Should list actual available actions
        self.assertIn("echo", result.stdout)

    def test_dispatcher_case_sensitive_action_names(self):
        """Test that action names are case-sensitive."""
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "ECHO", "test"],
            expect_success=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown action", result.stdout)

    def test_dispatcher_action_with_dash_in_name(self):
        """Test actions with dashes (underscores in filename) work correctly."""
        # organize_desktop becomes organize-desktop (or use underscore)
        result = self.run_command(
            [sys.executable, str(self.dispatcher_script), "organize_desktop", "--help"]
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("organize", result.stdout.lower())


@pytest.mark.integration
class TestInstallation(unittest.TestCase):
    """Test installation functionality."""

    def test_echo_script_is_executable(self):
        """Test that echo script has executable permissions."""
        echo_script = (
            Path.home()
            / "dev"
            / "lsimons-auto"
            / "lsimons_auto"
            / "actions"
            / "echo.py"
        )

        if not echo_script.exists():
            self.skipTest(f"Echo script not found: {echo_script}")

        # Check if file has executable permissions
        self.assertTrue(
            echo_script.stat().st_mode & 0o111,
            "Echo script should have executable permissions",
        )

    def test_dispatcher_script_is_executable(self):
        """Test that dispatcher script has executable permissions."""
        dispatcher_script = (
            Path.home() / "dev" / "lsimons-auto" / "lsimons_auto" / "lsimons_auto.py"
        )

        if not dispatcher_script.exists():
            self.skipTest(f"Dispatcher script not found: {dispatcher_script}")

        # Check if file has executable permissions
        self.assertTrue(
            dispatcher_script.stat().st_mode & 0o111,
            "Dispatcher script should have executable permissions",
        )

    def test_auto_wrapper_script_exists(self):
        """Test that auto wrapper script exists in ~/.local/bin."""
        wrapper_path = Path.home() / ".local" / "bin" / "auto"

        # Skip if wrapper doesn't exist (installation may not have been run)
        if not wrapper_path.exists():
            self.skipTest("auto wrapper script not found - run install.py first")

        self.assertTrue(wrapper_path.is_file(), "auto should be a file")
        self.assertFalse(wrapper_path.is_symlink(), "auto should not be a symlink")

        # Verify it's executable
        self.assertTrue(
            wrapper_path.stat().st_mode & 0o111,
            "auto wrapper script should be executable",
        )

        # Verify it contains expected content
        content = wrapper_path.read_text()
        self.assertIn("#!/bin/bash", content, "Wrapper should be a bash script")
        self.assertIn(".venv/bin/python", content, "Wrapper should use venv Python")
        self.assertIn("lsimons_auto.py", content, "Wrapper should call lsimons_auto.py")

    def test_installed_command_works(self):
        """Test that installed auto command works globally."""
        wrapper_path = Path.home() / ".local" / "bin" / "auto"

        if not wrapper_path.exists():
            self.skipTest("auto wrapper script not found - run install.py first")

        # Test the installed command
        result = subprocess.run(
            [str(wrapper_path), "echo", "installation test"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            self.fail(
                f"Installed command failed:\n"
                f"Exit code: {result.returncode}\n"
                f"Stdout: {result.stdout}\n"
                f"Stderr: {result.stderr}"
            )

        self.assertEqual(result.stdout.strip(), "installation test")


if __name__ == "__main__":
    unittest.main()
