"""Exercise runtime helpers for the PostgreSQL database module."""

from __future__ import annotations

import importlib


def test_runtime_metadata_exposed() -> None:
    module = importlib.import_module("modules.free.database.db_postgres")

    info = module.get_module_info()
    assert info["name"] == "db_postgres"
    assert info["status"] in ("active", "stable")
    assert "async_engine" in info["capabilities"]

    runtime = module.DatabasePostgres()
    assert runtime.get_version() == module.__version__
    assert runtime.get_info() == info
