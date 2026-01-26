"""Standard module metadata checks for Cart."""

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
        "test_cart_generator.py",
        "test_cart_overrides.py",
        "test_cart_runtime.py",
        "test_cart_adapters.py",
        "test_cart_validation.py",
        "test_cart_error_handling.py",
        "test_cart_health_check.py",
        "test_cart_framework_variants.py",
        "test_cart_vendor_layer.py",
        "test_cart_configuration.py",
        "test_cart_versioning.py",
        "test_cart_integration.py",
        "test_cart_standard_module.py",
    ]
    for name in expected:
        assert name in normalized


def test_module_marked_stable(module_config: dict[str, object]) -> None:
    assert module_config.get("status") == "stable"
