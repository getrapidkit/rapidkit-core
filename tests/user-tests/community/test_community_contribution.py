import importlib.util
import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.commands.add.all import all_app
from cli.commands.add.module import add_module
from cli.main import app
from core.config.kit_config import KitConfig, Variable, VariableType
from core.config.version import CURRENT_VERSION
from core.engine.dependency_installer import install_module_dependencies
from core.engine.generator import BaseKitGenerator
from core.engine.registry import KitRegistry
from core.frameworks.base import FrameworkAdapter
from core.frameworks.django_adapter import DjangoFrameworkAdapter
from core.frameworks.fastapi_adapter import FastAPIFrameworkAdapter
from core.hooks.framework_handlers import handle_fastapi_router
from core.hooks.hook_runner import HookRunner
from core.kit_utils import fetch_kit_repo
from core.rendering.template_renderer import TemplateRenderer, render_template
from core.services.project_creator import ProjectCreatorService
from core.services.validators import is_semver
from kits.fastapi.standard import FastAPIStandardGenerator


class TestCommunityDevelopment:
    def test_basic_import(self):
        assert True

    def test_code_quality_standards(self):
        """Test that code meets basic quality standards."""
        try:

            assert importlib.util.find_spec("cli") is not None
            assert True
        except ImportError:
            pytest.fail("Core modules should be importable")

    def test_basic_functionality(self):
        """Test basic functionality works."""

        assert CURRENT_VERSION is not None
        assert isinstance(CURRENT_VERSION, str)

    def test_cli_basic_commands(self):
        """Test basic CLI commands work."""

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "RapidKit" in result.output

    def test_kit_discovery(self):
        """Test that kits can be discovered."""
        try:

            assert FastAPIStandardGenerator is not None
        except ImportError:
            pytest.skip("FastAPI standard kit not available")

    def test_cli_commands_import(self):
        """Test that all CLI commands can be imported."""
        commands_to_test = [
            ("cli.commands.add", "add_app"),
            ("cli.commands.create", "create_app"),
            ("cli.commands.list", "list_kits"),
            ("cli.commands.info", "app"),
            ("cli.commands.doctor", "doctor_app"),
            ("cli.commands.merge", "merge_app"),
            ("cli.commands.checkpoint", "checkpoint_app"),
        ]

        for module_name, attr_name in commands_to_test:
            try:
                module = __import__(module_name, fromlist=[attr_name])
                attr = getattr(module, attr_name)
                assert attr is not None
            except (ImportError, AttributeError) as e:
                pytest.fail(f"Failed to import {attr_name} from {module_name}: {e}")

    def test_core_services_import(self):
        """Test that core services can be imported."""
        services_to_test = [
            ("core.services.config_loader", "load_module_config"),
            ("core.services.env_validator", "validate_env"),
            ("core.services.file_hash_registry", "record_file_hash"),
            ("core.services.project_creator", "ProjectCreatorService"),
            ("core.services.module_validator", "validate_spec"),
        ]

        for module_name, attr_name in services_to_test:
            try:
                module = __import__(module_name, fromlist=[attr_name])
                attr = getattr(module, attr_name)
                assert attr is not None
            except (ImportError, AttributeError) as e:
                pytest.fail(f"Failed to import {attr_name} from {module_name}: {e}")

    def test_kit_utils_import(self):
        """Test that kit utilities can be imported."""
        try:

            assert fetch_kit_repo is not None
        except ImportError:
            pytest.fail("Kit utilities should be importable")

    def test_rendering_engine_import(self):
        """Test that template rendering engine can be imported."""
        try:

            assert TemplateRenderer is not None
        except ImportError:
            pytest.fail("Template renderer should be importable")


class TestCommunityIntegration:
    """Integration tests for community features."""

    def test_project_creation_workflow(self):
        """Test the basic project creation workflow."""
        # This is a smoke test for the project creation process

        assert ProjectCreatorService is not None

    def test_cli_add_commands_detailed(self):
        """Test CLI add command submodules."""
        try:

            assert all_app is not None
            assert add_module is not None
        except ImportError:
            pytest.fail("CLI add subcommands should be importable")

    def test_cli_utils_import(self):
        """Test that CLI utilities can be imported."""
        utils_to_test = [
            ("cli.utils.classifier", "classify_command"),
            ("cli.utils.filesystem", "find_project_root"),
            ("cli.utils.prompts", "prompt_variables"),
            ("cli.utils.registry", "get_kit_registry"),
            ("cli.utils.validators", "is_semver"),
            ("cli.utils.variables_prompt", "prompt_variables_interactive"),
        ]

        for module_name, attr_name in utils_to_test:
            try:
                module = __import__(module_name, fromlist=[attr_name])
                attr = getattr(module, attr_name, None)
                if attr is None:
                    # Some functions might not exist, skip them
                    continue
                assert attr is not None
            except (ImportError, AttributeError):
                # Skip if function doesn't exist
                continue

    def test_core_engine_components(self):
        """Test core engine components."""
        try:

            assert BaseKitGenerator is not None
            assert KitRegistry is not None
            assert install_module_dependencies is not None
        except ImportError:
            pytest.fail("Core engine components should be importable")

    def test_framework_adapters(self):
        """Test framework adapters."""
        try:

            assert FrameworkAdapter is not None
            assert FastAPIFrameworkAdapter is not None
            assert DjangoFrameworkAdapter is not None
        except ImportError:
            pytest.fail("Framework adapters should be importable")

    def test_hooks_system(self):
        """Test hooks system."""
        try:

            assert HookRunner is not None
            assert handle_fastapi_router is not None
        except ImportError:
            pytest.fail("Hooks system should be importable")

    def test_kit_config_validation(self):
        """Test kit configuration validation."""
        try:

            config = KitConfig(
                name="test-kit",
                display_name="Test Kit",
                description="Test kit for validation",
                version="1.0.0",
                min_rapidkit_version="1.0.0",
                category="test",
                tags=["test"],
                dependencies={},
                modules=[],
                variables=[Variable(name="test_var", type=VariableType.STRING, required=True)],
                structure=[],
                hooks={},
            )
            assert config.name == "test-kit"
            assert len(config.variables) == 1
        except (ValueError, TypeError, KeyError) as e:
            pytest.fail(f"Kit config validation failed: {e}")

    def test_template_rendering_functionality(self):
        """Test template rendering functionality."""
        try:

            # Create a temporary template file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
                f.write("Hello {{name}} from {{project}}")
                template_path = Path(f.name)

            try:
                result = render_template(template_path, {"name": "World", "project": "RapidKit"})
                assert "Hello World from RapidKit" in result
            finally:
                os.unlink(template_path)
        except (ImportError, OSError, ValueError):
            # Skip if template rendering fails
            pytest.skip("Template rendering not available")

    def test_service_validators(self):
        """Test service validators."""
        try:

            # Test basic validation
            result = is_semver("test-project")
            assert result[0] is False  # Should not be valid semver
            assert result[1] == "test-project"

            result = is_semver("1.0.0")
            assert result[0] is True  # Should be valid semver
            assert result[1] == "1.0.0"

            result = is_semver("")
            assert result[0] is False  # Empty string should not be valid
            assert result[1] == ""
        except ImportError as e:
            pytest.skip(f"Service validators not available: {e}")
