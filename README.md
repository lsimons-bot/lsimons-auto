# start_the_day.py

A lightweight daily startup script for macOS that helps you establish consistent morning routines.

## Features

- **Once-per-day execution**: Automatically tracks if it has already run today
- **Configurable**: Uses simple TOML configuration for state management
- **Colorized output**: Terminal-friendly with ANSI color support
- **Force mode**: Override daily limit when needed
- **Cross-platform paths**: Works with standard Unix path conventions

## Installation

Run the installation script to set up a convenient symlink and daily automation:

```bash
python3 install.py
```

This:
- Creates `~/.local/bin/start-the-day` pointing to `start_the_day.py` (ensure `~/.local/bin` is in your PATH)
- Installs a macOS LaunchAgent to run the script automatically at 7:00 AM daily
- Creates `~/.local/log/` directory for execution logs

**Note**: This project uses `uv` for Python package management and virtual environment handling. While the script can run with standard Python, using `uv` is recommended for dependency management.

## Usage

```bash
# Using uv (recommended)
uv run start_the_day.py

# Run the daily routine
python3 start_the_day.py

# Force run even if already executed today
python3 start_the_day.py --force
```

## Configuration

The script stores execution state in `~/.start_the_day.toml` to track the last run date.

## Automation

After installation, the script runs automatically via macOS LaunchAgent:
- **Schedule**: Daily at 7:00 AM
- **Logs**: Written to `~/.local/log/start-the-day.log` and `~/.local/log/start-the-day-error.log`
- **Management**: Use `launchctl` to control the service:
  ```bash
  # Check status
  launchctl list | grep com.leosimons.start-the-day

  # Unload (disable)
  launchctl unload ~/Library/LaunchAgents/com.leosimons.start-the-day.plist

  # Load (re-enable)
  launchctl load ~/Library/LaunchAgents/com.leosimons.start-the-day.plist
  ```

## Development

- See [AGENT.md](AGENT.md) for development guidelines and agent instructions
- See [DESIGN.md](DESIGN.md) for architectural decisions and design rationale
- Run tests after changes: `uv run pytest`

## Testing

Unit tests are located in `test_start_the_day.py`. Run them using any of these methods:

```bash
# Using uv with pytest (recommended)
uv run pytest

# Using uv with specific test file
uv run pytest test_start_the_day.py

# Direct execution (legacy)
python3 test_start_the_day.py
```

## Customization

Modify the `start_the_day()` function in `start_the_day.py` to add your own daily startup tasks.
