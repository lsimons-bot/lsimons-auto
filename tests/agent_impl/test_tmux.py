#!/usr/bin/env python3
"""
Tests for tmux terminal control functions.

Tests the tmux.py module functionality. tmux commands are mocked.
"""

import subprocess
import unittest
from unittest.mock import Mock, patch

from lsimons_auto.actions.agent_impl import tmux


class TestTmuxHelpers(unittest.TestCase):
    """Test tmux helper functions."""

    @patch.object(tmux.subprocess, "run")
    def test_run_tmux_success(self, mock_run: Mock) -> None:
        """Test successful tmux command execution."""
        mock_run.return_value = Mock(stdout="output\n", stderr="")

        result = tmux.run_tmux("list-sessions")

        self.assertEqual(result, "output")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "tmux")
        self.assertEqual(args[1], "list-sessions")

    @patch.object(tmux.subprocess, "run")
    def test_run_tmux_failure(self, mock_run: Mock) -> None:
        """Test tmux command failure handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["tmux"], stderr="Error message"
        )

        with self.assertRaises(RuntimeError) as cm:
            tmux.run_tmux("invalid-command")
        self.assertIn("tmux command failed", str(cm.exception))

    @patch.object(tmux.subprocess, "run")
    def test_run_tmux_not_found(self, mock_run: Mock) -> None:
        """Test handling when tmux is not found."""
        mock_run.side_effect = FileNotFoundError()

        with self.assertRaises(RuntimeError) as cm:
            tmux.run_tmux("any-command")
        self.assertIn("tmux not found", str(cm.exception))

    @patch.object(tmux, "run_tmux")
    def test_session_exists_true(self, mock_run: Mock) -> None:
        """Test session_exists returns True when session exists."""
        mock_run.return_value = ""

        result = tmux.session_exists("test-session")

        self.assertTrue(result)
        mock_run.assert_called_once_with("has-session", "-t", "test-session", check=True)

    @patch.object(tmux, "run_tmux")
    def test_session_exists_false(self, mock_run: Mock) -> None:
        """Test session_exists returns False when session doesn't exist."""
        mock_run.side_effect = RuntimeError("session not found")

        result = tmux.session_exists("nonexistent")

        self.assertFalse(result)

    @patch.object(tmux, "run_tmux")
    def test_send_keys_with_enter(self, mock_run: Mock) -> None:
        """Test send_keys with Enter key."""
        mock_run.return_value = ""

        tmux.send_keys("%0", "ls -la", enter=True)

        mock_run.assert_called_once_with("send-keys", "-t", "%0", "ls -la", "Enter")

    @patch.object(tmux, "run_tmux")
    def test_send_keys_without_enter(self, mock_run: Mock) -> None:
        """Test send_keys without Enter key."""
        mock_run.return_value = ""

        tmux.send_keys("%0", "partial text", enter=False)

        mock_run.assert_called_once_with("send-keys", "-t", "%0", "partial text")

    @patch.object(tmux, "run_tmux")
    def test_select_pane(self, mock_run: Mock) -> None:
        """Test select_pane focuses the correct pane."""
        mock_run.return_value = ""

        tmux.select_pane("%1")

        mock_run.assert_called_once_with("select-pane", "-t", "%1")

    @patch.object(tmux, "run_tmux")
    def test_kill_pane(self, mock_run: Mock) -> None:
        """Test kill_pane closes the correct pane."""
        mock_run.return_value = ""

        tmux.kill_pane("%2")

        mock_run.assert_called_once_with("kill-pane", "-t", "%2")

    @patch.object(tmux, "run_tmux")
    def test_kill_session(self, mock_run: Mock) -> None:
        """Test kill_session terminates the session."""
        mock_run.return_value = ""

        tmux.kill_session("test-session")

        mock_run.assert_called_once_with("kill-session", "-t", "test-session")

    @patch.object(tmux, "run_tmux")
    def test_list_panes(self, mock_run: Mock) -> None:
        """Test list_panes returns pane IDs."""
        mock_run.return_value = "%0\n%1\n%2"

        result = tmux.list_panes("test-session")

        self.assertEqual(result, ["%0", "%1", "%2"])
        mock_run.assert_called_once_with(
            "list-panes", "-t", "test-session", "-F", "#{pane_id}"
        )

    @patch.object(tmux, "run_tmux")
    def test_list_panes_empty(self, mock_run: Mock) -> None:
        """Test list_panes with empty session."""
        mock_run.return_value = ""

        result = tmux.list_panes("empty-session")

        self.assertEqual(result, [])

    @patch.object(tmux, "run_tmux")
    def test_focus_pane_direction(self, mock_run: Mock) -> None:
        """Test focus_pane_direction with different directions."""
        mock_run.return_value = ""

        tmux.focus_pane_direction("test-session", "left")
        mock_run.assert_called_with("select-pane", "-t", "test-session", "-L")

        tmux.focus_pane_direction("test-session", "right")
        mock_run.assert_called_with("select-pane", "-t", "test-session", "-R")

        tmux.focus_pane_direction("test-session", "up")
        mock_run.assert_called_with("select-pane", "-t", "test-session", "-U")

        tmux.focus_pane_direction("test-session", "down")
        mock_run.assert_called_with("select-pane", "-t", "test-session", "-D")

    def test_is_inside_tmux_false(self) -> None:
        """Test is_inside_tmux when not in tmux."""
        with patch.dict("os.environ", {}, clear=True):
            result = tmux.is_inside_tmux()
            self.assertFalse(result)

    def test_is_inside_tmux_true(self) -> None:
        """Test is_inside_tmux when inside tmux."""
        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            result = tmux.is_inside_tmux()
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
