"""Standard module metadata checks for Api Keys."""

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
        assert module_docs.get(key), f"documentation.{key} missing"


def test_unit_tests_list(module_config: dict[str, object]) -> None:
    unit_tests = module_config.get("testing", {}).get("unit_tests", [])  # type: ignore[assignment]
    normalized = {Path(test_path).name for test_path in unit_tests}
    expected = [
        "test_api_keys_generator.py",
        "test_api_keys_overrides.py",
        "test_api_keys_runtime.py",
        "test_api_keys_adapters.py",
        "test_api_keys_validation.py",
        "test_api_keys_error_handling.py",
        "test_api_keys_health_check.py",
        "test_api_keys_framework_variants.py",
        "test_api_keys_vendor_layer.py",
        "test_api_keys_configuration.py",
        "test_api_keys_versioning.py",
        "test_api_keys_integration.py",
        "test_api_keys_standard_module.py",
    ]
    for name in expected:
        assert name in normalized
