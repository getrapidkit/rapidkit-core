"""Tests for core hook framework handlers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from core.hooks import framework_handlers

ROUTER_REFERENCE_COUNT = 2


@pytest.fixture()
def capture_printer(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    calls: dict[str, list[str]] = {"info": [], "success": [], "warning": []}

    def _store(key: str) -> Callable[[str], None]:
        def _inner(message: str) -> None:
            calls[key].append(message)

        return _inner

    monkeypatch.setattr(framework_handlers, "print_info", _store("info"))
    monkeypatch.setattr(framework_handlers, "print_success", _store("success"))
    monkeypatch.setattr(framework_handlers, "print_warning", _store("warning"))
    return calls


def test_handle_fastapi_router_missing_mount_path(
    tmp_path: Path, capture_printer: dict[str, list[str]]
) -> None:
    mount_path = tmp_path / "main.py"

    framework_handlers.handle_fastapi_router("api/routes.py", mount_path)

    assert capture_printer["warning"] == ["⚠️ Could not find main.py to auto-mount router."]
    assert not mount_path.exists()


def test_handle_fastapi_router_already_mounted(
    tmp_path: Path, capture_printer: dict[str, list[str]]
) -> None:
    mount_path = tmp_path / "main.py"
    mount_path.write_text(
        "from api.routes import router as routes_router\napp.include_router(routes_router)\n"
    )

    framework_handlers.handle_fastapi_router("api/routes.py", mount_path)

    assert not capture_printer["warning"]
    assert capture_printer["info"] == ["🔁 Router already mounted: routes"]
    assert mount_path.read_text().count("routes_router") == ROUTER_REFERENCE_COUNT


def test_handle_fastapi_router_appends_router(
    tmp_path: Path, capture_printer: dict[str, list[str]]
) -> None:
    mount_path = tmp_path / "application.py"
    mount_path.write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    framework_handlers.handle_fastapi_router("api/catalog.py", mount_path)

    content = mount_path.read_text()
    assert "from api.catalog import router as catalog_router" in content
    assert "app.include_router(catalog_router)" in content
    assert capture_printer["success"] == ["✅ Mounted router catalog in application.py"]


def test_handle_nestjs_module_missing_app_module(
    tmp_path: Path, capture_printer: dict[str, list[str]]
) -> None:
    framework_handlers.handle_nestjs_module(tmp_path, "users.module.ts", "project")

    assert capture_printer["warning"] == ["⚠️ app.module.ts not found."]


def test_handle_nestjs_module_already_registered(
    tmp_path: Path, capture_printer: dict[str, list[str]]
) -> None:
    app_module = tmp_path / "project/src/app.module.ts"
    app_module.parent.mkdir(parents=True, exist_ok=True)
    app_module.write_text(
        "import { UsersModule } from './users.module';\n\n@Module({\n  imports: [\n    UsersModule,\n  ],\n})\nexport class AppModule {}\n"
    )

    framework_handlers.handle_nestjs_module(tmp_path, "users.module.ts", "project")

    assert capture_printer["info"] == ["🔁 Module already imported: UsersModule"]
    assert capture_printer["success"] == []
    assert "UsersModule" in app_module.read_text()


def test_handle_nestjs_module_registers_new_module(
    tmp_path: Path, capture_printer: dict[str, list[str]]
) -> None:
    app_module = tmp_path / "project/src/app.module.ts"
    app_module.parent.mkdir(parents=True, exist_ok=True)
    app_module.write_text("@Module({\n  imports: [\n  ],\n})\nexport class AppModule {}\n")

    framework_handlers.handle_nestjs_module(tmp_path, "blog.module.ts", "project")

    content = app_module.read_text()
    assert "import { BlogModule } from './blog.module';" in content
    assert "    BlogModule," in content
    assert capture_printer["success"] == ["✅ Registered BlogModule in app.module.ts"]
