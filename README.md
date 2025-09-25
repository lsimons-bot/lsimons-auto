# start_the_day.py

A lightweight daily startup script for macOS that helps you establish consistent morning routines.

## Features

- **Once-per-day execution**: Automatically tracks if it has already run today
- **Configurable**: Uses simple TOML configuration for state management
- **Colorized output**: Terminal-friendly with ANSI color support
- **Force mode**: Override daily limit when needed
- **Cross-platform paths**: Works with standard Unix path conventions

## Installation

Run the installation script to set up a convenient symlink:

```bash
python3 install.py
```

This creates `~/.local/bin/start-the-day` pointing to `start_the_day.py` (ensure `~/.local/bin` is in your PATH).

## Usage

```bash
# Run the daily routine
python3 start_the_day.py

# Force run even if already executed today
python3 start_the_day.py --force
```

## Configuration

The script stores execution state in `~/.start_the_day.toml` to track the last run date.

## Development

- See [AGENT.md](AGENT.md) for development guidelines and agent instructions
- See [DESIGN.md](DESIGN.md) for architectural decisions and design rationale
- Run tests after changes: `python3 test_start_the_day.py`

## Testing

Unit tests are located in `test_start_the_day.py`. Run them using any of these methods:

```bash
# Direct execution
python3 test_start_the_day.py

# Via unittest module
python3 -m unittest test_start_the_day

```

## Customization

Modify the `start_the_day()` function in `start_the_day.py` to add your own daily startup tasks.