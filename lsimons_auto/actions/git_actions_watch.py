#!/usr/bin/env python3
"""
git_actions_watch.py - Show GitHub Actions CI status for local repos.

Scans a root directory for local git repos, looks up the latest CI run for
each (by commit, by recency, or the latest overall), and renders a compact
per-repo status line. Optional follow mode polls until runs complete.

See docs/spec/015-git-actions-watch.md.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from lsimons_auto.github import (
    get_origin_owner,
    get_origin_repo,
    iter_local_repos,
    iter_workflow_files,
)

DEFAULT_ROOT = Path.home() / "git" / "lsimons"
DEFAULT_RECENT_MINUTES = 10
DEFAULT_TIMEOUT_SECONDS = 20 * 60
INITIAL_POLL = 5
BACKOFF_AFTER_SECONDS = 60
BACKOFF_POLL = 15


@dataclass
class RunInfo:
    status: str  # queued | in_progress | completed | "" (no run)
    conclusion: str  # success | failure | cancelled | timed_out | skipped | ""
    display_title: str
    workflow_name: str
    url: str
    head_sha: str
    created_at: str


@dataclass
class RepoState:
    name: str
    owner: str | None
    gh_repo: tuple[str, str] | None
    head_sha: str | None
    run: RunInfo | None  # None when no run matched
    note: str = ""  # e.g. "archived", "no workflows"


def _head_sha(repo: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError, FileNotFoundError:
        return None
    return result.stdout.strip()


def _has_workflows(repo: Path) -> bool:
    for _ in iter_workflow_files(repo):
        return True
    return False


def _gh_run_list(
    owner: str,
    name: str,
    *,
    commit: str | None = None,
    limit: int = 1,
) -> list[dict[str, object]]:
    cmd = [
        "gh",
        "run",
        "list",
        "--repo",
        f"{owner}/{name}",
        "--limit",
        str(limit),
        "--json",
        "status,conclusion,displayTitle,url,workflowName,createdAt,headSha",
    ]
    if commit is not None:
        cmd.extend(["--commit", commit])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data  # pyright: ignore[reportUnknownVariableType]


def _run_info_from_dict(d: dict[str, object]) -> RunInfo:
    return RunInfo(
        status=str(d.get("status") or ""),
        conclusion=str(d.get("conclusion") or ""),
        display_title=str(d.get("displayTitle") or ""),
        workflow_name=str(d.get("workflowName") or ""),
        url=str(d.get("url") or ""),
        head_sha=str(d.get("headSha") or ""),
        created_at=str(d.get("createdAt") or ""),
    )


def collect_state(
    repo: Path,
    *,
    recent_minutes: int | None,
    latest: bool,
) -> RepoState:
    """Build a RepoState for a repo by querying `gh run list`."""
    gh_repo = get_origin_repo(repo)
    state = RepoState(
        name=repo.name,
        owner=get_origin_owner(repo),
        gh_repo=gh_repo,
        head_sha=_head_sha(repo),
        run=None,
    )
    if not _has_workflows(repo):
        state.note = "no workflows"
        return state
    if gh_repo is None:
        state.note = "no github origin"
        return state
    owner, name = gh_repo

    runs: list[dict[str, object]]
    if latest:
        runs = _gh_run_list(owner, name, limit=1)
    elif recent_minutes is not None:
        runs = _gh_run_list(owner, name, limit=5)
        cutoff = datetime.now(tz=UTC) - timedelta(minutes=recent_minutes)
        filtered: list[dict[str, object]] = []
        for r in runs:
            ts = _parse_iso(str(r.get("createdAt") or ""))
            if ts is not None and ts >= cutoff:
                filtered.append(r)
        runs = filtered
    else:
        if state.head_sha is None:
            state.note = "no HEAD"
            return state
        runs = _gh_run_list(owner, name, commit=state.head_sha, limit=1)

    if not runs:
        return state
    state.run = _run_info_from_dict(runs[0])
    return state


def _parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def classify(state: RepoState) -> str:
    """Return one of: running, ok, failed, skipped, pending."""
    if state.run is None:
        return "pending"
    if state.run.status in ("queued", "in_progress"):
        return "running"
    if state.run.status == "completed":
        conc = state.run.conclusion
        if conc == "success":
            return "ok"
        if conc in ("failure", "cancelled", "timed_out"):
            return "failed"
        if conc == "skipped":
            return "skipped"
    return "pending"


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _color(text: str, code: str) -> str:
    if not _use_color():
        return text
    return f"\033[{code}m{text}\033[0m"


_ICONS = {
    "ok": ("✓", "32"),  # green
    "failed": ("✗", "31"),  # red
    "running": ("⋯", "33"),  # yellow
    "skipped": ("-", "2"),  # dim
    "pending": ("·", "2"),  # dim
}


def render_lines(states: list[RepoState], *, verbose: bool = False) -> list[str]:
    """Render per-repo status lines."""
    width = max((len(s.name) for s in states), default=10)
    out: list[str] = []
    for s in states:
        kind = classify(s)
        icon, color = _ICONS[kind]
        icon_s = _color(icon, color)
        label = kind
        short_sha = (s.run.head_sha[:7] if s.run else (s.head_sha or "")[:7]) or "-------"
        wf = s.run.workflow_name if s.run else ""
        note = f" ({s.note})" if s.note else ""
        extra = ""
        if s.run and (kind == "failed" or verbose):
            extra = f"  {_color(s.run.url, '2')}"
        out.append(f"  {icon_s} {s.name:<{width}}  {label:<8}  {short_sha}  {wf}{note}{extra}")
    return out


def render(states: list[RepoState], *, verbose: bool = False) -> None:
    for line in render_lines(states, verbose=verbose):
        print(line)


def exit_code(states: list[RepoState], *, allow_running: bool) -> int:
    running = any(classify(s) == "running" for s in states)
    failed = any(classify(s) == "failed" for s in states)
    if failed:
        return 1
    if running and not allow_running:
        return 2
    return 0


def filter_by_owner(repos: list[Path], owner: str | None) -> list[Path]:
    if owner is None:
        return repos
    return [r for r in repos if get_origin_owner(r) == owner]


def _clear_previous(lines: int) -> None:
    if lines <= 0:
        return
    # Move cursor up `lines` and clear to end of screen
    sys.stdout.write(f"\033[{lines}F\033[J")
    sys.stdout.flush()


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="auto git-actions-watch",
        description="Show per-repo GitHub Actions CI status for local repos.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="scan root")
    parser.add_argument("-o", "--owner", default=None, help="filter repos by origin owner")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--recent",
        nargs="?",
        type=int,
        const=DEFAULT_RECENT_MINUTES,
        default=None,
        metavar="MINUTES",
        help="show any run created in the last N minutes (default 10)",
    )
    mode.add_argument(
        "--latest", action="store_true", help="show the latest run regardless of commit"
    )
    parser.add_argument("-f", "--follow", action="store_true", help="poll until runs finish")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="follow-mode timeout (default 1200)",
    )
    parser.add_argument("--verbose", action="store_true")
    parsed = parser.parse_args(args)

    root: Path = parsed.root
    if not root.is_dir():
        print(f"Error: root not found: {root}", file=sys.stderr)
        sys.exit(1)

    repos = filter_by_owner(list(iter_local_repos(root)), parsed.owner)
    if not repos:
        print(f"No git repos under {root}.")
        sys.exit(0)

    def snapshot() -> list[RepoState]:
        return [collect_state(r, recent_minutes=parsed.recent, latest=parsed.latest) for r in repos]

    states = snapshot()
    render(states, verbose=parsed.verbose)

    if not parsed.follow:
        sys.exit(exit_code(states, allow_running=False))

    start = time.time()
    poll = INITIAL_POLL
    prev_line_count = len(render_lines(states, verbose=parsed.verbose))
    while any(classify(s) == "running" for s in states):
        if time.time() - start > parsed.timeout:
            print("(timeout)")
            sys.exit(exit_code(states, allow_running=True))
        time.sleep(poll)
        if time.time() - start > BACKOFF_AFTER_SECONDS:
            poll = BACKOFF_POLL
        states = snapshot()
        _clear_previous(prev_line_count)
        render(states, verbose=parsed.verbose)
        prev_line_count = len(render_lines(states, verbose=parsed.verbose))

    sys.exit(exit_code(states, allow_running=True))


if __name__ == "__main__":
    main()
