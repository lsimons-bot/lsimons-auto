"""Tests for lsimons_auto main dispatcher."""

import subprocess
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from lsimons_auto.lsimons_auto import discover_actions, main, normalize_action_name


class TestDiscoverActions:
    """Test action discovery."""

    def test_discover_actions_returns_dict(self) -> None:
        """Test that discover_actions returns a dictionary."""
        actions = discover_actions()
        assert isinstance(actions, dict)

    def test_discover_actions_finds_echo(self) -> None:
        """Test that echo action is discovered."""
        actions = discover_actions()
        assert "echo" in actions
        assert actions["echo"].name == "echo.py"

    def test_discover_actions_converts_underscores(self) -> None:
        """Test that underscores in filenames are converted to dashes."""
        actions = discover_actions()
        # git_sync.py should become git-sync
        assert "git-sync" in actions
        assert "git_sync" not in actions

    def test_discover_actions_excludes_init(self) -> None:
        """Test that __init__.py is excluded from actions."""
        actions = discover_actions()
        assert "__init__" not in actions


class TestNormalizeActionName:
    """Test action name normalization."""

    def test_normalize_with_dashes(self) -> None:
        """Test that dashes are preserved."""
        assert normalize_action_name("git-sync") == "git-sync"

    def test_normalize_with_underscores(self) -> None:
        """Test that underscores are converted to dashes."""
        assert normalize_action_name("git_sync") == "git-sync"

    def test_normalize_mixed(self) -> None:
        """Test normalization with mixed separators."""
        assert normalize_action_name("test_action-name") == "test-action-name"


class TestMainDispatcher:
    """Test main dispatcher function."""

    @patch("sys.argv", ["auto"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_no_action_shows_help(self, mock_stdout: StringIO) -> None:
        """Test that no action argument shows help."""
        main()
        output = mock_stdout.getvalue()
        assert "Available actions:" in output
        assert "echo" in output

    @patch("sys.argv", ["auto", "--help"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_help_flag(self, mock_stdout: StringIO) -> None:
        """Test --help flag shows help."""
        main()
        output = mock_stdout.getvalue()
        assert "Available actions:" in output

    @patch("sys.argv", ["auto", "-h"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_help_short_flag(self, mock_stdout: StringIO) -> None:
        """Test -h flag shows help."""
        main()
        output = mock_stdout.getvalue()
        assert "Available actions:" in output

    @patch("sys.argv", ["auto", "unknown-action"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_unknown_action(self, mock_stdout: StringIO) -> None:
        """Test unknown action prints error."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        output = mock_stdout.getvalue()
        assert "Error: Unknown action 'unknown-action'" in output

    @patch("sys.argv", ["auto", "echo", "test"])
    @patch("subprocess.run")
    def test_execute_action(self, mock_run: MagicMock) -> None:
        """Test that action is executed via subprocess."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "echo.py" in str(call_args)
        assert "test" in call_args

    @patch("sys.argv", ["auto", "echo", "message", "--upper"])
    @patch("subprocess.run")
    def test_execute_action_with_flags(self, mock_run: MagicMock) -> None:
        """Test that action is executed with flags."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        call_args = mock_run.call_args[0][0]
        assert "message" in call_args
        assert "--upper" in call_args

    @patch("sys.argv", ["auto", "git_sync"])
    @patch("subprocess.run")
    def test_underscore_action_name(self, mock_run: MagicMock) -> None:
        """Test that underscore in action name is normalized."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should work because git_sync is normalized to git-sync
        assert exc_info.value.code == 0
        assert mock_run.called

    @patch("sys.argv", ["auto", "echo"])
    @patch("subprocess.run")
    def test_action_non_zero_exit(self, mock_run: MagicMock) -> None:
        """Test that non-zero exit code is propagated."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=42)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 42

    @patch("sys.argv", ["auto", "echo"])
    @patch("subprocess.run")
    @patch("sys.stdout", new_callable=StringIO)
    def test_keyboard_interrupt(self, mock_stdout: StringIO, mock_run: MagicMock) -> None:
        """Test KeyboardInterrupt handling."""
        mock_run.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 130
        assert "Interrupted" in mock_stdout.getvalue()

    @patch("sys.argv", ["auto", "echo"])
    @patch("subprocess.run")
    @patch("sys.stdout", new_callable=StringIO)
    def test_file_not_found(self, mock_stdout: StringIO, mock_run: MagicMock) -> None:
        """Test FileNotFoundError handling."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        assert "Action script not found" in mock_stdout.getvalue()
