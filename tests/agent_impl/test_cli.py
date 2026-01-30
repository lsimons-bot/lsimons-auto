#!/usr/bin/env python3
"""
Tests for CLI argument parsing and subcommand handlers.

Tests the cli.py module functionality.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lsimons_auto.actions.agent_impl import cli, session


class TestArgparseSubcommands(unittest.TestCase):
    """Test argument parsing for subcommands."""

    def test_spawn_default_args(self) -> None:
        """Test spawn with minimal arguments."""
        parser = cli.create_parser()
        args = parser.parse_args(["spawn", "lsimons", "auto"])
        self.assertEqual(args.subcommand, "spawn")
        self.assertEqual(args.org, "lsimons")
        self.assertEqual(args.repo, "auto")
        self.assertEqual(args.subagents, 1)
        self.assertEqual(args.command, "claude")
        self.assertFalse(args.no_zed)
        self.assertFalse(args.no_attach)

    def test_spawn_with_all_options(self) -> None:
        """Test spawn with all options."""
        parser = cli.create_parser()
        args = parser.parse_args(
            ["spawn", "lsimons", "auto", "-n", "3", "-c", "pi", "--no-zed", "--no-attach"]
        )
        self.assertEqual(args.subagents, 3)
        self.assertEqual(args.command, "pi")
        self.assertTrue(args.no_zed)
        self.assertTrue(args.no_attach)

    def test_attach_subcommand(self) -> None:
        """Test attach subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["attach", "test-session"])
        self.assertEqual(args.subcommand, "attach")
        self.assertEqual(args.session, "test-session")

    def test_attach_default_session(self) -> None:
        """Test attach with default session (most recent)."""
        parser = cli.create_parser()
        args = parser.parse_args(["attach"])
        self.assertEqual(args.subcommand, "attach")
        self.assertIsNone(args.session)

    def test_send_subcommand(self) -> None:
        """Test send subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["send", "main", "hello", "world"])
        self.assertEqual(args.subcommand, "send")
        self.assertEqual(args.target, "main")
        self.assertEqual(args.text, ["hello", "world"])

    def test_broadcast_subcommand(self) -> None:
        """Test broadcast subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["broadcast", "test", "message", "--exclude-main"])
        self.assertEqual(args.subcommand, "broadcast")
        self.assertEqual(args.text, ["test", "message"])
        self.assertTrue(args.exclude_main)

    def test_focus_subcommand(self) -> None:
        """Test focus subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["focus", "left"])
        self.assertEqual(args.subcommand, "focus")
        self.assertEqual(args.target, "left")

    def test_list_subcommand(self) -> None:
        """Test list subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["list", "-v"])
        self.assertEqual(args.subcommand, "list")
        self.assertTrue(args.verbose)

    def test_close_subcommand(self) -> None:
        """Test close subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["close", "001", "-s", "test-session"])
        self.assertEqual(args.subcommand, "close")
        self.assertEqual(args.target, "001")
        self.assertEqual(args.session, "test-session")

    def test_kill_subcommand(self) -> None:
        """Test kill subcommand parsing."""
        parser = cli.create_parser()
        args = parser.parse_args(["kill", "test-session", "-f"])
        self.assertEqual(args.subcommand, "kill")
        self.assertEqual(args.session, "test-session")
        self.assertTrue(args.force)

    def test_subcommand_required(self) -> None:
        """Test that subcommand is required."""
        parser = cli.create_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])


class TestCLIHelp(unittest.TestCase):
    """Test CLI help output."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test environment."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.agent_script = cls.project_root / "lsimons_auto" / "actions" / "agent.py"

        if not cls.agent_script.exists():
            raise unittest.SkipTest(f"Agent script not found: {cls.agent_script}")

    def test_cli_main_help(self) -> None:
        """Test main help output."""
        result = subprocess.run(
            [sys.executable, str(self.agent_script), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("spawn", result.stdout)
        self.assertIn("attach", result.stdout)
        self.assertIn("send", result.stdout)
        self.assertIn("broadcast", result.stdout)
        self.assertIn("focus", result.stdout)
        self.assertIn("list", result.stdout)
        self.assertIn("close", result.stdout)
        self.assertIn("kill", result.stdout)

    def test_cli_spawn_help(self) -> None:
        """Test spawn subcommand help."""
        result = subprocess.run(
            [sys.executable, str(self.agent_script), "spawn", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--subagents", result.stdout)
        self.assertIn("--command", result.stdout)
        self.assertIn("--no-zed", result.stdout)
        self.assertIn("--no-attach", result.stdout)

    def test_cli_list_help(self) -> None:
        """Test list subcommand help."""
        result = subprocess.run(
            [sys.executable, str(self.agent_script), "list", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--verbose", result.stdout)


class TestCmdList(unittest.TestCase):
    """Test list command execution."""

    def test_cmd_list_empty(self) -> None:
        """Test list command with no sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                parser = cli.create_parser()
                args = parser.parse_args(["list"])
                # Should not raise
                cli.cmd_list(args)

    def test_cmd_list_with_sessions(self) -> None:
        """Test list command with sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)

            session_data: dict[str, object] = {
                "session_id": "test-session",
                "workspace_path": "/test/path",
                "repo_name": "test-repo",
                "org_name": "test-org",
                "created_at": "2026-01-21T00:00:00Z",
                "panes": [],
            }
            with open(sessions_dir / "test-session.json", "w") as f:
                json.dump(session_data, f)

            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                parser = cli.create_parser()
                args = parser.parse_args(["list", "-v"])
                # Should not raise
                cli.cmd_list(args)


if __name__ == "__main__":
    unittest.main()
