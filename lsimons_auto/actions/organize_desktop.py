#!/usr/bin/env python3
"""
organize_desktop.py - Organize desktop files into date-based directory structure

Moves all files and directories from ~/Desktop into a year/month/day hierarchy
based on creation time, with special handling for images and text files.
"""

import argparse
import io
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_creation_date(file_path: Path) -> datetime:
    """Get file creation date, with fallback handling."""
    file_stat = file_path.stat()

    # macOS: use birth time if available, fallback to change time
    timestamp: float = getattr(file_stat, "st_birthtime", file_stat.st_ctime)

    return datetime.fromtimestamp(timestamp)


def set_directory_timestamps(directory: Path, target_date: datetime) -> None:
    """Set creation and modification times for a directory."""
    try:
        timestamp = target_date.timestamp()
        # Set modification time
        os.utime(directory, (timestamp, timestamp))

        # On macOS, also try to set birth time if possible
        if hasattr(os, "stat_result") and hasattr(os.stat_result, "st_birthtime"):
            try:
                # Use touch command to set birth time on macOS
                date_str = target_date.strftime("%Y%m%d%H%M.%S")
                subprocess.run(
                    ["touch", "-t", date_str, str(directory)],
                    check=False,
                    capture_output=True,
                )
            except subprocess.SubprocessError, FileNotFoundError:
                # If touch command fails, continue without birth time setting
                pass
    except OSError, ValueError:
        # If timestamp setting fails, continue without error
        pass


def ensure_date_directory(base_path: Path, date_obj: datetime) -> Path:
    """Create year/month/day directory structure if it doesn't exist."""
    year_dir = base_path / str(date_obj.year)
    month_dir = year_dir / f"{date_obj.month:02d}"
    day_dir = month_dir / f"{date_obj.day:02d}"

    # Track which directories we create to set timestamps
    created_dirs: list[tuple[str, Path]] = []

    if not year_dir.exists():
        year_dir.mkdir(exist_ok=True)
        created_dirs.append(("year", year_dir))

    if not month_dir.exists():
        month_dir.mkdir(exist_ok=True)
        created_dirs.append(("month", month_dir))

    if not day_dir.exists():
        day_dir.mkdir(exist_ok=True)
        created_dirs.append(("day", day_dir))

    # Set appropriate timestamps for newly created directories
    for dir_type, directory in created_dirs:
        if dir_type == "year":
            # Set to first day of year
            target_date = datetime(date_obj.year, 1, 1)
        elif dir_type == "month":
            # Set to first day of month
            target_date = datetime(date_obj.year, date_obj.month, 1)
        else:  # day
            # Set to the actual date
            target_date = date_obj

        set_directory_timestamps(directory, target_date)

    return day_dir


def compress_cleanshot_image(image_path: Path, target_dir: Path) -> Path:
    """Compress CleanShot image to approximately 1MB."""
    try:
        from PIL import Image
    except ImportError:
        print("Warning: Pillow library not found. Falling back to standard copy.")
        # Fall back to standard move
        output_path = target_dir / image_path.name
        shutil.copy2(image_path, output_path)
        return output_path

    target_size = 1024 * 1024  # 1MB in bytes

    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG compression)
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background

            # Use binary search to find optimal quality level
            # Start with quality range [10, 95]
            min_quality = 10
            max_quality = 95
            best_buffer = io.BytesIO()

            while min_quality <= max_quality:
                mid_quality = (min_quality + max_quality) // 2
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=mid_quality, optimize=True)
                size = len(buffer.getvalue())

                if size <= target_size:
                    # This quality works, try higher for better quality
                    best_buffer = buffer
                    min_quality = mid_quality + 1
                else:
                    # Too large, try lower quality
                    max_quality = mid_quality - 1

            # Save compressed image with best quality found
            output_path = target_dir / f"{image_path.stem}_compressed.jpg"
            with open(output_path, "wb") as f:
                f.write(best_buffer.getvalue())

            return output_path

    except OSError as e:
        print(f"Warning: Could not compress image {image_path.name}: {e}")
        # Fall back to standard move
        output_path = target_dir / image_path.name
        shutil.copy2(image_path, output_path)
        return output_path


def convert_txt_to_md(txt_path: Path, target_dir: Path) -> Path:
    """Convert .txt file to .md extension."""
    md_filename = txt_path.stem + ".md"
    output_path = target_dir / md_filename

    # Copy content with new extension
    shutil.copy2(txt_path, output_path)

    return output_path


def is_cleanshot_image(file_path: Path) -> bool:
    """Check if file is a CleanShot image that should be compressed."""
    if not file_path.name.startswith("CleanShot"):
        return False

    if file_path.suffix.lower() not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tiff",
    }:
        return False

    return file_path.stat().st_size > 1024 * 1024  # > 1MB


def organize_file(file_path: Path, target_dir: Path, dry_run: bool = False) -> None:
    """Organize a single file with special processing."""
    filename = file_path.name

    if dry_run:
        # Show what would happen
        try:
            relative_path = target_dir.relative_to(Path.home() / "Desktop")
        except ValueError:
            # For test cases or when not under ~/Desktop
            relative_path = target_dir.name

        if is_cleanshot_image(file_path):
            print(
                f"Would compress and move: {filename}"
                f" -> {relative_path}/{file_path.stem}_compressed.jpg"
            )
        elif file_path.suffix.lower() == ".txt":
            print(f"Would convert and move: {filename} -> {relative_path}/{file_path.stem}.md")
        else:
            print(f"Would move: {filename} -> {relative_path}/{filename}")
        return

    try:
        # Check for CleanShot image compression
        if is_cleanshot_image(file_path):
            new_path = compress_cleanshot_image(file_path, target_dir)
            print(f"Compressed and moved: {filename} -> {new_path.name}")
            file_path.unlink()  # Remove original

        # Check for text file conversion
        elif file_path.suffix.lower() == ".txt":
            new_path = convert_txt_to_md(file_path, target_dir)
            print(f"Converted and moved: {filename} -> {new_path.name}")
            file_path.unlink()  # Remove original

        # Standard file move
        else:
            new_path = target_dir / filename
            # Handle filename conflicts - check existence first
            if new_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                counter = 1
                while new_path.exists():
                    new_path = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            file_path.rename(new_path)
            try:
                relative_path = new_path.relative_to(Path.home() / "Desktop")
            except ValueError:
                # For test cases or when not under ~/Desktop
                relative_path = new_path.name
            print(f"Moved: {filename} -> {relative_path}")

    except Exception as e:
        print(f"Error organizing {filename}: {e}")


def organize_directory(dir_path: Path, target_dir: Path, dry_run: bool = False) -> None:
    """Move directory to target location."""
    if dry_run:
        try:
            relative_path = target_dir.relative_to(Path.home() / "Desktop")
        except ValueError:
            # For test cases or when not under ~/Desktop
            relative_path = target_dir.name
        print(f"Would move directory: {dir_path.name} -> {relative_path}/{dir_path.name}")
        return

    try:
        new_path = target_dir / dir_path.name
        # Handle directory name conflicts
        counter = 1
        while new_path.exists():
            new_path = target_dir / f"{dir_path.name}_{counter}"
            counter += 1

        dir_path.rename(new_path)
        try:
            relative_path = new_path.relative_to(Path.home() / "Desktop")
        except ValueError:
            # For test cases or when not under ~/Desktop
            relative_path = new_path.name
        print(f"Moved directory: {dir_path.name} -> {relative_path}")

    except Exception as e:
        print(f"Error organizing directory {dir_path.name}: {e}")


def organize_single_item(item_path: Path, base_path: Path, dry_run: bool = False) -> None:
    """Organize a single file or directory."""
    creation_date = get_creation_date(item_path)
    target_dir = ensure_date_directory(base_path, creation_date)

    if item_path.is_file():
        organize_file(item_path, target_dir, dry_run)
    else:
        organize_directory(item_path, target_dir, dry_run)


def get_items_to_organize(desktop_path: Path) -> list[Path]:
    """Get list of items on desktop that need to be organized."""
    items_to_organize: list[Path] = []

    for item in desktop_path.iterdir():
        # Skip hidden files and existing year directories
        if item.name.startswith("."):
            continue
        if item.is_dir() and item.name.isdigit() and len(item.name) == 4:
            continue  # Skip existing year directories

        items_to_organize.append(item)

    return items_to_organize


def organize_desktop_items(dry_run: bool = False) -> None:
    """Organize all items on desktop into date-based directories."""
    desktop_path = Path.home() / "Desktop"

    if not desktop_path.exists():
        print("Desktop directory not found")
        return

    items_to_organize = get_items_to_organize(desktop_path)

    if not items_to_organize:
        print("No items found to organize on desktop")
        return

    print(f"Found {len(items_to_organize)} items to organize")

    if dry_run:
        print("\nDRY RUN - Showing what would be organized:\n")

    organized_count = 0
    error_count = 0

    for item in items_to_organize:
        try:
            organize_single_item(item, desktop_path, dry_run)
            organized_count += 1
        except Exception as e:
            print(f"Error organizing {item.name}: {e}")
            error_count += 1
            continue

    if not dry_run:
        print(f"\nOrganization completed: {organized_count} items organized, {error_count} errors")
    else:
        print(f"\nDry run completed: {organized_count} items would be organized")


def main(args: list[str] | None = None) -> None:
    """Main function to organize desktop."""
    parser = argparse.ArgumentParser(
        description="Organize desktop files into date-based directory structure"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be organized without making changes",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information about each file processed",
    )

    parsed_args = parser.parse_args(args)

    try:
        organize_desktop_items(dry_run=parsed_args.dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error organizing desktop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
