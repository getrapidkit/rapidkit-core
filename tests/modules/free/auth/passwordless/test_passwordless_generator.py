"""Smoke tests for the passwordless module generator."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_generator_is_importable() -> None:
    module = importlib.import_module("modules.free.auth.passwordless.generate")
    assert hasattr(module, "main")


def test_module_yaml_declares_variants() -> None:
    module = importlib.import_module("modules.free.auth.passwordless.generate")
    config = module.load_module_config()
    variants = config.get("generation", {}).get("variants", {})
    assert set(variants) >= {"fastapi", "nestjs"}


def test_generate_vendor_and_variant_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("modules.free.auth.passwordless.generate")
    config = module.load_module_config()
    renderer = module.TemplateRenderer()
    if getattr(renderer, "_env", None) is None:
        pytest.skip("jinja2 is required to render Passwordless templates")

    base_context = module.build_base_context(config)

    module.generate_vendor_files(config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )
    vendor_runtime = (
        vendor_root / "src" / "modules" / "free" / "auth" / "passwordless" / "passwordless.py"
    )
    vendor_types = (
        vendor_root / "src" / "modules" / "free" / "auth" / "passwordless" / "passwordless_types.py"
    )
    vendor_health_candidates = [
        vendor_root
        / "src"
        / "modules"
        / "free"
        / "auth"
        / "passwordless"
        / "health"
        / "passwordless.py",
        vendor_root / "src" / "core" / "passwordless_health.py",
        vendor_root / "src" / "health" / "passwordless.py",
    ]
    vendor_health = next(
        (p for p in vendor_health_candidates if p.exists()), vendor_health_candidates[0]
    )
    vendor_config = vendor_root / "nestjs" / "configuration.js"

    for artefact in (vendor_runtime, vendor_types, vendor_health, vendor_config):
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        contents = artefact.read_text(encoding="utf-8").strip()
        assert contents, f"Generated vendor file {artefact} is empty"

    runtime_src = vendor_runtime.read_text(encoding="utf-8")
    for token in (
        "class PasswordlessRuntime",
        "def issue_code",
        "def issue_magic_link",
        "def verify_code",
        "def list_passwordless_features",
        "__all__",
    ):
        assert token in runtime_src, f"Vendor runtime missing {token}"

    types_src = vendor_types.read_text(encoding="utf-8")
    for token in ("class PasswordlessHealthSnapshot", "def as_dict"):
        assert token in types_src, f"Vendor types missing {token}"

    health_src = vendor_health.read_text(encoding="utf-8")
    for token in (
        "passwordless_health_check",
        "register_passwordless_health",
        "router =",
    ):
        assert token in health_src, f"Vendor health helper missing {token}"

    config_src = vendor_config.read_text(encoding="utf-8")
    for token in ("function loadConfiguration", "module.exports"):
        assert token in config_src, f"Vendor configuration missing {token}"

    module.generate_variant_files(config, "fastapi", tmp_path, renderer, base_context)
    fastapi_runtime = (
        tmp_path / "src" / "modules" / "free" / "auth" / "passwordless" / "passwordless.py"
    )
    fastapi_types = (
        tmp_path / "src" / "modules" / "free" / "auth" / "passwordless" / "passwordless_types.py"
    )
    fastapi_health_candidates = [
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "auth"
        / "passwordless"
        / "health"
        / "passwordless.py",
        tmp_path / "src" / "core" / "health" / "passwordless.py",
        tmp_path / "src" / "health" / "passwordless.py",
    ]
    fastapi_health = next(
        (p for p in fastapi_health_candidates if p.exists()), fastapi_health_candidates[0]
    )

    fastapi_shared_health_candidates = [
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "auth"
        / "passwordless"
        / "health"
        / "passwordless.py",
        tmp_path / "src" / "core" / "passwordless_health.py",
        tmp_path / "src" / "health" / "passwordless.py",
    ]
    fastapi_shared_health = next(
        (p for p in fastapi_shared_health_candidates if p.exists()),
        fastapi_shared_health_candidates[0],
    )
    fastapi_routes = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "auth"
        / "passwordless"
        / "routers"
        / "passwordless.py"
    )

    for artefact in (
        fastapi_runtime,
        fastapi_types,
        fastapi_health,
        fastapi_shared_health,
        fastapi_routes,
    ):
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        contents = artefact.read_text(encoding="utf-8").strip()
        assert contents, f"Generated FastAPI file {artefact} is empty"

    fastapi_runtime_src = fastapi_runtime.read_text(encoding="utf-8")
    for token in (
        "class PasswordlessRuntime",
        "def get_runtime",
        "def create_router",
        '@router.get("/metadata"',
        '@router.get("/features"',
        '@router.post("/tokens"',
        '@router.post("/magic-link"',
        '@router.post("/verify"',
        "__all__",
    ):
        assert token in fastapi_runtime_src, f"FastAPI runtime missing {token}"
    assert "Depends(get_runtime)" in fastapi_runtime_src

    fastapi_health_src = fastapi_health.read_text(encoding="utf-8")
    for token in (
        "register_passwordless_health",
        "passwordless_health_check",
        "router =",
    ):
        assert token in fastapi_health_src, f"FastAPI health shim missing {token}"

    fastapi_shared_health_src = fastapi_shared_health.read_text(encoding="utf-8")
    for token in ("register_passwordless_health", "passwordless_health_check"):
        assert (
            token in fastapi_shared_health_src
        ), f"Shared passwordless health runtime missing {token}"

    fastapi_types_src = fastapi_types.read_text(encoding="utf-8")
    for token in (
        "class PasswordlessHealthSnapshot",
        "def as_dict",
    ):
        assert token in fastapi_types_src, f"FastAPI passwordless types missing {token}"

    fastapi_routes_src = fastapi_routes.read_text(encoding="utf-8")
    for token in ("create_router", "get_runtime", "__all__"):
        assert token in fastapi_routes_src, f"FastAPI router re-export missing {token}"

    module.generate_variant_files(config, "nestjs", tmp_path, renderer, base_context)
    nest_root = tmp_path / "src" / "modules" / "free" / "auth" / "passwordless"
    nest_service = nest_root / "passwordless.service.ts"
    nest_controller = nest_root / "passwordless.controller.ts"
    nest_module = nest_root / "passwordless.module.ts"
    nest_index = nest_root / "index.ts"
    nest_configuration = nest_root / "configuration.ts"
    nest_validation = nest_root / "config" / "passwordless.validation.ts"

    for artefact in (
        nest_service,
        nest_controller,
        nest_module,
        nest_index,
        nest_configuration,
        nest_validation,
    ):
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        contents = artefact.read_text(encoding="utf-8").strip()
        assert contents, f"Generated NestJS file {artefact} is empty"

    nest_service_src = nest_service.read_text(encoding="utf-8")
    for token in (
        "export class PasswordlessService",
        "issueCode(",
        "issueMagicLink(",
        "verifyCode(",
        "describe(): PasswordlessMetadata",
        "listFeatures(): string[]",
        "listDeliveryMethods(): string[]",
    ):
        assert token in nest_service_src, f"NestJS service missing {token}"

    nest_controller_src = nest_controller.read_text(encoding="utf-8")
    assert (
        "@Controller('passwordless')" in nest_controller_src
        or '@Controller("passwordless")' in nest_controller_src
    ), "Passwordless controller should mount passwordless route"
    for decorator in (
        "@Get('metadata')",
        "@Get('features')",
        "@Get('delivery-methods')",
        "@Post('tokens')",
        "@Post('magic-link')",
        "@Post('verify')",
    ):
        mirror = decorator.replace("'", '"')
        assert (
            decorator in nest_controller_src or mirror in nest_controller_src
        ), f"Passwordless controller missing {decorator}"

    nest_module_src = nest_module.read_text(encoding="utf-8")
    for token in (
        "export class PasswordlessModule",
        "@Module",
        "ConfigModule.forFeature",
        "PasswordlessService",
        "PasswordlessController",
    ):
        assert token in nest_module_src, f"NestJS module missing {token}"

    nest_index_src = nest_index.read_text(encoding="utf-8")
    for token in (
        'export * from "./passwordless.module"',
        'export * from "./passwordless.service"',
        'export * from "./passwordless.controller"',
    ):
        assert token in nest_index_src, f"NestJS index missing {token}"

    nest_configuration_src = nest_configuration.read_text(encoding="utf-8")
    for token in ("registerAs", "export default", "parseInteger"):
        assert token in nest_configuration_src, f"NestJS configuration missing {token}"

    nest_validation_src = nest_validation.read_text(encoding="utf-8")
    for token in (
        "passwordlessValidationSchema",
        "PASSWORDLESS_TOKEN_TTL_SECONDS",
        "PASSWORDLESS_TOKEN_LENGTH",
        "PASSWORDLESS_RESEND_COOLDOWN_SECONDS",
    ):
        assert token in nest_validation_src, f"NestJS validation missing {token}"
