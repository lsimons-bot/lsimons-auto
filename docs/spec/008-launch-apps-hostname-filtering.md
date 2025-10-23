# 008 - Launch Apps Hostname-Based Filtering

**Purpose:** Modify launch-apps action to launch a reduced set of applications when running on the "paddo" host

**Requirements:**
- Detect system hostname at runtime
- When hostname is "paddo", launch only: TextEdit, Ghostty, Zed, and IntelliJ IDEA
- When hostname is not "paddo", launch the full default set of applications
- Maintain existing command-line interface (--list, --help)
- No configuration files needed - hostname detection is automatic

**Design Approach:**
- Use `socket.gethostname()` from standard library to detect hostname
- Define two command sets: PADDO_COMMANDS and DEFAULT_COMMANDS
- Select appropriate command set based on hostname at runtime
- Preserve all existing functionality (background launching, error handling, logging)

**Implementation Notes:**
- PADDO_COMMANDS contains only 4 apps: TextEdit, Ghostty, Zed, IntelliJ IDEA
- DEFAULT_COMMANDS contains the full existing list
- Hostname comparison should be case-insensitive for robustness
- The --list flag should show the commands that would run on the current host

**Status:** Implemented