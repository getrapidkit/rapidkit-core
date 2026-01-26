"""Tests for the framework plugin system."""

import json
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest  # type: ignore

frameworks_module = import_module("modules.free.essentials.settings.frameworks")
discover_external_plugins = frameworks_module.discover_external_plugins
get_plugin = frameworks_module.get_plugin
list_available_plugins = frameworks_module.list_available_plugins
refresh_plugin_registry = frameworks_module.refresh_plugin_registry
validate_all_plugins = frameworks_module.validate_all_plugins

fastapi_frameworks = import_module("modules.free.essentials.settings.frameworks.fastapi")
nestjs_frameworks = import_module("modules.free.essentials.settings.frameworks.nestjs")

FastAPIPlugin = fastapi_frameworks.FastAPIPlugin
FastAPIStandardPlugin = fastapi_frameworks.FastAPIStandardPlugin
FastAPIDDDPlugin = fastapi_frameworks.FastAPIDDDPlugin
NestJSPlugin = nestjs_frameworks.NestJSPlugin
NestJSStandardPlugin = nestjs_frameworks.NestJSStandardPlugin


class TestPluginSystem:
    """Test the plugin registry and factory functions."""

    def test_list_available_plugins(self) -> None:
        """Test listing all available plugins."""
        plugins = list_available_plugins()

        assert isinstance(plugins, dict)
        expected = {
            "fastapi": "FastAPI",
            "fastapi.standard": "FastAPI (standard kit)",
            "fastapi.ddd": "FastAPI (DDD kit)",
            "nestjs": "NestJS",
            "nestjs.standard": "NestJS (standard kit)",
        }
        for key, label in expected.items():
            assert plugins.get(key) == label

    def test_get_plugin_fastapi(self) -> None:
        """Test getting FastAPI plugin."""
        plugin = get_plugin("fastapi")

        assert isinstance(plugin, FastAPIPlugin)
        assert plugin.name == "fastapi"
        assert plugin.language == "python"
        assert plugin.display_name == "FastAPI"

    def test_get_plugin_nestjs(self) -> None:
        """Test getting NestJS plugin."""
        plugin = get_plugin("nestjs")

        assert isinstance(plugin, NestJSPlugin)
        assert plugin.name == "nestjs"
        assert plugin.language == "typescript"
        assert plugin.display_name == "NestJS"

    def test_get_plugin_fastapi_standard(self) -> None:
        """Ensure fastapi.standard resolves to the FastAPI alias plugin."""

        plugin = get_plugin("fastapi.standard")

        assert isinstance(plugin, FastAPIStandardPlugin)
        assert plugin.name == "fastapi.standard"
        assert plugin.display_name == "FastAPI (standard kit)"

    def test_get_plugin_fastapi_ddd(self) -> None:
        """Ensure fastapi.ddd resolves to the FastAPI alias plugin."""

        plugin = get_plugin("fastapi.ddd")

        assert isinstance(plugin, FastAPIDDDPlugin)
        assert plugin.name == "fastapi.ddd"
        assert plugin.display_name == "FastAPI (DDD kit)"

    def test_get_plugin_nestjs_standard(self) -> None:
        """Ensure nestjs.standard resolves to the NestJS alias plugin."""

        plugin = get_plugin("nestjs.standard")

        assert isinstance(plugin, NestJSStandardPlugin)
        assert plugin.name == "nestjs.standard"
        assert plugin.display_name == "NestJS (standard kit)"

    def test_get_plugin_unknown(self) -> None:
        """Test getting unknown plugin raises ValueError."""
        with pytest.raises(ValueError, match="Unknown framework 'unknown'"):
            get_plugin("unknown")

    def test_plugin_template_mappings(self) -> None:
        """Test that plugins return correct template mappings."""
        fastapi_plugin = get_plugin("fastapi")
        nestjs_plugin = get_plugin("nestjs")

        fastapi_mappings = fastapi_plugin.get_template_mappings()
        nestjs_mappings = nestjs_plugin.get_template_mappings()

        assert "settings" in fastapi_mappings
        assert "custom_sources" in fastapi_mappings
        assert "hot_reload" in fastapi_mappings

        assert "configuration" in nestjs_mappings
        assert "settings_service" in nestjs_mappings

        # Check that template paths exist
        for template_path in fastapi_mappings.values():
            full_path = Path("src/modules/free/essentials/settings") / template_path
            assert full_path.exists(), f"Template {template_path} does not exist"

        for template_path in nestjs_mappings.values():
            full_path = Path("src/modules/free/essentials/settings") / template_path
            assert full_path.exists(), f"Template {template_path} does not exist"

    def test_plugin_output_paths(self) -> None:
        """Test that plugins return correct output paths."""
        fastapi_plugin = get_plugin("fastapi")
        nestjs_plugin = get_plugin("nestjs")

        fastapi_paths = fastapi_plugin.get_output_paths()
        nestjs_paths = nestjs_plugin.get_output_paths()

        assert fastapi_paths["settings"] == "src/modules/free/essentials/settings/settings.py"
        assert (
            fastapi_paths["custom_sources"]
            == "src/modules/free/essentials/settings/custom_sources.py"
        )
        assert fastapi_paths["hot_reload"] == "src/modules/free/essentials/settings/hot_reload.py"

        assert (
            nestjs_paths["configuration"] == "src/modules/free/essentials/settings/configuration.ts"
        )
        assert (
            nestjs_paths["settings_service"]
            == "src/modules/free/essentials/settings/settings.service.ts"
        )

    def test_plugin_context_enrichments(self) -> None:
        """Test that plugins enrich context correctly."""
        fastapi_plugin = get_plugin("fastapi")
        nestjs_plugin = get_plugin("nestjs")

        base_context = {"rapidkit_vendor_module": "settings", "version": "1.0.0"}

        fastapi_context = fastapi_plugin.get_context_enrichments(base_context)
        nestjs_context = nestjs_plugin.get_context_enrichments(base_context)

        assert fastapi_context["framework"] == "fastapi"
        assert nestjs_context["framework"] == "nestjs"

    @patch("sys.version_info", (3, 10, 0))
    def test_fastapi_validate_requirements_success(self) -> None:
        """Test FastAPI plugin validation when requirements are met."""
        with patch.dict("sys.modules", {"fastapi": Mock(__version__="1.0.0")}):
            plugin = get_plugin("fastapi")
            errors = plugin.validate_requirements()

            assert errors == []

    @patch("sys.version_info", (3, 6, 0))
    def test_fastapi_validate_requirements_old_python(self) -> None:
        """Test FastAPI plugin validation when Python version is too old."""
        plugin = get_plugin("fastapi")
        errors = plugin.validate_requirements()

        assert len(errors) > 0
        assert "Python 3.10+" in " ".join(errors)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_nestjs_validate_requirements_success(self, mock_run: Mock, mock_which: Mock) -> None:
        """Test NestJS plugin validation when requirements are met."""
        mock_which.return_value = "/usr/bin/node"
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n", stderr="")

        plugin = get_plugin("nestjs")
        errors = plugin.validate_requirements()

        assert errors == []

    @patch("shutil.which")
    def test_nestjs_validate_requirements_node_missing(self, mock_which: Mock) -> None:
        """Test NestJS plugin validation when Node.js is not found."""
        mock_which.return_value = None

        plugin = get_plugin("nestjs")
        errors = plugin.validate_requirements()

        assert len(errors) > 0
        assert "Node.js" in " ".join(errors)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_nestjs_validate_requirements_old_version(
        self, mock_run: Mock, mock_which: Mock
    ) -> None:
        """Test NestJS plugin validation when Node.js version is too old."""
        mock_which.return_value = "/usr/bin/node"
        mock_run.return_value = Mock(returncode=0, stdout="v14.0.0\n", stderr="")

        plugin = get_plugin("nestjs")
        errors = plugin.validate_requirements()

        assert len(errors) > 0
        assert "Node.js version" in " ".join(errors)

    def test_validate_all_plugins(self) -> None:
        """Test validating all plugins."""
        results = validate_all_plugins()

        assert isinstance(results, dict)
        expected = ("fastapi", "fastapi.standard", "fastapi.ddd", "nestjs", "nestjs.standard")
        for key in expected:
            assert key in results
            assert isinstance(
                results[key], list
            ), f"Validation result for {key} should be a list of errors"

    def test_plugin_documentation_urls(self) -> None:
        """Test that plugins provide documentation URLs."""
        fastapi_plugin = get_plugin("fastapi")
        nestjs_plugin = get_plugin("nestjs")

        fastapi_urls = fastapi_plugin.get_documentation_urls()
        nestjs_urls = nestjs_plugin.get_documentation_urls()

        assert "framework_docs" in fastapi_urls
        assert "tutorial" in fastapi_urls
        assert "framework_docs" in nestjs_urls
        assert "config_docs" in nestjs_urls

    def test_plugin_post_generation_hook(self, tmp_path: Path) -> None:
        """Test that post-generation hooks can be called without error."""
        fastapi_plugin = get_plugin("fastapi")
        nestjs_plugin = get_plugin("nestjs")

        # Should not raise exceptions
        fastapi_plugin.post_generation_hook(tmp_path)
        nestjs_plugin.post_generation_hook(tmp_path)

    def test_nestjs_pre_generation_hook_merges_existing_files(self, tmp_path: Path) -> None:
        """Ensure NestJS hook augments rather than overwrites existing project files."""
        plugin = get_plugin("nestjs")

        tsconfig_path = tmp_path / "tsconfig.json"
        tsconfig_path.write_text(json.dumps({"compilerOptions": {"module": "esnext"}}, indent=2))

        package_path = tmp_path / "package.json"
        package_path.write_text(json.dumps({"dependencies": {"custom": "1.0.0"}}, indent=2))

        plugin.pre_generation_hook(tmp_path)

        tsconfig_data = json.loads(tsconfig_path.read_text())
        assert tsconfig_data["compilerOptions"]["module"] == "esnext"
        assert "target" in tsconfig_data["compilerOptions"]

        package_data = json.loads(package_path.read_text())
        assert "custom" in package_data["dependencies"]
        assert "@nestjs/core" in package_data["dependencies"]


def test_discover_external_plugins_registers_custom_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """External entry points should be discoverable and registered dynamically."""

    del monkeypatch

    from modules.shared.frameworks.base import FrameworkPlugin  # type: ignore

    class ExternalPlugin(FrameworkPlugin):
        @property
        def name(self) -> str:
            return "external"

        @property
        def language(self) -> str:
            return "python"

        @property
        def display_name(self) -> str:
            return "External"

        def get_template_mappings(self) -> dict[str, str]:
            return {}

        def get_output_paths(self) -> dict[str, str]:
            return {}

        def get_context_enrichments(self, base_context: dict[str, str]) -> dict[str, str]:
            return base_context

        def validate_requirements(self) -> list[str]:
            return []

    entry_point = SimpleNamespace(name="external", load=lambda: ExternalPlugin)

    refresh_plugin_registry(auto_discover=False)
    discovered = discover_external_plugins([entry_point])

    try:
        assert "ExternalPlugin" in discovered
        assert "external" in list_available_plugins()
    finally:
        refresh_plugin_registry()


class TestPluginIntegration:
    """Test plugin integration with the generator."""

    def test_plugin_integration_with_generator(self, tmp_path: Path) -> None:
        """Test that plugins work correctly with the generator."""
        from importlib import import_module

        from modules.shared.generator import TemplateRenderer  # type: ignore[import-not-found]

        generate_module = import_module("modules.free.essentials.settings.generate")
        frameworks_module = import_module("modules.free.essentials.settings.frameworks")

        target_dir = tmp_path / "generated"
        target_dir.mkdir()

        module_config = generate_module.load_module_config()
        base_context = generate_module.build_base_context(module_config)
        renderer = TemplateRenderer(Path("src/modules/free/essentials/settings/templates"))

        original_get_plugin = frameworks_module.get_plugin

        def _get_plugin(name: str):
            plugin = original_get_plugin(name)
            plugin.validate_requirements = lambda: []  # type: ignore[attr-defined]
            return plugin

        with patch.object(generate_module, "get_plugin", side_effect=_get_plugin):
            # Test FastAPI plugin
            generate_module.generate_variant_files("fastapi", target_dir, renderer, base_context)

            # Check that FastAPI files were generated
            fastapi_dir = target_dir / "src" / "modules" / "free" / "essentials" / "settings"
            assert (fastapi_dir / "settings.py").exists()
            assert (fastapi_dir / "custom_sources.py").exists()
            assert (fastapi_dir / "hot_reload.py").exists()
            fastapi_settings = (fastapi_dir / "settings.py").read_text()
            assert "SettingsConfigDict" in fastapi_settings

            # Test NestJS plugin
            generate_module.generate_variant_files("nestjs", target_dir, renderer, base_context)

            # Check that NestJS files were generated
            nest_dir = target_dir / "src" / "modules" / "free" / "essentials" / "settings"
            assert (nest_dir / "configuration.ts").exists()
            assert (nest_dir / "settings.service.ts").exists()
            nestjs_config = (nest_dir / "configuration.ts").read_text()
            assert "registerAs(SETTINGS_CONFIG_KEY" in nestjs_config

    def test_plugin_error_handling(self) -> None:
        """Test that plugins handle errors appropriately."""
        from importlib import import_module

        template_renderer_module = import_module("modules.shared.generator")
        TemplateRenderer = template_renderer_module.TemplateRenderer
        generate_module = import_module("modules.free.essentials.settings.generate")
        GeneratorError = generate_module.GeneratorError
        generate_variant_files = generate_module.generate_variant_files

        # Test with invalid framework
        with pytest.raises(GeneratorError):
            generate_variant_files("invalid", Path("/tmp"), TemplateRenderer(Path("/tmp")), {})

    def test_plugin_context_inheritance(self) -> None:
        """Test that plugins properly inherit and enrich context."""
        fastapi_plugin = get_plugin("fastapi")
        nestjs_plugin = get_plugin("nestjs")

        base_context = {
            "rapidkit_vendor_module": "settings",
            "rapidkit_vendor_version": "1.0.0",
            "custom_field": "test_value",
        }

        fastapi_enriched = fastapi_plugin.get_context_enrichments(base_context)
        nestjs_enriched = nestjs_plugin.get_context_enrichments(base_context)

        # Check that base context is preserved
        assert fastapi_enriched["rapidkit_vendor_module"] == "settings"
        assert fastapi_enriched["custom_field"] == "test_value"
        assert nestjs_enriched["rapidkit_vendor_module"] == "settings"
        assert nestjs_enriched["custom_field"] == "test_value"

        # Check that framework-specific context is added
        assert fastapi_enriched["framework"] == "fastapi"
        assert nestjs_enriched["framework"] == "nestjs"
