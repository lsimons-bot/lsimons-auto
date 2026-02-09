#!/usr/bin/env python3
"""
tc.py - Technology Council meeting management

Subcommands:
- prep-meeting: Prepare for next Monday's meeting
- gen-pdf: Convert .docx files to PDF for current year
- create-dirs: Create directories for all Mondays of next year
"""

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

DEFAULT_BASE_DIR = (
    "~/Schuberg Philis/Engineering - Documents/\U0001f4c5 Meetings/Technology Council"
)


def get_base_dir(args_base_dir: str | None) -> Path:
    """Get the base directory from args, env, or default."""
    if args_base_dir:
        return Path(args_base_dir).expanduser()
    env_dir = os.environ.get("TC_BASE_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    return Path(DEFAULT_BASE_DIR).expanduser()


def get_next_monday(reference_date: date | None = None) -> date:
    """Get the date of the next Monday (or today if today is Monday)."""
    today = reference_date or date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if today.weekday() == 0:  # Today is Monday
        return today
    return today + timedelta(days=days_until_monday)


def get_previous_monday(current_monday: date) -> date:
    """Get the date of the Monday before the current Monday."""
    return current_monday - timedelta(days=7)


def format_date_yyyymmdd(date_obj: date) -> str:
    """Format a date object as YYYYMMDD string."""
    return date_obj.strftime("%Y%m%d")


def find_docx_file(directory_path: Path, date_str: str) -> Path | None:
    """Check if a .docx file exists in the directory."""
    expected_filename = f"{date_str} Minutes Technology Council.docx"
    file_path = directory_path / expected_filename
    return file_path if file_path.exists() else None


def copy_template_file(source_template: Path, target_directory: Path, date_str: str) -> Path | None:
    """Copy the template file to the target directory with the correct name."""
    target_filename = f"{date_str} Minutes Technology Council.docx"
    target_path = target_directory / target_filename

    try:
        shutil.copy2(source_template, target_path)
        print(f"Created new meeting document: {target_path}")
        return target_path
    except OSError as e:
        print(f"Error copying template file: {e}")
        return None


def open_document_in_word(file_path: Path) -> bool:
    """Open a document in Microsoft Word using osascript."""
    try:
        script = f'''
        tell application "Microsoft Word"
            activate
            open POSIX file "{file_path}"
        end tell
        '''
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        print(f"Opened document in Word: {file_path}")
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["open", "-a", "Microsoft Word", str(file_path)],
                check=True,
                capture_output=True,
            )
            print(f"Opened document using fallback method: {file_path}")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"Fallback method also failed: {e2}")
            return False


def find_most_recent_meeting_document(
    base_dir: Path, current_monday: date
) -> tuple[Path | None, date | None]:
    """Find the most recent existing meeting document within the current year."""
    current_year = current_monday.year
    check_monday = get_previous_monday(current_monday)

    while check_monday.year == current_year:
        check_date_str = format_date_yyyymmdd(check_monday)
        year_dir = base_dir / str(check_monday.year)
        meeting_dir = year_dir / check_date_str

        if meeting_dir.exists():
            docx_file = find_docx_file(meeting_dir, check_date_str)
            if docx_file:
                print(f"Found most recent meeting document: {docx_file}")
                return docx_file, check_monday

        check_monday = get_previous_monday(check_monday)

    print(f"No previous meeting documents found in {current_year}")
    return None, None


def prep_meeting(base_dir: Path, dry_run: bool = False) -> int:
    """Prepare for Technology Council meeting."""
    print("Technology Council Meeting Preparation")
    print("=" * 50)

    template_file = base_dir / "YYYYMMDD Minutes Technology Council.docx"

    if not template_file.exists():
        print(f"Error: Template file not found: {template_file}")
        return 1

    current_monday = get_next_monday()
    current_date_str = format_date_yyyymmdd(current_monday)
    current_year = current_monday.year

    print(f"Current Monday: {current_monday} ({current_date_str})")

    current_year_dir = base_dir / str(current_year)
    current_meeting_dir = current_year_dir / current_date_str

    if dry_run:
        print(f"Would create directory: {current_meeting_dir}")
    else:
        current_meeting_dir.mkdir(parents=True, exist_ok=True)
        print(f"Meeting directory: {current_meeting_dir}")

    current_docx_file = find_docx_file(current_meeting_dir, current_date_str)

    if current_docx_file is None:
        if dry_run:
            target = current_meeting_dir / f"{current_date_str} Minutes Technology Council.docx"
            print(f"Would copy template to: {target}")
            current_docx_file = target
        else:
            print("No existing meeting document found, creating new one from template...")
            current_docx_file = copy_template_file(
                template_file, current_meeting_dir, current_date_str
            )
            if current_docx_file is None:
                return 1
    else:
        print(f"Found existing meeting document: {current_docx_file}")

    if not dry_run:
        print("\nOpening current meeting document...")
        if not open_document_in_word(current_docx_file):
            print("Warning: Could not open current meeting document in Word")

    print("\n" + "=" * 50)
    previous_monday = get_previous_monday(current_monday)
    previous_date_str = format_date_yyyymmdd(previous_monday)
    previous_year = previous_monday.year

    print(f"Previous Monday: {previous_monday} ({previous_date_str})")

    previous_year_dir = base_dir / str(previous_year)
    previous_meeting_dir = previous_year_dir / previous_date_str
    previous_docx_file = None

    if previous_meeting_dir.exists():
        previous_docx_file = find_docx_file(previous_meeting_dir, previous_date_str)
        if previous_docx_file:
            print(f"Found previous meeting document: {previous_docx_file}")
        else:
            print(f"Previous meeting directory exists but no .docx file: {previous_meeting_dir}")
    else:
        print(f"Previous meeting directory does not exist: {previous_meeting_dir}")

    if previous_docx_file is None:
        print("Searching for most recent meeting document in current year...")
        previous_docx_file, _ = find_most_recent_meeting_document(base_dir, current_monday)

    if previous_docx_file and not dry_run:
        print("Opening previous meeting document...")
        if not open_document_in_word(previous_docx_file):
            print("Warning: Could not open previous meeting document in Word")
    elif previous_docx_file is None:
        print("No previous meeting documents found to open for reference")

    print("\nMeeting preparation complete!")
    return 0


def find_docx_without_pdf(base_dir: Path) -> list[tuple[Path, Path]]:
    """Find subdirectories containing .docx files but no corresponding .pdf files."""
    results: list[tuple[Path, Path]] = []

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Error: Directory '{base_dir}' does not exist or is not a directory.")
        return results

    subdirs = [item for item in base_dir.iterdir() if item.is_dir()]

    for subdir in subdirs:
        docx_files = list(subdir.glob("*.docx"))

        for docx_file in docx_files:
            pdf_file = docx_file.with_suffix(".pdf")
            if not pdf_file.exists():
                results.append((subdir, docx_file))

    return results


def generate_pdf_command(docx_file: Path) -> str:
    """Generate the AppleScript command to convert .docx to .pdf."""
    docx_path = docx_file.resolve()
    pdf_path = docx_path.with_suffix(".pdf")

    applescript = f'''
osascript -e '
tell application "Microsoft Word"
    activate
    open POSIX file "{docx_path}"
    tell active document
        set fieldList to fields
        repeat with ef in fieldList
            update field ef
        end repeat
        save as it file name "{pdf_path}" file format format PDF
        close saving no
    end tell
end tell'
'''.strip()
    return applescript


def gen_pdf(base_dir: Path, dry_run: bool = False) -> int:
    """Generate PDFs for all .docx files missing PDFs in current year."""
    year = str(date.today().year)
    year_dir = base_dir / year

    print(f"Scanning directory: {year_dir.resolve()}")
    docx_files = find_docx_without_pdf(year_dir)

    if not docx_files:
        print("No .docx files found that need PDF conversion.")
        return 0

    print(f"Found {len(docx_files)} .docx file(s) that need PDF conversion.")

    commands: list[tuple[str, Path]] = []
    for _, docx_file in docx_files:
        command = generate_pdf_command(docx_file)
        commands.append((command, docx_file))

    if dry_run:
        print("\nWould execute the following conversions:")
        for _, docx_file in commands:
            print(f"  {docx_file} -> {docx_file.with_suffix('.pdf')}")
        return 0

    print("Executing commands...")
    for command, docx_file in commands:
        print(f"Converting {docx_file}...")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print("  Command executed successfully")
            else:
                print(f"  Command failed with return code {result.returncode}")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
        except OSError as e:
            print(f"  Error executing command: {e}")

    return 0


def mondays_of_year(year: int) -> Iterator[date]:
    """Generate all Mondays of a given year."""
    d = date(year, 1, 1)
    while d.weekday() != 0:
        d += timedelta(days=1)
    while d.year == year:
        yield d
        d += timedelta(days=7)


def create_dirs(base_dir: Path, dry_run: bool = False) -> int:
    """Create meeting directories for all Mondays of next year."""
    next_year = date.today().year + 1

    print(f"Working in: {base_dir}")

    year_dir = base_dir / str(next_year)
    if not year_dir.exists():
        if dry_run:
            print(f"Would create directory for year {next_year}")
        else:
            year_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory for year {next_year}")

    count = 0
    for monday in mondays_of_year(next_year):
        name = monday.strftime("%Y%m%d")
        meeting_dir = year_dir / name

        should_create = True
        if year_dir.exists():
            for entry in year_dir.iterdir():
                if entry.name.startswith(name):
                    should_create = False
                    print(f"Skipping {name} (found {entry.name})")
                    break

        if should_create:
            if dry_run:
                print(f"Would create directory: {name}")
            else:
                meeting_dir.mkdir(exist_ok=True)
                print(f"Created directory: {name}")
            count += 1

    verb = "Would create" if dry_run else "Created"
    print(f"{verb} {count} directories for Mondays of {next_year}.")
    return 0


def main(args: list[str] | None = None) -> None:
    """Main function that dispatches to subcommands."""
    parser = argparse.ArgumentParser(
        description="Technology Council meeting management",
        prog="auto tc",
    )

    parser.add_argument(
        "--base-dir",
        help="Base directory for meeting files (default: TC_BASE_DIR env or standard path)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    prep_parser = subparsers.add_parser("prep-meeting", help="Prepare for next Monday's meeting")
    prep_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )

    gen_parser = subparsers.add_parser("gen-pdf", help="Generate PDFs for current year's meetings")
    gen_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )

    dirs_parser = subparsers.add_parser(
        "create-dirs", help="Create meeting directories for next year"
    )
    dirs_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return

    base_dir = get_base_dir(parsed_args.base_dir)

    if not base_dir.exists():
        print(f"Error: Base directory does not exist: {base_dir}")
        sys.exit(1)

    dry_run = getattr(parsed_args, "dry_run", False)

    if parsed_args.command == "prep-meeting":
        sys.exit(prep_meeting(base_dir, dry_run))
    elif parsed_args.command == "gen-pdf":
        sys.exit(gen_pdf(base_dir, dry_run))
    elif parsed_args.command == "create-dirs":
        sys.exit(create_dirs(base_dir, dry_run))


if __name__ == "__main__":
    main()
