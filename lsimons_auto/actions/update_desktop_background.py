#!/usr/bin/env python3
"""
update_desktop_background.py - Generate and set custom desktop background

Creates a desktop background with "lsimons-auto" branding and current UTC time
using a monospace font optimized for high-resolution macOS displays.
"""

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def find_available_font() -> str:
    """Find the best available monospace font on the system."""
    preferred_fonts = [
        "/System/Library/Fonts/Supplemental/JetBrainsMono-Regular.ttf",
        "/System/Library/Fonts/Supplemental/SourceCodePro-Regular.ttf",
        "/System/Library/Fonts/Supplemental/SFMono-Regular.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Courier New.ttf",
    ]

    for font_path in preferred_fonts:
        if Path(font_path).exists():
            return font_path

    # System fallback - Monaco should always be available on macOS
    return "Monaco"


def generate_background(width: int = 2880, height: int = 1800) -> Path:
    """Generate desktop background image with current timestamp."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: Pillow library not found. Install with: pip install pillow")
        sys.exit(1)

    # Create image with dark background
    img = Image.new("RGB", (width, height), color="#1A1A1A")
    draw = ImageDraw.Draw(img)

    # Load fonts
    font_path = find_available_font()
    try:
        title_font = ImageFont.truetype(font_path, 32)
        time_font = ImageFont.truetype(font_path, 20)
    except OSError:
        # Fallback to default font if TrueType loading fails
        print(f"Warning: Could not load font {font_path}, using default font")
        title_font = ImageFont.load_default()
        time_font = ImageFont.load_default()

    # Generate timestamp
    now_utc = datetime.now(UTC)
    timestamp = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Calculate text positioning
    title_text = "lsimons-auto"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    time_bbox = draw.textbbox((0, 0), timestamp, font=time_font)

    # Position text in bottom left corner (with padding from edges)
    left_padding = 80
    bottom_padding = 35
    title_x = left_padding
    title_y = (
        height
        - bottom_padding
        - (time_bbox[3] - time_bbox[1])
        - (title_bbox[3] - title_bbox[1])
        - 20
    )

    time_x = left_padding
    time_y = height - bottom_padding - (time_bbox[3] - time_bbox[1])

    # Draw text
    draw.text((title_x, title_y), title_text, font=title_font, fill="#E8E8E8")
    draw.text((time_x, time_y), timestamp, font=time_font, fill="#E8E8E8")

    # Ensure backgrounds directory exists
    bg_dir = Path.home() / ".local" / "share" / "lsimons-auto" / "backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename and save
    filename = f"background_{now_utc.strftime('%Y%m%d_%H%M%S')}.png"
    filepath = bg_dir / filename

    img.save(filepath, "PNG")
    filepath.chmod(0o600)

    return filepath


def set_desktop_background(image_path: Path) -> None:
    """Set the desktop background using macOS APIs."""
    script = f'''
    tell application "System Events"
        tell every desktop
            set picture to "{image_path}"
        end tell
    end tell
    '''

    try:
        print(f"Running command: osascript -e {repr(script)}")
        result = subprocess.run(
            ["osascript", "-e", script], check=True, text=True, capture_output=True
        )
        if result.stdout:
            print(f"Command output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Command stderr: {result.stderr.strip()}")
        print(f"Desktop background updated: {image_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set desktop background: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: osascript not found. This action requires macOS.")
        sys.exit(1)


def cleanup_old_backgrounds(keep_count: int = 5) -> None:
    """Remove old background files, keeping only the most recent."""
    bg_dir = Path.home() / ".local" / "share" / "lsimons-auto" / "backgrounds"

    if not bg_dir.exists():
        return

    background_files = sorted(
        bg_dir.glob("background_*.png"), key=lambda x: x.stat().st_mtime, reverse=True
    )

    for old_file in background_files[keep_count:]:
        try:
            old_file.unlink()
            print(f"Cleaned up old background: {old_file.name}")
        except OSError as e:
            print(f"Warning: Could not remove {old_file.name}: {e}")


def main(args: list[str] | None = None) -> None:
    """Main function to generate and set desktop background."""
    parser = argparse.ArgumentParser(
        description="Generate and set desktop background with current UTC time"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate image but don't set as background",
    )

    parsed_args = parser.parse_args(args)

    try:
        # Generate new background (hardcoded to 2880x1800)
        print("Generating desktop background...")
        image_path = generate_background(2880, 1800)
        print(f"Generated background: {image_path}")

        # Set as desktop background (unless dry-run)
        if not parsed_args.dry_run:
            set_desktop_background(image_path)
        else:
            print("Dry run mode: Desktop background not changed")

        # Cleanup old files (keep 5 most recent)
        cleanup_old_backgrounds(5)

        print("Desktop background update completed successfully!")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
