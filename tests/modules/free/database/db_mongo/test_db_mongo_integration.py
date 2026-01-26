"""Integration smoke tests for Db Mongo."""

from __future__ import annotations

import importlib


def test_generate_module_importable() -> None:
    module = importlib.import_module("modules.free.database.db_mongo.generate")
    assert module.MODULE_NAME == "db_mongo"


def test_template_renderer_accessible(module_generate) -> None:
    assert hasattr(module_generate, "TemplateRenderer")
