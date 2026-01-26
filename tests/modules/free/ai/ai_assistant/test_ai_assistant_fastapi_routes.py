from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.free.ai.ai_assistant import generate
from modules.shared.generator import TemplateRenderer


def _load_module(module_name: str, module_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def _materialize_runtime(tmp_path: Path, renderer: TemplateRenderer, context: dict) -> Path:
    package_root = tmp_path / f"runtime_{uuid4().hex}"
    runtime_root = package_root / "src" / "modules" / "free" / "ai" / "ai_assistant"
    health_root = package_root / "src" / "health"
    runtime_root.mkdir(parents=True)
    health_root.mkdir(parents=True)

    for pkg in [
        package_root / "src",
        package_root / "src" / "health",
        package_root / "src" / "modules",
        package_root / "src" / "modules" / "free",
        package_root / "src" / "modules" / "free" / "ai",
        runtime_root,
    ]:
        (pkg / "__init__.py").write_text("", encoding="utf-8")

    (runtime_root / "ai_assistant.py").write_text(
        renderer.render_template("base/ai_assistant.py.j2", context),
        encoding="utf-8",
    )
    (runtime_root / "ai_assistant_types.py").write_text(
        renderer.render_template("base/ai_assistant_types.py.j2", context),
        encoding="utf-8",
    )
    (health_root / "ai_assistant.py").write_text(
        renderer.render_template("base/ai_assistant_health.py.j2", context),
        encoding="utf-8",
    )
    return package_root


def _load_router_module(tmp_path: Path):
    renderer = TemplateRenderer(generate.MODULE_ROOT / "templates")
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    package_root = _materialize_runtime(tmp_path, renderer, context)

    # The generated router template imports runtime symbols from `modules.*`.
    # Ensure the materialized `src/` package is importable.
    package_root_str = str(package_root)
    if package_root_str not in sys.path:
        sys.path.insert(0, package_root_str)

    # `src` is also a real package in this repository, and the full test suite
    # may have already imported it from the repo root. Evict it so imports
    # resolve against the materialized runtime under `package_root`.
    # IMPORTANT: restore after the test to avoid cross-test import corruption.
    purge_names = (
        "src.modules.free.ai.ai_assistant.ai_assistant",
        "src.modules.free.ai.ai_assistant.ai_assistant_types",
        "src.health.ai_assistant",
        "src.health",
        "src.modules.free.ai.ai_assistant",
        "src.modules.free.ai",
        "src.modules.free",
        "src.modules",
        "src",
    )
    removed = {}
    for name in purge_names:
        existing = sys.modules.pop(name, None)
        if existing is not None:
            removed[name] = existing

    module_path = tmp_path / f"ai_assistant_routes_{uuid4().hex}.py"
    module_path.write_text(
        renderer.render_template("variants/fastapi/ai_assistant_routes.py.j2", context),
        encoding="utf-8",
    )

    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_path.stem] = module
    spec.loader.exec_module(module)
    return module, module_path.stem, package_root, removed


def _cleanup_modules(package_root: Path, handle: str, removed: dict[str, object]) -> None:
    sys.modules.pop(handle, None)

    for name in (
        "src.modules.free.ai.ai_assistant.ai_assistant",
        "src.modules.free.ai.ai_assistant.ai_assistant_types",
        "src.health.ai_assistant",
        "src.health",
        "src.modules.free.ai.ai_assistant",
        "src.modules.free.ai",
        "src.modules.free",
        "src.modules",
        "src",
    ):
        sys.modules.pop(name, None)

    # Restore any previously-imported modules we evicted.
    for name, module in removed.items():
        sys.modules[name] = module

    package_root_str = str(package_root)
    if package_root_str in sys.path:
        sys.path.remove(package_root_str)


def test_fastapi_router_handles_completion(tmp_path: Path) -> None:
    module, handle, package_root, removed = _load_router_module(tmp_path)
    app = FastAPI()
    module.register_ai_assistant(app)
    client = TestClient(app)

    response = client.post("/ai/assistant/completions", json={"prompt": "hello"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"]
    assert payload["content"]

    _cleanup_modules(package_root, handle, removed)


def test_fastapi_router_reports_health(tmp_path: Path) -> None:
    module, handle, package_root, removed = _load_router_module(tmp_path)
    app = FastAPI()
    module.register_ai_assistant(app)
    client = TestClient(app)

    response = client.get("/ai/assistant/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime"]["module"] == "ai_assistant"

    _cleanup_modules(package_root, handle, removed)
