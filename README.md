# lsimons-auto

A comprehensive personal automation toolkit for macOS that helps establish consistent daily routines and desktop organization through a modular command-line interface.

## Overview

The lsimons-auto project provides:
- **Unified CLI**: A single `auto` command that dispatches to various automation actions
- **Modular Actions**: Individual automation scripts that can run standalone or as subcommands
- **Daily Routines**: Automated morning startup sequences with configurable scheduling
- **Desktop Management**: Tools for organizing files and customizing desktop appearance
- **Spec-Based Development**: Structured approach to feature documentation and implementation

## Quick Start

```bash
# Install the automation toolkit
python3 install.py

# Run daily startup routine
start-the-day

# Use the auto CLI for other actions
auto organize-desktop
auto update-desktop-background
auto echo "Hello, World!"
```

## The `auto` Command

The `auto` command is a unified CLI that provides access to modular automation actions:

```bash
# See all available actions
auto --help

# Get help for a specific action
auto organize-desktop --help

# Run actions with arguments
auto echo --upper "hello world"
auto organize-desktop --dry-run
auto update-desktop-background --dry-run

start-the-day --help
```

## Available Actions

### Daily Routine (Separate Command)
- **`start-the-day`** - Daily startup routine with automated scheduling (separate from auto CLI)

### Auto CLI Actions
- **`organize-desktop`** - Organize Desktop files by creation date into dated directories
- **`update-desktop-background`** - Generate custom desktop background with current UTC time
- **`launch-apps`** - Launch a set of productivity and communication apps for your daily workflow
- **`echo`** - Simple echo utility for testing the command dispatcher

### Action Details
Auto CLI actions can be run either through the dispatcher or directly:
```bash
# Via auto dispatcher (recommended)
auto organize-desktop --dry-run

# Direct execution
python3 lsimons_auto/actions/organize_desktop.py --dry-run
```

The daily routine runs as a separate command:
```bash
start-the-day
start-the-day --force
```

## Installation

The installation script sets up both the daily automation and the CLI tool:

```bash
python3 install.py
```

This creates:
- `~/.local/bin/start-the-day` - Daily startup script with automated scheduling
- `~/.local/bin/auto` - CLI dispatcher for modular automation actions
- macOS LaunchAgent for automatic 7:00 AM daily execution of start-the-day
- Log directories in `~/.local/log/`

**Requirements**: This project uses `uv` for Python package management. Ensure `~/.local/bin` is in your PATH.

## Features

### Daily Automation
- **Once-per-day execution**: Automatically tracks if daily routine has already run
- **Automated scheduling**: macOS LaunchAgent runs the routine at 7:00 AM daily
- **Configurable state**: Uses TOML configuration for execution tracking
- **Force mode**: Override daily limit when needed with `--force`

### Desktop Organization
- **Date-based filing**: Automatically organizes Desktop files into `YYYY-MM-DD` directories
- **Smart file handling**: Preserves directory timestamps and handles various file types
- **Image optimization**: Compresses CleanShot images to save disk space
- **Text file conversion**: Converts `.txt` files to `.md` format
- **Safe operation**: Dry-run mode for testing before actual organization

### Desktop Customization
- **Dynamic backgrounds**: Generates desktop wallpapers with current UTC time
- **High-resolution support**: Optimized for modern macOS displays (2880x1800)
- **Monospace typography**: Uses programming fonts like JetBrains Mono for geeky aesthetic
- **Automatic cleanup**: Manages background image storage to prevent disk bloat

## Configuration

### Daily Routine State
The daily routine stores execution state in `~/.start_the_day.toml` to track the last run date.

### Background Images
Generated desktop backgrounds are stored in `~/.local/share/lsimons-auto/backgrounds/` with automatic cleanup of old files.

### Desktop Organization
Organized files are placed in dated directories on the Desktop (`~/Desktop/YYYY/MM/DD/`).

## Development

This project follows a spec-based development approach documented in [`docs/spec/`](docs/spec/).

### Development Guidelines
- See [CLAUDE.md](CLAUDE.md) for Claude Code-specific guidance
- See [AGENTS.md](AGENTS.md) for development guidelines and agent instructions
- See [DESIGN.md](DESIGN.md) for architectural decisions and design rationale
- Reference spec numbers in commit messages during feature implementation
- Run tests after changes: `uv run pytest`

### Adding New Actions
1. Create specification in `docs/spec/` following the established template
2. Implement action script in `lsimons_auto/actions/` following the standard pattern
3. Action scripts are automatically discovered by the `auto` command dispatcher
4. Add comprehensive tests and update documentation

## Testing

Unit and integration tests are located in `tests/`. Tests are separated by markers:

- **Unit tests**: Fast, no side effects, run by default
- **Integration tests**: End-to-end tests with real side effects (file I/O, subprocess calls)

```bash
# Run unit tests only (default, fast)
uv run pytest

# Run all tests including integration tests
uv run pytest -m ""

# Run only integration tests
uv run pytest -m integration

# Specific test file
uv run pytest tests/test_start_the_day.py

# With verbose output
uv run pytest -v
```

## System Management

### LaunchAgent Control
The automated daily routine can be managed via macOS LaunchAgent:

```bash
# Check status
launchctl list | grep com.leosimons.start-the-day

# Disable automatic execution
launchctl unload ~/Library/LaunchAgents/com.leosimons.start-the-day.plist

# Re-enable automatic execution
launchctl load ~/Library/LaunchAgents/com.leosimons.start-the-day.plist
```

### Logs
Execution logs are written to:
- `~/.local/log/start-the-day.log` - Standard output
- `~/.local/log/start-the-day-error.log` - Error output

## Customization

### Extending Daily Routines
Modify the `start_the_day()` function in `lsimons_auto/start_the_day.py` to add custom daily startup tasks.

### Creating Custom Actions
Follow the pattern in existing action scripts:
1. Create a new `.py` file in `lsimons_auto/actions/`
2. Implement a `main(args: Optional[list[str]] = None)` function
3. Add proper argument parsing and error handling
4. The action will automatically be available via `auto {action-name}`

## Dependencies

- **Python 3.13+** with `uv` package manager
- **macOS** (required for LaunchAgent automation and desktop management)
- **Pillow** - Image generation and processing
- **System fonts** - Monospace fonts for desktop background generation

## Architecture

The project uses a dual-command architecture:

### Daily Routine System
- **`start_the_day.py`** - Standalone daily routine script with automated scheduling
- **LaunchAgent integration** - macOS automation for consistent daily execution
- **Independent operation** - Runs separately from the auto CLI system

### Modular Actions System
- **`lsimons_auto.py`** - Command dispatcher that routes subcommands to action scripts
- **`actions/`** - Individual automation scripts that can run standalone or as subcommands
- **Dynamic discovery** - Auto CLI automatically detects new actions in the actions directory

### Development Framework
- **Spec-driven development** - All new features documented in `docs/spec/` before implementation

This dual architecture provides both reliable daily automation and flexible on-demand actions while maintaining clean separation between different functionality areas.
