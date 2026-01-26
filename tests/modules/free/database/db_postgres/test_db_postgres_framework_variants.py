"""Framework variant expectations for Db Postgres."""

from __future__ import annotations


def test_variants_declared(module_config: dict[str, object]) -> None:
    variants = module_config.get("generation", {}).get("variants", {})  # type: ignore[assignment]
    assert isinstance(variants, dict)
    assert "fastapi" in variants
    assert "nestjs" in variants


def test_fastapi_variant_outputs(module_config: dict[str, object]) -> None:
    fastapi = module_config["generation"]["variants"]["fastapi"]  # type: ignore[index]
    files = fastapi.get("files", [])
    outputs = {entry.get("output") for entry in files if isinstance(entry, dict)}
    assert "src/modules/free/database/db_postgres/postgres.py" in outputs
    health_candidates = {"src/health/postgres.py"}
    vendor_files = module_config.get("generation", {}).get("vendor", {}).get("files", [])
    vendor_relatives = {entry.get("relative") for entry in vendor_files if isinstance(entry, dict)}
    assert not health_candidates.isdisjoint(outputs) or not health_candidates.isdisjoint(
        vendor_relatives
    ), f"Expected {health_candidates} in variant outputs or vendor files"
    assert "config/database/postgres.yaml" in outputs
    assert "tests/modules/integration/database/test_postgres_integration.py" in outputs


def test_nestjs_variant_outputs(module_config: dict[str, object]) -> None:
    nestjs = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nestjs.get("files", [])
    outputs = {entry.get("output") for entry in files if isinstance(entry, dict)}
    assert "src/modules/free/database/db_postgres/postgres.service.ts" in outputs
    assert "src/modules/free/database/db_postgres/postgres.module.ts" in outputs
    assert "src/health/postgres-health.controller.ts" in outputs
    assert "src/health/postgres-health.module.ts" in outputs
    assert "nestjs/configuration.js" in outputs
    assert "tests/modules/integration/database/postgres.integration.spec.ts" in outputs
