"""Vendor health helper tests for Db Postgres."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Iterator

import pytest

from modules.free.database.db_postgres.generate import DbPostgresModuleGenerator


@pytest.fixture()
def rendered_db_postgres_health(tmp_path) -> Iterator[ModuleType]:
    generator = DbPostgresModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    package_root = tmp_path / "rendered_db_postgres"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")

    types_code = renderer.render_template("templates/base/db_postgres_types.py.j2", context)
    (package_root / "db_postgres_types.py").write_text(types_code, encoding="utf-8")

    health_code = renderer.render_template("templates/base/db_postgres_health.py.j2", context)
    (package_root / "db_postgres_health.py").write_text(health_code, encoding="utf-8")

    sys_path_entry = str(tmp_path)
    sys.path.insert(0, sys_path_entry)
    try:
        module = importlib.import_module("rendered_db_postgres.db_postgres_health")
        yield module
    finally:
        if sys_path_entry in sys.path:
            sys.path.remove(sys_path_entry)
        for name in list(sys.modules):
            if name == "rendered_db_postgres" or name.startswith("rendered_db_postgres."):
                sys.modules.pop(name, None)


def test_health_metadata_masks_password(rendered_db_postgres_health) -> None:
    module = rendered_db_postgres_health
    metadata = module.build_postgres_metadata(
        database_url="postgresql://user:secret@localhost:5432/app",
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        test_database_url="postgresql://user:secret@localhost:5432/app_test",
    )
    assert metadata["database_url"].startswith("postgresql://user:***@")
    assert metadata["test_database_url"].startswith("postgresql://user:***@")
    assert metadata["pool"]["size"] == 10


def test_render_health_snapshot(rendered_db_postgres_health) -> None:
    module = rendered_db_postgres_health
    snapshot = module.build_health_snapshot(
        "ok",
        database_url="postgresql://user:pass@db:5432/app",
        pool_size=5,
        max_overflow=5,
        pool_timeout=15,
        pool_recycle=120,
    )
    payload = module.render_health_snapshot(snapshot)
    assert payload["status"] == "ok"
    assert payload["module"] == "db_postgres"
    assert "checked_at" in payload
