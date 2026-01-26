"""Error handling tests for Db Sqlite runtime."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_invalid_sql_raises_custom_exception(generated_db_sqlite_modules, tmp_path: Path) -> None:
    modules = generated_db_sqlite_modules
    runtime_module = modules.base
    runtime = runtime_module.DbSqlite(
        runtime_module.DbSqliteConfig(database_path=str(tmp_path / "errors.db"))
    )
    runtime.execute("CREATE TABLE demo(id INTEGER PRIMARY KEY)", commit=True)

    with pytest.raises(runtime_module.DbSqliteExecutionError):
        runtime.execute("INSERRT INTO demo(id) VALUES (1)", commit=True)

    runtime.close()
