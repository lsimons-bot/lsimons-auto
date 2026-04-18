"""
Shared helpers for GitHub / workflow operations.

Used by:
- actions/git_actions_upgrade.py (spec 014)
- actions/git_actions_watch.py (spec 015)

Not currently used by git_sync.py, but structured so its repo-iteration
logic can migrate here when convenient.

Depends on: `gh` CLI (authenticated) and `git` for caller commands.
"""

import json
import re
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple

USES_RE = re.compile(r"^(\s*uses:\s+)(\S+)(\s*(?:#.*)?)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class UsesRef(NamedTuple):
    """A parsed `uses:` reference from a workflow file."""

    owner: str
    name: str
    ref: str
    is_sha: bool
    comment: str | None

    @property
    def qualified(self) -> str:
        return f"{self.owner}/{self.name}"


def parse_uses(line: str) -> UsesRef | None:
    """Parse a single workflow line. Return None when it is not a `uses:` line."""
    stripped = line.rstrip("\n")
    m = USES_RE.match(stripped)
    if not m:
        return None
    _prefix, ref_part, trailing = m.groups()
    if "@" not in ref_part:
        return None
    name_with_owner, _, ref = ref_part.partition("@")
    if name_with_owner.startswith("./") or "/" not in name_with_owner:
        return None
    owner, _, name = name_with_owner.partition("/")
    comment_text: str | None = None
    stripped_trailing = trailing.strip()
    if stripped_trailing.startswith("#"):
        comment_text = stripped_trailing.lstrip("#").strip()
    return UsesRef(
        owner=owner,
        name=name,
        ref=ref,
        is_sha=bool(SHA_RE.fullmatch(ref)),
        comment=comment_text,
    )


def iter_local_repos(root: Path) -> Iterator[Path]:
    """Yield immediate subdirectories of `root` that look like git repos."""
    if not root.is_dir():
        return
    for path in sorted(root.iterdir()):
        if path.is_dir() and (path / ".git").exists():
            yield path


def iter_workflow_files(repo: Path) -> Iterator[Path]:
    """Yield `.github/workflows/*.y*ml` files in a repo."""
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.is_dir():
        return
    for path in sorted(wf_dir.iterdir()):
        if path.is_file() and path.suffix in (".yml", ".yaml"):
            yield path


def get_origin_owner(repo: Path) -> str | None:
    """Return the owner segment of the repo's `origin` remote URL, or None."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError, FileNotFoundError:
        return None
    url = result.stdout.strip()
    # https://github.com/<owner>/<repo>.git  or  git@github.com:<owner>/<repo>.git
    m = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/", url)
    if not m:
        return None
    return m.group(1)


def get_origin_repo(repo: Path) -> tuple[str, str] | None:
    """Return `(owner, name)` of the origin remote, or None."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError, FileNotFoundError:
        return None
    url = result.stdout.strip()
    m = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/([^/.]+?)(?:\.git)?/?$", url)
    if not m:
        return None
    return m.group(1), m.group(2)


def gh_api_json(endpoint: str) -> Any:  # pyright: ignore[reportExplicitAny]
    """Run `gh api <endpoint>` and return parsed JSON."""
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh api {endpoint}: {result.stderr.strip() or 'failed'}")
    return json.loads(result.stdout)


def resolve_latest(owner: str, name: str) -> tuple[str, str]:
    """Return `(tag, sha)` for the latest release of `owner/name`."""
    release = gh_api_json(f"repos/{owner}/{name}/releases/latest")
    tag = str(release["tag_name"])
    ref_obj = gh_api_json(f"repos/{owner}/{name}/git/refs/tags/{tag}")
    sha = str(ref_obj["object"]["sha"])
    obj_type = str(ref_obj["object"]["type"])
    if obj_type == "tag":
        tag_obj = gh_api_json(f"repos/{owner}/{name}/git/tags/{sha}")
        sha = str(tag_obj["object"]["sha"])
    return tag, sha


def major_tag(tag: str) -> str:
    """Given `v6.0.2` return `v6`. Given `6.0.2` return `v6`. Given `v6` return `v6`."""
    stripped = tag.removeprefix("v")
    major = stripped.split(".")[0]
    if not major:
        return tag
    return f"v{major}"


def rewrite_workflow(path: Path, upgrades: dict[str, tuple[str, str]]) -> int:
    """
    Rewrite `uses:` lines in a workflow file.

    `upgrades` maps `"owner/name"` to `(new_sha, new_major_tag)`.
    Returns the number of lines changed. Idempotent: re-running on an already-
    upgraded file returns 0.
    """
    original = path.read_text()
    lines = original.splitlines(keepends=True)
    changes = 0
    for i, line in enumerate(lines):
        parsed = parse_uses(line)
        if parsed is None:
            continue
        if parsed.qualified not in upgrades:
            continue
        new_sha, new_tag = upgrades[parsed.qualified]
        if parsed.ref == new_sha:
            continue
        indent_match = re.match(r"^(\s*uses:\s+)", line)
        assert indent_match is not None
        prefix = indent_match.group(1)
        newline = f"{prefix}{parsed.qualified}@{new_sha} # {new_tag}\n"
        if not line.endswith("\n"):
            newline = newline.rstrip("\n")
        if line != newline:
            lines[i] = newline
            changes += 1
    if changes:
        path.write_text("".join(lines))
    return changes
