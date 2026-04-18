#!/usr/bin/env python3
"""
git_actions_upgrade.py - Upgrade GitHub Actions pinned SHAs to latest stable.

Scans a root directory for local git repos, finds every `uses:` reference in
their workflows, resolves each unique action to its latest stable release SHA
via the `gh` CLI, presents a proposal, and on confirmation commits and pushes
the changes per repo.

See docs/spec/014-git-actions-upgrade.md.
"""

import argparse
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from lsimons_auto.github import (
    UsesRef,
    get_origin_owner,
    iter_local_repos,
    iter_workflow_files,
    major_tag,
    parse_uses,
    resolve_latest,
    rewrite_workflow,
)

DEFAULT_ROOT = Path.home() / "git" / "lsimons"

COMMIT_MSG = """ci: upgrade pinned actions to latest stable versions

Upgrades the pinned GitHub Action references in this repo's workflows
to the latest stable releases resolved by `auto git-actions-upgrade`
(spec 014). SHAs remain pinned; the trailing `# vN` comment reflects
the resolved major version.

Co-Authored-By: lsimons-bot <bot@leosimons.com>
Assisted-by: Claude:claude-opus-4-7
"""


class Usage(NamedTuple):
    repo: Path
    workflow: Path
    line_number: int
    ref: UsesRef


@dataclass
class Plan:
    """Aggregated upgrade proposal."""

    # owner/name -> (latest_tag, latest_sha)
    latest: dict[str, tuple[str, str]] = field(default_factory=dict)
    # Flat list of every parsed usage across all repos.
    usages: list[Usage] = field(default_factory=list)
    # Actions whose latest resolution failed (e.g. no releases).
    unresolved: set[str] = field(default_factory=set)

    def upgrades(self) -> dict[str, tuple[str, str]]:
        """Return `{qualified: (new_sha, new_major_tag)}` for resolved actions."""
        return {qualified: (sha, major_tag(tag)) for qualified, (tag, sha) in self.latest.items()}

    def usages_needing_change(self) -> list[Usage]:
        up = self.upgrades()
        result: list[Usage] = []
        for u in self.usages:
            if u.ref.qualified not in up:
                continue
            new_sha, _ = up[u.ref.qualified]
            if u.ref.ref != new_sha:
                result.append(u)
        return result


def discover_usages(repos: Iterable[Path]) -> list[Usage]:
    """Scan every workflow file under each repo and return parsed usages."""
    out: list[Usage] = []
    for repo in repos:
        for wf in iter_workflow_files(repo):
            text = wf.read_text()
            for line_no, line in enumerate(text.splitlines(), start=1):
                parsed = parse_uses(line)
                if parsed is None:
                    continue
                out.append(Usage(repo=repo, workflow=wf, line_number=line_no, ref=parsed))
    return out


def filter_by_owner(repos: Iterable[Path], owner: str | None) -> list[Path]:
    """Keep only repos whose origin URL matches `owner` (when set)."""
    repos = list(repos)
    if owner is None:
        return repos
    return [r for r in repos if get_origin_owner(r) == owner]


def build_plan(usages: list[Usage]) -> Plan:
    """Resolve latest release SHAs for every unique action in `usages`."""
    plan = Plan(usages=usages)
    unique = sorted({u.ref.qualified for u in usages})
    for qualified in unique:
        owner, _, name = qualified.partition("/")
        try:
            tag, sha = resolve_latest(owner, name)
        except (RuntimeError, KeyError, ValueError) as e:
            print(f"  warn: could not resolve {qualified}: {e}", file=sys.stderr)
            plan.unresolved.add(qualified)
            continue
        plan.latest[qualified] = (tag, sha)
    return plan


def _short(sha: str) -> str:
    return sha[:7]


def render_proposal(plan: Plan) -> None:
    """Print the upgrade proposal to stdout."""
    usages_needing = plan.usages_needing_change()

    # Per-action table
    print("Action upgrades:")
    width = max((len(q) for q in plan.latest), default=20)
    for qualified, (tag, sha) in sorted(plan.latest.items()):
        new_major = major_tag(tag)
        # Determine if any usage in this group needs change
        any_change = any(u.ref.qualified == qualified and u.ref.ref != sha for u in plan.usages)
        if any_change:
            # Collect current versions in use
            current: set[str] = set()
            for u in plan.usages:
                if u.ref.qualified != qualified:
                    continue
                if u.ref.ref == sha:
                    continue
                label = u.ref.comment or u.ref.ref
                current.add(label)
            current_label = ", ".join(sorted(current))
            print(f"  {qualified:<{width}}  {current_label:<12} -> {tag:<10} ({_short(sha)})")
        else:
            print(f"  {qualified:<{width}}  already latest ({_short(sha)} {new_major})")
    for qualified in sorted(plan.unresolved):
        print(f"  {qualified:<{width}}  UNRESOLVED")

    # Per-repo table
    print()
    print("Per repo:")
    per_repo: dict[Path, list[Usage]] = {}
    for u in usages_needing:
        per_repo.setdefault(u.repo, []).append(u)
    repo_width = max((len(r.name) for r in per_repo), default=20)
    repos_with_workflows = {u.repo for u in plan.usages}
    for repo in sorted(repos_with_workflows, key=lambda p: p.name):
        changes = per_repo.get(repo, [])
        if not changes:
            print(f"  {repo.name:<{repo_width}}  (no changes)")
            continue
        files = sorted({u.workflow.name for u in changes})
        files_label = ", ".join(files)
        print(f"  {repo.name:<{repo_width}}  {len(changes)} refs  ({files_label})")


def apply_plan(plan: Plan, *, verbose: bool = False) -> dict[Path, str]:
    """Rewrite workflow files per repo.

    Returns `{repo: outcome}` where outcome is one of:
      - "changed"  — files modified
      - "noop"     — nothing to do
    """
    upgrades = plan.upgrades()
    outcomes: dict[Path, str] = {}
    per_repo: dict[Path, list[Usage]] = {}
    for u in plan.usages_needing_change():
        per_repo.setdefault(u.repo, []).append(u)

    for repo, changes in per_repo.items():
        workflows = sorted({u.workflow for u in changes})
        total = 0
        for wf in workflows:
            n = rewrite_workflow(wf, upgrades)
            total += n
            if verbose:
                print(f"  {repo.name}/{wf.name}: {n} lines rewritten")
        outcomes[repo] = "changed" if total else "noop"
    return outcomes


def commit_and_push(repo: Path, verbose: bool = False) -> str:
    """Commit workflow changes and push. Returns an outcome label."""

    def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, cwd=repo, capture_output=True, text=True)

    add = run(["git", "add", ".github/workflows/"])
    if add.returncode != 0:
        return f"add-failed: {add.stderr.strip()}"
    commit = run(["git", "commit", "-m", COMMIT_MSG])
    if commit.returncode != 0:
        return f"commit-failed: {commit.stderr.strip() or commit.stdout.strip()}"
    pull = run(["git", "pull", "--rebase"])
    if pull.returncode != 0:
        return f"pull-failed: {pull.stderr.strip()}"
    push = run(["git", "push"])
    if push.returncode == 0:
        return "pushed"
    err = (push.stderr or "") + (push.stdout or "")
    if "repository was archived" in err.lower() or "archived so it is read-only" in err.lower():
        # Undo local commit so working tree matches origin
        _ = run(["git", "reset", "--hard", "HEAD~1"])
        return "archived"
    return f"push-failed: {err.strip()}"


def confirm(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="auto git-actions-upgrade",
        description=(
            "Upgrade pinned GitHub Action refs to latest stable releases across local repos."
        ),
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="scan root")
    parser.add_argument("-o", "--owner", default=None, help="filter repos by origin owner")
    parser.add_argument("-y", "--yes", action="store_true", help="skip the confirmation prompt")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="build the proposal but never modify files or push",
    )
    parser.add_argument("--verbose", action="store_true")
    parsed = parser.parse_args(args)

    root: Path = parsed.root
    if not root.is_dir():
        print(f"Error: root not found: {root}", file=sys.stderr)
        sys.exit(1)

    repos = filter_by_owner(iter_local_repos(root), parsed.owner)
    if not repos:
        print(f"No git repos found under {root}")
        sys.exit(0)

    print(f"Scanning {len(repos)} repos under {root} ...")
    usages = discover_usages(repos)
    if not usages:
        print("No workflows found — nothing to do.")
        sys.exit(0)

    unique_actions = sorted({u.ref.qualified for u in usages})
    print(f"Found {len(usages)} `uses:` refs across {len(unique_actions)} unique actions.")

    print("Resolving latest versions ...")
    plan = build_plan(usages)
    print()
    render_proposal(plan)

    needing = plan.usages_needing_change()
    if not needing:
        print("\nAll actions already at latest. Nothing to do.")
        sys.exit(0)

    if parsed.dry_run:
        print("\n(dry-run) Not applying changes.")
        sys.exit(0)

    if not parsed.yes:
        print()
        if not confirm(f"Apply to {len({u.repo for u in needing})} repos?"):
            print("Aborted.")
            sys.exit(0)

    print("\nApplying ...")
    outcomes = apply_plan(plan, verbose=parsed.verbose)

    print("\nCommitting and pushing ...")
    archived: list[Path] = []
    pushed: list[Path] = []
    failed: list[tuple[Path, str]] = []
    for repo, outcome in outcomes.items():
        if outcome != "changed":
            continue
        result = commit_and_push(repo, verbose=parsed.verbose)
        if result == "pushed":
            pushed.append(repo)
            print(f"  {repo.name}: pushed")
        elif result == "archived":
            archived.append(repo)
            print(f"  {repo.name}: archived (commit reset)")
        else:
            failed.append((repo, result))
            print(f"  {repo.name}: {result}")

    print()
    print(f"Pushed: {len(pushed)}. Archived: {len(archived)}. Failed: {len(failed)}.")
    if pushed:
        print("Tip: `auto git-actions-watch --recent --follow` to track CI.")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
