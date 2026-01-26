"""Standard module metadata checks for Db Postgres."""

from __future__ import annotations


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


def test_unit_tests_listed(module_config: dict[str, object]) -> None:
    unit_tests = module_config.get("testing", {}).get("unit_tests", [])  # type: ignore[assignment]
    expected = {
        "tests/modules/free/database/db_postgres/test_db_postgres_cli_entry.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_configuration.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_framework_variants.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_generate.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_health_check.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_integration.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_overrides.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_standard_module.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_validation.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_vendor_layer.py",
        "tests/modules/free/database/db_postgres/test_db_postgres_versioning.py",
        "tests/modules/free/database/db_postgres/test_postgres_runtime.py",
    }
    assert expected.issubset(set(unit_tests))
