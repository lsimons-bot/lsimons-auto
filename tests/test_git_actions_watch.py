"""Tests for lsimons_auto.actions.git_actions_watch."""

import pytest

from lsimons_auto.actions.git_actions_watch import (
    RepoState,
    RunInfo,
    classify,
    exit_code,
    render_lines,
)


def _state(name: str, **kwargs: object) -> RepoState:
    base = RepoState(
        name=name,
        owner="lsimons",
        gh_repo=("lsimons", name),
        head_sha="abcdef0abcdef0abcdef0abcdef0abcdef0abcd0",
        run=None,
    )
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


def _run(status: str, conclusion: str = "") -> RunInfo:
    return RunInfo(
        status=status,
        conclusion=conclusion,
        display_title="ci",
        workflow_name="CI",
        url="https://example/runs/1",
        head_sha="abcdef01234567",
        created_at="2026-04-18T04:00:00Z",
    )


def test_classify_ok() -> None:
    s = _state("a", run=_run("completed", "success"))
    assert classify(s) == "ok"


def test_classify_failed() -> None:
    s = _state("a", run=_run("completed", "failure"))
    assert classify(s) == "failed"


def test_classify_running() -> None:
    s = _state("a", run=_run("in_progress"))
    assert classify(s) == "running"


def test_classify_skipped() -> None:
    s = _state("a", run=_run("completed", "skipped"))
    assert classify(s) == "skipped"


def test_classify_no_run() -> None:
    s = _state("a")
    assert classify(s) == "pending"


def test_exit_code_all_ok() -> None:
    states = [_state("a", run=_run("completed", "success"))]
    assert exit_code(states, allow_running=False) == 0


def test_exit_code_any_failed() -> None:
    states = [
        _state("a", run=_run("completed", "success")),
        _state("b", run=_run("completed", "failure")),
    ]
    assert exit_code(states, allow_running=False) == 1


def test_exit_code_running_no_follow() -> None:
    states = [
        _state("a", run=_run("completed", "success")),
        _state("b", run=_run("in_progress")),
    ]
    assert exit_code(states, allow_running=False) == 2


def test_exit_code_running_in_follow_considered_ok_if_no_failures() -> None:
    states = [_state("a", run=_run("in_progress"))]
    assert exit_code(states, allow_running=True) == 0


def test_exit_code_failed_beats_running() -> None:
    states = [
        _state("a", run=_run("in_progress")),
        _state("b", run=_run("completed", "failure")),
    ]
    assert exit_code(states, allow_running=True) == 1


def test_render_lines_includes_name_and_label(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    states = [
        _state("alpha", run=_run("completed", "success")),
        _state("beta", run=_run("completed", "failure")),
        _state("gamma"),
    ]
    lines = render_lines(states)
    assert any("alpha" in line and "ok" in line for line in lines)
    assert any("beta" in line and "failed" in line for line in lines)
    assert any("gamma" in line and "pending" in line for line in lines)


def test_render_lines_with_note(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    s = _state("alpha")
    s.note = "no workflows"
    lines = render_lines([s])
    assert "(no workflows)" in lines[0]
