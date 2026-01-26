"""Render deployment health helper and ensure it exposes expected API."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from uuid import uuid4

from modules.free.essentials.deployment import generate


def _render_health(tmp_path: Path) -> ModuleType:
    renderer = generate.TemplateRenderer(generate.MODULE_ROOT / "templates")
    cfg = generate.load_module_config()
    ctx = generate.build_base_context(cfg)
    template = generate.MODULE_ROOT / "templates" / "base" / "deployment_health.py.j2"
    out_file = tmp_path / "deployment_health.py"
    out_file.write_text(renderer.render(template, ctx), encoding="utf-8")
    module_name = f"deployment_health_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, out_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import rendered deployment health module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_health_exports(tmp_path: Path) -> None:
    module = _render_health(tmp_path)
    assert hasattr(module, "build_health_payload")
    assert hasattr(module, "register_deployment_health")
