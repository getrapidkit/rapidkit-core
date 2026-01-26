"""Ensure middleware health template renders and exposes register function."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest

from modules.free.essentials.middleware import generate


def _render_health(tmp_path: Path) -> ModuleType:
    renderer = generate.TemplateRenderer(generate.MODULE_ROOT / "templates")
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    template = generate.MODULE_ROOT / "templates" / "base" / "middleware_health.py.j2"
    out_file = tmp_path / "middleware_health.py"
    out_file.write_text(renderer.render(template, context), encoding="utf-8")

    module_name = f"middleware_health_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, out_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import rendered middleware health module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_health_exports(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    module = _render_health(tmp_path)
    assert hasattr(module, "register_middleware_health")
    assert hasattr(module, "router")
