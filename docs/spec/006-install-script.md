# 006 - Installation Script

## Overview
This specification documents the `install.py` script that provides automated installation and setup of the lsimons-auto personal automation toolkit, including CLI wrappers, LaunchAgent configuration, and directory structure creation.

## Status
- [x] Draft
- [x] Under Review  
- [x] Approved
- [x] In Progress
- [x] Implemented
- [ ] Deprecated

## Motivation
A robust installation process is essential for:
- Seamless setup of the automation toolkit on new systems
- Proper integration with macOS system services (LaunchAgent)
- Creation of necessary directory structures and configuration files
- Installation of CLI wrapper scripts that use the project's virtual environment
- Automated configuration of daily execution scheduling
- User-friendly installation experience without manual configuration steps

## Requirements

### Functional Requirements
1. **Script Installation**: Create executable wrapper scripts for `start-the-day` and `auto` commands
2. **Virtual Environment Integration**: Ensure wrapper scripts use the project's `.venv/bin/python`
3. **Directory Creation**: Create necessary directories (`~/.local/bin`, `~/.local/log`)
4. **LaunchAgent Setup**: Install and configure macOS LaunchAgent for daily automation
5. **User-specific Configuration**: Replace template placeholders with current user information
6. **Idempotent Operation**: Handle existing installations gracefully without errors
7. **Dependency Validation**: Check for required dependencies before installation
8. **Status Reporting**: Provide clear feedback about installation progress and results

### Non-Functional Requirements
1. **Reliability**: Must work consistently across different macOS versions and user configurations
2. **Safety**: Graceful handling of existing files and configurations without data loss
3. **User Experience**: Clear, informative output with helpful error messages
4. **Maintainability**: Modular design allowing easy addition of new installation steps
5. **Robustness**: Proper error handling for file system operations and system commands

## Design

### Architecture Overview
The installation script operates in three main phases:

1. **Script Installation Phase**: Creates wrapper scripts that execute Python modules using the project's virtual environment
2. **LaunchAgent Installation Phase**: Sets up macOS LaunchAgent for automated daily execution
3. **Validation Phase**: Confirms successful installation and provides usage instructions

### Core Components

#### Wrapper Script Generation
- **Template-based Generation**: Creates bash wrapper scripts with embedded paths
- **Virtual Environment Integration**: Uses project `.venv/bin/python` for execution
- **Argument Forwarding**: Passes all command-line arguments to target Python scripts
- **Executable Permissions**: Sets appropriate file permissions (0o755)

#### LaunchAgent Management
- **Template Processing**: Customizes LaunchAgent plist with current user information
- **System Integration**: Installs to `~/Library/LaunchAgents/` directory
- **Automatic Loading**: Attempts to load LaunchAgent via `launchctl`
- **Error Recovery**: Provides manual instructions if automatic loading fails

#### Directory Structure Management
- **Standard Locations**: Creates directories following Unix conventions (`~/.local/`)
- **Recursive Creation**: Creates parent directories as needed
- **Existence Checking**: Handles existing directories without errors
- **Permission Validation**: Ensures directories are writable

### Installation Target Structure
```
~/.local/
├── bin/
│   ├── start-the-day        # Wrapper script for daily routine
│   └── auto                 # Wrapper script for CLI dispatcher
├── log/                     # Log directory for LaunchAgent output
└── share/lsimons-auto/      # Created by actions, not install script
    └── backgrounds/

~/Library/LaunchAgents/
└── com.leosimons.start-the-day.plist  # Daily automation configuration
```

### Wrapper Script Template
```bash
#!/bin/bash
# Auto-generated wrapper script for lsimons-auto
# Uses project virtual environment to ensure dependencies are available
exec "{venv_python}" "{target_script}" "$@"
```

## Implementation Details

### Main Installation Flow

#### Primary Entry Point
```python
def main() -> None:
    """Main installation function."""
    print("Installing lsimons-auto...")
    
    install_scripts()
    install_launch_agent()
    
    print("\nInstallation completed successfully!")
    # ... success messages
```

#### Script Installation Logic
```python
def install_scripts() -> None:
    """Install the start-the-day and auto wrapper scripts."""
    # Path resolution and validation
    script_dir = Path(__file__).parent.absolute()
    start_the_day_path = script_dir / "lsimons_auto" / "start_the_day.py"
    lsimons_auto_path = script_dir / "lsimons_auto" / "lsimons_auto.py"
    venv_python = script_dir / ".venv" / "bin" / "python"
    
    # Dependency validation
    if not start_the_day_path.exists():
        print(f"Error: {start_the_day_path} not found")
        sys.exit(1)
    
    # Directory creation
    local_bin_dir = Path.home() / ".local" / "bin"
    local_bin_dir.mkdir(parents=True, exist_ok=True)
    
    # Wrapper script installation
    install_wrapper_script(venv_python, start_the_day_path, local_bin_dir / "start-the-day")
    install_wrapper_script(venv_python, lsimons_auto_path, local_bin_dir / "auto")
```

#### Wrapper Script Creation
```python
def install_wrapper_script(venv_python: Path, target_script: Path, wrapper_path: Path) -> None:
    """Install a wrapper script that uses the project's virtual environment Python."""
    wrapper_content = f"""#!/bin/bash
# Auto-generated wrapper script for lsimons-auto
# Uses project virtual environment to ensure dependencies are available
exec "{venv_python}" "{target_script}" "$@"
"""
    
    # Handle existing files
    if wrapper_path.exists():
        if wrapper_path.read_text().strip() == wrapper_content.strip():
            print(f"Wrapper script already up-to-date: {wrapper_path}")
            return
        else:
            print(f"Updating existing wrapper script: {wrapper_path}")
            wrapper_path.unlink()
    
    # Create and make executable
    print(f"Creating wrapper script: {wrapper_path}")
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)
```

#### LaunchAgent Installation
```python
def install_launch_agent() -> None:
    """Install macOS LaunchAgent for daily execution."""
    # Log directory creation
    local_log_dir = Path.home() / ".local" / "log"
    local_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Username resolution
    username = os.environ.get("USER", "unknown")
    
    # Template processing
    script_dir = Path(__file__).parent.absolute()
    plist_template_path = script_dir / "etc" / "com.leosimons.start-the-day.plist"
    plist_content = plist_template_path.read_text()
    plist_content = plist_content.replace("/Users/lsimons/", f"/Users/{username}/")
    
    # Installation and loading
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    plist_dest_path = launch_agents_dir / "com.leosimons.start-the-day.plist"
    plist_dest_path.write_text(plist_content)
    
    # LaunchAgent activation
    result = os.system(f"launchctl load {plist_dest_path}")
    if result != 0:
        print("Warning: Failed to load LaunchAgent. Manual loading required.")
```

### Error Handling Strategy

#### Dependency Validation
The script validates all required dependencies before proceeding:
- Python script files existence (`start_the_day.py`, `lsimons_auto.py`)
- Virtual environment Python interpreter
- LaunchAgent template plist file
- Write permissions for target directories

#### Graceful Degradation
- Continues installation if non-critical steps fail
- Provides clear error messages with remediation instructions
- Exits early only for critical dependency failures
- Offers manual alternatives for automated steps that fail

#### File System Operations
- Uses `Path.mkdir(parents=True, exist_ok=True)` for safe directory creation
- Checks existing file content before overwriting
- Handles permission errors with informative messages
- Uses atomic write operations where possible

### Template System

#### LaunchAgent Template
Located at `etc/com.leosimons.start-the-day.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.leosimons.start-the-day</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/lsimons/.local/bin/start-the-day</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/lsimons/.local/log/start-the-day.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/lsimons/.local/log/start-the-day-error.log</string>
</dict>
</plist>
```

#### Username Substitution
The template uses `/Users/lsimons/` as a placeholder that gets replaced with `/Users/{current_username}/` during installation, ensuring the LaunchAgent works for any user.

### Virtual Environment Integration

#### Why Wrapper Scripts
Direct symlinks to Python scripts would use the system Python interpreter, potentially missing project dependencies. Wrapper scripts ensure:
- Project virtual environment is always used
- Dependencies are available at runtime
- Python path is correctly configured
- Environment variables are preserved

#### Wrapper Script Benefits
- **Dependency Isolation**: Uses project-specific virtual environment
- **Path Independence**: Works regardless of where project is installed
- **Argument Forwarding**: Transparent to users (all args passed through)
- **Shell Integration**: Appears as native shell commands
- **Update Resilience**: Wrapper content only changes when paths change

## Testing Strategy

### Unit Tests
- **Path Resolution**: Test script and dependency path detection
- **Directory Creation**: Test directory creation with various permission scenarios
- **Template Processing**: Test username substitution in LaunchAgent template
- **Wrapper Script Generation**: Test wrapper script content and permissions
- **Error Handling**: Test behavior with missing dependencies and write permissions

### Integration Tests
- **End-to-End Installation**: Test complete installation process in clean environment
- **Idempotent Behavior**: Test repeated installations don't cause errors
- **LaunchAgent Integration**: Test LaunchAgent installation and loading
- **Wrapper Script Execution**: Test that generated wrapper scripts work correctly
- **Cross-User Compatibility**: Test installation with different usernames

### Test Implementation Considerations
- **Temporary Directories**: Use temporary paths for file system tests
- **Mock System Commands**: Mock `launchctl` and `os.system` calls for testing
- **Permission Testing**: Test behavior with read-only directories
- **Cleanup**: Ensure test artifacts are cleaned up after test runs
- **User Environment**: Test with different `USER` environment variable values

### Manual Testing Checklist
- [ ] Fresh macOS system installation
- [ ] Installation with existing `~/.local/bin` directory
- [ ] Installation with existing wrapper scripts
- [ ] Installation with existing LaunchAgent
- [ ] Re-installation after manual modifications
- [ ] Installation with non-standard username characters
- [ ] Wrapper script execution after installation
- [ ] LaunchAgent execution at scheduled time

## Usage Examples

### Standard Installation
```bash
# From project root directory
python3 install.py
```

### Expected Output
```
Installing lsimons-auto...
Creating directory: /Users/username/.local/bin
Creating wrapper script: /Users/username/.local/bin/start-the-day
Creating wrapper script: /Users/username/.local/bin/auto
Creating directory: /Users/username/.local/log
Installing LaunchAgent: /Users/username/Library/LaunchAgents/com.leosimons.start-the-day.plist
Loading LaunchAgent...
LaunchAgent loaded successfully!

Installation completed successfully!
- You can now run 'start-the-day' from anywhere (if ~/.local/bin is in your PATH)
- You can now run 'auto' from anywhere (if ~/.local/bin is in your PATH)
- Scripts use project virtual environment to ensure dependencies are available
- The start-the-day script will automatically run daily at 7:00 AM via LaunchAgent
- Logs will be written to ~/.local/log/start-the-day.log
- Use 'auto --help' to see available actions
```

### Verification Commands
```bash
# Verify wrapper scripts exist and are executable
ls -la ~/.local/bin/start-the-day ~/.local/bin/auto

# Test wrapper scripts
~/.local/bin/start-the-day --help
~/.local/bin/auto --help

# Check LaunchAgent installation
ls -la ~/Library/LaunchAgents/com.leosimons.start-the-day.plist
launchctl list | grep com.leosimons.start-the-day

# Verify log directory
ls -la ~/.local/log/
```

## Troubleshooting

### Common Issues

#### Missing Virtual Environment
**Error**: `Error: Virtual environment Python not found at /path/to/.venv/bin/python`
**Solution**: Run `uv sync` to create the virtual environment before installation

#### Permission Denied
**Error**: `Permission denied when creating ~/.local/bin`
**Solution**: Check home directory permissions and disk space

#### LaunchAgent Load Failure
**Error**: `Warning: Failed to load LaunchAgent`
**Solution**: Manually load with `launchctl load ~/Library/LaunchAgents/com.leosimons.start-the-day.plist`

#### PATH Issues
**Error**: `command not found: start-the-day`
**Solution**: Ensure `~/.local/bin` is in your PATH or use full path `~/.local/bin/start-the-day`

### Debugging Commands
```bash
# Check installation directory
ls -la ~/.local/bin/

# Check LaunchAgent status
launchctl list | grep start-the-day
launchctl print gui/$(id -u)/com.leosimons.start-the-day

# Test wrapper scripts directly
~/.local/bin/start-the-day
~/.local/bin/auto --help

# Check Python virtual environment
ls -la /path/to/project/.venv/bin/python
/path/to/project/.venv/bin/python --version
```

## Maintenance and Updates

### Updating Installation
Re-running `install.py` is safe and will:
- Update wrapper scripts if paths have changed
- Skip creation of existing directories
- Update LaunchAgent configuration if template has changed
- Reload LaunchAgent if necessary

### Uninstallation
To remove the installation:
```bash
# Remove wrapper scripts
rm ~/.local/bin/start-the-day ~/.local/bin/auto

# Unload and remove LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.leosimons.start-the-day.plist
rm ~/Library/LaunchAgents/com.leosimons.start-the-day.plist

# Optionally remove log directory
rm -rf ~/.local/log/
```

### Version Migration
When updating the project:
1. Pull latest changes
2. Run `uv sync` to update dependencies
3. Re-run `python3 install.py` to update wrapper scripts
4. New features will be automatically available

## Security Considerations

### File System Security
- Creates files only in user's home directory
- Uses standard Unix permissions (0o755 for executables)
- No system-wide modifications or root privileges required
- Respects existing file permissions and ownership

### LaunchAgent Security
- Runs in user context, not system-wide
- Uses user's LaunchAgents directory
- No elevated privileges or special capabilities
- Logs to user-writable directories only

### Script Security
- Wrapper scripts contain only trusted, hardcoded paths
- No user input processing or dynamic command construction
- Virtual environment paths are validated before use
- No network access or external dependencies during installation

## Dependencies

### System Requirements
- **macOS**: Required for LaunchAgent functionality
- **Python 3.13+**: Required for project virtual environment
- **uv**: Package manager used for virtual environment creation
- **bash**: Required for wrapper script execution
- **launchctl**: macOS system service for LaunchAgent management

### File System Requirements
- Write access to `~/.local/bin` (created if needed)
- Write access to `~/.local/log` (created if needed)
- Write access to `~/Library/LaunchAgents` (created if needed)
- Read access to project directory and files

### Project Structure Dependencies
- `lsimons_auto/start_the_day.py` must exist
- `lsimons_auto/lsimons_auto.py` must exist
- `.venv/bin/python` must exist (created by `uv sync`)
- `etc/com.leosimons.start-the-day.plist` template must exist

## Future Enhancements

### Potential Improvements
1. **Configuration Options**: Allow customization of installation paths and schedule
2. **Update Detection**: Check if reinstallation is needed based on file changes
3. **Backup/Restore**: Create backups of existing configurations before modification
4. **Validation Suite**: More comprehensive post-installation validation
5. **Cross-Platform**: Extend to support Linux/Windows (with appropriate service managers)

### Extensibility Points
- **Additional Wrapper Scripts**: Easy to add new CLI commands
- **Multiple LaunchAgents**: Support for different schedules or tasks
- **Custom Templates**: Support for user-customized LaunchAgent templates
- **Plugin Architecture**: Support for third-party installation extensions

## References
- macOS LaunchAgent documentation: `man launchd.plist`, `man launchctl`
- Unix filesystem hierarchy standard for `~/.local` usage
- Python pathlib documentation: https://docs.python.org/3/library/pathlib.html
- macOS service management: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/
- Virtual environment best practices: https://docs.python.org/3/tutorial/venv.html