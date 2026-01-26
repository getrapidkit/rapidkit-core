from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.free.database.db_sqlite.frameworks import (
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
from modules.free.database.db_sqlite.frameworks.fastapi import FastAPIPlugin
from modules.free.database.db_sqlite.frameworks.nestjs import NestJSPlugin, NestJSStandardPlugin
from modules.shared.frameworks import FrameworkPlugin


def test_registry_refresh_and_lookup() -> None:
    refresh_plugin_registry(auto_discover=False)
    available = list_available_plugins()
    assert "fastapi" in available and "nestjs" in available
    assert is_plugin_available("fastapi")
    assert get_plugin_class("nestjs").__name__ == "NestJSPlugin"
    assert get_plugin("fastapi").display_name == "FastAPI"
    assert validate_all_plugins()["nestjs"] == []


def test_nestjs_context_and_mappings() -> None:
    plugin = NestJSPlugin()
    base_context = {
        "module_kebab": "db-sqlite",
        "rapidkit_vendor_configuration_relative": "vendor/config.js",
        "nest_configuration_relative": "cfg.ts",
        "nest_health_controller_relative": "health_ctrl.ts",
        "nest_health_module_relative": "health_mod.ts",
        "nest_test_relative": "tests.ts",
    }
    ctx = plugin.get_context_enrichments(base_context)
    assert ctx["framework"] == "nestjs"
    assert ctx["framework_display_name"] == "NestJS"
    assert ctx["module_kebab"] == "db-sqlite"
    assert ctx["integration_test_relative"] == "tests.ts"
    assert "service" in plugin.get_template_mappings()
    assert "service" in plugin.get_output_paths()


def test_nestjs_pre_generation_creates_structure(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    plugin = NestJSPlugin()
    with caplog.at_level("WARNING"):
        plugin.pre_generation_hook(tmp_path)
    expected_dirs = [
        tmp_path / "src" / "modules" / "free" / "database" / "db_sqlite" / "db-sqlite",
        tmp_path / "src" / "health",
        tmp_path / "nestjs",
        tmp_path / "tests" / "modules" / "integration" / "database",
    ]
    for path in expected_dirs:
        assert path.exists()


def test_nestjs_package_json_invalid(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text("{not json")
    plugin = NestJSPlugin()
    with caplog.at_level("WARNING"):
        plugin._ensure_package_dependencies(package_json)
    assert "invalid JSON" in caplog.text


def test_nestjs_package_json_not_object(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text("[]")
    plugin = NestJSPlugin()
    with caplog.at_level("WARNING"):
        plugin._ensure_package_dependencies(package_json)
    assert "package.json is not a JSON object" in caplog.text


def test_nestjs_package_json_updates_dependencies(tmp_path: Path) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps({"dependencies": {"better-sqlite3": "^0.0.1"}, "devDependencies": {}})
    )
    plugin = NestJSPlugin()
    plugin._ensure_package_dependencies(package_json)
    data = json.loads(package_json.read_text())
    assert data["dependencies"]["better-sqlite3"] == "^12.5.0"
    assert data["devDependencies"]["@types/better-sqlite3"] == "^7.6.13"


def test_nestjs_locate_package_json_walks_parents(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "child"
    nested.mkdir(parents=True)
    package_json = tmp_path / "nested" / "package.json"
    package_json.write_text("{}")
    plugin = NestJSPlugin()
    found = plugin._locate_package_json(nested)
    assert found == package_json


def test_nestjs_standard_alias_properties() -> None:
    plugin = NestJSStandardPlugin()
    assert plugin.name == "nestjs.standard"
    assert plugin.display_name.startswith("NestJS")


def test_register_plugin_wrapper_registers_fastapi() -> None:
    refresh_plugin_registry(auto_discover=False)
    register_plugin(FastAPIPlugin)
    assert is_plugin_available("fastapi")
    assert get_plugin("fastapi").display_name == "FastAPI"


def test_discover_external_plugins_registers_custom_entrypoint() -> None:
    class DummyPlugin(FrameworkPlugin):
        @property
        def name(self) -> str:
            return "thirdparty"

        @property
        def language(self) -> str:
            return "python"

        @property
        def display_name(self) -> str:
            return "Third Party"

        def get_template_mappings(self) -> dict[str, str]:
            return {}

        def get_output_paths(self) -> dict[str, str]:
            return {}

        def get_context_enrichments(self, base_context):
            return dict(base_context)

        def validate_requirements(self) -> list[str]:
            return []

    class DummyEntryPoint:
        def __init__(self, target):
            self._target = target

        def load(self):
            return self._target

    refresh_plugin_registry(auto_discover=False)
    registered = discover_external_plugins([DummyEntryPoint(DummyPlugin)])
    assert "DummyPlugin" in registered
    assert is_plugin_available("thirdparty")


def test_get_plugin_info_handles_missing_and_returns_metadata() -> None:
    refresh_plugin_registry(auto_discover=False)
    assert get_plugin_info("missing") is None
    info = get_plugin_info("nestjs")
    assert info is not None
    assert info["name"] == "nestjs"
    assert "better-sqlite3" in info["dependencies"]
    assert info["validation_errors"] == []


def test_nestjs_dependency_lists() -> None:
    plugin = NestJSPlugin()
    assert "@nestjs/common" in plugin.get_dependencies()
    assert plugin.get_dev_dependencies() == ["@types/node"]


def test_nestjs_package_json_missing_logs_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    plugin = NestJSPlugin()
    with caplog.at_level("WARNING"):
        plugin._ensure_package_dependencies(tmp_path / "subdir" / "package.json")
    assert "package.json not found" in caplog.text
