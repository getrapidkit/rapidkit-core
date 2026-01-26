"""Standard module metadata checks for Security Headers."""

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
        "api_reference",
    ]
    for key in expected:
        value = module_docs.get(key)
        if key == "api_reference":
            value = value or module_docs.get("api_docs")
        assert value, f"documentation.{key} missing"


def test_unit_tests_list(module_config: dict[str, object]) -> None:
    testing_cfg = module_config.get("testing", {})
    assert isinstance(testing_cfg, dict)
    unit_tests = testing_cfg.get("unit_tests", [])
    assert isinstance(unit_tests, list)
    normalized = {Path(test_path).name for test_path in unit_tests}
    expected = [
        "test_security_headers_generator.py",
        "test_security_headers_overrides.py",
        "test_security_headers_runtime.py",
        "test_security_headers_adapters.py",
        "test_security_headers_validation.py",
        "test_security_headers_error_handling.py",
        "test_security_headers_health_check.py",
        "test_security_headers_framework_variants.py",
        "test_security_headers_vendor_layer.py",
        "test_security_headers_configuration.py",
        "test_security_headers_versioning.py",
        "test_security_headers_integration.py",
        "test_security_headers_standard_module.py",
    ]
    for name in expected:
        assert name in normalized
