"""Standard module metadata checks for Inventory."""

from __future__ import annotations

from pathlib import Path


def test_documentation_links_present(module_docs: dict[str, object]) -> None:
    expected = [
        "readme",
        "overview",
        "usage",
        "advanced",
        "migration",
        "troubleshooting",
        "api_docs",
    ]
    for key in expected:
        assert key in module_docs, f"documentation.{key} missing"
        if key == "api_docs":
            continue
        assert module_docs.get(key), f"documentation.{key} must be set"


def test_unit_tests_list(module_config: dict[str, object]) -> None:
    unit_tests = module_config.get("testing", {}).get("unit_tests", [])  # type: ignore[assignment]
    normalized = {Path(test_path).name for test_path in unit_tests}
    expected = [
        "test_inventory_generator.py",
        "test_inventory_overrides.py",
        "test_inventory_runtime.py",
        "test_inventory_adapters.py",
        "test_inventory_validation.py",
        "test_inventory_error_handling.py",
        "test_inventory_health_check.py",
        "test_inventory_framework_variants.py",
        "test_inventory_vendor_layer.py",
        "test_inventory_configuration.py",
        "test_inventory_versioning.py",
        "test_inventory_integration.py",
        "test_inventory_standard_module.py",
    ]
    for name in expected:
        assert name in normalized


def test_module_tags_cover_inventory(module_config: dict[str, object]) -> None:
    tags = set(module_config.get("tags", []))  # type: ignore[arg-type]
    assert "inventory" in tags
    assert "billing" in tags
