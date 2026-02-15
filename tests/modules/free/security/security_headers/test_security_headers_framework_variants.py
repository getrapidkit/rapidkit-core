"""Framework variant expectations for Security Headers."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.free.security.security_headers import generate as security_generate


def test_variants_declared(module_config: dict[str, object]) -> None:
    variants = module_config.get("generation", {}).get("variants", {})  # type: ignore[assignment]
    assert isinstance(variants, dict)
    assert "fastapi" in variants
    assert "nestjs" in variants


def test_fastapi_files_listed(module_config: dict[str, object]) -> None:
    fastapi_variants = module_config["generation"]["variants"]["fastapi"]  # type: ignore[index]
    files = fastapi_variants.get("files", [])
    assert any(
        entry.get("output") == "src/modules/free/security/security_headers/security_headers.py"
        for entry in files
    )


def test_nestjs_files_listed(module_config: dict[str, object]) -> None:
    nest_variants = module_config["generation"]["variants"]["nestjs"]  # type: ignore[index]
    files = nest_variants.get("files", [])
    assert any(
        entry.get("output")
        == "src/modules/free/security/security_headers/security-headers/security-headers.service.ts"
        for entry in files
    )


def test_nestjs_variant_generates_expected_routes(tmp_path: Path) -> None:
    config = security_generate.load_module_config()
    renderer = security_generate.TemplateRenderer()
    if getattr(renderer, "_env", None) is None:
        pytest.skip("jinja2 not available in this environment")

    base_context = security_generate.build_base_context(config)

    security_generate.generate_vendor_files(config, tmp_path, renderer, base_context)
    security_generate.generate_variant_files(
        config,
        "nestjs",
        tmp_path,
        renderer,
        base_context,
    )

    controller_file = (
        tmp_path / "src/modules/free/security/security_headers/security-headers.controller.ts"
    )
    module_file = tmp_path / "src/modules/free/security/security_headers/security-headers.module.ts"
    service_file = (
        tmp_path / "src/modules/free/security/security_headers/security-headers.service.ts"
    )
    health_controller_file = tmp_path / "src/health/security-headers-health.controller.ts"

    for artefact in (controller_file, module_file, service_file, health_controller_file):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to be generated"
        assert artefact.read_text().strip(), f"Generated file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert any(
        marker in controller_src
        for marker in (
            "@Controller('security-headers')",
            '@Controller("security-headers")',
            "@Controller('security_headers')",
            '@Controller("security_headers")',
        )
    ), "Security headers controller should mount security headers routes"
    assert "@Get('health')" not in controller_src
    assert '@Get("health")' not in controller_src
    assert "@Get('headers')" in controller_src or '@Get("headers")' in controller_src

    health_controller_src = health_controller_file.read_text()
    assert (
        "@Controller('api/health/module')" in health_controller_src
        or '@Controller("api/health/module")' in health_controller_src
    )
    assert (
        "@Get('security-headers')" in health_controller_src
        or '@Get("security-headers")' in health_controller_src
    )

    module_src = module_file.read_text()
    assert "@Module" in module_src
    assert "SecurityHeadersController" in module_src

    service_src = service_file.read_text()
    assert "class SecurityHeadersService" in service_src
