# 016 - Clean Tmp Action

**Purpose:** Empty the `~/git/lsimons/lsimons-tmp/` scratch directory so throwaway scripts and files do not accumulate.

**Requirements:**
- Delete all contents (files and subdirectories) of `~/git/lsimons/lsimons-tmp/`.
- Preserve the directory itself.
- Create the directory (with parents) if it does not exist.
- Run daily via the `start-the-day` routine.
- Support `--dry-run` to report what would be removed without deleting.

**Design Approach:**
- Follow the standard action script template (see `000-shared-patterns.md`).
- Target directory path is fixed (`~/git/lsimons/lsimons-tmp/`); no configuration needed.
- Use `pathlib` for path handling and `shutil.rmtree` for directory removal.
- Skip hidden dotfiles at the top level is **not** required — everything goes, because the directory is explicitly scratch space.
- Integrate into the daily routine by adding a `run_command(["auto", "clean-tmp"], ...)` call in `start_the_day.start_the_day()`. No separate LaunchAgent is needed.

**Implementation Notes:**
- Dependencies: standard library only (`pathlib`, `shutil`).
- Errors removing individual entries should be logged and skipped; the action should not abort on one bad entry.
- Exit code 0 on success (including when the directory was empty or freshly created).

**Status:** Implemented
