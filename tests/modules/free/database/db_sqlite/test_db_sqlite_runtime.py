"""Runtime behaviour tests for the Db Sqlite vendor payload."""

from __future__ import annotations

from pathlib import Path

import pytest


def _build_runtime(modules, tmp_path: Path):
    runtime_module = modules.base
    config = runtime_module.DbSqliteConfig(database_path=str(tmp_path / "runtime.db"))
    return runtime_module.DbSqlite(config)


def test_runtime_executes_queries_successfully(generated_db_sqlite_modules, tmp_path: Path) -> None:
    runtime = _build_runtime(generated_db_sqlite_modules, tmp_path)

    runtime.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, name TEXT)", commit=True)
    runtime.executemany(
        "INSERT INTO items(name) VALUES (?)",
        [("alpha",), ("beta",)],
        commit=True,
    )

    result = runtime.execute("SELECT id, name FROM items ORDER BY id")
    assert result.columns == ("id", "name")
    assert [row["name"] for row in result.rows] == ["alpha", "beta"]
    runtime.close()


def test_runtime_transaction_rolls_back_on_error(
    generated_db_sqlite_modules, tmp_path: Path
) -> None:
    runtime = _build_runtime(generated_db_sqlite_modules, tmp_path)
    runtime.execute("CREATE TABLE tx(id INTEGER PRIMARY KEY, amount REAL)", commit=True)

    with pytest.raises(ValueError), runtime.transaction() as connection:
        connection.execute("INSERT INTO tx(amount) VALUES (?)", (10.5,))
        raise ValueError("trigger rollback")

    rows = runtime.execute("SELECT COUNT(*) AS total FROM tx")
    assert rows.rows[0]["total"] == 0
    runtime.close()


def test_runtime_health_check_reports_ok(generated_db_sqlite_modules, tmp_path: Path) -> None:
    runtime = _build_runtime(generated_db_sqlite_modules, tmp_path)
    runtime.execute("CREATE TABLE health(id INTEGER PRIMARY KEY)", commit=True)

    report = runtime.health_check()
    assert report.status == "ok"
    assert report.detail == "ok"
    assert "journal_mode" in report.pragmas
    runtime.close()
