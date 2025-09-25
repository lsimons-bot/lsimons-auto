#!/usr/bin/env python3
"""
install.py - Installation script for start_the_day.py

This script:
1. Creates ~/.local/bin directory if it doesn't exist
2. Creates a symlink ~/.local/bin/start-the-day pointing to start_the_day.py
"""

import sys
from pathlib import Path


def main() -> None:
    """Main installation function."""
    # Get the absolute path to start_the_day.py in the same directory as this script
    script_dir = Path(__file__).parent.absolute()
    start_the_day_path = script_dir / "start_the_day.py"

    if not start_the_day_path.exists():
        print(f"Error: {start_the_day_path} not found")
        sys.exit(1)

    # Create ~/.local/bin directory if it doesn't exist
    local_bin_dir = Path.home() / ".local" / "bin"
    if not local_bin_dir.exists():
        print(f"Creating directory: {local_bin_dir}")
        local_bin_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Directory already exists: {local_bin_dir}")

    # Create symlink ~/.local/bin/start-the-day if it doesn't exist
    symlink_path = local_bin_dir / "start-the-day"

    if symlink_path.exists():
        if symlink_path.is_symlink():
            existing_target = symlink_path.readlink()
            if existing_target == start_the_day_path:
                print(
                    f"Symlink already exists and points to correct target: {symlink_path}"
                )
                return
            else:
                print(
                    f"Symlink exists but points to different target: {existing_target}"
                )
                print("Removing existing symlink and creating new one...")
                symlink_path.unlink()
        else:
            print(f"Error: {symlink_path} exists but is not a symlink")
            sys.exit(1)

    print(f"Creating symlink: {symlink_path} -> {start_the_day_path}")
    symlink_path.symlink_to(start_the_day_path)

    print("Installation completed successfully!")
    print(
        "You can now run 'start-the-day' from anywhere (if ~/.local/bin is in your PATH)"
    )


if __name__ == "__main__":
    main()
