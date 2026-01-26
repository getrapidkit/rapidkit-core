from __future__ import annotations

import sys
from importlib import import_module, util as import_util
from pathlib import Path

import pytest

from modules.free.tasks.celery.frameworks.fastapi import FastAPIPlugin
from modules.free.tasks.celery.frameworks.nestjs import NestJSPlugin
from modules.free.tasks.celery.overrides import CeleryOverrides


def test_overrides_are_noop_by_default() -> None:
    overrides = CeleryOverrides()

    sentinel = object()
    assert overrides.mutate_config(lambda: sentinel) is sentinel
    assert overrides.post_create(sentinel) is sentinel


@pytest.mark.parametrize(
    "plugin_cls, expected_language",
    [
        (FastAPIPlugin, "python"),
        (NestJSPlugin, "typescript"),
    ],
)
def test_framework_plugins_expose_metadata(plugin_cls: type, expected_language: str) -> None:
    plugin = plugin_cls()
    assert plugin.language == expected_language
    assert plugin.name in {"fastapi", "nestjs"}
    mappings = plugin.get_template_mappings()
    outputs = plugin.get_output_paths()
    assert mappings
    assert outputs


def test_framework_plugin_hooks_create_directories(tmp_path: Path) -> None:
    FastAPIPlugin().pre_generation_hook(tmp_path)
    assert (tmp_path / "src" / "modules" / "free" / "tasks" / "celery").exists()
    assert (tmp_path / "config" / "tasks").exists()
    assert (tmp_path / "tests" / "modules" / "integration" / "tasks").exists()

    NestJSPlugin().pre_generation_hook(tmp_path)
    assert (tmp_path / "src" / "modules" / "free" / "tasks" / "celery").exists()
    assert (tmp_path / "src" / "health").exists()
    assert (tmp_path / "tests" / "modules" / "integration" / "tasks").exists()


def test_runtime_exposes_celery_primitives(tmp_path: Path) -> None:
    generator = import_module("modules.free.tasks.celery.generate")
    TemplateRenderer = generator.TemplateRenderer  # type: ignore[attr-defined]

    renderer = TemplateRenderer()
    jinja_env = getattr(renderer, "_env", None)  # type: ignore[attr-defined]
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Celery templates")

    config = generator.load_module_config()
    context = generator.build_base_context(config)

    target_dir = tmp_path / "generated"
    target_dir.mkdir(parents=True, exist_ok=True)

    generator.generate_vendor_files(config, target_dir, renderer, context)

    runtime_rel = generator.infer_vendor_runtime_path(config)
    runtime_path = (
        target_dir
        / ".rapidkit"
        / "vendor"
        / context["rapidkit_vendor_module"]
        / str(context["rapidkit_vendor_version"])
        / runtime_rel
    )
    assert runtime_path.exists(), f"Missing generated vendor runtime at {runtime_path}"

    spec = import_util.spec_from_file_location("rapidkit_test_celery_runtime", runtime_path)
    if spec is None or spec.loader is None:
        pytest.fail("Unable to load generated celery runtime module")

    module = import_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert hasattr(module, "CeleryAppConfig")
    assert hasattr(module, "create_celery_app")
