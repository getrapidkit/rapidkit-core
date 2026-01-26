from __future__ import annotations

import sys
from importlib import import_module, util as import_util
from pathlib import Path
from unittest import mock

import pytest

from modules.free.tasks.celery import generate as celery_generate
from modules.free.tasks.celery.frameworks import (
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
)


def test_plugin_registry_lists_builtin_plugins() -> None:
    refresh_plugin_registry(auto_discover=False)
    available = list_available_plugins()
    assert available["fastapi"]
    assert available["nestjs"]

    plugin = get_plugin("fastapi")
    assert plugin.name == "fastapi"


def test_build_base_context_normalizes_defaults() -> None:
    config = celery_generate.load_module_config()
    ctx = celery_generate.build_base_context(config)

    assert ctx["module_name"] == "celery"
    assert ctx["module_class_name"] == "Celery"
    assert isinstance(ctx["celery_defaults"], dict)

    autodiscover = ctx["celery_defaults"].get("autodiscover")
    assert isinstance(autodiscover, list)

    settings_defaults = ctx["celery_settings_defaults"]
    assert isinstance(settings_defaults.get("imports"), list)
    assert isinstance(settings_defaults.get("include"), list)


def _render(target_dir: Path, framework: str) -> tuple[dict[str, object], dict[str, object]]:
    config = celery_generate.load_module_config()
    base_context = celery_generate.build_base_context(config)
    renderer = celery_generate.TemplateRenderer()

    celery_generate.generate_vendor_files(config, target_dir, renderer, base_context)
    celery_generate.generate_variant_files(config, framework, target_dir, renderer, base_context)

    return dict(config), dict(base_context)


def test_fastapi_generation_produces_expected_files(tmp_path: Path) -> None:
    config, _ctx = _render(tmp_path, "fastapi")

    vendor_root = tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_expected = {
        vendor_root / Path(entry["relative"])
        for entry in config["generation"]["vendor"].get("files", [])
    }
    assert vendor_expected, "Expected at least one vendor artefact"
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        assert artefact.read_text(encoding="utf-8").strip(), f"Vendor file {artefact} is empty"

    fastapi_expected = {
        tmp_path / Path(entry["output"])
        for entry in config["generation"]["variants"]["fastapi"].get("files", [])
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        assert artefact.read_text(encoding="utf-8").strip(), f"FastAPI file {artefact} is empty"


def test_nestjs_generation_produces_expected_files(tmp_path: Path) -> None:
    config, _ctx = _render(tmp_path, "nestjs")

    nest_expected = {
        tmp_path / Path(entry["output"])
        for entry in config["generation"]["variants"]["nestjs"].get("files", [])
    }
    assert nest_expected, "Expected at least one NestJS artefact"
    for artefact in nest_expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        assert artefact.read_text(encoding="utf-8").strip(), f"NestJS file {artefact} is empty"


def test_infer_vendor_paths_from_config() -> None:
    config = celery_generate.load_module_config()
    runtime_rel = celery_generate.infer_vendor_runtime_path(config)
    assert runtime_rel.endswith("src/modules/free/tasks/celery/celery.py")

    cfg_rel = celery_generate.infer_vendor_configuration_path(config)
    assert cfg_rel.endswith("nestjs/configuration.js")


@pytest.fixture(autouse=True)
def ensure_repo_root_on_path() -> None:
    """Guarantee the repository src package is importable."""
    repo_root = Path(__file__).resolve().parents[5]
    repo_str = str(repo_root)
    for name, module in list(sys.modules.items()):
        if not (name == "src" or name.startswith("src.")):
            continue
        module_file = getattr(module, "__file__", "") or ""
        try:
            module_path = Path(module_file).resolve()
        except (OSError, ValueError):
            module_path = None
        if module_path is None or repo_root not in module_path.parents and module_path != repo_root:
            sys.modules.pop(name, None)
    if repo_str in sys.path:
        sys.path.remove(repo_str)
    sys.path.insert(0, repo_str)
    sys.path[:] = [p for p in sys.path if "pytest-of" not in p]


def load_runtime_module():
    repo_root = Path(__file__).resolve().parents[5]
    try:
        return import_module("runtime.tasks.celery")
    except (ModuleNotFoundError, ImportError):
        module_path = repo_root / "src" / "runtime" / "tasks" / "celery.py"
        spec = import_util.spec_from_file_location("runtime.tasks.celery", module_path)
        if spec is None or spec.loader is None:
            pytest.fail("Unable to load celery runtime module")
        module = import_util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


TWO_MINUTES_SECONDS = 120


def test_celery_generator_entrypoint() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        module = import_module("modules.free.tasks.celery.generate")
    except (ModuleNotFoundError, ImportError):
        module_path = repo_root / "src/modules/free/tasks/celery/generate.py"
        spec = import_util.spec_from_file_location(
            "modules.free.tasks.celery.generate", module_path
        )
        if spec is None or spec.loader is None:
            pytest.fail("Unable to load celery generator module")
        module = import_util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

    assert module


def test_create_celery_app_builds_configuration() -> None:
    runtime = load_runtime_module()
    config = runtime.CeleryAppConfig.from_mapping(
        {
            "name": "test",
            "settings": {
                "broker_url": "redis://localhost:6379/0",
                "imports": ["tests.fake"],
                "beat_schedule": {
                    "ping": {
                        "task": "celery.ping",
                        "schedule": {"type": "interval", "every": 60, "period": "seconds"},
                    }
                },
            },
        }
    )
    with mock.patch.object(runtime, "Celery") as celery_cls:
        app_instance = mock.Mock()
        celery_cls.return_value = app_instance
        runtime.create_celery_app(config)
        celery_cls.assert_called_once()
        assert "beat_schedule" in app_instance.conf.update.call_args.kwargs


def test_get_celery_app_caches_default_instance() -> None:
    runtime = load_runtime_module()
    runtime._get_default_celery_app.cache_clear()
    with mock.patch.object(runtime, "create_celery_app") as create_app:
        create_app.return_value = mock.Mock()
        runtime.get_celery_app()
        runtime.get_celery_app()
        assert create_app.call_count == 1
    runtime._get_default_celery_app.cache_clear()


def test_get_celery_app_supports_custom_config_without_cache() -> None:
    runtime = load_runtime_module()
    config = runtime.CeleryAppConfig.from_mapping({"name": "custom"})
    with mock.patch.object(runtime, "create_celery_app") as create_app:
        runtime.get_celery_app(config)
        create_app.assert_called_once_with(config)


def test_celery_schedule_interval_without_schedule_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = load_runtime_module()
    monkeypatch.setattr(runtime, "celery_schedule", None)
    schedule = runtime.CelerySchedule.from_mapping(
        {
            "task": "tasks.ping",
            "schedule": {"type": "interval", "every": 5, "period": "seconds"},
        }
    )
    assert schedule.schedule == {"every": 5, "period": "seconds"}


def test_celery_schedule_interval_invalid_period(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_module()
    monkeypatch.setattr(runtime, "celery_schedule", lambda run_every: run_every)
    payload = {
        "task": "tasks.ping",
        "schedule": {"type": "interval", "every": 1, "period": "weeks"},
    }
    with pytest.raises(ValueError):
        runtime.CelerySchedule.from_mapping(payload)


def test_coerce_schedule_crontab_requires_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_module()
    monkeypatch.setattr(runtime, "crontab", None)
    with pytest.raises(runtime.CeleryRuntimeError):
        runtime._coerce_schedule({"type": "crontab", "minute": "0"})


def test_coerce_schedule_crontab_invokes_crontab(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_module()
    captured: dict[str, str] = {}

    def fake_crontab(**kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(runtime, "crontab", fake_crontab)
    schedule = runtime._coerce_schedule(
        {
            "type": "crontab",
            "minute": "15",
            "hour": "*",
            "day_of_week": "mon-fri",
        }
    )
    assert schedule["minute"] == "15"
    assert captured["day_of_week"] == "mon-fri"


def test_task_registry_requires_celery(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_module()
    monkeypatch.setattr(runtime, "Celery", None)
    registry = runtime.CeleryTaskRegistry(mock.Mock())
    with pytest.raises(runtime.CeleryRuntimeError):
        registry.task()


def test_load_config_from_env_parses_sequences() -> None:
    runtime = load_runtime_module()
    env = {
        "RAPIDKIT_CELERY_BROKER_URL": "redis://example:6379/0",
        "RAPIDKIT_CELERY_RESULT_BACKEND": "redis://result:6379/1",
        "RAPIDKIT_CELERY_TIMEZONE": "Europe/Paris",
        "RAPIDKIT_CELERY_ENABLE_UTC": "false",
        "RAPIDKIT_CELERY_DEFAULT_QUEUE": "critical",
        "RAPIDKIT_CELERY_IMPORTS": "pkg.tasks, pkg.jobs ",
        "RAPIDKIT_CELERY_INCLUDE": "pkg.extra",
        "RAPIDKIT_CELERY_AUTODISCOVER": "pkg.autodiscover",
        "RAPIDKIT_CELERY_APP_NAME": "custom",
    }
    config = runtime.load_config_from_env(env=env)
    assert config.name == "custom"
    assert config.settings.broker_url == "redis://example:6379/0"
    assert config.settings.result_backend == "redis://result:6379/1"
    assert config.settings.timezone == "Europe/Paris"
    assert config.settings.enable_utc is False
    assert config.settings.task_default_queue == "critical"
    assert config.settings.imports == ("pkg.tasks", "pkg.jobs")
    assert config.settings.include == ("pkg.extra",)
    assert config.autodiscover == ("pkg.autodiscover",)


def test_celery_schedule_requires_task_field() -> None:
    runtime = load_runtime_module()
    with pytest.raises(ValueError):
        runtime.CelerySchedule.from_mapping(
            {"schedule": {"type": "interval", "every": 1, "period": "seconds"}}
        )


def test_celery_schedule_requires_schedule_payload() -> None:
    runtime = load_runtime_module()
    with pytest.raises(ValueError):
        runtime.CelerySchedule.from_mapping({"task": "tasks.ping"})


def test_celery_settings_from_mapping_parses_beat_schedule(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_module()

    class DummySchedule:
        calls: list = []

        def __call__(self, *, run_every):
            self.calls.append(run_every)
            return {"run_every": run_every}

    dummy_schedule = DummySchedule()
    monkeypatch.setattr(runtime, "celery_schedule", dummy_schedule)
    settings = runtime.CelerySettings.from_mapping(
        {
            "beat_schedule": {
                "ping": {
                    "task": "tasks.ping",
                    "schedule": {"type": "interval", "every": 2, "period": "minutes"},
                }
            }
        }
    )
    assert "ping" in settings.beat_schedule
    assert dummy_schedule.calls and dummy_schedule.calls[0].seconds == TWO_MINUTES_SECONDS


def test_write_file_creates_parent_directories(tmp_path: Path) -> None:
    runtime = import_module("modules.free.tasks.celery.generate")
    target = tmp_path / "nested" / "file.txt"
    runtime.write_file(target, "hello")
    assert target.exists()
    assert target.read_text() == "hello"


def test_format_missing_dependencies_outputs_lines() -> None:
    runtime = import_module("modules.free.tasks.celery.generate")
    output = runtime._format_missing_dependencies({"jinja2": "Install via pip"})
    assert "jinja2" in output
    assert output.startswith("Missing optional dependencies")


def test_format_missing_dependencies_empty() -> None:
    runtime = import_module("modules.free.tasks.celery.generate")
    assert runtime._format_missing_dependencies({}) == ""


def test_infer_vendor_runtime_path_uses_module_yaml() -> None:
    generator = import_module("modules.free.tasks.celery.generate")
    config = generator.load_module_config()
    path = generator.infer_vendor_runtime_path(config)
    assert path.endswith("src/modules/free/tasks/celery/celery.py")


def test_generate_vendor_files_renders_templates(tmp_path: Path) -> None:
    generator = import_module("modules.free.tasks.celery.generate")
    config = generator.load_module_config()
    context = generator.build_base_context(config)

    class DummyRenderer:
        def render(self, template_path: Path, context: dict) -> str:
            return "// rendered"

    renderer = DummyRenderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    expected = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / context["rapidkit_vendor_module"]
        / context["rapidkit_vendor_version"]
        / generator.infer_vendor_runtime_path(config)
    )
    assert expected.exists()
    assert expected.read_text() == "// rendered"


def test_generate_variant_files_writes_outputs(tmp_path: Path) -> None:
    generator = import_module("modules.free.tasks.celery.generate")
    config = generator.load_module_config()
    context = generator.build_base_context(config)

    class DummyRenderer:
        def render(self, template_path: Path, context: dict) -> str:
            return "content"

    renderer = DummyRenderer()
    generator.generate_variant_files(config, "fastapi", tmp_path, renderer, context)

    variant_cfg = config["generation"]["variants"]["fastapi"]
    root = Path(variant_cfg.get("root", "."))
    expected_outputs = [root / Path(entry["output"]) for entry in variant_cfg["files"]]

    for relative in expected_outputs:
        output_path = (tmp_path / relative).resolve()
        assert output_path.exists(), f"Expected variant artefact missing: {output_path}"
        assert output_path.read_text(encoding="utf-8") == "content"


def test_generate_variant_files_unknown_variant(tmp_path: Path) -> None:
    generator = import_module("modules.free.tasks.celery.generate")
    config = generator.load_module_config()
    context = generator.build_base_context(config)

    class DummyRenderer:
        def render(self, template_path: Path, context: dict) -> str:
            return "content"

    renderer = DummyRenderer()
    with pytest.raises(generator.GeneratorError):
        generator.generate_variant_files(config, "unknown", tmp_path, renderer, context)


@pytest.mark.parametrize("variant", ["fastapi", "nestjs"], ids=["fastapi", "nestjs"])
def test_generator_emits_expected_artifacts(tmp_path: Path, variant: str) -> None:
    generator = import_module("modules.free.tasks.celery.generate")
    TemplateRenderer = generator.TemplateRenderer  # type: ignore[attr-defined]

    renderer = TemplateRenderer()
    jinja_env = getattr(renderer, "_env", None)  # type: ignore[attr-defined]
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Celery templates")

    config = generator.load_module_config()
    context = generator.build_base_context(config)

    target_dir = tmp_path / "generated"
    target_dir.mkdir()

    generator.generate_vendor_files(config, target_dir, renderer, context)
    generator.generate_variant_files(config, variant, target_dir, renderer, context)

    vendor_cfg = config["generation"]["vendor"]
    vendor_root = Path(vendor_cfg.get("root", ".rapidkit/vendor"))
    module_name = context["rapidkit_vendor_module"]
    version = str(context["rapidkit_vendor_version"])

    expected_vendor_files = {
        target_dir / vendor_root / module_name / version / Path(entry["relative"])
        for entry in vendor_cfg.get("files", [])
    }

    for vendor_path in expected_vendor_files:
        assert vendor_path.exists(), f"Missing vendor artefact {vendor_path}"
        contents = vendor_path.read_text(encoding="utf-8").strip()
        assert contents, f"Vendor artefact {vendor_path} is empty"

        # disambiguate between runtime and canonical health vendor artefacts
        if vendor_path.as_posix().endswith("src/modules/free/tasks/celery/celery.py"):
            for symbol in (
                "class CeleryAppConfig",
                "class CelerySettings",
                "def create_celery_app",
                "def get_celery_metadata",
                "MODULE_FEATURES",
            ):
                assert symbol in contents
        elif vendor_path.as_posix().endswith("src/health/celery.py"):
            assert "build_health_snapshot" in contents
            assert "render_health_snapshot" in contents
            assert "DEFAULT_FEATURES" in contents
        elif vendor_path.name == "celery_types.py":
            assert "class CeleryHealthSnapshot" in contents
            assert "class CeleryBeatEntrySnapshot" in contents
        elif vendor_path.suffix == ".js":
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    if variant == "fastapi":
        runtime_path = target_dir / "src" / "modules" / "free" / "tasks" / "celery" / "celery.py"
        routes_path = (
            target_dir / "src" / "modules" / "free" / "tasks" / "celery" / "celery_routes.py"
        )
        config_path = target_dir / "config" / "tasks" / "celery.yaml"
        integration_test_path = (
            target_dir
            / "tests"
            / "modules"
            / "integration"
            / "tasks"
            / "test_celery_integration.py"
        )

        for artefact in (
            runtime_path,
            routes_path,
            config_path,
            integration_test_path,
        ):
            assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
            contents = artefact.read_text(encoding="utf-8").strip()
            assert contents, f"FastAPI artefact {artefact} is empty"

        runtime_src = runtime_path.read_text(encoding="utf-8")
        assert "create_router" in runtime_src
        assert "register_celery_lifespan" in runtime_src
        assert "apply_module_overrides" in runtime_src
        assert "refresh_vendor_module" in runtime_src

        routes_src = routes_path.read_text(encoding="utf-8")
        assert "register_celery_routes" in routes_src
        assert "get_celery_metadata" in routes_src
        assert "MODULE_FEATURES" in routes_src

        config_src = config_path.read_text(encoding="utf-8")
        assert "celery:" in config_src
        assert "broker_url" in config_src
        assert "autodiscover" in config_src

        fastapi_test_src = integration_test_path.read_text(encoding="utf-8")
        assert (
            "test_celery_runtime_importable" in fastapi_test_src
            or "import_module" in fastapi_test_src
        )

    else:
        service_path = (
            target_dir / "src" / "modules" / "free" / "tasks" / "celery" / "celery.service.ts"
        )
        controller_path = (
            target_dir / "src" / "modules" / "free" / "tasks" / "celery" / "celery.controller.ts"
        )
        module_path = (
            target_dir / "src" / "modules" / "free" / "tasks" / "celery" / "celery.module.ts"
        )
        configuration_path = (
            target_dir / "src" / "modules" / "free" / "tasks" / "celery" / "celery.configuration.ts"
        )
        health_controller_path = target_dir / "src" / "health" / "celery-health.controller.ts"
        health_module_path = target_dir / "src" / "health" / "celery-health.module.ts"
        integration_spec_path = (
            target_dir
            / "tests"
            / "modules"
            / "integration"
            / "tasks"
            / "celery.integration.spec.ts"
        )

        for artefact in (
            service_path,
            controller_path,
            module_path,
            configuration_path,
            health_controller_path,
            health_module_path,
            integration_spec_path,
        ):
            assert artefact.exists(), f"Expected NestJS artefact {artefact}"
            contents = artefact.read_text(encoding="utf-8").strip()
            assert contents, f"NestJS artefact {artefact} is empty"

        service_src = service_path.read_text(encoding="utf-8")
        assert "class CeleryService" in service_src
        assert "async sendTask" in service_src
        assert "createCeleryHealthCheck" in service_src
        assert "CELERY_FEATURES" in service_src
        assert "autodiscover" in service_src

        controller_src = controller_path.read_text(encoding="utf-8")
        assert (
            "@Controller('tasks/celery')" in controller_src
            or '@Controller("tasks/celery")' in controller_src
        )
        assert "@Get('metadata')" in controller_src or '@Get("metadata")' in controller_src
        assert "@Get('features')" in controller_src or '@Get("features")' in controller_src
        assert "@Get('health')" in controller_src or '@Get("health")' in controller_src

        module_src = module_path.read_text(encoding="utf-8")
        assert "@Module" in module_src
        assert "CeleryService" in module_src
        assert "CeleryModule" in module_src
        assert "ConfigModule.forFeature" in module_src

        configuration_src = configuration_path.read_text(encoding="utf-8")
        assert "registerAs" in configuration_src
        assert "CELERY_CONFIGURATION_NAMESPACE" in configuration_src

        health_controller_src = health_controller_path.read_text(encoding="utf-8")
        assert "Celery health check failed" in health_controller_src
        assert (
            "@Get('celery')" in health_controller_src or '@Get("celery")' in health_controller_src
        )

        health_module_src = health_module_path.read_text(encoding="utf-8")
        assert "CeleryHealthModule" in health_module_src

        integration_spec_src = integration_spec_path.read_text(encoding="utf-8")
        assert "describe('CeleryModule" in integration_spec_src
