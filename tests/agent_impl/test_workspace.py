#!/usr/bin/env python3
"""
Tests for workspace discovery and fuzzy matching.

Tests the workspace.py module functionality.
"""

import tempfile
import unittest
from pathlib import Path

from lsimons_auto.actions.agent_impl import workspace


class TestWorkspaceDiscovery(unittest.TestCase):
    """Test workspace discovery functionality."""

    def test_discover_workspaces_finds_orgs(self) -> None:
        """Test workspace discovery finds org directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = Path(tmpdir)
            (git_root / "org1" / "repo1").mkdir(parents=True)
            (git_root / "org1" / "repo2").mkdir(parents=True)
            (git_root / "org2" / "repo3").mkdir(parents=True)

            workspaces = workspace.discover_workspaces(git_root)

            self.assertIn("org1", workspaces)
            self.assertIn("org2", workspaces)
            self.assertEqual(len(workspaces["org1"]), 2)
            self.assertEqual(len(workspaces["org2"]), 1)

    def test_discover_workspaces_ignores_hidden(self) -> None:
        """Test workspace discovery ignores hidden directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = Path(tmpdir)
            (git_root / "org1" / "repo1").mkdir(parents=True)
            (git_root / ".hidden" / "repo2").mkdir(parents=True)
            (git_root / "org1" / ".hidden-repo").mkdir(parents=True)

            workspaces = workspace.discover_workspaces(git_root)

            self.assertIn("org1", workspaces)
            self.assertNotIn(".hidden", workspaces)
            self.assertNotIn(".hidden-repo", workspaces.get("org1", {}))

    def test_discover_workspaces_empty_dir(self) -> None:
        """Test workspace discovery handles empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = Path(tmpdir)

            workspaces = workspace.discover_workspaces(git_root)

            self.assertEqual(workspaces, {})

    def test_discover_workspaces_nonexistent_dir(self) -> None:
        """Test workspace discovery handles nonexistent directory."""
        workspaces = workspace.discover_workspaces(Path("/nonexistent/path"))
        self.assertEqual(workspaces, {})


class TestFuzzyMatching(unittest.TestCase):
    """Test fuzzy matching functionality."""

    def test_fuzzy_match_exact(self) -> None:
        """Test exact match returns correct workspace."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/test/path")}}
        result = workspace.fuzzy_match_workspace("lsimons", "lsimons-auto", workspaces)
        self.assertEqual(result[0], "lsimons")
        self.assertEqual(result[1], "lsimons-auto")
        self.assertEqual(result[2], Path("/test/path"))

    def test_fuzzy_match_partial_org(self) -> None:
        """Test partial org match works."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/test/path")}}
        result = workspace.fuzzy_match_workspace("lsim", "auto", workspaces)
        self.assertEqual(result[0], "lsimons")
        self.assertEqual(result[1], "lsimons-auto")

    def test_fuzzy_match_case_insensitive(self) -> None:
        """Test case insensitive matching."""
        workspaces = {"Lsimons": {"Lsimons-Auto": Path("/test/path")}}
        result = workspace.fuzzy_match_workspace("lsim", "auto", workspaces)
        self.assertEqual(result[0], "Lsimons")
        self.assertEqual(result[1], "Lsimons-Auto")

    def test_fuzzy_match_exact_org_preferred(self) -> None:
        """Test exact org match is preferred over partial matches."""
        workspaces = {
            "lsimons": {"lsimons-auto": Path("/a")},
            "lsimons-bot": {"bot-repo": Path("/b")},
        }
        # "lsimons" should match exactly, not raise ambiguity
        result = workspace.fuzzy_match_workspace("lsimons", "auto", workspaces)
        self.assertEqual(result[0], "lsimons")
        self.assertEqual(result[1], "lsimons-auto")

    def test_fuzzy_match_ambiguous_org_raises(self) -> None:
        """Test ambiguous org match raises ValueError when no exact match."""
        workspaces = {
            "lsimons-dev": {"repo-a": Path("/a")},
            "lsimons-bot": {"repo-b": Path("/b")},
        }
        # "lsimons" matches both but is not exact match for either
        with self.assertRaises(ValueError) as cm:
            workspace.fuzzy_match_workspace("lsimons", "repo", workspaces)
        self.assertIn("Ambiguous", str(cm.exception))

    def test_fuzzy_match_ambiguous_repo_raises(self) -> None:
        """Test ambiguous repo match raises ValueError."""
        workspaces = {
            "lsimons": {
                "lsimons-auto": Path("/a"),
                "lsimons-tools": Path("/b"),
            }
        }
        with self.assertRaises(ValueError) as cm:
            workspace.fuzzy_match_workspace("lsimons", "lsimons", workspaces)
        self.assertIn("Ambiguous", str(cm.exception))

    def test_fuzzy_match_no_org_raises(self) -> None:
        """Test no org match raises ValueError."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/a")}}
        with self.assertRaises(ValueError) as cm:
            workspace.fuzzy_match_workspace("nonexistent", "auto", workspaces)
        self.assertIn("No org found", str(cm.exception))

    def test_fuzzy_match_no_repo_raises(self) -> None:
        """Test no repo match raises ValueError."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/a")}}
        with self.assertRaises(ValueError) as cm:
            workspace.fuzzy_match_workspace("lsimons", "nonexistent", workspaces)
        self.assertIn("No repo found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
