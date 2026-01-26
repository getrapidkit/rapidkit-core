"""Framework variant expectations for Db Mongo."""

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
    assert "src/modules/free/database/db_mongo/db_mongo.py" in outputs
    # health artefact should be present as the canonical vendor-backed placement
    # under the modules path (variant outputs or vendor 'relative' entries).
    health_candidates = {"src/health/db_mongo.py"}
    vendor_files = module_config.get("generation", {}).get("vendor", {}).get("files", [])
    vendor_relatives = {entry.get("relative") for entry in vendor_files if isinstance(entry, dict)}

    # Accept health mappings either in the variant outputs or in vendor payload 'relative' entries
    assert not health_candidates.isdisjoint(outputs) or not health_candidates.isdisjoint(
        vendor_relatives
    ), f"Expected {health_candidates} in variant outputs or vendor files"
    assert "src/modules/free/database/db_mongo/routers/db_mongo.py" in outputs
    assert "config/database/db_mongo.yaml" in outputs
    assert "tests/modules/integration/database/test_db_mongo_integration.py" in outputs


def test_nestjs_files_listed(module_config: dict[str, object]) -> None:
    nest_variants = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nest_variants.get("files", [])
    outputs = {entry.get("output") for entry in files if isinstance(entry, dict)}
    base_ts = "src/modules/free/database/db_mongo"
    assert f"{base_ts}/db-mongo.service.ts" in outputs
    assert f"{base_ts}/db-mongo.controller.ts" in outputs
    assert f"{base_ts}/db-mongo.module.ts" in outputs
    assert f"{base_ts}/db-mongo.configuration.ts" in outputs
    assert "src/health/db-mongo-health.controller.ts" in outputs
    assert "src/health/db-mongo-health.module.ts" in outputs
    assert "tests/modules/integration/database/db_mongo.integration.spec.ts" in outputs
