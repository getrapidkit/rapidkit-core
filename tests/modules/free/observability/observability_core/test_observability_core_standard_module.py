"""Standard module metadata checks for Observability Core."""

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
        "test_observability_core_generator.py",
        "test_observability_core_overrides.py",
        "test_observability_core_runtime.py",
        "test_observability_core_adapters.py",
        "test_observability_core_validation.py",
        "test_observability_core_error_handling.py",
        "test_observability_core_health_check.py",
        "test_observability_core_framework_variants.py",
        "test_observability_core_vendor_layer.py",
        "test_observability_core_configuration.py",
        "test_observability_core_versioning.py",
        "test_observability_core_integration.py",
        "test_observability_core_standard_module.py",
    ]
    for name in expected:
        assert name in normalized
