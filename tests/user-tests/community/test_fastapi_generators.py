# tests/test_fastapi_generators.py
"""Test FastAPI kit generators."""

from pathlib import Path

import pytest

import core.exceptions
from core.config.kit_config import KitConfig, StructureItem, Variable, VariableType
from kits.fastapi.standard.generator import FastAPIStandardGenerator

ValidationError = core.exceptions.ValidationError


def _make_minimal_config() -> KitConfig:
    """Create a test config for FastAPI minimal generator."""
    return KitConfig(
        name="fastapi-minimal",
        display_name="FastAPI Minimal",
        description="Minimal FastAPI kit for testing",
        version="0.1.0",
        min_rapidkit_version="0.0.1",
        category="web",
        tags=["fastapi", "minimal"],
        dependencies={},
        modules=[],
        variables=[
            Variable(name="project_name", type=VariableType.STRING, required=True),
        ],
        structure=[
            StructureItem(path="README.md", template="README.md.j2"),
            StructureItem(path="main.py", template="main.py.j2"),
        ],
        hooks={},
    )


@pytest.fixture()
def minimal_kit_dir(tmp_path: Path) -> Path:
    """Create a minimal test kit directory."""
    kt = tmp_path / "fastapi-minimal"
    templates = kt / "templates"
    templates.mkdir(parents=True)

    # Create test templates
    (templates / "README.md.j2").write_text("# {{ project_name }}\n", encoding="utf-8")
    (templates / "main.py.j2").write_text('print("{{ project_name }}")', encoding="utf-8")

    return kt


class TestFastAPIStandardGenerator:
    """Test the FastAPI standard kit generator."""

    def test_validate_variables_success(self, minimal_kit_dir: Path) -> None:
        """Test successful variable validation."""
        config = _make_minimal_config()
        generator = FastAPIStandardGenerator(minimal_kit_dir, config)

        variables = {"project_name": "test_project"}

        # Should not raise any exception
        generator._validate_variables(variables)

    def test_validate_variables_missing_required(self, minimal_kit_dir: Path) -> None:
        """Test validation fails when required variables are missing."""
        config = _make_minimal_config()
        generator = FastAPIStandardGenerator(minimal_kit_dir, config)

        # Missing project_name
        variables = {"secret_key": "my_secret_key"}

        with pytest.raises(ValueError, match="Variable 'project_name' is required"):
            generator._validate_variables(variables)

    def test_validate_variables_empty_values(self, minimal_kit_dir: Path) -> None:
        """Test validation fails when required variables are empty."""
        config = _make_minimal_config()
        generator = FastAPIStandardGenerator(minimal_kit_dir, config)

        # Empty project_name
        variables = {"project_name": ""}

        with pytest.raises(ValueError, match="Variable 'project_name' is required"):
            generator._validate_variables(variables)

    def test_validate_variables_invalid_project_name(self, minimal_kit_dir: Path) -> None:
        """Test validation fails with invalid project name format."""
        config = _make_minimal_config()
        generator = FastAPIStandardGenerator(minimal_kit_dir, config)

        # Invalid project name with special characters
        variables = {"project_name": "test@project!"}

        with pytest.raises(
            ValueError,
            match="Project name should start with a letter and contain only alphanumeric characters or underscores",
        ):
            generator._validate_variables(variables)

    def test_extra_context_returns_standard_context(self, minimal_kit_dir: Path) -> None:
        """Test that extra_context returns standard FastAPI context variables."""
        config = _make_minimal_config()
        generator = FastAPIStandardGenerator(minimal_kit_dir, config)

        context = generator.extra_context()
        expected_keys = [
            "has_postgres",
            "has_sqlite",
            "has_redis",
            "has_monitoring",
            "has_logging",
            "has_settings",
            "has_deployment",
            "has_tracing",
            "has_testing",
            "has_docs",
            "has_docker",
            "has_ci",
            "auth_jwt",
            "auth_oauth2",
            "auth_basic",
            "selected_modules",
        ]
        for key in expected_keys:
            assert key in context

    def test_generate_with_valid_variables(self, minimal_kit_dir: Path, tmp_path: Path) -> None:
        """Test successful generation with valid variables."""
        config = _make_minimal_config()
        generator = FastAPIStandardGenerator(minimal_kit_dir, config)

        out_dir = tmp_path / "generated"
        out_dir.mkdir()

        variables = {"project_name": "my_fastapi_app"}

        files = generator.generate(out_dir, variables)

        # Check that files were created
        EXPECTED_FILES_COUNT = 2
        assert len(files) == EXPECTED_FILES_COUNT
        assert (out_dir / "README.md").exists()
        assert (out_dir / "main.py").exists()

        # Check content rendering
        readme_content = (out_dir / "README.md").read_text()
        main_content = (out_dir / "main.py").read_text()

        assert "my_fastapi_app" in readme_content
        assert "my_fastapi_app" in main_content
