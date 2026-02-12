"""Tests for lsimons_auto.utils module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from lsimons_auto.utils import handle_error, run_command


class TestHandleError:
    """Test error handling utility."""

    def test_handle_error_exits_with_code(self) -> None:
        """Test that handle_error exits with correct code."""
        with pytest.raises(SystemExit) as exc_info:
            handle_error("Test error", ValueError("test"), exit_code=42)
        assert exc_info.value.code == 42

    def test_handle_error_default_exit_code(self) -> None:
        """Test that handle_error uses default exit code 1."""
        with pytest.raises(SystemExit) as exc_info:
            handle_error("Test error", RuntimeError("test"))
        assert exc_info.value.code == 1


class TestRunCommand:
    """Test subprocess command utility."""

    @patch("subprocess.run")
    def test_run_command_success(self, mock_run: MagicMock) -> None:
        """Test successful command execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "hello"], returncode=0, stdout="hello\n", stderr=""
        )

        result = run_command(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout == "hello\n"

    @patch("subprocess.run")
    def test_run_command_failure_with_check(self, mock_run: MagicMock) -> None:
        """Test that command failure with check=True exits."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"], returncode=1, stdout="", stderr="error"
        )

        with pytest.raises(SystemExit) as exc_info:
            run_command(["false"], check=True)
        assert exc_info.value.code == 1

    @patch("subprocess.run")
    def test_run_command_failure_without_check(self, mock_run: MagicMock) -> None:
        """Test that command failure with check=False returns result."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"], returncode=1, stdout="", stderr="error"
        )

        result = run_command(["false"], check=False)
        assert result.returncode == 1

    @patch("subprocess.run")
    def test_run_command_custom_error_message(self, mock_run: MagicMock) -> None:
        """Test custom error message is used."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["cmd"], returncode=1, stdout="", stderr="stderr"
        )

        with pytest.raises(SystemExit):
            run_command(["cmd"], error_message="Custom error")

    @patch("subprocess.run")
    def test_run_command_without_capture(self, mock_run: MagicMock) -> None:
        """Test command without output capture."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "test"], returncode=0
        )

        result = run_command(["echo", "test"], capture_output=False)
        assert result.returncode == 0
