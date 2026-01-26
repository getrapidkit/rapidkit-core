"""Smoke tests for the OAuth module generator."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_generator_is_importable() -> None:
    module = importlib.import_module("modules.free.auth.oauth.generate")
    assert hasattr(module, "main")


def test_module_yaml_declares_variants_and_vendor() -> None:
    module = importlib.import_module("modules.free.auth.oauth.generate")
    config = module.load_module_config()

    variants = config.get("generation", {}).get("variants", {})
    assert set(variants) >= {"fastapi", "nestjs"}

    vendor = config.get("generation", {}).get("vendor", {})
    files = vendor.get("files", []) if isinstance(vendor, dict) else []
    assert any(entry.get("template") for entry in files)


def test_generate_vendor_and_variant_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("modules.free.auth.oauth.generate")
    config = module.load_module_config()
    renderer = module.TemplateRenderer()
    if getattr(renderer, "_env", None) is None:
        raise pytest.skip("jinja2 is required to render OAuth templates")

    base_context = module.build_base_context(config)

    module.generate_vendor_files(config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )
    vendor_runtime = vendor_root / "src" / "modules" / "free" / "auth" / "oauth" / "oauth.py"
    vendor_types = vendor_root / "src" / "modules" / "free" / "auth" / "oauth" / "oauth_types.py"
    # health artefacts should be generated under the canonical module layout; keep
    # legacy aliases as fallbacks for backward compatibility.
    vendor_health_candidates = [
        vendor_root / "src" / "modules" / "free" / "auth" / "oauth" / "health" / "oauth.py",
        vendor_root / "src" / "core" / "oauth_health.py",
        vendor_root / "src" / "health" / "oauth.py",
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
        "class OAuthRuntime",
        "def build_authorize_url",
        "def validate_callback",
        "def metadata",
        "def list_oauth_features",
        "__all__",
    ):
        assert token in runtime_src, f"Vendor runtime missing {token}"

    types_src = vendor_types.read_text(encoding="utf-8")
    for token in (
        "class OAuthHealthSnapshot",
        "class OAuthProviderSnapshot",
        "def as_dict",
    ):
        assert token in types_src, f"Vendor types missing {token}"

    health_src = vendor_health.read_text(encoding="utf-8")
    for token in ("oauth_health_check", "register_oauth_health", "router ="):
        assert token in health_src, f"Vendor health helper missing {token}"

    config_src = vendor_config.read_text(encoding="utf-8")
    for token in ("function loadConfiguration", "module.exports"):
        assert token in config_src, f"Vendor configuration missing {token}"

    module.generate_variant_files(config, "fastapi", tmp_path, renderer, base_context)
    fastapi_runtime = tmp_path / "src" / "modules" / "free" / "auth" / "oauth" / "oauth.py"
    fastapi_types = tmp_path / "src" / "modules" / "free" / "auth" / "oauth" / "oauth_types.py"
    fastapi_health_candidates = [
        tmp_path / "src" / "modules" / "free" / "auth" / "oauth" / "health" / "oauth.py",
        tmp_path / "src" / "core" / "health" / "oauth.py",
        tmp_path / "src" / "health" / "oauth.py",
    ]
    fastapi_health = next(
        (p for p in fastapi_health_candidates if p.exists()), fastapi_health_candidates[0]
    )

    fastapi_shared_health_candidates = [
        tmp_path / "src" / "modules" / "free" / "auth" / "oauth" / "health" / "oauth.py",
        tmp_path / "src" / "core" / "oauth_health.py",
        tmp_path / "src" / "health" / "oauth.py",
    ]
    fastapi_shared_health = next(
        (p for p in fastapi_shared_health_candidates if p.exists()),
        fastapi_shared_health_candidates[0],
    )
    fastapi_routes = (
        tmp_path / "src" / "modules" / "free" / "auth" / "oauth" / "routers" / "oauth.py"
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
        "class OAuthRuntime",
        "def get_runtime",
        "def create_router",
        '@router.get("/metadata"',
        '@router.get("/features"',
        '@router.get("/providers"',
        '@router.get("/{provider}/authorize"',
        '@router.get("/{provider}/callback"',
        "RedirectResponse",
        "Depends(get_runtime)",
        "__all__",
    ):
        assert token in fastapi_runtime_src, f"FastAPI runtime missing {token}"

    fastapi_health_src = fastapi_health.read_text(encoding="utf-8")
    for token in (
        "oauth_health_router",
        "register_oauth_health",
        "oauth_health_check",
        "__all__",
    ):
        assert token in fastapi_health_src, f"FastAPI health shim missing {token}"

    fastapi_shared_health_src = fastapi_shared_health.read_text(encoding="utf-8")
    # The shared health runtime should expose registration and health check
    for token in ("register_oauth_health", "oauth_health_check"):
        assert token in fastapi_shared_health_src, f"Shared OAuth health runtime missing {token}"

    # Types like OAuthHealthSnapshot/as_dict should be present in the types file
    fastapi_types_src = fastapi_types.read_text(encoding="utf-8")
    for token in ("OAuthHealthSnapshot", "as_dict"):
        assert token in fastapi_types_src, f"FastAPI OAuth types missing {token}"

    fastapi_types_src = fastapi_types.read_text(encoding="utf-8")
    for token in (
        "class OAuthHealthSnapshot",
        "class OAuthProviderSnapshot",
        "def as_dict",
    ):
        assert token in fastapi_types_src, f"FastAPI OAuth types missing {token}"

    fastapi_routes_src = fastapi_routes.read_text(encoding="utf-8")
    for token in ("create_router", "get_runtime", "__all__"):
        assert token in fastapi_routes_src, f"FastAPI router re-export missing {token}"

    module.generate_variant_files(config, "nestjs", tmp_path, renderer, base_context)
    nest_root = tmp_path / "src" / "modules" / "free" / "auth" / "oauth"
    nest_service = nest_root / "oauth.service.ts"
    nest_controller = nest_root / "oauth.controller.ts"
    nest_module = nest_root / "oauth.module.ts"
    nest_index = nest_root / "index.ts"
    nest_configuration = nest_root / "configuration.ts"
    nest_validation = nest_root / "config" / "oauth.validation.ts"

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
        "export class OauthService",
        "listProviders():",
        "getProviderStrict(",
        "describe(): OauthMetadataSnapshot",
        "listFeatures(): string[]",
    ):
        assert token in nest_service_src, f"NestJS service missing {token}"

    nest_controller_src = nest_controller.read_text(encoding="utf-8")
    assert (
        "@Controller('oauth')" in nest_controller_src
        or '@Controller("oauth")' in nest_controller_src
    ), "OAuth controller should mount oauth routes"
    for decorator in (
        "@Get('metadata')",
        "@Get('features')",
        "@Get('providers')",
        "@Get('providers/:provider')",
    ):
        mirror = decorator.replace("'", '"')
        assert (
            decorator in nest_controller_src or mirror in nest_controller_src
        ), f"OAuth controller missing {decorator}"

    nest_module_src = nest_module.read_text(encoding="utf-8")
    for token in (
        "export class OauthModule",
        "@Module",
        "ConfigModule.forFeature",
        "OauthService",
        "OauthController",
    ):
        assert token in nest_module_src, f"NestJS module missing {token}"

    nest_index_src = nest_index.read_text(encoding="utf-8")
    for token in (
        'export * from "./oauth.module"',
        'export * from "./oauth.service"',
        'export * from "./oauth.controller"',
    ):
        assert token in nest_index_src, f"NestJS index missing {token}"

    nest_configuration_src = nest_configuration.read_text(encoding="utf-8")
    for token in ("registerAs", "export default", "parseProviders"):
        assert token in nest_configuration_src, f"NestJS configuration missing {token}"

    nest_validation_src = nest_validation.read_text(encoding="utf-8")
    for token in (
        "oauthValidationSchema",
        "OAUTH_REDIRECT_BASE_URL",
        "OAUTH_STATE_TTL_SECONDS",
        "OAUTH_STATE_CLEANUP_INTERVAL",
    ):
        assert token in nest_validation_src, f"NestJS validation missing {token}"
