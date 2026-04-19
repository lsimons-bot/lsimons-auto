"""Tests for lsimons_auto.actions.clean_tmp module."""

from pathlib import Path

import pytest

from lsimons_auto.actions.clean_tmp import clean_tmp_dir, main


class TestCleanTmpDir:
    """Test the clean_tmp_dir helper."""

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        """Missing target directory is created; nothing removed."""
        target = tmp_path / "missing"
        removed, errors = clean_tmp_dir(target)

        assert target.exists()
        assert target.is_dir()
        assert removed == 0
        assert errors == 0

    def test_removes_files_and_subdirs(self, tmp_path: Path) -> None:
        """All top-level entries are removed, directory itself stays."""
        (tmp_path / "file.txt").write_text("hello")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("world")

        removed, errors = clean_tmp_dir(tmp_path)

        assert tmp_path.exists()
        assert list(tmp_path.iterdir()) == []
        assert removed == 2
        assert errors == 0

    def test_removes_hidden_entries(self, tmp_path: Path) -> None:
        """Dotfiles and dot-directories are also removed."""
        (tmp_path / ".hidden").write_text("x")
        (tmp_path / ".hiddendir").mkdir()

        removed, errors = clean_tmp_dir(tmp_path)

        assert list(tmp_path.iterdir()) == []
        assert removed == 2
        assert errors == 0

    def test_handles_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory is a no-op."""
        removed, errors = clean_tmp_dir(tmp_path)

        assert removed == 0
        assert errors == 0
        assert tmp_path.exists()

    def test_dry_run_does_not_delete(self, tmp_path: Path) -> None:
        """Dry run counts entries but leaves them in place."""
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b").mkdir()

        removed, errors = clean_tmp_dir(tmp_path, dry_run=True)

        assert removed == 2
        assert errors == 0
        assert (tmp_path / "a.txt").exists()
        assert (tmp_path / "b").exists()

    def test_dry_run_does_not_create_directory(self, tmp_path: Path) -> None:
        """Dry run reports creation but does not create the directory."""
        target = tmp_path / "missing"

        removed, errors = clean_tmp_dir(target, dry_run=True)

        assert not target.exists()
        assert removed == 0
        assert errors == 0

    def test_follows_symlinks_safely(self, tmp_path: Path) -> None:
        """A symlink to a directory is unlinked, not recursively removed."""
        outside = tmp_path.parent / "clean_tmp_outside"
        outside.mkdir(exist_ok=True)
        (outside / "keep.txt").write_text("keep")

        target = tmp_path / "scratch"
        target.mkdir()
        link = target / "link"
        link.symlink_to(outside)

        try:
            removed, errors = clean_tmp_dir(target)
            assert removed == 1
            assert errors == 0
            assert not link.exists()
            assert (outside / "keep.txt").exists()
        finally:
            if (outside / "keep.txt").exists():
                (outside / "keep.txt").unlink()
            if outside.exists():
                outside.rmdir()


class TestCleanTmpCLI:
    """Test the main() CLI entry point."""

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--help exits 0 and prints usage."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "clean" in captured.out.lower() or "scratch" in captured.out.lower()

    def test_dry_run_cli(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--dry-run on CLI does not delete files."""
        monkeypatch.setattr("lsimons_auto.actions.clean_tmp.TMP_DIR", tmp_path)
        (tmp_path / "keep.txt").write_text("keep")

        main(["--dry-run"])

        assert (tmp_path / "keep.txt").exists()
        captured = capsys.readouterr()
        assert "Dry run" in captured.out

    def test_cli_cleans_target(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Default CLI invocation clears the target directory."""
        monkeypatch.setattr("lsimons_auto.actions.clean_tmp.TMP_DIR", tmp_path)
        (tmp_path / "gone.txt").write_text("gone")

        main([])

        assert list(tmp_path.iterdir()) == []
        captured = capsys.readouterr()
        assert "Cleanup complete" in captured.out
