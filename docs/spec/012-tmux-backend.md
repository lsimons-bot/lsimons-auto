# 012 - tmux Backend for Agent Sessions

**Purpose:** Replace AppleScript/Ghostty pane management with tmux for reliable operation in VMs and resource-constrained environments

**Requirements:**
- Replace all AppleScript-based terminal control with tmux commands
- Maintain all existing agent subcommands (spawn, send, broadcast, focus, list, close, kill)
- Keep worktree isolation, session persistence, and workspace discovery unchanged
- Support same layout configurations (1-4 subagents)
- Work reliably without UI timing delays

**Design Approach:**
- Create `tmux.py` module as drop-in replacement for `ghostty.py`
- Use tmux session per agent session (named `auto-agent-{timestamp}`)
- Use tmux windows and panes for layout management
- Store tmux pane IDs in session state for direct addressing
- Use `tmux send-keys` for text input (no AppleScript keystroke delays)
- Use `tmux split-window`, `tmux select-pane` for layout/navigation

**Layout Mapping:**

| Layout | tmux Implementation |
|--------|---------------------|
| main \| s1 | 2 panes: horizontal split (50/50) |
| main \| s1/s2 | 3 panes: main left, s1 top-right, s2 bottom-right |
| main \| s1/s2/s3 | 4 panes: main left, s1/s2/s3 stacked right |
| main \| s1/s2 \| s3/s4 | 5 panes: main left third, s1/s2 middle, s3/s4 right |

**tmux Commands Used:**
- `tmux new-session -d -s {session} -c {dir}` - Create detached session
- `tmux split-window -h/-v -t {target} -c {dir}` - Split horizontally/vertically
- `tmux select-pane -t {target}` - Focus pane
- `tmux send-keys -t {target} {text} Enter` - Send text with enter
- `tmux kill-pane -t {target}` - Close pane
- `tmux kill-session -t {session}` - Kill entire session
- `tmux list-panes -t {session} -F '#{pane_id}'` - List pane IDs
- `tmux attach-session -t {session}` - Attach to session

**Session State Changes:**
- Add `tmux_session_name: str` to AgentSession
- Add `tmux_pane_id: str` to AgentPane (e.g., `%0`, `%1`)
- Remove `window_id` (Ghostty-specific)

**CLI Changes:**
- Add `--attach` flag to `spawn` command (default: true)
- Spawn creates session detached, then attaches at end
- All pane operations use tmux pane IDs for direct targeting

**Zed Integration:**
- Keep Zed launch via `zed {workspace_path}` subprocess
- Remove window positioning (user can arrange manually)
- Optionally skip Zed entirely with `--no-zed`

**Implementation Notes:**
- tmux must be installed (`brew install tmux` on macOS)
- No AppleScript permissions required
- No timing delays needed - tmux commands are synchronous
- Works over SSH and in VMs without GUI
- Pane targeting by ID eliminates navigation complexity

**Migration:**
- Existing sessions using Ghostty/AppleScript are incompatible
- Users should `auto agent kill` existing sessions before upgrading
- Session file format changes (new fields, removed window_id)

**Status:** Implemented
