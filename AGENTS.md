# Agent Instructions for lsimons-auto

Personal automation toolkit for macOS with modular CLI (`auto`) and daily routine (`start-the-day`).

## Quick Reference

- **Install**: `python3 install.py`
- **Test**: `uv run pytest` (unit tests) or `uv run pytest -m integration` (integration tests)
- **Lint**: `uv run basedpyright`
- **Run**: `auto <action_name>` or `start-the-day`

## Structure

Actions live in `lsimons_auto/actions/`. Each is a self-contained Python script with `main(args: Optional[list[str]] = None)` function.

**Adding a new action:**
1. Create spec in `docs/spec/`
2. Implement in `lsimons_auto/actions/`
3. Add tests in `tests/`

## Guidelines

**Code quality:**
- Full type annotations (strict basedpyright)
- PEP 8 formatting
- Unit tests (fast, no side effects) run by default
- Integration tests marked with `@pytest.mark.integration`

**Specs:** Focus on design decisions, keep under 100 lines, reference shared patterns.

**Pyright ignores:** Use specific codes like `# pyright: ignore[reportAny]`

## Commit Message Convention

Follow [Conventional Commits](https://conventionalcommits.org/):

**Format:** `type(scope): description`

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci`, `perf`, `revert`, `improvement`, `chore`

Reference spec numbers: `feat(actions): implement organize-desktop (spec-004)`

## Session Completion

Work is NOT complete until `git push` succeeds.

1. **Quality gates** (if code changed):
   ```bash
   uv run pytest
   uv run basedpyright
   ```

2. **Push**:
   ```bash
   git pull --rebase && git push
   git status  # must show "up to date with origin"
   ```

Never stop before pushing. If push fails, resolve and retry.
