"""Tests for the middleware framework plugin registry."""

from importlib import import_module

import pytest

frameworks_module = import_module("modules.free.essentials.middleware.frameworks")

discover_external_plugins = frameworks_module.discover_external_plugins
get_plugin = frameworks_module.get_plugin
list_available_plugins = frameworks_module.list_available_plugins
refresh_plugin_registry = frameworks_module.refresh_plugin_registry

fastapi_plugins = import_module("modules.free.essentials.middleware.frameworks.fastapi")
nestjs_plugins = import_module("modules.free.essentials.middleware.frameworks.nestjs")

FastAPIPlugin = fastapi_plugins.FastAPIPlugin
FastAPIStandardPlugin = fastapi_plugins.FastAPIStandardPlugin
FastAPIDDDPlugin = fastapi_plugins.FastAPIDDDPlugin
NestJSPlugin = nestjs_plugins.NestJSPlugin
NestJSStandardPlugin = nestjs_plugins.NestJSStandardPlugin


class TestMiddlewarePluginRegistry:
    """Validate middleware registry exposes alias plugins."""

    def setup_method(self) -> None:  # noqa: D401 - pytest lifecycle hook
        refresh_plugin_registry(auto_discover=False)

    def test_list_available_plugins_includes_aliases(self) -> None:
        plugins = list_available_plugins()
        expected = {
            "fastapi": "FastAPI",
            "fastapi.standard": "FastAPI (standard kit)",
            "fastapi.ddd": "FastAPI (DDD kit)",
            "nestjs": "NestJS",
            "nestjs.standard": "NestJS (standard kit)",
        }
        for key, label in expected.items():
            assert plugins.get(key) == label

    def test_get_plugin_returns_alias_types(self) -> None:
        assert isinstance(get_plugin("fastapi"), FastAPIPlugin)
        assert isinstance(get_plugin("fastapi.standard"), FastAPIStandardPlugin)
        assert isinstance(get_plugin("fastapi.ddd"), FastAPIDDDPlugin)
        assert isinstance(get_plugin("nestjs"), NestJSPlugin)
        assert isinstance(get_plugin("nestjs.standard"), NestJSStandardPlugin)

    def test_unknown_plugin_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown framework"):
            get_plugin("unknown")

    def test_discover_external_plugins_registers_entry_points(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from modules.shared.frameworks.base import FrameworkPlugin  # type: ignore

        class ExternalPlugin(FrameworkPlugin):
            @property
            def name(self) -> str:  # pragma: no cover - simple property
                return "external"

            @property
            def language(self) -> str:  # pragma: no cover - simple property
                return "python"

            @property
            def display_name(self) -> str:  # pragma: no cover - simple property
                return "External"

            def get_template_mappings(self) -> dict[str, str]:  # pragma: no cover - tests
                return {}

            def get_output_paths(self) -> dict[str, str]:  # pragma: no cover - tests
                return {}

            def get_context_enrichments(self, base_context: dict[str, str]) -> dict[str, str]:
                return base_context

            def validate_requirements(self) -> list[str]:  # pragma: no cover - tests
                return []

        entry_point = type("EP", (), {"name": "external", "load": lambda: ExternalPlugin})

        refresh_plugin_registry(auto_discover=False)
        discovered = discover_external_plugins([entry_point])
        try:
            assert "ExternalPlugin" in discovered
            assert "external" in list_available_plugins()
        finally:
            refresh_plugin_registry(auto_discover=False)


__all__ = ["TestMiddlewarePluginRegistry"]
