"""Integration smoke tests for Db Sqlite."""

from __future__ import annotations

import importlib
from pathlib import Path

from modules.free.database.db_sqlite.generate import DbSqliteModuleGenerator


def test_generate_module_importable() -> None:
    module = importlib.import_module("modules.free.database.db_sqlite.generate")
    assert module.MODULE_NAME == "db_sqlite"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")


def test_fastapi_variant_renders_successfully(
    db_sqlite_generator: DbSqliteModuleGenerator,
    tmp_path: Path,
) -> None:
    config = db_sqlite_generator.load_module_config()
    base_context = db_sqlite_generator.build_base_context(config)
    enriched = db_sqlite_generator.apply_base_context_overrides(base_context)
    renderer = db_sqlite_generator.create_renderer()

    db_sqlite_generator.generate_vendor_files(config, tmp_path, renderer, enriched)
    db_sqlite_generator.generate_variant_files("fastapi", tmp_path, renderer, enriched)

    assert (
        tmp_path / "src" / "modules" / "free" / "database" / "db_sqlite" / "db_sqlite.py"
    ).exists()
