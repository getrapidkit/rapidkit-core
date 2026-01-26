"""Health helper tests for Db Sqlite."""

from __future__ import annotations

from pathlib import Path


def test_perform_health_check_reports_pragmas(generated_db_sqlite_modules, tmp_path: Path) -> None:
    modules = generated_db_sqlite_modules
    runtime_module = modules.base
    health_module = modules.health

    runtime = runtime_module.DbSqlite(
        runtime_module.DbSqliteConfig(database_path=str(tmp_path / "health.db"))
    )
    runtime.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY)", commit=True)

    report = health_module.perform_health_check(runtime._manager)
    assert report.status == "ok"
    assert report.detail == "ok"
    assert "journal_mode" in report.pragmas

    runtime.close()
