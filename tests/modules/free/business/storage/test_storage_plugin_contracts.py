from __future__ import annotations

from modules.free.business.storage.frameworks import (
    discover_external_plugins,
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
)


def test_storage_builtin_plugin_registry_contract() -> None:
    refresh_plugin_registry(auto_discover=False)

    available = list_available_plugins()

    assert available == {"fastapi": "FastAPI", "nestjs": "NestJS"}
    assert discover_external_plugins([]) == []


def test_storage_fastapi_plugin_contract() -> None:
    refresh_plugin_registry(auto_discover=False)
    plugin = get_plugin("fastapi")

    assert plugin.language == "python"
    assert plugin.validate_requirements() == []
    assert plugin.get_template_mappings()["routes"].endswith("storage_routes.py.j2")
    assert plugin.get_output_paths()["health"] == "src/health/storage.py"
    assert "python-multipart>=0.0.5" in plugin.get_dependencies()
    assert "pytest>=9.0.3,<10.0" in plugin.get_dev_dependencies()
    assert plugin.get_context_enrichments({})["route_prefix"] == "/api/v1/storage"


def test_storage_nestjs_plugin_contract(tmp_path) -> None:  # type: ignore[no-untyped-def]
    refresh_plugin_registry(auto_discover=False)
    plugin = get_plugin("nestjs")

    assert plugin.language == "typescript"
    assert plugin.validate_requirements() == []
    assert plugin.get_template_mappings()["health"].endswith("storage.health.ts.j2")
    assert (
        plugin.get_output_paths()["service"]
        == "src/modules/free/business/storage/storage.service.ts"
    )
    assert "@nestjs/common@^10.0.0" in plugin.get_dependencies()
    assert "@nestjs/testing@^10.0.0" in plugin.get_dev_dependencies()
    assert plugin.get_context_enrichments({})["module_service_class"] == "StorageService"

    plugin.pre_generation_hook(tmp_path)

    assert (tmp_path / "src/modules/free/business/storage").is_dir()
    assert (tmp_path / "tests/modules/integration/business").is_dir()
