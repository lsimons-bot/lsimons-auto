#!/usr/bin/env python3
"""
git_sync.py - Synchronize GitHub repositories

This action fetches repositories for configured owners and syncs them locally.
Active repos go to ~/git/<owner> (or configured local dir).
Archived repos go to ~/git/<owner>/archive (if enabled).
"""

import argparse
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional, NamedTuple


class OwnerConfig(NamedTuple):
    name: str
    local_dir: Optional[str] = None
    allow_archived: bool = True
    hostname_filter: Optional[str] = None


OWNER_CONFIGS = [
    OwnerConfig(name="lsimons"),
    OwnerConfig(name="typelinkmodel"),
    OwnerConfig(name="LAB271", local_dir="labs", allow_archived=False, hostname_filter="sbp"),
]


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> bool:
    """
    Run a shell command.
    Returns True if successful, False otherwise.
    Output is suppressed unless the command fails.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        if cwd:
            print(f"  Directory: {cwd}")
        print("  Output:")
        print(e.stdout)
        return False


def get_repos(owner: str, archive: bool = False) -> list[str]:
    """Fetch list of repositories using gh CLI."""
    # gh repo list owner -L 200 --json name,isFork,isArchived
    cmd = [
        "gh",
        "repo",
        "list",
        owner,
        "-L",
        "200",
        "--json",
        "name,isFork,isArchived",
    ]
    try:
        result = subprocess.run(
            cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        repos_data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repo list: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing gh output: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'gh' command not found. Please install GitHub CLI.")
        sys.exit(1)

    # Filter repos
    # .[] | select(.isFork == false && .isArchived == false) | .name
    filtered_repos = []
    for repo in repos_data:
        if repo.get("isFork") is True:
            continue
        
        is_repo_archived = repo.get("isArchived", False)
        if archive and is_repo_archived:
            filtered_repos.append(repo["name"])
        elif not archive and not is_repo_archived:
            filtered_repos.append(repo["name"])

    return filtered_repos


def sync_repo(owner: str, repo_name: str, target_dir: Path) -> bool:
    """
    Sync a single repository.
    Returns True if successful, False otherwise.
    """
    repo_path = target_dir / repo_name
    success = False
    
    if repo_path.exists():
        # git fetch --all
        print(f"Updating {owner}/{repo_name}...")
        success = run_command(["git", "fetch", "--all"], cwd=repo_path)
    else:
        # git clone
        print(f"Cloning {owner}/{repo_name}...")
        repo_url = f"https://github.com/{owner}/{repo_name}.git"
        success = run_command(["git", "clone", repo_url], cwd=target_dir)

    if not success:
        print(f"Failed to sync {owner}/{repo_name}")
    
    return success


def fetch_directory_repos(
    directory: Path, visited_repos: set[Path], dry_run: bool = False
) -> None:
    """Run git fetch on all git repositories in a directory that haven't been visited."""
    if not directory.exists():
        return

    print(f"Scanning {directory} for additional repositories...")
    
    # Iterate over subdirectories
    for item in directory.iterdir():
        if not item.is_dir():
            continue
            
        # Check if it's a git repo
        if (item / ".git").exists():
            if item.resolve() in visited_repos:
                continue
                
            if dry_run:
                print(f"Would fetch existing repo: {item}")
            else:
                print(f"Fetching existing repo: {item.name}...")
                run_command(["git", "fetch", "--all"], cwd=item)


def main(args: Optional[list[str]] = None) -> None:
    """Main function that performs the action work."""
    available_owners = ", ".join(cfg.name for cfg in OWNER_CONFIGS)
    parser = argparse.ArgumentParser(
        description=f"Synchronize GitHub repositories. Available owners: {available_owners}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print what would be done without doing it"
    )
    parser.add_argument(
        "--include-archive",
        action="store_true",
        help="Include archived repositories in the sync",
    )
    parser.add_argument(
        "-o",
        "--owner",
        help="Specific owner to sync (default: all)",
        choices=[cfg.name for cfg in OWNER_CONFIGS],
    )
    parsed_args = parser.parse_args(args)

    base_dir = Path.home() / "git"

    # Filter owners if specific one requested
    if parsed_args.owner:
        configs_to_process = [
            cfg for cfg in OWNER_CONFIGS if cfg.name == parsed_args.owner
        ]
    else:
        configs_to_process = OWNER_CONFIGS

    current_hostname = socket.gethostname()

    for config in configs_to_process:
        # Check hostname filter
        if config.hostname_filter and not current_hostname.startswith(config.hostname_filter):
            print(f"Skipping {config.name}: Hostname '{current_hostname}' does not start with '{config.hostname_filter}'.")
            continue

        owner = config.name
        # Use custom local directory if specified, otherwise use owner name
        local_dirname = config.local_dir if config.local_dir else owner
        owner_dir = base_dir / local_dirname
        archive_dir = owner_dir / "archive"
        
        # Track visited repos to avoid double-fetching
        visited_repos: set[Path] = set()

        # Create directories
        if not parsed_args.dry_run:
            owner_dir.mkdir(parents=True, exist_ok=True)
            # Only create archive dir if we might use it
            if parsed_args.include_archive and config.allow_archived:
                archive_dir.mkdir(parents=True, exist_ok=True)
        else:
            dirs_to_create = [str(owner_dir)]
            if parsed_args.include_archive and config.allow_archived:
                dirs_to_create.append(str(archive_dir))
            print(f"Would create directories: {', '.join(dirs_to_create)}")

        # Sync active repos
        print(f"Fetching active repository list for {owner}...")
        active_repos = get_repos(owner=owner, archive=False)
        print(f"Found {len(active_repos)} active repositories for {owner}.")

        for repo in active_repos:
            repo_path = (owner_dir / repo).resolve()
            visited_repos.add(repo_path)
            
            if parsed_args.dry_run:
                print(f"Would sync active repo: {owner}/{repo} to {owner_dir}")
            else:
                sync_repo(owner, repo, owner_dir)

        # Sync archived repos
        if parsed_args.include_archive:
            if config.allow_archived:
                print(f"Fetching archived repository list for {owner}...")
                archived_repos = get_repos(owner=owner, archive=True)
                print(f"Found {len(archived_repos)} archived repositories for {owner}.")

                for repo in archived_repos:
                    repo_path = (archive_dir / repo).resolve()
                    visited_repos.add(repo_path)

                    if parsed_args.dry_run:
                        print(f"Would sync archived repo: {owner}/{repo} to {archive_dir}")
                    else:
                        sync_repo(owner, repo, archive_dir)
            else:
                print(f"Skipping archived repositories for {owner} (configured to ignore)")
        
        # Sync any other existing repos in the directories
        fetch_directory_repos(owner_dir, visited_repos, parsed_args.dry_run)
        
        # Only scan archive directory if archives are included
        if parsed_args.include_archive and archive_dir.exists():
            fetch_directory_repos(archive_dir, visited_repos, parsed_args.dry_run)


if __name__ == "__main__":
    main()
