# 009 - Git Sync Action

**Purpose:** Synchronize git repositories from GitHub for configured owners (e.g., `lsimons`, `typelinkmodel`, `LAB271`) to the local machine.

**Requirements:**
- Support multiple GitHub owners/organizations.
- Configurable local directories (e.g., `~/git/labs` instead of `~/git/LAB271`).
- Fetch list of repositories using `gh` CLI (limit 200).
  - Active repos: `isFork == false && isArchived == false` -> `~/git/<local_dir>`
  - Archived repos: `isFork == false && isArchived == true` -> `~/git/<local_dir>/archive`
- Flags:
  - `--include-archive`: Sync archived repositories (default: false).
  - `--dry-run`: Print what would be done without executing commands.
  - `-o`/`--owner`: Sync only a specific owner (default: all).
- Configuration per owner:
  - `local_dir`: Optional custom directory name.
  - `allow_archived`: Whether to allow syncing archived repos (even if flag is set).
- For each repository:
  - If it doesn't exist locally: `git clone`
  - If it exists locally: `git fetch --all`
- Suppress git output unless there is an error (non-zero exit code).

**Design Approach:**
- Use `subprocess` to call `gh` and `git` commands.
- Parse `gh` output (JSON) to get repository lists.
- Define `OwnerConfig` named tuple for owner-specific settings.
- Iterate through configured owners (or filtered list) and perform sync operations.
- Use a helper function for running shell commands that handles output buffering and error reporting.

**Implementation Notes:**
- Dependencies: `gh` (GitHub CLI) must be installed and authenticated. `git` must be installed.
- Error handling: If `gh` fails, abort. If a single repo fails to sync, log error and continue with others.
- Path handling: Use `pathlib` for all path manipulations.
- The action name is `git_sync.py` (maps to `auto git-sync`).

**Fork Remote Configuration (lsimons-bot):**
- When authenticated as `lsimons-bot`, automatically configures fork remotes using origin/upstream pattern
- Detects authenticated user via `gh api user`
- If user is `lsimons-bot`, fetches list of all forks owned by that user
- For each synced repository that has a fork:
  - Configures `origin` remote → fork URL (lsimons-bot's fork)
  - Configures `upstream` remote → original URL (parent repo)
  - Sets GitHub CLI repo config:
    - Push destination: `origin` (fork)
    - Pull request base: `upstream` (parent repo)
- Example valid setup:
  ```
  origin    https://github.com/lsimons-bot/repo-name.git (fetch/push)
  upstream  https://github.com/original-org/repo-name.git (fetch/push)
  ```
- All fork operations are best-effort (failures don't block main sync):
  - Missing `gh` CLI skips fork configuration
  - GitHub API errors are reported but sync continues
  - Per-repo fork failures warn but continue to next repo
- Respects `--dry-run` flag (prints what would be done)
- Idempotent: checks for existing remotes before reconfiguring

**Status:** Implemented
