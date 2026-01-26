"""Framework variant expectations for Db Sqlite."""

from __future__ import annotations


def test_variants_declared(module_config: dict[str, object]) -> None:
    variants = module_config.get("generation", {}).get("variants", {})  # type: ignore[assignment]
    assert isinstance(variants, dict)
    assert "fastapi" in variants
    assert "nestjs" in variants


def test_fastapi_files_listed(module_config: dict[str, object]) -> None:
    fastapi_variants = module_config["generation"]["variants"]["fastapi"]  # type: ignore[index]
    files = fastapi_variants.get("files", [])
    outputs = {entry.get("output") for entry in files if isinstance(entry, dict)}
    expected_outputs = {
        "src/modules/free/database/db_sqlite/db_sqlite.py",
        "src/health/db_sqlite.py",
        "src/modules/free/database/db_sqlite/routers/db_sqlite.py",
        "config/database/db_sqlite.yaml",
        "tests/modules/integration/database/test_db_sqlite_integration.py",
    }
    assert expected_outputs.issubset(outputs)


def test_nestjs_files_listed(module_config: dict[str, object]) -> None:
    nest_variants = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nest_variants.get("files", [])
    outputs = {entry.get("output") for entry in files if isinstance(entry, dict)}
    expected_outputs = {
        "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.service.ts",
        "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.controller.ts",
        "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.module.ts",
        "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.configuration.ts",
        "src/health/db-sqlite-health.controller.ts",
        "src/health/db-sqlite-health.module.ts",
        "tests/modules/integration/database/db_sqlite.integration.spec.ts",
    }
    assert expected_outputs.issubset(outputs)
