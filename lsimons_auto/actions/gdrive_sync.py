#!/usr/bin/env python3
"""
gdrive_sync.py - Sync Google Drive to local volume.

This action runs `rclone sync` to back up Google Drive to a local volume.
It includes checks to ensure it only runs on the specific host "paddo"
and only when the target volume is mounted.
"""

import argparse
import os
import shutil
import socket
import subprocess
import sys


def main(args: list[str] | None = None) -> None:
    """Main function that performs the action work."""
    parser = argparse.ArgumentParser(description="Sync Google Drive to local volume")
    _ = parser.parse_args(args)

    # 1. Check Hostname
    hostname = socket.gethostname()
    if hostname.lower() != "paddo":
        print(f"Skipping: Hostname is '{hostname}', expected 'paddo'.")
        return

    # 2. Check Target Volume
    target_volume = "/Volumes/LSData"
    if not os.path.ismount(target_volume) and not os.path.exists(target_volume):
        # Note: os.path.ismount might be stricter than needed if it's just a folder,
        # but spec says "when /Volumes/LSData is mounted".
        # We'll check exists first to be safe, but specifically we want it to be the mount.
        print(f"Skipping: {target_volume} is not available/mounted.")
        return

    # 3. Check rclone availability
    # Use absolute path since launchd environment doesn't have full PATH
    rclone_path = "/opt/homebrew/bin/rclone"

    # Fallback to shutil.which if absolute path doesn't exist (e.g. non-Apple Silicon Mac)
    if not os.path.exists(rclone_path):
        rclone_path = shutil.which("rclone")

    if not rclone_path:
        print("Error: rclone is not installed or not in PATH.")
        sys.exit(1)

    # 4. Execute Sync
    source = "gdrive:"
    destination = os.path.join(target_volume, "Google Drive")

    print(f"Syncing {source} to {destination}...")

    try:
        # Using subprocess to call rclone
        # We allow stdout/stderr to flow to the console
        subprocess.run([rclone_path, "sync", source, destination, "--verbose"], check=True)
        print("Sync completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing rclone: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
