# Gemini Code-Gen Agent Instructions

This document provides instructions for the Gemini code-generation agent to ensure consistent and high-quality contributions to the `lsimons-auto` project.

For general agent instructions that apply to all AI assistants, see [AGENTS.md](AGENTS.md).

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

### Code Style

- **Typing**: The project uses strict type checking with `pyright`. All new code must be fully type-hinted.
- **Formatting**: Follow standard Python formatting guidelines (PEP 8).
- **Modularity**: Actions should be self-contained and independent.

### Commits

- Reference the relevant spec number in commit messages (e.g., "feat(actions): Implement organize-desktop action (spec-004)").
