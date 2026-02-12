"""Tests for lsimons_auto.actions.git_sync module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lsimons_auto.actions.git_sync import (
    BotRemoteContext,
    ForkContext,
    OwnerConfig,
    build_bot_remote_context,
    build_fork_context,
    configure_bot_remote,
    get_authenticated_user,
    get_command_output,
    get_repos,
    get_user_forks,
    run_command,
    try_fast_forward,
)


class TestOwnerConfig:
    """Test OwnerConfig NamedTuple."""

    def test_owner_config_defaults(self) -> None:
        """Test OwnerConfig with default values."""
        config = OwnerConfig(name="test-owner")
        assert config.name == "test-owner"
        assert config.local_dir is None
        assert config.allow_archived is True
        assert config.hostname_filter is None

    def test_owner_config_custom_values(self) -> None:
        """Test OwnerConfig with custom values."""
        config = OwnerConfig(
            name="test-owner",
            local_dir="custom-dir",
            allow_archived=False,
            hostname_filter="myhost",
        )
        assert config.name == "test-owner"
        assert config.local_dir == "custom-dir"
        assert config.allow_archived is False
        assert config.hostname_filter == "myhost"


class TestForkContext:
    """Test ForkContext NamedTuple."""

    def test_fork_context_creation(self) -> None:
        """Test ForkContext creation."""
        fork_map = {"owner/repo": "https://github.com/user/repo"}
        context = ForkContext(username="testuser", fork_map=fork_map)
        assert context.username == "testuser"
        assert context.fork_map == fork_map


class TestBotRemoteContext:
    """Test BotRemoteContext NamedTuple."""

    def test_bot_remote_context_creation(self) -> None:
        """Test BotRemoteContext creation."""
        bot_fork_map = {"owner/repo": "https://github.com/bot/repo"}
        context = BotRemoteContext(bot_fork_map=bot_fork_map)
        assert context.bot_fork_map == bot_fork_map


class TestGetCommandOutput:
    """Test get_command_output function."""

    @patch("subprocess.run")
    def test_get_command_output_success(self, mock_run: MagicMock) -> None:
        """Test successful command execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="test output\n", stderr=""
        )

        result = get_command_output(["echo", "test"])
        assert result == "test output"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_command_output_failure(self, mock_run: MagicMock) -> None:
        """Test failed command execution returns None."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["false"])

        result = get_command_output(["false"])
        assert result is None

    @patch("subprocess.run")
    def test_get_command_output_with_cwd(self, mock_run: MagicMock) -> None:
        """Test command execution with working directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="output", stderr=""
        )
        test_path = Path("/tmp/test")

        get_command_output(["pwd"], cwd=test_path)
        assert mock_run.call_args[1]["cwd"] == test_path


class TestTryFastForward:
    """Test try_fast_forward function."""

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    def test_try_fast_forward_not_on_main(self, mock_get_output: MagicMock) -> None:
        """Test fast-forward fails when not on main branch."""
        mock_get_output.return_value = "feature-branch"

        result = try_fast_forward(Path("/tmp/repo"))
        assert result is False

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    def test_try_fast_forward_dirty_working_copy(self, mock_get_output: MagicMock) -> None:
        """Test fast-forward fails when working copy is dirty."""
        mock_get_output.side_effect = ["main", "M somefile.txt"]

        result = try_fast_forward(Path("/tmp/repo"))
        assert result is False

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("lsimons_auto.actions.git_sync.get_command_output")
    def test_try_fast_forward_already_up_to_date(
        self, mock_get_output: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test fast-forward when already up to date."""
        mock_get_output.side_effect = [
            "main",  # current branch
            "",  # clean working copy
            "abc123",  # local hash
            "abc123",  # remote hash (same)
        ]

        result = try_fast_forward(Path("/tmp/repo"))
        assert result is False
        mock_run_cmd.assert_not_called()

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("lsimons_auto.actions.git_sync.get_command_output")
    def test_try_fast_forward_diverged(
        self, mock_get_output: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test fast-forward fails when branches have diverged."""
        mock_get_output.side_effect = [
            "main",  # current branch
            "",  # clean working copy
            "abc123",  # local hash
            "def456",  # remote hash
            "xyz789",  # merge base (not equal to local)
        ]

        result = try_fast_forward(Path("/tmp/repo"))
        assert result is False
        mock_run_cmd.assert_not_called()

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("lsimons_auto.actions.git_sync.get_command_output")
    def test_try_fast_forward_success_dry_run(
        self, mock_get_output: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test fast-forward in dry-run mode."""
        mock_get_output.side_effect = [
            "main",  # current branch
            "",  # clean working copy
            "abc123",  # local hash
            "def456",  # remote hash
            "abc123",  # merge base (equal to local, can fast-forward)
        ]

        result = try_fast_forward(Path("/tmp/repo"), dry_run=True)
        assert result is True
        mock_run_cmd.assert_not_called()

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("lsimons_auto.actions.git_sync.get_command_output")
    def test_try_fast_forward_success(
        self, mock_get_output: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test successful fast-forward."""
        mock_get_output.side_effect = [
            "main",  # current branch
            "",  # clean working copy
            "abc123",  # local hash
            "def456",  # remote hash
            "abc123",  # merge base (equal to local, can fast-forward)
        ]
        mock_run_cmd.return_value = True

        result = try_fast_forward(Path("/tmp/repo"), dry_run=False)
        assert result is True
        mock_run_cmd.assert_called_once()


class TestRunCommand:
    """Test run_command function."""

    @patch("subprocess.run")
    def test_run_command_success(self, mock_run: MagicMock) -> None:
        """Test successful command execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        result = run_command(["echo", "test"])
        assert result is True

    @patch("subprocess.run")
    def test_run_command_failure(self, mock_run: MagicMock) -> None:
        """Test failed command execution."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["false"], output="error output")

        result = run_command(["false"])
        assert result is False

    @patch("subprocess.run")
    def test_run_command_with_cwd(self, mock_run: MagicMock) -> None:
        """Test command with working directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        test_path = Path("/tmp/test")

        run_command(["pwd"], cwd=test_path)
        assert mock_run.call_args[1]["cwd"] == test_path


class TestGetRepos:
    """Test get_repos function."""

    @patch("subprocess.run")
    def test_get_repos_success(self, mock_run: MagicMock) -> None:
        """Test successful repository fetching."""
        repos_data = [
            {"name": "repo1", "isFork": False, "isArchived": False},
            {"name": "repo2", "isFork": True, "isArchived": False},
            {"name": "repo3", "isFork": False, "isArchived": True},
            {"name": "repo4", "isFork": False, "isArchived": False},
        ]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(repos_data), stderr=""
        )

        result = get_repos("testowner")
        assert "repo1" in result
        assert "repo4" in result
        assert "repo2" not in result  # Fork excluded
        assert "repo3" not in result  # Archived excluded

    @patch("subprocess.run")
    def test_get_repos_archived(self, mock_run: MagicMock) -> None:
        """Test fetching archived repositories."""
        repos_data = [
            {"name": "repo1", "isFork": False, "isArchived": False},
            {"name": "repo3", "isFork": False, "isArchived": True},
        ]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(repos_data), stderr=""
        )

        result = get_repos("testowner", archive=True)
        assert "repo3" in result
        assert "repo1" not in result

    @patch("subprocess.run")
    def test_get_repos_gh_not_found(self, mock_run: MagicMock) -> None:
        """Test error handling when gh CLI not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(SystemExit) as exc_info:
            get_repos("testowner")
        assert exc_info.value.code == 1

    @patch("subprocess.run")
    def test_get_repos_command_error(self, mock_run: MagicMock) -> None:
        """Test error handling when gh command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["gh"], stderr="error")

        with pytest.raises(SystemExit) as exc_info:
            get_repos("testowner")
        assert exc_info.value.code == 1

    @patch("subprocess.run")
    def test_get_repos_json_error(self, mock_run: MagicMock) -> None:
        """Test error handling when JSON parsing fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="invalid json", stderr=""
        )

        with pytest.raises(SystemExit) as exc_info:
            get_repos("testowner")
        assert exc_info.value.code == 1


class TestGetAuthenticatedUser:
    """Test get_authenticated_user function."""

    @patch("subprocess.run")
    def test_get_authenticated_user_success(self, mock_run: MagicMock) -> None:
        """Test successful user authentication."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="testuser\n", stderr=""
        )

        result = get_authenticated_user()
        assert result == "testuser"

    @patch("subprocess.run")
    def test_get_authenticated_user_failure(self, mock_run: MagicMock) -> None:
        """Test failed authentication."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["gh"])

        result = get_authenticated_user()
        assert result is None

    @patch("subprocess.run")
    def test_get_authenticated_user_gh_not_found(self, mock_run: MagicMock) -> None:
        """Test when gh CLI not found."""
        mock_run.side_effect = FileNotFoundError()

        result = get_authenticated_user()
        assert result is None


class TestGetUserForks:
    """Test get_user_forks function."""

    @patch("subprocess.run")
    def test_get_user_forks_success(self, mock_run: MagicMock) -> None:
        """Test successful fork fetching."""
        forks_data = [
            {
                "name": "forked-repo",
                "url": "https://github.com/user/forked-repo",
                "parent": {
                    "name": "original-repo",
                    "owner": {"login": "original-owner"},
                },
            }
        ]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(forks_data), stderr=""
        )

        result = get_user_forks("testuser")
        assert "original-owner/original-repo" in result
        assert result["original-owner/original-repo"] == "https://github.com/user/forked-repo"

    @patch("subprocess.run")
    def test_get_user_forks_empty(self, mock_run: MagicMock) -> None:
        """Test when user has no forks."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="[]", stderr=""
        )

        result = get_user_forks("testuser")
        assert result == {}

    @patch("subprocess.run")
    def test_get_user_forks_command_error(self, mock_run: MagicMock) -> None:
        """Test error handling when command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["gh"])

        result = get_user_forks("testuser")
        assert result == {}

    @patch("subprocess.run")
    def test_get_user_forks_json_error(self, mock_run: MagicMock) -> None:
        """Test error handling when JSON parsing fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="invalid", stderr=""
        )

        result = get_user_forks("testuser")
        assert result == {}


class TestBuildForkContext:
    """Test build_fork_context function."""

    @patch("lsimons_auto.actions.git_sync.get_user_forks")
    @patch("lsimons_auto.actions.git_sync.get_authenticated_user")
    def test_build_fork_context_bot_user(
        self, mock_get_user: MagicMock, mock_get_forks: MagicMock
    ) -> None:
        """Test building fork context for lsimons-bot."""
        mock_get_user.return_value = "lsimons-bot"
        mock_get_forks.return_value = {"owner/repo": "https://github.com/bot/repo"}

        result = build_fork_context()
        assert result is not None
        assert result.username == "lsimons-bot"
        assert len(result.fork_map) == 1

    @patch("lsimons_auto.actions.git_sync.get_authenticated_user")
    def test_build_fork_context_not_bot(self, mock_get_user: MagicMock) -> None:
        """Test building fork context for non-bot user."""
        mock_get_user.return_value = "regularuser"

        result = build_fork_context()
        assert result is None

    @patch("lsimons_auto.actions.git_sync.get_authenticated_user")
    def test_build_fork_context_no_user(self, mock_get_user: MagicMock) -> None:
        """Test building fork context when not authenticated."""
        mock_get_user.return_value = None

        result = build_fork_context()
        assert result is None


class TestBuildBotRemoteContext:
    """Test build_bot_remote_context function."""

    @patch("lsimons_auto.actions.git_sync.get_user_forks")
    @patch("lsimons_auto.actions.git_sync.get_authenticated_user")
    def test_build_bot_remote_context_regular_user(
        self, mock_get_user: MagicMock, mock_get_forks: MagicMock
    ) -> None:
        """Test building bot remote context for regular user."""
        mock_get_user.return_value = "regularuser"
        mock_get_forks.return_value = {"owner/repo": "https://github.com/bot/repo"}

        result = build_bot_remote_context()
        assert result is not None
        assert len(result.bot_fork_map) == 1

    @patch("lsimons_auto.actions.git_sync.get_authenticated_user")
    def test_build_bot_remote_context_bot_user(self, mock_get_user: MagicMock) -> None:
        """Test building bot remote context for bot user."""
        mock_get_user.return_value = "lsimons-bot"

        result = build_bot_remote_context()
        assert result is None

    @patch("lsimons_auto.actions.git_sync.get_authenticated_user")
    def test_build_bot_remote_context_no_user(self, mock_get_user: MagicMock) -> None:
        """Test building bot remote context when not authenticated."""
        mock_get_user.return_value = None

        result = build_bot_remote_context()
        assert result is None


class TestConfigureBotRemote:
    """Test configure_bot_remote function."""

    def test_configure_bot_remote_dry_run(self) -> None:
        """Test configuring bot remote in dry-run mode."""
        result = configure_bot_remote(
            Path("/tmp/repo"), "https://github.com/bot/repo", dry_run=True
        )
        assert result is True

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("subprocess.run")
    def test_configure_bot_remote_add_new(
        self, mock_run: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test adding new bot remote."""
        # First call: get remotes
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="origin\n", stderr=""
        )
        mock_run_cmd.return_value = True

        result = configure_bot_remote(
            Path("/tmp/repo"), "https://github.com/bot/repo", dry_run=False
        )
        assert result is True
        # Should be called twice: once to add remote, once to fetch
        assert mock_run_cmd.call_count == 2

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("subprocess.run")
    def test_configure_bot_remote_update_existing(
        self, mock_run: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test updating existing bot remote with different URL."""
        # Call sequence: get remotes, get current URL
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="origin\nbot\n", stderr=""),
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="https://github.com/old/repo\n", stderr=""
            ),
        ]
        mock_run_cmd.return_value = True

        result = configure_bot_remote(
            Path("/tmp/repo"), "https://github.com/bot/repo", dry_run=False
        )
        assert result is True
        # Should be called twice: once to update URL, once to fetch
        assert mock_run_cmd.call_count == 2

    @patch("lsimons_auto.actions.git_sync.run_command")
    @patch("subprocess.run")
    def test_configure_bot_remote_already_configured(
        self, mock_run: MagicMock, mock_run_cmd: MagicMock
    ) -> None:
        """Test when bot remote already points to correct URL."""
        # Call sequence: get remotes, get current URL
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="origin\nbot\n", stderr=""),
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="https://github.com/bot/repo\n", stderr=""
            ),
        ]
        mock_run_cmd.return_value = True

        result = configure_bot_remote(
            Path("/tmp/repo"), "https://github.com/bot/repo", dry_run=False
        )
        assert result is True
        # Should be called once to fetch (no add/update needed)
        mock_run_cmd.assert_called_once()
