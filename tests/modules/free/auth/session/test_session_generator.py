"""Smoke tests for the session module generator."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_generator_is_importable() -> None:
    module = importlib.import_module("modules.free.auth.session.generate")
    assert hasattr(module, "main")


def test_module_yaml_declares_variants() -> None:
    module = importlib.import_module("modules.free.auth.session.generate")
    config = module.load_module_config()
    variants = config.get("generation", {}).get("variants", {})
    assert set(variants) >= {"fastapi", "nestjs"}


def test_generate_vendor_and_variant_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("modules.free.auth.session.generate")
    config = module.load_module_config()
    renderer = module.TemplateRenderer()
    if getattr(renderer, "_env", None) is None:
        pytest.skip("jinja2 is required to render Session templates")

    base_context = module.build_base_context(config)

    module.generate_vendor_files(config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )
    vendor_runtime = vendor_root / "src" / "modules" / "free" / "auth" / "session" / "session.py"
    vendor_types = (
        vendor_root / "src" / "modules" / "free" / "auth" / "session" / "session_types.py"
    )
    vendor_health_candidates = [
        vendor_root / "src" / "modules" / "free" / "auth" / "session" / "health" / "session.py",
        vendor_root / "src" / "core" / "session_health.py",
        vendor_root / "src" / "health" / "session.py",
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
        "class SessionRuntime",
        "def load_session_settings",
        "def describe_session",
        "def list_session_features",
        "def get_session_metadata",
        "__all__",
    ):
        assert token in runtime_src, f"Vendor runtime missing {token}"

    types_src = vendor_types.read_text(encoding="utf-8")
    for token in ("class SessionHealthSnapshot", "def as_dict"):
        assert token in types_src, f"Vendor types missing {token}"

    health_src = vendor_health.read_text(encoding="utf-8")
    for token in ("session_health_check", "register_session_health", "router ="):
        assert token in health_src, f"Vendor health helper missing {token}"

    config_src = vendor_config.read_text(encoding="utf-8")
    for token in ("function loadConfiguration", "module.exports"):
        assert token in config_src, f"Vendor configuration missing {token}"

    module.generate_variant_files(config, "fastapi", tmp_path, renderer, base_context)
    fastapi_runtime = tmp_path / "src" / "modules" / "free" / "auth" / "session" / "session.py"
    fastapi_types = tmp_path / "src" / "modules" / "free" / "auth" / "session" / "session_types.py"
    fastapi_health_candidates = [
        tmp_path / "src" / "modules" / "free" / "auth" / "session" / "health" / "session.py",
        tmp_path / "src" / "core" / "health" / "session.py",
        tmp_path / "src" / "health" / "session.py",
    ]
    fastapi_health = next(
        (p for p in fastapi_health_candidates if p.exists()), fastapi_health_candidates[0]
    )

    fastapi_shared_health_candidates = [
        tmp_path / "src" / "modules" / "free" / "auth" / "session" / "health" / "session.py",
        tmp_path / "src" / "core" / "session_health.py",
        tmp_path / "src" / "health" / "session.py",
    ]
    fastapi_shared_health = next(
        (p for p in fastapi_shared_health_candidates if p.exists()),
        fastapi_shared_health_candidates[0],
    )
    fastapi_routes = (
        tmp_path / "src" / "modules" / "free" / "auth" / "session" / "routers" / "session.py"
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
        "class SessionRuntime",
        "def get_runtime",
        "def create_router",
        "def _apply_cookie",
        "__all__",
    ):
        assert token in fastapi_runtime_src, f"FastAPI runtime missing {token}"

    fastapi_health_src = fastapi_health.read_text(encoding="utf-8")
    for token in (
        "router = session_health_router",
        "session_health_check",
        "register_session_health",
        "SessionHealthSnapshot",
    ):
        assert token in fastapi_health_src, f"FastAPI health shim missing {token}"

    fastapi_shared_health_src = fastapi_shared_health.read_text(encoding="utf-8")
    for token in ("register_session_health", "session_health_check"):
        assert token in fastapi_shared_health_src, f"Shared session health runtime missing {token}"

    fastapi_types_src = fastapi_types.read_text(encoding="utf-8")
    for token in ("SessionHealthSnapshot", "def as_dict"):
        assert token in fastapi_types_src, f"Session types file missing {token}"

    fastapi_types_src = fastapi_types.read_text(encoding="utf-8")
    for token in ("class SessionHealthSnapshot", "def as_dict"):
        assert token in fastapi_types_src, f"Session types file missing {token}"

    fastapi_routes_src = fastapi_routes.read_text(encoding="utf-8")
    assert "from src.modules.free.auth.session.session import create_router" in fastapi_routes_src
    assert "router = create_router()" in fastapi_routes_src
    assert '__all__ = ["create_router", "router"]' in fastapi_routes_src
    assert "Depends(get_runtime)" in fastapi_runtime_src

    module.generate_variant_files(config, "nestjs", tmp_path, renderer, base_context)
    nest_root = tmp_path / "src" / "modules" / "free" / "auth" / "session"
    nest_service = nest_root / "session.service.ts"
    nest_controller = nest_root / "session.controller.ts"
    nest_module = nest_root / "session.module.ts"
    nest_index = nest_root / "index.ts"
    nest_configuration = nest_root / "configuration.ts"
    nest_validation = nest_root / "config" / "session.validation.ts"

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
        "export class SessionService",
        "issueSession(userId",
        "verifySessionToken",
        "rotateSession",
        "revokeSession",
        "describe(): SessionMetadataSnapshot",
        "listFeatures(): string[]",
    ):
        assert token in nest_service_src, f"NestJS service missing {token}"

    nest_controller_src = nest_controller.read_text(encoding="utf-8")
    assert (
        "@Controller('sessions')" in nest_controller_src
        or '@Controller("sessions")' in nest_controller_src
    ), "Session controller should mount sessions route"
    for decorator in (
        "@Get('metadata')",
        "@Get('features')",
        "@Post()",
        "@Post('refresh')",
        "@Post('verify')",
        "@Delete(':sessionId')",
    ):
        counterpart = decorator.replace("'", '"')
        assert (
            decorator in nest_controller_src or counterpart in nest_controller_src
        ), f"Session controller missing {decorator}"

    nest_module_src = nest_module.read_text(encoding="utf-8")
    for token in (
        "export class SessionModule",
        "@Module",
        "ConfigModule.forFeature",
        "SessionService",
        "SessionController",
    ):
        assert token in nest_module_src, f"NestJS module missing {token}"

    nest_index_src = nest_index.read_text(encoding="utf-8")
    for token in ('export * from "./session.module"', 'export * from "./session.service"'):
        assert token in nest_index_src, f"NestJS index missing {token}"

    nest_configuration_src = nest_configuration.read_text(encoding="utf-8")
    assert "registerAs" in nest_configuration_src, "NestJS configuration should use registerAs"
    assert "export default" in nest_configuration_src, "NestJS configuration should export default"

    nest_validation_src = nest_validation.read_text(encoding="utf-8")
    for token in ("sessionValidationSchema", "Joi.object", "SESSION_TTL_SECONDS"):
        assert token in nest_validation_src, f"NestJS validation missing {token}"
