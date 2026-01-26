"""Generator-level guardrails for Security Headers."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, Mapping

import pytest

from modules.free.security.security_headers import generate as security_headers_generate


def test_core_files_exist(module_root: Path) -> None:
    expected = [
        "module.yaml",
        "generate.py",
        "overrides.py",
        "config/base.yaml",
        "config/snippets.yaml",
        "module.verify.json",
        ".module_state.json",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_framework_files_exist(module_root: Path) -> None:
    expected = [
        "frameworks/fastapi.py",
        "frameworks/nestjs.py",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_templates_exist(module_root: Path) -> None:
    expected = [
        "templates/base/security_headers.py.j2",
        "templates/base/security_headers_health.py.j2",
        "templates/base/security_headers_types.py.j2",
        "templates/variants/fastapi/security_headers.py.j2",
        "templates/variants/fastapi/security_headers_routes.py.j2",
        "templates/variants/fastapi/security_headers_health.py.j2",
        "templates/variants/fastapi/security_headers_config.yaml.j2",
        "templates/variants/nestjs/security_headers.service.ts.j2",
        "templates/variants/nestjs/security_headers.controller.ts.j2",
        "templates/variants/nestjs/security_headers.module.ts.j2",
        "templates/variants/nestjs/security_headers.configuration.ts.j2",
        "templates/variants/nestjs/security_headers.health.controller.ts.j2",
        "templates/variants/nestjs/security_headers.health.module.ts.j2",
        "templates/tests/integration/security_headers.integration.spec.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_generator_module_exposes_main() -> None:
    module = importlib.import_module("modules.free.security.security_headers.generate")
    assert hasattr(module, "main"), "Security Headers generator should expose a main entrypoint"


@pytest.fixture(scope="module")
def module_config() -> Dict[str, Any]:
    return security_headers_generate.load_module_config()


@pytest.fixture
def renderer() -> security_headers_generate.TemplateRenderer:
    instance = security_headers_generate.TemplateRenderer()
    if getattr(instance, "_env", None) is None:
        pytest.skip("jinja2 is required to render Security Headers templates")
    return instance


def _render_variant(
    module_config: Mapping[str, Any],
    renderer: security_headers_generate.TemplateRenderer,
    tmp_path: Path,
    variant: str,
) -> tuple[Path, Dict[str, Any]]:
    base_context = security_headers_generate.build_base_context(module_config)
    target_dir = tmp_path / f"security_headers_{variant}"
    target_dir.mkdir(parents=True, exist_ok=True)

    security_headers_generate.generate_vendor_files(
        module_config, target_dir, renderer, base_context
    )
    security_headers_generate.generate_variant_files(
        module_config,
        variant,
        target_dir,
        renderer,
        base_context,
    )

    return target_dir, dict(base_context)


def test_vendor_payload_exposes_runtime_contracts(
    module_config: Mapping[str, Any],
    renderer: security_headers_generate.TemplateRenderer,
    tmp_path: Path,
) -> None:
    output_dir, context = _render_variant(module_config, renderer, tmp_path, "fastapi")

    vendor_cfg = module_config["generation"]["vendor"]
    vendor_root = Path(vendor_cfg.get("root", ".rapidkit/vendor"))
    module_name = context["rapidkit_vendor_module"]
    version = str(context["rapidkit_vendor_version"])

    vendor_dir = output_dir / vendor_root / module_name / version

    runtime_path = vendor_dir / "src/modules/free/security/security_headers/security_headers.py"
    health_path = vendor_dir / "src/health/security_headers.py"
    types_path = vendor_dir / "src/modules/free/security/security_headers/types/security_headers.py"
    nest_config_path = vendor_dir / "nestjs" / "configuration.js"

    assert runtime_path.exists(), "Vendor runtime should be generated"
    runtime_src = runtime_path.read_text(encoding="utf-8")
    for token in (
        "class SecurityHeaders",
        "def metadata",
        "def health_check",
        "__all__",
    ):
        assert token in runtime_src, f"Vendor runtime missing {token}"

    assert health_path.exists(), "Vendor health helper should be generated"
    health_src = health_path.read_text(encoding="utf-8")
    for token in ("def build_health_payload", "def evaluate_completeness"):
        assert token in health_src, f"Vendor health helper missing {token}"

    assert types_path.exists(), "Vendor types file should be generated"
    types_src = types_path.read_text(encoding="utf-8")
    for token in ("class SecurityHeadersConfig", "class SecurityHeadersMetrics"):
        assert token in types_src, f"Vendor types missing {token}"

    assert nest_config_path.exists(), "Vendor NestJS configuration helper should be generated"
    nest_src = nest_config_path.read_text(encoding="utf-8")
    for token in ("DEFAULT_SECURITY_HEADERS", "loadConfiguration", "module.exports"):
        assert token in nest_src, f"Vendor configuration missing {token}"


def test_fastapi_variant_wires_runtime_and_routes(
    module_config: Mapping[str, Any],
    renderer: security_headers_generate.TemplateRenderer,
    tmp_path: Path,
) -> None:
    output_dir, _context = _render_variant(module_config, renderer, tmp_path, "fastapi")

    runtime_path = output_dir / "src/modules/free/security/security_headers/security_headers.py"
    routes_path = (
        output_dir / "src/modules/free/security/security_headers/routers/security_headers.py"
    )
    health_path = output_dir / "src/health/security_headers.py"
    config_path = output_dir / "config" / "security" / "security_headers.yaml"
    integration_test_path = (
        output_dir
        / "tests"
        / "modules"
        / "integration"
        / "security"
        / "test_security_headers_integration.py"
    )

    assert runtime_path.exists(), "FastAPI runtime adapter should be generated"
    runtime_src = runtime_path.read_text(encoding="utf-8")
    for token in (
        "SecurityHeadersSettings",
        "SecurityHeadersMiddleware",
        "def configure_security_headers",
        "def get_runtime",
        "def register_fastapi",
    ):
        assert token in runtime_src, f"FastAPI runtime missing {token}"

    assert routes_path.exists(), "FastAPI router should be generated"
    routes_src = routes_path.read_text(encoding="utf-8")
    for token in (
        "def build_router",
        "def read_health",
        "def list_headers",
        "def apply_headers",
        "Depends(get_runtime)",
    ):
        assert token in routes_src, f"FastAPI routes missing {token}"

    assert health_path.exists(), "FastAPI health registration should be generated"
    health_src = health_path.read_text(encoding="utf-8")
    for token in (
        "def build_health_router",
        "register_security_headers_health",
    ):
        assert token in health_src, f"FastAPI health helper missing {token}"

    assert config_path.exists(), "FastAPI configuration defaults should be generated"
    config_src = config_path.read_text(encoding="utf-8")
    for token in ("security_headers:", "strict_transport_security:", "permissions_policy:"):
        assert token in config_src, f"FastAPI configuration missing {token}"

    assert integration_test_path.exists(), "FastAPI integration test scaffold should be generated"
    integration_src = integration_test_path.read_text(encoding="utf-8")
    for token in ("def test_generator_entrypoint", "Path(__file__)"):
        assert token in integration_src, f"FastAPI integration test missing {token}"


def test_nestjs_variant_surfaces_service_and_module(
    module_config: Mapping[str, Any],
    renderer: security_headers_generate.TemplateRenderer,
    tmp_path: Path,
) -> None:
    output_dir, _context = _render_variant(module_config, renderer, tmp_path, "nestjs")

    service_path = (
        output_dir / "src/modules/free/security/security_headers/security-headers.service.ts"
    )
    controller_path = (
        output_dir / "src/modules/free/security/security_headers/security-headers.controller.ts"
    )
    module_path = (
        output_dir / "src/modules/free/security/security_headers/security-headers.module.ts"
    )
    configuration_path = (
        output_dir / "src/modules/free/security/security_headers/security-headers.configuration.ts"
    )
    health_controller_path = output_dir / "src/health/security-headers-health.controller.ts"
    health_module_path = output_dir / "src/health/security-headers-health.module.ts"
    integration_test_path = (
        output_dir
        / "tests"
        / "modules"
        / "integration"
        / "security"
        / "security_headers.integration.spec.ts"
    )

    assert service_path.exists(), "NestJS service should be generated"
    service_src = service_path.read_text(encoding="utf-8")
    for token in (
        "export class SecurityHeadersService",
        "const DEFAULT_OPTIONS",
        "apply(response: Response)",
        "health():",
    ):
        assert token in service_src, f"NestJS service missing {token}"

    assert controller_path.exists(), "NestJS controller should be generated"
    controller_src = controller_path.read_text(encoding="utf-8")
    controller_tokens = (
        '@Controller("security-headers")',
        '@Get("health")',
        '@Get("headers")',
    )
    for token in controller_tokens:
        assert (
            token in controller_src or token.replace('"', "'") in controller_src
        ), f"NestJS controller missing {token}"

    assert module_path.exists(), "NestJS module should be generated"
    module_src = module_path.read_text(encoding="utf-8")
    for token in (
        "export const SECURITY_HEADERS_OPTIONS_TOKEN",
        "static register",
        "useFactory",
        "exports: [SecurityHeadersService]",
    ):
        assert token in module_src, f"NestJS module missing {token}"

    assert configuration_path.exists(), "NestJS configuration should be generated"
    configuration_src = configuration_path.read_text(encoding="utf-8")
    for token in ("registerAs", "securityHeadersConfiguration", "SECURITY_HEADERS_ENABLED"):
        assert token in configuration_src, f"NestJS configuration missing {token}"

    assert health_controller_path.exists(), "NestJS health controller should be generated"
    health_controller_src = health_controller_path.read_text(encoding="utf-8")
    for token in (
        "@Controller('api/health/module')",
        "@Get('security-headers')",
        "ServiceUnavailableException",
    ):
        assert (
            token in health_controller_src or token.replace("'", '"') in health_controller_src
        ), f"NestJS health controller missing {token}"

    assert health_module_path.exists(), "NestJS health module should be generated"
    health_module_src = health_module_path.read_text(encoding="utf-8")
    for token in ("import { SecurityHeadersModule }", "SecurityHeadersHealthController"):
        assert token in health_module_src, f"NestJS health module missing {token}"

    assert integration_test_path.exists(), "NestJS integration test should be generated"
    integration_src = integration_test_path.read_text(encoding="utf-8")
    for token in (
        "supertest",
        "describe('SecurityHeadersModule",
        "get('/api/health/module/security-headers')",
    ):
        assert (
            token in integration_src or token.replace("'", '"') in integration_src
        ), f"NestJS integration test missing {token}"
