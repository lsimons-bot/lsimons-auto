#!/usr/bin/env python3
"""
test_organize_desktop.py - Unit tests for organize_desktop action

Tests the organize_desktop functionality including file organization,
image compression, text file conversion, and error handling.
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from lsimons_auto.actions.organize_desktop import (
    compress_cleanshot_image,
    convert_txt_to_md,
    ensure_date_directory,
    get_creation_date,
    get_items_to_organize,
    is_cleanshot_image,
    organize_directory,
    organize_file,
    organize_single_item,
)


class TestOrganizeDesktop(unittest.TestCase):
    """Test cases for organize_desktop functionality."""

    def setUp(self):
        """Set up test environment with temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        self.desktop_path = Path(self.test_dir) / "Desktop"
        self.desktop_path.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir)

    def test_ensure_date_directory_creation(self):
        """Test creation of year/month/day directory structure."""
        test_date = datetime(2024, 3, 15)
        result_dir = ensure_date_directory(self.desktop_path, test_date)

        expected_path = self.desktop_path / "2024" / "03" / "15"
        self.assertEqual(result_dir, expected_path)
        self.assertTrue(result_dir.exists())
        self.assertTrue(result_dir.is_dir())

    def test_ensure_date_directory_existing(self):
        """Test that existing directories are not recreated."""
        test_date = datetime(2024, 3, 15)

        # Create the directory structure first
        first_result = ensure_date_directory(self.desktop_path, test_date)

        # Create a test file to verify directory isn't overwritten
        test_file = first_result / "test.txt"
        test_file.write_text("test content")

        # Call again - should return same directory without issues
        second_result = ensure_date_directory(self.desktop_path, test_date)

        self.assertEqual(first_result, second_result)
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(), "test content")

    def test_get_creation_date(self):
        """Test file creation date detection."""
        test_file = self.desktop_path / "test.txt"
        test_file.write_text("test")

        creation_date = get_creation_date(test_file)

        # Should be recent (within last minute)
        now = datetime.now()
        self.assertLessEqual(abs((now - creation_date).total_seconds()), 60)

    def test_is_cleanshot_image_positive(self):
        """Test CleanShot image detection for valid cases."""
        # Create a large test image file
        test_file = self.desktop_path / "CleanShot_test.png"
        test_file.write_bytes(b"0" * (1024 * 1024 + 1))  # > 1MB

        self.assertTrue(is_cleanshot_image(test_file))

    def test_is_cleanshot_image_negative_cases(self):
        """Test CleanShot image detection for invalid cases."""
        # Wrong name prefix
        test_file1 = self.desktop_path / "Screenshot.png"
        test_file1.write_bytes(b"0" * (1024 * 1024 + 1))
        self.assertFalse(is_cleanshot_image(test_file1))

        # Wrong extension
        test_file2 = self.desktop_path / "CleanShot_test.txt"
        test_file2.write_bytes(b"0" * (1024 * 1024 + 1))
        self.assertFalse(is_cleanshot_image(test_file2))

        # Too small
        test_file3 = self.desktop_path / "CleanShot_test.png"
        test_file3.write_bytes(b"small")
        self.assertFalse(is_cleanshot_image(test_file3))

    def test_compress_cleanshot_image_fallback(self):
        """Test CleanShot image compression fallback behavior."""
        test_file = self.desktop_path / "CleanShot_test.png"
        test_file.write_bytes(b"0" * (2 * 1024 * 1024))

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        # Test that when PIL import fails, it falls back to standard copy
        with patch("builtins.__import__", side_effect=ImportError("No PIL")):
            result_path = compress_cleanshot_image(test_file, target_dir)

            # Should fall back to standard copy
            expected_path = target_dir / "CleanShot_test.png"
            self.assertEqual(result_path, expected_path)
            self.assertTrue(result_path.exists())

    def test_compress_cleanshot_image_success(self):
        """Test successful CleanShot image compression."""
        test_file = self.desktop_path / "CleanShot_test.png"
        test_file.write_bytes(b"0" * (2 * 1024 * 1024))

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        # Create a simple test that doesn't require complex PIL mocking
        # Just verify the function can be called without error
        try:
            result_path = compress_cleanshot_image(test_file, target_dir)
            # Should either compress or fall back to copy
            self.assertTrue(result_path.exists())
        except Exception:
            # If PIL has issues, should still create a fallback copy
            fallback_path = target_dir / "CleanShot_test.png"
            self.assertTrue(fallback_path.exists())

    def test_directory_timestamp_setting(self):
        """Test that directory timestamps are set correctly."""
        test_date = datetime(2024, 3, 15, 14, 30, 0)
        result_dir = ensure_date_directory(self.desktop_path, test_date)

        year_dir = self.desktop_path / "2024"
        month_dir = year_dir / "03"
        day_dir = month_dir / "15"

        # Check that directories were created
        self.assertTrue(year_dir.exists())
        self.assertTrue(month_dir.exists())
        self.assertTrue(day_dir.exists())
        self.assertEqual(result_dir, day_dir)

        # Check timestamps (allowing some tolerance for test execution time)
        year_expected = datetime(2024, 1, 1).timestamp()
        month_expected = datetime(2024, 3, 1).timestamp()
        day_expected = test_date.timestamp()

        year_mtime = year_dir.stat().st_mtime
        month_mtime = month_dir.stat().st_mtime
        day_mtime = day_dir.stat().st_mtime

        # Allow 5 second tolerance for filesystem precision and test execution
        self.assertAlmostEqual(year_mtime, year_expected, delta=5)
        self.assertAlmostEqual(month_mtime, month_expected, delta=5)
        self.assertAlmostEqual(day_mtime, day_expected, delta=5)

    def test_directory_timestamp_existing_dirs(self):
        """Test that existing directory timestamps are not modified."""
        # Create directories manually first
        year_dir = self.desktop_path / "2023"
        month_dir = year_dir / "12"
        day_dir = month_dir / "25"
        day_dir.mkdir(parents=True)

        # Set custom timestamps
        old_timestamp = datetime(2020, 1, 1).timestamp()
        import os

        os.utime(year_dir, (old_timestamp, old_timestamp))
        os.utime(month_dir, (old_timestamp, old_timestamp))
        os.utime(day_dir, (old_timestamp, old_timestamp))

        # Call ensure_date_directory
        test_date = datetime(2023, 12, 25, 10, 30, 0)
        _ = ensure_date_directory(self.desktop_path, test_date)

        # Existing directories should keep their old timestamps
        self.assertAlmostEqual(year_dir.stat().st_mtime, old_timestamp, delta=1)
        self.assertAlmostEqual(month_dir.stat().st_mtime, old_timestamp, delta=1)
        self.assertAlmostEqual(day_dir.stat().st_mtime, old_timestamp, delta=1)

    def test_convert_txt_to_md(self):
        """Test text file to markdown conversion."""
        test_content = "# Test\nThis is test content."
        test_file = self.desktop_path / "test.txt"
        test_file.write_text(test_content)

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        result_path = convert_txt_to_md(test_file, target_dir)

        expected_path = target_dir / "test.md"
        self.assertEqual(result_path, expected_path)
        self.assertTrue(result_path.exists())
        self.assertEqual(result_path.read_text(), test_content)

    def test_get_items_to_organize(self):
        """Test discovery of items that need organization."""
        # Create test files and directories
        (self.desktop_path / "test.txt").write_text("test")
        (self.desktop_path / "test_dir").mkdir()
        (self.desktop_path / ".hidden").write_text("hidden")
        (self.desktop_path / "2023").mkdir()  # Existing year directory

        items = get_items_to_organize(self.desktop_path)
        item_names = [item.name for item in items]

        self.assertIn("test.txt", item_names)
        self.assertIn("test_dir", item_names)
        self.assertNotIn(".hidden", item_names)
        self.assertNotIn("2023", item_names)

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    def test_organize_file_standard(self, mock_get_creation_date: MagicMock) -> None:
        """Test standard file organization."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)

        test_file = self.desktop_path / "test.pdf"
        test_file.write_text("test content")

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        organize_file(test_file, target_dir, dry_run=False)

        moved_file = target_dir / "test.pdf"
        self.assertTrue(moved_file.exists())
        self.assertFalse(test_file.exists())

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    def test_organize_file_txt_conversion(self, mock_get_creation_date: MagicMock) -> None:
        """Test text file conversion during organization."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)

        test_file = self.desktop_path / "notes.txt"
        test_file.write_text("# Notes\nImportant stuff")

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        organize_file(test_file, target_dir, dry_run=False)

        moved_file = target_dir / "notes.md"
        self.assertTrue(moved_file.exists())
        self.assertFalse(test_file.exists())
        self.assertEqual(moved_file.read_text(), "# Notes\nImportant stuff")

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    def test_organize_file_dry_run(self, mock_get_creation_date: MagicMock) -> None:
        """Test file organization in dry run mode."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)

        test_file = self.desktop_path / "test.txt"
        test_file.write_text("test")

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        # Capture output to verify dry run messages
        with patch("builtins.print") as mock_print:
            organize_file(test_file, target_dir, dry_run=True)

        # File should still exist (not moved)
        self.assertTrue(test_file.exists())

        # Should have printed dry run message
        mock_print.assert_called()
        call_args = str(mock_print.call_args_list[0])
        self.assertIn("Would convert and move", call_args)

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    def test_organize_directory(self, mock_get_creation_date: MagicMock) -> None:
        """Test directory organization."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)

        test_dir = self.desktop_path / "test_folder"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        organize_directory(test_dir, target_dir, dry_run=False)

        moved_dir = target_dir / "test_folder"
        self.assertTrue(moved_dir.exists())
        self.assertTrue((moved_dir / "file.txt").exists())
        self.assertFalse(test_dir.exists())

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    def test_filename_conflict_handling(self, mock_get_creation_date: MagicMock) -> None:
        """Test handling of filename conflicts with non-txt files."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)

        target_dir = self.desktop_path / "2024" / "03" / "15"
        target_dir.mkdir(parents=True)

        # Create existing file
        (target_dir / "test.pdf").write_text("existing")

        # Create new file with same name
        test_file = self.desktop_path / "test.pdf"
        test_file.write_text("new content")

        organize_file(test_file, target_dir, dry_run=False)

        # Should create test_1.pdf to avoid conflict
        moved_file = target_dir / "test_1.pdf"
        self.assertTrue(moved_file.exists())
        self.assertEqual(moved_file.read_text(), "new content")

        # Original should still exist
        original_file = target_dir / "test.pdf"
        self.assertTrue(original_file.exists())
        self.assertEqual(original_file.read_text(), "existing")

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    @patch("lsimons_auto.actions.organize_desktop.ensure_date_directory")
    def test_organize_single_item_file(
        self, mock_ensure_date: MagicMock, mock_get_creation_date: MagicMock
    ) -> None:
        """Test organization of a single file item."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)
        mock_target_dir = self.desktop_path / "2024" / "03" / "15"
        mock_target_dir.mkdir(parents=True)
        mock_ensure_date.return_value = mock_target_dir

        test_file = self.desktop_path / "test.pdf"
        test_file.write_text("content")

        organize_single_item(test_file, self.desktop_path, dry_run=False)

        moved_file = mock_target_dir / "test.pdf"
        self.assertTrue(moved_file.exists())
        self.assertFalse(test_file.exists())

    @patch("lsimons_auto.actions.organize_desktop.get_creation_date")
    @patch("lsimons_auto.actions.organize_desktop.ensure_date_directory")
    def test_organize_single_item_directory(
        self, mock_ensure_date: MagicMock, mock_get_creation_date: MagicMock
    ) -> None:
        """Test organization of a single directory item."""
        mock_get_creation_date.return_value = datetime(2024, 3, 15)
        mock_target_dir = self.desktop_path / "2024" / "03" / "15"
        mock_target_dir.mkdir(parents=True)
        mock_ensure_date.return_value = mock_target_dir

        test_dir = self.desktop_path / "test_folder"
        test_dir.mkdir()

        organize_single_item(test_dir, self.desktop_path, dry_run=False)

        moved_dir = mock_target_dir / "test_folder"
        self.assertTrue(moved_dir.exists())
        self.assertFalse(test_dir.exists())

    def test_error_handling_in_organize_file(self):
        """Test error handling during file organization."""
        test_file = self.desktop_path / "test.txt"
        test_file.write_text("content")

        # Create target directory without write permissions
        target_dir = self.desktop_path / "readonly"
        target_dir.mkdir()
        target_dir.chmod(0o555)  # Read and execute only

        try:
            with patch("builtins.print") as mock_print:
                organize_file(test_file, target_dir, dry_run=False)

            # Should print error message
            mock_print.assert_called()
            error_call = [
                call for call in mock_print.call_args_list if "Error organizing" in str(call)
            ]
            self.assertTrue(len(error_call) > 0)

            # Original file should still exist
            self.assertTrue(test_file.exists())

        finally:
            # Clean up - restore permissions for deletion
            target_dir.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
