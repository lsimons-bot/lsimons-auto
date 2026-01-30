#!/usr/bin/env python3
"""
Tests for the agent action.

This module re-exports tests from tests/agent_impl/ to maintain backwards
compatibility. All test implementations are in the agent_impl subpackage,
matching the structure of lsimons_auto/actions/agent_impl/.
"""

# Re-export all test classes for backwards compatibility
from tests.agent_impl.test_cli import (
    TestArgparseSubcommands,
    TestCLIHelp,
    TestCmdList,
)
from tests.agent_impl.test_session import (
    TestAgentPaneWorktreePath,
    TestFindPaneByTarget,
    TestListSessions,
    TestSessionManagement,
)
from tests.agent_impl.test_tmux import TestTmuxHelpers
from tests.agent_impl.test_workspace import TestFuzzyMatching, TestWorkspaceDiscovery
from tests.agent_impl.test_worktree import TestWorktreeFunctions

__all__ = [
    # Workspace tests
    "TestWorkspaceDiscovery",
    "TestFuzzyMatching",
    # Session tests
    "TestSessionManagement",
    "TestListSessions",
    "TestFindPaneByTarget",
    "TestAgentPaneWorktreePath",
    # tmux tests
    "TestTmuxHelpers",
    # CLI tests
    "TestArgparseSubcommands",
    "TestCLIHelp",
    "TestCmdList",
    # Worktree tests
    "TestWorktreeFunctions",
]

if __name__ == "__main__":
    import unittest

    unittest.main()
