"""Tests for the NestJS standard kit generator."""

from pathlib import Path

import pytest

from core.config.kit_config import KitConfig, StructureItem, Variable, VariableType
from kits.nestjs.standard.generator import NestJSStandardGenerator
from kits.shared import get_settings_vendor_metadata

EXPECTED_MINIMAL_FILES = 2


@pytest.fixture()
def minimal_nestjs_config() -> KitConfig:
    """Create a minimal kit configuration for testing."""
    return KitConfig(
        name="nestjs-standard",
        display_name="NestJS Standard",
        description="NestJS standard kit for testing",
        version="0.1.0",
        min_rapidkit_version="0.0.1",
        category="web",
        tags=["nestjs", "standard"],
        dependencies={},
        modules=[],
        variables=[
            Variable(name="project_name", type=VariableType.STRING, required=True),
            Variable(
                name="package_manager",
                type=VariableType.CHOICE,
                default="npm",
                choices=["npm", "yarn", "pnpm"],
            ),
        ],
        structure=[
            StructureItem(path="README.md", template="README.md.j2"),
            StructureItem(path="src/main.ts", template="src/main.ts.j2"),
        ],
        hooks={},
    )


@pytest.fixture()
def minimal_kit_dir(tmp_path: Path) -> Path:
    kit_root = tmp_path / "nestjs-standard"
    templates = kit_root / "templates" / "src"
    templates.mkdir(parents=True)

    (kit_root / "templates" / "README.md.j2").write_text(
        "# {{ project_name }}\n",
        encoding="utf-8",
    )
    (templates / "main.ts.j2").write_text(
        "console.log('{{ project_name }}');\n",
        encoding="utf-8",
    )

    return kit_root


class TestNestJSStandardGenerator:
    def test_validate_variables_success(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        variables = {"project_name": "nestjs_app", "package_manager": "npm"}
        generator._validate_variables(variables)

    def test_validate_variables_missing_project_name(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        with pytest.raises(ValueError, match="Variable 'project_name' is required"):
            generator._validate_variables({"package_manager": "npm"})

    def test_validate_variables_invalid_name(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        with pytest.raises(ValueError, match="Project name should contain only letters"):
            generator._validate_variables({"project_name": "invalid name"})

    def test_validate_variables_invalid_package_manager(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        with pytest.raises(ValueError, match="package_manager must be one of"):
            generator._validate_variables({"project_name": "nestjs", "package_manager": "pip"})

    def test_extra_context_contains_expected_keys(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        context = generator.extra_context()
        expected_keys = {
            "has_postgres",
            "has_mysql",
            "has_sqlite",
            "has_mongodb",
            "has_redis",
            "has_monitoring",
            "has_logging",
            "has_testing",
            "has_docs",
            "has_docker",
            "has_ci",
            "package_manager",
            "package_manager_command",
            "auth_jwt",
            "auth_oauth2",
            "selected_modules",
            "runtime",
            "node_version",
            "rapidkit_vendor_module",
            "rapidkit_vendor_version",
            "rapidkit_vendor_root",
        }
        assert expected_keys.issubset(context.keys())

    def test_extra_context_provides_vendor_metadata(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        context = generator.extra_context()
        vendor_meta = get_settings_vendor_metadata()

        assert context["rapidkit_vendor_module"] == vendor_meta["module_name"]
        assert context["rapidkit_vendor_version"] == vendor_meta["version"]
        assert context["rapidkit_vendor_root"] == vendor_meta["vendor_root"]

    def test_extra_context_preserves_package_manager(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig, tmp_path: Path
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        output_dir = tmp_path / "pm-app"
        output_dir.mkdir()

        generator.generate(output_dir, {"project_name": "pm-app", "package_manager": "yarn"})
        context = generator.extra_context()

        assert context["package_manager"] == "yarn"
        assert context["package_manager_command"] == "yarn"

    def test_generate_creates_files(
        self, minimal_kit_dir: Path, minimal_nestjs_config: KitConfig, tmp_path: Path
    ) -> None:
        generator = NestJSStandardGenerator(minimal_kit_dir, minimal_nestjs_config)
        output_dir = tmp_path / "generated"
        output_dir.mkdir()

        variables = {"project_name": "sample-app", "package_manager": "npm"}
        created = generator.generate(output_dir, variables)

        assert len(created) == EXPECTED_MINIMAL_FILES
        assert (output_dir / "README.md").exists()
        assert (output_dir / "src/main.ts").exists()
        readme = (output_dir / "README.md").read_text(encoding="utf-8")
        assert "sample-app" in readme
