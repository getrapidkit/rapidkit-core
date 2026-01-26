from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict, Mapping

import pytest

from modules.free.communication.email import generate as email_generate


class StubRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Mapping[str, Any]]] = []

    def render(self, template_path: Path, context: Mapping[str, Any]) -> str:
        self.calls.append((template_path, context))
        return template_path.name


@pytest.fixture
def module_config() -> Dict[str, Any]:
    return email_generate.load_module_config()


def test_template_renderer_falls_back_without_jinja(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "sample.j2"
    template_path.write_text("Hello {{ name }}", encoding="utf-8")

    renderer = email_generate.TemplateRenderer(template_dir)
    renderer.jinja_env = None  # type: ignore[attr-defined]

    rendered = renderer.render(template_path, {"name": "Email"})
    assert rendered == "Hello Email"


def test_template_renderer_renders_when_env_available(module_config: Dict[str, Any]) -> None:
    renderer = email_generate.create_renderer()
    if getattr(renderer, "jinja_env", None) is None:
        pytest.skip("jinja2 not available in this environment")

    context = email_generate.build_base_context(module_config)
    rendered = renderer.render(
        email_generate.MODULE_ROOT / "templates/variants/fastapi/email.py.j2",
        context,
    )
    assert "Project-facing wrapper" in rendered


def test_build_base_context_uses_config_defaults(module_config: Dict[str, Any]) -> None:
    context = email_generate.build_base_context(module_config)
    assert context["module_class_name"] == email_generate.MODULE_CLASS
    assert context["python_config_relative"] == email_generate.PYTHON_CONFIG_REL
    assert context["nest_test_relative"] == email_generate.NEST_TEST_REL
    assert "email_defaults" in context


def test_generate_vendor_files_creates_vendor_artifacts(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = email_generate.create_renderer()
    if getattr(renderer, "jinja_env", None) is None:
        pytest.skip("jinja2 not available in this environment")
    context = email_generate.build_base_context(module_config)
    email_generate.generate_vendor_files(module_config, tmp_path, renderer, context)

    vendor_top = (
        tmp_path
        / ".rapidkit/vendor"
        / context["rapidkit_vendor_module"]
        / context["rapidkit_vendor_version"]
    )
    vendor_file = vendor_top / "src" / "modules" / "free" / "communication" / "email" / "email.py"
    assert vendor_file.exists()
    runtime_src = vendor_file.read_text(encoding="utf-8")
    for token in (
        "class EmailService",
        "async def send_templated_email",
        "def get_email_service",
        "def register_email_service",
        "def list_email_features",
        "__all__",
    ):
        assert token in runtime_src, f"Vendor runtime missing {token}"

    email_health_file = vendor_top / "src" / "health" / "email.py"
    email_types_file = (
        vendor_top / "src" / "modules" / "free" / "communication" / "email" / "email_types.py"
    )

    assert email_health_file.exists()
    assert email_types_file.exists()

    health_src = email_health_file.read_text(encoding="utf-8")
    for token in ("def register_email_health", "def email_health_check", "describe_email"):
        assert token in health_src, f"Vendor health helper missing {token}"

    types_src = email_types_file.read_text(encoding="utf-8")
    for token in ("class EmailHealthSnapshot", "def as_dict"):
        assert token in types_src, f"Vendor types missing {token}"


def test_generate_variant_files_creates_outputs(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = email_generate.create_renderer()
    if getattr(renderer, "jinja_env", None) is None:
        pytest.skip("jinja2 not available in this environment")
    context = email_generate.build_base_context(module_config)
    email_generate.generate_variant_files(module_config, "fastapi", tmp_path, renderer, context)

    variant_output = tmp_path / "src" / "modules" / "free" / "communication" / "email" / "email.py"
    assert variant_output.exists()

    types_output = (
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "email_types.py"
    )
    assert types_output.exists()

    health_output = tmp_path / "src" / "health" / "email.py"
    routes_output = (
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "routers" / "email.py"
    )

    assert health_output.exists()
    assert routes_output.exists()

    config_output = (
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "config" / "email.yaml"
    )
    test_output = (
        tmp_path
        / "tests"
        / "modules"
        / "free"
        / "communication"
        / "email"
        / "test_email_integration.py"
    )

    assert config_output.exists()
    assert test_output.exists()

    runtime_src = variant_output.read_text(encoding="utf-8")
    for token in (
        "AttachmentPayload = _resolve_export",
        "EmailService = _resolve_export",
        "register_email_service = _resolve_export",
        "refresh_vendor_module",
        "__all__",
    ):
        assert token in runtime_src, f"FastAPI runtime adapter missing {token}"

    health_src = health_output.read_text(encoding="utf-8")
    for token in (
        "def build_health_router",
        "register_email_health",
        "refresh_vendor_module",
    ):
        assert token in health_src, f"FastAPI health shim missing {token}"

    config_src = config_output.read_text(encoding="utf-8")
    for token in ("email:", "provider:", "smtp:", "template:"):
        assert token in config_src, f"FastAPI config missing {token}"

    test_src = test_output.read_text(encoding="utf-8")
    for token in (
        "async def test_send_email",
        "await async_client.post",
        "status_code == 202",
        'payload["accepted"] is True',
    ):
        assert token in test_src, f"Integration test missing {token}"


def test_generate_variants_produce_expected_outputs(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = email_generate.create_renderer()
    if getattr(renderer, "jinja_env", None) is None:
        pytest.skip("jinja2 not available in this environment")

    base_context = email_generate.build_base_context(module_config)

    email_generate.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
    )
    vendor_expected = {
        vendor_root / "src" / "modules" / "free" / "communication" / "email" / "email.py",
        vendor_root / "src" / "health" / "email.py",
        vendor_root / "src" / "modules" / "free" / "communication" / "email" / "email_types.py",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated vendor file {artefact} is empty"

    email_generate.generate_variant_files(
        module_config, "fastapi", tmp_path, renderer, base_context
    )
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "email.py",
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "routers" / "email.py",
        tmp_path / "src" / "health" / "email.py",
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "config" / "email.yaml",
        tmp_path
        / "tests"
        / "modules"
        / "free"
        / "communication"
        / "email"
        / "test_email_integration.py",
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated FastAPI file {artefact} is empty"

    router_src = (
        tmp_path / "src" / "modules" / "free" / "communication" / "email" / "routers" / "email.py"
    ).read_text()
    assert any(
        token in router_src
        for token in (
            'APIRouter(prefix="/communication/email"',
            "APIRouter(prefix='/communication/email'",
        )
    ), "FastAPI router should expose /communication/email namespace"
    for endpoint in ("/metadata", "/features", "/send", "/send-templated", "/verify", "/status"):
        assert any(
            token in router_src
            for token in (
                f"@router.get('{endpoint}'",
                f'@router.get("{endpoint}"',
                f"@router.post('{endpoint}'",
                f'@router.post("{endpoint}"',
            )
        ), f"FastAPI router should expose {endpoint} endpoint"

    email_generate.generate_variant_files(module_config, "nestjs", tmp_path, renderer, base_context)
    nest_root = tmp_path / "src" / "modules" / "free" / "communication" / "email"
    nest_expected = {
        nest_root / "email.service.ts",
        nest_root / "email.controller.ts",
        nest_root / "email.module.ts",
        nest_root / "email.configuration.ts",
        tmp_path / "src" / "health" / "email.health.ts",
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "communication"
        / "email.integration.spec.ts",
    }
    for artefact in nest_expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated NestJS file {artefact} is empty"

    controller_src = (nest_root / "email.controller.ts").read_text()
    assert any(
        token in controller_src
        for token in (
            "@Controller('communication/email')",
            '@Controller("communication/email")',
        )
    ), "NestJS controller should mount communication/email route"
    for decorator in (
        "@Get('metadata')",
        "@Get('features')",
        "@Get('status')",
        "@Post('verify')",
        "@Post('send')",
        "@Post('send-templated')",
    ):
        counterpart = decorator.replace("'", '"')
        assert (
            decorator in controller_src or counterpart in controller_src
        ), f"Expected {decorator} handler"

    module_src = (nest_root / "email.module.ts").read_text()
    for token in (
        "export class EmailModule",
        "DynamicModule",
        "EMAIL_MODULE_CONFIG",
        "EMAIL_TEMPLATE_OPTIONS",
        "EMAIL_TRANSPORT",
        "static register",
    ):
        assert token in module_src, f"NestJS module missing {token}"

    service_src = (nest_root / "email.service.ts").read_text()
    for signature in (
        "export class EmailService",
        "const FEATURE_FLAGS",
        "async sendEmail",
        "async sendTemplatedEmail",
        "async verifyConnection",
        "status():",
        "describe():",
        "listFeatures():",
        "EmailDeliveryError",
        "EmailSendResult",
    ):
        assert signature in service_src, f"Expected service element {signature}"

    config_src = (nest_root / "email.configuration.ts").read_text(encoding="utf-8")
    for token in ("registerAs('email'", "provider:", "smtp:"):
        assert token in config_src, f"NestJS configuration missing {token}"

    health_src = (tmp_path / "src" / "health" / "email.health.ts").read_text(encoding="utf-8")
    for token in ("EmailHealthIndicator", "extends HealthIndicator", "isHealthy"):
        assert token in health_src, f"NestJS health indicator missing {token}"

    integration_src = (
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "communication"
        / "email.integration.spec.ts"
    ).read_text(encoding="utf-8")
    for token in (
        "describe('EmailModule (Integration)'",
        "request(server)",
        "post('/communication/email/send')",
    ):
        assert token in integration_src, f"NestJS integration test missing {token}"


def test_generate_variant_files_unknown_variant(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = StubRenderer()
    context = email_generate.build_base_context(module_config)

    with pytest.raises(email_generate.GeneratorError):
        email_generate.generate_variant_files(module_config, "unknown", tmp_path, renderer, context)


def test_generate_vendor_files_missing_template(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = StubRenderer()
    broken_config = copy.deepcopy(module_config)
    broken_config["generation"]["vendor"]["files"][0]["template"] = "missing.j2"
    context = email_generate.build_base_context(broken_config)

    with pytest.raises(email_generate.GeneratorError):
        email_generate.generate_vendor_files(broken_config, tmp_path, renderer, context)


def test_format_missing_dependencies_reports_each_package() -> None:
    message = email_generate.format_missing_dependencies({"jinja2": "Install it"})
    assert "jinja2" in message


def test_main_requires_arguments() -> None:
    original = sys.argv
    sys.argv = ["generate"]
    try:
        with pytest.raises(email_generate.GeneratorError):
            email_generate.main()
    finally:
        sys.argv = original


def test_main_generates_files_with_stub_renderer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _create_stub_renderer(_self: email_generate.EmailModuleGenerator) -> StubRenderer:
        return StubRenderer()

    monkeypatch.setattr(
        email_generate.EmailModuleGenerator,
        "create_renderer",
        _create_stub_renderer,
    )
    monkeypatch.setattr(
        email_generate,
        "ensure_version_consistency",
        lambda config, **_kwargs: (config, False),
    )

    original = sys.argv
    sys.argv = ["generate", "fastapi", str(tmp_path)]
    try:
        email_generate.main()
    finally:
        sys.argv = original

    assert (tmp_path / "src" / "modules" / "free" / "communication" / "email" / "email.py").exists()
