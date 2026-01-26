from __future__ import annotations

import copy
from importlib import import_module
from pathlib import Path

import pytest  # type: ignore[import-not-found]

from modules.shared.generator import TemplateRenderer  # type: ignore[import-not-found]

generate_module = import_module("modules.free.essentials.settings.generate")

MODULE_ROOT = generate_module.MODULE_ROOT
GeneratorError = generate_module.GeneratorError
build_base_context = generate_module.build_base_context
generate_variant_files = generate_module.generate_variant_files
generate_vendor_files = generate_module.generate_vendor_files
load_module_config = generate_module.load_module_config


@pytest.fixture(autouse=True)
def _stub_framework_requirement_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid relying on local FastAPI/Node installations during generator tests."""

    frameworks = import_module("modules.free.essentials.settings.frameworks")

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

    # Use the actual MODULE_ROOT as template root for settings module
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    generate_vendor_files(module_config, target_dir, renderer, base_context)
    generate_variant_files(variant, target_dir, renderer, base_context)

    # Check vendor files
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
        vendor_contents = file_path.read_text().strip()
        assert vendor_contents, f"Generated vendor file {file_path} is empty"

        if file_path.suffix == ".js":
            assert "module.exports" in vendor_contents
            assert "DEFAULT_CONFIG" in vendor_contents
            assert "refreshSettings" in vendor_contents
            assert "stopHotReload" in vendor_contents
            assert "HOT_RELOAD_DISABLED" in vendor_contents

    # Check framework-specific files using plugin expectations
    frameworks = import_module("modules.free.essentials.settings.frameworks")
    plugin = frameworks.get_plugin(variant)
    output_paths = plugin.get_output_paths()

    for logical_name, output_path in output_paths.items():
        file_path = target_dir / output_path
        assert (
            file_path.exists()
        ), f"Expected plugin file {file_path} to be generated for {logical_name}"
        assert file_path.read_text().strip(), f"Generated plugin file {file_path} is empty"

    if variant == "fastapi":
        settings_src = (target_dir / output_paths["settings"]).read_text()
        assert "configure_fastapi_app" in settings_src
        assert "overrides.setdefault" in settings_src
        assert "refresh_vendor_settings" in settings_src

        router_src = (target_dir / output_paths["router"]).read_text()
        assert "APIRouter" in router_src
        assert '@router.get("/"' in router_src or "@router.get('/'" in router_src
        assert '@router.post("/refresh"' in router_src or "@router.post('/refresh'" in router_src

        integration_src = (target_dir / output_paths["integration_tests"]).read_text()
        assert "configure_fastapi_app" in integration_src
        assert "test_settings_singleton" in integration_src

        custom_sources_src = (target_dir / output_paths["custom_sources"]).read_text()
        assert "load_from_yaml" in custom_sources_src
        assert "__all__" in custom_sources_src

        hot_reload_src = (target_dir / output_paths["hot_reload"]).read_text()
        assert "start_hot_reload" in hot_reload_src
        assert "_vendor" in hot_reload_src

        health_router_src = (target_dir / output_paths["settings_health"]).read_text()
        assert "register_settings_health" in health_router_src
        assert (
            "APIRouter" in health_router_src
            or "Project shim exposing vendor health helpers for settings" in health_router_src
            or "build_health_router" in health_router_src
        )

        if variant == "nestjs":
            controller_src = (target_dir / output_paths["settings_controller"]).read_text()
            assert (
                "@Controller('settings')" in controller_src
                or '@Controller("settings")' in controller_src
            ), "Settings controller should expose settings route"
            assert "@Get()" in controller_src
            assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
            assert "@Get('config')" in controller_src or '@Get("config")' in controller_src
            assert "SettingsMetadata" in controller_src

            module_src = (target_dir / output_paths["settings_module"]).read_text()
            assert "@Module" in module_src
            assert "SettingsController" in module_src
            assert "exports: [SettingsService]" in module_src

            service_src = (target_dir / output_paths["settings_service"]).read_text()
            assert "class SettingsService" in service_src
            assert "refresh():" in service_src
            assert "value<" in service_src
            assert "getMetadata" in service_src
            assert "getHealth()" in service_src

            configuration_src = (target_dir / output_paths["configuration"]).read_text()
            required_exports = [
                "export const settingsConfiguration",
                "export const getSettings",
                "export const refreshSettings",
                "export const loadSettings",
            ]
            for export in required_exports:
                assert export in configuration_src

            health_src = (target_dir / output_paths["settings_health"]).read_text()
            assert "SettingsHealthController" in health_src
            assert "@HttpCode(200)" in health_src or "@HttpCode(HttpStatus.OK)" in health_src

            metadata_src = (target_dir / output_paths["metadata"]).read_text()
            assert "buildSettingsMetadata" in metadata_src

            integration_src = (target_dir / output_paths["integration_tests"]).read_text()
            assert "SettingsModule (Integration)" in integration_src
            assert "get('/settings')" in integration_src


def test_nestjs_configuration_template_exports_expected_symbols() -> None:
    """Smoke test for Node/NestJS variant to ensure key exports exist."""

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    configuration_template = (
        MODULE_ROOT / "templates" / "variants" / "nestjs" / "configuration.ts.j2"
    )
    rendered = renderer.render(
        configuration_template,
        {**base_context, "vendor_configuration_relative": "nestjs/configuration.js"},
    )

    required_exports = [
        "export const settingsConfiguration",
        "export const getSettings",
        "export const refreshSettings",
        "export const loadSettings",
    ]

    for symbol in required_exports:
        assert symbol in rendered, f"Expected '{symbol}' export in NestJS configuration template"


def test_generate_variant_files_raises_on_requirement_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_module = import_module("modules.shared.frameworks.base")
    FrameworkPlugin = base_module.FrameworkPlugin

    class FailingPlugin(FrameworkPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple property
            return "failing"

        @property
        def language(self) -> str:  # pragma: no cover
            return "python"

        @property
        def display_name(self) -> str:  # pragma: no cover
            return "Failing"

        def get_template_mappings(self) -> dict[str, str]:
            return {}

        def get_output_paths(self) -> dict[str, str]:
            return {}

        def get_context_enrichments(self, base_context: dict[str, str]) -> dict[str, str]:
            return dict(base_context)

        def validate_requirements(self) -> list[str]:
            return ["missing dependency"]

    frameworks = import_module("modules.free.essentials.settings.frameworks")

    original_get_plugin = frameworks.get_plugin

    def _get_plugin(name: str):
        if name == "failing":
            return FailingPlugin()  # type: ignore[return-value]
        return original_get_plugin(name)

    monkeypatch.setattr(frameworks, "get_plugin", _get_plugin)
    monkeypatch.setattr(generate_module, "get_plugin", _get_plugin)

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    with pytest.raises(GeneratorError) as exc:
        generate_variant_files("failing", Path.cwd(), renderer, base_context)

    assert "requirements failed" in str(exc.value)


def test_generate_variant_files_runs_pre_generation_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frameworks = import_module("modules.free.essentials.settings.frameworks")
    fastapi_module = import_module("modules.free.essentials.settings.frameworks.fastapi")
    FastAPIPlugin = fastapi_module.FastAPIPlugin

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
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    generate_variant_files("tracking-fastapi", tmp_path, renderer, base_context)

    assert marker_file.exists(), "Expected pre-generation hook to create marker file"


def test_generate_variant_files_raises_on_pre_generation_hook_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frameworks = import_module("modules.free.essentials.settings.frameworks")
    fastapi_module = import_module("modules.free.essentials.settings.frameworks.fastapi")
    FastAPIPlugin = fastapi_module.FastAPIPlugin

    class FailingPreHookPlugin(FastAPIPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple override
            return "failing-pre-hook"

        def pre_generation_hook(self, output_dir: Path) -> None:  # pragma: no cover - trivial
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
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    with pytest.raises(GeneratorError) as exc:
        generate_variant_files("failing-pre-hook", tmp_path, renderer, base_context)

    assert "Pre-generation hook failed" in str(exc.value)


def test_generate_variant_files_reports_post_generation_hook_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    frameworks = import_module("modules.free.essentials.settings.frameworks")
    fastapi_module = import_module("modules.free.essentials.settings.frameworks.fastapi")
    FastAPIPlugin = fastapi_module.FastAPIPlugin

    class FailingPostHookPlugin(FastAPIPlugin):
        @property
        def name(self) -> str:  # pragma: no cover - simple override
            return "failing-post-hook"

        def validate_requirements(self) -> list[str]:
            return []

        def post_generation_hook(self, output_dir: Path) -> None:  # pragma: no cover - trivial
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
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    generate_variant_files("failing-post-hook", tmp_path, renderer, base_context)

    captured = capsys.readouterr()
    assert "Post-generation hook failed" in captured.out


def test_vendor_generation_filters_by_project_type(tmp_path: Path) -> None:
    """Ensure vendor files are filtered by target project type heuristics.

    - A target dir with pyproject.toml should skip node/nestjs vendor files.
    - A target dir with package.json should skip python vendor files.
    """

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    # Python host -> should only contain .py vendor files
    py_dir = tmp_path / "pyhost"
    py_dir.mkdir()
    (py_dir / "pyproject.toml").write_text('[tool.poetry]\nname="test"\n')
    generate_vendor_files(module_config, py_dir, renderer, base_context)
    vendor_root_value = module_config["generation"]["vendor"].get("root", ".rapidkit/vendor")
    vendor_root = Path(vendor_root_value)
    normalized_root = str(vendor_root).replace("\\", "/").lstrip("./")
    vendor_is_cache = normalized_root.startswith("rapidkit/vendor")
    module_name = base_context["rapidkit_vendor_module"]
    version = base_context["rapidkit_vendor_version"]
    vendor_dir = py_dir / vendor_root / module_name / version
    assert vendor_dir.exists()
    nestjs_paths = [p for p in vendor_dir.glob("**/*") if "nestjs" in str(p)]
    if vendor_is_cache:
        assert nestjs_paths, "Vendor cache should retain NestJS assets for Python projects"
    else:
        assert not nestjs_paths, "NestJS files should be skipped for Python projects"

    # Node host -> create package.json and ensure no .py vendor files
    node_dir = tmp_path / "nodehost"
    node_dir.mkdir()
    (node_dir / "package.json").write_text('{ "name": "test" }')
    generate_vendor_files(module_config, node_dir, renderer, base_context)
    vendor_dir_node = node_dir / vendor_root / module_name / version
    assert vendor_dir_node.exists()
    python_vendor_files = list(vendor_dir_node.rglob("*.py"))
    if vendor_is_cache:
        assert python_vendor_files, "Vendor cache should retain Python assets for Node projects"
    else:
        assert not python_vendor_files, "Python vendor files should be skipped for Node projects"

    # Re-run with a non-cache vendor root to ensure heuristics still filter entries
    filtered_config = copy.deepcopy(module_config)
    filtered_config["generation"]["vendor"]["root"] = "vendor"
    filtered_context = build_base_context(filtered_config)
    filtered_renderer = renderer

    filtered_py_dir = tmp_path / "filtered_pyhost"
    filtered_py_dir.mkdir()
    (filtered_py_dir / "pyproject.toml").write_text('[tool.poetry]\nname="test"\n')
    generate_vendor_files(filtered_config, filtered_py_dir, filtered_renderer, filtered_context)
    filtered_vendor_dir = (
        filtered_py_dir
        / Path(filtered_config["generation"]["vendor"]["root"])
        / filtered_context["rapidkit_vendor_module"]
        / filtered_context["rapidkit_vendor_version"]
    )
    assert filtered_vendor_dir.exists()
    assert not any(
        "nestjs" in str(p) for p in filtered_vendor_dir.glob("**/*")
    ), "NestJS files should be skipped for Python hosts when vendor root is not cache-backed"

    filtered_node_dir = tmp_path / "filtered_nodehost"
    filtered_node_dir.mkdir()
    (filtered_node_dir / "package.json").write_text('{ "name": "test" }')
    generate_vendor_files(filtered_config, filtered_node_dir, filtered_renderer, filtered_context)
    filtered_vendor_dir_node = (
        filtered_node_dir
        / Path(filtered_config["generation"]["vendor"]["root"])
        / filtered_context["rapidkit_vendor_module"]
        / filtered_context["rapidkit_vendor_version"]
    )
    assert filtered_vendor_dir_node.exists()
    assert not any(
        str(p).endswith(".py") for p in filtered_vendor_dir_node.rglob("*.py")
    ), "Python vendor files should be skipped for Node hosts when vendor root is not cache-backed"


def test_vendor_generation_honors_context_hint(tmp_path: Path) -> None:
    """When no pyproject/package.json present, respect 'target_framework' in context."""

    module_config = load_module_config()
    base_context = build_base_context(module_config)
    renderer = TemplateRenderer(MODULE_ROOT / "templates")

    tmp = tmp_path / "temp"
    tmp.mkdir()

    # No pyproject/package.json, but context hints at fastapi
    ctx_fastapi = {**base_context, "target_framework": "fastapi"}
    generate_vendor_files(module_config, tmp, renderer, ctx_fastapi)
    vendor_root_value = module_config["generation"]["vendor"].get("root", ".rapidkit/vendor")
    vendor_root = Path(vendor_root_value)
    normalized_root = str(vendor_root).replace("\\", "/").lstrip("./")
    vendor_is_cache = normalized_root.startswith("rapidkit/vendor")

    module_name = base_context["rapidkit_vendor_module"]
    version = base_context["rapidkit_vendor_version"]
    vendor_dir = tmp / vendor_root / module_name / version
    assert vendor_dir.exists()
    if vendor_is_cache:
        assert any(
            "nestjs" in str(p) for p in vendor_dir.glob("**/*")
        ), "Vendor cache should retain NestJS assets despite FastAPI hint"
    else:
        assert not any(
            "nestjs" in str(p) for p in vendor_dir.glob("**/*")
        ), "NestJS assets should be skipped for FastAPI hints when vendor root is not cache-backed"

    # Now hint node/nestjs
    tmp2 = tmp_path / "tempnode"
    tmp2.mkdir()
    ctx_node = {**base_context, "target_framework": "nestjs"}
    generate_vendor_files(module_config, tmp2, renderer, ctx_node)
    vendor_dir_node = tmp2 / vendor_root / module_name / version
    assert vendor_dir_node.exists()
    if vendor_is_cache:
        assert any(
            vendor_dir_node.rglob("*.py")
        ), "Vendor cache should retain Python assets despite NestJS hint"
    else:
        assert not any(
            vendor_dir_node.rglob("*.py")
        ), "Python assets should be skipped for NestJS hints when vendor root is not cache-backed"

    # Re-run with non-cache root to ensure hints still filter when requested
    filtered_config = copy.deepcopy(module_config)
    filtered_config["generation"]["vendor"]["root"] = "vendor"
    filtered_context = build_base_context(filtered_config)
    filtered_vendor_root = Path(filtered_config["generation"]["vendor"]["root"])

    tmp3 = tmp_path / "filtered-fastapi"
    tmp3.mkdir()
    ctx_fastapi_filtered = {**filtered_context, "target_framework": "fastapi"}
    generate_vendor_files(filtered_config, tmp3, renderer, ctx_fastapi_filtered)
    filtered_vendor_dir = (
        tmp3
        / filtered_vendor_root
        / filtered_context["rapidkit_vendor_module"]
        / filtered_context["rapidkit_vendor_version"]
    )
    assert filtered_vendor_dir.exists()
    assert not any(
        "nestjs" in str(p) for p in filtered_vendor_dir.glob("**/*")
    ), "FastAPI hints should filter NestJS assets when vendor root is not cache-backed"

    tmp4 = tmp_path / "filtered-nestjs"
    tmp4.mkdir()
    ctx_node_filtered = {**filtered_context, "target_framework": "nestjs"}
    generate_vendor_files(filtered_config, tmp4, renderer, ctx_node_filtered)
    filtered_vendor_dir_node = (
        tmp4
        / filtered_vendor_root
        / filtered_context["rapidkit_vendor_module"]
        / filtered_context["rapidkit_vendor_version"]
    )
    assert filtered_vendor_dir_node.exists()
    assert not any(
        filtered_vendor_dir_node.rglob("*.py")
    ), "NestJS hints should filter Python assets when vendor root is not cache-backed"
