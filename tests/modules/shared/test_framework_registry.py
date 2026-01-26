from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

import pytest

from modules.shared.frameworks.base import FrameworkPlugin
from modules.shared.frameworks.registry import PluginRegistry


class _BasePlugin(FrameworkPlugin):
    should_fail = False

    def __init__(self) -> None:  # pragma: no cover - exercised in subclasses
        if type(self).should_fail:  # pragma: no branch - deterministic flag
            raise ValueError("forced failure")

    @property
    def name(self) -> str:
        return "base"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "Base"

    def get_template_mappings(self) -> Dict[str, str]:
        return {"example": "templates/example.j2"}

    def get_output_paths(self) -> Dict[str, str]:
        return {"example": "src/core/example.py"}

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(base_context)

    def validate_requirements(self) -> list[str]:
        return []


class ExamplePlugin(_BasePlugin):
    @property
    def name(self) -> str:
        return "example"

    @property
    def display_name(self) -> str:
        return "Example"


class DuplicateNamePlugin(_BasePlugin):
    @property
    def name(self) -> str:
        return "example"


class FailingInitPlugin(_BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        raise TypeError("missing arguments")

    @property
    def name(self) -> str:
        return "broken"


class FlakyPlugin(_BasePlugin):
    should_fail = False

    @property
    def name(self) -> str:
        return "flaky"


class MissingDisplayPlugin(_BasePlugin):
    @property
    def name(self) -> str:
        return "nodisplay"

    @property
    def display_name(self) -> str:
        raise AttributeError("display not available")


class ReportingPlugin(_BasePlugin):
    @property
    def name(self) -> str:
        return "reporting"

    def validate_requirements(self) -> list[str]:
        return ["needs dependency"]


@dataclass
class _FakeEntryPoint:
    loaded: object

    def load(self) -> object:
        return self.loaded


def test_register_and_lookup_roundtrip() -> None:
    registry = PluginRegistry()
    registry.register(ExamplePlugin)

    plugin = registry.get("example")
    assert isinstance(plugin, ExamplePlugin)

    assert registry.get_class("example") is ExamplePlugin
    assert registry.is_available("example") is True
    assert registry.list_available() == {"example": "Example"}


def test_register_rejects_duplicate_name() -> None:
    registry = PluginRegistry()
    registry.register(ExamplePlugin)

    with pytest.raises(ValueError):
        registry.register(DuplicateNamePlugin)


def test_register_raises_when_instantiation_fails() -> None:
    registry = PluginRegistry()

    with pytest.raises(ValueError):
        registry.register(FailingInitPlugin)


def test_get_raises_for_unknown_framework() -> None:
    registry = PluginRegistry()

    with pytest.raises(ValueError):
        registry.get("missing")


def test_get_raises_when_instantiation_fails() -> None:
    registry = PluginRegistry()
    registry.register(FlakyPlugin)

    FlakyPlugin.should_fail = True
    with pytest.raises(RuntimeError):
        registry.get("flaky")
    FlakyPlugin.should_fail = False


def test_list_available_falls_back_to_key() -> None:
    registry = PluginRegistry()
    registry.register(MissingDisplayPlugin)

    assert registry.list_available() == {"nodisplay": "nodisplay"}


def test_validate_all_collects_results() -> None:
    registry = PluginRegistry()
    registry.register(ReportingPlugin)

    results = registry.validate_all()
    assert results == {"reporting": ["needs dependency"]}


def test_discover_with_entry_points() -> None:
    registry = PluginRegistry(entry_point_group="rapidkit")
    registry.register(ExamplePlugin)

    class ExternalPlugin(_BasePlugin):
        @property
        def name(self) -> str:
            return "external"

    entry_points = [
        _FakeEntryPoint(ExternalPlugin),
        _FakeEntryPoint(object),
        _FakeEntryPoint(DuplicateNamePlugin),
    ]

    registered = registry.discover(entry_points=entry_points)  # type: ignore[arg-type]
    assert "ExternalPlugin" in registered
    assert registry.is_available("external") is True


def test_discover_without_group_returns_empty() -> None:
    registry = PluginRegistry()
    assert registry.discover() == []


def test_reset_and_refresh_respects_builtins() -> None:
    registry = PluginRegistry()
    registry.register(ExamplePlugin)

    registry.refresh(builtins=(ReportingPlugin,), auto_discover=False)
    assert registry.is_available("example") is False
    assert registry.is_available("reporting") is True


def test_framework_plugin_defaults_expose_empty_hooks(tmp_path) -> None:
    plugin = ExamplePlugin()

    assert plugin.get_dependencies() == []
    assert plugin.get_dev_dependencies() == []
    plugin.pre_generation_hook(tmp_path)
    plugin.post_generation_hook(tmp_path)
    assert plugin.get_documentation_urls() == {}
    assert plugin.get_example_configurations() == {}
