"""Standard module metadata checks for Db Sqlite."""

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
        "test_db_sqlite_generator.py",
        "test_db_sqlite_overrides.py",
        "test_db_sqlite_runtime.py",
        "test_db_sqlite_adapters.py",
        "test_db_sqlite_validation.py",
        "test_db_sqlite_error_handling.py",
        "test_db_sqlite_health_check.py",
        "test_db_sqlite_framework_variants.py",
        "test_db_sqlite_vendor_layer.py",
        "test_db_sqlite_configuration.py",
        "test_db_sqlite_versioning.py",
        "test_db_sqlite_integration.py",
        "test_db_sqlite_standard_module.py",
    ]
    for name in expected:
        assert name in normalized
