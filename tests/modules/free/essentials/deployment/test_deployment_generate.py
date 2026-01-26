# ruff: noqa: I001
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping

import pytest  # type: ignore[import-not-found]

from modules.free.essentials.deployment.frameworks.fastapi import (
    FastAPIPlugin,  # type: ignore[import-not-found]
)
from modules.shared.frameworks.base import FrameworkPlugin  # type: ignore[import-not-found]
from modules.shared.generator import TemplateRenderer  # type: ignore[import-not-found]

generate_module = import_module("modules.free.essentials.deployment.generate")

MODULE_ROOT = generate_module.MODULE_ROOT
TEMPLATES_ROOT = generate_module.TEMPLATES_ROOT
GeneratorError = generate_module.GeneratorError
build_base_context = generate_module.build_base_context
generate_variant_files = generate_module.generate_variant_files
generate_vendor_files = generate_module.generate_vendor_files
load_module_config = generate_module.load_module_config


@pytest.fixture(autouse=True)
def _stub_framework_requirement_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid local runtime dependency checks during generator tests."""

    frameworks = import_module("modules.free.essentials.deployment.frameworks")
    original_get_plugin = frameworks.get_plugin

    def _patched_get_plugin(name: str):
        plugin = original_get_plugin(name)
        monkeypatch.setattr(plugin, "validate_requirements", lambda: [], raising=False)
        return plugin

    monkeypatch.setattr(frameworks, "get_plugin", _patched_get_plugin)
    monkeypatch.setattr(generate_module, "get_plugin", _patched_get_plugin)


@pytest.mark.parametrize("variant", ["fastapi", "nestjs"], ids=["fastapi", "nestjs"])
def test_generator_creates_expected_files(tmp_path: Path, variant: str) -> None:
    target_dir = tmp_path / "generated"
    target_dir.mkdir()

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(TEMPLATES_ROOT)
    jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Deployment templates")

    generate_vendor_files(module_config, target_dir, renderer, base_context)
    generate_variant_files(variant, target_dir, renderer, base_context)

    vendor_cfg = module_config["generation"]["vendor"]
    vendor_root = Path(vendor_cfg.get("root", ".rapidkit/vendor"))
    module_name = base_context["rapidkit_vendor_module"]
    version = base_context["rapidkit_vendor_version"]

    expected_vendor_files = {
        target_dir / vendor_root / module_name / version / Path(entry["relative"])
        for entry in vendor_cfg.get("files", [])
    }

    for file_path in expected_vendor_files:
        assert file_path.exists(), f"Expected vendor file {file_path} to be generated"
        assert file_path.read_text().strip(), f"Generated vendor file {file_path} is empty"

    frameworks = import_module("modules.free.essentials.deployment.frameworks")
    plugin = frameworks.get_plugin(variant)
    output_paths = plugin.get_output_paths()

    for logical_name, output_path in output_paths.items():
        file_path = target_dir / output_path
        assert file_path.exists(), f"Expected plugin file {file_path} for {logical_name}"
        assert file_path.read_text().strip(), f"Generated plugin file {file_path} is empty"

    if variant == "nestjs":
        controller_src = (target_dir / output_paths["controller"]).read_text()
        assert (
            "@Controller('deployment')" in controller_src
            or '@Controller("deployment")' in controller_src
        ), "Deployment controller should mount deployment routes"
        assert "@Get('plan')" in controller_src or '@Get("plan")' in controller_src
        assert "@Get('assets')" in controller_src or '@Get("assets")' in controller_src

        module_src = (target_dir / output_paths["module"]).read_text()
        assert "@Module" in module_src
        assert "DeploymentController" in module_src
        assert "DeploymentService" in module_src

        health_controller_src = (target_dir / output_paths["health_controller"]).read_text()
        assert (
            "@Controller('api/health/module')" in health_controller_src
            or '@Controller("api/health/module")' in health_controller_src
        ), "Health controller should mount /api/health/module namespace"
        assert (
            "@Get('deployment')" in health_controller_src
            or '@Get("deployment")' in health_controller_src
        ), "Health controller should expose deployment health endpoint"
        assert "HttpCode" in health_controller_src
        assert "ServiceUnavailableException" in health_controller_src
        assert "DeploymentService" in health_controller_src
        assert "getDeploymentHealth" in health_controller_src

        service_src = (target_dir / output_paths["service"]).read_text()
        assert "getPlan" in service_src
        assert "describePlan" in service_src
        assert "listAssets" in service_src
        assert "getHealth" in service_src
        assert "const VENDOR_MODULE" in service_src

        health_module_src = (target_dir / output_paths["health_module"]).read_text()
        assert "DeploymentHealthController" in health_module_src
        assert "DeploymentHealthModule" in health_module_src
        assert "DeploymentModule" in health_module_src

        configuration_src = (target_dir / output_paths["configuration"]).read_text()
        assert (
            "registerAs('deployment'" in configuration_src
            or 'registerAs("deployment"' in configuration_src
        )
        assert "includeCi" in configuration_src

        integration_spec_src = (target_dir / output_paths["integration_tests"]).read_text()
        assert "describe('DeploymentModule" in integration_spec_src
        assert (
            "get('/deployment/plan')" in integration_spec_src
            or 'get("/deployment/plan")' in integration_spec_src
        )
    else:
        routes_src = (target_dir / output_paths["routes"]).read_text()
        assert (
            'APIRouter(prefix="/deployment"' in routes_src
            or "APIRouter(prefix='/deployment'" in routes_src
        ), "Deployment router should expose /deployment namespace"
        assert '@router.get("/plan"' in routes_src or "@router.get('/plan'" in routes_src
        assert '@router.get("/assets"' in routes_src or "@router.get('/assets'" in routes_src

        health_src = (target_dir / output_paths["health_router"]).read_text()
        # Health router may be a framework-specific router or a vendor-backed shim
        assert (
            'APIRouter(prefix="/api/health/module"' in health_src
            or "APIRouter(prefix='/api/health/module'" in health_src
            or "Project shim exposing vendor health helpers for deployment" in health_src
            or "build_health_router" in health_src
        ), "Health router should mount /api/health/module namespace or be a vendor shim"

        integration_src = (target_dir / output_paths["integration_tests"]).read_text()
        assert "TestClient" in integration_src
        assert "deployment" in integration_src.lower()

        config_path = target_dir / output_paths["config"]
        assert config_path.exists(), "Deployment configuration YAML should be generated"
        config_contents = config_path.read_text()
        assert "deployment:" in config_contents
        assert "include_ci" in config_contents


def test_generate_variant_files_raises_on_requirement_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    class FailingPlugin(FrameworkPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple property
            return "failing"

        @property
        def language(self) -> str:  # pragma: no cover - trivial
            return "python"

        @property
        def display_name(self) -> str:  # pragma: no cover - trivial
            return "Failing"

        def get_template_mappings(self) -> dict[str, str]:
            return {}

        def get_output_paths(self) -> dict[str, str]:
            return {}

        def get_context_enrichments(self, base_context: Mapping[str, Any]) -> dict[str, Any]:
            return dict(base_context)

        def validate_requirements(self) -> list[str]:
            return ["missing dependency"]

    frameworks = import_module("modules.free.essentials.deployment.frameworks")
    original_get_plugin = frameworks.get_plugin

    def _get_plugin(name: str):
        if name == "failing":
            return FailingPlugin()  # type: ignore[return-value]
        return original_get_plugin(name)

    monkeypatch.setattr(frameworks, "get_plugin", _get_plugin)
    monkeypatch.setattr(generate_module, "get_plugin", _get_plugin)

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    with pytest.raises(GeneratorError) as exc:
        generate_variant_files("failing", Path.cwd(), renderer, base_context)

    assert "requirements failed" in str(exc.value)


def test_generate_variant_files_runs_pre_generation_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frameworks = import_module("modules.free.essentials.deployment.frameworks")

    marker_file = tmp_path / "pre_generation_invoked"

    class TrackingPlugin(FastAPIPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple override
            return "tracking-fastapi"

        def pre_generation_hook(self, output_dir: Path) -> None:
            marker_file.write_text("ran")
            super().pre_generation_hook(output_dir)

        def validate_requirements(self) -> list[str]:
            return []

    original_get_plugin = frameworks.get_plugin

    def _get_plugin(name: str):
        if name == "tracking-fastapi":
            return TrackingPlugin()
        return original_get_plugin(name)

    monkeypatch.setattr(frameworks, "get_plugin", _get_plugin)
    monkeypatch.setattr(generate_module, "get_plugin", _get_plugin)

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    generate_variant_files("tracking-fastapi", tmp_path, renderer, base_context)

    assert marker_file.exists(), "Expected pre-generation hook to create marker file"


def test_generate_variant_files_raises_on_pre_generation_hook_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frameworks = import_module("modules.free.essentials.deployment.frameworks")

    class FailingPreHookPlugin(FastAPIPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple override
            return "failing-pre-hook"

        def pre_generation_hook(self, output_dir: Path) -> None:  # pragma: no cover
            raise RuntimeError("boom")

        def validate_requirements(self) -> list[str]:
            return []

    original_get_plugin = frameworks.get_plugin

    def _get_plugin(name: str):
        if name == "failing-pre-hook":
            return FailingPreHookPlugin()
        return original_get_plugin(name)

    monkeypatch.setattr(frameworks, "get_plugin", _get_plugin)
    monkeypatch.setattr(generate_module, "get_plugin", _get_plugin)

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    with pytest.raises(GeneratorError) as exc:
        generate_variant_files("failing-pre-hook", tmp_path, renderer, base_context)

    assert "Pre-generation hook failed" in str(exc.value)


def test_generate_variant_files_reports_post_generation_hook_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    frameworks = import_module("modules.free.essentials.deployment.frameworks")

    class FailingPostHookPlugin(FastAPIPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple override
            return "failing-post-hook"

        def validate_requirements(self) -> list[str]:
            return []

        def post_generation_hook(self, output_dir: Path) -> None:  # pragma: no cover
            raise RuntimeError("post boom")

    original_get_plugin = frameworks.get_plugin

    def _get_plugin(name: str):
        if name == "failing-post-hook":
            return FailingPostHookPlugin()
        return original_get_plugin(name)

    monkeypatch.setattr(frameworks, "get_plugin", _get_plugin)
    monkeypatch.setattr(generate_module, "get_plugin", _get_plugin)

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    generate_variant_files("failing-post-hook", tmp_path, renderer, base_context)

    captured = capsys.readouterr()
    assert "Post-generation hook failed" in captured.out


def test_generate_variant_files_respects_skip_ci_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_SKIP_CI", "1")

    module_config = load_module_config()
    overrides = generate_module.DeploymentOverrides(generate_module.MODULE_ROOT)
    base_context = overrides.apply_base_context(build_base_context(module_config))
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    generate_variant_files("fastapi", tmp_path, renderer, base_context, overrides)

    workflow_path = tmp_path / ".github/workflows/ci.yml"
    assert not workflow_path.exists(), "Expected CI workflow to be skipped by override"


def test_generate_variant_files_writes_extra_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_path = tmp_path / "extra-workflow.yml.j2"
    template_path.write_text("name: extra for {{ variant }}\n")
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW", str(template_path))

    module_config = load_module_config()
    overrides = generate_module.DeploymentOverrides(generate_module.MODULE_ROOT)
    base_context = overrides.apply_base_context(build_base_context(module_config))
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    generate_variant_files("fastapi", tmp_path, renderer, base_context, overrides)

    expected_output = tmp_path / ".github/workflows/extra-workflow.yml"
    assert expected_output.exists(), "Expected extra workflow to be rendered"
    assert "extra for fastapi" in expected_output.read_text()


def test_generate_variant_files_raises_when_extra_workflow_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW", str(tmp_path / "missing.yml.j2"))

    module_config = load_module_config()
    overrides = generate_module.DeploymentOverrides(generate_module.MODULE_ROOT)
    base_context = overrides.apply_base_context(build_base_context(module_config))
    renderer = TemplateRenderer(TEMPLATES_ROOT)

    with pytest.raises(GeneratorError) as exc:
        generate_variant_files("fastapi", tmp_path, renderer, base_context, overrides)

    assert "Extra workflow template" in str(exc.value)
