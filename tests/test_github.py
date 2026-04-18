"""Tests for lsimons_auto.github."""

from pathlib import Path
from unittest.mock import patch

from lsimons_auto.github import (
    iter_local_repos,
    iter_workflow_files,
    major_tag,
    parse_uses,
    rewrite_workflow,
)


def test_parse_uses_unpinned() -> None:
    ref = parse_uses("      - uses: actions/checkout@v4")
    # Line must start with `uses:` optionally with leading whitespace.
    assert ref is None  # `- uses:` has a dash, regex requires `uses:` at start


def test_parse_uses_plain_line() -> None:
    ref = parse_uses("        uses: actions/checkout@v4")
    assert ref is not None
    assert ref.owner == "actions"
    assert ref.name == "checkout"
    assert ref.ref == "v4"
    assert ref.is_sha is False
    assert ref.comment is None


def test_parse_uses_pinned_with_comment() -> None:
    ref = parse_uses("        uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4")
    assert ref is not None
    assert ref.owner == "actions"
    assert ref.name == "checkout"
    assert ref.ref == "34e114876b0b11c390a56381ad16ebd13914f8d5"
    assert ref.is_sha is True
    assert ref.comment == "v4"


def test_parse_uses_local_action_skipped() -> None:
    assert parse_uses("        uses: ./path/to/local-action") is None


def test_parse_uses_single_segment_skipped() -> None:
    assert parse_uses("        uses: owneronly@v1") is None


def test_parse_uses_not_a_uses_line() -> None:
    assert parse_uses("        name: something") is None
    assert parse_uses("") is None


def test_major_tag_variants() -> None:
    assert major_tag("v6.0.2") == "v6"
    assert major_tag("v6") == "v6"
    assert major_tag("6.0.2") == "v6"
    assert major_tag("v1.2.3-beta") == "v1"


def test_iter_local_repos(tmp_path: Path) -> None:
    (tmp_path / "repo-a" / ".git").mkdir(parents=True)
    (tmp_path / "repo-b" / ".git").mkdir(parents=True)
    (tmp_path / "not-a-repo").mkdir()
    (tmp_path / "loose-file").write_text("hi")

    repos = list(iter_local_repos(tmp_path))
    assert [r.name for r in repos] == ["repo-a", "repo-b"]


def test_iter_local_repos_missing_root(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    assert list(iter_local_repos(missing)) == []


def test_iter_workflow_files(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("")
    (wf / "build.yaml").write_text("")
    (wf / "readme.md").write_text("")

    files = list(iter_workflow_files(tmp_path))
    assert [f.name for f in files] == ["build.yaml", "ci.yml"]


def test_iter_workflow_files_no_dir(tmp_path: Path) -> None:
    assert list(iter_workflow_files(tmp_path)) == []


def test_rewrite_workflow_pins_unpinned(tmp_path: Path) -> None:
    wf = tmp_path / "ci.yml"
    wf.write_text(
        "jobs:\n  x:\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v4\n"
    )
    upgrades = {"actions/checkout": ("de0fac2e4500dabe0009e67214ff5f5447ce83dd", "v6")}
    n = rewrite_workflow(wf, upgrades)
    assert n == 1
    text = wf.read_text()
    assert "uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6" in text


def test_rewrite_workflow_idempotent(tmp_path: Path) -> None:
    wf = tmp_path / "ci.yml"
    sha = "de0fac2e4500dabe0009e67214ff5f5447ce83dd"
    wf.write_text(f"        uses: actions/checkout@{sha} # v6\n")
    upgrades = {"actions/checkout": (sha, "v6")}
    assert rewrite_workflow(wf, upgrades) == 0
    assert rewrite_workflow(wf, upgrades) == 0


def test_rewrite_workflow_unknown_action_ignored(tmp_path: Path) -> None:
    wf = tmp_path / "ci.yml"
    wf.write_text("        uses: third-party/thing@v1\n")
    assert rewrite_workflow(wf, {}) == 0
    assert "third-party/thing@v1" in wf.read_text()


def test_rewrite_workflow_preserves_other_lines(tmp_path: Path) -> None:
    wf = tmp_path / "ci.yml"
    original = (
        "name: CI\n"
        "jobs:\n"
        "  x:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"  # has dash prefix -> skipped by regex
        "        uses: actions/checkout@v4\n"  # this one matches
        "      - run: echo hi\n"
    )
    wf.write_text(original)
    upgrades = {"actions/checkout": ("abc" * 13 + "a", "v6")}
    _ = rewrite_workflow(wf, upgrades)
    text = wf.read_text()
    assert "      - uses: actions/checkout@v4\n" in text  # untouched
    assert "run: echo hi" in text


def test_parse_uses_reflects_is_sha_boundary() -> None:
    # 39-char not a SHA, 40-char is
    short = "a" * 39
    long = "a" * 40
    assert parse_uses(f"        uses: x/y@{short}") is not None
    assert parse_uses(f"        uses: x/y@{short}").is_sha is False  # type: ignore[union-attr]
    assert parse_uses(f"        uses: x/y@{long}").is_sha is True  # type: ignore[union-attr]


def test_resolve_latest_annotated_tag() -> None:
    from lsimons_auto import github as gh_mod

    calls: list[str] = []

    def fake_api(endpoint: str) -> object:
        calls.append(endpoint)
        if endpoint.endswith("/releases/latest"):
            return {"tag_name": "v6.0.2"}
        if endpoint.endswith("/git/refs/tags/v6.0.2"):
            return {"object": {"sha": "tagobj123", "type": "tag"}}
        if endpoint.endswith("/git/tags/tagobj123"):
            return {"object": {"sha": "commit456", "type": "commit"}}
        raise AssertionError(f"unexpected endpoint: {endpoint}")

    with patch.object(gh_mod, "gh_api_json", side_effect=fake_api):
        tag, sha = gh_mod.resolve_latest("actions", "checkout")

    assert tag == "v6.0.2"
    assert sha == "commit456"
    assert len(calls) == 3


def test_resolve_latest_lightweight_tag() -> None:
    from lsimons_auto import github as gh_mod

    def fake_api(endpoint: str) -> object:
        if endpoint.endswith("/releases/latest"):
            return {"tag_name": "v4.6.2"}
        if endpoint.endswith("/git/refs/tags/v4.6.2"):
            return {"object": {"sha": "directcommit", "type": "commit"}}
        raise AssertionError(endpoint)

    with patch.object(gh_mod, "gh_api_json", side_effect=fake_api):
        tag, sha = gh_mod.resolve_latest("actions", "upload-artifact")

    assert tag == "v4.6.2"
    assert sha == "directcommit"
