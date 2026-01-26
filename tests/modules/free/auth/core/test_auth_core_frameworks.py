"""Tests for the Auth Core framework plugin registry and implementations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping

import pytest

from modules.free.auth.core.frameworks import (
    discover_external_plugins,
    get_plugin,
    get_plugin_class,
    get_plugin_info,
    is_plugin_available,
    list_available_plugins,
    refresh_plugin_registry,
    register_plugin,
    validate_all_plugins,
)
from modules.free.auth.core.frameworks.fastapi import FastAPIPlugin
from modules.free.auth.core.frameworks.nestjs import NestJSPlugin
from modules.shared.frameworks import FrameworkPlugin

EXPECTED_FASTAPI_ITERATIONS = 390_000


@pytest.fixture(autouse=True)
def reset_auth_core_registry() -> Iterator[None]:
    refresh_plugin_registry(auto_discover=False)
    yield
    refresh_plugin_registry(auto_discover=False)


class StubEntryPoint:
    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def load(self) -> Any:
        return self._obj


class DummyPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "Dummy"

    def get_template_mappings(self) -> Dict[str, str]:
        return {}

    def get_output_paths(self) -> Dict[str, str]:
        return {}

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(base_context)

    def validate_requirements(self) -> List[str]:
        return []


class BadPlugin(FrameworkPlugin):
    def __init__(self, token: str) -> None:  # pragma: no cover - instantiation should fail
        self.token = token

    @property
    def name(self) -> str:
        return "bad"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "Bad"

    def get_template_mappings(self) -> Dict[str, str]:
        return {}

    def get_output_paths(self) -> Dict[str, str]:
        return {}

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(base_context)

    def validate_requirements(self) -> List[str]:
        return []


def test_registry_exposes_builtin_plugins() -> None:
    plugin = get_plugin("fastapi")
    assert isinstance(plugin, FastAPIPlugin)

    assert is_plugin_available("nestjs")
    assert list_available_plugins() == {"fastapi": "FastAPI", "nestjs": "NestJS"}
    assert get_plugin_class("nestjs") is NestJSPlugin

    validation = validate_all_plugins()
    assert validation["fastapi"] == []

    info = get_plugin_info("nestjs")
    assert info and info["display_name"] == "NestJS"
    assert get_plugin_info("missing") is None


def test_register_plugin_behaviour() -> None:
    register_plugin(DummyPlugin)
    assert isinstance(get_plugin("dummy"), DummyPlugin)

    with pytest.raises(ValueError):
        register_plugin(BadPlugin)


def test_discover_external_plugins() -> None:
    class ExternalPlugin(DummyPlugin):
        @property
        def name(self) -> str:
            return "external"

    discover_external_plugins([StubEntryPoint(ExternalPlugin)])  # type: ignore[arg-type]
    assert isinstance(get_plugin("external"), ExternalPlugin)


def test_fastapi_plugin_hooks(tmp_path: Path) -> None:
    plugin = FastAPIPlugin()

    plugin.pre_generation_hook(tmp_path)
    plugin.post_generation_hook(tmp_path)

    health_init = tmp_path / "src" / "health" / "__init__.py"
    assert health_init.exists()
    assert "register_auth_core_health" in health_init.read_text(encoding="utf-8")

    assert plugin.get_documentation_urls()["fastapi"].startswith("https://")
    config = plugin.get_example_configurations()["auth_core"]
    assert config["iterations"] == EXPECTED_FASTAPI_ITERATIONS
    assert "pydantic" in plugin.get_dependencies()[0]
    assert plugin.get_dev_dependencies() == ["pytest>=8.3.0"]


def test_nestjs_plugin_creates_defaults(tmp_path: Path) -> None:
    plugin = NestJSPlugin()
    plugin.pre_generation_hook(tmp_path)
    plugin.post_generation_hook(tmp_path)

    outputs = plugin.get_output_paths()
    assert outputs["validation"] == "src/modules/free/auth/core/config/auth-core.validation.ts"

    tsconfig = tmp_path / "tsconfig.json"
    package_json = tmp_path / "package.json"
    assert tsconfig.exists()
    assert package_json.exists()

    tsconfig_data = json.loads(tsconfig.read_text())
    assert tsconfig_data["compilerOptions"]["module"] == "commonjs"

    package_data = json.loads(package_json.read_text())
    assert "@nestjs/common" in package_data["dependencies"]


def test_nestjs_plugin_updates_existing_files(tmp_path: Path) -> None:
    plugin = NestJSPlugin()

    tsconfig = tmp_path / "tsconfig.json"
    tsconfig.write_text(json.dumps({"compilerOptions": {"module": "ESNext"}}))
    plugin._ensure_tsconfig(tsconfig)
    updated_tsconfig = json.loads(tsconfig.read_text())
    assert updated_tsconfig["compilerOptions"]["module"] == "ESNext"
    assert updated_tsconfig["compilerOptions"]["declaration"] is True

    package_json = tmp_path / "package.json"
    package_json.write_text(json.dumps({"scripts": {}, "dependencies": {"joi": "^17"}}))
    plugin._ensure_package_json(package_json)
    updated_package = json.loads(package_json.read_text())
    assert updated_package["scripts"]["build"] == "nest build"
    assert updated_package["dependencies"]["joi"] == "^17"
    assert updated_package["dependencies"]["@nestjs/core"] == "^11.1.6"


def test_nestjs_plugin_ignores_invalid_files(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    plugin = NestJSPlugin()

    tsconfig = tmp_path / "tsconfig.json"
    tsconfig.write_text("not-json")
    plugin._ensure_tsconfig(tsconfig)
    assert caplog.records[-1].message.startswith("Skipping invalid tsconfig.json")

    package_json = tmp_path / "package.json"
    package_json.write_text("not-json")
    plugin._ensure_package_json(package_json)
    assert caplog.records[-1].message.startswith("Skipping invalid package.json")
