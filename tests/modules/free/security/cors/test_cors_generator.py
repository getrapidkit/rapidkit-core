from __future__ import annotations

import copy
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Mapping

import pytest

from modules.free.security.cors import generate as cors_generate


class StubRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Mapping[str, Any]]] = []

    def render(self, template_path: Path, context: Mapping[str, Any]) -> str:
        self.calls.append((template_path, context))
        return template_path.name


@pytest.fixture
def module_config() -> Dict[str, Any]:
    return cors_generate.load_module_config()


def test_module_imports() -> None:
    module = importlib.import_module("modules.free.security.cors.generate")
    assert hasattr(module, "main")


def test_template_renderer_requires_select_autoescape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cors_generate, "JinjaEnvironment", object())

    def dummy_loader(*_args: object, **_kwargs: object) -> object:
        return object()

    monkeypatch.setattr(cors_generate, "FileSystemLoader", dummy_loader)
    monkeypatch.setattr(cors_generate, "StrictUndefined", object())
    monkeypatch.setattr(cors_generate, "select_autoescape", None)

    with pytest.raises(cors_generate.GeneratorError):
        cors_generate.TemplateRenderer()


def test_template_renderer_requires_env() -> None:
    renderer = cors_generate.TemplateRenderer()
    renderer._env = None  # type: ignore[attr-defined]
    with pytest.raises(cors_generate.GeneratorError):
        renderer.render(cors_generate.MODULE_ROOT / "templates/variants/fastapi/cors.py.j2", {})


def test_infer_vendor_settings_path_returns_vendor_relative(module_config: Dict[str, Any]) -> None:
    relative = cors_generate.infer_vendor_settings_path(module_config)
    assert relative.endswith("src/modules/free/security/cors/cors.py")


def test_generate_vendor_files_creates_output(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = StubRenderer()
    context = cors_generate.build_base_context(module_config)
    cors_generate.generate_vendor_files(module_config, tmp_path, renderer, context)

    vendor_output = (
        tmp_path
        / ".rapidkit/vendor"
        / context["rapidkit_vendor_module"]
        / context["rapidkit_vendor_version"]
        / "src/modules/free/security/cors/cors.py"
    )
    assert vendor_output.exists()
    assert vendor_output.read_text(encoding="utf-8")


def test_generate_vendor_files_missing_destination(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = StubRenderer()
    broken_config = copy.deepcopy(module_config)
    broken_config["generation"]["vendor"]["files"][0].pop("relative")
    context = cors_generate.build_base_context(broken_config)

    with pytest.raises(cors_generate.GeneratorError):
        cors_generate.generate_vendor_files(broken_config, tmp_path, renderer, context)


def test_generate_variant_files_unknown_variant(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = StubRenderer()
    context = cors_generate.build_base_context(module_config)

    with pytest.raises(cors_generate.GeneratorError):
        cors_generate.generate_variant_files(module_config, "unknown", tmp_path, renderer, context)


def test_generate_variant_files_missing_template(
    module_config: Dict[str, Any], tmp_path: Path
) -> None:
    renderer = StubRenderer()
    corrupted = copy.deepcopy(module_config)
    corrupted["generation"]["variants"]["fastapi"]["files"][0]["template"] = "missing.j2"
    context = cors_generate.build_base_context(corrupted)

    with pytest.raises(cors_generate.GeneratorError):
        cors_generate.generate_variant_files(corrupted, "fastapi", tmp_path, renderer, context)


def test_format_missing_dependencies_reports_packages() -> None:
    message = cors_generate._format_missing_dependencies({"jinja2": "Install"})
    assert "jinja2" in message


def test_main_requires_arguments() -> None:
    original = sys.argv
    sys.argv = ["generate"]
    try:
        with pytest.raises(cors_generate.GeneratorError):
            cors_generate.main()
    finally:
        sys.argv = original


def test_main_generates_files_with_stub_renderer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cors_generate, "TemplateRenderer", lambda: StubRenderer())
    monkeypatch.setattr(
        cors_generate,
        "ensure_version_consistency",
        lambda config, **_kwargs: (config, False),
    )

    original = sys.argv
    sys.argv = ["generate", "fastapi", str(tmp_path)]
    try:
        cors_generate.main()
    finally:
        sys.argv = original

    assert (tmp_path / "src" / "modules" / "free" / "security" / "cors" / "cors.py").exists()


def test_main_reports_missing_optional_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cors_generate, "JinjaEnvironment", None)
    monkeypatch.setattr(cors_generate, "FileSystemLoader", None)
    monkeypatch.setattr(cors_generate, "StrictUndefined", None)
    monkeypatch.setattr(cors_generate, "select_autoescape", None)
    monkeypatch.setattr(
        cors_generate,
        "ensure_version_consistency",
        lambda config, **_kwargs: (config, False),
    )

    def fail_vendor(*_args, **_kwargs) -> None:
        raise cors_generate.GeneratorError("Renderer unavailable")

    monkeypatch.setattr(cors_generate, "TemplateRenderer", lambda: StubRenderer())
    monkeypatch.setattr(cors_generate, "generate_vendor_files", fail_vendor)

    def noop_variant(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(cors_generate, "generate_variant_files", noop_variant)

    original = sys.argv
    sys.argv = ["generate", "fastapi", str(tmp_path)]
    try:
        with pytest.raises(SystemExit):
            cors_generate.main()
    finally:
        sys.argv = original

    out = capsys.readouterr().out
    assert "Renderer unavailable" in out
    assert "Missing optional dependencies" in out


@pytest.mark.parametrize("variant", ["fastapi", "nestjs"])
def test_variant_templates_exist(variant: str) -> None:
    templates_dir = Path("src/modules/free/security/cors/templates")
    assert (templates_dir / "base" / "cors.py.j2").exists()
    variant_dir = templates_dir / "variants" / variant
    assert variant_dir.exists()


def test_snippets_config_enabled(module_config: Dict[str, Any]) -> None:
    snippets = module_config.get("generation", {}).get("snippets", {})
    assert snippets.get("enabled") is True
    assert snippets.get("config") == "config/snippets.yaml"


@pytest.mark.parametrize("variant", ["fastapi", "nestjs"], ids=["fastapi", "nestjs"])
def test_generator_emits_framework_parity(
    module_config: Dict[str, Any], tmp_path: Path, variant: str
) -> None:
    renderer = cors_generate.TemplateRenderer()
    if getattr(renderer, "_env", None) is None:
        pytest.skip("jinja2 is required to render CORS templates")

    context = cors_generate.build_base_context(module_config)
    target_dir = tmp_path / "generated"
    target_dir.mkdir()

    cors_generate.generate_vendor_files(module_config, target_dir, renderer, context)
    cors_generate.generate_variant_files(module_config, variant, target_dir, renderer, context)

    vendor_cfg = module_config["generation"]["vendor"]
    vendor_root = Path(vendor_cfg.get("root", ".rapidkit/vendor"))
    module_name = context["rapidkit_vendor_module"]
    version = str(context["rapidkit_vendor_version"])

    expected_vendor_files = {
        target_dir / vendor_root / module_name / version / Path(entry["relative"])
        for entry in vendor_cfg.get("files", [])
    }

    for vendor_path in expected_vendor_files:
        assert vendor_path.exists(), f"Expected vendor artefact {vendor_path}"
        contents = vendor_path.read_text(encoding="utf-8").strip()
        assert contents, f"Vendor artefact {vendor_path} is empty"

        # vendor runtime vs health may both be named `cors.py`; disambiguate
        # based on the vendor path.
        if vendor_path.as_posix().endswith("src/modules/free/security/cors/cors.py"):
            assert "class CorsConfig" in contents
            assert "def build_default_config" in contents
        elif vendor_path.as_posix().endswith("src/health/cors.py"):
            assert "build_health_snapshot" in contents
            assert "render_health_snapshot" in contents
            assert "_CORS_FEATURES" in contents
        elif vendor_path.name == "cors_types.py":
            assert "class CorsHealthSnapshot" in contents
            assert "class CorsPolicySnapshot" in contents
        elif vendor_path.suffix == ".js":
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    if variant == "fastapi":
        runtime_path = target_dir / "src" / "modules" / "free" / "security" / "cors" / "cors.py"
        routes_path = (
            target_dir / "src" / "modules" / "free" / "security" / "cors" / "routers" / "cors.py"
        )
        health_path = target_dir / "src" / "health" / "cors.py"
        shared_types_path = (
            target_dir / "src" / "modules" / "free" / "security" / "cors" / "cors_types.py"
        )
        integration_path = (
            target_dir
            / "tests"
            / "modules"
            / "integration"
            / "security"
            / "test_cors_integration.py"
        )

        for artefact in (
            runtime_path,
            routes_path,
            health_path,
            shared_types_path,
            integration_path,
        ):
            assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
            contents = artefact.read_text(encoding="utf-8").strip()
            assert contents, f"FastAPI artefact {artefact} is empty"

        runtime_src = runtime_path.read_text(encoding="utf-8")
        assert "class CORSConfig" in runtime_src
        assert "def create_cors_middleware" in runtime_src
        assert "def setup_cors" in runtime_src
        assert "cors_settings" in runtime_src

        routes_src = routes_path.read_text(encoding="utf-8")
        assert "register_cors_routes" in routes_src
        assert "build_health_snapshot" in routes_src
        assert "Any" in routes_src  # guard against missing import retry

        health_src = health_path.read_text(encoding="utf-8")
        # Accept either the router registration (variant-level) or the
        # shared helper materialised into the canonical public path.
        assert "register_cors_health" in health_src or "build_health_snapshot" in health_src
        # Accept either a router-style handler or shared helper materialisation
        assert (
            "cors_health_check" in health_src
            or "register_cors_health" in health_src
            or "build_health_snapshot" in health_src
        )
        assert (
            ("status.HTTP_200_OK" in health_src)
            or ("build_health_snapshot" in health_src)
            or ("build_health_router" in health_src)
        )

        integration_src = integration_path.read_text(encoding="utf-8")
        assert "test_generator_entrypoint" in integration_src

    else:
        service_path = (
            target_dir / "src" / "modules" / "free" / "security" / "cors" / "cors.service.ts"
        )
        controller_path = (
            target_dir / "src" / "modules" / "free" / "security" / "cors" / "cors.controller.ts"
        )
        module_path = (
            target_dir / "src" / "modules" / "free" / "security" / "cors" / "cors.module.ts"
        )

        for artefact in (service_path, controller_path, module_path):
            assert artefact.exists(), f"Expected NestJS artefact {artefact}"
            contents = artefact.read_text(encoding="utf-8").strip()
            assert contents, f"NestJS artefact {artefact} is empty"

        controller_src = controller_path.read_text(encoding="utf-8")
        assert (
            "@Controller('security/cors')" in controller_src
            or '@Controller("security/cors")' in controller_src
        )
        assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
        assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
        assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
        assert "CORS_FEATURES" in controller_src

        service_src = service_path.read_text(encoding="utf-8")
        assert "class CorsService" in service_src
        assert "setCorsOptions" in service_src
        assert "getStatus" in service_src

        module_src = module_path.read_text(encoding="utf-8")
        assert "@Module" in module_src
        assert "CorsService" in module_src
        assert "CorsModule" in module_src
