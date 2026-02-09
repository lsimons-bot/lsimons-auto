#!/usr/bin/env python3
"""
Tests for the install.py script.

These tests focus on installation functionality including directory creation,
wrapper script generation, and LaunchAgent installation.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestInstallScript(unittest.TestCase):
    """Test cases for install.py script."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.project_root = Path.home() / "dev" / "lsimons-auto"
        cls.install_script = cls.project_root / "install.py"

        # Verify test environment
        if not cls.project_root.exists():
            raise unittest.SkipTest(f"Project root not found: {cls.project_root}")
        if not cls.install_script.exists():
            raise unittest.SkipTest(f"Install script not found: {cls.install_script}")

    def test_install_script_exists(self):
        """Test that install.py exists and is executable."""
        self.assertTrue(self.install_script.exists())
        self.assertTrue(self.install_script.is_file())

    def test_install_script_has_shebang(self):
        """Test that install.py has proper shebang."""
        content = self.install_script.read_text()
        self.assertTrue(content.startswith("#!/usr/bin/env python3"))

    def test_install_script_imports(self):
        """Test that install.py has necessary imports."""
        content = self.install_script.read_text()
        self.assertIn("import os", content)
        self.assertIn("import sys", content)
        self.assertIn("from pathlib import Path", content)

    def test_install_wrapper_script_function_exists(self):
        """Test that install_wrapper_script function is defined."""
        # Import the install module
        import importlib.util

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install_module)

        self.assertTrue(hasattr(install_module, "install_wrapper_script"))
        self.assertTrue(callable(install_module.install_wrapper_script))

    def test_install_scripts_function_exists(self):
        """Test that install_scripts function is defined."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install_module)

        self.assertTrue(hasattr(install_module, "install_scripts"))
        self.assertTrue(callable(install_module.install_scripts))

    def test_install_launch_agent_function_exists(self):
        """Test that install_launch_agent function is defined."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install_module)

        self.assertTrue(hasattr(install_module, "install_launch_agent"))
        self.assertTrue(callable(install_module.install_launch_agent))

    def test_wrapper_script_content_format(self):
        """Test that wrapper scripts have correct bash format."""
        import importlib.util
        import tempfile

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install_module)

        with tempfile.TemporaryDirectory() as tmpdir:
            venv_python = Path(tmpdir) / "python"
            venv_python.touch()
            target_script = Path(tmpdir) / "target.py"
            target_script.touch()
            wrapper_path = Path(tmpdir) / "wrapper"

            install_module.install_wrapper_script(venv_python, target_script, wrapper_path)

            # Verify wrapper was created
            self.assertTrue(wrapper_path.exists())

            # Verify content
            content = wrapper_path.read_text()
            self.assertIn("#!/bin/bash", content)
            self.assertIn("exec", content)
            self.assertIn(str(venv_python), content)
            self.assertIn(str(target_script), content)
            self.assertIn('"$@"', content)

            # Verify permissions
            self.assertTrue(wrapper_path.stat().st_mode & 0o111)

    def test_wrapper_script_idempotent(self):
        """Test that installing wrapper script twice doesn't fail."""
        import importlib.util
        import tempfile

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install_module)

        with tempfile.TemporaryDirectory() as tmpdir:
            venv_python = Path(tmpdir) / "python"
            venv_python.touch()
            target_script = Path(tmpdir) / "target.py"
            target_script.touch()
            wrapper_path = Path(tmpdir) / "wrapper"

            # Install once
            install_module.install_wrapper_script(venv_python, target_script, wrapper_path)
            content1 = wrapper_path.read_text()

            # Install again
            install_module.install_wrapper_script(venv_python, target_script, wrapper_path)
            content2 = wrapper_path.read_text()

            # Should be identical
            self.assertEqual(content1, content2)

    def test_plist_template_exists(self):
        """Test that LaunchAgent plist template exists."""
        plist_path = self.project_root / "etc" / "com.leosimons.start-the-day.plist"
        self.assertTrue(plist_path.exists())

    def test_plist_template_has_username_placeholder(self):
        """Test that plist template has username placeholder."""
        plist_path = self.project_root / "etc" / "com.leosimons.start-the-day.plist"
        content = plist_path.read_text()
        self.assertIn("/Users/lsimons/", content)

    def test_plist_template_is_valid_xml(self):
        """Test that plist template is valid XML."""
        import xml.etree.ElementTree as ET

        plist_path = self.project_root / "etc" / "com.leosimons.start-the-day.plist"

        try:
            tree = ET.parse(plist_path)
            root = tree.getroot()
            self.assertEqual(root.tag, "plist")
        except ET.ParseError as e:
            self.fail(f"Plist template is not valid XML: {e}")

    def test_plist_template_has_required_keys(self):
        """Test that plist template has required LaunchAgent keys."""
        plist_path = self.project_root / "etc" / "com.leosimons.start-the-day.plist"
        content = plist_path.read_text()

        required_keys = [
            "Label",
            "ProgramArguments",
            "StartCalendarInterval",
            "StandardOutPath",
            "StandardErrorPath",
        ]

        for key in required_keys:
            self.assertIn(f"<key>{key}</key>", content)

    def test_install_script_checks_venv_exists(self):
        """Test that install script verifies virtual environment exists."""
        content = self.install_script.read_text()
        self.assertIn("venv_python", content)
        self.assertIn(".venv", content)
        self.assertIn("exists()", content)

    def test_install_script_checks_scripts_exist(self):
        """Test that install script verifies target scripts exist."""
        content = self.install_script.read_text()
        self.assertIn("start_the_day.py", content)
        self.assertIn("lsimons_auto.py", content)
        self.assertIn("exists()", content)

    def test_install_script_creates_directories(self):
        """Test that install script creates necessary directories."""
        content = self.install_script.read_text()
        self.assertIn(".local/bin", content)
        self.assertIn(".local/log", content)
        self.assertIn("mkdir", content)

    def test_install_script_handles_missing_venv(self):
        """Test that install script exits if venv is missing."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)

        # Mock Path to simulate missing venv
        with patch("pathlib.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.parent.absolute.return_value = mock_path
            mock_path.__truediv__ = lambda self, other: mock_path  # pyright: ignore[reportUnknownLambdaType]
            mock_path.exists.return_value = False  # Simulate missing files
            mock_path_class.return_value = mock_path
            mock_path_class.__file__ = str(self.install_script)

            with self.assertRaises(SystemExit):
                spec.loader.exec_module(install_module)
                install_module.install_scripts()

    def test_main_function_exists(self):
        """Test that main function is defined."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("install", self.install_script)
        if spec is None or spec.loader is None:
            self.fail("Could not load install.py module")

        install_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install_module)

        self.assertTrue(hasattr(install_module, "main"))
        self.assertTrue(callable(install_module.main))

    def test_install_script_output_messages(self):
        """Test that install script provides helpful output messages."""
        content = self.install_script.read_text()

        # Should have informative messages
        self.assertIn("Installing", content)
        self.assertIn("Creating", content)
        self.assertIn("successfully", content)
        self.assertIn("PATH", content)


if __name__ == "__main__":
    unittest.main()
