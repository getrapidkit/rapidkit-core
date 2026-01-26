"""Ensure logging health template renders and exposes register function."""

import importlib.util
import logging
import sys
import types
from pathlib import Path
from types import ModuleType
from uuid import uuid4

from modules.free.essentials.logging import generate


def _render_health(tmp_path: Path) -> ModuleType:
    renderer = generate.TemplateRenderer(generate.MODULE_ROOT / "templates")
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    template = generate.MODULE_ROOT / "templates" / "base" / "logging_health.py.j2"
    out_file = tmp_path / "logging_health.py"
    out_file.write_text(renderer.render(template, context), encoding="utf-8")

    runtime_dir = tmp_path / "src" / "modules" / "free" / "essentials" / "logging"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    for pkg in [
        runtime_dir.parent.parent.parent,  # src/modules
        runtime_dir.parent.parent,  # src/modules/free
        runtime_dir.parent,  # src/modules/free/essentials
        runtime_dir,  # src/modules/free/essentials/logging
    ]:
        init_file = pkg / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
    src_init = tmp_path / "src" / "__init__.py"
    if not src_init.exists():
        src_init.write_text("", encoding="utf-8")
    runtime_file = runtime_dir / "logging.py"
    runtime_file.write_text(
        """
def get_logger(name):
    import logging
    return logging.getLogger(name)


def get_logging_metadata():
    return {}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    src_path = tmp_path / "src"
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)

    # Prevent any pre-existing src namespace from shadowing the stub runtime.
    module_names = [
        "src",
        "src.modules",
        "modules.free",
        "modules.free.essentials",
        "modules.free.essentials.logging",
    ]
    original_modules = {name: sys.modules.get(name) for name in module_names}
    for name in module_names:
        sys.modules.pop(name, None)

    # Provide a lightweight stub for core.logging used by the rendered module.
    original_core = sys.modules.get("core")
    original_core_logging = sys.modules.get("core.logging")
    core_pkg = types.ModuleType("core")
    logging_mod = types.ModuleType("core.logging")

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def get_logging_metadata() -> dict:
        return {}

    logging_mod.get_logger = get_logger
    logging_mod.get_logging_metadata = get_logging_metadata
    sys.modules["core"] = core_pkg
    sys.modules["core.logging"] = logging_mod

    module_name = f"logging_health_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, out_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import rendered logging health module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Restore any prior src modules to avoid leaking stubs into other tests.
    for name, original in original_modules.items():
        if original is not None:
            sys.modules[name] = original
        else:
            sys.modules.pop(name, None)

    # Restore any prior core modules to avoid leaking stubs into other tests.
    if original_core is not None:
        sys.modules["core"] = original_core
    else:
        sys.modules.pop("core", None)
    if original_core_logging is not None:
        sys.modules["core.logging"] = original_core_logging
    else:
        sys.modules.pop("core.logging", None)
    if src_path_str in sys.path:
        sys.path.remove(src_path_str)
    return module


def test_health_exports(tmp_path: Path) -> None:
    module = _render_health(tmp_path)
    assert hasattr(module, "register_logging_health")
    assert hasattr(module, "router")
