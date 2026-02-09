#!/usr/bin/env python3
"""
lsimons_auto.py - Command dispatcher for lsimons-auto actions

This script acts as a unified CLI interface that routes subcommands to
corresponding action scripts in the actions/ directory.

See AGENTS.md for agent instructions and DESIGN.md for design decisions.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def discover_actions() -> dict[str, Path]:
    """Discover available action scripts in the actions directory.

    Returns a dict mapping CLI command names (with dashes) to script paths.
    E.g., 'git-sync' -> Path('.../actions/git_sync.py')
    """
    # Determine project root relative to this script file
    # This script is at lsimons_auto/lsimons_auto.py
    # So project root is the parent directory
    script_dir = Path(__file__).parent
    actions_dir = script_dir / "actions"
    actions: dict[str, Path] = {}

    if not actions_dir.exists():
        return actions

    for file_path in actions_dir.glob("*.py"):
        if file_path.name != "__init__.py":
            # Convert Python naming (underscores) to CLI naming (dashes)
            action_name = file_path.stem.replace("_", "-")
            actions[action_name] = file_path

    return actions


def normalize_action_name(name: str) -> str:
    """Normalize action name to CLI convention (dashes).

    Accepts both 'git-sync' and 'git_sync', returns 'git-sync'.
    """
    return name.replace("_", "-")


def main() -> None:
    """Main dispatcher function."""
    parser = argparse.ArgumentParser(description="lsimons-auto command dispatcher", prog="auto")

    actions = discover_actions()

    if not actions:
        print("Error: No actions found in actions directory")
        print(f"Expected location: {Path(__file__).parent / 'actions'}")
        sys.exit(1)

    # Parse arguments manually to handle unknown actions gracefully
    if len(sys.argv) < 2:
        parser.print_help()
        print("\nAvailable actions:")
        for name in sorted(actions.keys()):
            print(f"  {name:<24} Run {name} action")
        print("\nUse 'auto <action> --help' for help on a specific action")
        return

    action_input = sys.argv[1]
    remaining = sys.argv[2:]

    # Handle help for dispatcher
    if action_input in ["-h", "--help"]:
        parser.print_help()
        print("\nAvailable actions:")
        for name in sorted(actions.keys()):
            print(f"  {name:<24} Run {name} action")
        print("\nUse 'auto <action> --help' for help on a specific action")
        return

    # Normalize action name (accept both dashes and underscores)
    action_name = normalize_action_name(action_input)

    if action_name not in actions:
        print(f"Error: Unknown action '{action_input}'")
        print("\nAvailable actions:")
        for name in sorted(actions.keys()):
            print(f"  {name}")
        sys.exit(1)

    # Execute the action script using subprocess
    action_script = actions[action_name]
    cmd = [sys.executable, str(action_script)] + remaining

    try:
        result = subprocess.run(cmd, check=False)  # Don't raise on non-zero exit
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"Error: Action script not found: {action_script}")
        print("This usually indicates an installation or configuration problem.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error executing action '{action_name}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
