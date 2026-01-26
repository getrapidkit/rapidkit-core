"""Override scaffolding tests for Db Sqlite."""

from __future__ import annotations

from pathlib import Path

from modules.free.database.db_sqlite import overrides
from modules.free.database.db_sqlite.overrides import DbSqliteOverrides


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class DbSqliteOverrides" in overrides_source


def test_environment_overrides_mutate_context(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_PATH", "/tmp/rapidkit.sqlite3")
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE", "8")

    overrides = DbSqliteOverrides()
    context = {
        "default_database_path": "./app.db",
        "default_pool": {"max_size": 4, "recycle_seconds": 600},
    }
    mutated = overrides.apply_base_context(context)

    assert mutated["default_database_path"] == "/tmp/rapidkit.sqlite3"
    assert mutated["default_pool"]["max_size"] == 8


def test_parsers_handle_truthy_and_falsy(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING", "yes")
    assert overrides._parse_bool("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING") is True

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING", "0")
    assert overrides._parse_bool("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING") is False

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING", "not-a-bool")
    assert overrides._parse_bool("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING") is None


def test_parsers_handle_int_float_and_mapping(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE", "12")
    assert overrides._parse_int("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE") == 12

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE", "oops")
    assert overrides._parse_int("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE") is None

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS", "3.5")
    assert overrides._parse_float("RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS") == 3.5

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS", "nope")
    assert overrides._parse_float("RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS") is None

    monkeypatch.setenv(
        "RAPIDKIT_DB_SQLITE_PRAGMAS", '{"journal_mode": "wal", "busy_timeout": 5000}'
    )
    assert overrides._parse_mapping("RAPIDKIT_DB_SQLITE_PRAGMAS") == {
        "journal_mode": "wal",
        "busy_timeout": "5000",
    }

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_PRAGMAS", "cache_size=1000,synchronous=off")
    assert overrides._parse_mapping("RAPIDKIT_DB_SQLITE_PRAGMAS") == {
        "cache_size": "1000",
        "synchronous": "off",
    }

    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_PRAGMAS", "not=a-mapping;missing-equals")
    assert overrides._parse_mapping("RAPIDKIT_DB_SQLITE_PRAGMAS") == {
        "not": "a-mapping;missing-equals",
    }


def test_apply_base_context_clamps_and_merges(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE", "-2")
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_POOL_RECYCLE_SECONDS", "-10")
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS", "-1.5")
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_PRAGMAS", "journal_mode=wal")
    monkeypatch.setenv("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING", "0")

    overrides_obj = DbSqliteOverrides()
    base_context = {
        "default_pool": {"max_size": 4, "recycle_seconds": 600},
        "default_timeout_seconds": 30.0,
        "default_pragmas": {"busy_timeout": "3000"},
        "default_create_if_missing": True,
    }

    mutated = overrides_obj.apply_base_context(base_context)

    assert mutated["default_pool"] == {"max_size": 1, "recycle_seconds": 0}
    assert mutated["default_timeout_seconds"] == 0.0
    assert mutated["default_pragmas"] == {"busy_timeout": "3000", "journal_mode": "wal"}
    assert mutated["default_create_if_missing"] is False


def test_apply_base_context_no_env_returns_original(monkeypatch) -> None:
    monkeypatch.delenv("RAPIDKIT_DB_SQLITE_PATH", raising=False)
    monkeypatch.delenv("RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE", raising=False)
    monkeypatch.delenv("RAPIDKIT_DB_SQLITE_POOL_RECYCLE_SECONDS", raising=False)
    monkeypatch.delenv("RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("RAPIDKIT_DB_SQLITE_PRAGMAS", raising=False)
    monkeypatch.delenv("RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING", raising=False)

    overrides_obj = DbSqliteOverrides()
    base_context = {
        "default_database_path": "./app.db",
        "default_pool": {"max_size": 4, "recycle_seconds": 600},
        "default_timeout_seconds": 30.0,
        "default_pragmas": {"busy_timeout": "3000"},
        "default_create_if_missing": True,
    }

    mutated = overrides_obj.apply_base_context(base_context)
    assert mutated == base_context
