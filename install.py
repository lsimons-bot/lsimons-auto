#!/usr/bin/env python3
"""
install.py - Installation script for lsimons-auto

This script:
1. Creates ~/.local/bin directory if it doesn't exist
2. Creates a symlink ~/.local/bin/start-the-day pointing to start_the_day.py
3. Creates a symlink ~/.local/bin/auto pointing to lsimons_auto.py
4. Creates ~/.local/log directory for LaunchAgent logs
5. Installs macOS LaunchAgent plist for daily 7am execution
"""

import os
import subprocess
import sys
from pathlib import Path


def install_scripts() -> None:
    """Install the start-the-day and auto wrapper scripts."""
    # Get the absolute path to scripts in the lsimons_auto directory
    script_dir = Path(__file__).parent.absolute()
    start_the_day_path = script_dir / "lsimons_auto" / "start_the_day.py"
    lsimons_auto_path = script_dir / "lsimons_auto" / "lsimons_auto.py"
    venv_python = script_dir / ".venv" / "bin" / "python"

    if not start_the_day_path.exists():
        print(f"Error: {start_the_day_path} not found")
        sys.exit(1)

    if not lsimons_auto_path.exists():
        print(f"Error: {lsimons_auto_path} not found")
        sys.exit(1)

    if not venv_python.exists():
        print(f"Error: Virtual environment Python not found at {venv_python}")
        print("Run 'uv sync' first to create the virtual environment")
        sys.exit(1)

    # Create ~/.local/bin directory if it doesn't exist
    local_bin_dir = Path.home() / ".local" / "bin"
    if not local_bin_dir.exists():
        print(f"Creating directory: {local_bin_dir}")
        local_bin_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Directory already exists: {local_bin_dir}")

    # Install start-the-day wrapper script
    install_wrapper_script(venv_python, start_the_day_path, local_bin_dir / "start-the-day")

    # Install auto wrapper script
    install_wrapper_script(venv_python, lsimons_auto_path, local_bin_dir / "auto")


def install_wrapper_script(venv_python: Path, target_script: Path, wrapper_path: Path) -> None:
    """Install a wrapper script that uses the project's virtual environment Python."""
    # Create wrapper script content
    wrapper_content = f"""#!/bin/bash
# Auto-generated wrapper script for lsimons-auto
# Uses project virtual environment to ensure dependencies are available
exec "{venv_python}" "{target_script}" "$@"
"""

    # Handle existing files
    if wrapper_path.exists() or wrapper_path.is_symlink():
        if wrapper_path.exists() and wrapper_path.read_text().strip() == wrapper_content.strip():
            print(f"Wrapper script already up-to-date: {wrapper_path}")
            return
        else:
            print(f"Updating existing wrapper script (overwriting): {wrapper_path}")
            wrapper_path.unlink()

    # Create the wrapper script
    print(f"Creating wrapper script: {wrapper_path}")
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)  # Make executable


def install_launch_agent() -> None:
    """Install macOS LaunchAgents."""
    # Create ~/.local/log directory for LaunchAgent logs
    local_log_dir = Path.home() / ".local" / "log"
    if not local_log_dir.exists():
        print(f"Creating directory: {local_log_dir}")
        local_log_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Directory already exists: {local_log_dir}")

    # Get current user's username for plist template
    username = os.environ.get("USER", "unknown")

    # Get the absolute path to the plist template
    script_dir = Path(__file__).parent.absolute()

    # List of plist templates to install
    plist_files = ["com.leosimons.start-the-day.plist", "com.leosimons.gdrive-sync.plist"]

    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    if not launch_agents_dir.exists():
        print(f"Creating directory: {launch_agents_dir}")
        launch_agents_dir.mkdir(parents=True, exist_ok=True)

    for plist_file in plist_files:
        plist_template_path = script_dir / "etc" / plist_file

        if not plist_template_path.exists():
            print(f"Error: {plist_template_path} not found")
            continue

        # Read plist template and replace username
        plist_content = plist_template_path.read_text()
        plist_content = plist_content.replace("/Users/lsimons/", f"/Users/{username}/")

        plist_dest_path = launch_agents_dir / plist_file

        # Write the customized plist
        print(f"Installing LaunchAgent: {plist_dest_path}")
        plist_dest_path.write_text(plist_content)

        # Load the LaunchAgent
        print(f"Loading LaunchAgent {plist_file}...")
        # Unload first to ensure reload works if it changed
        subprocess.run(
            ["launchctl", "unload", str(plist_dest_path)],
            stderr=subprocess.DEVNULL,
            check=False,
        )
        result = subprocess.run(["launchctl", "load", str(plist_dest_path)], check=False)
        if result.returncode == 0:
            print(f"LaunchAgent {plist_file} loaded successfully!")
        else:
            print(f"Warning: Failed to load LaunchAgent {plist_file}.")


def main() -> None:
    """Main installation function."""
    print("Installing lsimons-auto...")

    install_scripts()
    install_launch_agent()

    print("\nInstallation completed successfully!")
    print("- You can now run 'start-the-day' from anywhere (if ~/.local/bin is in your PATH)")
    print("- You can now run 'auto' from anywhere (if ~/.local/bin is in your PATH)")
    print("- Scripts use project virtual environment to ensure dependencies are available")
    print("- The start-the-day script will automatically run daily at 7:00 AM via LaunchAgent")
    print("- Logs will be written to ~/.local/log/start-the-day.log")
    print("- Use 'auto --help' to see available actions")


if __name__ == "__main__":
    main()
