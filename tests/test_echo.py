"""Tests for lsimons_auto.actions.echo module."""

from io import StringIO
from unittest.mock import patch

from lsimons_auto.actions.echo import main


class TestEcho:
    """Test echo action."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_default_message(self, mock_stdout: StringIO) -> None:
        """Test echo with no arguments prints default message."""
        main([])
        assert mock_stdout.getvalue().strip() == "Hello, World!"

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_custom_message(self, mock_stdout: StringIO) -> None:
        """Test echo with custom message."""
        main(["Hello", "there"])
        assert mock_stdout.getvalue().strip() == "Hello there"

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_with_upper(self, mock_stdout: StringIO) -> None:
        """Test echo with uppercase flag."""
        main(["hello", "world", "--upper"])
        assert mock_stdout.getvalue().strip() == "HELLO WORLD"

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_with_prefix(self, mock_stdout: StringIO) -> None:
        """Test echo with prefix."""
        main(["world", "--prefix", "Hello"])
        assert mock_stdout.getvalue().strip() == "Hello: world"

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_with_prefix_and_upper(self, mock_stdout: StringIO) -> None:
        """Test echo with both prefix and uppercase."""
        main(["test", "--prefix", "Info", "--upper"])
        assert mock_stdout.getvalue().strip() == "Info: TEST"

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_single_word(self, mock_stdout: StringIO) -> None:
        """Test echo with single word."""
        main(["test"])
        assert mock_stdout.getvalue().strip() == "test"

    @patch("sys.stdout", new_callable=StringIO)
    def test_echo_default_with_upper(self, mock_stdout: StringIO) -> None:
        """Test default message with uppercase."""
        main(["--upper"])
        assert mock_stdout.getvalue().strip() == "HELLO, WORLD!"
