# 011 - Agent Action

**Purpose:** Manage multiple Claude Code CLI instances within Ghostty terminal with layout management and session orchestration

**Requirements:**
- Spawn a new Ghostty window with main agent pane and 1-4 configurable subagent panes
- Workspace selection from ~/git/{org}/{repo} structure with fuzzy matching
- Open workspace folder in Zed editor alongside Ghostty, with terminal panel open
- Position Ghostty and Zed windows to fill screen (not full screen mode)
- Send commands/text to specific agents or broadcast to all
- Focus, close, and list agent panes
- Kill entire session
- Persist session state across restarts

**Workspace Selection:**
- Scan ~/git for org directories, then repos within each org
- Accept `[org] [repo]` as positional arguments with fuzzy matching
- Fuzzy match: unambiguous partial matches auto-resolve (e.g., `lsimo auto` → `lsimons/lsimons-auto`)
- Interactive picker if no args or ambiguous match
- Working directory set to selected repo for all agent panes

**Layout Configuration:**
- Main agent always occupies the left portion
- 1 subagent: main (left half) | subagent (right half)
- 2 subagents: main (left half) | subagent-1 (top-right) / subagent-2 (bottom-right)
- 3 subagents: main (left half) | subagent-1 / subagent-2 / subagent-3 (stacked right)
- 4 subagents: main (left third) | subagent-1 / subagent-2 (middle) | subagent-3 / subagent-4 (right)

```
1 subagent:        2 subagents:       3 subagents:       4 subagents:
┌──────┬──────┐    ┌──────┬──────┐    ┌──────┬──────┐    ┌────┬────┬────┐
│      │      │    │      │  s1  │    │      │  s1  │    │    │ s1 │ s3 │
│ main │  s1  │    │ main ├──────┤    │      ├──────┤    │main├────┼────┤
│      │      │    │      │  s2  │    │ main │  s2  │    │    │ s2 │ s4 │
└──────┴──────┘    └──────┴──────┘    │      ├──────┤    └────┴────┴────┘
                                      │      │  s3  │
                                      └──────┴──────┘
```

**Design Approach:**
- Follow action script architecture from DESIGN.md (template in 000-shared-patterns.md)
- Use AppleScript via `osascript` for Ghostty window/pane control and window positioning
- Control via Ghostty keybindings: Cmd+D (split right), Cmd+Shift+D (split down)
- Launch Zed with `zed {workspace_path}`, then send Cmd+J via AppleScript to open terminal panel
- Position both Ghostty and Zed windows to fill the screen (overlapping, not full screen mode)
- Store session state in `~/.config/auto/agent/sessions/{session-id}.json`

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `spawn` | Create new agent layout (--subagents 1-4, --command, [org] [repo]) |
| `send` | Send text to specific agent |
| `broadcast` | Send text to all agents |
| `focus` | Focus agent by id/name/direction |
| `list` | List active sessions |
| `close` | Close specific agent pane |
| `kill` | Terminate session and close window |

**Implementation Notes:**
- macOS-only (requires Ghostty, Zed, and AppleScript accessibility permissions)
- Agent commands: `claude` (default), `pi`; configurable via --command
- Use 0.3s delay between AppleScript actions for reliability
- Agent naming: M-{repo} for main, 001-{repo}, 002-{repo}, etc. for subagents
- Session auto-naming: `auto-agent-{timestamp}`
- Fuzzy matching: case-insensitive substring match, fail if multiple matches
- Requires System Settings → Privacy & Security → Accessibility permission

**Status:** Draft
