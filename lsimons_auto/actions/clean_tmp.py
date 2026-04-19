#!/usr/bin/env python3
"""
clean_tmp.py - Empty the ~/git/lsimons/lsimons-tmp/ scratch directory

Deletes all files and subdirectories inside ~/git/lsimons/lsimons-tmp/,
preserving the directory itself. Creates the directory if missing.
"""

import argparse
import shutil
import sys
from pathlib import Path

TMP_DIR = Path.home() / "git" / "lsimons" / "lsimons-tmp"


def clean_tmp_dir(tmp_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    """Remove all entries inside tmp_dir, returning (removed, errors)."""
    if not tmp_dir.exists():
        if dry_run:
            print(f"Would create directory: {tmp_dir}")
        else:
            print(f"Creating directory: {tmp_dir}")
            tmp_dir.mkdir(parents=True, exist_ok=True)
        return (0, 0)

    removed = 0
    errors = 0
    for entry in tmp_dir.iterdir():
        try:
            if dry_run:
                kind = "directory" if entry.is_dir() and not entry.is_symlink() else "file"
                print(f"Would remove {kind}: {entry}")
                removed += 1
                continue

            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            removed += 1
        except OSError as e:
            print(f"Warning: could not remove {entry}: {e}", file=sys.stderr)
            errors += 1

    return (removed, errors)


def main(args: list[str] | None = None) -> None:
    """Entry point for the clean-tmp action."""
    parser = argparse.ArgumentParser(
        description=f"Empty the {TMP_DIR} scratch directory (keep the directory itself)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything",
    )
    parsed_args = parser.parse_args(args)

    removed, errors = clean_tmp_dir(TMP_DIR, dry_run=parsed_args.dry_run)

    if parsed_args.dry_run:
        print(f"Dry run complete: {removed} entries would be removed")
    else:
        print(f"Cleanup complete: removed {removed} entries, {errors} errors")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
