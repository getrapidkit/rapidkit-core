from __future__ import annotations

from pathlib import Path

from modules.shared.utils.health import ensure_health_package


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_ensure_health_package_enriches_project_scaffold(tmp_path: Path) -> None:
    project_root = tmp_path
    main_py = project_root / "src" / "main.py"
    main_py_content = (
        '"""Example app."""\n\n'
        "from __future__ import annotations\n\n"
        "from fastapi import FastAPI\n"
        "from fastapi.middleware.cors import CORSMiddleware\n\n"
        "# <<<inject:imports>>>\n\n"
        "from .routing import api_router\n\n"
        'app = FastAPI(title="Example", version="0.1.0")\n\n'
        "app.add_middleware(\n"
        "    CORSMiddleware,\n"
        "    allow_origins=['*'],\n"
        "    allow_credentials=True,\n"
        "    allow_methods=['*'],\n"
        "    allow_headers=['*'],\n"
        ")\n\n"
        'app.include_router(api_router, prefix="/api")\n'
    )
    _write_file(main_py, main_py_content)

    health_py = project_root / "src" / "routing" / "health.py"
    health_py_content = (
        '"""Health endpoints."""\n\n'
        "from __future__ import annotations\n\n"
        "from fastapi import APIRouter\n\n"
        "router = APIRouter()\n\n"
        '@router.get("/", summary="Health check")\n'
        "async def heartbeat() -> dict[str, str]:\n"
        '    return {"status": "ok"}\n'
    )
    _write_file(health_py, health_py_content)

    ensure_health_package(project_root)

    updated_main = main_py.read_text(encoding="utf-8")
    assert "register_health_routes" in updated_main
    assert "_register_health_routes(app)" in updated_main

    updated_health = health_py.read_text(encoding="utf-8")
    assert ("_list_health_routes" in updated_health) or (
        "_list_registered_health_routes" in updated_health
    )
    assert "/modules" in updated_health

    ensure_health_package(project_root)
    assert updated_main == main_py.read_text(encoding="utf-8")
    assert updated_health == health_py.read_text(encoding="utf-8")


def test_ensure_health_package_accumulates_extra_registrars(tmp_path: Path) -> None:
    project_root = tmp_path

    ensure_health_package(
        project_root,
        extra_imports=[("vendor.alpha.health", "register_alpha_health")],
    )
    ensure_health_package(
        project_root,
        extra_imports=[("vendor.beta.health", "register_beta_health")],
    )

    init_path = project_root / "src/health/__init__.py"
    contents = init_path.read_text(encoding="utf-8")

    assert '"vendor.alpha.health", "register_alpha_health"' in contents
    assert '"vendor.beta.health", "register_beta_health"' in contents
