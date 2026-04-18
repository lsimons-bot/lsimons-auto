"""Tests for lsimons_auto.actions.git_actions_upgrade."""

from pathlib import Path
from unittest.mock import patch

import pytest

from lsimons_auto.actions.git_actions_upgrade import (
    Plan,
    Usage,
    apply_plan,
    build_plan,
    discover_usages,
    render_proposal,
)
from lsimons_auto.github import UsesRef


def _make_repo(tmp: Path, name: str, workflow_body: str) -> Path:
    repo = tmp / name
    (repo / ".git").mkdir(parents=True)
    wf = repo / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(workflow_body)
    return repo


def test_discover_usages_finds_all_uses(tmp_path: Path) -> None:
    _ = _make_repo(
        tmp_path,
        "alpha",
        "jobs:\n  x:\n    steps:\n"
        "      - name: checkout\n"
        "        uses: actions/checkout@v4\n"
        "      - name: setup\n"
        "        uses: actions/setup-python@v5\n",
    )
    _ = _make_repo(
        tmp_path,
        "beta",
        "jobs:\n  x:\n    steps:\n      - name: checkout\n        uses: actions/checkout@v4\n",
    )

    usages = discover_usages(sorted(tmp_path.iterdir()))
    qualifieds = sorted(u.ref.qualified for u in usages)
    assert qualifieds == [
        "actions/checkout",
        "actions/checkout",
        "actions/setup-python",
    ]


def test_build_plan_resolves_unique_actions(tmp_path: Path) -> None:
    from lsimons_auto.actions import git_actions_upgrade as mod

    repo = _make_repo(
        tmp_path,
        "alpha",
        "jobs:\n  x:\n    steps:\n"
        "        uses: actions/checkout@v4\n"
        "        uses: actions/setup-python@v5\n",
    )
    usages = discover_usages([repo])

    fake_latest = {
        "actions/checkout": ("v6.0.2", "de0fac2e" + "0" * 32),
        "actions/setup-python": ("v6.2.0", "a309ff8b" + "0" * 32),
    }

    def fake_resolve(owner: str, name: str) -> tuple[str, str]:
        return fake_latest[f"{owner}/{name}"]

    with patch.object(mod, "resolve_latest", side_effect=fake_resolve):
        plan = build_plan(usages)

    assert plan.latest == fake_latest
    assert not plan.unresolved


def test_plan_upgrades_produces_major_tag() -> None:
    plan = Plan()
    plan.latest["actions/checkout"] = ("v6.0.2", "abc" * 13 + "a")
    assert plan.upgrades() == {"actions/checkout": ("abc" * 13 + "a", "v6")}


def test_plan_usages_needing_change_skips_already_pinned() -> None:
    sha_new = "d" * 40
    repo = Path("/fake")
    wf = repo / "ci.yml"
    usages = [
        Usage(
            repo=repo,
            workflow=wf,
            line_number=1,
            ref=UsesRef("actions", "checkout", "v4", False, None),
        ),
        Usage(
            repo=repo,
            workflow=wf,
            line_number=2,
            ref=UsesRef("actions", "checkout", sha_new, True, "v6"),
        ),
    ]
    plan = Plan(usages=usages)
    plan.latest["actions/checkout"] = ("v6.0.2", sha_new)

    needing = plan.usages_needing_change()
    assert len(needing) == 1
    assert needing[0].ref.ref == "v4"


def test_plan_unresolved_skips_changes(tmp_path: Path) -> None:
    from lsimons_auto.actions import git_actions_upgrade as mod

    repo = _make_repo(
        tmp_path,
        "alpha",
        "jobs:\n  x:\n    steps:\n        uses: weird/action@v1\n",
    )
    usages = discover_usages([repo])

    def fake_resolve(owner: str, name: str) -> tuple[str, str]:
        raise RuntimeError("no releases")

    with patch.object(mod, "resolve_latest", side_effect=fake_resolve):
        plan = build_plan(usages)

    assert plan.unresolved == {"weird/action"}
    assert plan.usages_needing_change() == []


def test_render_proposal_runs_without_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _make_repo(
        tmp_path,
        "alpha",
        "jobs:\n  x:\n    steps:\n"
        "        uses: actions/checkout@v4\n"
        "        uses: actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4\n",
    )
    usages = discover_usages([repo])
    plan = Plan(usages=usages)
    plan.latest["actions/checkout"] = ("v6.0.2", "de0fac2e" + "0" * 32)
    # cache latest equals current pinned SHA -> no change
    plan.latest["actions/cache"] = ("v4.0.0", "0057852bfaa89a56745cba8c7296529d2fc39830")

    render_proposal(plan)
    captured = capsys.readouterr()
    assert "actions/checkout" in captured.out
    assert "actions/cache" in captured.out
    assert "already latest" in captured.out
    assert "alpha" in captured.out


def test_apply_plan_rewrites_files(tmp_path: Path) -> None:
    repo = _make_repo(
        tmp_path,
        "alpha",
        "jobs:\n  x:\n    steps:\n        uses: actions/checkout@v4\n",
    )
    usages = discover_usages([repo])
    plan = Plan(usages=usages)
    plan.latest["actions/checkout"] = ("v6.0.2", "de0fac2e" + "0" * 32)

    outcomes = apply_plan(plan)
    assert outcomes[repo] == "changed"
    text = (repo / ".github" / "workflows" / "ci.yml").read_text()
    assert "@de0fac2e" in text
    assert " # v6" in text
