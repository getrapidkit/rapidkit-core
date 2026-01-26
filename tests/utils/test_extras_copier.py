import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core.services.extras_copier as extras_copier_module
from core.services.extras_copier import copy_extra_files, ensure_init_files


@contextlib.contextmanager
def _patched_extras_copier_prints():
    with (
        patch.object(extras_copier_module, "print_warning") as mock_warning,
        patch.object(extras_copier_module, "print_info") as mock_info,
        patch.object(extras_copier_module, "print_success") as mock_success,
    ):
        yield mock_warning, mock_info, mock_success


class TestEnsureInitFiles(unittest.TestCase):
    """Test cases for ensure_init_files function"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_ensure_init_files_creates_missing_init_files(self) -> None:
        """Test that missing __init__.py files are created"""
        # Create nested directory structure
        nested_dir = self.project_root / "src" / "package" / "subpackage"
        nested_dir.mkdir(parents=True)

        destination_file = nested_dir / "module.py"
        destination_file.touch()

        # Ensure init files are created
        ensure_init_files(destination_file, self.project_root)

        # Check that __init__.py files were created
        self.assertTrue((self.project_root / "src" / "__init__.py").exists())
        self.assertTrue((self.project_root / "src" / "package" / "__init__.py").exists())
        # Should not create at subpackage level since it's the immediate parent

    def test_ensure_init_files_skips_existing_init_files(self) -> None:
        """Test that existing __init__.py files are not overwritten"""
        # Create directory with existing __init__.py
        package_dir = self.project_root / "src" / "package"
        package_dir.mkdir(parents=True)

        init_file = package_dir / "__init__.py"
        init_file.write_text("# Existing init file")

        destination_file = package_dir / "module.py"
        destination_file.touch()

        # Ensure init files
        ensure_init_files(destination_file, self.project_root)

        # Check that existing file was not modified
        self.assertEqual(init_file.read_text(), "# Existing init file")

    def test_ensure_init_files_stops_at_project_root(self) -> None:
        """Test that function stops at project root and doesn't go above"""
        destination_file = self.project_root / "main.py"
        destination_file.touch()

        # Ensure init files
        ensure_init_files(destination_file, self.project_root)

        # Should not create __init__.py at project root
        self.assertFalse((self.project_root / "__init__.py").exists())


class TestCopyExtraFiles(unittest.TestCase):
    """Test cases for copy_extra_files function"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()
        self.modules_path = self.temp_dir / "modules"
        self.modules_path.mkdir()

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_copy_extra_files_copies_regular_file(self) -> None:
        """Test copying a regular file (not template)"""
        # Create source file in the correct location for template
        template_dir = self.modules_path / "test_module"
        template_dir.mkdir(parents=True)
        source_file = template_dir / "config.txt"
        source_file.write_text("test content")

        # Setup config
        config = {"migrations": [{"path": "config.txt", "template": "config.txt"}]}

        # Copy files
        with _patched_extras_copier_prints():
            copy_extra_files(
                section="migrations",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
            )

        # Check that file was copied
        dest_file = self.project_root / "config.txt"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "test content")

    def test_copy_extra_files_renders_template(self) -> None:
        """Test rendering a Jinja2 template"""
        # Create template file in the correct location
        template_dir = self.modules_path / "test_module"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "config.txt.j2"
        template_file.write_text("Hello {{ name }}!")

        # Setup config
        config = {"migrations": [{"path": "config.txt", "template": "config.txt.j2"}]}

        variables = {"name": "World"}

        # Copy files
        with _patched_extras_copier_prints():
            copy_extra_files(
                section="migrations",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
                variables=variables,
            )

        # Check that template was rendered
        dest_file = self.project_root / "config.txt"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "Hello World!")

    def test_copy_extra_files_creates_empty_doc_when_no_template(self) -> None:
        """Test creating empty documentation file when no template exists"""
        # Setup config for docs section
        config = {"docs": [{"path": "README.md", "description": "Project README"}]}

        # Copy files
        with _patched_extras_copier_prints():
            copy_extra_files(
                section="docs",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
            )

        # Check that empty doc was created with description
        dest_file = self.project_root / "README.md"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "# Project README\n")

    def test_copy_extra_files_skips_existing_files(self) -> None:
        """Test that existing files are skipped"""
        # Create existing destination file
        dest_file = self.project_root / "existing.txt"
        dest_file.write_text("existing content")

        # Create source file
        template_dir = self.modules_path / "test_module" / "templates"
        template_dir.mkdir(parents=True)
        source_file = template_dir / "existing.txt"
        source_file.write_text("new content")

        # Setup config
        config = {"docs": [{"path": "existing.txt", "template": "existing.txt"}]}

        # Copy files
        with _patched_extras_copier_prints():
            copy_extra_files(
                section="docs",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
            )

        # Check that existing file was not overwritten
        self.assertEqual(dest_file.read_text(), "existing content")

    def test_copy_extra_files_handles_nested_paths(self) -> None:
        """Test handling nested destination paths"""
        # Create source file in the correct location for template
        template_dir = self.modules_path / "test_module"
        template_dir.mkdir(parents=True)
        source_file = template_dir / "nested" / "file.txt"
        source_file.parent.mkdir()
        source_file.write_text("nested content")

        # Setup config
        config = {"docs": [{"path": "docs/api/nested/file.txt", "template": "nested/file.txt"}]}

        # Copy files
        with _patched_extras_copier_prints():
            copy_extra_files(
                section="docs",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
            )

        # Check that file was copied to nested path
        dest_file = self.project_root / "docs" / "api" / "nested" / "file.txt"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "nested content")

        # Check that __init__.py files were created
        self.assertTrue((self.project_root / "docs" / "__init__.py").exists())
        self.assertTrue((self.project_root / "docs" / "api" / "__init__.py").exists())

    def test_copy_extra_files_deduplicates_root_prefix(self) -> None:
        """Ensure destination paths are not prefixed with root twice."""
        template_dir = self.modules_path / "test_module"
        (template_dir / "docs").mkdir(parents=True)
        source_file = template_dir / "docs" / "info.md"
        source_file.write_text("info")

        config = {"docs": [{"path": "src/docs/info.md", "template": "docs/info.md"}]}

        with _patched_extras_copier_prints():
            copy_extra_files(
                section="docs",
                config=config,
                project_root=self.project_root,
                root_path="src",
                name="test_module",
                modules_path=self.modules_path,
            )

        expected = self.project_root / "src" / "docs" / "info.md"
        self.assertTrue(expected.exists())
        self.assertFalse((self.project_root / "src" / "src" / "docs" / "info.md").exists())

    def test_copy_extra_files_handles_ci_cd_nested_structure(self) -> None:
        """Test handling CI/CD nested structure"""
        # Create source files
        template_dir = self.modules_path / "test_module"
        template_dir.mkdir(parents=True)
        ci_file = template_dir / "ci.yml.j2"
        ci_file.write_text("name: {{ name }}")

        # Setup nested CI/CD config
        config = {
            "ci_cd": {"test": [{"path": ".github/workflows/ci.yml", "template": "ci.yml.j2"}]}
        }

        variables = {"name": "Test CI"}

        # Copy files
        with _patched_extras_copier_prints():
            copy_extra_files(
                section="ci_cd",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
                variables=variables,
            )

        # Check that CI file was created and rendered
        dest_file = self.project_root / ".github" / "workflows" / "ci.yml"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "name: Test CI")

    def test_copy_extra_files_handles_missing_source_file(self) -> None:
        """Test handling missing source files gracefully"""
        # Setup config with non-existent template
        config = {"docs": [{"path": "missing.txt", "template": "nonexistent.txt"}]}

        with _patched_extras_copier_prints() as (mock_warning, _, __):
            # Copy files - should not raise exception
            copy_extra_files(
                section="docs",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
            )

            # Check that warning was printed
            mock_warning.assert_called()

    def test_copy_extra_files_handles_invalid_entry(self) -> None:
        """Test handling invalid entry configurations"""
        # Setup config with invalid entry (no path or template)
        config = {"docs": [{"invalid": "entry"}]}

        with _patched_extras_copier_prints() as (mock_warning, _, __):
            # Copy files
            copy_extra_files(
                section="docs",
                config=config,
                project_root=self.project_root,
                root_path=".",
                name="test_module",
                modules_path=self.modules_path,
            )

            # Check that warning was printed for invalid entry
            mock_warning.assert_called()


if __name__ == "__main__":
    unittest.main()
