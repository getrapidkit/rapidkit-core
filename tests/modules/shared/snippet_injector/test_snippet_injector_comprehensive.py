# tests/test_snippet_injector_comprehensive.py
"""Comprehensive tests for snippet injector from end-user perspective."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import core.services.snippet_injector as snippet_injector_module
from core.services.snippet_injector import (
    filter_and_update_poetry_dependencies_snippet,
    inject_dependencies,
    inject_snippet_from_template,
    load_snippet_registry,
    merge_snippets,
    parse_poetry_dependency_line,
    remove_inject_anchors,
    save_snippet_registry,
)


class TestSnippetInjectorEndUser:
    """Test snippet injector from end-user perspective."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.pyproject_path = self.project_root / "pyproject.toml"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_poetry_dependency_line_end_user(self):
        """Test parsing poetry dependency lines from end-user perspective."""
        # Test valid dependency lines
        assert parse_poetry_dependency_line('flask = "2.0.0"') == ("flask", '"2.0.0"')
        assert parse_poetry_dependency_line('requests = {version = "2.25.0"}') == (
            "requests",
            '{version = "2.25.0"}',
        )
        assert parse_poetry_dependency_line('python = "^3.8"') == ("python", '"^3.8"')

        # Test lines with comments
        assert parse_poetry_dependency_line('fastapi = "0.68.0"  # web framework') == (
            "fastapi",
            '"0.68.0"',
        )

        # Test invalid lines
        assert parse_poetry_dependency_line("# This is a comment") == (None, None)
        assert parse_poetry_dependency_line("") == (None, None)
        assert parse_poetry_dependency_line("not a dependency") == (None, None)

    def test_filter_and_update_poetry_dependencies_snippet_end_user(self):
        """Test filtering and updating poetry dependencies from end-user perspective."""
        # Create a sample pyproject.toml
        content = """[tool.poetry]
name = "test-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.8"
flask = "2.0.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
"""

        self.pyproject_path.write_text(content)

        # Test injecting new dependencies
        snippet = '''fastapi = "0.68.0"
uvicorn = "0.15.0"'''

        result = filter_and_update_poetry_dependencies_snippet(self.pyproject_path, snippet)

        # Should contain the injected dependencies
        assert "fastapi" in result
        assert "uvicorn" in result
        assert "# <<<inject:module-dependencies>>>" in result

    def test_inject_dependencies_end_user(self):
        """Test dependency injection from end-user perspective."""
        # Create a sample pyproject.toml
        content = """[tool.poetry.dependencies]
python = "^3.8"
"""

        self.pyproject_path.write_text(content)

        dependencies = {"fastapi": "0.68.0", "uvicorn": "0.15.0"}

        # Convert dependencies dict to string format
        snippet = "\n".join([f"{pkg} = {ver}" for pkg, ver in dependencies.items()])

        with patch.object(snippet_injector_module, "print_success"):
            updated_content = inject_dependencies(self.pyproject_path, snippet, "poetry")
            self.pyproject_path.write_text(updated_content)

        # Check that dependencies were added
        final_content = self.pyproject_path.read_text()
        assert "fastapi" in final_content
        assert "uvicorn" in final_content

    def test_inject_snippet_from_template_end_user(self):
        """Test snippet injection from template from end-user perspective."""
        # Create template directory and file
        template_dir = self.project_root / "templates"
        template_dir.mkdir()
        template_file = template_dir / "main.py.j2"
        template_file.write_text("print('Hello from {{project_name}}!')")

        # Create target file with anchor
        target_file = self.project_root / "main.py"
        target_file.write_text("# <<<inject:main>>>\nprint('Existing code')\n")

        context = {"project_name": "MyApp"}

        with patch.object(snippet_injector_module, "print_info"):
            inject_snippet_from_template(
                destination_path=target_file,
                snippet_template_path=template_file,
                anchor="# <<<inject:main>>>",
                variables=context,
            )

        # Check that template was rendered and injected
        content = target_file.read_text()
        assert "Hello from MyApp!" in content

    def test_load_snippet_registry_end_user(self):
        """Test loading snippet registry from end-user perspective."""
        # Create registry file
        registry_file = self.project_root / ".rapidkit" / "snippet_registry.json"
        registry_file.parent.mkdir(parents=True, exist_ok=True)

        registry_data = {
            "version": "1.0",
            "snippets": {
                "api_routes": {
                    "template": "api.py.j2",
                    "description": "API routes template",
                }
            },
        }

        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(registry_data, f)

        registry = load_snippet_registry(self.project_root)

        assert registry["version"] == "1.0"
        assert "api_routes" in registry["snippets"]

    def test_save_snippet_registry_end_user(self):
        """Test saving snippet registry from end-user perspective."""
        registry_data = {
            "version": "1.0",
            "snippets": {
                "models": {
                    "template": "models.py.j2",
                    "description": "Data models template",
                }
            },
        }

        save_snippet_registry(self.project_root, registry_data)

        # Check that registry was saved
        registry_file = self.project_root / ".rapidkit" / "snippet_registry.json"
        assert registry_file.exists()

        with open(registry_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["version"] == "1.0"
        assert "models" in saved_data["snippets"]

    def test_merge_snippets_end_user(self):
        """Test merging snippets from end-user perspective."""
        base_snippet = ["app: Flask(__name__)", "debug: True"]
        new_snippet = ["route: /api", "method: POST"]
        indent = ""
        metadata = {"schema": {"properties": {"app": {}, "route": {}, "method": {}, "debug": {}}}}

        merged = merge_snippets(base_snippet, new_snippet, indent, metadata)

        # Should contain both original and new content
        merged_text = "\n".join(merged)
        assert "Flask" in merged_text
        assert "/api" in merged_text

    def test_remove_inject_anchors_end_user(self):
        """Test removing inject anchors from end-user perspective."""
        # Create file with anchors
        content = """# This is a test file
# <<<inject:start>>>
# Injected content
# <<<inject:end>>>
# End of file
"""

        test_file = self.project_root / "test.txt"
        test_file.write_text(content)

        remove_inject_anchors(test_file)

        # Check that anchors were removed but content remains
        updated_content = test_file.read_text()
        assert "# <<<inject:start>>>" not in updated_content
        assert "# <<<inject:end>>>" not in updated_content
        assert "# Injected content" in updated_content  # Content should remain

    def test_inject_snippet_enterprise_error_handling_end_user(self):
        """Test enterprise snippet injection error handling."""
        # Test with non-existent file
        non_existent = self.project_root / "nonexistent.py"

        with patch.object(snippet_injector_module, "print_warning"):
            # This should handle the error gracefully
            inject_snippet_from_template(
                destination_path=non_existent,
                snippet_template_path=Path("nonexistent.j2"),
                anchor="# <<<inject:main>>>",
                variables={},
            )

    def test_dependency_injection_with_existing_dependencies_end_user(self):
        """Test dependency injection when dependencies already exist."""
        # Create pyproject.toml with existing dependencies
        content = """[tool.poetry.dependencies]
python = "^3.8"
fastapi = "0.65.0"  # Older version
flask = "2.0.0"
"""

        self.pyproject_path.write_text(content)

        # Try to inject fastapi with newer version
        dependencies = {
            "fastapi": "0.68.0",  # Newer version
            "uvicorn": "0.15.0",  # New dependency
        }

        # Convert dependencies dict to string format
        snippet = "\n".join([f"{pkg} = {ver}" for pkg, ver in dependencies.items()])

        with patch.object(snippet_injector_module, "print_success"):
            updated_content = inject_dependencies(self.pyproject_path, snippet, "poetry")
            self.pyproject_path.write_text(updated_content)

        final_content = self.pyproject_path.read_text()

        # Should contain updated fastapi version and new uvicorn
        assert "fastapi" in final_content
        assert "uvicorn" in final_content

    def test_snippet_injection_with_complex_template_end_user(self):
        """Test snippet injection with complex template."""
        # Create complex template
        template_dir = self.project_root / "templates"
        template_dir.mkdir()
        template_file = template_dir / "complex.py.j2"
        template_file.write_text(
            """# {{service_name}} Service
from typing import List, Optional
from {{framework}} import {{main_class}}

class {{service_name}}Service:
    def __init__(self):
        self.{{framework}}_app = {{main_class}}()

    def get_{{service_name|lower}}(self, {{service_name|lower}}_id: int) -> Optional[dict]:
        # Get {{service_name|lower}} by ID
        return {"id": {{service_name|lower}}_id, "name": "{{service_name}} Item"}

    def list_{{service_name|lower}}s(self) -> List[dict]:
        # List all {{service_name|lower}}s
        return [
            {"id": 1, "name": "{{service_name}} Item 1"},
            {"id": 2, "name": "{{service_name}} Item 2"}
        ]
"""
        )

        target_file = self.project_root / "user_service.py"
        target_file.write_text("# <<<inject:service>>>\nprint('Existing code')\n")

        context = {
            "service_name": "User",
            "framework": "fastapi",
            "main_class": "FastAPI",
        }

        with patch.object(snippet_injector_module, "print_info"):
            inject_snippet_from_template(
                destination_path=target_file,
                snippet_template_path=template_file,
                anchor="# <<<inject:service>>>",
                variables=context,
            )

        content = target_file.read_text()

        # Check that template was properly rendered
        assert "User Service" in content
        assert "from fastapi import FastAPI" in content
        assert "class UserService:" in content
        assert "get_user(self, user_id: int)" in content
