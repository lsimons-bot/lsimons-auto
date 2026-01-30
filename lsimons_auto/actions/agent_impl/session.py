"""
session.py - Data classes for agent session management.

Defines AgentPane and AgentSession for tracking multi-agent Ghostty layouts.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# Constants
SESSIONS_DIR = Path.home() / ".config" / "auto" / "agent" / "sessions"


@dataclass
class AgentPane:
    """Represents a single agent pane in the session."""

    id: str  # e.g., "M-lsimons-auto" or "001-lsimons-auto"
    pane_index: int  # 0 for main, 1+ for subagents
    command: str  # e.g., "claude" or "pi"
    is_main: bool
    worktree_path: Optional[str] = None  # Path to git worktree for this pane
    tmux_pane_id: Optional[str] = None  # tmux pane ID (e.g., "%0", "%1")


@dataclass
class AgentSession:
    """Represents an active agent session."""

    session_id: str  # e.g., "auto-agent-20260121-143052"
    workspace_path: str  # e.g., "/Users/lsimons/git/lsimons/lsimons-auto"
    repo_name: str  # e.g., "lsimons-auto"
    org_name: str  # e.g., "lsimons"
    created_at: str  # ISO timestamp
    panes: list[AgentPane] = field(default_factory=lambda: [])
    window_id: Optional[int] = None  # Deprecated: Ghostty window ID
    tmux_session_name: Optional[str] = None  # tmux session name

    @classmethod
    def load(cls, session_id: str) -> "AgentSession":
        """Load session from disk."""
        session_file = SESSIONS_DIR / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        with open(session_file) as f:
            data = json.load(f)
        panes = [AgentPane(**p) for p in data.pop("panes", [])]
        return cls(**data, panes=panes)

    def save(self) -> None:
        """Persist session to disk."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_file = SESSIONS_DIR / f"{self.session_id}.json"
        with open(session_file, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def delete(self) -> None:
        """Remove session file from disk."""
        session_file = SESSIONS_DIR / f"{self.session_id}.json"
        if session_file.exists():
            session_file.unlink()


def list_sessions() -> list[AgentSession]:
    """List all saved sessions."""
    sessions: list[AgentSession] = []
    if not SESSIONS_DIR.exists():
        return sessions

    for session_file in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            session = AgentSession.load(session_file.stem)
            sessions.append(session)
        except (json.JSONDecodeError, KeyError):
            continue

    return sessions


def get_most_recent_session() -> Optional[AgentSession]:
    """Get the most recently created session."""
    sessions = list_sessions()
    return sessions[0] if sessions else None


def find_pane_by_target(
    session: AgentSession, target: str
) -> Optional[tuple[AgentPane, int]]:
    """Find pane by ID, index, or 'main'."""
    target_lower = target.lower()

    # Check for 'main' keyword
    if target_lower == "main":
        for i, pane in enumerate(session.panes):
            if pane.is_main:
                return (pane, i)

    # Check for numeric index
    if target.isdigit():
        idx = int(target)
        if 0 <= idx < len(session.panes):
            return (session.panes[idx], idx)

    # Check for pane ID match
    for i, pane in enumerate(session.panes):
        if target_lower in pane.id.lower():
            return (pane, i)

    return None
