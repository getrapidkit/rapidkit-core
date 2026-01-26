"""Override scaffolding tests for Db Postgres."""

from __future__ import annotations

from pathlib import Path

from modules.free.database.db_postgres import overrides as overrides_module


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class DatabasePostgresOverrides" in overrides_source


def test_engine_config_overrides(monkeypatch) -> None:
    base_config = {"pool_timeout": 30}
    mutated_same = overrides_module._enhance_engine_config(base_config)
    assert mutated_same == base_config
    assert mutated_same is not base_config

    monkeypatch.setenv("RAPIDKIT_DB_POSTGRES_POOL_PRE_PING", "true")
    monkeypatch.setenv("RAPIDKIT_DB_POSTGRES_ECHO_POOL", "1")
    monkeypatch.setenv("RAPIDKIT_DB_POSTGRES_STATEMENT_TIMEOUT", "15")

    mutated = overrides_module._enhance_engine_config(base_config)
    assert mutated is not base_config
    assert mutated["pool_pre_ping"] is True
    assert mutated["echo_pool"] is True
    assert mutated.get("connect_args", {}).get("options") == "-c statement_timeout=15s"
