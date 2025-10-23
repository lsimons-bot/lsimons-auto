# Agent Instructions

This document provides instructions for AI code-generation agents to ensure consistent and high-quality contributions to the `lsimons-auto` project.

## Response Style

- Be concise in responses - avoid over-explaining changes.
- Focus on the specific task requested rather than extensive commentary.

## Project Overview

The `lsimons-auto` project is a comprehensive personal automation toolkit for macOS. It provides a modular command-line interface (`auto`) for on-demand actions and a scheduled daily routine (`start-the-day`) to establish consistent workflows.

- **`auto` CLI**: A unified command dispatcher that dynamically discovers and executes modular "action" scripts.
- **`start-the-day`**: A separate, scheduled script that runs a sequence of actions each morning.
- **Spec-Based Development**: All features are first defined in specification documents before implementation.

## Building and Running

- **Installation**: `python3 install.py`
  - This script creates symlinks in `~/.local/bin` and installs a macOS LaunchAgent for the daily routine.
- **Testing**: `uv run pytest`
  - Runs the full suite of unit and integration tests.
- **Running Actions**:
  - `auto <action_name>` (e.g., `auto organize-desktop`)
  - `start-the-day`

## Development Conventions

### Adding a New Action

1.  **Create a Specification**: Add a new Markdown file in `docs/spec/` that defines the feature's purpose, design, and implementation notes. Follow the existing format (e.g., `000-shared-patterns.md`).
2.  **Implement the Action**: Create a new Python script in `lsimons_auto/actions/`.
    - The script must be executable.
    - It should include a `main(args: Optional[list[str]] = None)` function.
    - Use the `argparse` module for command-line argument handling.
3.  **Add Tests**: Create a corresponding test file in the `tests/` directory.

### Testing

- **Unit tests**: Fast tests with no side effects (run by default with `uv run pytest`)
- **Integration tests**: End-to-end tests with real side effects (file I/O, subprocess calls)
  - Mark integration test classes with `@pytest.mark.integration`
  - Run explicitly with `uv run pytest -m integration`
  - Skipped by default to keep test runs fast
- **Test separation**: Unit tests validate logic, integration tests validate real-world behavior
- **Default behavior**: `uv run pytest` runs only unit tests (fast feedback loop)

### Code Style

- **Typing**: The project uses strict type checking with `pyright`. All new code must be fully type-hinted.
- **Formatting**: Follow standard Python formatting guidelines (PEP 8).
- **Modularity**: Actions should be self-contained and independent.

### Commits

- Reference the relevant spec number in commit messages (e.g., "feat(actions): Implement organize-desktop action (spec-004)").

### Specification Writing

- Focus on design decisions and rationale, not implementation details.
- Keep specs under 100 lines when possible - longer specs likely need splitting.
- Reference shared patterns (action scripts, testing, installation) rather than repeating.
- Include code only for critical design interfaces, not full implementations.
- Use bullet points for lists rather than verbose paragraphs.
- Eliminate sections that would be identical across multiple specs.

### Diagnostic Handling

For diagnostic warnings, use specific Pyright ignore comments with error codes:
- `# pyright: ignore[reportAny]` for "Type is Any" warnings
- `# pyright: ignore[reportImplicitOverride]` for unittest method override warnings
- Use `_ = function_call()` assignment for unused return value warnings.


## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**
```bash
bd ready --json
```

**Create new issues:**
```bash
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**
```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**
```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:
- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### MCP Server (Recommended)

If using Claude or MCP-compatible clients, install the beads MCP server:

```bash
pip install beads-mcp
```

Add to MCP config (e.g., `~/.config/claude/config.json`):
```json
{
  "beads": {
    "command": "beads-mcp",
    "args": []
  }
}
```

Then use `mcp__beads__*` functions instead of CLI commands.

### Workflow: Update bd BEFORE Committing

**CRITICAL**: Always update bd issue status **before** making commits:

1. `bd update <id> --status in_progress --json` - Claim the work
2. Do the work (make code changes)
3. `bd close <id> --reason "Description of what was done" --json` - Close the issue
4. `git add -A && git commit -m "..."` - Commit (includes `.beads/issues.jsonl`)
5. Repeat for next issue

This ensures:
- Issue status is tracked in version control
- Commits reference closed issues
- `.beads/issues.jsonl` is always up-to-date in commits

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ **Update bd status BEFORE committing** (not after)
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems
- ❌ Do NOT commit before updating bd status

For more details, see README.md and QUICKSTART.md.

## If Unsure

1. Re-read [AGENTS.md](AGENTS.md)
2. Look at an existing similar spec or action
3. Propose a tiny spec stub if direction unclear
4. Keep the PR small
