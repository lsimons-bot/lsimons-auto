#!/usr/bin/env python3
"""
Tests for session management.

Tests the session.py module functionality including AgentPane, AgentSession,
session persistence, and pane finding.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lsimons_auto.actions.agent_manager_impl import session


class TestSessionManagement(unittest.TestCase):
    """Test session state persistence."""

    def test_session_save_and_load(self) -> None:
        """Test session round-trip through disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                test_session = session.AgentSession(
                    session_id="test-session",
                    workspace_path="/test/path",
                    repo_name="test-repo",
                    org_name="test-org",
                    created_at="2026-01-21T00:00:00Z",
                    panes=[
                        session.AgentPane(
                            id="M-test",
                            pane_index=0,
                            command="claude",
                            is_main=True,
                        )
                    ],
                )
                test_session.save()

                loaded = session.AgentSession.load("test-session")

                self.assertEqual(loaded.session_id, test_session.session_id)
                self.assertEqual(loaded.workspace_path, test_session.workspace_path)
                self.assertEqual(len(loaded.panes), 1)
                self.assertEqual(loaded.panes[0].id, "M-test")

    def test_session_delete(self) -> None:
        """Test session deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                test_session = session.AgentSession(
                    session_id="test-session",
                    workspace_path="/test/path",
                    repo_name="test-repo",
                    org_name="test-org",
                    created_at="2026-01-21T00:00:00Z",
                )
                test_session.save()

                session_file = sessions_dir / "test-session.json"
                self.assertTrue(session_file.exists())

                test_session.delete()

                self.assertFalse(session_file.exists())

    def test_session_load_not_found(self) -> None:
        """Test loading nonexistent session raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)
            with (
                patch.object(session, "SESSIONS_DIR", sessions_dir),
                self.assertRaises(FileNotFoundError),
            ):
                session.AgentSession.load("nonexistent")


class TestListSessions(unittest.TestCase):
    """Test session listing functionality."""

    def test_list_sessions_empty(self) -> None:
        """Test listing sessions when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                sessions = session.list_sessions()
                self.assertEqual(sessions, [])

    def test_list_sessions_finds_all(self) -> None:
        """Test listing sessions finds all valid sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)

            # Create test sessions
            for i in range(3):
                session_data: dict[str, object] = {
                    "session_id": f"test-session-{i}",
                    "workspace_path": "/test/path",
                    "repo_name": "test-repo",
                    "org_name": "test-org",
                    "created_at": f"2026-01-21T0{i}:00:00Z",
                    "panes": [],
                }
                with open(sessions_dir / f"test-session-{i}.json", "w") as f:
                    json.dump(session_data, f)

            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                sessions_list = session.list_sessions()
                self.assertEqual(len(sessions_list), 3)

    def test_get_most_recent_session(self) -> None:
        """Test getting most recent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)

            # Create test sessions
            for i in range(3):
                session_data: dict[str, object] = {
                    "session_id": f"test-session-{i}",
                    "workspace_path": "/test/path",
                    "repo_name": "test-repo",
                    "org_name": "test-org",
                    "created_at": f"2026-01-21T0{i}:00:00Z",
                    "panes": [],
                }
                with open(sessions_dir / f"test-session-{i}.json", "w") as f:
                    json.dump(session_data, f)

            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                recent = session.get_most_recent_session()
                self.assertIsNotNone(recent)

    def test_get_most_recent_session_none(self) -> None:
        """Test getting most recent session when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                recent = session.get_most_recent_session()
                self.assertIsNone(recent)


class TestFindPaneByTarget(unittest.TestCase):
    """Test pane finding functionality."""

    def setUp(self) -> None:
        """Set up test session."""
        self.test_session = session.AgentSession(
            session_id="test",
            workspace_path="/test",
            repo_name="repo",
            org_name="org",
            created_at="2026-01-21T00:00:00Z",
            panes=[
                session.AgentPane("M-repo", 0, "claude", True),
                session.AgentPane("001-repo", 1, "claude", False),
                session.AgentPane("002-repo", 2, "claude", False),
            ],
        )

    def test_find_by_main_keyword(self) -> None:
        """Test finding main pane by 'main' keyword."""
        result = session.find_pane_by_target(self.test_session, "main")
        assert result is not None
        pane, idx = result
        self.assertEqual(pane.id, "M-repo")
        self.assertEqual(idx, 0)

    def test_find_by_index(self) -> None:
        """Test finding pane by numeric index."""
        result = session.find_pane_by_target(self.test_session, "1")
        assert result is not None
        pane, idx = result
        self.assertEqual(pane.id, "001-repo")
        self.assertEqual(idx, 1)

    def test_find_by_id_partial(self) -> None:
        """Test finding pane by partial ID."""
        result = session.find_pane_by_target(self.test_session, "002")
        assert result is not None
        pane, _ = result
        self.assertEqual(pane.id, "002-repo")

    def test_find_not_found(self) -> None:
        """Test finding nonexistent pane returns None."""
        result = session.find_pane_by_target(self.test_session, "999")
        self.assertIsNone(result)


class TestAgentPaneWorktreePath(unittest.TestCase):
    """Test AgentPane worktree_path field."""

    def test_agent_pane_with_worktree_path(self) -> None:
        """Test AgentPane can store worktree path."""
        pane = session.AgentPane(
            id="M-test",
            pane_index=0,
            command="claude",
            is_main=True,
            worktree_path="/path/to/worktree",
        )
        self.assertEqual(pane.worktree_path, "/path/to/worktree")

    def test_agent_pane_worktree_path_default_none(self) -> None:
        """Test AgentPane worktree_path defaults to None."""
        pane = session.AgentPane(
            id="M-test",
            pane_index=0,
            command="claude",
            is_main=True,
        )
        self.assertIsNone(pane.worktree_path)

    def test_session_save_load_with_worktree_path(self) -> None:
        """Test session save/load preserves worktree paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(session, "SESSIONS_DIR", sessions_dir):
                test_session = session.AgentSession(
                    session_id="test-session",
                    workspace_path="/test/path",
                    repo_name="test-repo",
                    org_name="test-org",
                    created_at="2026-01-21T00:00:00Z",
                    panes=[
                        session.AgentPane(
                            id="M-test",
                            pane_index=0,
                            command="claude",
                            is_main=True,
                            worktree_path="/worktrees/M",
                        ),
                        session.AgentPane(
                            id="001-test",
                            pane_index=1,
                            command="claude",
                            is_main=False,
                            worktree_path="/worktrees/001",
                        ),
                    ],
                )
                test_session.save()

                loaded = session.AgentSession.load("test-session")

                self.assertEqual(len(loaded.panes), 2)
                self.assertEqual(loaded.panes[0].worktree_path, "/worktrees/M")
                self.assertEqual(loaded.panes[1].worktree_path, "/worktrees/001")


if __name__ == "__main__":
    unittest.main()
