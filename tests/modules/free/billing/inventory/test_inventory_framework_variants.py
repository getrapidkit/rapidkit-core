"""Framework variant expectations for Inventory."""

from __future__ import annotations

from src.modules.free.billing.inventory.frameworks import (
    get_plugin,
    list_available_plugins,
    validate_all_plugins,
)


def test_variants_declared(module_config: dict[str, object]) -> None:
    variants = module_config.get("generation", {}).get("variants", {})  # type: ignore[assignment]
    assert isinstance(variants, dict)
    assert "fastapi" in variants
    assert "nestjs" in variants


def test_fastapi_files_listed(module_config: dict[str, object]) -> None:
    fastapi_variants = module_config["generation"]["variants"]["fastapi"]  # type: ignore[index]
    files = fastapi_variants.get("files", [])
    assert any(
        entry.get("output") == "src/modules/free/billing/inventory/inventory.py" for entry in files
    )


def test_nestjs_files_listed(module_config: dict[str, object]) -> None:
    nest_variants = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nest_variants.get("files", [])
    assert any(
        entry.get("output") == "src/modules/free/billing/inventory/inventory.service.ts"
        for entry in files
    )


def test_framework_plugins_registered() -> None:
    plugins = list_available_plugins()
    assert "fastapi" in plugins
    assert "nestjs" in plugins


def test_plugin_validation_executes() -> None:
    plugin = get_plugin("fastapi")
    assert plugin.display_name == "FastAPI"
    result = validate_all_plugins()
    assert "fastapi" in result
