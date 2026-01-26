"""Framework variant expectations for Observability Core."""

from __future__ import annotations

from pathlib import Path

from modules.free.observability.core import generate as observability_generate


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
        "src/modules/free/observability/core/observability_core.py",
        "src/modules/free/observability/core/routers/observability_core.py",
        "config/observability/observability_core.yaml",
        "tests/modules/integration/observability/test_observability_core_integration.py",
    }

    vendor_files = module_config.get("generation", {}).get("vendor", {}).get("files", [])
    vendor_relatives = {entry.get("relative") for entry in vendor_files if isinstance(entry, dict)}

    # health may be provided by vendor-backed shims; accept either variant output or vendor 'relative'
    health_candidates = {
        "src/health/observability_core.py",
    }
    assert expected_outputs.issubset(outputs)
    assert not health_candidates.isdisjoint(outputs) or not health_candidates.isdisjoint(
        vendor_relatives
    )


def test_nestjs_files_listed(module_config: dict[str, object]) -> None:
    nest_variants = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nest_variants.get("files", [])
    outputs = {entry.get("output") for entry in files if isinstance(entry, dict)}
    expected_outputs = {
        "src/modules/free/observability/core/observability-core/observability-core.service.ts",
        "src/modules/free/observability/core/observability-core/observability-core.controller.ts",
        "src/modules/free/observability/core/observability-core/observability-core.module.ts",
        "src/modules/free/observability/core/observability-core/observability-core.configuration.ts",
        "src/health/observability-core-health.controller.ts",
        "src/health/observability-core-health.module.ts",
        "tests/modules/integration/observability/observability_core.integration.spec.ts",
    }
    assert expected_outputs.issubset(outputs)


def test_nestjs_variant_generates_expected_routes(tmp_path: Path) -> None:
    generator = observability_generate.ObservabilityModuleGenerator()
    config = generator.load_module_config()
    renderer = generator.create_renderer()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))

    generator.generate_vendor_files(config, tmp_path, renderer, base_context)
    generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)

    controller_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.controller.ts"
    )
    module_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.module.ts"
    )
    service_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.service.ts"
    )

    for artefact in (controller_file, module_file, service_file):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert any(
        marker in controller_src
        for marker in (
            "@Controller('observability-core')",
            '@Controller("observability-core")',
            "@Controller('observability_core')",
            '@Controller("observability_core")',
        )
    ), "Observability controller should mount observability core routes"
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
    assert "@Get('metrics')" in controller_src or '@Get("metrics")' in controller_src
    assert "@Get('events')" in controller_src or '@Get("events")' in controller_src
    assert "@Post('events')" in controller_src or '@Post("events")' in controller_src
    assert "@Get('traces')" in controller_src or '@Get("traces")' in controller_src

    module_src = module_file.read_text()
    assert "@Module" in module_src
    assert "ObservabilityCoreController" in module_src

    service_src = service_file.read_text()
    assert "class ObservabilityCoreService" in service_src
